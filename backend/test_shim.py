from app.db.database import supabase
import json

phone = "+919999999999"

# 1. Reset
supabase.table("farmers").update({"bot_state": "START", "metadata_json": {}}).eq("phone", phone).execute()

# 2. Update metadata
meta = {"location_text": "Ludhiana"}
print(f"Updating with payload: {meta}")
resp = supabase.table("farmers").update({"metadata_json": meta}).eq("phone", phone).execute()
print(f"Update response data: {resp.data}")

# 3. Read back
resp = supabase.table("farmers").select("*").eq("phone", phone).execute()
print(f"Read back data: {resp.data}")
