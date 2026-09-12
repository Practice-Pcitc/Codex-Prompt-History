class DatabaseUnavailableError(Exception):
    """History storage could not be accessed."""


class RecordNotFoundError(Exception):
    """The requested prompt does not exist."""
