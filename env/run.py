from eduplan import app
import psycopg2

conn = psycopg2.connect(
    host = "localhost",
    database = "CSC_490_Capstone",
    user = "postgres",
    password = "definitelynotthepassword"
)
#testing 3
cur = conn.cursor()
insert_query = """
INSERT INTO users (email, password_hash, role) 
VALUES (%s, %s, %s)
RETURNING user_id;
"""
user_data = ("43@example.com", "testpassword123", "student")
cur.execute(insert_query,user_data)
new_user_id = cur.fetchone()[0]
print(f"Inserted user with ID: {new_user_id}")
conn.commit()
cur.close()
conn.close()




if __name__ == '__main__':
    app.run()



