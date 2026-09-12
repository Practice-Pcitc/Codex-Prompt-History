from app.repositories.prompt_history import PromptHistoryRepository
from app.services.prompt_history import PromptHistoryService


def get_prompt_history_service() -> PromptHistoryService:
    return PromptHistoryService(PromptHistoryRepository())
