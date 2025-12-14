from functions import widgets
from pathlib import Path
from io import BytesIO
import streamlit as st
import csv
import usaddress

from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

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
        c.setFont("Helvetica", 10)
        ra_lines = return_address.split("\n")
        for i, line in enumerate(ra_lines):
            c.drawString(0.3 * inch, 3.6 * inch - i * 12, line)

        stamp_box_top = 3.0 * inch
        c.setLineWidth(2)
        c.rect(label_width - 0.3 * inch - 0.85 * inch, stamp_box_top, 0.85 * inch, 0.85 * inch)
        c.setFont("Helvetica", 9)
        stamp_x = label_width - 0.3 * inch - 0.85 * inch / 2
        stamp_y = stamp_box_top + 0.85 * inch / 2 - 6
        c.drawCentredString(stamp_x, stamp_y, "STAMP HERE")

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

def main():
    if "clear_orders" not in st.session_state:
        st.session_state["clear_orders"] = False
    # Track address validity across reruns
    if "return_address_valid" not in st.session_state:
        st.session_state["return_address_valid"] = False

    st.title("Tcgplayer Print Orders – CSV to 6x4 Label PDF")
    st.write("Upload a TCGplayer shipping CSV to generate a printable 6x4 labels PDF.")

    # --- Return Address with US validation ---
    with st.expander("Return Address", expanded=True):
        user_logged_in = st.session_state.get("current_user")

        # Do NOT clear return_address for guests; just avoid loading/saving from DB
        if user_logged_in and st.session_state.get("reload_return_address"):
            _, _, db_return_address = widgets.get_user_data_db(st.session_state["current_user"])
            st.session_state["return_address"] = db_return_address or ""
            del st.session_state["reload_return_address"]

        if user_logged_in and "return_address" not in st.session_state:
            _, _, db_return_address = widgets.get_user_data_db(st.session_state["current_user"])
            st.session_state["return_address"] = db_return_address or ""

        return_address = st.text_area("", key="return_address", height=100)

        # Default to invalid until we prove it's good
        st.session_state["return_address_valid"] = False
        if return_address.strip():
            try:
                parsed, address_type = usaddress.tag(return_address)
                required_fields = ["AddressNumber", "StreetName", "PlaceName", "StateName", "ZipCode"]
                missing = [field for field in required_fields if field not in parsed]
                if not missing:
                    st.session_state["return_address_valid"] = True
                    st.info(":white_check_mark: Return address appears valid (usaddress).")
                else:
                    st.warning(f":warning: Return address is missing fields: {', '.join(missing)}")
            except usaddress.RepeatedLabelError as e:
                st.warning(f":warning: Return address parsing error: {e}")
            except Exception as e:
                st.warning(f":warning: Return address validation error: {e}")
        else:
            # Empty field is invalid
            st.warning("Please enter a return address.")

        if user_logged_in and st.button("Save Return Address", key="save_return_address_btn"):
            widgets.save_user_data_db(
                st.session_state["current_user"],
                st.session_state.get("saved_rules", []),
                st.session_state.get("rule_templates", []),
                st.session_state["return_address"],
            )
            st.success("Return address saved!")

    # --- CSV upload -> labels PDF ---
    uploaded_file = st.file_uploader("Choose a Shipping CSV", type="csv")

    if st.session_state["clear_orders"]:
        st.session_state["removed_orders"] = set()
        st.session_state["clear_orders"] = False
        st.rerun()

    elif uploaded_file is not None:
        # Before doing any work, enforce a valid return address
        if not st.session_state.get("return_address_valid", False):
            st.error("Return address is not valid. Please correct it above before generating labels.")
            return

        data_dir = Path(__file__).parents[1] / "data" / "tcgplayer"
        data_dir.mkdir(parents=True, exist_ok=True)
        temp_csv_path = data_dir / "uploaded_shipping.csv"
        with temp_csv_path.open("wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            orders_for_labels = create_labels_excel(temp_csv_path)
        except Exception as e:
            st.error(f"Failed to parse CSV: {e}")
            return

        return_address = st.session_state.get("return_address", "").strip()
        # Log for debugging: show what Streamlit sees
        if not return_address:
            st.warning("Please enter a return address above before generating labels.")
            return

        pdf_buffer: BytesIO = create_labels_pdf(orders_for_labels, return_address)

        st.download_button(
            label="Download Shipping Labels PDF",
            data=pdf_buffer,
            file_name="shipping_labels.pdf",
            mime="application/pdf",
            use_container_width=True,
            disabled=not st.session_state.get("return_address_valid", False),
        )


if __name__ == "__main__":
    main()
    widgets.show_pages_sidebar()
    widgets.footer()