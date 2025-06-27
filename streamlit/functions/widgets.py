import streamlit as st
import json
import psycopg2
import bcrypt

def ensure_users_table():
    
    conn = psycopg2.connect(
        dbname='tcgplayerdb',
        user='rmangana',
        password='password',
        host='52.73.212.127',
        port=5432
    )
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            rules JSONB,
            templates JSONB
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()


def create_user_db(username, password):
    ensure_users_table()
    
    conn = psycopg2.connect(
        dbname='tcgplayerdb',
        user='rmangana',
        password='password',
        host='52.73.212.127',
        port=5432
    )
    cur = conn.cursor()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        cur.execute('INSERT INTO users (username, password_hash, rules, templates) VALUES (%s, %s, %s, %s)', (username, password_hash, json.dumps([]), json.dumps([])))
        conn.commit()
        return True
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def check_user_db(username, password):
    ensure_users_table()
    
    conn = psycopg2.connect(
        dbname='tcgplayerdb',
        user='rmangana',
        password='password',
        host='52.73.212.127',
        port=5432
    )
    cur = conn.cursor()
    cur.execute('SELECT password_hash FROM users WHERE username = %s', (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return bcrypt.checkpw(password.encode('utf-8'), row[0].encode('utf-8'))
    return False

def get_user_data_db(username):
    ensure_users_table()
    
    conn = psycopg2.connect(
        dbname='tcgplayerdb',
        user='rmangana',
        password='password',
        host='52.73.212.127',
        port=5432
    )
    cur = conn.cursor()
    cur.execute('SELECT rules, templates FROM users WHERE username = %s', (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row[0] or [], row[1] or []
    return [], []

def save_user_data_db(username, rules, templates):
    ensure_users_table()
    
    conn = psycopg2.connect(
        dbname='tcgplayerdb',
        user='rmangana',
        password='password',
        host='52.73.212.127',
        port=5432
    )
    cur = conn.cursor()
    cur.execute('UPDATE users SET rules = %s, templates = %s WHERE username = %s', (json.dumps(rules), json.dumps(templates), username))
    conn.commit()
    cur.close()
    conn.close()

def login():
    with st.popover("👤 Login/Logout", use_container_width=True):
        if st.session_state.get("current_user"):
            st.markdown(f"**👤 Logged in as:** `{st.session_state['current_user']}`")
            if st.button("Logout", key="logout_button_sidebar"):
                # Save any new rules/templates before logging out
                save_user_data_db(
                    st.session_state['current_user'],
                    st.session_state.get("saved_rules", []),
                    st.session_state.get("rule_templates", [])
                )
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
                    if username.strip() and password.strip():
                        if check_user_db(username.strip(), password.strip()):
                            st.session_state["current_user"] = username.strip()
                            # Load user data from DB
                            rules, templates = get_user_data_db(username.strip())
                            st.session_state["saved_rules"] = rules
                            st.session_state["rule_templates"] = templates
                            st.success(f"Logged in as {username.strip()}")
                            st.rerun()
                        else:
                            st.warning("Invalid username or password.")
                    else:
                        st.warning("Please enter a username and password.")
            with tab_create:
                new_username = st.text_input("New Username", key="create_username_sidebar")
                new_password = st.text_input("New Password", type="password", key="create_password_sidebar")
                if st.button("Create Account", key="create_account_button", use_container_width=True):
                    if new_username.strip() and new_password.strip():
                        if create_user_db(new_username.strip(), new_password.strip()):
                            st.success(f"Account created for user: {new_username.strip()}. You can now log in.")
                        else:
                            st.warning("Username already exists. Please choose another.")
                    else:
                        st.warning("Please enter a username and password.")

def show_pages_sidebar():
    # Expander for Pages

    with st.sidebar.expander("📄 Pages", expanded=False):
        login()
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("pages/home.py")
        if st.button("💲 Repricer", use_container_width=True):
            st.switch_page("pages/Repricer.py")
        if st.button("📦 EV Tools", use_container_width=True):
            st.switch_page("pages/EVTools.py")
        if st.button("⚡ Pokémon Price Tracker", use_container_width=True):
            st.switch_page("pages/PokemonPriceTracker.py")            
        if st.button("📦 Manabox", use_container_width=True):
            st.switch_page("pages/Manabox.py")
        if st.button("📦 Manage Inventory", use_container_width=True):
            st.switch_page("pages/Manage_Inventory.py")
        if st.session_state.get('current_user') == 'rmangana':
            if st.button("🔄 Update TCGplayer IDs", use_container_width=True):
                st.switch_page("pages/Update_TCGplayer_IDs.py")
            if st.button("☁️ Cloud Control", use_container_width=True):
                st.switch_page("pages/Cloud_Control.py")
            if st.button("🖨️ TCGPlayer Print", use_container_width=True):
                st.switch_page("pages/Tcgplayer_Print_Orders.py")
            if st.button("Test Crop", use_container_width=True):
                st.switch_page("pages/test_crop.py")

def footer():
    """Display a divider, Buy Me a Coffee button, and Discord button as a footer on the page."""
    st.markdown('---')
    discord_url = "https://discord.gg/mrxCZbrg"  # Replace with your actual Discord invite link
    st.markdown(
        f"""
        <style>
        .footer-bar {{ position: fixed; left: 0; bottom: 0; width: 100%; background: #23272a; color: white; text-align: center; padding: 0.5em 0; z-index: 9999; }}
        .footer-bar a.discord-link {{ color: #7289da; font-weight: bold; text-decoration: none; margin-left: 0.5em; }}
        .footer-bar a.coffee-link img {{ vertical-align: middle; margin-bottom: 0; height: 32px; }}
        </style>
        <div class="footer-bar">
            <span>Need help? Have a feature suggestion or bug report? Join our <a href="{discord_url}" class="discord-link" target="_blank">Discord</a>!</span>
            <span style="margin-left: 1.5em;">
                <a href="https://www.buymeacoffee.com/ronaldmangu" class="coffee-link" target="_blank">
                    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" />
                </a>
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )
    # Streamlit native theming via config.toml (see https://docs.streamlit.io/develop/concepts/configuration/theming)
    # This will only take effect if the user has not overridden the theme in their own config or UI
    if "theme" in st.session_state:
        if st.session_state["theme"] == "Dark":
            st.markdown("""
                <style>
                body, .stApp { background-color: #0E1117 !important; color: #FAFAFA !important; }
                .stButton > button { color: #FAFAFA !important; background-color: #262730 !important; }
                </style>
            """, unsafe_allow_html=True)
        elif st.session_state["theme"] == "Light":
            st.markdown("""
                <style>
                body, .stApp { background-color: #FFFFFF !important; color: #262730 !important; }
                .stButton > button { color: #262730 !important; background-color: #FAFAFA !important; }
                </style>
            """, unsafe_allow_html=True)
