from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from pdf2image import convert_from_path
import tempfile
import io
router = APIRouter()

@router.post("/crop-pdf/")
async def crop_pdf(
    pdf: UploadFile = File(...),
    left: int = Form(...),
    upper: int = Form(...),
    right: int = Form(...),
    lower: int = Form(...),
    page: int = Form(1)
):
    # Save uploaded PDF to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(await pdf.read())
        temp_pdf_path = tmp_file.name

    # Convert the specified page to image
    pages = convert_from_path(temp_pdf_path, dpi=200, first_page=page, last_page=page)
    img = pages[0]
    cropped = img.crop((left, upper, right, lower))

    # Save cropped image to bytes
    img_bytes = io.BytesIO()
    cropped.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return StreamingResponse(img_bytes, media_type="image/png")