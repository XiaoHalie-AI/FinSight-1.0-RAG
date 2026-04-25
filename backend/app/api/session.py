"""
In-memory session store — one entry per user session.

Each session holds:
  - retriever:       built from the user's uploaded PDFs
  - agent_executor:  stateless ReAct agent wired to that retriever
  - history:         ChatMessageHistory for this conversation

Sessions are keyed by a UUID the frontend stores in localStorage.
"""

import uuid
from dataclasses import dataclass, field
from typing import Optional

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_classic.agents import AgentExecutor


@dataclass
class Session:
    retriever: object
    agent_executor: AgentExecutor
    history: ChatMessageHistory = field(default_factory=ChatMessageHistory)


# Global in-memory store
_sessions: dict[str, Session] = {}


def create_session(retriever, agent_executor: AgentExecutor) -> str:
    session_id = str(uuid.uuid4())
    _sessions[session_id] = Session(
        retriever=retriever,
        agent_executor=agent_executor,
    )
    return session_id


def get_session(session_id: str) -> Optional[Session]:
    return _sessions.get(session_id)


def delete_session(session_id: str) -> None:
    _sessions.pop(session_id, None)
