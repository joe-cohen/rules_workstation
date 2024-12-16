import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Fetch variables
USER = 'postgres'
PASSWORD = os.getenv('POSTGRES_PSWD')
HOST = os.getenv('POSTGRES_HOST')
PORT = 5432
DBNAME = 'postgres'

# Connect to the database
try:
    connection = psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME,
        options='-c statement_timeout=0'  # Set timeout to 60 seconds (60000 ms)
    )
    print("Connection successful!")
    
    # Create a cursor to execute SQL queries
    cursor = connection.cursor()
    
    # SQL query to create an index with a timeout
    create_index_query = """
    CREATE INDEX IF NOT EXISTS cpt_codes_embeddings_idx
    ON cpt_codes
    USING hnsw (description_embedding vector_cosine_ops)
    WITH (m = 24, ef_construction = 200);
    """
    
    # Execute the query
    cursor.execute(create_index_query)
    connection.commit()  # Commit the transaction
    print("Index created successfully!")

    # Close the cursor and connection
    cursor.close()
    connection.close()
    print("Connection closed.")

except Exception as e:
    print(f"Failed to connect or execute query: {e}")