import sqlite3
from datetime import datetime, timedelta

def create_test_session():
    conn = sqlite3.connect('backend/carbon.db')
    cursor = conn.cursor()
    
    token = 'test-farmer-link'
    phone = '+919876543210'
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    # Insert or replace session
    cursor.execute('''
        INSERT OR REPLACE INTO sessions (token, phone, expires_at)
        VALUES (?, ?, ?)
    ''', (token, phone, expires_at.isoformat()))
    
    conn.commit()
    conn.close()
    print(f"Test session created: {token}")

if __name__ == "__main__":
    create_test_session()
