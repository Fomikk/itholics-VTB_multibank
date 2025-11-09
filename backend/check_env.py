"""Utility script to check .env configuration."""
import os
import sys
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def check_env():
    """Check .env file configuration."""
    env_path = Path(__file__).parent / ".env"
    
    print("=" * 60)
    print("Проверка конфигурации .env")
    print("=" * 60)
    print()
    
    if not env_path.exists():
        print("[ERROR] Файл .env не найден!")
        print(f"   Ожидаемый путь: {env_path}")
        print()
        print("Создайте файл .env в папке backend/ с содержимым:")
        print()
        print("VBANK_CLIENT_ID=team268")
        print("VBANK_CLIENT_SECRET=ваш_ключ")
        print("ABANK_CLIENT_ID=team268")
        print("ABANK_CLIENT_SECRET=ваш_ключ")
        print("SBANK_CLIENT_ID=team268")
        print("SBANK_CLIENT_SECRET=ваш_ключ")
        return False
    
        print(f"[OK] Файл .env найден: {env_path}")
    print()
    
    # Read .env file
    env_vars = {}
    with open(env_path, 'r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    # Check required variables
    required_vars = [
        'VBANK_CLIENT_ID',
        'VBANK_CLIENT_SECRET',
        'ABANK_CLIENT_ID',
        'ABANK_CLIENT_SECRET',
        'SBANK_CLIENT_ID',
        'SBANK_CLIENT_SECRET',
    ]
    
    print("Проверка переменных окружения:")
    print("-" * 60)
    
    all_ok = True
    for var in required_vars:
        value = env_vars.get(var, '')
        if value:
            # Mask secret values
            if 'SECRET' in var:
                display_value = value[:4] + '...' if len(value) > 4 else '***'
            else:
                display_value = value
            print(f"[OK] {var:25} = {display_value}")
            
            # Check for common issues
            if value.startswith('"') or value.startswith("'"):
                print(f"   [WARN] ВНИМАНИЕ: Значение в кавычках! Уберите кавычки.")
                all_ok = False
            if ' ' in value and not (value.startswith('"') or value.startswith("'")):
                print(f"   [WARN] ВНИМАНИЕ: Пробелы в значении могут вызвать проблемы.")
        else:
            print(f"[ERROR] {var:25} = (не задано)")
            all_ok = False
    
    print()
    print("-" * 60)
    
    if all_ok:
        print("[OK] Все переменные настроены!")
        print()
        print("Следующие шаги:")
        print("1. Убедитесь, что значения правильные (без кавычек, без лишних пробелов)")
        print("2. Перезапустите backend (Ctrl+C и запустите заново)")
        print("3. Попробуйте получить токен через Swagger UI")
    else:
        print("[ERROR] Найдены проблемы в конфигурации!")
        print()
        print("Исправьте следующие проблемы:")
        print("1. Добавьте недостающие переменные")
        print("2. Убедитесь, что нет кавычек вокруг значений")
        print("3. Убедитесь, что нет пробелов вокруг знака =")
        print("4. Перезапустите backend после изменений")
    
    print()
    print("=" * 60)
    
    return all_ok

if __name__ == "__main__":
    check_env()

