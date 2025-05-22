import asyncio
from asyncio import Semaphore
from playwright.async_api import async_playwright
from datetime import datetime
import re
import requests
import db
import sys
import logging

CONCURRENT_LIMIT = 3  # Try 2-5 to start

def send_discord_alert(message, webhook_url):
    data = {"content": message}
    requests.post(webhook_url, json=data)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler(sys.stdout)])

class Data:
    def __init__(self, card, listing_quantity, lowest_price, market_price, rarity, card_number, set_name, link):
        self.card = card
        self.listing_quantity = listing_quantity
        self.lowest_price = lowest_price
        self.market_price = market_price
        self.rarity = rarity
        self.card_number = card_number
        self.set_name = set_name
        self.link = link

URL_TEMPLATE = "https://www.tcgplayer.com/search/pokemon/product?productLineName=pokemon&view=grid&ProductTypeName=Cards&page={page}&Condition=Near+Mint&Rarity=Ultra+Rare|Illustration+Rare|Special+Illustration+Rare|Hyper+Rare|Rare+BREAK|Amazing+Rare|Shiny+Ultra+Rare|Prism+Rare|Secret+Rare&inStock=true&Language=English&ListingType=standard"

async def scrape_page(page_num, context, sem):
    async with sem:
        page = await context.new_page()
        page_start = datetime.now()
        print(f"Scraping page {page_num}")
        await page.goto(URL_TEMPLATE.format(page=page_num))
        try:
            await page.wait_for_selector(".search-result", timeout=10000)
        except Exception:
            print(f"No listings on page {page_num}")
            await page.close()
            return []

        listings = await page.query_selector_all(".search-result")
        page_data = []
        for listing in listings:
            try:
                name_el = await listing.query_selector("[class*='product-card__title']")
                name = await name_el.inner_text() if name_el else "Unknown"

                listing_count_el = await listing.query_selector("span.inventory__listing-count")
                listing_count_text = await listing_count_el.inner_text() if listing_count_el else "0"
                listing_count = int(re.search(r"\d+", listing_count_text).group()) if re.search(r"\d+", listing_count_text) else 0

                lowest_price_el = await listing.query_selector("span.inventory__price-with-shipping")
                lowest_price = await lowest_price_el.inner_text() if lowest_price_el else "0"
                lowest_price = lowest_price.replace("$", "").replace(",", "")

                rarity_section = await listing.query_selector(".product-card__rarity__variant")
                if rarity_section:
                    rarity_parts = await rarity_section.query_selector_all("span")
                    rarity = await rarity_parts[0].inner_text() if len(rarity_parts) > 0 else "Unknown"
                    card_number = await rarity_parts[1].inner_text() if len(rarity_parts) > 1 else "Unknown"
                else:
                    rarity = "Unknown"
                    card_number = "Unknown"

                set_name_el = await listing.query_selector(".product-card__set-name__variant")
                set_name = await set_name_el.inner_text() if set_name_el else "Unknown"

                market_price_el = await listing.query_selector("span.product-card__market-price--value")
                market_price = await market_price_el.inner_text() if market_price_el else "0"
                market_price = market_price.replace("$", "").replace(",", "")

                link_el = await listing.query_selector("a[data-testid*='product-card__image']")
                product_link = await link_el.get_attribute("href") if link_el else ""
                if product_link and not product_link.startswith("http"):
                    product_link = "https://www.tcgplayer.com" + product_link

                page_data.append(Data(
                    name, listing_count, lowest_price, market_price, rarity, card_number, set_name, product_link
                ))
            except Exception as e:
                print(f"Error on page {page_num}: {e}")

        # Print time taken for this page
        page_end = datetime.now()
        page_elapsed = page_end - page_start
        p_min, p_sec = divmod(page_elapsed.total_seconds(), 60)
        print(f"Finished page {page_num} in {int(p_min)} min {int(p_sec)} sec")
        await page.close()
        return page_data

async def main():
    # Logging and startup message
    start = datetime.now()
    msg = f"Started Scraping {start.strftime('%Y-%m-%d %I:%M:%S %p')}"
    send_discord_alert(msg, "https://discord.com/api/webhooks/1348736048066461788/7cLvt3ajZ9-hX7ZIFjurWyNyv87ka44-eViI3U2eWXEdAogqMehev5hIsGduUCbdkudV")

    sem = Semaphore(CONCURRENT_LIMIT)
    all_data = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        # Determine total pages
        page = await context.new_page()
        await page.goto(URL_TEMPLATE.format(page=1))
        try:
            await page.wait_for_selector(".search-pagination", timeout=10000)
            pagination = await page.query_selector(".search-pagination")
            page_links = await pagination.query_selector_all("a")
            total_pages = int(await page_links[-2].inner_text())
        except Exception:
            total_pages = 1
        print(f"Total pages detected: {total_pages}")
        await page.close()

        tasks = [scrape_page(page_num, context, sem) for page_num in range(1, total_pages + 1)]
        results = await asyncio.gather(*tasks)
        for result in results:
            all_data.extend(result)

        await browser.close()
    
        end = datetime.now()
        elapsed = end - start
        minutes, seconds = divmod(elapsed.total_seconds(), 60)
        msg = f"Finished Scraping {end.strftime('%Y-%m-%d %I:%M:%S %p')}\nTime elapsed: {int(minutes)} min {int(seconds)} sec"
        send_discord_alert(msg, "https://discord.com/api/webhooks/1348736048066461788/7cLvt3ajZ9-hX7ZIFjurWyNyv87ka44-eViI3U2eWXEdAogqMehev5hIsGduUCbdkudV")

    if all_data:
        start = datetime.now()
        db.writeDB(db.connectDB(), all_data)
        end = datetime.now()
        
        elapsed = end - start
        minutes, seconds = divmod(elapsed.total_seconds(), 60)
        msg = f"Finished Writing to DB {end.strftime('%Y-%m-%d %I:%M:%S %p')}\nTime elapsed: {int(minutes)} min {int(seconds)} sec"
        send_discord_alert(msg, "https://discord.com/api/webhooks/1348736048066461788/7cLvt3ajZ9-hX7ZIFjurWyNyv87ka44-eViI3U2eWXEdAogqMehev5hIsGduUCbdkudV")

if __name__ == "__main__":
    asyncio.run(main())
