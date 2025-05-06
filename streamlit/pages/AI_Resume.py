import streamlit as st
import os 
from io import StringIO
import pandas as pd
import sys
from PyPDF2 import PdfReader
from docx import Document
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..function')))


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
            elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
                doc = Document(uploaded_file)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                st.write(text)
            else:
                st.error("Unsupported file type. Please upload a PDF or Word document.")

    with col3:
        if st.button("Simulate!", use_container_width=True):
            ev = mtg_box_sim.simulate(f"{set}", int(boxes_to_open))
            # Add to history
            st.session_state.ev_history.append({
                "Set": set,
                "Boxes Opened": int(boxes_to_open),
                "EV": round(ev, 2)
            })
        if st.button("clear",use_container_width=True ):
            st.session_state.ev_history = []
