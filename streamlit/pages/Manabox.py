import streamlit as st
from functions import widgets, manabox_db_updater, db
import pandas as pd
import time
import psycopg2
import requests
import logging
import subprocess
import os



def run_playwright_script(url):
    """
    Run the Playwright script as a separate process and retrieve the AddToCart ID.

    Args:
        url (str): The URL of the TCGPlayer product page.

    Returns:
        str: The AddToCart ID if found, else None.
    """
    script_path = os.path.join(os.path.dirname(__file__), '../functions/scrape_playwright.py')
    result = subprocess.run(
        ["python", script_path, url],
        capture_output=True,
        text=True,
        env=os.environ.copy(),  # Pass the current environment variables
        cwd=os.path.dirname(script_path)  # Set the working directory to the script's location
    )
    logging.info(f"Subprocess stdout: {result.stdout.strip()}")
    logging.info(f"Subprocess stderr: {result.stderr.strip()}")
    if result.returncode != 0:
        logging.warning(f"Subprocess failed with return code {result.returncode}")
        return None
    output = result.stdout.strip()
    # Only return output if it looks like an ID (digits), else return None
    if output and output.isdigit():
        return output
    return None

widgets.show_pages_sidebar()

st.title("🧩 ManaBox Converter")
st.markdown("""
Welcome to the ManaBox Converter! This tool allows you to convert your card data into the ManaBox format.
""")
tcgplayer_df = None  # Initialize the DataFrame to avoid reference errors
manabox_csv = st.file_uploader("Upload your card data file", type=[
                               "csv", "json"], key="mana_box_uploader")

# Use session state to cache processed DataFrame for the current upload
if 'manabox_last_filename' not in st.session_state:
    st.session_state['manabox_last_filename'] = None
if 'manabox_tcgplayer_df' not in st.session_state:
    st.session_state['manabox_tcgplayer_df'] = None
if 'manabox_output_csv' not in st.session_state:
    st.session_state['manabox_output_csv'] = None

