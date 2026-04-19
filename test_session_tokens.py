#!/usr/bin/env python3
"""Test session token functionality in database shim."""

import sys
import os
from datetime import datetime, timedelta
import secrets

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.db.database import supabase

def test_session_table_mapped():
    """Test that sessions table is in the table map."""
    print("✓ Testing sessions table mapping...")
    try:
        # This will raise ValueError if table not mapped
        result = supabase.table("sessions").select("*").execute()
        print(f"  ✅ Sessions table is accessible (found {result.count} existing sessions)")
        return True
    except ValueError as e:
        print(f"  ❌ FAILED: {e}")
        return False

def test_insert_session():
    """Test inserting a session token."""
    print("✓ Testing session token insertion...")
    try:
        token = secrets.token_urlsafe(12)
        phone = "+918497010516"
        expires_at = datetime.utcnow() + timedelta(hours=24)

        response = supabase.table("sessions").insert({
            "token": token,
            "phone": phone,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at
        }).execute()

        if response.data:
            print(f"  ✅ Successfully inserted session token: {token[:8]}...")
            return token, phone
        else:
            print(f"  ❌ Insert returned no data")
            return None, None
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return None, None

def test_retrieve_session(token, phone):
    """Test retrieving a session by token."""
    print("✓ Testing session token retrieval...")
    try:
        response = supabase.table("sessions").select("*").eq("token", token).execute()

        if response.data and response.data[0]["phone"] == phone:
            print(f"  ✅ Successfully retrieved session for {phone}")
            return True
        else:
            print(f"  ❌ Session not found or phone mismatch")
            return False
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False

def test_token_expiry():
    """Test token expiry checking."""
    print("✓ Testing token expiry logic...")
    try:
        token = secrets.token_urlsafe(12)
        phone = "+919876543210"
        expires_at = datetime.utcnow() - timedelta(hours=1)  # Already expired

        response = supabase.table("sessions").insert({
            "token": token,
            "phone": phone,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at
        }).execute()

        # Retrieve and check expiry
        session_resp = supabase.table("sessions").select("expires_at").eq("token", token).execute()
        if session_resp.data:
            expires_str = session_resp.data[0]["expires_at"]
            if isinstance(expires_str, str):
                expires = datetime.fromisoformat(expires_str)
            else:
                expires = expires_str

            is_expired = datetime.utcnow() > expires
            if is_expired:
                print(f"  ✅ Token expiry detection working (token is expired as expected)")
                return True
            else:
                print(f"  ❌ Token should be expired but isn't")
                return False
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("SESSION TOKEN DATABASE TESTS")
    print("="*60 + "\n")

    results = []

    # Test 1: Table mapping
    results.append(test_session_table_mapped())
    print()

    # Test 2: Insert
    token, phone = test_insert_session()
    results.append(token is not None)
    print()

    # Test 3: Retrieve
    if token:
        results.append(test_retrieve_session(token, phone))
        print()

    # Test 4: Expiry
    results.append(test_token_expiry())
    print()

    # Summary
    passed = sum(results)
    total = len(results)
    print("="*60)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("="*60)

    if passed == total:
        print("✅ All session token tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
