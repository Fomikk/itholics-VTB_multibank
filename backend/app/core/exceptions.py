"""Custom exceptions."""
from fastapi import HTTPException


class BankAPIError(HTTPException):
    """Error from bank API."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class ConsentRequiredError(HTTPException):
    """Consent is required for the operation."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