if manabox_csv is not None:
    # Only process if new file uploaded
    if manabox_csv.name != st.session_state['manabox_last_filename']:
        uploaded_df = pd.read_csv(manabox_csv, index_col=0)
        tcgplayer_data = []
        total_cards = len(uploaded_df)
        progress_bar = st.progress(0, text="Processing card data...")
        required_headers = [
            "TCGplayer Id", "Product Line", "Set Name", "Product Name", "Title", "Number", "Rarity", "Condition",
            "TCG Market Price", "TCG Direct Low", "TCG Low Price With Shipping", "TCG Low Price", "Total Quantity",
            "Add to Quantity", "TCG Marketplace Price", "Photo URL"
        ]
        
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(levelname)s %(message)s')
        
        # Use scryfall_id for all lookups
        card_info_list = [
            # name, collector_number, set_name, foil (True/False)
            (str(card[0]), str(card[3]), str(card[2]), True if str(card[4]).lower() == 'foil' else False)
            for card in uploaded_df.itertuples()
            if pd.notna(card[0]) and pd.notna(card[3]) and pd.notna(card[2]) and pd.notna(card[4])
        ]
        db_lookup = db.batch_get_tcgplayer_ids_by_name_collector_set(card_info_list)
        logging.info(f"DB lookup result: {db_lookup}")
        
        lands = ['Island', 'Mountain', 'Forest', 'Swamp', 'Plains']
        rarity_map = { 
            'common': 'C',
            'uncommon': 'U',
            'rare': 'R',
            'mythic': 'M',
        }
        
        # for each card not found in the db_lookup use scryfall api to update the database
        for idx, card in enumerate(uploaded_df.itertuples()):
            tcgplayer_card_id = None  # Initialize to None for each card
            card_name = card[0]  # Name of the card
            set_symbol = card[1] if len(card) > 1 else ''
            set_name = card[2] if len(card) > 2 else ''
            collector_number = card[3] if len(card) > 3 else ''
            printing = card[4] if len(card) > 4 else ''
            rarity = card[5] if len(card) > 5 else ''
            rarity = rarity_map.get(rarity.lower(), rarity)  # Map rarity to single letter
            quantity = card[6] if len(card) > 6 else ''
            tcg_martket_price = card[9] if len(card) > 9 else ''
            printing = printing.capitalize()  # Capitalize only the first letter
            condition = card[12] if len(card) > 12 else ''
            # Normalize and format condition string
            if condition == "damaged":
                condition = condition.capitalize()
            else:
                # Split at '_' and capitalize each part, then join with spaces
                condition = ' '.join([part.capitalize() for part in condition.split('_')])
                
            if card_name in lands:
                card_name = f"{card_name} (0{collector_number})"
                rarity = 'L'  # Set rarity to 'L' for lands

            lookup_key = (str(card[0]), str(card[3]), str(card[2]))
            if lookup_key not in db_lookup:
                logging.info(f"No TCGplayer ID for card: {card_name} ({set_symbol}), scraping Scryfall...")
                tcgplayer_id = manabox_db_updater.add_single_scryfall_card_to_db(set_symbol, collector_number)
                print(f"DEBUG: tcgplayer_id returned: {(tcgplayer_id)}")
                if tcgplayer_id is not None:
                    url = f"https://www.tcgplayer.com/product/{tcgplayer_id}?Language=English&page=1&Printing={printing}&Condition=Near+Mint"
                    logging.info(f"TCGPlayer URL for {card_name} ({set_symbol}): {url}")
                    tcgplayer_card_id = run_playwright_script(url)
                    logging.info(f"DEBUG: tcgplayer_card_id returned: {repr(tcgplayer_card_id)}")
                    manabox_db_updater.add_tcgplayer_card_id_to_db(card[8], tcgplayer_card_id)
            else:
                # some cards will only come in foil and will not need the offset
                

                tcgplayer_card_id = int(db_lookup[lookup_key])
                # Define the offset mapping
                offset_map = {
                    ('nonfoil', 'Near Mint'): 0,
                    ('nonfoil', 'Lightly Played'): 1,
                    ('nonfoil', 'Moderately Played'): 2,
                    ('nonfoil', 'Heavily Played'): 3,
                    ('nonfoil', 'Damaged'): 4,
                    ('foil', 'Near Mint'): 6,
                    ('foil', 'Lightly Played'): 7,
                    ('foil', 'Moderately Played'): 8,
                    ('foil', 'Heavily Played'): 9,
                    ('foil', 'Damaged'): 10,
                }
                # Normalize printing and condition for lookup (match formatting)
                printing_key = printing.lower() if printing else 'nonfoil'
                condition_key = condition  # Already formatted as 'Near Mint', 'Lightly Played', etc.
                offset = offset_map.get((printing_key, condition_key), 0)
                # does not work when the condition is not near mint
                #  NEED TO REBUILD THE DB TO HAVE CARD NAME tcgplayer_id {foil, nonfoil}
                # so that i dont need to know if there is only a foil version or not

            
            tcgplayer_data.append({
                "TCGplayer Id": int(tcgplayer_card_id) if tcgplayer_card_id else pd.NA,
                "Product Line": 'Magic',
                "Set Name": set_name if len(card) > 2 else '',
                "Product Name": card_name if len(card) > 0 else '',
                "Title": '',
                "Number": collector_number if len(card) > 3 else '',
                "Rarity": rarity if len(card) > 5 else '',
                "Condition": f'{condition} Foil' if card[4] == 'foil' else f'{condition}',
                "TCG Market Price": '',
                "TCG Direct Low": '',
                "TCG Low Price With Shipping": '',
                "TCG Low Price": '',
                "Total Quantity": '',
                "Add to Quantity": quantity if len(card) > 6 else '',
                "TCG Marketplace Price": tcg_martket_price if len(card) > 9 else '',
                "Photo URL": ''
            })
            progress_bar.progress((idx + 1) / total_cards, text=f"[{idx + 1}/{total_cards}] {card[0]}: Processed")
        progress_bar.empty()
        tcgplayer_df = pd.DataFrame(tcgplayer_data, columns=required_headers)
        # Ensure TCGplayer Id is nullable integer for Arrow compatibility
        tcgplayer_df["TCGplayer Id"] = tcgplayer_df["TCGplayer Id"].astype(
            'Int64')
        output_csv = "manabox_tcgplayer_ids.csv"
        st.session_state['manabox_tcgplayer_df'] = tcgplayer_df
        st.session_state['manabox_output_csv'] = output_csv
        st.session_state['manabox_last_filename'] = manabox_csv.name
    else:
        tcgplayer_df = st.session_state['manabox_tcgplayer_df']
        output_csv = st.session_state['manabox_output_csv']

    # UI: Three columns for controls
    all_columns = list(tcgplayer_df.columns)
    blank_columns = [col for col in all_columns if tcgplayer_df[col].replace(
        '', pd.NA).isna().all()]
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        hidden_columns = st.multiselect(
            "Hide columns", options=all_columns, default=[])
    with col2:
        # Group the two checkboxes vertically
        show_missing_only = st.checkbox(
            "Show only cards missing TCGplayer Id", value=False)
        hide_blank = st.checkbox("Hide all blank columns", value=True)
        if hide_blank:
            hidden_columns = blank_columns
    with col3:
        pass
    # Filter DataFrame if needed
    df_to_show = tcgplayer_df.copy()
    if show_missing_only:
        df_to_show = df_to_show[df_to_show['TCGplayer Id'].isna()]
    if hidden_columns:
        df_to_show = df_to_show.drop(columns=hidden_columns)

    def highlight_missing_id(row):
        # Use pd.isna to check for missing TCGplayer Id
        color = 'background-color: #ffcccc' if pd.isna(
            row.get('TCGplayer Id', None)) else ''
        return [color] * len(row)
    styled_df = df_to_show.style.apply(
        highlight_missing_id, axis=1) if 'TCGplayer Id' in df_to_show.columns else df_to_show
    # Also update missing_count calculation to use .isna()
    missing_count = df_to_show['TCGplayer Id'].isna(
    ).sum() if 'TCGplayer Id' in df_to_show.columns else 0
    st.toast(f"TCGPlayer IDs saved to {output_csv}")
    # Autosize columns using set_sticky and set_properties for best fit
    styled_df = styled_df.set_sticky(axis="columns").set_properties(
        **{"min-width": "80px", "max-width": "400px", "white-space": "pre-wrap"})
    st.dataframe(styled_df, use_container_width=True)

if st.session_state.get('manabox_tcgplayer_df') is not None and not st.session_state['manabox_tcgplayer_df'].empty:
    # Add checkbox for exporting only cards with TCGplayer Ids
    export_only_with_ids = st.checkbox(
        "Download only cards with TCGplayer Id", value=False)
    export_df = st.session_state['manabox_tcgplayer_df']
    if export_only_with_ids:
        export_df = export_df[export_df['TCGplayer Id'].notna()]
    st.download_button(
        label="Download Converted CSV",
        data=export_df.to_csv(index=False).encode('utf-8'),
        file_name=st.session_state['manabox_output_csv'],
        mime='text/csv'
    )
    st.warning(f"PLEASE KEEP IN MIND TOKENS ARE WILL NOT BE ASSIGNED A TCGPLAYER ID.")

widgets.footer()
