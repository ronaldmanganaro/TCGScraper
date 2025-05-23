import os 
import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    # Get the current script's directory
    current_dir = os.path.dirname(__file__)
    csv_path = os.path.join(current_dir, "TestInventory.csv")
    # Only load once, when not already in session state
    if "repricer_csv" not in st.session_state:
        try:
            st.session_state.repricer_csv = pd.read_csv(csv_path)  # Adjust path if needed
            st.toast("Test CSV loaded from repo.")
        except FileNotFoundError:
            st.error("CSV file not found. Check the path.")

def filter_data(df, min_price, max_price, min_listing, max_listing, product_line, set_name, search_text):
    filtered = df[
        (df["TCG Marketplace Price"] >= min_price) &
        (df["TCG Marketplace Price"] <= max_price) &
        (df["Total Quantity"] >= min_listing) &
        (df["Total Quantity"] <= max_listing) &
        (df["Product Line"] == product_line) &
        (df["Set Name"] == set_name) & 
        (df["Rarity"] == rarity_filter)  # Assuming rarity_filter is defined
    ]
    if search_text:
        filtered = filtered[filtered["Product Name"].str.contains(search_text, case=False, na=False)]
    return filtered

@st.cache_data
def convert_for_download(df):
    return df.to_csv().encode("utf-8")

df = load_data()
# Optional: let user upload instead
uploaded_file = st.file_uploader("Upload CSV", type=["csv"], )
if uploaded_file:
    st.session_state.repricer_csv = pd.read_csv(uploaded_file)
    st.success("CSV uploaded.")

if "repricer_csv" in st.session_state and not st.session_state.repricer_csv.empty:
    df = st.session_state.repricer_csv.copy()
    price_dif_df = df
    for row in price_dif_df.iterrows():
        # add a new column that is shows the percentage difference between the price and the market price need to round the percenttae difference to 2 decimal places
        price_dif_df.loc[row[0], "percentage_difference"] = (price_dif_df.loc[row[0], "TCG Marketplace Price"] - price_dif_df.loc[row[0], "TCG Market Price"]) / price_dif_df.loc[row[0], "TCG Market Price"] * 100  
    
    # for each column in the price_dif_df remove the column if it is not TCG Marketplace Price TCG Market Price TCG Market Price column
    price_dif_df = price_dif_df[["Product Line", "Set Name", "Product Name","Total Quantity", "TCG Marketplace Price", "TCG Market Price", "percentage_difference"]]
    
    
    
    tab1, tab2 = st.tabs(["Full Inventory", "Price Differentials"])    
    with tab1:
        st.dataframe(df, use_container_width=True)
    with tab2:
        st.dataframe(price_dif_df, use_container_width=True)
    
    
    # header for the filters
    st.markdown("### Filters")    
    filter_col1, filter_col2, filter_col3, filter_col4,filter_col5, filter_col6 = st.columns([2,2,1,1,1,1])
    with filter_col1: # dropdown menu with options pulled form the product line column
        product_line = st.selectbox(
            "Product Line",
            options=df["Product Line"].unique(),
            index=0,
            key="product_line_filter"
        )
        set_name = st.selectbox(
            "Set Name",
            options=df[df["Product Line"] == product_line]["Set Name"].unique(),
            index=0,
            key="set_name_filter"
        )

    with filter_col2:
        search_text = st.text_input(
            "Filter cards",
            "",
            placeholder="Type part of a card name or number..."
        )
    # create filter option for rarity that pulls from the options in the dataframe based on product line and set name
        rarity_filter = st.selectbox(
            "Rarity",
            options=df[(df["Product Line"] == product_line) & (df["Set Name"] == set_name)]["Rarity"].unique(),
            index=0,
            key="rarity_filter"
        )
    with filter_col3:
        min_listing = st.number_input(
            "Min Listings",
            min_value=0,
            value=0,
            step=1,
            key="min_inv_listing_filter"
        )
    with filter_col4:
        max_listing = st.number_input(
            "Max Listings",
            min_value=0,
            value=st.session_state.get("min_quantity_selectbox", 10000),  # Default to max listing quantity
            step=1,
            key="max_inv_listing_filter"
        )
    with filter_col5:
        min_price = st.number_input(
            "Min Price",
            min_value=0.0,
            value=0.0,
            step=0.01,
            key="min_price_filter"
        )
    with filter_col6:
        max_price = st.number_input(
            "Max Price",
            min_value=0,
            value=st.session_state.get("min_quantity_selectbox", 10000),  # Default to max listing quantity
            step=1,
            key="max_price_filter"
        )
        
    filter_btn_col1, filter_btn_col2 = st.columns([1,1])
    with filter_btn_col1:
        if st.button('Filter'):
            filtered_df = filter_data(df, min_price, max_price, min_listing, max_listing, product_line, set_name, search_text)
            st.session_state.filtered_df = pd.read_csv(filtered_df)
            st.dataframe(filtered_df, use_container_width=True)
    with filter_btn_col2:        
        if st.button("Reprice"):
            # Perform repricing logic here
            # For example, you can update the prices in the DataFrame
            df["new_price"] = df["price"] * 1.1  # Example: increase price by 10%
            st.dataframe(df, use_container_width=True)
            csv = None
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="data.csv",
                mime="text/csv",
                icon=":material/download:",
            )
        
        if st.download_button:
            if st.session_state.filtered_df not in st.session_state:
                csv = convert_for_download(st.session_state.repricer_csv)
            else:
                csv = convert_for_download(st.session_state.filtered_df)
