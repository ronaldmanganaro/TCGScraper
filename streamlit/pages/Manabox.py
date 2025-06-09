import streamlit as st
from functions import widgets
import pandas as pd
import time
import psycopg2
import requests
import logging


# --- DB Connection Helper ---
def get_db_connection():
    return psycopg2.connect(
        dbname='scryfall',
        user='rmangana',
        password='password',
        host='52.73.212.127',
        port=5432
    )

# --- Get TCGplayer ID from DB ---
def get_tcgplayer_id_from_db(scryfall_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT tcgplayer_id FROM scryfall
            WHERE id = %s
            LIMIT 1
        """, (scryfall_id,))
        result = cur.fetchone()
        return result[0] if result and result[0] is not None else None
    finally:
        cur.close()
        conn.close()


# --- Get TCGplayer ID from Scryfall ID via Scryfall API ---
def get_tcgplayer_id_from_scryfall_id(scryfall_id, foil=False):
    """
    Given a Scryfall card ID, fetch the card from the Scryfall API and return its TCGplayer ID.
    If foil=True, prefer tcgplayer_foil_id. If foil=False, prefer tcgplayer_nonfoil_id.
    Fallback to tcgplayer_id if specific field is missing.
    """
    url = f"https://api.scryfall.com/cards/{scryfall_id}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if foil:
                tcg_id = data.get("tcgplayer_foil_id")
                if tcg_id is not None:
                    return tcg_id
            else:
                tcg_id = data.get("tcgplayer_nonfoil_id")
                if tcg_id is not None:
                    return tcg_id
            # Fallback
            return data.get("tcgplayer_id")
    except Exception as e:
        logging.warning(f"Error fetching Scryfall card by id {scryfall_id}: {e}")
    return None

# --- Main lookup function ---
def get_tcgplayer_id(card_name, set_name):
    tcg_id = get_tcgplayer_id_from_db()
    if tcg_id:
        return tcg_id
    return get_tcgplayer_id_from_scryfall(card_name, set_name)

def batch_get_tcgplayer_ids_from_db(scryfall_id_list):
    """
    scryfall_id_list: List of Scryfall IDs (strings)
    Returns: dict mapping scryfall_id -> tcgplayer_id
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        format_strings = ','.join(['%s'] * len(scryfall_id_list))
        cur.execute(f"""
            SELECT tcgplayer_id, id FROM scryfall
            WHERE id IN ({format_strings})
        """, scryfall_id_list)
        results = cur.fetchall()
        # Build lookup dict: scryfall_id -> tcgplayer_id
        lookup = { id: tcgplayer_id for tcgplayer_id, id in results if tcgplayer_id is not None }
        return lookup
    finally:
        cur.close()
        conn.close()


widgets.show_pages_sidebar()

st.title("🧩 ManaBox Converter")
st.markdown("""
Welcome to the ManaBox Converter! This tool allows you to convert your card data into the ManaBox format.
""")
tcgplayer_df = None  # Initialize the DataFrame to avoid reference errors
manabox_csv = st.file_uploader("Upload your card data file", type=["csv", "json"], key="mana_box_uploader")

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
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
        # Use scryfall_id for all lookups
        scryfall_id_list = list({str(card[8]) for card in uploaded_df.itertuples() if pd.notna(card[8])})
        logging.info(f"Batch lookup Scryfall IDs: {scryfall_id_list}")
        db_lookup = batch_get_tcgplayer_ids_from_db(scryfall_id_list)
        logging.info(f"DB lookup result: {db_lookup}")
        for idx, card in enumerate(uploaded_df.itertuples()):
            scryfall_id = str(card[8]) if pd.notna(card[8]) else None
            logging.info(f"Processing card: idx={idx}, name={card[1]}, set={card[2]}, scryfall_id={scryfall_id}")
            tcg_id_db = db_lookup.get(scryfall_id) if scryfall_id else None
            if tcg_id_db:
                tcg_id = tcg_id_db
                source = "DB"
                logging.info(f"Found in DB: {card[1]} ({card[2]}) -> {tcg_id}")
            else:
                if scryfall_id:
                    logging.info(f"Not found in DB: {card[1]} ({card[2]}), querying Scryfall API...")
                    progress_bar.progress((idx + 1) / total_cards, text=f"[{idx + 1}/{total_cards}] {card[1]}: Not found in DB, querying Scryfall API...")
                    is_foil = (card[4] == 'foil') if len(card) > 4 else False
                    tcg_id_api = get_tcgplayer_id_from_scryfall_id(scryfall_id, foil=is_foil)
                    if tcg_id_api is not None:
                        tcg_id = tcg_id_api
                        source = "API"
                        logging.info(f"Found in Scryfall API: {card[1]} ({card[2]}) -> {tcg_id}")
                    else:
                        tcg_id = None
                        source = "Not found"
                        logging.warning(f"Not found in DB or API: {card[1]} ({card[2]})")
                else:
                    tcg_id = None
                    source = "No Scryfall ID"
                    logging.warning(f"No Scryfall ID for card: {card[1]} ({card[2]})")
            tcgplayer_data.append({
                "TCGplayer Id": int(tcg_id) if tcg_id is not None else pd.NA,
                "Product Line": 'Magic',
                "Set Name": card[2] if len(card) > 2 else '',
                "Product Name": card[0],
                "Title": '',
                "Number": card[3] if len(card) > 3 else '',
                "Rarity": card[5] if len(card) > 5 else '',
                "Condition": 'Near Mint Foil' if card[4] == 'foil' else 'Near Mint',
                "TCG Market Price": '',
                "TCG Direct Low": '',
                "TCG Low Price With Shipping": '',
                "TCG Low Price": '',
                "Total Quantity": '',
                "Add to Quantity": card[6] if len(card) > 6 else '',
                "TCG Marketplace Price": '',
                "Photo URL": ''
            })
            progress_bar.progress((idx + 1) / total_cards, text=f"[{idx + 1}/{total_cards}] {card[1]}: TCGplayer ID source: {source}")
        progress_bar.empty()
        tcgplayer_df = pd.DataFrame(tcgplayer_data, columns=required_headers)
        # Ensure TCGplayer Id is nullable integer for Arrow compatibility
        tcgplayer_df["TCGplayer Id"] = tcgplayer_df["TCGplayer Id"].astype('Int64')
        output_csv = "manabox_tcgplayer_ids.csv"
        st.session_state['manabox_tcgplayer_df'] = tcgplayer_df
        st.session_state['manabox_output_csv'] = output_csv
        st.session_state['manabox_last_filename'] = manabox_csv.name
    else:
        tcgplayer_df = st.session_state['manabox_tcgplayer_df']
        output_csv = st.session_state['manabox_output_csv']

    # UI: Three columns for controls
    all_columns = list(tcgplayer_df.columns)
    blank_columns = [col for col in all_columns if tcgplayer_df[col].replace('', pd.NA).isna().all()]
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        hidden_columns = st.multiselect("Hide columns", options=all_columns, default=[])
    with col2:
        # Group the two checkboxes vertically
        show_missing_only = st.checkbox("Show only cards missing TCGplayer Id", value=False)
        hide_blank = st.checkbox("Hide all blank columns")
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
        color = 'background-color: #ffcccc' if pd.isna(row.get('TCGplayer Id', None)) else ''
        return [color] * len(row)
    styled_df = df_to_show.style.apply(highlight_missing_id, axis=1) if 'TCGplayer Id' in df_to_show.columns else df_to_show
    # Also update missing_count calculation to use .isna()
    missing_count = df_to_show['TCGplayer Id'].isna().sum() if 'TCGplayer Id' in df_to_show.columns else 0
    st.toast(f"TCGPlayer IDs saved to {output_csv}")
    # Autosize columns using set_sticky and set_properties for best fit
    styled_df = styled_df.set_sticky(axis="columns").set_properties(**{"min-width": "80px", "max-width": "400px", "white-space": "pre-wrap"})
    st.dataframe(styled_df, use_container_width=True)

if st.session_state.get('manabox_tcgplayer_df') is not None and not st.session_state['manabox_tcgplayer_df'].empty:
    # Add checkbox for exporting only cards with TCGplayer Ids
    export_only_with_ids = st.checkbox("Download only cards with TCGplayer Id", value=False)
    export_df = st.session_state['manabox_tcgplayer_df']
    if export_only_with_ids:
        export_df = export_df[export_df['TCGplayer Id'].notna()]
    st.download_button(
        label="Download Converted CSV",
        data=export_df.to_csv(index=False).encode('utf-8'),
        file_name=st.session_state['manabox_output_csv'],
        mime='text/csv'
    )

widgets.footer()
