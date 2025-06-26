import os
import streamlit as st
import pandas as pd
from functions import widgets
import logging
from st_aggrid import AgGrid, GridOptionsBuilder
from functions import widgets

widgets.show_pages_sidebar()

st.title("💲 Repricer")

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

def convert_df_for_tabs(df, selected_columns):
    # Convert the DataFrame for display in tabs, based on selected columns
    if "filtered_df" in st.session_state and st.session_state.filtered_df is not None:
        df = st.session_state.filtered_df
    else:
        df = df.copy()  # Avoid SettingWithCopyWarning
    return df[selected_columns]


def inventory_tabs(df, selected_columns):
    tab1, tab2, tab3 = st.tabs([
        "Full Inventory", "Price Differentials", "Filtered Cards"
    ])
    with tab1:
        # Always use the main DataFrame from session_state for Full Inventory
        st.dataframe(st.session_state.repricer_csv[selected_columns], use_container_width=True)
        total_marketplace_value = (st.session_state.repricer_csv["Total Quantity"] * st.session_state.repricer_csv["TCG Marketplace Price"]).sum()
        total_market_value = (st.session_state.repricer_csv["Total Quantity"] * st.session_state.repricer_csv["TCG Market Price"]).sum()
        st.write(f"**Total Marketplace Value (Quantity x Marketplace Price):** ${total_marketplace_value:.2f}")
        st.write(f"**Total Market Value (Quantity x Market Price):** ${total_market_value:.2f}")
        if st.button("Refresh Full Inventory", key="refresh_full_inventory"):
            st.rerun()
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


def repricing_tabs(df, selected_columns):
    st.markdown("### 💲 Repricing Tools")
    repricing_rules_tab, repricing_templates_tab = st.tabs(["Repricing Rules", "Repricing Templates"])
        
    with repricing_rules_tab:
        repricing_rules(df, selected_columns)

    with repricing_templates_tab:
        repricing_templates(df, selected_columns)


