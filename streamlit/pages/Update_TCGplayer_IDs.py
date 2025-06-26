import streamlit as st
import os
import logging
import subprocess
import json
import psycopg2
import time
import pandas as pd
from functions import widgets

widgets.show_pages_sidebar()
# Check if user is logged in and is 'rmangana'
if not st.session_state.get('current_user') or st.session_state['current_user'] != 'rmangana':
    st.warning('You must be logged in as rmangana to view this page.')
    widgets.login()
    st.stop()
    

def run_playwright_script(url):
    script_path = os.path.join(os.path.dirname(__file__), '../functions/scrape_playwright.py')
    result = subprocess.run(
        ["python", script_path, url],
        capture_output=True,
        text=True,
        env=os.environ.copy(),
        cwd=os.path.dirname(script_path)
    )
    logging.info(f"Subprocess stdout: {result.stdout.strip()}")
    logging.info(f"Subprocess stderr: {result.stderr.strip()}")
    if result.returncode != 0:
        logging.warning(f"Subprocess failed with return code {result.returncode}")
        return None
    output = result.stdout.strip()
    if output and output.isdigit():
        return output
    return None


def update_tcgplayer_ids_from_json_streamlit(json_file, dbname='scryfall', selected_sets=None):
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
    cards = json.load(json_file)
    logging.debug(f"Loaded {len(cards)} cards from JSON.")
    conn = psycopg2.connect(
        dbname=dbname,
        user='rmangana',
        password='password',
        host='52.73.212.127',
        port=5432
    )
    cur = conn.cursor()
    total = len(cards)
    progress = st.progress(0, text="Starting...")
    updated = 0
    updated_normal = 0
    updated_foil = 0
    failed = 0
    updated_cards = []
    failed_cards = []
    console_output = st.empty()
    for idx, card in enumerate(cards):
        if selected_sets and card.get('set') not in selected_sets:
            logging.debug(f"Skipping card {card.get('name', card.get('id'))} because it's not in the selected sets.")
            continue
        tcgplayer_id = card.get('tcgplayer_id')
        logging.debug(f"Processing card {idx+1}/{total}: {card.get('name', card.get('id'))} (tcgplayer_id={tcgplayer_id})")
        if not tcgplayer_id:
            logging.debug(f"Skipping card {card.get('name', card.get('id'))} because tcgplayer_id is missing.")
            continue
        # Always define these at the start of the loop so they are available everywhere in the loop
        should_scrape_normal = card.get('nonfoil', True)
        should_scrape_foil = card.get('foil', True)
        add_to_cart_id_normal = None
        add_to_cart_id_foil = None

        # Only define and use should_scrape_normal/should_scrape_foil in this block
        if should_scrape_normal:
            url_normal = f"https://www.tcgplayer.com/product/{int(tcgplayer_id)}?Language=English&page=1&Printing=Normal&Condition=Near+Mint"
            logging.info(f"Scraping TCGplayer URL: {url_normal}")
            add_to_cart_id_normal = run_playwright_script(url_normal)
        if should_scrape_foil:
            url_foil = f"https://www.tcgplayer.com/product/{int(tcgplayer_id)}?Language=English&page=1&Printing=Foil&Condition=Near+Mint"
            logging.info(f"Scraping TCGplayer URL: {url_foil}")
            add_to_cart_id_foil = run_playwright_script(url_foil)
        logging.debug(f"Normal AddToCart ID: {add_to_cart_id_normal}")
        logging.debug(f"Foil AddToCart ID: {add_to_cart_id_foil}")
        scryfall_id = card.get('id')
        card_name = card.get('name', scryfall_id)
        try:
            did_update = False
            if add_to_cart_id_normal:
                cur.execute(
                    """
                    UPDATE scryfall
                    SET tcgplayer_id_normal = %s
                    WHERE id = %s
                    """,
                    (add_to_cart_id_normal, scryfall_id)
                )
                updated_normal += 1
                did_update = True
                console_output.write(f"[Normal] Updated {card_name} ({scryfall_id}) with {add_to_cart_id_normal}")
                logging.info(f"[Normal] Updated {card_name} ({scryfall_id}) with {add_to_cart_id_normal}")
            if add_to_cart_id_foil:
                cur.execute(
                    """
                    UPDATE scryfall
                    SET tcgplayer_id_foil = %s
                    WHERE id = %s
                    """,
                    (add_to_cart_id_foil, scryfall_id)
                )
                updated_foil += 1
                did_update = True
                console_output.write(f"[Foil] Updated {card_name} ({scryfall_id}) with {add_to_cart_id_foil}")
                logging.info(f"[Foil] Updated {card_name} ({scryfall_id}) with {add_to_cart_id_foil}")
            if did_update:
                updated += 1
                updated_cards.append(card_name)
            conn.commit()
        except Exception as e:
            msg = f"Failed to update {card_name} ({scryfall_id}): {e}"
            st.warning(msg)
            console_output.write(msg)
            logging.error(msg)
            conn.rollback()
            failed += 1
            failed_cards.append(card_name)
        progress.progress((idx + 1) / total, text=f"Processing card {idx + 1} of {total}")
    cur.close()
    conn.close()
    progress.empty()
    st.success(f"Done! Updated {updated} cards. Normal: {updated_normal}, Foil: {updated_foil}, Failed: {failed}")


