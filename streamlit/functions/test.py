import db
import csv
from pathlib import Path
from io import BytesIO
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

"""
card_info_list: List of (name, collector_number, set)
Returns: dict mapping (name, collector_number, set) -> tcgplayer_card_id
"""
cards = [
    ("Ancestor's Chosen", "1", "10e", True),
    ("Ancestor's Chosen", "1", "10e", False),
]

conn = db.connectDB("scryfall")
cur = conn.cursor()
try:
    # Build WHERE clause for batch query
    format_strings = ','.join(['(%s,%s,%s,%s)'] * len(cards))
    params = []
    for name, collector_number, set, foil in cards:
        print(name, collector_number, set, foil)
        params.extend([name, collector_number, set, foil])
    
    query = f"""
        SELECT name, collector_number, set, foil, tcgplayer_id FROM scryfall
        WHERE (name, collector_number, set, foil) IN ({format_strings})
    """
    cur.execute(query, params)
    results = cur.fetchall()
    lookup = {}
    for name, collector_number, set, foil, tcgplayer_card_id in results:
        if tcgplayer_card_id is not None:
            lookup[(name, collector_number, set, foil)] = tcgplayer_card_id
    print(lookup) 
finally:
    cur.close()
    conn.close()


def create_labels_excel(shipping_csv: Path | None = None) -> list[str]:
    """Read TCGplayer_ShippingExport.csv and return one multi-line address string per order."""
    if shipping_csv is None:
        shipping_csv = Path(__file__).parents[1] / "data" / "TCGplayer_ShippingExport.csv"
    else:
        shipping_csv = Path(shipping_csv)

    parsed_orders: list[str] = []

    with shipping_csv.open(mode="r", newline="", encoding="utf-8") as f:
        orders = csv.DictReader(f)

        for order in orders:
            first_name = order.get("FirstName", "").strip()
            last_name = order.get("LastName", "").strip()
            address1 = order.get("Address1", "").strip()
            address2 = order.get("Address2", "").strip()
            city = order.get("City", "").strip()
            state = order.get("State", "").strip()
            zip_code = order.get("PostalCode", "").strip()

            # Build address lines without extra blank line when address2 is empty
            lines: list[str] = [
                f"{first_name} {last_name}".strip(),
                address1,
            ]
            if address2:
                lines.append(address2)
            lines.append(f"{city}, {state} {zip_code}".strip())

            shipping_address = "\n".join(l for l in lines if l)
            parsed_orders.append(shipping_address)

    return parsed_orders


def create_labels_pdf(orders: list[str], return_address: str) -> BytesIO:
    """Create a labels PDF from a list of multi-line shipping address strings."""
    buffer = BytesIO()
    label_width, label_height = 6 * inch, 4 * inch
    c = canvas.Canvas(buffer, pagesize=landscape((label_width, label_height)))

    for order in orders:
        # Return address block
        c.setFont("Helvetica", 10)
        ra_lines = return_address.split("\n")
        for i, line in enumerate(ra_lines):
            c.drawString(0.3 * inch, 3.6 * inch - i * 12, line)

        # Stamp box
        stamp_box_top = 3.0 * inch
        c.setLineWidth(2)
        c.rect(label_width - 0.3 * inch - 0.85 * inch, stamp_box_top, 0.85 * inch, 0.85 * inch)
        c.setFont("Helvetica", 9)
        stamp_x = label_width - 0.3 * inch - 0.85 * inch / 2
        stamp_y = stamp_box_top + 0.85 * inch / 2 - 6
        c.drawCentredString(stamp_x, stamp_y, "STAMP HERE")

        # Shipping address (order is already multi-line string)
        ship_address = order
        c.setFont("Helvetica-Bold", 12)
        lines: list[str] = []
        for line in ship_address.split("\n"):
            wrapped = simpleSplit(line, "Helvetica-Bold", 12, 5 * inch)
            lines.extend(wrapped)

        total_height = len(lines) * 14
        y_start = 2.1 * inch + total_height / 2
        for i, line in enumerate(lines):
            text_width = c.stringWidth(line, "Helvetica-Bold", 12)
            x = (label_width - text_width) / 2
            y = y_start - i * 14
            c.drawString(x, y, line)

        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer


if __name__ == "__main__":
    orders = create_labels_excel()
    return_address = "My Company\n123 Business Rd.\nBusiness City, BC 12345"

    pdf_buffer = create_labels_pdf(orders, return_address)

    output_path = Path(__file__).with_name("labels.pdf")
    with output_path.open("wb") as f:
        f.write(pdf_buffer.getvalue())

    print(f"Wrote {output_path}")