def repricing_rules(df, selected_columns):
    # --- Load inventory (replace with your actual loading logic) ---
    if "repricer_csv" not in st.session_state:
        st.session_state.repricer_csv = pd.read_csv("streamlit/pages/TestInventory.csv")

    df = st.session_state.repricer_csv.copy()

    # --- Session state for rules ---
    if "repricer_rules" not in st.session_state:
        st.session_state.repricer_rules = []

    # --- Rule builder ---
    st.header("📜 Add Repricing Rule")
    with st.popover("Add Rule"):
        col1, col2, col3 = st.columns(3)
        with col1:
            rule_name = st.text_input("Rule Name (unique, required)", value="", key="add_rule_name", help="Give this rule a unique name (required)")
            all_rule_names = [r.get("name", "") for r in st.session_state.repricer_rules]
            all_saved_names = [r.get("name", "") for r in st.session_state.get("saved_rules", [])]
            name_exists = rule_name.strip() in all_rule_names or rule_name.strip() in all_saved_names or not rule_name.strip()
            if not rule_name.strip():
                st.warning("Rule name is required.")
            elif rule_name.strip() in all_rule_names or rule_name.strip() in all_saved_names:
                st.warning("Rule name must be unique.")
            card_type_options = ["All"] + sorted([str(x) for x in df["Product Line"].dropna().unique()])
            card_type = st.selectbox("Card Type", card_type_options, key="add_rule_card_type")
            if card_type == "All":
                set_options = ["All"] + sorted([str(x) for x in df["Set Name"].dropna().unique()])
            else:
                set_options = ["All"] + sorted([str(x) for x in df[df["Product Line"] == card_type]["Set Name"].dropna().unique()])
            set_name = st.selectbox("Set", set_options, key="add_rule_set_name")
            if set_name == "All":
                rarity_options = ["All"] + sorted([str(x) for x in df[(df["Product Line"] == card_type) | (card_type == "All")]["Rarity"].dropna().unique()])
            else:
                rarity_options = ["All"] + sorted([str(x) for x in df[(df["Set Name"] == set_name) & ((df["Product Line"] == card_type) | (card_type == "All"))]["Rarity"].dropna().unique()])
            rarity = st.selectbox("Rarity", rarity_options, key="add_rule_rarity")
        with col2:
            min_price = st.number_input("Min Price", value=0.0, key="add_rule_min_price")
            max_price = st.number_input("Max Price", value=1000.0, key="add_rule_max_price")
            min_qty = st.number_input("Min Quantity", value=0, key="add_rule_min_qty")
            max_qty = st.number_input("Max Quantity", value=1000, key="add_rule_max_qty")
        with col3:
            condition = st.selectbox("Condition", ["All"] + sorted(df["Condition"].unique()), key="add_rule_condition")
            action_type = st.selectbox("Action", [
                "Set to Market + X%", "Set to Market + $X", "Set to Fixed Value", "Set to Market Price"
            ], key="add_rule_action_type")
            action_value = st.number_input("Value (for % or $ or fixed)", value=0.0, key="add_rule_action_value")
        save_col, cancel_col = st.columns(2)
        with save_col:
            if st.button("Save Rule", key="add_rule_save_btn", disabled=name_exists):
                if not rule_name.strip():
                    st.warning("Rule name is required.")
                elif rule_name.strip() in all_rule_names or rule_name.strip() in all_saved_names:
                    st.warning("Rule name must be unique.")
                else:
                    st.session_state.repricer_rules.append({
                        "name": rule_name,
                        "card_type": card_type,
                        "set_name": set_name,
                        "rarity": rarity,
                        "min_price": min_price,
                        "max_price": max_price,
                        "min_qty": min_qty,
                        "max_qty": max_qty,
                        "condition": condition,
                        "action_type": action_type,
                        "action_value": action_value
                    })
                    st.toast("Rule added!")
                    st.session_state["_popover"] = None  # Close the popover
                    st.rerun()
        with cancel_col:
            if st.button("Cancel", key="add_rule_cancel_btn"):
                st.rerun()

    # --- Preview rules ---
    preview_df = None
    ignore_unaffected = st.checkbox("Ignore cards not affected by the rule", value=True)
    with st.popover("Preview Rule Effects", use_container_width=True):
        
        if "repricer_csv" in st.session_state:
            preview_df = st.session_state.repricer_csv.copy()
            preview_df["Affected Rule"] = "None"
            preview_df["New Price"] = preview_df["TCG Marketplace Price"]
            for rule in st.session_state.repricer_rules:
                affected_rows = preview_df[
                    (preview_df["Product Line"] == rule["card_type"] if rule["card_type"] != "All" else True) &
                    (preview_df["Set Name"] == rule["set_name"] if rule["set_name"] != "All" else True) &
                    (preview_df["Rarity"] == rule["rarity"] if rule["rarity"] != "All" else True) &
                    (preview_df["TCG Marketplace Price"] >= rule["min_price"]) &
                    (preview_df["TCG Marketplace Price"] <= rule["max_price"]) &
                    (preview_df["Total Quantity"] >= rule["min_qty"]) &
                    (preview_df["Total Quantity"] <= rule["max_qty"]) &
                    (preview_df["Condition"] == rule["condition"] if rule["condition"] != "All" else True)
                ]
                preview_df.loc[affected_rows.index, "Affected Rule"] = f"{rule['action_type']} ({rule['action_value']})"
                if rule["action_type"] == "Set to Market + X%":
                    preview_df.loc[affected_rows.index, "New Price"] = (preview_df.loc[affected_rows.index, "TCG Market Price"] * (1 + rule["action_value"] / 100)).round(2)
                elif rule["action_type"] == "Set to Market + $X":
                    preview_df.loc[affected_rows.index, "New Price"] = (preview_df.loc[affected_rows.index, "TCG Market Price"] + rule["action_value"]).round(2)
                elif rule["action_type"] == "Set to Fixed Value":
                    preview_df.loc[affected_rows.index, "New Price"] = rule["action_value"]
                elif rule["action_type"] == "Set to Market Price":
                    preview_df.loc[affected_rows.index, "New Price"] = preview_df.loc[affected_rows.index, "TCG Market Price"].round(2)
            preview_df["New Price"] = preview_df["New Price"].astype(float)
            st.session_state.preview_df = preview_df  # <-- Store in session state
            display_df = preview_df
            if ignore_unaffected:
                display_df = preview_df[preview_df["Affected Rule"] != "None"]
            required_cols = ["Product Line", "Set Name", "Product Name", "TCG Marketplace Price", "TCG Market Price", "New Price", "Affected Rule"]
            for col in required_cols:
                if col not in display_df.columns:
                    display_df[col] = None  # or a sensible default
            if not display_df.empty:
                st.dataframe(display_df[required_cols], use_container_width=True)
            else:
                st.info("No cards to display.")
    # Use preview_df from session state for saving
    if st.button("Save New Prices"):
        preview_df = st.session_state.get("preview_df")
        if preview_df is not None:
            # Vectorized update for speed
            key_cols = ["Product Name", "Set Name", "Condition"]
            # Only update rows that have changed
            updated = preview_df[[*key_cols, "New Price"]].copy()
            updated = updated.rename(columns={"New Price": "TCG Marketplace Price"})
            # Set index for fast update
            st.session_state.repricer_csv.set_index(key_cols, inplace=True)
            updated.set_index(key_cols, inplace=True)
            st.session_state.repricer_csv.update(updated)
            st.session_state.repricer_csv.reset_index(inplace=True)
            # Also update filtered_df if it exists
            if "filtered_df" in st.session_state and st.session_state.filtered_df is not None:
                st.session_state.filtered_df.set_index(key_cols, inplace=True)
                st.session_state.filtered_df.update(updated)
                st.session_state.filtered_df.reset_index(inplace=True)
            st.toast("New prices saved to the full inventory!")
            updated_csv = convert_for_download(st.session_state.repricer_csv)
            st.download_button(
                label="Download Updated Inventory",
                data=updated_csv,
                file_name="updated_inventory.csv",
                mime="text/csv",
                key="download_inventory_button"
            )
        else:
            st.warning("No data available for preview.")
        
    rules_tab1, rules_tab2 = st.tabs(["Current Rules", "Saved Rules"])
    # --- Show current rules ---
    with rules_tab1:
        st.write("### Current Repricing Rules")
        # Add Clear All Rules button
        if st.session_state.repricer_rules:
            if st.button("Clear All Rules", key="clear_all_rules"):
                st.session_state.repricer_rules = []
                st.toast("All current rules cleared!")
                st.rerun()
        if not st.session_state.repricer_rules:
            st.info("No repricing rules set. Create a new rule in the 'Add Repricing Rule' section.")
        else:
            for idx, rule in enumerate(st.session_state.repricer_rules):
                rule_df = pd.DataFrame([rule])
                st.dataframe(rule_df, use_container_width=True)
                rule_name = rule.get("name", f"Rule {idx+1}")
                if rule.get("name"):
                    st.write(f"**Rule Name:** {rule['name']}")
                col1, col2, col3 = st.columns([1,1,1])
                with col1:
                    with st.popover(f"Edit Rule '{rule_name}'", use_container_width=True):
                        edit = rule.copy()
                        col1e, col2e, col3e = st.columns(3)
                        with col1e:
                            edit["name"] = st.text_input("Rule Name (unique, required)", value=edit.get("name", ""), key=f"edit_name_{rule_name}")
                            all_names = [r.get("name", "") for i, r in enumerate(st.session_state.repricer_rules) if i != idx]
                            name_exists = edit["name"].strip() in all_names or not edit["name"].strip()
                            if not edit["name"].strip():
                                st.warning("Rule name is required.")
                            elif edit["name"].strip() in all_names:
                                st.warning("Rule name must be unique.")
                        with col2e:
                            card_type_options = ["All"] + sorted([str(x) for x in df["Product Line"].dropna().unique()])
                            edit["card_type"] = st.selectbox("Card Type", card_type_options, index=card_type_options.index(edit.get("card_type", "All")), key=f"edit_card_type_{rule_name}")
                            if edit["card_type"] == "All":
                                set_options = ["All"] + sorted([str(x) for x in df["Set Name"].dropna().unique()])
                            else:
                                set_options = ["All"] + sorted([str(x) for x in df[df["Product Line"] == edit["card_type"]]["Set Name"].dropna().unique()])
                            edit["set_name"] = st.selectbox("Set", set_options, index=set_options.index(edit.get("set_name", "All")), key=f"edit_set_{rule_name}")
                            if edit["set_name"] == "All":
                                rarity_options = ["All"] + sorted([str(x) for x in df[(df["Product Line"] == edit["card_type"]) | (edit["card_type"] == "All")]["Rarity"].dropna().unique()])
                            else:
                                rarity_options = ["All"] + sorted([str(x) for x in df[(df["Set Name"] == edit["set_name"]) & ((df["Product Line"] == edit["card_type"]) | (edit["card_type"] == "All"))]["Rarity"].dropna().unique()])
                            edit["rarity"] = st.selectbox("Rarity", rarity_options, index=rarity_options.index(edit.get("rarity", "All")), key=f"edit_rarity_{rule_name}")
                        with col3e:
                            edit["min_price"] = st.number_input("Min Price", value=float(edit.get("min_price", 0.0)), key=f"edit_min_price_{rule_name}")
                            edit["max_price"] = st.number_input("Max Price", value=float(edit.get("max_price", 1000.0)), key=f"edit_max_price_{rule_name}")
                            edit["min_qty"] = st.number_input("Min Quantity", value=int(edit.get("min_qty", 0)), key=f"edit_min_qty_{rule_name}")
                            edit["max_qty"] = st.number_input("Max Quantity", value=int(edit.get("max_qty", 1000)), key=f"edit_max_qty_{rule_name}")
                            edit["condition"] = st.selectbox("Condition", ["All"] + sorted(df["Condition"].unique()), index=( ["All"] + sorted(df["Condition"].unique())).index(edit.get("condition", "All")), key=f"edit_condition_{rule_name}")
                            action_types = ["Set to Market + X%", "Set to Market + $X", "Set to Fixed Value", "Set to Market Price"]
                            edit["action_type"] = st.selectbox("Action", action_types, index=action_types.index(edit.get("action_type", action_types[0])), key=f"edit_action_type_{rule_name}")
                            edit["action_value"] = st.number_input("Value (for % or $ or fixed)", value=float(edit.get("action_value", 0.0)), key=f"edit_action_value_{rule_name}")
                        save_col, cancel_col = st.columns(2)
                        with save_col:
                            if st.button("Save Changes", key=f"save_changes_{rule_name}", disabled=name_exists):
                                st.session_state.repricer_rules[idx] = edit.copy()
                                st.toast("Rule updated!")
                                st.rerun()
                        with cancel_col:
                            if st.button("Cancel", key=f"cancel_edit_{rule_name}"):
                                st.rerun()
                with col2:
                    if st.button(f"Save Rule '{rule_name}'", key=f"save_rule_{rule_name}'", use_container_width=True):
                        if "saved_rules" not in st.session_state:
                            st.session_state.saved_rules = []
                        st.session_state.saved_rules.append(rule)
                        st.toast("Rule saved!")
                        st.rerun()
                with col3:
                    if st.button(f"Remove Rule '{rule_name}'", key=f"remove_rule_{rule_name}", use_container_width=True):
                        st.session_state.repricer_rules.pop(idx)
                        st.toast("Rule removed!")
                        st.rerun()
                # ...existing code...
    with rules_tab2:
        st.write("### Saved Repricing Rules")
        if "saved_rules" in st.session_state and st.session_state.saved_rules:
            if "edit_saved_rule_idx" not in st.session_state:
                st.session_state.edit_saved_rule_idx = None
            for idx, saved_rule in enumerate(st.session_state.saved_rules):
                saved_rule_df = pd.DataFrame([saved_rule])
                st.dataframe(saved_rule_df, use_container_width=True)
                rule_name = saved_rule.get("name", f"Saved Rule {idx+1}")
                if saved_rule.get("name"):
                    st.write(f"**Rule Name:** {saved_rule['name']}")
                col1, col2, col3 = st.columns([1,1,1])
                with col1:
                    if st.button(f"Edit Saved Rule '{rule_name}'", key=f"edit_saved_rule_{rule_name}"):
                        st.session_state.edit_saved_rule_idx = idx
                        st.session_state.edit_saved_rule_data = saved_rule.copy()
                        st.rerun()
                with col2:
                    if st.button(f"Use Rule '{rule_name}'", key=f"use_saved_rule_{rule_name}"):
                        st.session_state.repricer_rules.append(saved_rule)
                        st.toast("Rule added to Current Rules!")
                        st.rerun()
                with col3:
                    if st.button(f"Remove Saved Rule '{rule_name}'", key=f"remove_saved_rule_{rule_name}"):
                        st.session_state.saved_rules.pop(idx)
                        st.toast("Saved rule removed!")
                        st.rerun()
                # Editable form for the selected saved rule
                if st.session_state.edit_saved_rule_idx == idx:
                    st.markdown("**Edit Saved Rule**")
                    edit = st.session_state.edit_saved_rule_data
                    edit["name"] = st.text_input("Rule Name", value=edit.get("name", ""), key=f"edit_saved_name_{rule_name}")
                    card_type_options = ["All"] + sorted([str(x) for x in df["Product Line"].dropna().unique()])
                    edit["card_type"] = st.selectbox("Card Type", card_type_options, index=card_type_options.index(edit.get("card_type", "All")), key=f"edit_saved_card_type_{rule_name}")
                    if edit["card_type"] == "All":
                        set_options = ["All"] + sorted([str(x) for x in df["Set Name"].dropna().unique()])
                    else:
                        set_options = ["All"] + sorted([str(x) for x in df[df["Product Line"] == edit["card_type"]]["Set Name"].dropna().unique()])
                    edit["set_name"] = st.selectbox("Set", set_options, index=set_options.index(edit.get("set_name", "All")), key=f"edit_saved_set_{rule_name}")
                    if edit["set_name"] == "All":
                        rarity_options = ["All"] + sorted([str(x) for x in df[(df["Product Line"] == edit["card_type"]) | (edit["card_type"] == "All")]["Rarity"].dropna().unique()])
                    else:
                        rarity_options = ["All"] + sorted([str(x) for x in df[(df["Set Name"] == edit["set_name"]) & ((df["Product Line"] == edit["card_type"]) | (edit["card_type"] == "All"))]["Rarity"].dropna().unique()])
                    edit["rarity"] = st.selectbox("Rarity", rarity_options, index=rarity_options.index(edit.get("rarity", "All")), key=f"edit_saved_rarity_{rule_name}")
                    edit["min_price"] = st.number_input("Min Price", value=float(edit.get("min_price", 0.0)), key=f"edit_saved_min_price_{rule_name}")
                    edit["max_price"] = st.number_input("Max Price", value=float(edit.get("max_price", 1000.0)), key=f"edit_saved_max_price_{rule_name}")
                    edit["min_qty"] = st.number_input("Min Quantity", value=int(edit.get("min_qty", 0)), key=f"edit_saved_min_qty_{rule_name}")
                    edit["max_qty"] = st.number_input("Max Quantity", value=int(edit.get("max_qty", 1000)), key=f"edit_saved_max_qty_{rule_name}")
                    edit["condition"] = st.selectbox("Condition", ["All"] + sorted(df["Condition"].unique()), index=( ["All"] + sorted(df["Condition"].unique())).index(edit.get("condition", "All")), key=f"edit_saved_condition_{rule_name}")
                    action_types = ["Set to Market + X%", "Set to Market + $X", "Set to Fixed Value", "Set to Market Price"]
                    edit["action_type"] = st.selectbox("Action", action_types, index=action_types.index(edit.get("action_type", action_types[0])), key=f"edit_saved_action_type_{rule_name}")
                    edit["action_value"] = st.number_input("Value (for % or $ or fixed)", value=float(edit.get("action_value", 0.0)), key=f"edit_saved_action_value_{rule_name}")
                    save_col, cancel_col = st.columns(2)
                    with save_col:
                        if st.button("Save Changes", key=f"save_saved_changes_{rule_name}"):
                            st.session_state.saved_rules[idx] = edit.copy()
                            st.session_state.edit_saved_rule_idx = None
                            st.toast("Saved rule updated!")
                            st.rerun()
                    with cancel_col:
                        if st.button("Cancel", key=f"cancel_saved_edit_{rule_name}"):
                            st.session_state.edit_saved_rule_idx = None
                            st.rerun()
        else:
            st.info("No saved rules available. Save a rule from the Current Rules tab.")

