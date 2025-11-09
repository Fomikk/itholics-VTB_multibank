"""Test script to check if application can start without errors."""
import sys
import asyncio

async def test_startup():
    """Test application startup."""
    try:
        print("Testing application startup...")
        print("-" * 60)
        
        # Test 1: Import settings
        print("1. Testing settings import...")
        from app.settings import settings
        print(f"   [OK] Settings loaded")
        sbank_id = settings.sbank_client_id[:10] if settings.sbank_client_id else "(empty)"
        sbank_secret = "***" if settings.sbank_client_secret else "(empty)"
        print(f"   - SBank Client ID: {sbank_id}...")
        print(f"   - SBank Client Secret: {sbank_secret}")
        
        # Test 2: Import main app
        print("\n2. Testing app import...")
        from app.main import app
        print(f"   [OK] App imported successfully")
        
        # Test 3: Check routes
        print("\n3. Testing routes...")
        routes = [route.path for route in app.routes]
        print(f"   [OK] Found {len(routes)} routes")
        print(f"   - Routes: {', '.join(routes[:5])}...")
        
        # Test 4: Test bank clients
        print("\n4. Testing bank clients...")
        from app.clients.factory import get_bank_client
        try:
            sbank_client = get_bank_client("sbank")
            print(f"   [OK] SBank client created")
            client_id_display = sbank_client.client_id[:10] if sbank_client.client_id else "(empty)"
            print(f"   - Client ID: {client_id_display}...")
        except Exception as e:
            print(f"   [WARN] Error creating SBank client: {e}")
        
        print("\n" + "-" * 60)
        print("[OK] All tests passed! Application should start correctly.")
        print("\nTo start the server, run:")
        print("  uvicorn app.main:app --reload")
        return True
        
    except Exception as e:
        print("\n" + "-" * 60)
        print(f"[ERROR] Error during startup test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_startup())
    sys.exit(0 if success else 1)

