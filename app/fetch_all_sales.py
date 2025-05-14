import asyncio
import time
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # headless=False to see the browser
        page = await browser.new_page()

        # Navigate to the page
        await page.goto("https://www.tcgplayer.com/product/517052/pokemon-sv-scarlet-and-violet-151-switch-206-165?Condition=Near+Mint&page=1&Language=English9909")  # Replace with the correct URL

        # Wait for the button to be available and click it
        await page.wait_for_selector(".modal__activator")
        await page.click(".modal__activator")

        # Optional: Wait for some content after clicking
        # await page.wait_for_selector(".some-other-element")

        # Close the browser
        time.sleep(5)
        await browser.close()

# Run the async function
asyncio.run(run())
