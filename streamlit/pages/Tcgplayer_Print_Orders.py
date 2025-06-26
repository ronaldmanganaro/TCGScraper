# make a streamlit page that reads a pdf file and extracts all the shiopping information from it as well as the otrder date shipping method buyyer name seller name and qunatitiya nd descipt price and total price
import streamlit as st
from PyPDF2 import PdfReader
import re
import pandas as pd
from datetime import datetime
from pdf2image import convert_from_path
from PIL import Image
from st_copy_to_clipboard import st_copy_to_clipboard
import usaddress
from functions import widgets   

def preprocess_text(text):
    # Remove boilerplate and repeated seller info (all occurrences, flexible pattern)
    boilerplate_pattern = (
        r"ForAny Questions About Your Order:.*?feedback foryour order\."  # match everything between these phrases
    )
    text = re.sub(boilerplate_pattern, "", text, flags=re.DOTALL | re.IGNORECASE)
    # Remove 'Thank you...' and 'Holo HitsTCG' everywhere
    text = re.sub(r"Thank youforbuying from Holo HitsTCG onTCGplayer.com\.?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Holo HitsTCG", "", text, flags=re.IGNORECASE)
    # Add newline after each field label if not present
    labels = [
        "Order Number:", "Shipping Address:", "Order Date:",
        "Shipping Method:", "Buyer Name:", "Seller Name:"
    ]
    for label in labels:
        text = re.sub(f"({label})(?!\\s*\\n)", r"\1\n", text)
    return text

