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

from functions import fetch_all_sales, db


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


with st.expander("Pokemon Price Chart", expanded=True):
    price_df, fig  = None, None
    if 'card_list' not in st.session_state:
        st.session_state.card_list = []

    connection = db.connectDB()

    # Create columns for the dropdown and number input
    col1, col2 = st.columns([3, 1])

    # New row for Query and Pull Historical Data buttons, aligned under the inputs
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])


    with btn_col1:
        if st.button("Query", use_container_width=True):
            
            with st.spinner("Querying..."):
                cards = db.get_card_name(connection, st.session_state.min_quantity_selectbox)
                st.session_state.card_list = [
                    f"{card[0]}, ({card[1]}) [Listings: {card[3]}]" for card in cards
                ]
                st.session_state.card_tuples = cards
            st.toast("Query complete!")
            st.balloons()  # 🎈 Balloons animation

    with btn_col2:
        if st.button("Pull Historical Data", use_container_width=True):
            selected_url = None
            if "card_tuples" in st.session_state :
                for card in st.session_state.card_tuples:
                    if card[0] in  st.session_state.pkm_selectbox:
                        selected_url = card[2]
                        break
            if selected_url:
                with st.spinner("Pulling historical data..."):
                    logging.info(f"Scraping url {selected_url}...")
                    asyncio.run(fetch_all_sales.scrape_table_update_db(selected_url))
                    st.rerun()
                st.balloons()  # 🎈 Balloons animation
            else:
                st.toast("No URL found for selected card.")
                
    with btn_col3:
        if st.button("Copy Card Url", use_container_width=True):
                # Get the URL for the selected card
            selected_url = None
            if "card_tuples" in st.session_state :
                for card in st.session_state.card_tuples:
                    if card[0] in  st.session_state.pkm_selectbox:
                        selected_url = card[2]
                        break
            if selected_url:
                pyperclip.copy(selected_url)
                st.toast('Link Copied to Clipboard!', icon='😍')
                st.snow() 
            else:
                st.toast("No URL found for selected card.")
    # Filters header
    st.markdown("### Filters")

    # Create columns for the dropdown, number input, and filters
    filter_col1, filter_col2, filter_col3 = st.columns([3, 2, 3])

    with filter_col1:
        search_text = st.text_input(
            "Filter cards",
            "",
            key="card_name_filter",
            placeholder="Type part of a card name or number..."
        )
    with filter_col2:
        min_listing = st.number_input(
            "Min Listings",
            min_value=0,
            value=0,
            step=1,
            key="min_listing_filter"
        )
    with filter_col3:
        max_listing = st.number_input(
            "Max Listings",
            min_value=0,
            value=st.session_state.get("min_quantity_selectbox", 10000),  # Default to max listing quantity
            step=1,
            key="max_listing_filter"
        )

    # Filter the card list based on search_text and listing quantity range (case-insensitive)
    def extract_listing(card_str):
        # Assumes format: "Name, (Number) [Listings: X]"
        try:
            return int(card_str.split("[Listings:")[1].split("]")[0].strip())
        except Exception:
            return 0

    filtered_card_list = [
        card for card in st.session_state.card_list
        if search_text.lower() in card.lower()
        and min_listing <= extract_listing(card) <= max_listing
    ]

    with col1:
        pkm_selectbox = st.selectbox(
            "Pokemon Card Name, Card Number",
            filtered_card_list,
            index=0 if filtered_card_list else None,
            key="pkm_selectbox"
        )

    with col2:
        min_quantity_selectbox = st.number_input(
            "Max Listing Quantity",
            min_value=1,
            max_value=10000,
            value=5,  # default value
            step=1,
            key="min_quantity_selectbox"
        )



    if st.session_state.pkm_selectbox:
        
        
        # Remove the [Listings: x] part before splitting
        selectbox_value = st.session_state.pkm_selectbox.split(" [Listings:")[0]
        logging.info(f"Selectbox value: {selectbox_value}")
        card_name = selectbox_value.split(", (")[0]
        card_number = selectbox_value.split(", (")[1].strip(")")
        # Now use card_name and card_number for your DB queries
        logging.info(f"Selected card: {card_name}, Card Number: {card_number}") 
        card_data = db.get_card_data(connection, card_name, card_number)

        if card_data:
            price_data = db.get_price_date(
                connection, card_name, card_number)

            if price_data and len(price_data[0]):
                price_df = pd.DataFrame(price_data, columns=[
                    "date", "lowest_price", "market_price", "listing_quantity", "velocity"
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

            else:
                st.warning("Price data shape does not match expected columns.")
        else:
            st.info("No data found for this card.")

    tab1, tab2, tab3 = st.tabs(["Price Data", "Market vs Market Price", "Velocity"])
    with tab1:
        if price_df is not None:
            st.dataframe(price_df, use_container_width=True)
        else:
            st.write("No Data")

    with tab2:
        if fig is not None:
            fig.update_layout(
                template="plotly_white",
                xaxis_tickangle=-45,
                xaxis_title="Date",
                yaxis_title="Price",
                legend_title="Price Type",
                hovermode="x unified",
                bargap=0.2,
                font=dict(size=14),
                title_font=dict(size=20),
                plot_bgcolor="#f9f9f9",
                paper_bgcolor="#f9f9f9"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No Data")

    with tab3:
        if price_df is not None and "velocity" in price_df.columns:
            # Invert the velocity values
            price_df["velocity"] = -price_df["velocity"]
            velocity_fig = go.Figure()
            velocity_fig.add_trace(go.Scatter(
                x=price_df["date"],
                y=price_df["velocity"],
                mode="lines+markers",
                line=dict(width=3, color="#636EFA"),
                marker=dict(size=8),
                name="Velocity"
            ))
            velocity_fig.update_layout(
                template="plotly_white",
                xaxis_tickangle=-45,
                xaxis_title="Date",
                yaxis_title="Velocity (Inverted)",
                hovermode="x unified",
                font=dict(size=14),
                title=f"Velocity Over Time for {card_name} ({card_number})",
                plot_bgcolor="#f9f9f9",
                paper_bgcolor="#f9f9f9"
            )
            st.plotly_chart(velocity_fig, use_container_width=True)
        else:
            st.write("No Data")
            



# ------------------ Sidebar Theme Options ------------------
#st.title("TCG Tools")
# Initialize session state defaults
if "theme_selector" not in st.session_state:
    st.session_state.theme_selector = "Light"
if "font_size" not in st.session_state:
    st.session_state.font_size = 16
if "layout_width" not in st.session_state:
    st.session_state.layout_width = "centered"
    
with st.sidebar:
    st.markdown("## 🎨 Appearance Settings")

    st.session_state.theme_selector = st.selectbox(
        "Theme",
        options=["Light", "Dark", "Cyberpunk", "Forest"],
        index=["Light", "Dark", "Cyberpunk", "Forest"].index(st.session_state.theme_selector)
    )
    st.session_state.font_size = st.slider(
            "Font Size",
            min_value=12,
            max_value=28,
            value=st.session_state.font_size
        )

    st.session_state.layout_width = st.radio(
        "Page Layout",
        options=["centered", "wide"],
        index=0 if st.session_state.layout_width == "centered" else 1
    )

# ------------------ Apply Selected Theme ------------------

def apply_theme(theme, font_size, layout_width):
    layout_css = "max-width: 1000px;" if layout_width == "centered" else "max-width: 100%;"

    theme_css = {
        "Light": f"""
        body, .stApp {{
            background-color: #ffffff;
            color: #000000;
            font-size: {font_size}px;
            {layout_css}
        }}""",
        "Dark": f"""
        body, .stApp {{
            background-color: #0e1117;
            color: #fafafa;
            font-size: {font_size}px;
            {layout_css}
        }}""",
        "Cyberpunk": f"""
        body, .stApp {{
            background-color: #0f0f0f;
            color: #00ffff;
            font-size: {font_size}px;
            {layout_css}
        }}
        .stMarkdown, .stSelectbox label {{
            color: #ff00ff !important;
        }}""",
        "Forest": f"""
        body, .stApp {{
            background-color: #e8f5e9;
            color: #1b5e20;
            font-size: {font_size}px;
            {layout_css}
        }}"""
    }

    st.markdown(f"<style>{theme_css.get(theme, '')}</style>", unsafe_allow_html=True)

apply_theme(
    st.session_state.theme_selector,
    st.session_state.font_size,
    st.session_state.layout_width
)

