from playwright.sync_api import sync_playwright

PROFILE = "/home/msp-fsp321/chatgpt_archive/firefox_profile"

with sync_playwright() as p:
    context = p.firefox.launch_persistent_context(
        PROFILE,
        headless=False,
    )

    page = context.pages[0] if context.pages else context.new_page()

    page.goto("https://chatgpt.com", wait_until="domcontentloaded")

    print("\nFirefox launched successfully.")
    print("Title:", page.title())
    print("URL:", page.url)

    input("\nPress ENTER to close the test browser...")

    context.close()
