from functions import widgets
import streamlit as st
import os 
import pandas as pd
widgets.show_pages_sidebar()


def sidebar(df):
    st.markdown("### 🔍 Inventory Management")
    with st.expander("Filter Options", expanded=True):
        # Basic Filters
        st.markdown("### 🔧 Hide Columns")
        all_columns = df.columns.tolist()
        essential_columns = [
            "Product Line", "Set Name", "Product Name", "Total Quantity",
            "TCG Marketplace Price", "TCG Market Price"
        ]
        columns_to_display = st.radio(
            "Select columns to display:",
            options=["All Columns", "Essential Columns", "Custom Columns"],
            index=0,
            key="sidebar_columns_radio"
        )
        if columns_to_display == "All Columns":
            selected_columns = all_columns
        elif columns_to_display == "Essential Columns":
            selected_columns = essential_columns
        else:
            selected_columns = st.multiselect(
                "Select columns to display:",
                options=all_columns,
                default=essential_columns,
                key="sidebar_columns_multiselect"
            )
        
        search_text = st.text_input(
            "Filter cards", "", placeholder="Type part of a card name or number..."
        )
        product_line = st.selectbox(
            "Product Line", options=["All"] + df["Product Line"].unique().tolist(), index=0
        )
        set_name = st.selectbox(
            "Set Name", options=["All"] + df[df["Product Line"] == product_line]["Set Name"].unique().tolist() if product_line != "All" else ["All"], index=0
        )
        rarity_filter = st.selectbox(
            "Rarity", options=["All"] + df[(df["Product Line"] == product_line) & (df["Set Name"] == set_name)]["Rarity"].unique().tolist() if set_name != "All" else ["All"], index=0
        )

        st.markdown("---")

        # Listings Range
        st.markdown("#### 📊 Listings Range")
        if "listings_range" not in st.session_state:
            st.session_state["listings_range"] = (0, 100)

        listings_min = st.number_input(
            "Listings Min",
            min_value=0,
            max_value=100,
            value=st.session_state["listings_range"][0],
            step=1,
            key="listings_min_input"
        )
        listings_max = st.number_input(
            "Listings Max",
            min_value=0,
            max_value=100,
            value=st.session_state["listings_range"][1],
            step=1,
            key="listings_max_input"
        )
        st.session_state["listings_range"] = (listings_min, listings_max)

        # Price Range
        st.markdown("#### 💲 Price Range")
        if "price_range" not in st.session_state:
            st.session_state["price_range"] = (0.0, 1000.0)

        price_min = st.number_input(
            "Price Min",
            min_value=0.0,
            max_value=1000.0,
            value=st.session_state["price_range"][0],
            step=0.01,
            key="price_min_input"
        )
        price_max = st.number_input(
            "Price Max",
            min_value=0.0,
            max_value=1000.0,
            value=st.session_state["price_range"][1],
            step=0.01,
            key="price_max_input"
        )
        st.session_state["price_range"] = (price_min, price_max)

        # Add a floor price input
        st.markdown("### Set Floor Price")
        if "floor_price" not in st.session_state:
            st.session_state.floor_price = 0.0

        floor_price = st.number_input(
            "Floor Price (USD)",
            min_value=0.0,
            max_value=1000.0,
            value=st.session_state.floor_price,
            step=0.01,
            help="Cards priced below this value will not be included in repricing suggestions."
        )
        st.session_state.floor_price = floor_price

        # Apply Filters Button
        if st.button("Apply Filters"):
            filtered_df = filter_data(
                df,
                price_min,
                price_max,
                listings_min,
                listings_max,
                product_line,
                set_name,
                rarity_filter,
                search_text
            )
            st.session_state.filtered_df = filtered_df
            st.session_state.suggested_repricing_df = None  # Clear old suggestions
            st.success("Filters applied! Check the 'Filtered Cards' tab.")
            st.rerun()  # Force the interface to refresh

        # Clear All Filters Button
        if st.button("Clear All Filters"):
            st.session_state["listings_range"] = (0, 100)
            st.session_state["price_range"] = (0.0, 1000.0)
            st.session_state.filtered_df = None
            st.success("Filters cleared!")
            st.rerun()  # Force the interface to refresh

        return selected_columns


