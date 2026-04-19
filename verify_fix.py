import sqlite3
import requests

def verify():
    # 1. Force state to LOCATION for user
    conn = sqlite3.connect('backend/carbon.db')
    conn.execute("UPDATE farmers SET bot_state='LOCATION', language='hinglish' WHERE phone='+918497010516'")
    conn.commit()
    conn.close()
    
    # 2. Simulate garbage text
    payload = {
        "From": "whatsapp:+918497010516",
        "Body": "Ok done"
    }
    
    # Use headers to simulate Twilio form data
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post("http://localhost:8000/api/v1/webhook/whatsapp", data=payload, headers=headers)
    
    print("Response Status:", r.status_code)
    print("Response Body:")
    print(r.text)

if __name__ == "__main__":
    verify()
