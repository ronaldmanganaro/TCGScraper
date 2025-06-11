from playwright.sync_api import sync_playwright
import logging

def scrape_add_to_cart_id(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined })")
        page = context.new_page()
        try:
            page.set_extra_http_headers({
                "Accept-Language": "en-US,en;q=0.9"
            })
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector("section[data-testid^='AddToCart_FS_']", timeout=60000)


            section = page.locator("section[data-testid^='AddToCart_FS_']")
            data_testid = section.get_attribute("data-testid")

            if data_testid:
                return data_testid.split('_')[2].split('-')[0]

        except Exception as e:
            logging.warning(f"Error scraping AddToCart ID: {e}")
            page.screenshot(path="error_screenshot.png")
            with open("error_page.html", "w", encoding="utf-8") as f:
                f.write(page.content())
        finally:
            browser.close()
        return None


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.tcgplayer.com/product/269069/magic-streets-of-new-capenna-sewer-crocodile?page=1&Language=English"
    result = scrape_add_to_cart_id(url)
    if result:
        print(result)
    else:
        print("")
