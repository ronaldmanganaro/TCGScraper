import streamlit as st
import requests
import io
from PIL import Image
from pdf2image import convert_from_bytes
from functions import widgets

API_URL = "http://172.17.0.3:80/crop-pdf/"  # Change to your FastAPI endpoint

widgets.show_pages_sidebar()

st.title("PDF Cropper (FastAPI Backend)")

pdf_file = st.file_uploader("Upload PDF", type="pdf")

if pdf_file:
    # For UI, get the first page size locally (optional, for slider range)

    pages = convert_from_bytes(pdf_file.read(), dpi=200, first_page=1, last_page=1)
    img = pages[0]
    width, height = img.size
    st.image(img, caption="Full Page", use_column_width=True)

    st.markdown("### Adjust Crop Region")
    left = st.slider("Left", 0, width, 0)
    upper = st.slider("Top", 0, height, 0)
    right = st.slider("Right", 0, width, width)
    lower = st.slider("Bottom", 0, height, height)

    # Reset file pointer for upload
    pdf_file.seek(0)

    if right > left and lower > upper:
        if st.button("Crop via FastAPI"):
            files = {"pdf": pdf_file}
            data = {
                "left": left,
                "upper": upper,
                "right": right,
                "lower": lower,
                "page": 1,
            }
            response = requests.post(API_URL, files=files, data=data)
            if response.status_code == 200:
                cropped_img = Image.open(io.BytesIO(response.content))
                st.image(cropped_img, caption="Cropped Region (from FastAPI)", use_column_width=True)
            else:
                st.error(f"FastAPI error: {response.text}")
    else:
        st.warning("Right must be greater than Left and Bottom must be greater than Top.")

widgets.footer()