def extract_order_info(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"

    # Preprocess text to add newlines after field labels
    text = preprocess_text(text)

    # Regular expressions to match the required fields
    shipping_method_pattern = r"Shipping Method:\s*([^\n]+)"
    buyer_name_pattern = r"Buyer Name:\s*([^\n]+)"
    seller_name_pattern = r"Seller Name:\s*([^\n]+)"
    item_pattern = r"Item:\s*([^\n]+)\s*Quantity:\s*(\d+)\s*Price:\s*\$([\d,.]+)\s*Total Price:\s*\$([\d,.]+)"

    # Try to extract order date after 'Order Date:' or after 'Seller Name:'
    order_date = None
    order_date_match = re.search(r"Order Date:\s*(\d{2}/\d{2}/\d{4})", text)
    if order_date_match:
        order_date = order_date_match.group(1)
    else:
        # Try after Seller Name:
        seller_name_match = re.search(r"Seller Name:\s*([^\n]+)\n(\d{2}/\d{2}/\d{4})", text)
        if seller_name_match:
            order_date = seller_name_match.group(2)

    shipping_method_match = re.search(shipping_method_pattern, text)
    buyer_name_match = re.search(buyer_name_pattern, text)
    seller_name_match = re.search(seller_name_pattern, text)

    shipping_method = shipping_method_match.group(1) if shipping_method_match else "N/A"
    buyer_name = buyer_name_match.group(1) if buyer_name_match else "N/A"
    seller_name = seller_name_match.group(1) if seller_name_match else "N/A"

    items = []
    for match in re.finditer(item_pattern, text):
        item_desc, quantity, price, total_price = match.groups()
        items.append({
            "Description": item_desc.strip(),
            "Quantity": int(quantity),
            "Price": float(price.replace(',', '')),
            "Total Price": float(total_price.replace(',', ''))
        })

    return {
        "Order Date": datetime.strptime(order_date, "%m/%d/%Y") if order_date else None,
        "Shipping Method": shipping_method,
        "Buyer Name": buyer_name,
        "Seller Name": seller_name,
        "Items": items
    }, text

def extract_orders_from_text(text):
    # Split only on 'Order Number:' at the start of a line (not after 'Ship To:' etc)
    blocks = re.split(r'^Order Number:', text, flags=re.MULTILINE)
    orders = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        block = 'Order Number:' + block  # Add back the label
        # Only process if block contains a valid order number and a date
        if not re.search(r'Order Number:\s*[\w\- ]+', block):
            continue
        if not re.search(r'\d{2}/\d{2}/\d{4}', block):
            continue
        # Extract fields
        order_number = re.search(r'Order Number:\s*([\w\- ]+)', block)
        shipping_address = re.search(r'Shipping Address:\s*([\s\S]*?)Order Date:', block)
        order_date = re.search(r'(\d{2}/\d{2}/\d{4})', block)
        # Improved Shipping Method extraction
        shipping_method = 'N/A'
        shipping_method_match = re.search(r'Shipping Method:(.*)', block)
        if shipping_method_match:
            after_shipping = block[shipping_method_match.end():]
            for line in after_shipping.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Skip if line is a label or a date
                if line.endswith(':') or re.match(r'\d{2}/\d{2}/\d{4}', line):
                    continue
                if line.lower() in ['buyer name:', 'seller name:']:
                    continue
                shipping_method = line
                break
        if not shipping_method:
            shipping_method_match = re.search(r'Shipping Method:\s*\n([^\n]+)', block)
            shipping_method = shipping_method_match.group(1).strip() if shipping_method_match else 'N/A'
        # Items: look for lines with pattern: quantity description $price $total
        # Improved item extraction: handle multiline descriptions
        items = []
        # Only extract items after the 'Quantity Description Price Total Price' header
        items_section = ''
        items_header_match = re.search(r'Quantity Description Price Total Price', block)
        if items_header_match:
            items_section = block[items_header_match.end():]
        item_pattern = re.compile(
            r'^(?P<qty>\d+)\s+(?P<desc>(?:[^$\n]*\n?)+?)\$?(?P<price>[\d,.]+)\s*\$?(?P<total>[\d,.]+)$',
            re.MULTILINE
        )
        card_items = []
        sealed_items = []
        for m in item_pattern.finditer(items_section):
            quantity = int(m.group('qty'))
            description = m.group('desc').replace('\n', ' ').replace('\r', '').strip()
            # Skip summary lines like 'Total'
            if description.strip().lower() == 'total':
                continue
            price = float(m.group('price').replace(',', ''))
            total = float(m.group('total').replace(',', ''))

            # Parse single card details if possible
            set_name = card_name = collector_number = rarity = condition = ''
            is_card = False
            if description.startswith('Magic -') and not re.search(r'(Unopened|Sealed)', description, re.IGNORECASE):
                desc_parts = description[len('Magic -'):].split(' -')
                # Improved: Try to robustly extract collector number, rarity, and condition
                set_name = card_name = collector_number = rarity = condition = ''
                if len(desc_parts) >= 2:
                    set_name = desc_parts[0].strip()
                    card_name = desc_parts[1].strip()
                # Look for collector number, rarity, and condition in the remaining parts
                for part in desc_parts[2:]:
                    part = part.strip()
                    # Collector number: starts with # or is all digits/letters
                    if not collector_number and (part.startswith('#') or re.match(r'^[\w\-]+$', part)):
                        collector_number = part.lstrip('#').strip()
                        continue
                    # Rarity and condition: look for e.g. 'R- Near Mint' or 'Near Mint'
                    if '-' in part:
                        rar, cond = part.split('-', 1)
                        rarity = rar.strip()
                        condition = cond.strip()
                    elif not rarity and part in ['Common', 'Uncommon', 'Rare', 'Mythic', 'R', 'U', 'C', 'M']:
                        rarity = part
                    elif not condition:
                        condition = part
                card_items.append({
                    'Quantity': quantity,
                    'Set Name': set_name,
                    'Card Name': card_name,
                    'Collector Number': collector_number,
                    'Rarity': rarity,
                    'Condition': condition,
                    'Price': price,
                    'Total Price': total
                })
                is_card = True
            if not is_card:
                sealed_items.append({
                    'Quantity': quantity,
                    'Description': description,
                    'Price': price,
                    'Total Price': total
                })
        shipping_address_block = shipping_address.group(1).strip() if shipping_address else 'N/A'
        # Split shipping address into 3 lines: name, street, city/state/zip
        address_lines = [line.strip() for line in shipping_address_block.split('\n') if line.strip()]
        # Fix name capitalization (e.g., RoyDeWitt -> Roy Dewitt, Roy De Witt -> Roy Dewitt)
        def fix_name(name):
            # Remove extra spaces, split on capital letters, then join and title-case
            name = re.sub(r'\s+', '', name)
            name = re.sub(r'(?<!^)([A-Z])', r' \1', name)
            # Special case: join 'De Witt' and similar to 'Dewitt'
            name = re.sub(r'\bDe\s+Witt\b', 'Dewitt', name, flags=re.IGNORECASE)
            return name.title().strip()
        name = fix_name(address_lines[0]) if len(address_lines) > 0 else ''
        # Improved address parsing to handle apartment/unit numbers on their own line
        street = ''
        apt = ''
        city_state_zip = ''
        if len(address_lines) == 2:
            # Only street and city/state/zip
            street = address_lines[1]
        elif len(address_lines) == 3:
            # Street, city/state/zip, or street, apt, city/state/zip
            if re.match(r'^[\d\w\-]+$', address_lines[2].replace(',', '').strip()):
                # If the third line is just a number or unit, treat as apt/unit
                street = address_lines[1]
                apt = address_lines[2]
            else:
                street = address_lines[1]
                city_state_zip = address_lines[2]
        elif len(address_lines) >= 4:
            # Street, apt/unit, city/state/zip
            street = address_lines[1]
            apt = address_lines[2]
            city_state_zip = address_lines[3]
        else:
            street = ''
            city_state_zip = ''
        # Combine street and apt/unit if present
        if apt:
            street = f"{street}, {apt}".strip(', ')
        if not city_state_zip and len(address_lines) > 2:
            city_state_zip = address_lines[-1]
        # Only split street number and name if joined (e.g., 821EMosier St -> 821 E Mosier St)
        street_match = re.match(r'^(\d+)([A-Za-z].*)$', street)
        if street_match and not street.startswith(' '):
            street_number = street_match.group(1)
            street_name = street_match.group(2)
            # Only add space if not already present
            if not street_name.startswith(' '):
                street = f"{street_number} {street_name.strip()}"
        # Do NOT add extra spaces or replace 'St' with ' St'
        # Split city_state_zip into city, state, zip
        city, state, zip_code = '', '', ''
        city_state_zip_match = re.match(r'^(.*?),\s*([A-Z]{2})([\d\- ]+)$', city_state_zip.replace(' ', ''))
        if city_state_zip_match:
            city = city_state_zip_match.group(1)
            state = city_state_zip_match.group(2)
            zip_code_raw = city_state_zip_match.group(3).replace(' ', '').replace('-', '')
            # Format zip with hyphen if 9 digits
            if len(zip_code_raw) == 9 and zip_code_raw.isdigit():
                zip_code = f"{zip_code_raw[:5]}-{zip_code_raw[5:]}"
            else:
                zip_code = zip_code_raw
        else:
            city = city_state_zip
        orders.append({
            'Order Number': order_number.group(1).strip() if order_number else 'N/A',
            'Shipping Name': name,
            'Shipping Street': street,
            'Shipping City': city,
            'Shipping State': state,
            'Shipping Zip': zip_code,
            'Order Date': order_date.group(1) if order_date else None,
            'Shipping Method': shipping_method,
            'Card Items': card_items,
            'Sealed Items': sealed_items
        })
    return orders

def main():
    if 'clear_orders' not in st.session_state:
        st.session_state['clear_orders'] = False
    st.title("Tcgplayer Print Orders Extractor")
    st.write("Upload a PDF file containing Tcgplayer order details to extract information.")

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    if st.session_state['clear_orders']:
        st.session_state['removed_orders'] = set()
        st.session_state['clear_orders'] = False
        st.rerun()
    if uploaded_file is not None:
        with open("temp_order.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        # Get preprocessed text
        _, extracted_text = extract_order_info("temp_order.pdf")
        # Extract all orders
        orders = extract_orders_from_text(extracted_text)
        # Track removed orders in session state
        if 'removed_orders' not in st.session_state:
            st.session_state['removed_orders'] = set()
        # Only show orders not removed
        visible_orders = [order for order in orders if order['Order Number'] not in st.session_state['removed_orders']]
        for idx, order in enumerate(visible_orders, 1):
            with st.expander(f"Order {idx}: {order['Order Number']}", expanded=False):
                processed = st.checkbox(f"Processed", key=f"processed_{idx}")
                st.markdown(f"**Order Date:** `{order['Order Date']}`  ")
                # Shipping Method dropdown
                shipping_options = [order['Shipping Method'], '2-3 Days Tracked Shipment']
                shipping_options = list(dict.fromkeys([opt for opt in shipping_options if opt and opt != 'N/A']))  # Remove duplicates and N/A
                selected_shipping_method = st.selectbox(
                    "Shipping Method:",
                    options=shipping_options,
                    index=0,
                    key=f"shipping_method_{idx}"
                )
                st.markdown("**Shipping Address:**")
                shipping_label = f"{order['Shipping Name']}\n{order['Shipping Street']}\n{order['Shipping City']}, {order['Shipping State']} {order['Shipping Zip']}"
                # Make shipping address editable
                edited_address = st.text_area(
                    "Edit Shipping Address:",
                    value=shipping_label,
                    key=f"shipping_address_{order['Order Number']}"
                )
                # Use streamlit-copy-to-clipboard for a copy button
                st_copy_to_clipboard(
                    edited_address,
                    "Copy Address to Clipboard",
                    key=f"copy_address_{order['Order Number']}"
                )
                # Validate shipping address using usaddress
                address_valid = None
                address_message = ""
                try:
                    # usaddress tag returns a dict of address components and a label
                    parsed, address_type = usaddress.tag(edited_address)
                    required_fields = ["AddressNumber", "StreetName", "PlaceName", "StateName", "ZipCode"]
                    missing = [field for field in required_fields if field not in parsed]
                    if not missing:
                        address_valid = True
                        address_message = ":white_check_mark: Address appears valid (usaddress)."
                    else:
                        address_valid = False
                        address_message = f":warning: Address missing fields: {', '.join(missing)}"
                except usaddress.RepeatedLabelError as e:
                    address_valid = False
                    address_message = f":warning: Address parsing error: {e}"
                except Exception as e:
                    address_valid = False
                    address_message = f":warning: Address validation error: {e}"
                # Show address validation as warning/info instead of markdown
                if address_valid is True:
                    st.info(address_message)
                else:
                    st.warning(address_message)
                # Show cropped PDF region for cards ordered, just below the edit shipping address
                pdf_path = "streamlit/temp_order.pdf"  # or the path to the current PDF
                try:
                    # Each order is on its own page: idx is 1-based for expander, so use idx for page number
                    pages = convert_from_path(pdf_path, dpi=200, first_page=idx, last_page=idx)
                    img = pages[0]
                    # Use the exact crop numbers provided for each page
                    crop_left = 92
                    crop_top = 543
                    crop_right = 1612
                    crop_bottom = 820
                    cropped = img.crop((crop_left, crop_top, crop_right, crop_bottom))
                    st.image(cropped,  use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not render card images: {e}")
                if order['Card Items']:
                    st.markdown("**Cards Ordered:**")
                    items_df = pd.DataFrame(order['Card Items'])
                    st.dataframe(items_df, use_container_width=True, hide_index=True)
                    total_order_price = items_df["Total Price"].sum()
                    st.markdown(f"**Total Card Order Price:** `${{total_order_price:.2f}}`")
                if order['Sealed Items']:
                    st.markdown("**Sealed/Unopened Products:**")
                    sealed_df = pd.DataFrame(order['Sealed Items'])
                    st.dataframe(sealed_df, use_container_width=True, hide_index=True)
                    total_sealed_price = sealed_df["Total Price"].sum()
                    st.markdown(f"**Total Sealed Order Price:** `${total_sealed_price:.2f}`")
                if not order['Card Items'] and not order['Sealed Items']:
                    st.info("No items found for this order.")
                # Add Remove Order button at the bottom
                if st.button(f"Remove Order", key=f"remove_order_{order['Order Number']}"):
                    st.session_state['removed_orders'].add(order['Order Number'])
                    st.rerun()
        
        # Add Print Shipping Labels, Clear Orders, and Clear Processed Orders buttons at the bottom
        if orders:
            col1, col2, col3 = st.columns([0.4, 0.3, 0.3], gap="small")
            with col1:
                if st.button("Print Shipping Labels", use_container_width=True):
                    st.markdown("## Shipping Labels")
                    for idx, order in enumerate(orders, 1):
                        st.markdown(f"**Order {idx}:**")
                        st.markdown(
                            f"{order['Shipping Name']}<br>{order['Shipping Street']}<br>{order['Shipping City']}, {order['Shipping State']} {order['Shipping Zip']}",
                            unsafe_allow_html=True
                        )
                        st.markdown("---")
            with col2:
                if st.button("Clear Orders", use_container_width=True):
                    st.session_state['clear_orders'] = True
                    st.rerun()
            with col3:
                if st.button("Clear Processed Orders", use_container_width=True):
                    # Remove all orders marked as processed
                    to_remove = set()
                    for idx, order in enumerate(visible_orders, 1):
                        if st.session_state.get(f"processed_{idx}"):
                            to_remove.add(order['Order Number'])
                    st.session_state['removed_orders'].update(to_remove)
                    st.rerun()
    
if __name__ == "__main__":
    main()

widgets.show_pages_sidebar()
widgets.footer()