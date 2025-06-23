import psycopg2
import os
import logging
import subprocess
import json

def run_playwright_script(url):
    script_path = os.path.join(os.path.dirname(__file__), 'scrape_playwright.py')
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

def update_tcgplayer_ids_from_json(json_path, dbname='scryfall'):
    """
    For each card in the JSON with a tcgplayer_id, scrape TCGplayer and update the scryfall_to_tcgplayer table.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        cards = json.load(f)
    conn = psycopg2.connect(
        dbname=dbname,
        user='rmangana',
        password='password',
        host='52.73.212.127',
        port=5432
    )
    cur = conn.cursor()
    for card in cards:
        tcgplayer_id = card.get('tcgplayer_id')
        if not tcgplayer_id:
            continue
        url_normal = f"https://www.tcgplayer.com/product/{int(tcgplayer_id)}?Language=English&page=1&Printing=Normal&Condition=Near+Mint"
        add_to_cart_id_normal = run_playwright_script(url_normal)
        url_foil = f"https://www.tcgplayer.com/product/{int(tcgplayer_id)}?Language=English&page=1&Printing=Foil&Condition=Near+Mint"
        add_to_cart_id_foil = run_playwright_script(url_foil)
        scryfall_id = card.get('id')
        try:
            if add_to_cart_id_normal:
                cur.execute(
                    """
                    UPDATE scryfall_to_tcgplayer
                    SET tcgplayer_id_normal = %s
                    WHERE id = %s
                    """,
                    (add_to_cart_id_normal, scryfall_id)
                )
                print(f"Updated {scryfall_id} with tcgplayer_id_normal {add_to_cart_id_normal}")
            if add_to_cart_id_foil:
                cur.execute(
                    """
                    UPDATE scryfall_to_tcgplayer
                    SET tcgplayer_id_foil = %s
                    WHERE id = %s
                    """,
                    (add_to_cart_id_foil, scryfall_id)
                )
                print(f"Updated {scryfall_id} with tcgplayer_id_foil {add_to_cart_id_foil}")
            conn.commit()
        except Exception as e:
            print(f"Failed to update {scryfall_id}: {e}")
            conn.rollback()
    cur.close()
    conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python update_tcgplayer_ids_from_json.py <json_path>")
    else:
        update_tcgplayer_ids_from_json(sys.argv[1])