import sqlite3
import os

# Ajuste se o banco tiver outro nome
db_path = os.path.join("src", "visionmoto.db")

con = sqlite3.connect(db_path)
cur = con.cursor()
try:
    cur.execute("ALTER TABLE detections ADD COLUMN timestamp TEXT")
    con.commit()
    print("✅ Coluna 'timestamp' adicionada.")
except Exception as e:
    print("⚠️ Aviso:", e)
finally:
    con.close()
