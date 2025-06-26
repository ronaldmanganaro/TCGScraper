import streamlit as st
from pdf2image import convert_from_path
from PIL import Image
import tempfile
from functions import widgets

# Upload PDF
pdf_file = st.file_uploader("Upload PDF", type="pdf")

if pdf_file:
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(pdf_file.read())
        temp_pdf_path = tmp_file.name

    # Convert first page to image
    pages = convert_from_path(temp_pdf_path, dpi=200, first_page=1, last_page=1)
    img = pages[0]
    width, height = img.size

    st.image(img, caption="Full Page", use_column_width=True)

    st.markdown("### Adjust Crop Region")

    # Sliders to select crop box
    left = st.slider("Left", 0, width, 0)
    upper = st.slider("Top", 0, height, 0)
    right = st.slider("Right", 0, width, width)
    lower = st.slider("Bottom", 0, height, height)

    if right > left and lower > upper:
        cropped = img.crop((left, upper, right, lower))
        st.image(cropped, caption=f"Cropped Region ({left}, {upper}, {right}, {lower})", use_container_width=True)
    else:
        st.warning("Right must be greater than Left and Bottom must be greater than Top.")

widgets.show_pages_sidebar()
widgets.footer()
