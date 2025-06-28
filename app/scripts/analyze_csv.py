import time
import logging
import sys
import csv


import argparse
import requests

def calculate_net_profit(csv_file_name, product_line):
    # for each row add total amount - fee amount
    total_profit = 0
    with open(csv_file_name) as csv_file:
        reader = csv.DictReader(csv_file)
        
        filtered_rows = [row for row in reader if row['Product Line'].lower() == f"{product_line}"]
        
        for row in filtered_rows:
            
            item_price = float(row['Price'])
            fee_amount = float(row['Fee Amount'])
            quantity = float(row['Quantity'])
            profit = (item_price * quantity) - fee_amount
            # Negative profit means that there were more than one card sold first card gets all the fees
            # if profit < 0:
            #     print(f"{row['Order Id']}")
            #     print(f" (item_price * quantity) - fee_amount = profit")
            #     print(f" {item_price} * {quantity} - {fee_amount} = {profit}")
            total_profit += profit
        
    print(f"{product_line} {total_profit}")
    return total_profit

def parse_args():
    parser = argparse.ArgumentParser(description="Takes in CSV from order wand and calculates things")
    parser.add_argument("-f", "--file")
    return parser.parse_args()

def main():
    args = parse_args()
   
    corrected_csv = fix_product_line(args.file)
    
    # with open(corrected_csv, newline='') as csv_file:
    #     reader = csv.DictReader(csv_file)
    #     filtered_rows = [row for row in reader if row['Product Line'] == 'MtG']
    #     # for each oreder id add 
    #     #order_ids = 
    
    all_profit = 0      
    
    all_profit += calculate_net_profit(corrected_csv, 'pokemon')
    all_profit += calculate_net_profit(corrected_csv, 'mtg')
    all_profit += calculate_net_profit(corrected_csv, 'digimon')
    all_profit += calculate_net_profit(corrected_csv, 'yugioh')
    
    print(all_profit)
    
        
def fix_product_line(csv_file):
    
    with open(csv_file, newline='') as csv_file:
        reader = csv.DictReader(csv_file)
        # product line unknown fix by parsing the product name
        rows = list(reader)
        fieldnames = reader.fieldnames  # Capture this before the file closes

        for row in rows:
            if row['Product Line'].lower() == 'unknown':
                name = row['Product Name'].lower()
                if 'magic' in name:
                    row['Product Line'] = 'MtG'
                elif 'pokemon' in name:
                    row['Product Line'] = 'Pokemon'
                elif 'yugioh' in name:
                    row['Product Line'] = "YuGiOh"
                elif 'digimon' in name:
                    row['Product Line'] = "digimon"
    
    csv_name = "fixed.csv"
    # Overwrite the original file
    with open(csv_name, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    return csv_name


if __name__ == "__main__":
    main()
