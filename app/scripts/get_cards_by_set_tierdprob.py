import requests
import json
import csv
from collections import Counter

# Set the set code
set_code = "dft"
url = f'https://api.scryfall.com/cards/search?q=set:{set_code}+include:extras'

all_cards = []

# Fetch all cards
while url:
    response = requests.get(url)
    data = response.json()

    if 'data' not in data:
        print("❌ Error:", data.get('details', 'Unknown error'))
        break

    all_cards.extend(data['data'])
    url = data.get('next_page')

# Function to calculate the pull probability based on price tiers
def calculate_price_tier(price):
    if price < 1:
        return 9.6  # Higher probability for cards under $1
    elif price < 5:
        return 6  # Medium-low probability for cards under $5
    elif price < 10:
        return 0.24  # Medium probability for cards under $10
    elif price < 20:
        return 1.2  # Low probability for cards under $20
    else:
        return 0.48  # Very low probability for cards over $20

# Set base rarity probabilities (can be adjusted)
pull_chances = {
    'common': 10,  # Commons appear 10 times
    'uncommon': 3,  # Uncommons appear 3 times
    'rare': 1,  # Rares appear 1 time
    'mythic': 3  # Mythics appear 1 in 8 packs (for example)
}

# Count how many of each rarity in the set
rarity_counts = Counter(card['rarity'] for card in all_cards)

# Total number of cards per rarity
total_rarity = {
    rarity: sum(1 for card in all_cards if card['rarity'] == rarity)
    for rarity in rarity_counts
}

# Add pull probability based on rarity and price tier
for card in all_cards:
    rarity = card.get('rarity', 'common')
    
    # Calculate base probability from rarity
    base_chance = pull_chances.get(rarity, 0) / total_rarity.get(rarity, 1)
    
    # Price-based probability adjustment
    price_str = card.get('prices', {}).get('usd', '0')
    try:
        price = float(price_str) if price_str else 0
    except ValueError:
        price = 0

    price_probability = calculate_price_tier(price)
    
    # Combine the rarity and price-based probabilities
    # Assuming we multiply the base chance by the price-based probability
    combined_probability = base_chance * price_probability
    
    # Assign the calculated probability to the card
    card['estimated_pull_probability'] = round(combined_probability, 6)

# Save the updated cards with probabilities to a JSON file
with open(f'{set_code}_cards_with_probabilities.json', 'w', encoding='utf-8') as f:
    json.dump(all_cards, f, indent=2, ensure_ascii=False)

# Save the data to a CSV file
csv_file = f'{set_code}_cards_with_probabilities.csv'
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

print(f"✅ Saved {len(all_cards)} cards to {set_code}_cards_with_probabilities.json and {csv_file}")
