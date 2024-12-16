import streamlit as st
from code_match_llm import llm_match 
import pandas as pd
import re

# Define your function that processes the input
def process_input(user_input: str):
    match_inst = llm_match()
    cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', '', user_input)
    
    # Select the appropriate generator function
    if st.session_state.search_type == "icd":
        generator = match_inst.icd_main(input_text=user_input)
    elif st.session_state.search_type == "cpt":
        generator = match_inst.cpt_main(input_text=user_input)
    
    # Stream output to the Streamlit UI
    output_placeholder = st.empty()  # Create a placeholder for dynamic updates
    full_output = ""  # Buffer to store the cumulative response

    # Iterate over the generator to get chunks and update Streamlit dynamically
    for chunk in generator:
        full_output += chunk  # Append the new chunk to the full response
        output_placeholder.text_area("Output", value=full_output, height=400)  # Update the placeholder dynamically

    with st.spinner("Cross- referencing..."):
        if st.session_state.search_type == "cpt":
            filtered_response = match_inst.cpt_post_processing(full_output)
        if st.session_state.search_type == "icd":
            filtered_response = match_inst.icd_post_processing(full_output)
            
    clipboard_data = '\n'.join(str(item) for item in filtered_response)
    output_placeholder.text_area("Output (Post-Processed)", value=clipboard_data, height=400)

    return full_output

st.title("cohere ICD code match")
if "search_type" not in st.session_state:
    st.session_state.search_type = "icd"  # Default value

col1, col2 = st.columns([1,3])
with col1:
    st.session_state.search_type = st.selectbox("searching for", ("icd", "cpt"))
with col2:
# Text input for user
    user_input = st.text_input("Enter the description to match:")

# When user clicks this button, we run the process_input function

if st.button("Run Code Match") and len(user_input)>=1:
    result = process_input(user_input)
    st.session_state["result"] = result
    
