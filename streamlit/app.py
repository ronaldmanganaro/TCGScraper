import streamlit as st
st.set_page_config(page_title="app", layout="wide", page_icon="icon.png")

# --- Startup logic: You can add any initialization here ---
if "startup_complete" not in st.session_state:
    st.session_state.startup_complete = True
    # You can add more startup logic here if needed

# Only add the restricted page if the user is rmangana
pages = [
    st.Page('pages/Home.py'),
    st.Page('pages/Repricer.py'),
    st.Page('pages/EVTools.py'),
    st.Page('pages/PokemonPriceTracker.py'),
    st.Page('pages/Manabox.py'),
    st.Page('pages/Manage_Inventory.py'),
    st.Page('pages/Tcgplayer_Print_Orders.py'),
    st.Page('pages/Underpriced_Cards_Snapshot.py')
    ]
if st.session_state.get('current_user') == 'rmangana':
    pages.append(st.Page('pages/Update_TCGplayer_IDs.py'))
    pages.append(st.Page('pages/Cloud_Control.py'))
    pages.append(st.Page('pages/test_crop.py'))

pg = st.navigation(pages, position="hidden")
pg.run()
