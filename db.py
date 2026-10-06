import os
import psycopg2


def get_connection():
    return psycopg2.connect(
        os.getenv("postgresql://myuser:mypassword@db:5432/mydb")
    )


def create_messages_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            role VARCHAR(20) NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()

    cursor.close()
    conn.close()


def save_message(role, content):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO messages (role, content)
        VALUES (%s, %s)
        """,
        (role, content)
    )

    conn.commit()

    cursor.close()
    conn.close()