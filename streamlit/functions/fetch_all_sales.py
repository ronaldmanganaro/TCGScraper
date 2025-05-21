"""Fetch all sales data from TCGPlayer and save to CSV and database.
This script uses Playwright to scrape sales data from a specific TCGPlayer product page.
"""

import asyncio
import time
import csv
import datetime
from playwright.async_api import async_playwright, Page
import db


async def scrape_sales_table(page: Page):
    """
    Scrape the sales table from the TCGPlayer page.
    """
    # Wait for table to load
    selector = ".modal__activator"

    await page.wait_for_selector(selector, timeout=20000)
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
        writer = csv.DictWriter(csvfile, fieldnames=[
                                "date", "condition", "quantity", "price"])
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
            'quantity': cell_texts[2].replace('$', '').replace(".00", '') if len(cell_texts) > 2 else '',
        }
        data.append(row_data)

    headers = ['dateRange', 'averagePrice', 'quantity']
    with open("graph.csv", mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


def add_to_db(sales_data, url, card_number):
    print(sales_data)
    daily_totals = {}
    average_prices = {}

    for sale in sales_data:
        # need to get the average cost by adding up all the prices on each date and dividing by the number of prices
        if sale['date'] not in daily_totals:

            print(f"Adding new date: {sale['date']}")
            daily_totals[sale['date']] = {'total_price': 0, 'count': 0}
            daily_totals[sale['date']]['total_price'] += sale['price']
            daily_totals[sale['date']]['count'] += 1
        else:
            print(f"Updating existing date: {sale['date']}")
            daily_totals[sale['date']]['total_price'] += sale['price']
            daily_totals[sale['date']]['count'] += 1

        for date, totals in daily_totals.items():
            average_prices[date] = totals['total_price'] / totals['count']
            print(f"Date: {date}, Average Price: {average_prices[date]}")

    lowest_prices = {}
    for sale in sales_data:
        if sale['date'] not in lowest_prices or sale['price'] < lowest_prices[sale['date']]:
            lowest_prices[sale['date']] = sale['price']

    for day, avg_price in average_prices.items():
        lowest_price = lowest_prices.get(day, None)
        converted_date = datetime.datetime.strptime(
            day, "%m/%d/%y").strftime("%Y-%m-%d")

        print(f"Card Number: {card_number}")

        # Add to database
        db.add_card_data(converted_date, card_number, avg_price, lowest_price)


async def main():
    async with async_playwright() as p:
        # Launch browser
        # headless=False to see the browser
        browser = await p.chromium.launch(headless=False)
        page: Page = await browser.new_page()

        url = "https://www.tcgplayer.com/product/113682/pokemon-generations-vaporeon-ex?Condition=Near+Mint&inStock=true&Language=English&ListingType=standard&page=1"
        # Navigate to the page
        # url = "https://www.tcgplayer.com/product/517052/pokemon-sv-scarlet-and-violet-151-switch-206-165?Condition=Near+Mint&page=1&Language=English9909"
        await page.goto(url)  # Replace with the correct URL

        # Find the span next to the strong tag with specific text
        card_info: str = await page.locator(
            "//strong[text()='Card Number / Rarity:']/following-sibling::span"
        ).inner_text()

        # Extract just the card number
        card_number = '#' + card_info.split(" / ")[0]
        print("Card Number:", card_number)

        # Wait for the page to load
        await scrape_graph(page)
        sales_data = await scrape_sales_table(page)
        add_to_db(sales_data, url, card_number)
        # db.estimate_velocity(db.connectDB(), "Switch - 206/165", "206/165")
        # Close the browser
        time.sleep(5)
        # await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
