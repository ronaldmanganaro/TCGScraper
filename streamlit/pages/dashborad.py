import streamlit as st
from PIL import Image

st.set_page_config(layout="wide", page_title="TCG Seller Dashboard")

# Load brand images (optional)
st.title("📊 TCG Seller Dashboard")


st.markdown("Welcome to the **TCG Tools Dashboard** for sellers of Magic: The Gathering and Pokémon cards.")

# Navigation cards
st.markdown("---")
st.subheader("🧰 Tools")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📦 Booster Box EV Calculator")
    st.write("Estimate the expected value of MTG or Pokémon booster boxes based on current market prices.")
    if st.button("Go to Booster EV Tool", key="booster"):
        st.session_state.page = "booster"

    st.markdown("### 📋 Precon EV Calculator")
    st.write("Calculate expected value of Commander decks, League Battle decks, or other preconstructed products.")
    if st.button("Go to Precon EV Tool", key="precon"):
        st.session_state.page = "precon"

with col2:
    st.markdown("### 🔍 Card Lookup & Price Trends")
    st.write("Search card prices, set info, rarity, and historical value from TCGPlayer or Scryfall APIs.")
    if st.button("Go to Card Lookup", key="lookup"):
        st.session_state.page = "lookup"

    st.markdown("### 📈 Price Chart Viewer")
    st.write("Visualize market price trends for popular cards over time, export as PNG or CSV.")
    if st.button("Go to Price Chart", key="charts"):
        st.session_state.page = "charts"

# Route to selected page (requires imported pages or functions in real app)
if "page" in st.session_state:
    st.markdown("---")
    if st.session_state.page == "booster":
        st.header("📦 Booster Box EV Tool")
        st.info("[Insert Booster EV UI here]")
    elif st.session_state.page == "precon":
        st.header("📋 Precon EV Tool")
        st.info("[Insert Precon EV UI here]")
    elif st.session_state.page == "lookup":
        st.header("🔍 Card Lookup Tool")
        st.info("[Insert Card Lookup UI here]")
    elif st.session_state.page == "charts":
        st.header("📈 Price Chart Viewer")
        st.info("[Insert Chart Viewer UI here]")
