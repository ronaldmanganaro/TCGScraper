import streamlit as st
import os, json
def login():
    with st.popover("👤 Login/Logout", use_container_width=True):
        if st.session_state.get("current_user"):
            st.markdown(f"**👤 Logged in as:** `{st.session_state['current_user']}`")
            if st.button("Logout", key="logout_button_sidebar"):
                # Save any new rules/templates before logging out
                user_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'users')
                os.makedirs(user_dir, exist_ok=True)
                user_file = os.path.join(user_dir, f"{st.session_state['current_user']}.json")
                rules = st.session_state.get("saved_rules", [])
                templates = st.session_state.get("rule_templates", [])
                # If password exists, preserve it
                password = None
                if os.path.exists(user_file):
                    with open(user_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    password = data.get("password")
                save_data = {"rules": rules, "templates": templates}
                if password is not None:
                    save_data["password"] = password
                with open(user_file, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, indent=2)
                # Clear inventory from session state
                st.session_state.pop("repricer_csv", None)
                st.session_state.pop("filtered_df", None)
                st.session_state.pop("suggested_repricing_df", None)
                st.session_state.pop("accepted_prices", None)
                st.session_state.pop("repricer_page", None)
                st.session_state.pop("cards_per_page", None)
                st.session_state.pop("preview_df", None)
                st.session_state.pop("price_floor", None)
                st.session_state.pop("floor_price", None)
                st.session_state.pop("listings_range", None)
                st.session_state.pop("price_range", None)
                st.session_state.pop("column_mode_radio_sidebar", None)
                st.session_state.pop("custom_columns_multiselect_sidebar", None)
                st.session_state.pop("repricer_threshold_input", None)
                st.session_state.pop("repricing_rarity_selectbox_tab", None)
                st.session_state.pop("repricing_condition_selectbox_tab", None)
                st.session_state.pop("repricing_min_value_input", None)
                st.session_state.pop("repricing_max_value_input", None)
                st.session_state.pop("cards_per_page_selectbox_inline", None)
                st.session_state.pop("repricing_tab", None)
                st.session_state.pop("repricing_rules_tab", None)
                st.session_state.pop("repricing_templates_tab", None)
                st.session_state.pop("download_inventory_button", None)
                st.session_state.pop("download_inventory_button_templates", None)
                st.session_state.pop("download_inventory_button_templates_apply", None)
                st.session_state.pop("template_multiselect", None)
                st.session_state.pop("template_name_input", None)
                st.session_state.pop("template_selectbox", None)
                st.session_state.pop("edit_saved_rule_idx", None)
                st.session_state.pop("edit_saved_rule_data", None)
                st.session_state.pop("_popover", None)
                st.session_state.pop("sidebar_columns_radio", None)
                st.session_state.pop("sidebar_columns_multiselect", None)
                st.session_state.pop("selected_tcg", None)
                st.session_state.pop("filtered_unique_cards", None)
                st.session_state.pop("filtered_market_value", None)
                st.session_state.pop("filtered_total_quantity", None)
                st.session_state.pop("filtered_rarity_counts", None)
                st.session_state.pop("filtered_avg_market_price", None)
                st.session_state.pop("filtered_avg_marketplace_price", None)
                st.session_state.pop("filtered_marketplace_value", None)
                st.session_state.pop("filtered_market_value", None)
                st.session_state.pop("current_user", None)
                st.session_state.pop("saved_rules", None)
                st.session_state.pop("rule_templates", None)
                st.success("Logged out, rules saved, and inventory cleared.")
                st.rerun()
        else:
            st.markdown("#### User Login or Create Account")
            tab_login, tab_create = st.tabs(["Login", "Create Account"])
            with tab_login:
                username = st.text_input("Username", key="login_username_sidebar")
                password = st.text_input("Password", type="password", key="login_password_sidebar")
                if st.button("Login", key="login_button_sidebar", use_container_width=True):
                    if username.strip():
                        user_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'users')
                        user_file = os.path.join(user_dir, f"{username.strip()}.json")
                        st.session_state.pop("saved_rules", None)
                        st.session_state.pop("rule_templates", None)
                        # Reload last inventory for this user if it exists
                        inventory_file = os.path.join(user_dir, f"{username.strip()}_inventory.csv")
                        if os.path.exists(user_file):
                            with open(user_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            st.session_state["saved_rules"] = data.get("rules", [])
                            st.session_state["rule_templates"] = data.get("templates", [])
                            st.success(f"Loaded rules and templates for user: {username.strip()}")
                            # Load last inventory if present
                            if os.path.exists(inventory_file):
                                import pandas as pd
                                st.session_state["repricer_csv"] = pd.read_csv(inventory_file)
                                st.success(f"Loaded last inventory for user: {username.strip()}")
                        else:
                            st.session_state["saved_rules"] = []
                            st.session_state["rule_templates"] = []
                            st.info(f"No saved rules found for user: {username.strip()} (starting fresh)")
                        st.session_state["current_user"] = username.strip()
                    else:
                        st.warning("Please enter a username.")
                    st.rerun()
            with tab_create:
                new_username = st.text_input("New Username", key="create_username_sidebar")
                new_password = st.text_input("New Password", type="password", key="create_password_sidebar")
                if st.button("Create Account", key="create_account_button", use_container_width=True):
                    if new_username.strip() and new_password.strip():
                        user_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'users')
                        os.makedirs(user_dir, exist_ok=True)
                        user_file = os.path.join(user_dir, f"{new_username.strip()}.json")
                        if os.path.exists(user_file):
                            st.warning("Username already exists. Please choose another.")
                        else:
                            # Save password in plaintext for demo only (not secure!)
                            with open(user_file, 'w', encoding='utf-8') as f:
                                json.dump({"password": new_password.strip(), "rules": [], "templates": []}, f, indent=2)
                            st.success(f"Account created for user: {new_username.strip()}. You can now log in.")
                    else:
                        st.warning("Please enter a username and password.")

def show_pages_sidebar():
    # Expander for Pages

    with st.sidebar.expander("📄 Pages", expanded=True):
        login()
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("pages/home.py")
        if st.button("💲 Repricer", use_container_width=True):
            st.switch_page("pages/Repricer.py")
        if st.button("📦 EV Tools", use_container_width=True):
            st.switch_page("pages/EVTools.py")
        if st.button("⚡ Pokémon Price Tracker", use_container_width=True):
            st.switch_page("pages/PokemonPriceTracker.py")
        if st.button("☁️ Cloud Control", use_container_width=True):
            st.switch_page("pages/Cloud_Control.py")
