from playwright.sync_api import sync_playwright
from pathlib import Path
import time
import json

PROFILE = "/home/msp-fsp321/chatgpt_archive/firefox_profile"

CHAT_URL = (
    "https://chatgpt.com/g/g-p-6a94243042c48191809ddc8971ec785d/"
    "c/6a94245e-0390-83e8-81e8-f531e1d5251f"
)

OUT = Path("/home/msp-fsp321/chatgpt_archive/output")
OUT.mkdir(exist_ok=True)

ARCHIVE = OUT / "conversation_live.txt"
LOG = OUT / "conversation_progress.jsonl"

SCROLL_STEP = 650
SCROLL_WAIT = 2
TOP_WAIT = 5


def get_stats(text):
    return {
        "characters": len(text),
        "lines": len(text.splitlines()),
    }


with sync_playwright() as p:

    print("=" * 70)
    print("       CHATGPT FULL CONVERSATION TEXT TEST")
    print("=" * 70)

    context = p.firefox.launch_persistent_context(
        PROFILE,
        headless=False
    )

    page = context.pages[0] if context.pages else context.new_page()

    print("\nOpening conversation...")

    page.goto(
        CHAT_URL,
        wait_until="domcontentloaded",
        timeout=120000
    )

    print("Waiting for ChatGPT...")

    time.sleep(15)

    container = page.locator(
        "div.group\\/scroll-root"
    ).first

    container.wait_for(
        state="visible",
        timeout=60000
    )

    print("✓ Conversation container found")

    # Start from latest content.
    container.evaluate(
        "el => el.scrollTop = el.scrollHeight"
    )

    time.sleep(4)

    print("\nStarting upward extraction...")
    print("Firefox will scroll automatically.")
    print("Sidebar is ignored.\n")

    previous_text = ""
    pass_number = 0

    while True:

        pass_number += 1

        # --------------------------------------------------
        # Read ALL currently rendered conversation text
        # --------------------------------------------------

        current_text = container.inner_text()

        stats = get_stats(current_text)

        # --------------------------------------------------
        # Save the CURRENT rendered text
        # --------------------------------------------------

        ARCHIVE.write_text(
            current_text,
            encoding="utf-8"
        )

        # --------------------------------------------------
        # Save progress record
        # --------------------------------------------------

        state = container.evaluate("""
            el => ({
                scrollTop: el.scrollTop,
                scrollHeight: el.scrollHeight,
                clientHeight: el.clientHeight
            })
        """)

        record = {
            "pass": pass_number,
            "characters": stats["characters"],
            "lines": stats["lines"],
            "scrollTop": state["scrollTop"],
            "scrollHeight": state["scrollHeight"],
            "timestamp": time.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        }

        with LOG.open(
            "a",
            encoding="utf-8"
        ) as f:

            f.write(
                json.dumps(record)
                + "\n"
            )

        # --------------------------------------------------
        # DISPLAY
        # --------------------------------------------------

        print(
            f"Pass {pass_number:04d} | "
            f"Characters: {stats['characters']:,} | "
            f"Lines: {stats['lines']:,} | "
            f"Scroll: {state['scrollTop']:.0f}"
        )

        # --------------------------------------------------
        # CURRENT TOP
        # --------------------------------------------------

        if state["scrollTop"] <= 5:

            print()
            print("⏳ Current loaded top reached.")
            print("⏳ Waiting for older history...")

            before = container.inner_text()
            before_height = container.evaluate(
                "el => el.scrollHeight"
            )

            time.sleep(TOP_WAIT)

            after = container.inner_text()
            after_height = container.evaluate(
                "el => el.scrollHeight"
            )

            # ChatGPT loaded another older section.
            if (
                after != before
                or after_height != before_height
            ):

                print("✓ Older history loaded.")
                print(
                    f"  Characters now: {len(after):,}"
                )
                print(
                    f"  Lines now:       {len(after.splitlines()):,}"
                )

                continue

            print("\nNo new history detected.")
            print("For this TEST, we stop here.")

            break

        # --------------------------------------------------
        # SCROLL UP
        # --------------------------------------------------

        container.evaluate(
            f"""
            el => {{
                el.scrollTop = Math.max(
                    0,
                    el.scrollTop - {SCROLL_STEP}
                );
            }}
            """
        )

        time.sleep(SCROLL_WAIT)

    print()
    print("=" * 70)
    print("                    TEST COMPLETE")
    print("=" * 70)

    final_text = container.inner_text()

    print(
        f"\nFinal visible characters: "
        f"{len(final_text):,}"
    )

    print(
        f"Final visible lines:      "
        f"{len(final_text.splitlines()):,}"
    )

    print(
        f"\nLive text file:"
        f"\n{ARCHIVE}"
    )

    print(
        f"\nProgress log:"
        f"\n{LOG}"
    )

    print(
        "\n⚠️ This test intentionally does NOT claim "
        "that the whole conversation has been recovered."
    )

    print(
        "We are testing the exact text-saving mechanism first."
    )

    input("\nPress ENTER to close Firefox...")

    context.close()