def repricing_templates(df, selected_columns):
    st.markdown("### 🗂️ Repricing Templates (Saved Rules)")
    if "saved_rules" not in st.session_state or not st.session_state.saved_rules:
        st.info("No saved rules available. Save a rule from the Current Rules tab.")
        return
    # --- Template management ---
    if "rule_templates" not in st.session_state:
        st.session_state.rule_templates = []  # Each: {"name": str, "rules": [rule, ...]}
    st.markdown("#### 📦 Save/Load Rule Templates")
    # Save current selection as template
    rule_names = [r.get("name", f"Saved Rule {i+1}") for i, r in enumerate(st.session_state.saved_rules)]
    selected_rule_names = st.multiselect(
        "Select one or more saved rules to preview/apply:",
        options=rule_names,
        key="template_multiselect"
    )
    if selected_rule_names:
        template_name = st.text_input("Template Name (to save this set):", key="template_name_input")
        if st.button("Save as Template", key="save_template_btn") and template_name.strip():
            # Save selected rules as a template
            selected_rules = [r for r, name in zip(st.session_state.saved_rules, rule_names) if name in selected_rule_names]
            # Prevent duplicate template names
            if any(t["name"] == template_name.strip() for t in st.session_state.rule_templates):
                st.warning("Template name must be unique.")
            else:
                st.session_state.rule_templates.append({"name": template_name.strip(), "rules": selected_rules})
                st.success(f"Template '{template_name.strip()}' saved!")
                st.rerun()
    # --- Load and apply a template ---
    if st.session_state.rule_templates:
        st.markdown("#### 📂 Load a Saved Template")
        template_options = [t["name"] for t in st.session_state.rule_templates]
        selected_template = st.selectbox("Select a template to preview/apply:", ["None"] + template_options, key="template_selectbox")
        if selected_template != "None":
            template = next(t for t in st.session_state.rule_templates if t["name"] == selected_template)
            selected_rules = template["rules"]
            st.info(f"Previewing template: {selected_template}")
            # Preview logic (apply rules in order)
            preview_df = st.session_state.repricer_csv.copy()
            preview_df["Affected Rule"] = "None"
            preview_df["New Price"] = preview_df["TCG Marketplace Price"]
            for rule in selected_rules:
                affected_rows = preview_df[
                    (preview_df["Product Line"] == rule["card_type"] if rule["card_type"] != "All" else True) &
                    (preview_df["Set Name"] == rule["set_name"] if rule["set_name"] != "All" else True) &
                    (preview_df["Rarity"] == rule["rarity"] if rule["rarity"] != "All" else True) &
                    (preview_df["TCG Marketplace Price"] >= rule["min_price"]) &
                    (preview_df["TCG Marketplace Price"] <= rule["max_price"]) &
                    (preview_df["Total Quantity"] >= rule["min_qty"]) &
                    (preview_df["Total Quantity"] <= rule["max_qty"]) &
                    (preview_df["Condition"] == rule["condition"] if rule["condition"] != "All" else True)
                ]
                preview_df.loc[affected_rows.index, "Affected Rule"] = f"{rule['name']} ({rule['action_type']} {rule['action_value']})"
                if rule["action_type"] == "Set to Market + X%":
                    preview_df.loc[affected_rows.index, "New Price"] = (preview_df.loc[affected_rows.index, "TCG Market Price"] * (1 + rule["action_value"] / 100)).round(2)
                elif rule["action_type"] == "Set to Market + $X":
                    preview_df.loc[affected_rows.index, "New Price"] = (preview_df.loc[affected_rows.index, "TCG Market Price"] + rule["action_value"]).round(2)
                elif rule["action_type"] == "Set to Fixed Value":
                    preview_df.loc[affected_rows.index, "New Price"] = rule["action_value"]
                elif rule["action_type"] == "Set to Market Price":
                    preview_df.loc[affected_rows.index, "New Price"] = preview_df.loc[affected_rows.index, "TCG Market Price"].round(2)
            preview_df["New Price"] = preview_df["New Price"].astype(float)
            display_df = preview_df[preview_df["Affected Rule"] != "None"]
            required_cols = ["Product Line", "Set Name", "Product Name", "TCG Marketplace Price", "TCG Market Price", "New Price", "Affected Rule"]
            for col in required_cols:
                if col not in display_df.columns:
                    display_df[col] = None
            if not display_df.empty:
                st.dataframe(display_df[required_cols], use_container_width=True)
            else:
                st.info("No cards to display for the selected template.")
            if st.button("Apply Template (Save New Prices)", key="apply_template_btn"):
                key_cols = ["Product Name", "Set Name", "Condition"]
                updated = preview_df[[*key_cols, "New Price"]].copy()
                updated = updated.rename(columns={"New Price": "TCG Marketplace Price"})
                st.session_state.repricer_csv.set_index(key_cols, inplace=True)
                updated.set_index(key_cols, inplace=True)
                st.session_state.repricer_csv.update(updated)
                st.session_state.repricer_csv.reset_index(inplace=True)
                if "filtered_df" in st.session_state and st.session_state.filtered_df is not None:
                    st.session_state.filtered_df.set_index(key_cols, inplace=True)
                    st.session_state.filtered_df.update(updated)
                    st.session_state.filtered_df.reset_index(inplace=True)
                st.toast(f"Template '{selected_template}' applied and prices saved!")
                updated_csv = convert_for_download(st.session_state.repricer_csv)
                st.download_button(
                    label="Download Updated Inventory",
                    data=updated_csv,
                    file_name="updated_inventory.csv",
                    mime="text/csv",
                    key="download_inventory_button_templates_apply"
                )
            # Option to delete template
            if st.button("Delete Template", key="delete_template_btn"):
                st.session_state.rule_templates = [t for t in st.session_state.rule_templates if t["name"] != selected_template]
                st.success(f"Template '{selected_template}' deleted.")
                st.rerun()
    # --- Legacy: preview/apply ad-hoc selection (still supported) ---
    if not selected_rule_names:
        st.info("Select at least one saved rule to preview changes.")
        return
    selected_rules = [r for r, name in zip(st.session_state.saved_rules, rule_names) if name in selected_rule_names]
    preview_df = st.session_state.repricer_csv.copy()
    preview_df["Affected Rule"] = "None"
    preview_df["New Price"] = preview_df["TCG Marketplace Price"]
    for rule in selected_rules:
        affected_rows = preview_df[
            (preview_df["Product Line"] == rule["card_type"] if rule["card_type"] != "All" else True) &
            (preview_df["Set Name"] == rule["set_name"] if rule["set_name"] != "All" else True) &
            (preview_df["Rarity"] == rule["rarity"] if rule["rarity"] != "All" else True) &
            (preview_df["TCG Marketplace Price"] >= rule["min_price"]) &
            (preview_df["TCG Marketplace Price"] <= rule["max_price"]) &
            (preview_df["Total Quantity"] >= rule["min_qty"]) &
            (preview_df["Total Quantity"] <= rule["max_qty"]) &
            (preview_df["Condition"] == rule["condition"] if rule["condition"] != "All" else True)
        ]
        preview_df.loc[affected_rows.index, "Affected Rule"] = f"{rule['name']} ({rule['action_type']} {rule['action_value']})"
        if rule["action_type"] == "Set to Market + X%":
            preview_df.loc[affected_rows.index, "New Price"] = (preview_df.loc[affected_rows.index, "TCG Market Price"] * (1 + rule["action_value"] / 100)).round(2)
        elif rule["action_type"] == "Set to Market + $X":
            preview_df.loc[affected_rows.index, "New Price"] = (preview_df.loc[affected_rows.index, "TCG Market Price"] + rule["action_value"]).round(2)
        elif rule["action_type"] == "Set to Fixed Value":
            preview_df.loc[affected_rows.index, "New Price"] = rule["action_value"]
        elif rule["action_type"] == "Set to Market Price":
            preview_df.loc[affected_rows.index, "New Price"] = preview_df.loc[affected_rows.index, "TCG Market Price"].round(2)
    preview_df["New Price"] = preview_df["New Price"].astype(float)
    display_df = preview_df[preview_df["Affected Rule"] != "None"]
    required_cols = ["Product Line", "Set Name", "Product Name", "TCG Marketplace Price", "TCG Market Price", "New Price", "Affected Rule"]
    for col in required_cols:
        if col not in display_df.columns:
            display_df[col] = None
    if not display_df.empty:
        st.dataframe(display_df[required_cols], use_container_width=True)
    else:
        st.info("No cards to display for the selected rules.")
    if st.button("Save New Prices from Templates", key="save_templates_btn"):
        key_cols = ["Product Name", "Set Name", "Condition"]
        updated = preview_df[[*key_cols, "New Price"]].copy()
        updated = updated.rename(columns={"New Price": "TCG Marketplace Price"})
        st.session_state.repricer_csv.set_index(key_cols, inplace=True)
        updated.set_index(key_cols, inplace=True)
        st.session_state.repricer_csv.update(updated)
        st.session_state.repricer_csv.reset_index(inplace=True)
        if "filtered_df" in st.session_state and st.session_state.filtered_df is not None:
            st.session_state.filtered_df.set_index(key_cols, inplace=True)
            st.session_state.filtered_df.update(updated)
            st.session_state.filtered_df.reset_index(inplace=True)
        st.toast("New prices from templates saved to the full inventory!")
        updated_csv = convert_for_download(st.session_state.repricer_csv)
        st.download_button(
            label="Download Updated Inventory",
            data=updated_csv,
            file_name="updated_inventory.csv",
            mime="text/csv",
            key="download_inventory_button_templates"
        )


def main():
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
        df = st.session_state.repricer_csv
        with st.sidebar:
            selected_columns = sidebar(df)

        repricing_tabs(df, selected_columns)


            
    else:
        st.warning("No inventory loaded. Please upload a CSV file.")


if __name__ == "__main__":
    main()
widgets.footer()