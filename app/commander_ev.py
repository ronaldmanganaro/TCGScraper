import requests
import time

def search_card(name, set_code):
    query = f'{name} set:{set_code}'.replace(' ', '+')
    url = f'https://api.scryfall.com/cards/search?q={query}'

    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to fetch from Scryfall:", response.status_code)
        return

    data = response.json()

    if data['object'] == 'error':
        print("Error:", data['details'])
        return

    if data['total_cards'] == 0:
        print("No cards found.")
        return

    # Print the first match
    card = data['data'][0]
    print(f"Name: {card['name']}")
    print(f"Set: {card['set_name']}")
    print(f"Price (USD): {card['prices']['usd']}")
    print(f"Scryfall URL: {card['scryfall_uri']}")
    
    return card['prices']['usd']



with open("TemurRoar copy.txt", "r") as decklist:
    EV = 0
    for line in decklist:
        line = line.strip()
        if not line: 
            continue
        # Step 1: Extract set from brackets
        start = line.index('[')
        end = line.index(']')
        set_code = line[start+1:end]

        # Step 2: Get quantity and card name
        before_set = line[:start].strip()  # "1 Arcane Signet"
        parts = before_set.split(" ", 1)
        quantity = parts[0]
        card_name = parts[1]
        
        print("Quantity:", quantity)
        print("Card Name:", card_name)
        print("Set Code:", set_code)
        
        
        ''' 
        need to account for 
        <extended>
        1 Eshki, Temur's Roar <borderless> [TDC] (F)

        <borderless>
        at the end of the card name
        '''
        price = search_card(card_name, set_code.lower())
        
        
        EV += (float(price) * float(quantity))
        time.sleep(0.101)
    print(f"Total profit {EV}")

