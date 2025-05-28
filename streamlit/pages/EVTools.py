from functions import fetch_all_sales, db
from functions import mtg_box_sim, commander_ev, db
import streamlit as st
import os
import pandas as pd
import sys
import logging
import requests
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import asyncio
import sys
import pyperclip


if sys.platform.startswith('win') and sys.version_info >= (3, 8):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
import asyncio
import altair as alt

sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..functions')))


logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[
                    logging.StreamHandler(sys.stdout)])

st.title("TCG Tools")
with st.expander("Booster Box EV Calculator"):
    st.divider()
    # Initialize session state to store EV results
    if 'ev_history' not in st.session_state:
        st.session_state.ev_history = []

    # Initialize options in session state
    if "options" not in st.session_state:
        st.session_state.options = []

    # Create 3 columns
    col1, col2, col3 = st.columns([2, 3, 1])

    # Inputs and button
    with col1:
        set = st.text_input("Set Name", placeholder="dft", value="dft")

    with col2:
        boxes_to_open = st.number_input("Boxes to open", min_value=1, step=1)

    with col3:
        if st.button("Simulate!", use_container_width=True):
            ev = mtg_box_sim.simulate(f"{set}", int(boxes_to_open))
            # Add to history
            st.session_state.ev_history.append({
                "Set": set,
                "Boxes Opened": int(boxes_to_open),
                "EV": round(ev, 2)
            })
        if st.button("clear", use_container_width=True):
            st.session_state.ev_history = []

    # Display table with 2 columns
    if st.session_state.ev_history:
        df = pd.DataFrame(st.session_state.ev_history)
        # Center align the entire DataFrame
        styled_data = df.style.set_properties(**{'text-align': 'center'})
        styled_data.set_table_styles([{
            'selector': 'th',
            'props': [('text-align', 'center')]
        }])

        # Display with Streamlit
        st.dataframe(styled_data, use_container_width=True)

precon_ev = 0

with st.expander("Precon EV Calculator"):
    precons_by_set = {}

    sets = []
    cwd = os.getcwd()
    set_path = os.path.join(cwd, "data", "precons")
    for set in os.listdir(set_path):
        sets = set
        precons_by_set[set] = []
        precon_path = os.path.join(set_path, set)
        for precon in os.listdir(precon_path):
            precons_by_set[set].append(precon)
    # print(precons_by_set)

    if 'precon_ev_history' not in st.session_state:
        st.session_state.precon_ev_history = []
    st.divider()

    # Create 3 columns
    col1, col2, col3 = st.columns([2, 3, 1])

    # Inputs and button
    with col1:
        set_selectbox = st.selectbox(
            "Please select a set code",
            # Use the dynamically populated sets list
            [key.upper() for key in precons_by_set.keys()],
        )

    with col2:
        precon = st.selectbox(
            "Precon Name",
            # Use the dynamically populated precons list
            [precon.replace(".txt", "")
             for precon in precons_by_set[set_selectbox]],
            key="precon_selectbox",
            # Reset EV to 0 when a new precon is selected
            on_change=lambda: st.session_state.update({"precon_ev": 0})
        )

    with col3:
        # Use session state to store the EV value
        if "precon_ev" not in st.session_state:
            st.session_state.precon_ev = 0  # Initialize to 0 or a default value

        # Display the number input with the session state value
        st.number_input("EV", value=st.session_state.precon_ev, key="ev_input")

    # Calculate EV button
    if st.button("Calculate EV", use_container_width=True):
        # Calculate the EV and update the session state
        st.session_state.precon_ev = commander_ev.calculate_ev(
            set_selectbox, precon)
        st.rerun()
