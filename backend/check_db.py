import sqlite3
import json

conn = sqlite3.connect('carbon.db')
cursor = conn.cursor()
cursor.execute('SELECT metadata_json FROM farmers WHERE phone = ?', ('+919999999999',))
row = cursor.fetchone()
print(f"Metadata JSON: {row[0] if row else 'No record found'}")
conn.close()
