"""
POST /chat — Streaming chat endpoint.

Uses Server-Sent Events (SSE) so the frontend can render tokens as they arrive.
Each token is sent as: data: <token>\n\n
End of stream is signaled by: data: [DONE]\n\n
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from queue import Queue, Empty
from threading import Thread
from langchain_core.callbacks import BaseCallbackHandler

from app.core.agent import run_agent
from app.api.session import get_session

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    question: str


class StreamingCallbackHandler(BaseCallbackHandler):
    """
    Streams only the final agent answer token-by-token.

    ReAct agents make multiple LLM calls (one per tool + final answer).
    on_llm_end fires after EACH call, so we can't use it as the sentinel.
    Instead, on_agent_finish fires exactly once when the full chain is done.
    """

    def __init__(self, queue: Queue):
        self.queue = queue
        self._in_final_answer = False

    def on_llm_new_token(self, token: str, **kwargs):
        # Buffer tokens and check if we've reached "Final Answer:"
        if self._in_final_answer:
            self.queue.put(token)
        elif "Final Answer:" in token:
            self._in_final_answer = True
            # Strip the "Final Answer:" prefix from the token
            content = token.split("Final Answer:", 1)[-1].lstrip()
            if content:
                self.queue.put(content)

    def on_agent_finish(self, finish, **kwargs):
        # Fallback: if streaming didn't capture tokens, send the full output
        if not self._in_final_answer:
            self.queue.put(finish.return_values.get("output", ""))
        self.queue.put(None)  # sentinel: done

    def on_llm_error(self, error, **kwargs):
        self.queue.put(None)


@router.post("/chat")
async def chat(request: ChatRequest):
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please upload PDFs first."
        )
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    token_queue: Queue = Queue()
    handler = StreamingCallbackHandler(token_queue)

    # Run agent in a background thread (AgentExecutor is synchronous)
    def run_in_thread():
        try:
            run_agent(
                agent_executor=session.agent_executor,
                question=request.question,
                history=session.history,
                callbacks=[handler],
            )
        except Exception as e:
            token_queue.put(None)

    thread = Thread(target=run_in_thread, daemon=True)
    thread.start()

    def token_stream():
        while True:
            try:
                token = token_queue.get(timeout=30)
                if token is None:
                    yield "data: [DONE]\n\n"
                    break
                # Escape newlines for SSE format
                yield f"data: {token.replace(chr(10), '<br>')}\n\n"
            except Empty:
                yield "data: [DONE]\n\n"
                break

    return StreamingResponse(
        token_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )
