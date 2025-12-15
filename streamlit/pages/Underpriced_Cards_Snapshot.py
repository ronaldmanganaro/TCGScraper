import streamlit as st
import pandas as pd

from functions import db, widgets

widgets.show_pages_sidebar()


def render_clickable_table(df: pd.DataFrame):
    """Render a DataFrame as an HTML table where the Link column is clickable."""
    cols = df.columns.tolist()
    html = ["<table style='width:100%; border-collapse: collapse;'>"]
    html.append("<thead><tr>")
    for c in cols:
        html.append(
            f"<th style='border: 1px solid #ddd; padding: 4px; text-align:left;'>{c}</th>"
        )
    html.append("</tr></thead><tbody>")

    for _, row in df.iterrows():
        html.append("<tr>")
        for c in cols:
            val = row[c]
            if c == "Link" and isinstance(val, str) and val:
                cell = f"<a href='{val}' target='_blank'>Link</a>"
            else:
                cell = str(val)
            html.append(
                f"<td style='border: 1px solid #ddd; padding: 4px; text-align:left;'>{cell}</td>"
            )
        html.append("</tr>")
    html.append("</tbody></table>")

    st.markdown("".join(html), unsafe_allow_html=True)


st.title("Underpriced Cards (Latest Snapshot)")
st.write(
    "Search for cards where the TCG Market Price is significantly above the current lowest price "
    "based on the latest snapshot in the database."
)

col1, col2, col3 = st.columns(3)
with col1:
    max_pct = st.number_input(
        "Min % Above Lowest",
        min_value=0.0,
        max_value=1000.0,
        value=25.0,
        step=1.0,
        help="Minimum percentage that Market Price must be above Lowest Price.",
        key="snapshot_min_pct",
    )
with col2:
    min_qty = st.number_input(
        "Min Listing Quantity",
        min_value=0,
        max_value=10000,
        value=0,
        step=1,
        help="Ignore cards whose latest listing quantity is below this.",
        key="snapshot_min_qty",
    )
with col3:
    max_qty = st.number_input(
        "Max Listing Quantity",
        min_value=1,
        max_value=10000,
        value=100,
        step=1,
        help="Ignore cards whose latest listing quantity is above this.",
        key="snapshot_max_qty",
    )

if st.button("Find Underpriced Cards", use_container_width=True, key="snapshot_find_btn"):
    with st.spinner("Querying latest snapshot for underpriced cards..."):
        conn = db.connectDB("tcgplayerdb")
        try:
            cur = conn.cursor()
            cur.execute(
                """
                WITH latest AS (
                    SELECT DISTINCT ON (card, card_number)
                        card,
                        card_number,
                        set_name,
                        lowest_price,
                        market_price,
                        listing_quantity,
                        link,
                        date
                    FROM public.prices
                    WHERE lowest_price IS NOT NULL
                      AND market_price IS NOT NULL
                      AND lowest_price > 0
                    ORDER BY card, card_number, date DESC
                )
                SELECT card, card_number, set_name,
                       lowest_price, market_price, listing_quantity, link
                FROM latest
                WHERE listing_quantity BETWEEN %s AND %s
                  AND market_price >= lowest_price * (1 + %s)
                ORDER BY (market_price - lowest_price) DESC
                LIMIT 500
                """,
                (int(min_qty), int(max_qty), float(max_pct) / 100.0),
            )
            rows = cur.fetchall()
        finally:
            conn.close()

    if rows:
        df = pd.DataFrame(
            rows,
            columns=[
                "Card", "Card Number", "Set", "Lowest Price",
                "Market Price", "Listing Quantity", "Link",
            ],
        )
        # Ensure numeric types for price columns
        df["Lowest Price"] = pd.to_numeric(df["Lowest Price"], errors="coerce")
        df["Market Price"] = pd.to_numeric(df["Market Price"], errors="coerce")

        df["Diff"] = df["Market Price"] - df["Lowest Price"]
        df["% Above Lowest"] = ((df["Market Price"] / df["Lowest Price"] - 1) * 100).round(2)

        # Keep Card as plain text and add a separate clickable Link column
        df["Link"] = df["Link"].fillna("").astype(str)

        render_clickable_table(df)
        st.success(f"Found {len(df)} potentially underpriced cards.")
    else:
        st.info("No underpriced cards found with the current criteria.")

widgets.footer()