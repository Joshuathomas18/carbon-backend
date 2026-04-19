# WhatsApp Integration Testing Guide

**Status:** ✅ Backend running and ready  
**Server:** http://localhost:8000  
**Health:** Running on port 8000

---

## Current Status

### ✅ Backend Running
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### ✅ Endpoint Verified
```bash
curl -X POST http://localhost:8000/api/v1/webhook/whatsapp \
  -d "From=whatsapp:+919876543210" \
  -d "Body=hi"

# Response: Valid TwiML XML with welcome message
# ✅ No errors, no crashes
```

---

## Step 1: Expose Backend to Internet (Use ngrok)

You need to tunnel your local backend to the internet so Twilio can send webhooks.

### Option A: Use ngrok (Recommended)

1. **Download ngrok** from https://ngrok.com/download
   ```bash
   # On Linux:
   wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
   tar xvf ngrok-v3-stable-linux-amd64.tgz
   sudo mv ngrok /usr/local/bin/
   ```

2. **Sign up** at https://ngrok.com (free account)

3. **Authenticate ngrok**
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

4. **Expose your backend**
   ```bash
   ngrok http 8000
   ```

   **Output:**
   ```
   ngrok by @inconshapely
   
   Session Status                online
   Account                       user@example.com
   Version                       3.x.x
   Region                        us
   Latency                       45ms
   Web Interface                 http://127.0.0.1:4040
   Forwarding                    https://xxxx-xx-xxx-xxx-xx.ngrok.io -> http://localhost:8000
   ```

   **Copy the HTTPS URL:** `https://xxxx-xx-xxx-xxx-xx.ngrok.io`

### Option B: Use your own domain/VPS

If you have a domain and server, deploy the backend there instead of using ngrok.

---

## Step 2: Configure Twilio WhatsApp Webhook

1. **Go to Twilio Console:** https://console.twilio.com

2. **Find your WhatsApp-enabled number:**
   - Go to: **Messaging** → **Try it out** → **Send an SMS**
   - Or: **Messaging** → **Settings** → **WhatsApp** (if available)

3. **Set Webhook URL:**
   - Location varies by Twilio version, but typically:
   - **Messaging** → **Settings** → **Webhooks** → **Incoming messages**
   - Or: **Phone Numbers** → **Your Number** → **Webhook URL**
   
4. **Enter webhook URL:**
   ```
   https://xxxx-xx-xxx-xxx-xx.ngrok.io/api/v1/webhook/whatsapp
   ```

5. **HTTP Method:** POST

6. **Save/Update**

---

## Step 3: Update Environment Variables

Edit `backend/.env`:

```env
# Get these from Twilio console
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=whatsapp:+1234567890  # Your Twilio WhatsApp number

# This can stay as localhost during ngrok testing
FRONTEND_URL=http://localhost:3000

# Everything else stays the same
DATABASE_URL=sqlite:///./carbon.db
ENVIRONMENT=development
DEBUG=True
```

---

## Step 4: Restart Backend (Optional)

If you've changed the `.env` file, restart the server:

```bash
# Kill the running server
pkill -f "uvicorn"

# Start it again
cd /home/user/carbon-backend/backend && \
PYTHONPATH=/tmp/supabase_local:$PYTHONPATH \
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Step 5: Test with Real WhatsApp

1. **Open WhatsApp on your phone**

2. **Send a message to your Twilio WhatsApp number** with any text
   - Example: "hi", "hello", "test"

3. **Instant Response:**
   - You should get an immediate response with:
     - Welcome message in Hindi
     - Magic link to draw farm boundary
     - Instructions for next steps

---

## Expected Response Flow

### Message 1: "hi"
```
🌾 *Namaste!* 🌾

Carbon Sequestration Program mein aapka swagat hai!

[Welcome message in Hindi]

*Yahan click karke apna farm draw karein:*
http://localhost:3000/discover?phone=+919876543210

Iske baad, hum aapko 3 simple sawal puchenge. Shuruaat karein! 👇
```

### Click the link:
- Opens React map on your phone
- Draw a polygon on the map
- Submit → sends to backend
- Backend triggers question-asking

### Message 2: (auto-sent after polygon)
```
✅ Shukriya! Aapka farm map mila.

*Aab yeh 3 sawal jawaab dein:*

