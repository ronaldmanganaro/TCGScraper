from functions import fetch_all_sales, db, widgets
import streamlit as st
import pandas as pd
import logging
import plotly.express as px
import plotly.graph_objects as go
import asyncio
from math import ceil

widgets.show_pages_sidebar()

price_df, fig = None, None
if 'card_list' not in st.session_state:
    st.session_state.card_list = []

# --- Top row: dropdown | Min/Max listings | Query button (unchanged, fast) ---
col1, col2, col3 = st.columns([3, 2, 1])

with col1:
    pkm_selectbox = st.selectbox(
        "Pokemon Card Name, Card Number",
        st.session_state.card_list,
        index=0 if st.session_state.card_list else None,
        key="pkm_selectbox",
    )

    # Clickable TCGPlayer link under dropdown
    selected_url = None
    selected_label = st.session_state.get("pkm_selectbox")
    if selected_label and "card_tuples" in st.session_state:
        for card in st.session_state.card_tuples:
            label = f"{card[0]}, ({card[1]}) [Listings: {card[3]}]"
            if label == selected_label:
                selected_url = card[2]
                break
    if selected_url:
        st.markdown(f"[**TCGPlayer Link**]({selected_url})")

with col2:
    min_col, max_col = st.columns(2)
    with min_col:
        min_listing = st.number_input(
            "Min Listings",
            min_value=0,
            max_value=10000,
            value=st.session_state.get("min_listing", 0),
            step=1,
            key="min_listing",
        )
    with max_col:
        max_listing = st.number_input(
            "Max Listings",
            min_value=1,
            max_value=10000,
            value=st.session_state.get("max_listing", 5),
            step=1,
            key="max_listing",
        )

with col3:
    st.caption(
        "Query loads cards whose current listing count is between Min and Max Listings."
    )
    if st.button("Query", use_container_width=True):
        with st.spinner("Querying..."):
            connection = db.connectDB("tcgplayerdb")
            try:
                cards = db.get_card_name(
                    connection, st.session_state.get("max_listing", 5)
                )
                min_l = st.session_state.get("min_listing", 0)
                cards = [c for c in cards if c[3] >= min_l]
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
        st.balloons()

# --- Underpriced search section: ONLY runs when its own button is clicked ---
st.markdown("---")
st.subheader("Market Price Anomalies")

opt_col1, opt_col2, opt_col3 = st.columns(3)
with opt_col1:
    pct_threshold = st.number_input(
        "Min % Above Lowest",
        min_value=0.0,
        max_value=1000.0,
        value=st.session_state.get("underpriced_min_pct", 25.0),
        step=1.0,
        help="Minimum percentage that Market Price must be above Lowest Price.",
        key="underpriced_min_pct",
    )
with opt_col2:
    diff_threshold = st.number_input(
        "Min $ Difference",
        min_value=0.0,
        max_value=10000.0,
        value=st.session_state.get("underpriced_min_diff", 0.0),
        step=0.1,
        help="Minimum absolute dollar gap between Market and Lowest price.",
        key="underpriced_min_diff",
    )
with opt_col3:
    min_listings_under = st.number_input(
        "Min Listings (Card)",
        min_value=0,
        max_value=10000,
        value=st.session_state.get("underpriced_min_listings", 0),
        step=1,
        help="Ignore cards whose latest listing quantity is below this.",
        key="underpriced_min_listings",
    )

