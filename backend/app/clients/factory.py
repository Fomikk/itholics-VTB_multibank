"""Factory for creating bank clients."""
from app.clients.abank_client import ABankClient
from app.clients.sbank_client import SBankClient
from app.clients.vbank_client import VBankClient
from app.core.base_client import BaseBankClient


def get_bank_client(bank_code: str) -> BaseBankClient:
    """Get bank client by bank code.

    Args:
        bank_code: Bank code (vbank, abank, sbank)

    Returns:
        Bank client instance

    Raises:
        ValueError: If bank code is not supported
    """
    bank_code_lower = bank_code.lower()

    if bank_code_lower == "vbank":
        return VBankClient()
    elif bank_code_lower == "abank":
        return ABankClient()
    elif bank_code_lower == "sbank":
        return SBankClient()
    else:
        raise ValueError(f"Unsupported bank code: {bank_code}")


def get_all_bank_clients() -> dict[str, BaseBankClient]:
    """Get all bank clients.

    Returns:
        Dictionary mapping bank codes to client instances
    """
    return {
        "vbank": VBankClient(),
        "abank": ABankClient(),
        "sbank": SBankClient(),
    }

