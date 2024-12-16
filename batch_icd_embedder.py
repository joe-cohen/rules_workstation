import openai
from supabase import create_client, Client
import os
import dotenv

# Load environment variables
dotenv.load_dotenv('.env', override=True)

OPENAI_API_KEY =  os.getenv('OPENAI_API_KEY')
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

openai.api_key = OPENAI_API_KEY

# Initialize Supabase client
supabase: Client = create_client(supabase_url, supabase_key)

# Configuration
TABLE_NAME = "cpt_codes"
SOURCE_COLUMN = "cpt_description"
EMBEDDINGS_COLUMN = "description_embedding"
MODEL_NAME = "text-embedding-ada-002"
BATCH_SIZE = 500  # Adjust as needed based on memory/latency constraints

def get_rows_missing_embeddings():
    # Fetch rows that do not have embeddings yet
    # The 'limit' parameter may be used if you have a large number of rows and want to process in chunks
    response = supabase.table(TABLE_NAME).select("*").is_(EMBEDDINGS_COLUMN, None).limit(20000).execute()
    return response.data if response.data else []

def compute_embeddings_in_batch(texts):
    # Send multiple texts to the embeddings endpoint at once
    response = openai.embeddings.create(
        input=texts,
        model=MODEL_NAME
    )
    # The response will have one embedding per input text
    embeddings = [item.embedding for item in response.data]
    #print(embeddings)
    return embeddings

def update_embedding(row_id, embedding_vector):
    # Update a single row's embedding
    supabase.table(TABLE_NAME).update({EMBEDDINGS_COLUMN: embedding_vector}).eq("id", row_id).execute()

def main():
    rows = get_rows_missing_embeddings()
    rowmark = 0
    if not rows:
        print("No rows found needing embeddings update.")
        return
    
    # Process rows in batches
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i+BATCH_SIZE]
        texts = [row[SOURCE_COLUMN] for row in batch if row.get(SOURCE_COLUMN)]

        # Skip if no valid texts in this batch
        if not texts:
            continue
        
        # Compute all embeddings for this batch in one request
        embeddings = compute_embeddings_in_batch(texts)

        # Now, update each corresponding row with its embedding
        # We matched texts to rows in order, so embeddings should align
        emb_idx = 0
        for row in batch:
            if row.get(SOURCE_COLUMN):
                update_embedding(row['id'], embeddings[emb_idx])
                #print(row)
                rowmark = row
                emb_idx += 1
        print(rowmark)
        print(f"Processed batch {i//BATCH_SIZE + 1} with {len(texts)} embeddings.")

    print("All missing embeddings have been updated.")

if __name__ == "__main__":
    for i in range(0,10):
        main()