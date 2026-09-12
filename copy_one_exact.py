from playwright.sync_api import sync_playwright
from pathlib import Path
import subprocess
import time

PROFILE = "/home/msp-fsp321/chatgpt_archive/firefox_profile"

CHAT_URL = (
    "https://chatgpt.com/g/g-p-6a94243042c48191809ddc8971ec785d/"
    "c/6a94245e-0390-83e8-81e8-f531e1d5251f"
)

OUT = Path(
    "/home/msp-fsp321/chatgpt_archive/output/copy_test"
)
OUT.mkdir(parents=True, exist_ok=True)

OUTPUT = OUT / "EXACT_ASSISTANT_RESPONSE.txt"


def clipboard():
    result = subprocess.run(
        ["xclip", "-selection", "clipboard", "-o"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.stdout


with sync_playwright() as p:

    print("=" * 70)
    print("       EXACT ONE ASSISTANT RESPONSE COPY TEST")
    print("=" * 70)

    context = p.firefox.launch_persistent_context(
        PROFILE,
        headless=False
    )

    page = (
        context.pages[0]
        if context.pages
        else context.new_page()
    )

    page.goto(
        CHAT_URL,
        wait_until="domcontentloaded",
        timeout=120000
    )

    print("\nWaiting for ChatGPT...")
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

    time.sleep(3)

    copies = page.get_by_role(
        "button",
        name="Copy"
    )

    print(f"✓ Initially visible Copy buttons: {copies.count()}")

    # The target response begins with this exact text.
    target_text = (
        "Yes. I reviewed the uploaded output and checked "
        "the current NIST position"
    )

    print("\nSearching for target assistant response...")

    target = None

    # ChatGPT progressively mounts older windows.
    # Keep moving upward until the target text becomes mounted.
    for attempt in range(30):

        # Look for the target text anywhere in the conversation.
        matches = page.get_by_text(
            target_text,
            exact=False
        )

        if matches.count() > 0:
            print(
                f"✓ Target response mounted "
                f"(upward attempt {attempt + 1})"
            )

            # Find the nearest ancestor that contains both
            # the target response and a Copy button.
            target = matches.first.locator(
                "xpath=ancestor::*[.//button][1]"
            ).get_by_role(
                "button",
                name="Copy"
            ).first

            if target.count() > 0:
                break

        # Move the REAL conversation scroller upward.
        old_top = container.evaluate(
            "el => el.scrollTop"
        )

        container.evaluate("""
            el => {
                el.scrollTop = Math.max(
                    0,
                    el.scrollTop - 5000
                );
            }
        """)

        time.sleep(1.5)

        new_top = container.evaluate(
            "el => el.scrollTop"
        )

        print(
            f"  attempt {attempt + 1:02d} | "
            f"scroll {old_top:.0f} -> {new_top:.0f} | "
            f"Copy buttons: {page.get_by_role('button', name='Copy').count()}"
        )

    if target is None or target.count() == 0:
        raise RuntimeError(
            "Could not find the target assistant response."
        )

    print("✓ Exact assistant Copy button located")
    target.scroll_into_view_if_needed()

    # ChatGPT's toolbar can have an overlay intercepting
    # the normal pointer action, so use force.
    target.click(force=True)

    time.sleep(1)

    text = clipboard()

    print("\n✓ Clipboard captured")

    print(
        f"Characters: {len(text):,}"
    )

    print(
        f"Lines:      {len(text.splitlines()):,}"
    )

    OUTPUT.write_text(
        text,
        encoding="utf-8"
    )

    print(
        f"\nSaved:\n{OUTPUT}"
    )

    print("\n" + "=" * 70)
    print("FIRST 15 LINES")
    print("=" * 70)

    print(
        "\n".join(
            text.splitlines()[:15]
        )
    )

    print("\n" + "=" * 70)
    print("LAST 15 LINES")
    print("=" * 70)

    print(
        "\n".join(
            text.splitlines()[-15:]
        )
    )

    print("\n" + "=" * 70)

    # Important verification.
    expected = (
        "Yes. I reviewed the uploaded output "
        "and checked the current NIST position"
    )

    if expected.lower() in text.lower():
        print(
            "✅ VERIFIED: correct assistant response copied."
        )
    else:
        print(
            "❌ WRONG RESPONSE COPIED."
        )
        print(
            "The Copy button was clicked, but the clipboard "
            "does not contain the expected assistant response."
        )

    print("=" * 70)

    input("\nPress ENTER to close Firefox...")

    context.close()
