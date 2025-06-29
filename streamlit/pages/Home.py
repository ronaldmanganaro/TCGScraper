# app.py
from streamlit_extras.floating_button import floating_button
import streamlit as st
from PIL import Image
# Import the coffee button
from streamlit_extras.buy_me_a_coffee import button as coffee_button
from functions import widgets

# Set page configuration globally at the start

st.title("Home", anchor=None, help=None, width="stretch")

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

# User preferences dialog using decorator
@st.dialog("User Preferences", width="medium")
def preferences_dialog():
    st.header("Preferences")
    theme = st.selectbox("Theme", ["Light", "Dark", "Auto"], key="theme_select_dialog")
    notifications = st.checkbox("Enable notifications", key="notif_checkbox_dialog")
    if st.button("Save Preferences"):
        st.session_state["theme"] = theme
        st.session_state["notifications"] = notifications
        st.success("Preferences saved!")
        st.rerun()

# Apply theme based on user preference
if "theme" in st.session_state:
    if st.session_state["theme"] == "Dark":
        st.markdown("""
            <style>
            body, .stApp { background-color: #18191A !important; color: #F5F6F7 !important; }
            </style>
        """, unsafe_allow_html=True)
    elif st.session_state["theme"] == "Light":
        st.markdown("""
            <style>
            body, .stApp { background-color: #FFFFFF !important; color: #18191A !important; }
            </style>
        """, unsafe_allow_html=True)
    # 'Auto' uses default Streamlit theme

clicked = floating_button(
    label="⚙️",  # Gear icon as label
    key="prefs_btn"
)

if clicked:
    preferences_dialog()

widgets.footer()