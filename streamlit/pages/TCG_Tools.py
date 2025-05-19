from functions import mtg_box_sim, commander_ev, db
import streamlit as st
import os
import pandas as pd
import sys
import logging
import requests
import matplotlib.pyplot as plt
import plotly.express as px

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


def shortenLink(url: str) -> str:
    response = requests.get(f"https://tinyurl.com/api-create.php?url={url}")
    if response.status_code == 200:
        return response.text
    return url


with st.expander("Pokemon Price Chart", expanded=True):
    if 'card_list' not in st.session_state:
        st.session_state.card_list = []

    connection = db.connectDB()

    min_quantity_selectbox = st.selectbox(
        "Minimum Listing Quantity",
        [5, 10, 20, 50, 100, 500],
        index=0,
        key="min_quantity_selectbox"
    )

    if st.button("Query"):
        cards = db.get_card_name(connection, min_quantity_selectbox)
        st.session_state.card_list = [
            f"{card[0]} ({card[1]})" for card in cards
        ]

    pkm_selectbox = st.selectbox(
        "Pokemon Card",
        st.session_state.card_list,
        index=0 if st.session_state.card_list else None,
        key="pkm_selectbox"
    )
    tab1, tab2 = st.tabs(["📈 Chart", "🗃 Data"])

    if st.session_state.pkm_selectbox:
        logging.debug(
            f"Querying data for card: {st.session_state.pkm_selectbox}")
        card_name = st.session_state.pkm_selectbox.split(" (")[0]
        card_number = st.session_state.pkm_selectbox.split(
            " (")[1].replace(")", "")
        card_data = db.get_card_data(connection, card_name, card_number)

        if card_data:
            price_data = db.estimate_velocity(
                connection, card_name, card_number)

            if price_data and len(price_data[0]):
                price_df = pd.DataFrame(price_data, columns=[
                    "date", "lowest_price", "market_price", "listing_quantity", "velocity_sold"
                ])
                price_df["date"] = pd.to_datetime(price_df["date"])
                price_df["lowest_price"] = price_df["lowest_price"].astype(
                    float)
                price_df["market_price"] = price_df["market_price"].astype(
                    float)
                price_df = price_df.sort_values("date")

                # Melt the data for grouped bar chart
                melted_df = price_df.melt(
                    id_vars=["date"],
                    value_vars=["lowest_price", "market_price"],
                    var_name="Price Type",
                    value_name="Price"
                )

                # Create grouped bar chart with Plotly Express
                fig = px.bar(
                    melted_df,
                    x="date",
                    y="Price",
                    color="Price Type",
                    barmode="group",
                    labels={"date": "Date", "Price": "Price",
                            "Price Type": "Price Type"},
                    title=f"Lowest Price vs Market Price for {card_name} ({card_number})"
                )

                fig.update_layout(xaxis_tickangle=-45)
                tab1 st.plotly_chart(fig, use_container_width=True)

            else:
                st.warning("Price data shape does not match expected columns.")
        else:
            st.info("No data found for this card.")
