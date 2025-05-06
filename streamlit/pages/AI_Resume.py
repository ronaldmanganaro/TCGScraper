import streamlit as st
import os 
from io import StringIO
import pandas as pd
import sys
from PyPDF2 import PdfReader

st.title("AI Tools")
with st.expander("Augment Resume"):
    st.divider()

    url = st.text_input("Job URL",placeholder="https://indeed.com/some_job")

    uploaded_file = st.file_uploader("Upload Resume", type=["pdf"])
    if uploaded_file is not None:
        if uploaded_file.type == "application/pdf":
            pdf_reader = PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        else:
            st.error("Unsupported file type. Please upload a PDF or Word document.")

    if st.button("Update Resume!", use_container_width=True):
        pass
