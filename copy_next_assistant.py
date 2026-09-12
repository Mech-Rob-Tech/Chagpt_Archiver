from playwright.sync_api import sync_playwright
import subprocess
import time
from pathlib import Path

PROFILE = "/home/msp-fsp321/chatgpt_archive/firefox_profile"

CHAT_URL = (
    "https://chatgpt.com/g/g-p-6a94243042c48191809ddc8971ec785d/"
    "c/6a94245e-0390-83e8-81e8-f531e1d5251f"
)

OUT = Path("/home/msp-fsp321/chatgpt_archive/output/copy_test")
OUT.mkdir(parents=True, exist_ok=True)


def clipboard():
    return subprocess.run(
        ["xclip", "-selection", "clipboard", "-o"],
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout


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

    # Get all visible Copy buttons.
    copies = page.get_by_role(
        "button",
        name="Copy"
    )

    print()
    print("=" * 70)
    print("VISIBLE COPY BUTTONS:", copies.count())
    print("=" * 70)

    # Print the surrounding text for each Copy button.
    for i in range(copies.count()):

        btn = copies.nth(i)

        info = btn.evaluate("""
        el => {
            let p = el;

            for (let i = 0; i < 10 && p; i++, p = p.parentElement) {

                const text = (p.innerText || '').trim();

                if (text.length >= 200) {
                    return {
                        tag: p.tagName,
                        text: text.slice(0, 700)
                    };
                }
            }

            return {
                tag: el.tagName,
                text: ''
            };
        }
        """)

        print()
        print(f"--- COPY BUTTON {i} ---")
        print(info["tag"])
        print(info["text"].replace("\n", " | "))

    print()
    print("=" * 70)
    print("CLICKING COPY BUTTON BEFORE THE LAST USER MESSAGE")
    print("=" * 70)

    # The final visible Copy button may belong to the latest assistant
    # response, but the user's latest message has no Copy button.
    # Therefore select the last Copy button currently exposed.
    target = copies.last

    target.scroll_into_view_if_needed()
    target.click(force=True)

    time.sleep(0.5)

    text = clipboard()

    output = OUT / "next_assistant_copy.txt"

    output.write_text(
        text,
        encoding="utf-8"
    )

    print()
    print("✓ COPIED")
    print("Characters:", len(text))
    print("Lines:", len(text.splitlines()))
    print("File:", output)

    print()
    print("FIRST 20 LINES:")
    print("-" * 70)
    print("\n".join(text.splitlines()[:20]))

    input("\nPress ENTER to close Firefox...")

    context.close()
