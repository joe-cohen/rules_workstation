import streamlit as st
from code_match_llm import llm_match 

# Define your function that processes the input
def process_input(user_input: str) -> str:
    match_inst = llm_match()
    func_output = match_inst.main(input_text = user_input)
    # Example function that just echoes the input with some modification
    # Replace this with your actual logic
    return func_output

st.title("cohere code match")

# Text input for user
user_input = st.text_input("Enter your text:")

# When user clicks this button, we run the process_input function

if st.button("Run Function") and len(user_input)>=1:
    result = process_input(user_input)
    st.session_state["result"] = result

# Display the output if available
if "result" in st.session_state:
    st.write("Output:")
    st.table(st.session_state["result"])
    
    # Button to copy the output to clipboard (using Streamlit's experimental feature)
    # Note: As of Streamlit 1.19, st.write can be used with `st.text_area` to copy easily.
    # For a direct "copy to clipboard" button, we'd rely on JavaScript or st.markdown hacks.
    # Below is a workaround using markdown and html. Please note that this might not work in 
    # all environments due to security restrictions.
    
    copy_js = f"""
    <script>
    function copyToClipboard(text) {{
        navigator.clipboard.writeText(text);
        alert('Copied to clipboard');
    }}
    </script>
    """
    st.markdown(copy_js, unsafe_allow_html=True)
    st.markdown(f'<button onclick="copyToClipboard(\'{st.session_state["result"]}\')">Copy Output</button>', unsafe_allow_html=True)
