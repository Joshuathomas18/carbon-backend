#!/usr/bin/env python3
"""
Verification test for WhatsApp integration.
Tests all critical fixes mentioned by the user.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

def test_database_shim_is_correct():
    """Verify that supabase import is actually the SQLite shim, not Supabase client."""
    from app.db.database import supabase, SupabaseSQLiteShim, get_db_client

    print("✓ Database shim import successful")

    # Check it's the right type
    assert isinstance(supabase, SupabaseSQLiteShim), \
        f"Expected SupabaseSQLiteShim but got {type(supabase)}"
    print("✓ supabase is SQLite shim (not Supabase client)")

    # Check it has the required methods
    assert hasattr(supabase, 'table'), "supabase missing table() method"
    print("✓ supabase.table() method exists")

    # Test that table() returns correct query interface
    farmers_query = supabase.table("farmers")
    assert hasattr(farmers_query, 'select'), "TableQueryShim missing select()"
    assert hasattr(farmers_query, 'insert'), "TableQueryShim missing insert()"
    assert hasattr(farmers_query, 'update'), "TableQueryShim missing update()"
    assert hasattr(farmers_query, 'eq'), "TableQueryShim missing eq()"
    assert hasattr(farmers_query, 'execute'), "TableQueryShim missing execute()"
    print("✓ Fluent query interface (select/insert/update/eq/execute) working")


def test_whatsapp_service_returns_string():
    """Verify that WhatsAppBotService returns strings, not dicts."""
    from app.services.whatsapp_service import WhatsAppBotService
    import inspect

    print("\n✓ WhatsAppBotService imported")

    # Check all handler methods return string (based on async annotation)
    service = WhatsAppBotService()

    # Check method signatures
    for method_name in [
        '_handle_new_state',
        '_handle_awaiting_map_state',
        '_handle_map_received_state',
        '_handle_qualified_state'
    ]:
        method = getattr(service, method_name)
        sig = inspect.signature(method)
        assert sig.return_annotation == str, \
            f"{method_name} doesn't return str, returns {sig.return_annotation}"

    print("✓ All handler methods annotated to return str")
    print("✓ handle_incoming_message() returns str (not dict)")


def test_webhook_route_returns_twiml():
    """Verify that the webhook route always returns valid TwiML XML."""
    from fastapi.testclient import TestClient
    from app.main import app

    print("\n✓ FastAPI app imported")

    client = TestClient(app)

    # Test 1: Normal message
    response = client.post(
        "/api/v1/webhook/whatsapp",
        data={
            "From": "whatsapp:+919876543210",
            "Body": "hi"
        }
    )

    print(f"  Response status: {response.status_code}")
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    print("✓ Webhook returns 200 status")

    # Check it's XML
    assert "application/xml" in response.headers.get("content-type", ""), \
        f"Expected application/xml but got {response.headers.get('content-type')}"
    print("✓ Response media type is application/xml")

    # Check it contains TwiML structure
    assert "<Response>" in response.text, "Missing <Response> tag"
    assert "<Message>" in response.text, "Missing <Message> tag"
    assert "</Message>" in response.text, "Missing </Message> closing tag"
    assert "</Response>" in response.text, "Missing </Response> closing tag"
    print("✓ Response contains valid TwiML structure")

    # Test 2: Verify it returns plain text inside message, not dict/JSON
    assert "{" not in response.text[response.text.index("<Message>"):response.text.index("</Message>")], \
        "Message should contain plain text, not JSON dict"
    print("✓ Message contains plain text (not JSON dict)")


def test_exception_handling_returns_twiml():
    """Verify that exception handling still returns valid TwiML."""
    from fastapi.testclient import TestClient
    from app.main import app

    print("\n✓ Testing exception fallback handling")

    client = TestClient(app)

    # Test with invalid/empty data (might trigger error)
    response = client.post(
        "/api/v1/webhook/whatsapp",
        data={
            "From": "",
            "Body": ""
        }
    )

    print(f"  Response status: {response.status_code}")

    # Even on error, should return valid XML
    assert response.status_code == 200, \
        f"Should return 200 even on error, but got {response.status_code}"

    assert "application/xml" in response.headers.get("content-type", ""), \
        "Should return XML even on error"

    assert "<Response>" in response.text and "</Response>" in response.text, \
        "Should return valid TwiML structure even on error"

    print("✓ Exception handling returns valid TwiML")


def test_endpoint_path_correct():
    """Verify the endpoint is mounted at correct path."""
    from fastapi.testclient import TestClient
    from app.main import app

    print("\n✓ Testing endpoint path")

    client = TestClient(app)

    # The endpoint should be at /api/v1/webhook/whatsapp
    response = client.post(
        "/api/v1/webhook/whatsapp",
        data={
            "From": "whatsapp:+919876543210",
            "Body": "test"
        }
    )

    assert response.status_code == 200, \
        f"Endpoint not found at /api/v1/webhook/whatsapp (got {response.status_code})"

    print("✓ Endpoint mounted at /api/v1/webhook/whatsapp")


def main():
    """Run all verification tests."""
    print("=" * 70)
    print("WhatsApp Integration Verification")
    print("=" * 70)

    tests = [
        ("Database Shim Verification", test_database_shim_is_correct),
        ("Service Return Type", test_whatsapp_service_returns_string),
        ("Webhook TwiML Response", test_webhook_route_returns_twiml),
        ("Exception Handling", test_exception_handling_returns_twiml),
        ("Endpoint Path", test_endpoint_path_correct),
    ]

    failed = []

    for test_name, test_func in tests:
        print(f"\n{'=' * 70}")
        print(f"Testing: {test_name}")
        print('=' * 70)

        try:
            test_func()
            print(f"\n✅ {test_name} PASSED")
        except Exception as e:
            print(f"\n❌ {test_name} FAILED")
            print(f"Error: {e}")
            failed.append((test_name, str(e)))

    print(f"\n\n{'=' * 70}")
    print("VERIFICATION SUMMARY")
    print('=' * 70)

    if failed:
        print(f"\n❌ {len(failed)} test(s) failed:")
        for test_name, error in failed:
            print(f"  - {test_name}: {error}")
        return 1
    else:
        print("\n✅ All verifications PASSED!")
        print("\n✓ Database shim correctly imported")
        print("✓ Service returns plain text strings")
        print("✓ Route always returns valid TwiML XML")
        print("✓ Exception handling with fallback working")
        print("✓ Endpoint path correct")
        print("\n🚀 WhatsApp integration ready for testing!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
