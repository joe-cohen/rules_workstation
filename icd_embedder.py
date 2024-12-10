import openai
from supabase import create_client, Client
import os
import dotenv

# Set these environment variables or just hardcode them here
dotenv.load_dotenv('.env', override=True)

OPENAI_API_KEY =  os.getenv('OPENAI_API_KEY')#"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" #os.getenv("OPENAI_API_KEY")
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

openai.api_key = OPENAI_API_KEY

# Initialize Supabase client
supabase: Client = create_client(supabase_url, supabase_key)

# The table and column names
TABLE_NAME = "icd_codes"
SOURCE_COLUMN = "code_description"
EMBEDDINGS_COLUMN = "embeddings"

def get_rows_missing_embeddings():
    # Fetch rows that do not have embeddings yet, or need updating.
    # Adjust filters as necessary.
    response = supabase.table(TABLE_NAME).select("*").is_(EMBEDDINGS_COLUMN, None).execute()
    return response.data if response.data else []

def compute_embedding(text):
    # Use OpenAI embeddings endpoint (for example, 'text-embedding-ada-002')
    response = openai.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    embedding = response.data[0].embedding
    return embedding

def update_embeddings(row_id, embedding_vector):
    # Update the embeddings column with the new embedding vector
    supabase.table(TABLE_NAME).update({EMBEDDINGS_COLUMN: embedding_vector}).eq("id", row_id).execute()

def main():
    rows = get_rows_missing_embeddings()
    if not rows:
        print("No rows found needing embeddings update.")
        return

    for row in rows:
        text_value = row.get(SOURCE_COLUMN)
        if not text_value:
            print(f"Skipping row {row['id']} due to missing source text.")
            continue

        # Compute embeddings
        embedding_vector = compute_embedding(text_value)

        # Update the row
        update_embeddings(row['id'], embedding_vector)
        print(f"Updated embeddings for row ID {row['id']}.")

if __name__ == "__main__":
    main()
