import streamlit as st
from functions import widgets, commander_ev
import pandas as pd
import time


widgets.show_pages_sidebar()

st.title("🧩 ManaBox Converter")
st.markdown("""
Welcome to the ManaBox Converter! This tool allows you to convert your card data into the ManaBox format.
""")

manabox_csv = st.file_uploader("Upload your card data file", type=["csv", "json"], key="mana_box_uploader")
if manabox_csv is not None:
    if "manabox_csv" not in st.session_state or st.session_state.get("manabox_file_name") != manabox_csv.name:
        st.session_state.manabox_csv = pd.read_csv(manabox_csv, index_col=0)
        st.session_state.manabox_file_name = manabox_csv.name
        tcgplayer_data = []
        total_cards = len(st.session_state.manabox_csv)
        progress_bar = st.progress(0, text="Processing card data...")
        # Define required headers
        required_headers = [
            "TCGplayer Id", "Product Line", "Set Name", "Product Name", "Title", "Number", "Rarity", "Condition",
            "TCG Market Price", "TCG Direct Low", "TCG Low Price With Shipping", "TCG Low Price", "Total Quantity",
            "Add to Quantity", "TCG Marketplace Price", "Photo URL"
        ]

        # Build the output data for each card
        for idx, card in enumerate(st.session_state.manabox_csv.itertuples()):
            tcg_id = commander_ev.get_tcgplayerid(card[1], card[3])
            # Need to use condition to alter near_mint to Near Mint Foil or Near Mint
            tcgplayer_data.append({
                "TCGplayer Id": tcg_id,
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
        st.session_state.tcgplayer_df = pd.DataFrame(tcgplayer_data, columns=required_headers)
    tcgplayer_df = st.session_state.tcgplayer_df
    output_csv = "manabox_tcgplayer_ids.csv"
    tcgplayer_df.to_csv(output_csv, index=False)

    # Highlight missing TCGplayer Ids
    def highlight_missing_id(row):
        color = 'background-color: #ffcccc' if not row['TCGplayer Id'] else ''
        return [color] * len(row)
    styled_df = tcgplayer_df.style.apply(highlight_missing_id, axis=1)

    # Count missing TCGplayer Ids
    missing_count = (tcgplayer_df['TCGplayer Id'] == '').sum()

    st.success(f"TCGPlayer IDs saved to {output_csv}")
    st.dataframe(styled_df, use_container_width=True)

    # Show warning if there are missing TCGplayer Ids
    if missing_count > 0:
        st.warning(f"Warning: {missing_count} cards do not have a TCGplayer Id. They will be included in the download.")

    st.download_button(
        label="Download Converted CSV",
        data=tcgplayer_df.to_csv(index=False).encode('utf-8'),
        file_name=output_csv,
        mime='text/csv'
    )
