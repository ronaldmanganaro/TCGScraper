import asyncio
import time
import csv
from playwright.async_api import async_playwright, Page

async def scrape_sales_table(page: Page):
    # Wait for table to load
    selector = ".modal__activator"
    
    await page.wait_for_selector(selector,timeout=20000)
    await page.locator(selector).click() 
    while True:
        try:
            # Check if the selector is available
            await page.wait_for_selector("button:has-text('Load More Sales')", timeout=20000)
            await page.click("button:has-text('Load More Sales')")
            
        except Exception as e:
            print(f"Selector not found, retrying... {e}")
            break
    
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

async def run():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # headless=False to see the browser
        page: Page = await browser.new_page()
        
        # Navigate to the page
        await page.goto("https://www.tcgplayer.com/product/517052/pokemon-sv-scarlet-and-violet-151-switch-206-165?Condition=Near+Mint&page=1&Language=English9909")  # Replace with the correct URL

        # Wait for the page to load
        await scrape_graph(page)
        await scrape_sales_table(page)
        # Close the browser
        time.sleep(5)
        #await browser.close()


# Run the async function
asyncio.run(run())


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