def load_data():
    # Get the current script's directory
    current_dir = os.path.dirname(__file__)
    csv_path = os.path.join(current_dir, "TestInventory.csv")
    # Only load once, when not already in session_state
    if "repricer_csv" not in st.session_state:
        try:
            st.session_state.repricer_csv = pd.read_csv(
                csv_path)  # Adjust path if needed
            st.toast("Test CSV loaded from repo.")
        except FileNotFoundError:
            st.toast("CSV file not found. Check the path.")

def inventory_tabs(df, selected_columns):
    tab1, tab2, tab3 = st.tabs([
        "Full Inventory", "Price Differentials", "Filtered Cards"
    ])
    with tab1:
        st.dataframe(st.session_state.repricer_csv[selected_columns], use_container_width=True)
        total_marketplace_value = (st.session_state.repricer_csv["Total Quantity"] * st.session_state.repricer_csv["TCG Marketplace Price"]).sum()
        total_market_value = (st.session_state.repricer_csv["Total Quantity"] * st.session_state.repricer_csv["TCG Market Price"]).sum()
        st.write(f"**Total Marketplace Value (Quantity x Marketplace Price):** ${total_marketplace_value:.2f}")
        st.write(f"**Total Market Value (Quantity x Market Price):** ${total_market_value:.2f}")
    with tab2:
        price_dif_df = df.copy()
        price_dif_df["percentage_difference"] = (
            (price_dif_df["TCG Marketplace Price"] - price_dif_df["TCG Market Price"]) /
            price_dif_df["TCG Market Price"] * 100
        ).round(2)
        st.dataframe(
            price_dif_df[selected_columns + ["percentage_difference"]], use_container_width=True
        )
    with tab3:
        if "filtered_df" in st.session_state and st.session_state.filtered_df is not None:
            st.dataframe(
                st.session_state.filtered_df[selected_columns], use_container_width=True
            )
            if st.button("Refresh Filtered Cards", key="refresh_filtered_cards"):
                st.rerun()
        else:
            st.info(
                "No filters applied yet. Use the Filter Options tab to filter cards."
            )

def inventory_summary_tab(df):
    summary_tab1, summary_tab2 = st.tabs(["Full Inventory", "Filtered Cards"])
    with summary_tab1:
        # Total unique cards
        total_unique_cards = df["Product Name"].nunique()
        st.write(f"**Total Unique Cards:** {total_unique_cards}")

        # Total market price times quantity
        total_market_value = (df["Total Quantity"] *
                              df["TCG Market Price"]).sum()
        st.write(
            f"**Total Market Value (Quantity x Market Price):** ${total_market_value:.2f}"
        )

        # Total quantity of cards
        total_quantity = df["Total Quantity"].sum()
        st.write(f"**Total Quantity of Cards:** {total_quantity}")

        # Rarity Counts
        rarity_counts = df["Rarity"].value_counts()
        st.write("**Rarity Counts:**")
        # Transpose the DataFrame to show rarity names on top and autosize
        st.dataframe(rarity_counts.to_frame().T, use_container_width=True)

        # Average Market Price
        avg_market_price = df["TCG Market Price"].mean()
        st.write(f"**Average Market Price:** ${avg_market_price:.2f}")

        # Average Marketplace Price
        avg_marketplace_price = df["TCG Marketplace Price"].mean()
        st.write(
            f"**Average Marketplace Price:** ${avg_marketplace_price:.2f}"
        )

        # Total marketplace value and total market value
        total_marketplace_value = (df["Total Quantity"] * df["TCG Marketplace Price"]).sum()
        total_market_value = (df["Total Quantity"] * df["TCG Market Price"]).sum()
        st.write(f"**Total Marketplace Value (Quantity x Marketplace Price):** ${total_marketplace_value:.2f}")
        st.write(f"**Total Market Value (Quantity x Market Price):** ${total_market_value:.2f}")
    with summary_tab2:
        if st.session_state.filtered_df is not None:
            # Total unique cards in filtered data
            filtered_unique_cards = st.session_state.filtered_df["Product Name"].nunique(
            )
            st.write(
                f"**Total Unique Cards (Filtered):** {filtered_unique_cards}")

            # Total market price times quantity in filtered data
            filtered_market_value = (
                st.session_state.filtered_df["Total Quantity"] *
                st.session_state.filtered_df["TCG Market Price"]
            ).sum()
            st.write(
                f"**Total Market Value (Filtered):** ${filtered_market_value:.2f}"
            )

            # Total quantity of cards in filtered data
            filtered_total_quantity = st.session_state.filtered_df["Total Quantity"].sum(
            )
            st.write(
                f"**Total Quantity of Cards (Filtered):** {filtered_total_quantity}")

            # Rarity Counts in filtered data
            filtered_rarity_counts = st.session_state.filtered_df["Rarity"].value_counts(
            )
            st.write("**Rarity Counts (Filtered):**")
            # Transpose the DataFrame for filtered rarity counts and autosize
            st.dataframe(filtered_rarity_counts.to_frame().T, use_container_width=True)

            # Average Market Price in filtered data
            filtered_avg_market_price = st.session_state.filtered_df["TCG Market Price"].mean(
            )
            st.write(
                f"**Average Market Price (Filtered):** ${filtered_avg_market_price:.2f}")

            # Average Marketplace Price in filtered data
            filtered_avg_marketplace_price = st.session_state.filtered_df["TCG Marketplace Price"].mean(
            )
            st.write(
                f"**Average Marketplace Price (Filtered):** ${filtered_avg_marketplace_price:.2f}"
            )

            # Total marketplace value and total market value in filtered data
            filtered_marketplace_value = (
                st.session_state.filtered_df["Total Quantity"] *
                st.session_state.filtered_df["TCG Marketplace Price"]
            ).sum()
            filtered_market_value = (
                st.session_state.filtered_df["Total Quantity"] *
                st.session_state.filtered_df["TCG Market Price"]
            ).sum()
            st.write(f"**Total Marketplace Value (Filtered):** ${filtered_marketplace_value:.2f}")
            st.write(f"**Total Market Value (Filtered):** ${filtered_market_value:.2f}")
        else:
            st.info("No filters applied. Use the Filter Options to filter cards.")

