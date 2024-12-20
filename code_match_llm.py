import openai
from supabase import create_client, Client
import dotenv
import pandas as pd
import os
import csv
import time


dotenv.load_dotenv('.env', override=True)

OPENAI_API_KEY =  os.getenv('OPENAI_API_KEY')
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase_client = create_client(supabase_url, supabase_key)
openai.api_key = OPENAI_API_KEY

class llm_match():
    def __init__(self, prompt_template=None):
        self.prompt_template = prompt_template or "Given the following input: '{input_text}', generate a response."
        self.supabase_client = create_client(supabase_url, supabase_key)
        
    # def query_openai(self, input_text):
    #     """
    #     Uses OpenAI's Python SDK to query the GPT-4 model with a prompt template.
    #     """
    #     try:
    #         # Create the prompt
    #         prompt = self.prompt_template.format(input_text=input_text)
            
    #         # Call OpenAI's completion API
    #         response = openai.chat.completions.create(
    #             model="gpt-4-turbo",  # Use "gpt-4" or "gpt-3.5-turbo"
    #             messages=[
    #                 {"role": "system", "content": "You are a helpful medical professional."},
    #                 {"role": "user", "content": prompt}
    #             ],
    #             temperature=0,
    #             timeout= 60
                
    #         )
    #         return response.choices[0].message.content
        
    #     except Exception as e:
    #         print(f"Error querying OpenAI API: {e}")
    #         return None

    def query_openai_streaming(self,input_text: str):
        """
        Streams GPT-4 output incrementally using OpenAI's Python SDK.
        """
        try:
            # Prepare prompt
            prompt = self.prompt_template.format(input_text=input_text)
            # Start streaming the OpenAI API response
            response_stream = openai.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful medical professional."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                stream=True  # Enable streaming
            )

            for chunk in response_stream:
                if chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    yield delta

        except Exception as e:
            yield f"Error: {str(e)}"


    def data_table_creator(self, response):

        if response:
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
    

    def match_over_table_bulk(self,embedded_table, rpc_function):
        embedded_table['formatted_embeddings'] = embedded_table['embeddings'].apply(
        lambda e: "[" + ", ".join(f"{x}" for x in e) + "]"
    )
    
        embeddings_list = embedded_table['formatted_embeddings'].tolist()
        response = self.supabase_client.rpc(rpc_function, {
                        "input_vectors": embeddings_list
                    }).execute()
        results_df = pd.DataFrame(response.data)
        # 'results_df' now has one result per original embedding.
        # 'idx' corresponds to the embedding index in embeddings_list.
        results_df.sort_values('idx', inplace=True)

        # Merge the results back into your main DataFrame
        embedded_table = embedded_table.reset_index(drop=True)
        final_df = pd.concat([embedded_table, results_df[['match_value', 'new_code', 'sim_score']]], axis=1)
        final_df['sim_score'] = 1 - final_df['sim_score']
        return final_df

    
    def results_filter(self,match_response):
        match_threshold = .93
        filtered_df = match_response.loc[match_response.groupby("new_code")["sim_score"].idxmax()]
        thresh_filtered_df = filtered_df[filtered_df['sim_score'] > match_threshold]
        return thresh_filtered_df
    

    def column_picker(self,full_filt_db):
        full_filt_db['return_col'] =   full_filt_db['new_code'] + " - " + full_filt_db['match_value']
        retDB = full_filt_db['return_col']
        #df_no_headers_index = retDB.to_string(header=False, index=False)
        return retDB



    def icd_main(self, input_text):
        # Instantiate the ruleCreator with a prompt template that can be changed
        prompt_template = '''
        Provide all relevant ICD codes for {input_text}.  

        If no appropriate ICD codes exist or the information is not available, return 'none' without adding any explanation.  

        Ensure the response is formatted as follows, with no headers or additional text:  

        Code | Description  

        For example:  
        B21 | HIV disease resulting in opportunistic infection  
        E11.9 | Type 2 diabetes mellitus without complications  
        ...  

        All ICD codes related to the condition must be included in this format. 
        '''

        rc = llm_match(prompt_template=prompt_template)
        response_text = ""  # Buffer to hold the streamed response
        for chunk in rc.query_openai_streaming(input_text):
            response_text += chunk
            yield chunk # Print dynamically to see progress
        return response_text

    def icd_post_processing(self, ai_output):
    
        if ai_output != 'None' and ai_output != 'none':
            table_response = self.data_table_creator(ai_output)
            #print(table_response)
            embedded_table = self.process_table(table_response=table_response)
            #print(embedded_table)
            #match = rc.match_over_table(df = embedded_table)
            match = self.match_over_table_bulk(embedded_table=embedded_table, rpc_function= "find_most_similar_bulk")
            #print(match)
            fin = self.column_picker(self.results_filter(match))

            return fin
        else:
            return 'No match'
        

    def cpt_main(self, input_text):
        # Instantiate the ruleCreator with a prompt template that can be changed
        prompt_template = '''
        Provide all relevant CPT codes for {input_text}. 

        If no appropriate CPT codes exist or the information is not available, return 'none' without adding any explanation.

        Ensure the response is formatted as follows, with no headers or additional text:

        Code | Description

        For example:
        61510 | Craniectomy or craniotomy for excision of brain tumor, supratentorial, except meningioma
        61512 | Craniectomy or craniotomy for excision of meningioma, supratentorial
        ...

        All CPT codes related to the procedure must be included in this format.
        
        '''

        rc = llm_match(prompt_template=prompt_template)
        response_text = ""  # Buffer to hold the streamed response
        for chunk in rc.query_openai_streaming(input_text):
            response_text += chunk
            yield chunk # Print dynamically to see progress
        return response_text

    def cpt_post_processing(self, ai_output):
    
        if ai_output != 'None' and ai_output != 'none':
            table_response = self.data_table_creator(ai_output)
            embedded_table = self.process_table(table_response=table_response)
            match = self.match_over_table_bulk(embedded_table=embedded_table, rpc_function= "find_most_similar_bulk_cpt")
            #print(match)
            fin = self.column_picker(self.results_filter(match))


            return fin
        else:
            return 'No match'

        
if __name__ == "__main__":
    input_text = input('enter:')
    match_inst = llm_match()
    match_response = match_inst.icd_main(input_text)
    filtered_response = match_inst.icd_post_processing(ai_output = match_response)                                               
    #print(match_response)