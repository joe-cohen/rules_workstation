import openai
from supabase import create_client, Client
import dotenv
import pandas as pd
import os
import csv
import time

dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase_client = create_client(supabase_url, supabase_key)

class llm_match():
    def __init__(self, prompt_template=None):
        self.prompt_template = prompt_template or "Given the following input: '{input_text}', generate a response."
        self.supabase_client = create_client(supabase_url, supabase_key)
        
    def query_openai(self, input_text):
        """
        Uses OpenAI's Python SDK to query the GPT-4 model with a prompt template.
        """
        try:
            # Create the prompt
            prompt = self.prompt_template.format(input_text=input_text)
            
            # Call OpenAI's completion API
            response = openai.chat.completions.create(
                model="gpt-4o-mini",  # Use "gpt-4" or "gpt-3.5-turbo"
                messages=[
                    {"role": "system", "content": "You are a helpful medical professional creating the most applicable phrases to help find the given indications as frequently as possible."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                timeout= 60
                
            )
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"Error querying OpenAI API: {e}")
            return None

    def data_table_creator(self, response):
        lines = response.strip().split("\n")
        #print('lines',lines)
        data = []

        for line in lines:
            # Split the line into code and description
            if "|" in line:
                #print('line' , line)
                code, description = line.split("|")
                #print('readout',code, description)
                if code and description:
                    data.append({"Code": code.strip(), "Description": description.strip()})


        # Create a DataFrame from the parsed data
        df = pd.DataFrame(data)
        return df
    
    def embed_text_openai(self, text: str) -> list:
        """
        Generates embeddings for the given text using OpenAI's embedding model.
        """
        try:
            response = openai.embeddings.create(
                input=text,
                model="text-embedding-ada-002"  # Correct model for embeddings
            )

            return response.data[0].embedding
        
        except Exception as e:
            print(f"Error generating embedding: {e}")

            return None
        
    def process_table(self, table_response):
        """
        Adds an 'embeddings' column to the DataFrame by embedding the 'Description' column.
        """
        table_response['embeddings'] = table_response['Description'].apply(
            lambda x: self.embed_text_openai(x)
        )
        return table_response
    
    def similarity_search(self, query_embedding):
        response = self.supabase_client.rpc("find_most_similar", {
        "input_vector": query_embedding
            }).execute()

            # Process and return results
        results = response.data
        #return [{"match": result[match_column], "score": result["similarity"]} for result in results]
        return results

    def match_over_table(self, df):
     
        df[['match_value','sim_score']] = df['embeddings'].apply(
            lambda x: pd.Series(self.similarity_search(x)[0])
        )
        return df



    def main(self, input_text):


        # Instantiate the ruleCreator with a prompt template that can be changed
        prompt_template = '''You are a highly sophisticated medical coder .Given the following input: '{input_text}',create a comprehenseive list of ICD codes that reprsent the inpu and their relevant description.
        There should be no headers, and the response should be in the structure: 
        
        B21 | HIV disease resulting in opportunistic infection. 
        
        There should not be any other markings before or after the dataset and all should have the same form
        '''

        rc = llm_match(prompt_template=prompt_template)
        response1 = rc.query_openai(input_text)
        #print('llm call completed', response1)
        table_response = rc.data_table_creator(response1)
        embedded_table = rc.process_table(table_response=table_response)
        match = rc.match_over_table(df = embedded_table)
        return match


        
if __name__ == "__main__":
    input_text = input('enter:')
    match_inst = llm_match()
    fin = match_inst.main(input_text)
    print(fin)