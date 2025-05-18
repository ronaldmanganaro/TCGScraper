import streamlit as st
import os 
import pandas as pd
import sys
import logging
import requests
import matplotlib.pyplot as plt
import asyncio
import altair as alt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..functions')))
from functions import mtg_box_sim, commander_ev, db, fetch_all_sales

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler(sys.stdout)])

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
        set = st.text_input("Set Name",placeholder="dft", value="dft")

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
        if st.button("clear",use_container_width=True ):
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
    #print(precons_by_set)


    if 'precon_ev_history' not in st.session_state:
        st.session_state.precon_ev_history = []
    st.divider()

    # Create 3 columns
    col1, col2, col3 = st.columns([2, 3, 1])

    # Inputs and button
    with col1:
        set_selectbox = st.selectbox(
            "Please select a set code",
            [key.upper() for key in precons_by_set.keys()],  # Use the dynamically populated sets list
        )

    with col2:
        precon = st.selectbox(
            "Precon Name",
            [precon.replace(".txt", "") for precon in precons_by_set[set_selectbox]],  # Use the dynamically populated precons list
            key="precon_selectbox",
            on_change=lambda: st.session_state.update({"precon_ev": 0})  # Reset EV to 0 when a new precon is selected
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
        st.session_state.precon_ev = commander_ev.calculate_ev(set_selectbox, precon)
        st.rerun()

def shortenLink(url: str) -> str:
    response = requests.get(f"https://tinyurl.com/api-create.php?url={url}")
    if response.status_code == 200:
        return response.text
    return url

with st.expander("Pokemon Price Chart", expanded=True):
    # Load data from database only if not already in session_state
    if 'card_list' not in st.session_state:
        st.session_state.card_list = []

    connection = db.connectDB()

    min_quantity_selectbox = st.selectbox(
        "Minimum Listing Quantity",
        [5, 10, 20, 50, 100],
        index=0,
        key="min_quantity_selectbox"
    )
    if st.button("Query"):
        cards = db.get_card_name(connection, min_quantity_selectbox)
        st.session_state.card_list = [f"{card[0]} ({card[1]})" for card in cards]

    def on_card_change():
        st.session_state['card_selected'] = True
        # Place your logic here

    pkm_selectbox = st.selectbox(
        "Pokemon Card",
        st.session_state.card_list,
        index=0 if st.session_state.card_list else None,
        key="pkm_selectbox"
    )

    if st.session_state.pkm_selectbox:
        logging.debug(f"Querying data for card: {st.session_state.pkm_selectbox}")
        card_name = st.session_state.pkm_selectbox.split(" (")[0]
        card_number = st.session_state.pkm_selectbox.split(" (")[1].replace(")", "")
        card_data = db.get_card_data(connection, card_name, card_number)
        
        #card_data[5] = shortenLink(card_data[5]) 
        
        if card_data:
            df = pd.DataFrame(card_data, columns=[
                "date", "card", "listing_quantity", "lowest_price", "market_price",
                "link", "rarity", "card_number", "set_name"
            ])
            df.set_index("date", inplace=True)
            st.dataframe(df, use_container_width=True)
            
            price_data = db.estimate_velocity(connection, card_name, card_number)
            for row in price_data:
                logging.info(f"Row: {row}")
                
            
            if price_data and len(price_data[0]):
                price_df = pd.DataFrame(price_data, columns=["date", "lowest_price", "market_price", "listing_quantity", "velocity_sold"])
                price_df["date"] = pd.to_datetime(price_df["date"])
                price_df["lowest_price"] = price_df["lowest_price"].astype(float)
                price_df["market_price"] = price_df["market_price"].astype(float)
                price_df["listing_quantity"] = price_df["listing_quantity"].astype(float)
                price_df["velocity_sold"] = price_df["velocity_sold"].astype(float)
                price_df = price_df.sort_values("date")

                # Melt for price lines
                price_df_melt = price_df.melt('date', value_vars=['lowest_price', 'market_price'],
                                              var_name='Price Type', value_name='Price')

                # Price line chart
                price_chart = alt.Chart(price_df_melt).mark_line(point=True).encode(
                    x=alt.X('date:T', title='Date'),
                    y=alt.Y('Price:Q', title='Price'),
                    color='Price Type:N',
                    tooltip=['date:T', 'Price Type:N', 'Price:Q']
                )

                # Listing quantity bar chart (secondary axis)
                quantity_chart = alt.Chart(price_df).mark_bar(opacity=0.3, color='gray').encode(
                    x='date:T',
                    y=alt.Y('listing_quantity:Q', title='Listing Quantity', axis=alt.Axis(titleColor='gray')),
                    tooltip=['date:T', 'listing_quantity:Q']
                )

                # Layer the charts
                combined_chart = alt.layer(
                    quantity_chart,
                    price_chart
                ).resolve_scale(
                    y='independent'
                ).properties(
                    title=f"Price & Listing Quantity Trends for {card_name} ({card_number})",
                    width='container'
                ).interactive()

                st.altair_chart(combined_chart, use_container_width=True)

                # --- Separate stacked bar chart for velocity_sold and listing_quantity ---
                velocity_melt = price_df.melt('date', value_vars=['listing_quantity', 'velocity_sold'],
                                              var_name='Metric', value_name='Value')

                velocity_chart = alt.Chart(velocity_melt).mark_bar().encode(
                    x=alt.X('date:T', title='Date'),
                    y=alt.Y('Value:Q', title='Count', stack='zero'),
                    color=alt.Color('Metric:N', title='Metric'),
                    tooltip=['date:T', 'Metric:N', 'Value:Q']
                ).properties(
                    title=f"Listing Quantity & Velocity Sold (Stacked) for {card_name} ({card_number})",
                    width='container'
                ).interactive()

                st.altair_chart(velocity_chart, use_container_width=True)
            else:
                st.warning("Price data shape does not match expected columns.")
                price_df = pd.DataFrame(price_data)
            
        else:
            st.info("No data found for this card.")



