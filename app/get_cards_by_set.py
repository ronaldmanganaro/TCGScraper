import requests
import json
import csv
from collections import Counter

# Set the set code
set_code = "dsk"
url = f'https://api.scryfall.com/cards/search?q=set:{set_code}+include:extras'

all_cards = []

# Loop to fetch all cards
while url:
    response = requests.get(url)
    data = response.json()

    if 'data' not in data:
        print("❌ Error:", data.get('details', 'Unknown error'))
        break

    all_cards.extend(data['data'])
    url = data.get('next_page')

# Get set information to calculate probabilities
set_info = requests.get(f"https://api.scryfall.com/sets/{set_code}").json()

# Count how many of each rarity in the set
rarity_counts = Counter(card['rarity'] for card in all_cards)

# Total number of cards per rarity
total_rarity = {
    rarity: sum(1 for card in all_cards if card['rarity'] == rarity)
    for rarity in rarity_counts
}

# Probability based on rarity (can adjust as needed)
pull_chances = {
    'common': 10,
    'uncommon': 3,
    'rare': 2,
    'mythic': 1/4  # Example, adjust accordingly for mythic slots
}

# Add probability field to each card
for card in all_cards:
    rarity = card.get('rarity', 'common')
    base_chance = pull_chances.get(rarity, 0)
    prob = base_chance / total_rarity.get(rarity, 1)  # Avoid division by zero
    card['estimated_pull_probability'] = round(prob, 6)

# Save to JSON file
with open(f'{set_code}_cards.json', 'w', encoding='utf-8') as f:
    json.dump(all_cards, f, indent=2, ensure_ascii=False)

# Save to CSV file
csv_file = f'{set_code}_cards.csv'
with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    # Write CSV headers
    writer.writerow([
        'Name', 'Set', 'Collector Number', 'Rarity',
        'Foil', 'Nonfoil', 'USD Price', 'Frame Effects', 'Estimated Pull Probability'
    ])
    
    # Write data for each card
    for card in all_cards:
        writer.writerow([
            card.get('name'),
            card.get('set'),
            card.get('collector_number'),
            card.get('rarity'),
            card.get('foil'),
            card.get('nonfoil'),
            card.get('prices', {}).get('usd'),
            ','.join(card.get('frame_effects', [])) if card.get('frame_effects') else '',
            card.get('estimated_pull_probability')
        ])

print(f"✅ Saved {len(all_cards)} cards to {set_code}_cards.json and {csv_file}")
