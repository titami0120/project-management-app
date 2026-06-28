from pydantic import BaseModel, ConfigDict


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    wbs_tmp: str
    name: str
    code: str | None
    display_order: int | None
    matter_id: int | None
    matter_name: str | None


class ProjectUpdateRequest(BaseModel):
    name: str | None = None
    code: str | None = None
    display_order: int | None = None


class ProjectMatterAssignRequest(BaseModel):
    matter_id: int | None
