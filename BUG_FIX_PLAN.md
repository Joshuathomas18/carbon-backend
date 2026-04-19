# Bug Fix Plan - WhatsApp Integration

## 🔍 Three Bugs Identified & Solutions

### BUG #1: HTML Entities in Messages (&#x27;, &gt;)
**Priority:** 1 (Highest - UX Impact)  
**Time:** 15 minutes  
**Severity:** High

#### Root Cause
TwiML library auto-escapes special characters for XML safety:
- `'` → `&#x27;`
- `>` → `&gt;`
- `<` → `&lt;`

WhatsApp displays the raw escape codes instead of unescaping them.

#### Solution
File: `backend/app/api/v1/routes.py` (lines 345-351)

```python
# BEFORE:
resp = MessagingResponse()
resp.message(safe_reply)
return Response(content=str(resp), media_type="application/xml")

# AFTER:
resp = MessagingResponse()
resp.message(safe_reply)
twiml_str = html.unescape(str(resp))
return Response(content=twiml_str, media_type="application/xml")
```

**Expected Result:** Farmer sees "it's" not "it&#x27;s" ✅

---

### BUG #2: GPS Location Reverse Geocoding
**Priority:** 2 (Medium - Data Quality)  
**Time:** 30 minutes  
**Severity:** Medium

#### Status
✅ GPS extraction already working (routes.py lines 321-323)  
✅ Metadata passing already implemented (routes.py line 335)  
✅ Location state already exists (whatsapp_service.py line 155)  
❌ Missing: Reverse geocoding integration (show village name, not coordinates)

#### Solution
File: `backend/app/services/whatsapp_service.py` (LOCATION state, ~line 155)

```python
from app.services.geo_service import GeoService

elif state == "LOCATION":
    lat = meta.get("latitude")
    lon = meta.get("longitude")
    
    if lat and lon:
        # NEW: Reverse geocode to get location name
        try:
            geo = GeoService()
            location_name = await geo.reverse_geocode(lat, lon)
        except Exception as e:
            location_name = f"{lat:.4f}, {lon:.4f}"
        
        # Store in DB
        self.db.table("farmers").update({
            "latitude": lat,
            "longitude": lon,
            "location_name": location_name,
            "bot_state": "LOCATION_CONFIRM",
        }).eq("phone", phone).execute()
        
        message = get_text("location_confirm", lang=lang, name=location_name)
        return message
    else:
        return get_text("location_prompt", lang=lang)
```

**Expected Result:** "We noted: Ludhiana, Punjab" not "We noted: 30.905, 75.857" ✅

---

### BUG #3: Magic Links Not Working + Phone Exposed
**Priority:** 3 (Medium - Security/Stability)  
**Time:** 45 minutes + 30 minutes (deployment)  
**Severity:** Medium-High

#### Problems
1. ngrok URLs die after 8 hours or session ends
2. Phone number exposed in URL: `?phone=+918497010516`
3. Link breaks if ngrok crashes

#### Solution (Layer 1 - Immediate)
Deploy to Render.com or Railway.app for stable URL (15 minutes):
1. Push to GitHub
2. Go to https://render.com/deploy
3. Connect repo & deploy
4. Get stable URL: `https://carbon-kheth.onrender.com`
5. Update `FRONTEND_URL` in `.env`
6. Update Twilio webhook URL

#### Solution (Layer 2 - Proper Security)
Use session tokens instead of phone in URL:

**Step 1:** Add SessionModel to `backend/app/db/database.py`
```python
class SessionModel(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
```

**Step 2:** Update `whatsapp_service.py` (GREETING state)
```python
import secrets
from datetime import timedelta

# Generate token
session_token = secrets.token_urlsafe(12)

# Store in DB
expires_at = datetime.utcnow() + timedelta(hours=24)
self.db.table("sessions").insert({
    "token": session_token,
    "phone": phone,
    "created_at": datetime.utcnow(),
    "expires_at": expires_at,
}).execute()

# Generate safe link (NO phone exposed!)
magic_link = f"{self.frontend_url}/map?token={session_token}"
```

**Step 3:** Update React `frontend/src/views/MapConfirmView.jsx`
```jsx
const token = new URLSearchParams(window.location.search).get('token');
const [phone, setPhone] = useState(null);

useEffect(() => {
    if (token) {
        fetch(`/api/v1/sessions/${token}`)
            .then(r => r.json())
            .then(data => setPhone(data.phone))
            .catch(e => console.error("Invalid token", e));
    }
}, [token]);
```

**Step 4:** Add endpoint to `routes.py`
```python
@router.get("/sessions/{token}")
async def get_session_phone(token: str, db: Client = Depends(get_supabase)):
    session = db.table("sessions").select("phone").eq("token", token).execute()
    if not session.data:
        raise HTTPException(status_code=404, detail="Invalid token")
    return {"phone": session.data[0]["phone"]}
```

**Expected Result:**
- Link: `https://yourdomain.com/map?token=aB3xK9mQ`
- Phone NOT exposed ✅
- Token expires in 24 hours ✅
- Privacy: ✅

---

## 📋 Implementation Order

| Priority | Bug | Time | Impact |
|----------|-----|------|--------|
| 1 | HTML Entities | 15m | High - User sees garbage |
| 2 | GPS Geocoding | 30m | Medium - Data quality |
| 3 | Secure Links | 45m | Medium - Security/privacy |
| 4 | Deploy Server | 30m | High - Stability |

**Total: ~2 hours**

---

## ✅ Verification Checklist

After each fix:

- [ ] Fix 1: Send "it's" → See "it's" not "it&#x27;s"
- [ ] Fix 2: Share location → See "Ludhiana, Punjab" not "30.905, 75.857"
- [ ] Fix 3: Copy link → Phone NOT in URL
- [ ] Fix 4: Close ngrok → Links still work

---

## 🚀 Next Steps

1. **TODAY:** Fix HTML entities (15m) - Highest impact
2. **TODAY:** Integrate reverse geocoding (30m) - Data quality
3. **TOMORROW:** Add session tokens (45m) - Security
4. **THIS WEEK:** Deploy to Render (30m) - Production ready

All fixes are backward-compatible and can be done incrementally.
