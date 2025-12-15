from functions import fetch_all_sales, db, widgets
import streamlit as st
import pandas as pd
import logging
import plotly.express as px
import plotly.graph_objects as go
import asyncio
import pyperclip
from psycopg2.extras import RealDictCursor

widgets.show_pages_sidebar()

price_df, fig = None, None
if 'card_list' not in st.session_state:
    st.session_state.card_list = []

# Create columns for the dropdown and number input
col1, col2 = st.columns([3, 1])

# New row for Query and Pull Historical Data buttons, aligned under the inputs
btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])

with btn_col1:
    if st.button("Query", use_container_width=True):

        with st.spinner("Querying..."):
            connection = db.connectDB("tcgplayerdb")
            try:
                cards = db.get_card_name(
                    connection, st.session_state.min_quantity_selectbox)
                st.session_state.card_list = [
                    f"{card[0]}, ({card[1]}) [Listings: {card[3]}]" for card in cards
                ]
                st.session_state.card_tuples = cards
            finally:
                try:
                    connection.close()
                except Exception:
                    pass
        st.toast("Query complete!")
        st.balloons()  # 🎈 Balloons animation

with btn_col2:
    if st.button("Pull Historical Data", use_container_width=True):
        selected_url = None
        if "card_tuples" in st.session_state:
            for card in st.session_state.card_tuples:
                if card[0] in st.session_state.pkm_selectbox:
                    selected_url = card[2]
                    break
        if selected_url:
            with st.spinner("Pulling historical data..."):
                logging.info(f"Scraping url {selected_url}...")
                asyncio.run(
                    fetch_all_sales.scrape_table_update_db(selected_url))
                st.rerun()
            st.balloons()  # 🎈 Balloons animation
        else:
            st.toast("No URL found for selected card.")

with btn_col3:
    if st.button("Copy Card Url", use_container_width=True):
        # Get the URL for the selected card
        selected_url = None
        if "card_tuples" in st.session_state:
            for card in st.session_state.card_tuples:
                if card[0] in st.session_state.pkm_selectbox:
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
        # Default to max listing quantity
        value=st.session_state.get("min_quantity_selectbox", 10000),
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
    connection = db.connectDB("tcgplayerdb")
    try:
        # Find the selected card's full tuple so we can get its stable link
        selected_link = None
        selected_label = st.session_state.pkm_selectbox
        if "card_tuples" in st.session_state:
            for card in st.session_state.card_tuples:
                label = f"{card[0]}, ({card[1]}) [Listings: {card[3]}]"
                if label == selected_label:
                    selected_link = card[2]
                    card_name = card[0]
                    card_number = card[1]
                    break

        if not selected_link:
            st.info("No data found for this card (missing link).")
        else:
            card_data = db.get_card_data(connection, card_name, card_number)
            if card_data:
                # Fetch full price history by link to avoid name/number mismatches
                price_data = db.get_price_date_by_link(connection, selected_link)

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
    finally:
        try:
            connection.close()
        except Exception:
            pass

tab1, tab2, tab3 = st.tabs(
    ["Price Data", "Market vs Market Price", "Velocity"])
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

st.markdown("---")
st.subheader("Underpriced Cards (Latest Snapshot from DB)")

col1, col2, col3 = st.columns(3)
with col1:
    latest_max_pct = st.slider(
        "Max lowest vs market %",
        min_value=10,
        max_value=100,
        value=70,
        step=5,
        help="Show cards where lowest_price is at most this % of market_price (latest date only).",
        key="latest_underpriced_max_pct",
    )
with col2:
    latest_min_qty = st.number_input(
        "Min listing quantity",
        min_value=1,
        value=4,
        step=1,
        key="latest_underpriced_min_qty",
    )
with col3:
    latest_max_qty = st.number_input(
        "Max listing quantity",
        min_value=1,
        value=20,
        step=1,
        key="latest_underpriced_max_qty",
    )

if st.button("Run Latest Snapshot Query", use_container_width=True, key="btn_latest_underpriced"):
    if latest_min_qty > latest_max_qty:
        st.error("Min quantity cannot be greater than max quantity.")
    else:
        sql = """
            WITH latest_date AS (
                SELECT MAX(date) AS dt
                FROM prices
            )
            SELECT
                p.card,
                p.link,
                p.lowest_price,
                p.market_price,
                p.listing_quantity,
                ROUND(
                    (p.lowest_price / NULLIF(p.market_price, 0)) * 100,
                    2
                ) AS lowest_vs_market_pct
            FROM prices p
            JOIN latest_date ld
              ON p.date = ld.dt
            WHERE p.lowest_price IS NOT NULL
              AND p.market_price IS NOT NULL
              AND p.lowest_price > 0
              AND p.lowest_price <= p.market_price * %s
              AND p.listing_quantity >= %s
              AND p.listing_quantity <= %s
            ORDER BY lowest_vs_market_pct ASC, p.market_price DESC;
        """
        conn = db.connectDB("tcgplayerdb")
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (latest_max_pct / 100.0, latest_min_qty, latest_max_qty))
                rows = cur.fetchall()
            latest_df = pd.DataFrame(rows)
        except Exception as e:
            st.error(f"Error running latest snapshot query: {e}")
            latest_df = None
        finally:
            conn.close()

        if latest_df is None or latest_df.empty:
            st.info("No results for the selected filters.")
        else:
            if "link" in latest_df.columns:
                latest_df["link"] = latest_df["link"].apply(lambda url: f"[Open]({url})" if url else "")
            st.dataframe(latest_df, use_container_width=True)

widgets.footer()
