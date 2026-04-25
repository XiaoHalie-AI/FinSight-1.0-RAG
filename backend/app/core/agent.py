"""
LCEL-based ReAct agent — replaces deprecated initialize_agent.

Key changes from old code:
- Uses create_react_agent + AgentExecutor (modern LangChain pattern)
- Agent is stateless; memory is passed in per-request (supports multi-user)
- Retriever is injected, not rebuilt on every call
"""

import yfinance as yf
from langchain_openai import ChatOpenAI
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_classic.tools import Tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import PromptTemplate

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)


def get_stock_price(ticker: str) -> str:
    """Fetch real-time stock price via yfinance."""
    try:
        symbol = ticker.strip().upper().replace("$", "")
        stock = yf.Ticker(symbol)
        price = stock.fast_info["lastPrice"]
        currency = stock.fast_info["currency"]
        return f"{symbol} current price: {price:.2f} {currency}"
    except Exception:
        return f"Could not fetch price for {ticker}. Try the search tool instead."


SYSTEM_PROMPT = """You are a rigorous financial analyst assistant.

You have access to the following tools:
{tools}

Use the following format STRICTLY:

Question: the input question you must answer
Thought: think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Rules:
- If the question has multiple parts, use ALL relevant tools before giving Final Answer.
- Never guess stock prices — always use Get_Live_Stock_Price.
- Never guess PDF content — always use PDF_Finance_Analyst.
- Keep Final Answer concise and directly address the question asked. Do not add unsolicited context.

Chat History:
{chat_history}

Question: {input}
Thought: {agent_scratchpad}"""


def build_agent(retriever) -> AgentExecutor:
    """
    Build a ReAct agent with injected retriever.
    Call this once per user session (or per request with session memory).
    """

    def pdf_search(query: str) -> str:
        docs = retriever.invoke(query)
        if not docs:
            return "No relevant content found in the uploaded PDFs."
        return "\n\n".join(f"[PDF]: {d.page_content}" for d in docs)

    tools = [
        Tool(
            name="PDF_Finance_Analyst",
            func=pdf_search,
            description=(
                "Search uploaded PDF financial reports. Use this for revenue, "
                "gross margin, EPS, operating income, or any data from documents. "
                "More authoritative than web search for internal data."
            ),
        ),
        Tool(
            name="Get_Live_Stock_Price",
            func=get_stock_price,
            description=(
                "Get real-time stock price. Input must be a ticker symbol (e.g. NVDA, AAPL). "
                "Always use this for stock price questions — never use web search for prices."
            ),
        ),
        Tool(
            name="Web_Search",
            func=DuckDuckGoSearchRun().run,
            description=(
                "Search the web for breaking news, macro trends, or analyst sentiment. "
                "Do NOT use for stock prices or PDF content."
            ),
        ),
    ]

    prompt = PromptTemplate.from_template(SYSTEM_PROMPT)
    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=6,
    )


def run_agent(
    agent_executor: AgentExecutor,
    question: str,
    history: ChatMessageHistory,
    callbacks: list = None,
) -> str:
    """
    Run the agent with conversation history.

    Args:
        agent_executor: The LCEL AgentExecutor
        question:       User's question
        history:        ChatMessageHistory — one instance per user session
        callbacks:      Optional list of LangChain callbacks (e.g. for streaming)
    """
    chat_history_text = ""
    for msg in history.messages:
        role = "Human" if msg.type == "human" else "Assistant"
        chat_history_text += f"{role}: {msg.content}\n"

    response = agent_executor.invoke(
        {"input": question, "chat_history": chat_history_text},
        config={"callbacks": callbacks} if callbacks else {},
    )
    output = response["output"]

    history.add_user_message(question)
    history.add_ai_message(output)

    return output


def make_history() -> ChatMessageHistory:
    """Create a fresh conversation history (one per user session)."""
    return ChatMessageHistory()
