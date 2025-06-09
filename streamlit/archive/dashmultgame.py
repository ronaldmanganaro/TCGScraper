import streamlit as st
from PIL import Image

st.set_page_config(page_title="TCG Tools Dashboard", layout="wide")

# ---- Sidebar Navigation ----
st.sidebar.header("Choose a TCG", divider=True)

cols = st.sidebar.columns(1)

if cols[0].button("🧙 Magic", use_container_width=True):
    st.session_state.selected_tcg = "Magic: The Gathering"
if cols[0].button("⚡ Pokémon", use_container_width=True):
    st.session_state.selected_tcg = "Pokémon"
if cols[0].button("🧩 Other",  use_container_width=True):
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
        # Placeholder or call your calculator function here
        st.button("Launch Booster Box EV Tool")

    with col2:
        st.subheader("🧪 Precon EV Calculator")
        st.markdown("_Calculate value of sealed Preconstructed decks._")
        # Placeholder or call your calculator function here
        st.button("Launch Precon EV Tool")

# ---- Pokémon Section ----
elif section == "Pokémon":
    st.title("⚡ Pokémon Tools")
    st.markdown("Tools specifically for Pokémon sellers.")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Pokémon Price Chart")
        st.markdown("_Track price trends over time._")
        # Placeholder or call your chart function here
        st.button("View Price Chart")

    with col2:
        st.subheader("🔎 Listing Scraper")
        st.markdown("_Scrape TCGPlayer listings to find deals or competitors._")
        # Placeholder or call your scraper function here
        st.button("Run Scraper")

# ---- Future TCG Section ----
else:
    st.title("🧩 Other TCGs (Coming Soon)")
    st.info("We’re planning to add tools for Yu-Gi-Oh!, Flesh and Blood, and more.")
    st.image("https://cdn.vox-cdn.com/thumbor/dTQveLbtHn9ZJhH7qZoTx2Ika4A=/0x0:1300x650/1400x933/filters:focal(546x226:754x434):no_upscale()/cdn.vox-cdn.com/uploads/chorus_image/image/72780383/Screen_Shot_2024_01_24_at_9.23.56_AM.0.png", caption="Future support for more TCGs", use_column_width=True)