1️⃣ *Kya aap stubble burn karte ho?*
   Jawab: haan ya nahi

2️⃣ *Kya aap zero-till farming karte ho?*
   Jawab: haan ya nahi

3️⃣ *Aap kitne urea bags use karte ho per season?*
   Jawab: number (jaise 5 ya 10)

Saare 3 questions ke jawab ek sath bhej dein!
```

### Message 3: Answer questions
```
You: "haan, nahi, 5"
```

### Message 4: (Carbon Estimate)
```
🎉 *Dhanyavaad!* 🎉

Aapke farm ke liye carbon estimate ready hai:

💰 *Estimated Payout:* ₹XXXX
📊 *Carbon:* X.XX tonnes CO2
✅ *Confidence:* XX%

Ek expert aapko 24 ghanton mein call karega details dene ke liye.

Shukriya! 🙏
```

---

## Monitoring Logs

### Real-Time Logs
To see logs as messages come in:

```bash
# In another terminal, tail the logs
tail -f /tmp/fastapi.log
```

### What to Look For

✅ **Success:**
```
2026-04-19 06:05:35,112 - app.services.whatsapp_service - INFO - WhatsApp message from +919876543210: hi
2026-04-19 06:05:35,115 - app.services.whatsapp_service - INFO - Farmer already exists
2026-04-19 06:05:35,120 - app.services.whatsapp_service - INFO - Sending welcome message
```

❌ **Error (but still handles gracefully):**
```
ERROR - Error handling WhatsApp message: [error details]
INFO - Responding with fallback message
```

---

## Troubleshooting

### Issue: No response from WhatsApp
**Solution:**
1. Check ngrok is running and showing "online"
2. Check Twilio webhook URL is correct
3. Check backend logs: `tail /tmp/fastapi.log`
4. Verify Twilio credentials in `.env` are correct

### Issue: Response delayed or timeout
**Solution:**
1. Check network latency: `ping 8.8.8.8`
2. Check backend is responding: `curl http://localhost:8000/health`
3. Check database isn't locked: Look for SQLite file lock errors in logs

### Issue: "Server error" message from Twilio
**Solution:**
1. Check the actual error in backend logs
2. Ensure all imports are installed: `pip list | grep -E "fastapi|twilio|shapely"`
3. Check `/api/v1/webhook/whatsapp` endpoint is returning valid XML

### Issue: Database error
**Solution:**
```bash
# Remove corrupted database
rm /home/user/carbon-backend/backend/carbon.db

# Restart backend
# It will auto-create new database
```

---

## Testing Checklist

- [ ] Backend running (`tail /tmp/fastapi.log` shows "Application startup complete")
- [ ] ngrok running and exposing http://0.0.0.0:8000
- [ ] Twilio webhook URL set to: `https://xxxxx.ngrok.io/api/v1/webhook/whatsapp`
- [ ] Twilio credentials in `.env` are correct
- [ ] Backend restarted (if `.env` changed)
- [ ] Local test passes: `curl -X POST http://localhost:8000/api/v1/webhook/whatsapp -d "From=..." -d "Body=hi"`
- [ ] Send test WhatsApp message to Twilio number
- [ ] Receive welcome message with magic link
- [ ] Click magic link → React map loads
- [ ] Draw polygon → submitted
- [ ] Receive questions on WhatsApp
- [ ] Answer questions
- [ ] Receive carbon estimate

---

## Files & Logs

**Server Logs:**
```bash
tail -f /tmp/fastapi.log
```

**Database:**
```bash
ls -lh /home/user/carbon-backend/backend/carbon.db
```

**Configuration:**
```bash
cat /home/user/carbon-backend/backend/.env
```

**Code:**
- Backend: `/home/user/carbon-backend/backend/app/`
- Routes: `/home/user/carbon-backend/backend/app/api/v1/routes.py`
- Service: `/home/user/carbon-backend/backend/app/services/whatsapp_service.py`

---

## Notes

- **Ngrok free plan:** Gives you a new URL each time you restart (no persistent domain)
- **Production:** Use your own domain and deploy to a server instead of ngrok
- **Rate limiting:** Twilio may have rate limits; test with 1-2 messages first
- **Logs:** All incoming messages and responses are logged with full details

---

**Ready to test!** 🚀

Once ngrok is running, just send a WhatsApp message and watch the logs for the magic.
