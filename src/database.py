import os
import psycopg2
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "pdfrag"),
        user=os.getenv("DB_USER", "raguser"),
        password=os.getenv("DB_PASSWORD", "ragpass"),
    )
    register_vector(conn)
    return conn