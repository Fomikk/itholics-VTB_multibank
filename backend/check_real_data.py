"""Скрипт для диагностики проблемы с реальными данными."""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.settings import settings
from app.services.aggregation import AggregationService, _has_bank_credentials
from app.services.account_linking import AccountLinkingService


async def check_credentials():
    """Проверить, загружены ли credentials."""
    print("\n=== ПРОВЕРКА CREDENTIALS ===")
    
    banks = ["vbank", "abank", "sbank"]
    has_any = False
    
    for bank in banks:
        has_creds = _has_bank_credentials(bank)
        status = "✅ ЕСТЬ" if has_creds else "❌ НЕТ"
        print(f"{bank.upper()}: {status}")
        
        if has_creds:
            has_any = True
            if bank == "vbank":
                print(f"  Client ID: {settings.vbank_client_id}")
                print(f"  Secret: {'***' if settings.vbank_client_secret else 'НЕТ'}")
            elif bank == "abank":
                print(f"  Client ID: {settings.abank_client_id}")
                print(f"  Secret: {'***' if settings.abank_client_secret else 'НЕТ'}")
            elif bank == "sbank":
                print(f"  Client ID: {settings.sbank_client_id}")
                print(f"  Secret: {'***' if settings.sbank_client_secret else 'НЕТ'}")
    
    return has_any


async def check_linked_accounts(client_id: str = "team268-1"):
    """Проверить привязанные счета."""
    print(f"\n=== ПРОВЕРКА ПРИВЯЗАННЫХ СЧЕТОВ (client_id={client_id}) ===")
    
    linked = AccountLinkingService.get_linked_accounts(client_id)
    print(f"Привязанных счетов: {len(linked)}")
    
    for acc in linked:
        print(f"  - {acc['bank']}: {acc['account_number']}")
    
    return linked


async def check_real_data(client_id: str = "team268-1"):
    """Попытаться получить реальные данные."""
    print(f"\n=== ПОПЫТКА ПОЛУЧИТЬ РЕАЛЬНЫЕ ДАННЫЕ (client_id={client_id}) ===")
    
    try:
        print("Получение счетов...")
        accounts = await AggregationService.get_accounts(client_id)
        print(f"  Получено счетов: {len(accounts)}")
        for acc in accounts:
            print(f"    - {acc.bank}: {acc.account_id} ({acc.currency})")
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        accounts = []
    
    try:
        print("\nПолучение балансов...")
        balances = await AggregationService.get_balances(client_id)
        print(f"  Получено балансов: {len(balances)}")
        for bal in balances:
            print(f"    - {bal.account_id}: {bal.amount} {bal.currency}")
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        balances = []
    
    return accounts, balances


async def main():
    """Основная функция."""
    print("=" * 60)
    print("ДИАГНОСТИКА ПРОБЛЕМЫ С РЕАЛЬНЫМИ ДАННЫМИ")
    print("=" * 60)
    
    # Проверка credentials
    has_creds = await check_credentials()
    
    # Проверка привязанных счетов
    client_id = "team268-1"
    linked = await check_linked_accounts(client_id)
    
    # Попытка получить реальные данные
    if has_creds:
        accounts, balances = await check_real_data(client_id)
        
        print("\n=== РЕЗУЛЬТАТ ===")
        if len(accounts) > 0 or len(balances) > 0:
            print("✅ РЕАЛЬНЫЕ ДАННЫЕ ПОЛУЧЕНЫ")
            print(f"   Счетов: {len(accounts)}")
            print(f"   Балансов: {len(balances)}")
        else:
            print("❌ РЕАЛЬНЫЕ ДАННЫЕ НЕ ПОЛУЧЕНЫ")
            print("   Возможные причины:")
            print("   1. Таймаут при запросе к банкам")
            print("   2. Ошибка при создании consent")
            print("   3. Банки не отвечают")
            print("   4. Неправильные credentials")
    else:
        print("\n=== РЕЗУЛЬТАТ ===")
        print("❌ CREDENTIALS НЕ НАСТРОЕНЫ")
        print("   Добавьте credentials в .env файл")
        print("   Система будет показывать демо-данные")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

