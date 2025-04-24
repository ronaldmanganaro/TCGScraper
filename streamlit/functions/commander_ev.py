import requests
import time
import json
import os
from urllib.parse import quote_plus


def search_card(card_name, set_code, collector_number=None, treatment=None, is_foil="nonfoil"):
    
    if collector_number is not None:
        url = f'https://api.scryfall.com/cards/{set_code}/{collector_number}'
        response = requests.get(url)
        if response.status_code != 200:
            print("Failed to fetch from Scryfall:", response.status_code)
            return

        card = response.json()
        
    else:
        if treatment == "extended":
            frame_treatment = "frame:extendedart"
        elif treatment == '':
            frame_treatment = ''
        elif treatment == 'borderless':
            frame_treatment = "frame:borderless"
        elif treatment == "retro":
             frame_treatment = "frame:1997"
        elif treatment == "showcase":
            frame_treatment = "frame:showcase"
        
        
        query = f'name:{card_name} set:{set_code} {frame_treatment} is:{is_foil}'
        # print(query)
        url = f'https://api.scryfall.com/cards/search?q={quote_plus(query)}'
        # print(url)
        response = requests.get(url)
        if response.status_code != 200:
            print("Failed to fetch from Scryfall:", response.status_code)
            print(url)
            print(card_name)
            return

        card = response.json()
        with open("data.json", 'w') as card_data:
            json.dump(card, card_data, indent=4)

        if card['object'] == 'error':
            print("Error:", card['details'])
            return

        if card['total_cards'] == 0:
            print("No cards found.")
            return

        # Print the first match
        card = card['data'][0]
        # print(f"Name: {card['name']}")
        # print(f"Set: {card['set_name']}")
        # print(f"Price (USD): {card['prices']['usd']}")
        # print(f"Scryfall URL: {card['scryfall_uri']}")
    
    return card['prices']['usd']


cwd = os.getcwd()

path = os.path.join(cwd, "app", "precons")

for root, dirs, files in os.walk(path):
    for filename in files:
        file_path = os.path.join(root, filename)
        with open(file_path, "r") as decklist:
            EV = 0
            for line in decklist:
                collector_number = None
                treatment = ''
                
                line = line.strip()
                if not line: 
                    continue
                
                #check if <> exists
                if '<' in line and '>' in line:
                    start = line.index('<')
                    end = line.index('>')
                    between_less_than_greater_than = line[start+1: end]
                    if between_less_than_greater_than == "borderless" or between_less_than_greater_than == "extended" or between_less_than_greater_than == "retro" or between_less_than_greater_than == "showcase":
                        treatment = between_less_than_greater_than
                        # print("Treatment:", treatment)           
                        line = line.replace(f"<{treatment}>", "")
                    else:
                        collector_number = between_less_than_greater_than
                        # print("Collector Number:", collector_number)           
                        line = line.replace(f"<{collector_number}>", "")
                        
                #check if <> exists
                if '(' in line and ')' in line:
                    start = line.index('(')
                    end = line.index(')')
                    between_parans = line[start+1: end]
                    if between_parans == "F":
                        is_foil = "foil"
                        # print("is foil:", is_foil)           
                        line = line.replace(f"F", "")
                else:
                    is_foil = "nonfoil"
                    
                    
                # Step 1: Extract set from brackets
                start = line.index('[')
                end = line.index(']')
                set_code = line[start+1:end]

                # Step 2: Get quantity and card name
                before_set = line[:start].strip()  # "1 Arcane Signet"
                parts = before_set.split(" ", 1)
                quantity = parts[0]
                card_name = parts[1]
                
                # print("Quantity:", quantity)
                # print("Card Name:", card_name)
                # print("Set Code:", set_code)
                
                if collector_number is not None:
                    price = search_card(card_name=card_name, set_code=set_code.lower(), collector_number=collector_number, is_foil=is_foil)
                else:
                    price = search_card(card_name=card_name, set_code=set_code.lower(), treatment=treatment, is_foil=is_foil)
                
                    
                EV += (float(price) * float(quantity))
                # print(f"{card_name} price: {float(price)}")
                time.sleep(0.101)
            print(f"{filename} Total profit {EV}")