def insert_cards_from_json_streamlit(json_file, dbname='scryfall', selected_sets=None):
    import psycopg2
    import json
    import logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
    cards = json.load(json_file)
    filtered_cards = [c for c in cards if c.get('set') in selected_sets]
    st.info(f"Processing {len(filtered_cards)} cards from sets: {', '.join(selected_sets)}")
    conn = psycopg2.connect(
        dbname=dbname,
        user='rmangana',
        password='password',
        host='52.73.212.127',
        port=5432
    )
    cur = conn.cursor()
    inserted = 0
    skipped = 0
    failed = 0
    progress = st.progress(0, text="Starting...")
    status_box = st.container()
    processed_cards = []
    start_time = time.time()
    estimated_time = None
    for idx, card in enumerate(filtered_cards):
        should_scrape_normal = card.get('nonfoil', True)
        should_scrape_foil = card.get('foil', True)
        add_to_cart_id_normal = None
        add_to_cart_id_foil = None
        cards_left = len(filtered_cards) - (idx + 1)
        estimated_time = cards_left * 7
        est_mins, est_secs = divmod(int(estimated_time), 60)
        mins, secs = divmod(int(time.time() - start_time), 60)
        # Show more card info in the progress bar
        progress_text = (
            f"Processing card {idx + 1} of {len(filtered_cards)}: "
            f"{card.get('name', card.get('id'))} | "
            f"Set: {card.get('set', 'N/A')} | "
            f"Collector #: {card.get('collector_number', 'N/A')} | "
            f"Rarity: {card.get('rarity', 'N/A')} | "
            f"TCG ID: {card.get('tcgplayer_id', 'N/A')} | "
            f"Elapsed: {mins}m {secs}s | Est. left: {est_mins}m"
        )
        progress.progress((idx + 1) / len(filtered_cards), text=progress_text)
        scryfall_id = card.get('id')
        card_name = card.get('name', scryfall_id)
        cur.execute("SELECT tcgplayer_id_normal, tcgplayer_id_foil FROM scryfall WHERE id = %s", (scryfall_id,))
        row = cur.fetchone()
        logging.debug(f"DB values for {scryfall_id}: normal={row[0]}, foil={row[1]}")
        status = {
            'Card Name': card_name,
            'Scryfall ID': scryfall_id,
            'Set': card.get('set'),
            'Collector Number': card.get('collector_number'),
            'Normal': '',
            'Foil': '',
            'Status': ''
        }
        normal_timeout = False
        foil_timeout = False
        if row:
            try:
                updated_any = False
                updated_types = []
                if should_scrape_normal and row[0] is None and card.get('tcgplayer_id'):
                    url_normal = f"https://www.tcgplayer.com/product/{int(card.get('tcgplayer_id'))}?Language=English&page=1&Printing=Normal&Condition=Near+Mint"
                    try:
                        add_to_cart_id_normal = run_playwright_script(url_normal)
                    except Exception as e:
                        normal_timeout = True
                    if add_to_cart_id_normal:
                        cur.execute(
                            """
                            UPDATE scryfall SET tcgplayer_id_normal = %s WHERE id = %s
                            """,
                            (add_to_cart_id_normal, scryfall_id)
                        )
                        conn.commit()
                        inserted += 1
                        updated_any = True
                        updated_types.append('Normal')
                        status['Normal'] = 'Added'
                    elif normal_timeout or add_to_cart_id_normal is None:
                        status['Normal'] = 'Timeout or Not Found'
                        normal_timeout = True
                elif not should_scrape_normal:
                    status['Normal'] = 'No Normal Print'
                elif row[0] is not None:
                    status['Normal'] = 'Already in DB'
                else:
                    status['Normal'] = 'No Normal Print'
                if should_scrape_foil and row[1] is None and card.get('tcgplayer_id'):
                    url_foil = f"https://www.tcgplayer.com/product/{int(card.get('tcgplayer_id'))}?Language=English&page=1&Printing=Foil&Condition=Near+Mint"
                    try:
                        add_to_cart_id_foil = run_playwright_script(url_foil)
                    except Exception as e:
                        foil_timeout = True
                    if add_to_cart_id_foil:
                        cur.execute(
                            """
                            UPDATE scryfall SET tcgplayer_id_foil = %s WHERE id = %s
                            """,
                            (add_to_cart_id_foil, scryfall_id)
                        )
                        conn.commit()
                        inserted += 1
                        updated_any = True
                        updated_types.append('Foil')
                        status['Foil'] = 'Added'
                    elif foil_timeout or add_to_cart_id_foil is None:
                        status['Foil'] = 'Timeout or Not Found'
                        foil_timeout = True
                elif not should_scrape_foil:
                    status['Foil'] = 'No Foil Print'
                elif row[1] is not None:
                    status['Foil'] = 'Already in DB'
                else:
                    status['Foil'] = 'No Foil Print'
                # Status summary for timeouts
                if normal_timeout and foil_timeout:
                    status['Status'] = 'Timeout: Both'
                elif normal_timeout:
                    status['Status'] = 'Timeout: Normal'
                elif foil_timeout:
                    status['Status'] = 'Timeout: Foil'
                elif updated_types:
                    status['Status'] = 'Added: ' + ', '.join(updated_types)
                else:
                    status['Status'] = 'No Update'
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Failed <b>{card_name}</b> ({scryfall_id}): {e}", icon="❌")
                progress.progress((idx + 1) / len(filtered_cards), text=f"Failed {card_name}")
                failed += 1
                status['Status'] = f'Failed: {e}'
            processed_cards.append(status)
            continue
        try:
            cur.execute(
                """
                INSERT INTO scryfall (id, name, collector_number, set, tcgplayer_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (scryfall_id, card.get('name'), card.get('collector_number'), card.get('set'), card.get('tcgplayer_id'))
            )
            conn.commit()
            inserted += 1
            status['Status'] = 'Inserted'
        except Exception as e:
            conn.rollback()
            failed += 1
            st.warning(f"Failed to insert {card_name} ({scryfall_id}): {e}")
            progress.progress((idx + 1) / len(filtered_cards), text=f"Failed {card_name}")
            status['Status'] = f'Failed: {e}'
        processed_cards.append(status)
    cur.close()
    conn.close()
    progress.empty()
    st.success(f"Done! Inserted {inserted} cards, skipped {skipped} (already in DB), failed {failed}.")
    # After processing, show the DataFrame using AgGrid and keep it in session state for paging
    if processed_cards:
        df = pd.DataFrame(processed_cards)
        st.session_state['processed_cards_df'] = df

st.title("Update TCGplayer IDs from JSON")
st.write("Upload a Scryfall-formatted JSON file. The app will let you pick which sets to update, then scrape TCGplayer and update the database, showing progress.")
json_file = st.file_uploader("Upload JSON file", type=["json"])
if json_file is not None:
    # Always load the cards DataFrame and store in session state so it persists across reruns
    if 'cards_data' not in st.session_state or st.session_state.get('cards_data_filename') != json_file.name:
        cards = json.load(json_file)
        st.session_state['cards_data'] = cards
        st.session_state['cards_data_filename'] = json_file.name
    else:
        cards = st.session_state['cards_data']
    all_sets = sorted(set(card.get('set', '') for card in cards if card.get('set')))
    with st.container():
        col_filter, col_select, col_buttons = st.columns([1, 2, 1])
        with col_filter:
            set_filter = st.text_input("Filter sets (type to search)", "")
        filtered_sets = [s for s in all_sets if set_filter.lower() in s.lower()]
        if 'selected_sets' not in st.session_state:
            st.session_state['selected_sets'] = filtered_sets.copy()
        with col_select:
            selected_sets = st.multiselect(
                "Select sets to update",
                options=filtered_sets,
                default=st.session_state['selected_sets'],
                key="set_multiselect"
            )
        with col_buttons:
            btn1, btn2 = st.columns(2)
            with btn1:
                st.markdown("<div style='padding-top: 0.5em'></div>", unsafe_allow_html=True)
                if st.button("Select All", key="select_all_sets", help="Select all sets currently shown in the filtered list.", use_container_width=True):
                    st.session_state['selected_sets'] = filtered_sets.copy()
                    st.rerun()
            with btn2:
                st.markdown("<div style='padding-top: 0.5em'></div>", unsafe_allow_html=True)
                if st.button("Clear All", key="clear_all_sets", help="Clear all selected sets.", use_container_width=True):
                    st.session_state['selected_sets'] = []
                    st.rerun()
        st.session_state['selected_sets'] = selected_sets
        # Rewind file for re-read
        json_file.seek(0)
        if st.button("Add Selected Sets to DB", help="Add all cards from the selected sets to the database."):
            from io import StringIO
            import json as _json
            cards_data_io = StringIO(_json.dumps(st.session_state['cards_data']))
            insert_cards_from_json_streamlit(cards_data_io, selected_sets=selected_sets)

# Move AgGrid display to the bottom and put it in an expander
if 'processed_cards_df' in st.session_state:
    import pandas as pd
    from st_aggrid import AgGrid, GridOptionsBuilder

    with st.expander('Processed Cards Summary', expanded=False):
        df = st.session_state['processed_cards_df']
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(filter=True, sortable=True, resizable=True, autoHeight=True, wrapText=True)
        gb.configure_pagination(paginationAutoPageSize=100)
        # Autosize columns to fit the longest text
        gb.configure_grid_options(domLayout='autoHeight')
        gridOptions = gb.build()
        AgGrid(df, gridOptions=gridOptions, enable_enterprise_modules=False, theme='streamlit', use_container_width=True)

from streamlit.functions.widgets import footer

footer()
