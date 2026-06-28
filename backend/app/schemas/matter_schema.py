from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class MatterCreateRequest(BaseModel):
    name: str
    code: str
    client_name: str | None = None
    status: str = "計画中"
    pm_member_id: int | None = None

    @field_validator("name", "code")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("空文字は使用できません")
        return v


class MatterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    client_name: str | None
    status: str
    pm_member_id: int | None
    project_count: int
    created_at: datetime
