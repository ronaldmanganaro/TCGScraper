import streamlit as st
from functions import widgets, commander_ev
import pandas as pd
import time


widgets.show_pages_sidebar()

st.title("🧩 ManaBox Converter")
st.markdown("""
Welcome to the ManaBox Converter! This tool allows you to convert your card data into the ManaBox format.
""")

# if  "manabox_csv" not in st.session_state:
#     st.session_state["manabox_csv"] = pd.read_csv("data/manabox/manaboxtest.csv", index_col=0)
#     print(st.session_state.manabox_csv)

manabox_csv =  st.file_uploader("Upload your card data file", type=["csv", "json"], key="mana_box_uploader")
if manabox_csv is not None:
    st.session_state.manabox_csv = pd.read_csv(manabox_csv, index_col=0)

    tcgplayer_data = []
    total_cards = len(st.session_state.manabox_csv)
    progress_bar = st.progress(0, text="Processing card data...")
    for idx, card in enumerate(st.session_state.manabox_csv.itertuples()):
        # progress bar for getting tcgplayer ids
        with st.spinner(f"Processing {card[1]}..."):
            tcg_id = commander_ev.get_tcgplayerid(card[1], card[3])
            tcgplayer_data.append({
                "Card Name": card[1],
                "Set": card[2] if len(card) > 2 else '',
                "Collector Number": card[3] if len(card) > 3 else '',
                "TCGPlayer ID": tcg_id
            })
            time.sleep(0.5)
        progress_bar.progress((idx + 1) / total_cards, text=f"Processed {idx + 1} of {total_cards} cards")
    progress_bar.empty()
    # Save to CSV
    tcgplayer_df = pd.DataFrame(tcgplayer_data)
    output_csv = "manabox_tcgplayer_ids.csv"
    tcgplayer_df.to_csv(output_csv, index=False)
    st.success(f"TCGPlayer IDs saved to {output_csv}")
    st.dataframe(tcgplayer_df, use_container_width=True)

# need to do a lookup of the card by name and collector number and set
# query scyfall for the card data
