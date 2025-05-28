import streamlit as st

st.set_page_config(page_title="TCG Seller Tools", layout="wide")

st.sidebar.image("https://upload.wikimedia.org/wikipedia/en/thumb/5/5f/Magic_the_gathering-card_back.jpg/220px-Magic_the_gathering-card_back.jpg", width=100)
st.sidebar.image("https://upload.wikimedia.org/wikipedia/en/thumb/3/3b/Pok%C3%A9mon_Trading_Card_Game_logo.svg/2560px-Pok%C3%A9mon_Trading_Card_Game_logo.svg.png", width=150)

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "🏠 Home",
    "💰 Price Lookup",
    "📦 Inventory Manager",
    "📈 Sales Tracker",
    "📊 Profit Calculator"
])

if page == "🏠 Home":
    st.title("Welcome to TCG Seller Tools")
    st.markdown("""
        This app is built for sellers of **Magic: The Gathering** and **Pokémon** TCGs.

        Use the sidebar to access:
        - Live price lookups
        - Inventory management
        - Sales analytics
        - Profit calculators
    """)

elif page == "💰 Price Lookup":
    st.title("Price Lookup")
    st.write("Search for Magic or Pokémon cards and get current listings and market value.")
    # Placeholder UI
    card_name = st.text_input("Enter card name")
    tcg = st.selectbox("Select TCG", ["Magic: The Gathering", "Pokémon"])
    if st.button("Lookup"):
        st.info(f"Would query Scryfall (MTG) or TCGPlayer (Pokémon) for: {card_name}")

elif page == "📦 Inventory Manager":
    st.title("Inventory Manager")
    st.write("Upload your card inventory and track stock levels.")
    uploaded_file = st.file_uploader("Upload CSV file with card inventory", type=["csv"])
    if uploaded_file:
        st.success("File uploaded successfully")
        # Here you'd parse and show preview

elif page == "📈 Sales Tracker":
    st.title("Sales Tracker")
    st.write("Upload your sales data and analyze revenue over time.")
    sales_file = st.file_uploader("Upload sales CSV", type=["csv"])
    if sales_file:
        st.success("Sales data uploaded")
        # Analysis would go here

elif page == "📊 Profit Calculator":
    st.title("Profit Calculator")
    st.write("Estimate profit margins per card or collection.")
    buy_price = st.number_input("Buy Price", min_value=0.0, format="%.2f")
    sell_price = st.number_input("Sell Price", min_value=0.0, format="%.2f")
    if st.button("Calculate Profit"):
        profit = sell_price - buy_price
        margin = (profit / buy_price) * 100 if buy_price > 0 else 0
        st.metric("Profit", f"${profit:.2f}")
        st.metric("Profit Margin", f"{margin:.1f}%")
