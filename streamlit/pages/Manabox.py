import streamlit as st
from functions import widgets, commander_ev
import pandas as pd


widgets.show_pages_sidebar()

st.title("🧩 ManaBox Converter")
st.markdown("""
Welcome to the ManaBox Converter! This tool allows you to convert your card data into the ManaBox format.
""")



if  "manabox_csv" not in st.session_state:
    st.session_state["manabox_csv"] = pd.read_csv("data/manabox/manaboxtest.csv", index_col=0)
    print(st.session_state.manabox_csv)

st.file_uploader("Upload your card data file", type=["csv", "json"], key="mana_box_uploader")

print(commander_ev.get_tcgplayerid("M21", "Lightning-Bolt"))


# need to do a lookup of the card by name and collector number and set 
# query scyfall for the card data