@st.cache_data
def filter_data(df, min_price, max_price, min_listing, max_listing, product_line, set_name, rarity_filter, search_text):
    """
    Filter the inventory based on user inputs.
    """
    filtered = df[
        (df["TCG Marketplace Price"] >= min_price) &
        (df["TCG Marketplace Price"] <= max_price) &
        (df["Total Quantity"] >= min_listing) &
        (df["Total Quantity"] <= max_listing)
    ]

    # Apply filters only if specific values are selected (not "All")
    if product_line and product_line != "All":
        filtered = filtered[filtered["Product Line"] == product_line]
    if set_name and set_name != "All":
        filtered = filtered[filtered["Set Name"] == set_name]
    if rarity_filter and rarity_filter != "All":
        filtered = filtered[filtered["Rarity"] == rarity_filter]

    # Apply search text filter
    if search_text:
        filtered = filtered[filtered["Product Name"].str.contains(
            search_text, case=False, na=False)]

    return filtered


def main():
    # Allow user to upload a CSV file
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"], key="inventory_csv_uploader")
    # If user removes the file (presses X), clear session state and show only uploader
    if uploaded_file:
        st.session_state.repricer_csv = pd.read_csv(uploaded_file)
        st.toast("CSV uploaded.")
    elif "repricer_csv" in st.session_state:
        # If file is removed, clear all related session state
        del st.session_state.repricer_csv
        if "filtered_df" in st.session_state:
            del st.session_state.filtered_df
        st.info("Please upload a CSV file to begin managing your inventory.")
        return

    # Only proceed if a CSV is uploaded and loaded
    if "repricer_csv" not in st.session_state or st.session_state.repricer_csv is None or st.session_state.repricer_csv.empty:
        st.info("Please upload a CSV file to begin managing your inventory.")
        return

    # Initialize session state variables
    if "filtered_df" not in st.session_state:
        st.session_state.filtered_df = None

    df = st.session_state.repricer_csv
    with st.sidebar:
        selected_columns = sidebar(df)
    inventory_management, inventory_analytics = st.tabs([
        "📦 Inventory Management", "📊 Inventory Summary"
    ])
    
    with inventory_management:
        inventory_tabs(df, selected_columns)
        

    with inventory_analytics:
        inventory_summary_tab(df)
    widgets.footer()


if __name__ == "__main__":
    main()
