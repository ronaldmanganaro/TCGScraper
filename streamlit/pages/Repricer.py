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
            st.session_state.repricer_csv = pd.read_csv(
                csv_path)  # Adjust path if needed
            st.toast("Test CSV loaded from repo.")
        except FileNotFoundError:
            st.error("CSV file not found. Check the path.")


@st.cache_data
def filter_data(df, min_price, max_price, min_listing, max_listing, product_line, set_name, rarity_filter, search_text):
    filtered = df[
        (df["TCG Marketplace Price"] >= min_price) &
        (df["TCG Marketplace Price"] <= max_price) &
        (df["Total Quantity"] >= min_listing) &
        (df["Total Quantity"] <= max_listing) &
        (df["Product Line"] == product_line) &
        (df["Set Name"] == set_name) &
        (df["Rarity"] == rarity_filter)
    ]
    if search_text:
        filtered = filtered[filtered["Product Name"].str.contains(
            search_text, case=False, na=False)]
    return filtered


@st.cache_data
def convert_for_download(df):
    return df.to_csv(index=False).encode("utf-8")


@st.cache_data
def analyze_repricing(df, threshold=10):
    """
    Analyze the inventory and suggest cards for repricing based on a percentage difference threshold.
    """
    analysis_df = df.copy()
    analysis_df["percentage_difference"] = (
        (analysis_df["TCG Marketplace Price"] - analysis_df["TCG Market Price"]) /
        analysis_df["TCG Market Price"] * 100
    ).round(2)

    # Suggest new prices based on the threshold
    analysis_df["suggested_price"] = analysis_df["TCG Market Price"] * \
        (1 + threshold / 100)

    # Filter cards where the percentage difference exceeds the threshold
    suggested_repricing = analysis_df[
        (analysis_df["percentage_difference"].abs() > threshold)
    ]

    return suggested_repricing


# Load data
load_data()

# Allow user to upload a CSV file
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
if uploaded_file:
    st.session_state.repricer_csv = pd.read_csv(uploaded_file)
    st.toast("CSV uploaded.")

# Initialize session state variables
if "filtered_df" not in st.session_state:
    st.session_state.filtered_df = None

