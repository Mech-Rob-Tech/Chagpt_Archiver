from playwright.sync_api import sync_playwright
import time

PROFILE = "/home/msp-fsp321/chatgpt_archive/firefox_profile"

CHAT_URL = (
    "https://chatgpt.com/g/g-p-6a94243042c48191809ddc8971ec785d/"
    "c/6a94245e-0390-83e8-81e8-f531e1d5251f"
)

with sync_playwright() as p:

    context = p.firefox.launch_persistent_context(
        PROFILE,
        headless=False
    )

    page = context.pages[0] if context.pages else context.new_page()

    page.goto(
        CHAT_URL,
        wait_until="domcontentloaded",
        timeout=120000
    )

    time.sleep(8)

    container = page.locator(
        "div.group\\/scroll-root"
    ).first

    container.wait_for(
        state="visible",
        timeout=60000
    )

    container.evaluate(
        "el => el.scrollTop = el.scrollHeight"
    )

    time.sleep(2)

    buttons = page.get_by_role(
        "button",
        name="Copy"
    )

    print()
    print("=" * 70)
    print(f"COPY BUTTONS FOUND: {buttons.count()}")
    print("=" * 70)

    for i in range(buttons.count()):

        button = buttons.nth(i)

        text = button.evaluate("""
        el => {
            let p = el.parentElement;

            for (let i = 0; i < 8 && p; i++, p = p.parentElement) {
                const t = (p.innerText || '').trim();

                if (t.length > 100) {
                    return t;
                }
            }

            return '';
        }
        """)

        text = text.strip()

        print()
        print(f"===== COPY BUTTON {i} =====")
        print(f"Characters in ancestor: {len(text):,}")
        print(text[:500].replace("\\n", " | "))

    print()
    print("=" * 70)
    print("END")
    print("=" * 70)

    input("\nPress ENTER to close...")

    context.close()
