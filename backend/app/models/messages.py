from pydantic import BaseModel
from typing import Any


class AgentMessage(BaseModel):
    type: str
    task_id: str
    payload: dict[str, Any] = {}


class StatusMessage(AgentMessage):
    type: str = "status"
    step: str = ""
    progress: int = 0


class LogMessage(AgentMessage):
    type: str = "log"
    message: str = ""


class ResourceRequestMessage(AgentMessage):
    type: str = "resource_request"
    resources_needed: list[dict[str, Any]] = []


class QuestionMessage(AgentMessage):
    type: str = "question"
    question: str = ""
    options: list[str] = []


class ResourceResponseMessage(AgentMessage):
    type: str = "resource_response"
    resources: list[dict[str, Any]] = []


class AnswerMessage(AgentMessage):
    type: str = "answer"
    answer: str = ""


class CompletionMessage(AgentMessage):
    type: str = "completed"
    report: dict[str, Any] = {}


class CancelMessage(AgentMessage):
    type: str = "cancel"