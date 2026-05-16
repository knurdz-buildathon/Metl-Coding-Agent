from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum
from datetime import datetime


class TaskStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    CLONING = "cloning"
    CODING = "coding"
    BUILDING = "building"
    INSPECTING = "inspecting"
    WAITING_FOR_RESOURCE = "waiting_for_resource"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResourceType(str, Enum):
    DATABASE = "database"
    FILE_STORAGE = "file_storage"
    EMAIL = "email"
    AUTH = "auth"
    PAYMENT = "payment"
    CACHE = "cache"
    QUEUE = "queue"
    SEARCH = "search"
    MONITORING = "monitoring"
    CUSTOM = "custom"


class Resource(BaseModel):
    type: ResourceType
    name: str
    description: Optional[str] = None
    env_vars: dict[str, str] = Field(default_factory=dict)
    config: dict[str, Any] = Field(default_factory=dict)


class Plan(BaseModel):
    original_prompt: str = ""
    original_plan_file: Optional[str] = None
    enhanced_plan: str = ""
    steps: list[str] = Field(default_factory=list)


class TaskCreate(BaseModel):
    github_url: str
    branch: str = "main"
    prompt: str
    plan_file: Optional[str] = None
    callback_url: Optional[str] = None
    available_resources: list[Resource] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Task(BaseModel):
    id: str = ""
    status: TaskStatus = TaskStatus.PENDING
    github_url: str = ""
    branch: str = "main"
    prompt: str = ""
    plan: Plan = Field(default_factory=lambda: Plan(original_prompt=""))
    available_resources: list[Resource] = Field(default_factory=list)
    callback_url: Optional[str] = None
    current_step: int = 0
    total_steps: int = 0
    log: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    report: Optional[dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)