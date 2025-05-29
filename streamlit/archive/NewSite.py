import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="TCG Seller Tools", layout="wide")

st.title("📦 TCG Seller Tools")
st.markdown("Tools for Magic: The Gathering and Pokémon card sellers")

tabs = st.tabs(["Home", "Price Lookup", "Booster Box EV", "Sales Tracker", "Inventory Manager", "Profit Calculator"])

with tabs[0]:
    st.header("Welcome to TCG Seller Tools")
    st.markdown("This platform helps TCG sellers track value, simulate profits, manage inventory, and more!")
    st.markdown("Choose a tab to get started.")

with tabs[1]:  # Price Lookup
    st.header("🔍 Price Lookup Tool")
    game = st.selectbox("Select Game", ["Magic: The Gathering", "Pokémon"])
    card_name = st.text_input("Enter card name")

    if card_name:
        if game == "Magic: The Gathering":
            url = f"https://api.scryfall.com/cards/named?fuzzy={card_name}"
            r = requests.get(url)
            if r.status_code == 200:
                data = r.json()
                st.image(data['image_uris']['normal'])
                st.write(f"**{data['name']}**")
                st.write(f"Set: {data['set_name']}")
                st.write(f"Market Price: ${data['prices']['usd']}")
            else:
                st.error("Card not found.")

        elif game == "Pokémon":
            url = f"https://api.pokemontcg.io/v2/cards?q=name:{card_name}"
            r = requests.get(url, headers={"X-Api-Key": "YOUR_POKEMON_API_KEY"})
            if r.status_code == 200:
                data = r.json()['data']
                if data:
                    card = data[0]
                    st.image(card['images']['large'])
                    st.write(f"**{card['name']}**")
                    st.write(f"Set: {card['set']['name']}")
                    st.write(f"Market Price: ${card.get('cardmarket', {}).get('prices', {}).get('averageSellPrice', 'N/A')}")
                else:
                    st.error("Card not found.")
            else:
                st.error("API error.")

with tabs[2]:  # Booster Box EV Calculator
    st.header("📦 Booster Box EV Calculator")
    st.markdown("(Coming soon – simulate average value of opening booster boxes)")

with tabs[3]:  # Sales Tracker
    st.header("📊 Sales Tracker")
    uploaded_file = st.file_uploader("Upload your sales CSV", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df)
        st.write("**Total Revenue:** $", df['Sale Price'].sum())
        df['Date'] = pd.to_datetime(df['Date'])
        sales_by_day = df.groupby(df['Date'].dt.date)['Sale Price'].sum()
        st.line_chart(sales_by_day)

with tabs[4]:  # Inventory Manager
    st.header("📋 Inventory Manager")
    st.markdown("(Coming soon – track your current inventory and valuations)")

with tabs[5]:  # Profit Calculator
    st.header("💰 Profit Margin Calculator")
    purchase_cost = st.number_input("Purchase Cost", min_value=0.0)
    sale_price = st.number_input("Sale Price", min_value=0.0)
    fees = st.number_input("Platform Fees (e.g. eBay, TCGPlayer)", min_value=0.0)
    shipping = st.number_input("Shipping Cost", min_value=0.0)
    tax = st.number_input("Taxes", min_value=0.0)

    if st.button("Calculate Profit"):
        net = sale_price - (purchase_cost + fees + shipping + tax)
        margin = (net / purchase_cost * 100) if purchase_cost else 0
        st.write(f"**Net Profit:** ${net:.2f}")
        st.write(f"**Profit Margin:** {margin:.2f}%")