if "repricer_csv" in st.session_state and not st.session_state.repricer_csv.empty:
    df = st.session_state.repricer_csv.copy()

    # Tabs for inventory, price differentials, and filtered cards
    with st.expander("Inventory Management", expanded=True):
        # Add hide columns functionality
        st.markdown("### 🔧 Hide Columns")
        columns_to_display = st.radio(
            "Select columns to display:",
            options=["All Columns", "Essential Columns", "Custom Columns"],
            index=0
        )

        # Define column sets
        all_columns = df.columns.tolist()
        essential_columns = [
            "Product Line", "Set Name", "Product Name", "Total Quantity",
            "TCG Marketplace Price", "TCG Market Price"
        ]

        # Handle column selection
        if columns_to_display == "All Columns":
            selected_columns = all_columns
        elif columns_to_display == "Essential Columns":
            selected_columns = essential_columns
        else:
            selected_columns = st.multiselect(
                "Select columns to display:",
                options=all_columns,
                default=essential_columns
            )

        tab1, tab2, tab3 = st.tabs(
            ["Full Inventory", "Price Differentials", "Filtered Cards"]
        )

        # Full Inventory Tab
        with tab1:
            st.dataframe(df[selected_columns], use_container_width=True)

        # Price Differentials Tab
        with tab2:
            price_dif_df = df.copy()
            price_dif_df["percentage_difference"] = (
                (price_dif_df["TCG Marketplace Price"] - price_dif_df["TCG Market Price"]) /
                price_dif_df["TCG Market Price"] * 100
            ).round(2)

            # Apply selected columns to the Price Differentials tab
            st.dataframe(
                price_dif_df[selected_columns + ["percentage_difference"]], use_container_width=True)

        # Filtered Cards Tab
        with tab3:
            if "filtered_df" in st.session_state and st.session_state.filtered_df is not None:
                st.dataframe(
                    st.session_state.filtered_df[selected_columns], use_container_width=True)
            else:
                st.info(
                    "No filters applied yet. Use the Filter Options below to filter cards."
                )

    # Filters
    with st.expander("Filter Options", expanded=True):
        st.markdown("### 🔍 Filter Cards")

        # Basic Filters
        search_text = st.text_input(
            "Filter cards", "", placeholder="Type part of a card name or number..."
        )

        product_line = st.selectbox(
            "Product Line", options=df["Product Line"].unique(), index=0
        )

        set_name = st.selectbox(
            "Set Name", options=df[df["Product Line"] == product_line]["Set Name"].unique(), index=0
        )

        rarity_filter = st.selectbox(
            "Rarity", options=df[(df["Product Line"] == product_line) & (df["Set Name"] == set_name)]["Rarity"].unique(), index=0
        )

        st.markdown("---")

        # Listings Range
        st.markdown("#### 📊 Listings Range")
        if "listings_range" not in st.session_state:
            st.session_state["listings_range"] = (0, 100)

        listings_min, listings_max = st.slider(
            "Listings Range",
            min_value=0,
            max_value=100,
            value=st.session_state["listings_range"],
            step=1,
            key="listings_slider"
        )
        st.session_state["listings_range"] = (listings_min, listings_max)

        # Price Range
        st.markdown("#### 💲 Price Range")
        if "price_range" not in st.session_state:
            st.session_state["price_range"] = (0.0, 1000.0)

        price_min, price_max = st.slider(
            "Price Range",
            min_value=0.0,
            max_value=1000.0,
            value=st.session_state["price_range"],
            step=0.01,
            key="price_slider"
        )
        st.session_state["price_range"] = (price_min, price_max)

        # Apply Filters Button
        if st.button("Apply Filters"):
            filtered_df = filter_data(
                df, price_min, price_max, listings_min, listings_max, product_line, set_name, rarity_filter, search_text
            )
            st.session_state.filtered_df = filtered_df
            st.success("Filters applied! Check the 'Filtered Cards' tab.")
            st.rerun()  # Force the interface to refresh

    # Repricing Options
    with st.expander("Repricing Options", expanded=True):
        st.markdown("### 💲 Repricing and Download")

        # Threshold Slider
        threshold = st.slider(
            "Set Threshold for Repricing Suggestions (%)",
            min_value=0,
            max_value=100,
            value=10,
            step=1,
            key="threshold_slider"
        )

        # Analysis Button
        if st.button("Analyze Repricing Suggestions"):
            if st.session_state.filtered_df is not None:
                suggested_repricing_df = analyze_repricing(
                    st.session_state.filtered_df, threshold=threshold)
                if not suggested_repricing_df.empty:
                    st.success(
                        "Analysis complete! Check the table below for suggestions.")
                    st.dataframe(
                        suggested_repricing_df[
                            [
                                "Product Line", "Set Name", "Product Name", "Total Quantity",
                                "TCG Marketplace Price", "TCG Market Price", "percentage_difference", "suggested_price"
                            ]
                        ],
                        use_container_width=True
                    )
                    # Save suggestions to session state for later use
                    st.session_state.suggested_repricing_df = suggested_repricing_df
                else:
                    st.info("No cards meet the criteria for repricing.")

        # Accept Suggestions Button
        if st.button("Accept Suggestions"):
            if "suggested_repricing_df" in st.session_state and st.session_state.suggested_repricing_df is not None:
                # Update the filtered DataFrame with the suggested prices
                st.session_state.filtered_df.update(
                    st.session_state.suggested_repricing_df[["Product Name", "suggested_price"]].rename(
                        columns={"suggested_price": "TCG Marketplace Price"}
                    )
                )
                st.success("Suggestions accepted! Updated prices applied.")

        # Reprice Button
        if st.button("Reprice"):
            if st.session_state.filtered_df is not None:
                repriced_df = st.session_state.filtered_df.copy()
                # Example: increase price by 10%
                repriced_df["TCG Marketplace Price"] = repriced_df["TCG Marketplace Price"] * (
                    1 + threshold / 100)
                st.session_state.filtered_df = repriced_df
                st.success(
                    "Repricing applied! Check the 'Filtered Cards' tab.")

        # Download Button
        if st.session_state.filtered_df is not None:
            csv = convert_for_download(st.session_state.filtered_df)
            st.download_button(
                label="Download Updated Inventory",
                data=csv,
                file_name="updated_inventory.csv",
                mime="text/csv"
            )