col_anom_btn, _ = st.columns([1, 3])
with col_anom_btn:
    if st.button("Find Underpriced Cards", use_container_width=True):
        if "card_tuples" not in st.session_state or not st.session_state.card_tuples:
            st.info("Run Query first to load cards into the dropdown.")
        else:
            total_cards = len(st.session_state.card_tuples)
            st.write(f"Scanning **{total_cards}** cards for underpriced opportunities...")
            if total_cards > 500:
                st.warning(
                    "Large result set detected. This search may take a bit longer than usual "
                    "(you can narrow it with Min/Max Listings)."
                )

            with st.spinner("Searching for underpriced cards in the current dropdown..."):
                conn = db.connectDB("tcgplayerdb")
                try:
                    cur = conn.cursor()
                    card_keys = [(c[0], c[1]) for c in st.session_state.card_tuples]
                    values_clause = ",".join(["(%s,%s)"] * len(card_keys))
                    params = []
                    for name, num in card_keys:
                        params.extend([name, num])

                    params.extend([
                        int(min_listings_under),
                        float(pct_threshold) / 100.0,
                        float(diff_threshold),
                    ])

                    query = f"""
                        WITH selected_cards(card, card_number) AS (
                            VALUES {values_clause}
                        )
                        SELECT p.card, p.card_number, p.set_name,
                               p.lowest_price, p.market_price, p.listing_quantity, p.link
                        FROM public.prices p
                        JOIN selected_cards s
                          ON p.card = s.card AND p.card_number = s.card_number
                        WHERE p.date = (
                            SELECT MAX(date) FROM public.prices p2
                            WHERE p2.card = p.card AND p2.card_number = p.card_number
                        )
                          AND p.lowest_price IS NOT NULL
                          AND p.market_price IS NOT NULL
                          AND p.lowest_price > 0
                          AND p.listing_quantity >= %s
                          AND p.market_price >= p.lowest_price * (1 + %s)
                          AND (p.market_price - p.lowest_price) >= %s
                        ORDER BY (p.market_price - p.lowest_price) DESC
                        LIMIT 200
                    """
                    cur.execute(query, params)
                    rows = cur.fetchall()
                finally:
                    try:
                        conn.close()
                    except Exception:
                        pass

            if rows:
                anom_df = pd.DataFrame(
                    rows,
                    columns=[
                        "Card", "Card Number", "Set", "Lowest Price", "Market Price",
                        "Listing Quantity", "Link",
                    ],
                )
                anom_df["Diff"] = anom_df["Market Price"] - anom_df["Lowest Price"]
                anom_df["% Above Lowest"] = (
                    (anom_df["Market Price"] / anom_df["Lowest Price"] - 1) * 100
                ).round(2)
                st.session_state["underpriced_cards_df"] = anom_df
                st.success(f"Found {len(anom_df)} potentially underpriced cards.")
            else:
                st.session_state["underpriced_cards_df"] = None
                st.info("No underpriced cards found with current criteria.")

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
                    # NOTE: price_data from DB is [date, lowest_price, market_price, listing_quantity, velocity]
                    price_df = pd.DataFrame(price_data, columns=[
                        "date", "lowest_price", "market_price", "listing_quantity", "velocity"
                    ])
                    # Removed the column swap so lowest_price and market_price map directly
                    price_df["date"] = pd.to_datetime(price_df["date"])
                    price_df["lowest_price"] = price_df["lowest_price"].astype(float)
                    price_df["market_price"] = price_df["market_price"].astype(float)
                    price_df = price_df.sort_values("date")

                    # Line chart: Lowest vs Market price over time
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=price_df["date"],
                        y=price_df["lowest_price"],
                        mode="lines+markers",
                        name="Lowest Price",
                    ))
                    fig.add_trace(go.Scatter(
                        x=price_df["date"],
                        y=price_df["market_price"],
                        mode="lines+markers",
                        name="Market Price",
                    ))

                    fig.update_layout(
                        title=f"Lowest vs Market Price for {card_name} ({card_number})",
                        xaxis_title="Date",
                        yaxis_title="Price",
                        hovermode="x unified",
                        xaxis_tickangle=-45,
                    )

                else:
                    st.warning("Price data shape does not match expected columns.")
            else:
                st.info("No data found for this card.")
    finally:
        try:
            connection.close()
        except Exception:
            pass

# Extend tabs to include Underpriced Cards view
if 'underpriced_cards_df' in st.session_state:
    tab1, tab2, tab3, tab4 = st.tabs([
        "Price Data", "Lowest vs Market Price", "Velocity", "Underpriced Cards",
    ])
else:
    tab1, tab2, tab3 = st.tabs([
        "Price Data", "Lowest vs Market Price", "Velocity",
    ])
    tab4 = None

with tab1:
    if price_df is not None:
        st.dataframe(price_df, use_container_width=True)
    else:
        st.write("No Data")

with tab2:
    if fig is not None:
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

if tab4 is not None:
    with tab4:
        if st.session_state.get("underpriced_cards_df") is not None:
            st.dataframe(st.session_state["underpriced_cards_df"], use_container_width=True)
        else:
            st.write("Run 'Find Underpriced Cards' to see results.")

widgets.footer()
