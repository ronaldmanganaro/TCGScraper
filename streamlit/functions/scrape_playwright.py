from playwright.sync_api import sync_playwright

def scrape_add_to_cart_id(url):
    """
    Scrape the AddToCart ID from the given TCGPlayer product page.

    Args:
        url (str): The URL of the TCGPlayer product page.

    Returns:
        str: The AddToCart ID (e.g., '5522523') if found, else None.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)

        # Wait for the AddToCart button to load
        page.wait_for_selector("button[id^='btnAddToCart_FS_']")

        # Extract the button's ID
        button_id = page.locator("button[id^='btnAddToCart_FS_']").get_attribute("id")

        browser.close()

        if button_id:
            # Extract only the numeric part of the ID
            return button_id.split('_')[2].split('-')[0]

        return None

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.tcgplayer.com/product/269069/magic-streets-of-new-capenna-sewer-crocodile?page=1&Language=English"
    print(scrape_add_to_cart_id(url))
