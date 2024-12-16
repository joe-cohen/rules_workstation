import streamlit as st
from code_match_llm import llm_match 
import pandas as pd
import re

# Define your function that processes the input
def process_input(user_input: str) -> str:
    match_inst = llm_match()
    cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', '', user_input)
    if st.session_state.search_type == "icd":
        func_output = match_inst.icd_main(input_text = user_input)
    elif st.session_state.search_type == "cpt":
        func_output = match_inst.cpt_main(input_text = user_input)
    # Example function that just echoes the input with some modification
    # Replace this with your actual logic
    return func_output

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

# Display the output if available
if "result" in st.session_state:
    if type(st.session_state["result"]) == str:
        st.text_area("Output", value='Not found', height = 300)

    else:
        data = st.session_state["result"].values.tolist()
        
        clipboard_data = '\n'.join(str(item) for item in data)
        st.text_area("Output", value=clipboard_data, height = 300)

    

    #st.markdown(copy_js, unsafe_allow_html=True)
    # if st.button("Copy to Clipboard"):
    #     pyperclip.copy(clipboard_data)
