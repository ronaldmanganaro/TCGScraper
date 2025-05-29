import streamlit as st
st.set_page_config(page_title="app", layout="wide")

# --- Startup logic: You can add any initialization here ---
if "startup_complete" not in st.session_state:
    st.session_state.startup_complete = True
    # You can add more startup logic here if needed


pg = st.navigation(
    [
        st.Page('pages/Home.py'),
        st.Page('pages/Repricer.py'),
        st.Page('pages/EVTools.py'),
        st.Page('pages/PokemonPriceTracker.py'),
        st.Page('pages/Cloud_Control.py'),
    ], position="hidden"
)

pg.run()
