from app.schemas.workload_schema import CsvValidationError


class CsvValidationException(Exception):
    def __init__(self, errors: list[CsvValidationError]) -> None:
        self.errors = errors
        super().__init__(f"{len(errors)} validation error(s)")
