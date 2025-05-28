import streamlit as st
import os 
from io import StringIO
import pandas as pd
import sys
from PyPDF2 import PdfReader
import requests

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
        if uploaded_file is not None and url:
            # Prepare the data to send to the Ollama container
            files = {'resume': uploaded_file.getvalue()}
            data = {'job_url': url}

            # Send the request to the local Ollama container
            try:
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3",
                        "prompt": f"Update this resume for the job at {url}:\n\n{text}"
                    }
                )
                response.raise_for_status()

                # Save the output to a file
                output_file_path = "updated_resume.pdf"
                with open(output_file_path, "wb") as f:
                    f.write(response.content)

                st.success(f"Updated resume downloaded: {output_file_path}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error communicating with Ollama container: {e}")
        else:
            st.error("Please provide both a job URL and a resume.")
        pass
