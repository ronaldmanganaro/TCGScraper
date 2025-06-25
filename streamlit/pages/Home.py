# app.py
import streamlit as st
from PIL import Image
# Import the coffee button
from streamlit_extras.buy_me_a_coffee import button as coffee_button
from functions import widgets
# Set page configuration globally at the start

st.title("🏠 Home", anchor=None, help=None, width="stretch")

# ---- Sidebar Navigation ----
st.sidebar.header("Choose a TCG", divider=True)

# Section for selecting TCG
cols = st.sidebar.columns(1)

if cols[0].button("🧙 Magic", use_container_width=True):
    st.session_state.selected_tcg = "Magic: The Gathering"
if cols[0].button("⚡ Pokémon", use_container_width=True):
    st.session_state.selected_tcg = "Pokémon"
if cols[0].button("✨ All", use_container_width=True):
    st.session_state.selected_tcg = "All TCGs"
if cols[0].button("🧩 Other", use_container_width=True):
    st.session_state.selected_tcg = "Other TCGs (Coming Soon)"

section = st.session_state.get("selected_tcg", "Magic: The Gathering")

# ---- Magic Section ----
if section == "Magic: The Gathering":
    st.title("🧙‍♂️ Magic: The Gathering Tools")
    st.markdown("Tools specifically for Magic sellers. More to come!")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📦 Booster Box EV Calculator")
        st.markdown("_Estimate expected value from booster box pulls._")
        if st.button("Launch Booster Box EV Tool"):
            st.switch_page("pages/EVTools.py")

    with col2:
        st.subheader("🧪 Precon EV Calculator")
        st.markdown("_Calculate value of sealed Preconstructed decks._")
        if st.button("Launch Precon EV Tool"):
            st.switch_page("pages/EVTools.py")

# ---- Pokémon Section ----
elif section == "Pokémon":
    st.title("⚡ Pokémon Tools")
    st.markdown("Tools specifically for Pokémon sellers.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Pokémon Price Chart")
        st.markdown("_Track price trends over time._")
        if st.button("View Price Chart"):
            st.switch_page("pages/PokemonPriceTracker.py")

elif section == "All TCGs":
    st.title("✨ All TCGs Tools")
    st.markdown("Tools that work across multiple TCGs. More to come!")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Price Comparison Tool")
        st.markdown("_Compare prices across different TCGs._")
        if st.button("Launch Price Comparison Tool"):
            st.switch_page("pages/Repricer.py")

# ---- Future TCG Section ----
else:
    st.title("🧩 Other TCGs (Coming Soon)")
    st.info("We’re planning to add tools for Yu-Gi-Oh!, Flesh and Blood, and more.")
    st.image("https://cdn.vox-cdn.com/thumbor/dTQveLbtHn9ZJhH7qZoTx2Ika4A=/0x0:1300x650/1400x933/filters:focal(546x226:754x434):no_upscale()/cdn.vox-cdn.com/uploads/chorus_image/image/72780383/Screen_Shot_2024_01_24_at_9.23.56_AM.0.png",
             caption="Future support for more TCGs", use_column_width=True)

widgets.show_pages_sidebar()

# ---- Footer ----
st.markdown("---")  # Add a horizontal line to separate the footer
