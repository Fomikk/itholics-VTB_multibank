"""Custom exceptions."""
from fastapi import HTTPException


class BankAPIError(HTTPException):
    """Error from bank API."""

    pass


class ConsentRequiredError(HTTPException):
    """Consent is required for the operation."""

    pass

