from typing import Literal, Self

from pydantic import AwareDatetime, Field, model_validator

from app.schemas.prompt import ApiModel


class CommonFilters(ApiModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    project_id: str | None = Field(default=None, max_length=200)
    project_name: str | None = Field(default=None, max_length=120)
    session_id: str | None = Field(default=None, max_length=200)
    start_time: AwareDatetime | None = None
    end_time: AwareDatetime | None = None

    @model_validator(mode="after")
    def validate_time_range(self) -> Self:
        if self.start_time and self.end_time and self.start_time > self.end_time:
            raise ValueError("startTime must not be after endTime")
        return self


class PromptFilters(CommonFilters):
    keyword: str | None = Field(default=None, max_length=500)


class SessionFilters(CommonFilters):
    status: Literal["active", "ended"] | None = None


class ToolEventFilters(CommonFilters):
    tool_name: str | None = Field(default=None, max_length=200)
    status: Literal["success", "failed"] | None = None
