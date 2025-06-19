import db

"""
card_info_list: List of (name, collector_number, set)
Returns: dict mapping (name, collector_number, set) -> tcgplayer_card_id
"""
cards = [
    ("Ancestor's Chosen", "1", "10e", True),
    ("Ancestor's Chosen", "1", "10e", False),
]

conn = db.connectDB("scryfall")
cur = conn.cursor()
try:
    # Build WHERE clause for batch query
    format_strings = ','.join(['(%s,%s,%s,%s)'] * len(cards))
    params = []
    for name, collector_number, set, foil in cards:
        print(name, collector_number, set, foil)
        params.extend([name, collector_number, set, foil])
    
    query = f"""
        SELECT name, collector_number, set, foil, tcgplayer_id FROM scryfall
        WHERE (name, collector_number, set, foil) IN ({format_strings})
    """
    cur.execute(query, params)
    results = cur.fetchall()
    lookup = {}
    for name, collector_number, set, foil, tcgplayer_card_id in results:
        if tcgplayer_card_id is not None:
            lookup[(name, collector_number, set, foil)] = tcgplayer_card_id
    print(lookup) 
finally:
    cur.close()
    conn.close()