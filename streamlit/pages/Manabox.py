import streamlit as st
from functions import widgets
import pandas as pd
import time
import psycopg2
import requests


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
def get_tcgplayer_id_from_db(card_name, set_name):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT tcgplayer_id FROM scryfall
            WHERE LOWER(name) = LOWER(%s) AND LOWER(set_name) = LOWER(%s)
            LIMIT 1
        """, (card_name, set_name))
        result = cur.fetchone()
        return result[0] if result and result[0] is not None else None
    finally:
        cur.close()
        conn.close()

# --- Get TCGplayer ID from Scryfall API ---
def get_tcgplayer_id_from_scryfall(card_name, set_name):
    url = f"https://api.scryfall.com/cards/named?exact={card_name}&set={set_name}"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        return data.get("tcgplayer_id")
    return None

# --- Main lookup function ---
def get_tcgplayer_id(card_name, set_name):
    tcg_id = get_tcgplayer_id_from_db(card_name, set_name)
    if tcg_id:
        return tcg_id
    return get_tcgplayer_id_from_scryfall(card_name, set_name)

def batch_get_tcgplayer_ids_from_db(card_set_pairs):
    """
    card_set_pairs: List of (card_name, set_name) tuples
    Returns: dict mapping (card_name.lower(), set_name.lower()) -> tcgplayer_id
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Prepare the WHERE clause for batch query
        # Use tuple unpacking for psycopg2's mogrify to avoid SQL injection
        format_strings = ','.join(['%s'] * len(card_set_pairs))
        cur.execute(f"""
            SELECT LOWER(name), LOWER(set_name), tcgplayer_id FROM scryfall
            WHERE (LOWER(name), LOWER(set_name)) IN ({format_strings})
        """, card_set_pairs)
        results = cur.fetchall()
        # Build lookup dict
        lookup = { (name, set_name): tcg_id for name, set_name, tcg_id in results if tcg_id is not None }
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
        card_set_pairs = list({(str(card[1]).lower(), str(card[2]).lower()) for card in uploaded_df.itertuples()})
        db_lookup = batch_get_tcgplayer_ids_from_db(card_set_pairs)
        for idx, card in enumerate(uploaded_df.itertuples()):
            key = (str(card[1]).lower(), str(card[2]).lower())
            tcg_id = db_lookup.get(key)
            if not tcg_id:
                tcg_id = get_tcgplayer_id_from_scryfall(card[1], card[2])
            tcgplayer_data.append({
                "TCGplayer Id": int(tcg_id) if tcg_id is not None else '',
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
            time.sleep(0.5)
            progress_bar.progress((idx + 1) / total_cards, text=f"Processed {idx + 1} of {total_cards} cards. Currrent card: {card[0]}")
        progress_bar.empty()
        tcgplayer_df = pd.DataFrame(tcgplayer_data, columns=required_headers)
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
        show_missing_only = st.checkbox("Show only cards missing TCGplayer Id", value=False)
    with col3:
        if st.button("Hide all blank columns"):
            hidden_columns = blank_columns
    # Filter DataFrame if needed
    df_to_show = tcgplayer_df.copy()
    if show_missing_only:
        df_to_show = df_to_show[df_to_show['TCGplayer Id'] == '']
    if hidden_columns:
        df_to_show = df_to_show.drop(columns=hidden_columns)
    def highlight_missing_id(row):
        color = 'background-color: #ffcccc' if not row.get('TCGplayer Id', None) else ''
        return [color] * len(row)
    styled_df = df_to_show.style.apply(highlight_missing_id, axis=1) if 'TCGplayer Id' in df_to_show.columns else df_to_show
    missing_count = (tcgplayer_df['TCGplayer Id'] == '').sum()
    st.toast(f"TCGPlayer IDs saved to {output_csv}")
    # Autosize columns using set_sticky and set_properties for best fit
    styled_df = styled_df.set_sticky(axis="columns").set_properties(**{"min-width": "80px", "max-width": "400px", "white-space": "pre-wrap"})
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    if missing_count > 0:
        st.warning(f"Warning: {missing_count} cards do not have a TCGplayer Id. They will be included in the download.")

if st.session_state.get('manabox_tcgplayer_df') is not None and not st.session_state['manabox_tcgplayer_df'].empty:
    st.download_button(
        label="Download Converted CSV",
        data=st.session_state['manabox_tcgplayer_df'].to_csv(index=False).encode('utf-8'),
        file_name=st.session_state['manabox_output_csv'],
        mime='text/csv'
    )
