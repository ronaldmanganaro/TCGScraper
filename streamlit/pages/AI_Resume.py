import streamlit as st
import os 
from io import StringIO
import pandas as pd
import sys
from PyPDF2 import PdfReader

st.title("AI Tools")
with st.expander("Augment Resume"):
    st.divider()
    # Initialize session state to store EV results
    if 'ev_history' not in st.session_state:
        st.session_state.ev_history = []

    # Initialize options in session state
    if "options" not in st.session_state:
        st.session_state.options = []

    # Create 3 columns
    col1, col2, col3 = st.columns([2, 3, 1])

    # Inputs and button
    with col1:
        url = st.text_input("Job URL",placeholder="https://indeed.com/some_job")

    with col2:
        uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "docx"])
        if uploaded_file is not None:
            if uploaded_file.type == "application/pdf":
                pdf_reader = PdfReader(uploaded_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                st.write(text)
            else:
                st.error("Unsupported file type. Please upload a PDF or Word document.")

    with col3:
        if st.button("Simulate!", use_container_width=True):
            pass
