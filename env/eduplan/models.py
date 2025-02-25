from eduplan import app
import psycopg2
import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "db_config.json")
with open(CONFIG_PATH, "r") as config_file:
    config = json.load(config_file)

conn = psycopg2.connect(
    host=config["host"],
    database=config["database"],
    user=config["user"],
    password=config["password"]
)

cur = conn.cursor()
insert_query = """
INSERT INTO users (email, password_hash, role) 
VALUES (%s, %s, %s)
RETURNING user_id;
"""
user_data = ("42@example.com", "testpassword123", "student")
cur.execute(insert_query,user_data)
new_user_id = cur.fetchone()[0]
print(f"Inserted user with ID: {new_user_id}")
conn.commit()
cur.close()
conn.close()