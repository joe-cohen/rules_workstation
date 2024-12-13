import streamlit as st
from code_match_llm import llm_match 
import pyperclip
import pandas as pd

# Define your function that processes the input
def process_input(user_input: str) -> str:
    match_inst = llm_match()
    func_output = match_inst.main(input_text = user_input)
    # Example function that just echoes the input with some modification
    # Replace this with your actual logic
    return func_output

st.title("cohere ICD code match")

# Text input for user
user_input = st.text_input("Enter your text:")

# When user clicks this button, we run the process_input function

if st.button("Run Function") and len(user_input)>=1:
    result = process_input(user_input)
    st.session_state["result"] = result

# Display the output if available
if "result" in st.session_state:
    st.write("Output:")
    data = st.session_state["result"].values.tolist()
    
    clipboard_data = '\n'.join(str(item) for item in data)
    st.table(data)

    

    #st.markdown(copy_js, unsafe_allow_html=True)
    if st.button("Copy to Clipboard"):
        pyperclip.copy(clipboard_data)
