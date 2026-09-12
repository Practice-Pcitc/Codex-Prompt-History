from unittest.mock import Mock

import pytest
from app.core.errors import RecordNotFoundError
from app.repositories.prompt_history import PromptHistoryRepository
from app.services.prompt_history import PromptHistoryService


def test_missing_record_is_a_domain_error():
    repository = Mock(spec=PromptHistoryRepository)
    repository.get.return_value = None
    with pytest.raises(RecordNotFoundError):
        PromptHistoryService(repository).get("missing")
    repository.get.assert_called_once_with(record_id="missing")
