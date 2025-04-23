import random
import json

# Function to simulate a single booster pack opening
def open_booster_pack(cards):
    booster_pack = []
    
    # Add commons (10) based on probability
    commons = [card for card in cards if card['rarity'] == 'common']
    commons_weights = [card['estimated_pull_probability'] for card in commons]
    booster_pack.extend(random.choices(commons, weights=commons_weights, k=10))

    # Add uncommons (3) based on probability
    uncommons = [card for card in cards if card['rarity'] == 'uncommon']
    uncommons_weights = [card['estimated_pull_probability'] for card in uncommons]
    booster_pack.extend(random.choices(uncommons, weights=uncommons_weights, k=3))

    # Add rare/mythic rare (1) based on probability
    rare_or_mythic = [card for card in cards if card['rarity'] in ['rare', 'mythic']]
    rare_or_mythic_weights = [card['estimated_pull_probability'] for card in rare_or_mythic]
    booster_pack.append(random.choices(rare_or_mythic, weights=rare_or_mythic_weights, k=1)[0])

    # Add a foil card (random foil, could be any rarity) based on probability
    foil_cards = [card for card in cards if card.get('foil', False)]
    if foil_cards:
        foil_weights = [card['estimated_pull_probability'] for card in foil_cards]
        booster_pack.append(random.choices(foil_cards, weights=foil_weights, k=1)[0])
    else:
        # If no foil cards, choose randomly from all cards
        booster_pack.append(random.choice(cards))

    return booster_pack

# Function to calculate the expected value (EV) for a given set of cards
def calculate_pack_ev(booster_pack):
    pack_ev = 0

    for card in booster_pack:
        price_str = card['prices'].get('usd', '0')

        try:
            price = float(price_str) if price_str else 0
        except ValueError:
            price = 0

        pack_ev += price

    return pack_ev

# Function to simulate the opening of a booster box
def simulate_booster_box(cards, num_packs=36):
    total_ev = 0
    
    for _ in range(num_packs):
        booster_pack = open_booster_pack(cards)
        total_ev += calculate_pack_ev(booster_pack)

    return total_ev

# Function to simulate multiple booster boxes and calculate average EV
def simulate_multiple_boxes(cards, num_boxes=10):
    total_ev_all_boxes = 0
    ev_list = []

    for i in range(num_boxes):
        ev = simulate_booster_box(cards)
        ev_list.append(ev)
        total_ev_all_boxes += ev
        print(f"Box {i + 1} EV: ${ev:.2f}")

    average_ev = total_ev_all_boxes / num_boxes if num_boxes > 0 else 0
    print(f"\nAverage EV across {num_boxes} boxes: ${average_ev:.2f}")
    return average_ev

def simulate(set, boxes):
    
    # Load the cards from the JSON file
    with open(f'{set}_cards.json', 'r', encoding='utf-8') as f:
        cards = json.load(f)

    # Choose how many boxes to simulate
    num_boxes_to_simulate = boxes
    

    return simulate_multiple_boxes(cards, num_boxes=num_boxes_to_simulate)
