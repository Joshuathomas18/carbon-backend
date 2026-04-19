import sqlite3
conn = sqlite3.connect('carbon.db')
cursor = conn.cursor()

# Ensure farmer exists
cursor.execute("INSERT OR IGNORE INTO farmers (phone, bot_state) VALUES ('+911234567890', 'AWAITING_MAP')")
# Update state
cursor.execute("UPDATE farmers SET bot_state = 'AWAITING_ANSWERS' WHERE phone = '+911234567890'")

# We also need a plot for this farmer because _handle_awaiting_answers_state looks for it
# Get farmer_id
cursor.execute("SELECT id FROM farmers WHERE phone = '+911234567890'")
farmer_id = cursor.fetchone()[0]

# Check if plot exists
cursor.execute("SELECT id FROM plots WHERE farmer_id = ?", (farmer_id,))
plot = cursor.fetchone()
if not plot:
    import json
    geom = {"type": "Polygon", "coordinates": [[[75.8, 30.9], [75.9, 30.9], [75.9, 31.0], [75.8, 31.0], [75.8, 30.9]]]}
    cursor.execute("INSERT INTO plots (farmer_id, area_hectares, geometry, plot_metadata) VALUES (?, ?, ?, ?)", 
                   (farmer_id, 10.0, json.dumps(geom), json.dumps({"lat": 30.9, "lon": 75.8})))

conn.commit()
conn.close()
print("Database updated for test case.")
