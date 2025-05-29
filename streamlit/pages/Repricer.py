import os
import streamlit as st
import pandas as pd
from functions import widgets

widgets.show_pages_sidebar()

st.title("💲 Repricer")


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
            st.toast("CSV file not found. Check the path.")


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
if "repricer_csv" not in st.session_state:
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

    # Tabs for Inventory, Repricing, and Summary (Filter and Repricing Options back in sidebar)
    main_tab1, main_tab2, main_tab3 = st.tabs([
        "Inventory Management", "Repricing Suggestions", "Inventory Summary"
    ])

    # --- SIDEBAR: Filter Options ---
    with st.sidebar:
        st.markdown("### 🔍 Inventory Management")
        with st.expander("Filter Options", expanded=True):
            # Basic Filters
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
                st.success("Filters applied! Check the 'Filtered Cards' tab.")
                st.rerun()  # Force the interface to refresh

            # Clear All Filters Button
            if st.button("Clear All Filters"):
                st.session_state["listings_range"] = (0, 100)
                st.session_state["price_range"] = (0.0, 1000.0)
                st.session_state.filtered_df = None
                st.success("Filters cleared!")
                st.rerun()  # Force the interface to refresh

    # --- MAIN TABS ---
    with main_tab1:
        st.markdown("### 🔧 Hide Columns")
        columns_to_display = st.radio(
            "Select columns to display:",
            options=["All Columns", "Essential Columns", "Custom Columns"],
            index=0
        )
        all_columns = df.columns.tolist()
        essential_columns = [
            "Product Line", "Set Name", "Product Name", "Total Quantity",
            "TCG Marketplace Price", "TCG Market Price"
        ]
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
        tab1, tab2, tab3 = st.tabs([
            "Full Inventory", "Price Differentials", "Filtered Cards"
        ])
        with tab1:
            st.dataframe(df[selected_columns], use_container_width=True)
            # Add total marketplace value and total market value below the table
            total_marketplace_value = (df["Total Quantity"] * df["TCG Marketplace Price"]).sum()
            total_market_value = (df["Total Quantity"] * df["TCG Market Price"]).sum()
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
            else:
                st.info(
                    "No filters applied yet. Use the Filter Options tab to filter cards."
                )

    with main_tab2:
        st.markdown("### 💲 Repricing Suggestions")
        # Move repricing filter options here (not in sidebar)
        st.markdown("#### Repricing Filters")
        if "price_floor" not in st.session_state:
            st.session_state["price_floor"] = 1.0
        threshold = st.slider(
            "Set Threshold for Repricing Suggestions (%)",
            min_value=0,
            max_value=100,
            value=10,
            step=1,
            key="repricing_threshold_slider_tab"
        )
        price_floor = st.slider(
            "Set Card Price Floor (USD)",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state["price_floor"],
            step=0.01,
            key="price_floor_slider_tab",
            help="Cards priced below or equal to this value will not be counted as underpriced."
        )
        st.session_state["price_floor"] = price_floor
        rarity_options = ["All"] + (
            st.session_state.filtered_df["Rarity"].unique().tolist()
            if st.session_state.filtered_df is not None
            else []
        )
        selected_rarity = st.selectbox(
            "Select Rarity to Reprice",
            options=rarity_options,
            index=0,
            help="Choose the rarity of cards you want to include in the repricing analysis.",
            key="repricing_rarity_selectbox_tab"
        )
        condition_options = ["All"] + (
            st.session_state.filtered_df["Condition"].unique().tolist()
            if st.session_state.filtered_df is not None
            else []
        )
        selected_condition = st.selectbox(
            "Select Condition to Reprice",
            options=condition_options,
            index=0,
            help="Choose the condition of cards you want to include in the repricing analysis.",
            key="repricing_condition_selectbox_tab"
        )
        st.markdown("#### 💲 Value Range")
        min_value, max_value = st.slider(
            "Select Value Range for Cards (USD)",
            min_value=0.0,
            max_value=1000.0,
            value=(0.0, 1000.0),
            step=0.01,
            help="Set the minimum and maximum value range for cards to include in the repricing analysis.",
            key="repricing_value_slider_tab"
        )

        # Analysis Button
        if st.button("Analyze Repricing Suggestions", key="analyze_repricing_button"):
            if st.session_state.filtered_df is not None:
                # Filter cards based on rarity, condition, and value range
                filtered_repricing_df = st.session_state.filtered_df[
                    (st.session_state.filtered_df["TCG Marketplace Price"] > st.session_state["price_floor"]) &
                    (st.session_state.filtered_df["TCG Marketplace Price"] >= min_value) &
                    (st.session_state.filtered_df["TCG Marketplace Price"] <= max_value)
                ]

                if selected_rarity != "All":
                    filtered_repricing_df = filtered_repricing_df[
                        filtered_repricing_df["Rarity"] == selected_rarity
                    ]

                if selected_condition != "All":
                    filtered_repricing_df = filtered_repricing_df[
                        filtered_repricing_df["Condition"] == selected_condition
                    ]

                # Analyze repricing suggestions
                suggested_repricing_df = analyze_repricing(
                    filtered_repricing_df, threshold=threshold
                )

                if not suggested_repricing_df.empty:
                    st.success("Analysis complete! You can edit the table below.")

                    # Calculate stats
                    num_overpriced = suggested_repricing_df[
                        suggested_repricing_df["percentage_difference"] > threshold
                    ].shape[0]
                    num_underpriced = suggested_repricing_df[
                        suggested_repricing_df["percentage_difference"] < -threshold
                    ].shape[0]
                    num_correctly_priced = suggested_repricing_df[
                        (suggested_repricing_df["percentage_difference"] <= threshold) &
                        (suggested_repricing_df["percentage_difference"] >= -threshold)
                    ].shape[0]

                    # Calculate total value before and after repricing
                    total_value_before = (
                        suggested_repricing_df["Total Quantity"] *
                        suggested_repricing_df["TCG Marketplace Price"]
                    ).sum()
                    total_value_after = (
                        suggested_repricing_df["Total Quantity"] *
                        suggested_repricing_df["suggested_price"]
                    ).sum()

                    # Display stats
                    st.write(f"**Number of Overpriced Cards:** {num_overpriced}")
                    st.write(f"**Number of Underpriced Cards:** {num_underpriced}")
                    st.write(
                        f"**Number of Correctly Priced Cards:** {num_correctly_priced}")
                    st.write(
                        f"**Total Value Before Repricing:** ${total_value_before:.2f}")
                    st.write(
                        f"**Total Value After Repricing:** ${total_value_after:.2f}")

                    # Format columns
                    formatted_df = suggested_repricing_df.copy()
                    formatted_df["percentage_difference"] = formatted_df["percentage_difference"].apply(
                        lambda x: f"{x:.2f}%")
                    formatted_df["suggested_price"] = formatted_df["suggested_price"].apply(
                        lambda x: f"${x:.2f}")

                    # Add color coding
                    def color_code_row(row):
                        if float(row["percentage_difference"].strip('%')) > threshold:
                            # Light red for overpriced
                            return ["background-color: #ffcccc"] * len(row)
                        elif float(row["percentage_difference"].strip('%')) < -threshold:
                            # Light green for underpriced
                            return ["background-color: #ccffcc"] * len(row)
                        return [""] * len(row)  # No color for correctly priced

                    styled_df = formatted_df.style.apply(color_code_row, axis=1)

                    # Display styled DataFrame
                    st.dataframe(styled_df, use_container_width=True)

                    # Save edited DataFrame to session state
                    st.session_state.suggested_repricing_df = suggested_repricing_df
                else:
                    st.info("No cards meet the criteria for repricing.")

        # Accept All Suggestions Button
        if st.button("Accept All Suggestions", key="accept_all_suggestions_button"):
            if "suggested_repricing_df" in st.session_state and st.session_state.suggested_repricing_df is not None:
                # Update the filtered DataFrame with all suggested prices
                for index, row in st.session_state.suggested_repricing_df.iterrows():
                    st.session_state.filtered_df.loc[
                        st.session_state.filtered_df["Product Name"] == row["Product Name"], "TCG Marketplace Price"
                    ] = row["suggested_price"]
                st.success("All suggested prices accepted!")

        # Download Button
        if st.session_state.repricer_csv is not None:
            # Apply changes from filtered_df back to the original DataFrame
            if "filtered_df" in st.session_state and st.session_state.filtered_df is not None:
                for index, row in st.session_state.filtered_df.iterrows():
                    st.session_state.repricer_csv.loc[
                        st.session_state.repricer_csv["Product Name"] == row["Product Name"], "TCG Marketplace Price"
                    ] = row["TCG Marketplace Price"]

            # Convert the updated original DataFrame to CSV for download
            updated_csv = convert_for_download(st.session_state.repricer_csv)
            st.download_button(
                label="Download Updated Inventory",
                data=updated_csv,
                file_name="updated_inventory.csv",
                mime="text/csv",
                key="download_inventory_button"
            )

    with main_tab3:
        st.markdown("### 📊 Inventory Summary")
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
            # Transpose the DataFrame to show rarity names on top
            st.write(rarity_counts.to_frame().T)

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
                # Transpose the DataFrame for filtered rarity counts
                st.write(filtered_rarity_counts.to_frame().T)

                # Average Market Price in filtered data
                filtered_avg_market_price = st.session_state.filtered_df["TCG Market Price"].mean(
                )
                st.write(
                    f"**Average Market Price (Filtered):** ${filtered_avg_market_price:.2f}")

                # Average Marketplace Price in filtered data
                filtered_avg_marketplace_price = st.session_state.filtered_df["TCG Marketplace Price"].mean(
                )
                st.write(
                    f"**Average Marketplace Price (Filtered):** ${filtered_avg_marketplace_price:.2f}")

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
