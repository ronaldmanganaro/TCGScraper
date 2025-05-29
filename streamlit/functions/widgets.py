import streamlit as st


def show_pages_sidebar():
    # Expander for Pages
    with st.sidebar.expander("📄 Pages", expanded=True):
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("pages/home.py")
        if st.button("💲 Repricer", use_container_width=True):
            st.switch_page("pages/Repricer.py")
        if st.button("📦 EV Tools", use_container_width=True):
            st.switch_page("pages/EVTools.py")
        if st.button("⚡ Pokémon Price Tracker", use_container_width=True):
            st.switch_page("pages/PokemonPriceTracker.py")
        if st.button("☁️ Cloud Control", use_container_width=True):
            st.switch_page("pages/Cloud_Control.py")
