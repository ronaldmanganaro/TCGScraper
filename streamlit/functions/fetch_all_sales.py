import asyncio
import time
import csv
import datetime
import db
from playwright.async_api import async_playwright, Page

async def scrape_sales_table(page: Page):
    # Wait for table to load
    selector = ".modal__activator"
    
    await page.wait_for_selector(selector,timeout=20000)
    await page.locator(selector).click() 
    # while True:
    #     try:
    #         # Check if the selector is available
    #         await page.wait_for_selector("button:has-text('Load More Sales')", timeout=20000)
    #         await page.click("button:has-text('Load More Sales')")
            
    #     except Exception as e:
    #         print(f"Selector not found, retrying... {e}")
    #         break
    
    await page.wait_for_selector(".latest-sales-table__tbody")

    rows = await page.query_selector_all(".latest-sales-table__tbody tr")

    sales_data = []
    for row in rows:
        date = await (await row.query_selector(".latest-sales-table__tbody__date")).inner_text()
        condition = await (await row.query_selector(".latest-sales-table__tbody__condition div")).inner_text()
        qty = await (await row.query_selector(".latest-sales-table__tbody_quantity")).inner_text()
        price = await (await row.query_selector(".latest-sales-table__tbody__price")).inner_text()

        sales_data.append({
            "date": date.strip(),
            "condition": condition.strip(),
            "quantity": int(qty.strip()),
            "price": float(price.replace("$", "").replace(",", "").strip())
        })
        
        print(f"Date: {date.strip()}, Condition: {condition.strip()}, Quantity: {qty.strip()}, Price: {price.replace('$', '').replace(',', '').strip()}")

    # Save to CSV
    with open("price_history.csv", "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["date", "condition", "quantity", "price"])
        writer.writeheader()
        writer.writerows(sales_data)
    return sales_data

async def scrape_graph(page: Page):
    await page.wait_for_selector("button:has-text('1Y')")
    await page.locator("button:has-text('1Y')").click() 
    # Wait for the container to load
    await page.wait_for_selector(".price-guide__market-price-history-graph-container")
    
    # Should be replaced with a check to see if the graph is loaded
    time.sleep(3)
    
    # Select the table rows within that container
    table_rows = await page.query_selector_all(
        ".price-guide__market-price-history-graph-container table tbody tr"
    )

    data = []
    for row in table_rows:
        cells = await row.query_selector_all("td")
        cell_texts = [await cell.inner_text() for cell in cells]
        print(f"Row: {cell_texts}")  # Debug print

        row_data = {
            'dateRange': cell_texts[0] if len(cell_texts) > 0 else '',
            'averagePrice': cell_texts[1] if len(cell_texts) > 1 else '',
            'quantity': cell_texts[2].replace('$','').replace(".00",'') if len(cell_texts) > 2 else '',
        }
        data.append(row_data)

    headers = ['dateRange', 'averagePrice', 'quantity']
    with open("graph.csv", mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

async def add_to_db(sales_data, url):
    print(sales_data)
    daily_totals = {}
    average_prices = {}

    for sale in sales_data:        
        # need to get the average cost by adding up all the prices on each date and dividing by the number of prices
        if sale['date'] not in daily_totals:
            daily_totals[sale['date']] = {'total_price': 0, 'count': 0}
            daily_totals[sale['date']]['total_price'] += sale['price']
            daily_totals[sale['date']]['count'] += 1

        for date, totals in daily_totals.items():
            average_prices[date] = totals['total_price'] / totals['count']
            print(f"Date: {date}, Average Price: {average_prices[date]}")
        
    for day in average_prices:
        try:
            converted_date = datetime.datetime.strptime(sale['date'], "%m/%d/%y").strftime("%Y-%m-%d")
        except ValueError as e:
            print(f"Error parsing date '{sale['date']}': {e}")
            continue
        card_number_numerator = url.split("?")[0].split("-")[-1]
        card_number_denominator = url.split("?")[0].split("-")[-2]
        card_number = "#" + card_number_numerator + "/" + card_number_denominator
        print(f"Card Number: {card_number}")
        
        # Add to database
        db.add_card_data(converted_date, card_number, average_prices[day])
    ...

async def main():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # headless=False to see the browser
        page: Page = await browser.new_page()
        
        # Navigate to the page
        url  = "https://www.tcgplayer.com/product/517052/pokemon-sv-scarlet-and-violet-151-switch-206-165?Condition=Near+Mint&page=1&Language=English9909"
        await page.goto(url)  # Replace with the correct URL

        # Wait for the page to load
        await scrape_graph(page)
        sales_data = await scrape_sales_table(page)
        await add_to_db(sales_data, url)
        # Close the browser
        time.sleep(5)
        #await browser.close()


if __name__ == "__main__":
    asyncio.run(main())



'''
How do I use the data scraped from the table?

Scrape card history from TCGPlayer
1. Scrape the sales table
2. Convert date from format "MM/DD/YYYY" to "YYYY-MM-DD"
3. lookup card number from database by parsing url for card number
4. Add database entry by copying
    - card name
    - rarity
    - set name
    - link
5. calculate pull lowest price in sales table
6. calculate pull average price in sales table for market price

How do I use the date scraped from the graph?
Recreate the graph on webpage
 test this

def process_scraped_data(sales_data, graph_data, url):
    # Convert date format in sales data
    for sale in sales_data:
        sale['date'] = datetime.datetime.strptime(sale['date'], "%m/%d/%Y").strftime("%Y-%m-%d")

    # Parse card number from URL
    card_number = url.split("?")[0].split("/")[-1]

    # Connect to the database
    conn = sqlite3.connect("tcgplayer.db")
    cursor = conn.cursor()

    # Add database entry
    card_name = "Switch"  # Replace with actual card name if available
    rarity = "Rare"  # Replace with actual rarity if available
    set_name = "Scarlet and Violet 151"  # Replace with actual set name if available
    link = url

    cursor.execute("""
        INSERT INTO cards (card_number, card_name, rarity, set_name, link)
        VALUES (?, ?, ?, ?, ?)
    """, (card_number, card_name, rarity, set_name, link))

    # Calculate lowest price and average price
    prices = [sale['price'] for sale in sales_data]
    lowest_price = min(prices)
    average_price = sum(prices) / len(prices)

    print(f"Lowest Price: {lowest_price}")
    print(f"Average Price: {average_price}")

    # Save graph data to database
    for entry in graph_data:
        cursor.execute("""
            INSERT INTO graph_data (card_number, date_range, average_price, quantity)
            VALUES (?, ?, ?, ?)
        """, (card_number, entry['dateRange'], entry['averagePrice'], entry['quantity']))

    # Commit and close the database connection
    conn.commit()
    conn.close()

    # Recreate the graph on a webpage (placeholder for actual implementation)
    print("Graph data saved. Recreate the graph on your webpage using the graph_data.")
'''