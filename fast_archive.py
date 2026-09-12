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

ARCHIVE = OUT / "conversation_FULL.txt"
SNAPSHOT_DIR = OUT / "raw_snapshots"
SNAPSHOT_DIR.mkdir(exist_ok=True)

# ============================================================
# SPEED SETTINGS
# ============================================================

SCROLL_STEP = 3000
FAST_WAIT = 0.25

# Only wait longer when ChatGPT reaches the currently
# loaded oldest section.
HISTORY_WAIT = 2.0

# Save cumulative archive every N chunks.
CHECKPOINT_EVERY = 5


def stats(text):
    return len(text), len(text.splitlines())


def find_new_top(old_text, new_text):
    """
    We moved UP.

    OLD:
        older-ish
        common
        common
        current

    NEW:
        NEWER OLD CONTENT
        older-ish
        common
        common

    We want only the newly exposed top portion.

    We intentionally use a simple suffix/prefix overlap.
    No complicated message reconstruction.
    """

    if not old_text:
        return new_text

    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    if not old_lines or not new_lines:
        return new_text

    max_overlap = min(len(old_lines), len(new_lines), 5000)

    # Find largest overlap:
    # end of NEW == beginning of OLD
    for k in range(max_overlap, 0, -1):

        if new_lines[-k:] == old_lines[:k]:
            return "\n".join(new_lines[:-k])

    # If exact overlap isn't found, don't lose data.
    # Save the new snapshot as-is.
    return new_text


def append_chunk(chunk):

    chunk = chunk.strip()

    if not chunk:
        return 0, 0

    # Blank line between extracted chunks.
    with ARCHIVE.open("a", encoding="utf-8") as f:
        f.write("\n\n")
        f.write(chunk)
        f.write("\n")

    chars, lines = stats(chunk)

    return chars, lines


with sync_playwright() as p:

    print("=" * 72)
    print("       FAST CHATGPT FULL CONVERSATION ARCHIVER")
    print("=" * 72)

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

    time.sleep(8)

    container = page.locator(
        "div.group\\/scroll-root"
    ).first

    container.wait_for(
        state="visible",
        timeout=60000
    )

    print("✓ Conversation container found")

    # Start at newest end.
    container.evaluate(
        "el => el.scrollTop = el.scrollHeight"
    )

    time.sleep(2)

    # Start fresh archive.
    ARCHIVE.write_text("", encoding="utf-8")

    previous_text = ""

    total_chars = 0
    total_lines = 0

    chunk_number = 0
    history_loads = 0
    no_change_count = 0

    print("\nStarting FAST extraction...\n")

    while True:

        # ----------------------------------------------------
        # Capture current visible/rendered conversation
        # ----------------------------------------------------

        current_text = container.inner_text()

        # Save raw snapshot for safety.
        chunk_number += 1

        raw_file = (
            SNAPSHOT_DIR
            / f"snapshot_{chunk_number:05d}.txt"
        )

        raw_file.write_text(
            current_text,
            encoding="utf-8"
        )

        # ----------------------------------------------------
        # Determine newly exposed older text
        # ----------------------------------------------------

        new_chunk = find_new_top(
            previous_text,
            current_text
        )

        added_chars, added_lines = append_chunk(
            new_chunk
        )

        total_chars += added_chars
        total_lines += added_lines

        state = container.evaluate("""
            el => ({
                scrollTop: el.scrollTop,
                scrollHeight: el.scrollHeight,
                clientHeight: el.clientHeight
            })
        """)

        print(
            f"Chunk {chunk_number:05d} | "
            f"Added: {added_chars:>7,} chars | "
            f"{added_lines:>5,} lines | "
            f"TOTAL: {total_chars:>10,} chars | "
            f"{total_lines:>7,} lines | "
            f"Scroll: {state['scrollTop']:.0f}"
        )

        previous_text = current_text

        # ----------------------------------------------------
        # Are we at the oldest currently loaded section?
        # ----------------------------------------------------

        if state["scrollTop"] <= 5:

            print(
                "\n  ↑ Current loaded top reached."
            )

            print(
                "  ⏳ Waiting for older ChatGPT history..."
            )

            before_text = container.inner_text()

            before_height = container.evaluate(
                "el => el.scrollHeight"
            )

            before_scroll = container.evaluate(
                "el => el.scrollTop"
            )

            time.sleep(HISTORY_WAIT)

            after_text = container.inner_text()

            after_height = container.evaluate(
                "el => el.scrollHeight"
            )

            after_scroll = container.evaluate(
                "el => el.scrollTop"
            )

            if (
                after_text != before_text
                or after_height != before_height
                or after_scroll != before_scroll
            ):

                history_loads += 1
                no_change_count = 0

                print(
                    f"  ✓ Older history loaded "
                    f"({history_loads})"
                )

                print(
                    f"  New window: "
                    f"{len(after_text):,} chars | "
                    f"{len(after_text.splitlines()):,} lines"
                )

                continue

            # ------------------------------------------------
            # One failed check does NOT mean we're finished.
            # Give ChatGPT another chance.
            # ------------------------------------------------

            no_change_count += 1

            print(
                f"  ⚠ No new history "
                f"({no_change_count}/3)"
            )

            if no_change_count < 3:

                time.sleep(HISTORY_WAIT)

                continue

            print("\n" + "=" * 72)
            print(" POSSIBLE TRUE BEGINNING REACHED")
            print("=" * 72)

            break

        # ----------------------------------------------------
        # FAST upward movement
        # ----------------------------------------------------

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

        time.sleep(FAST_WAIT)

    # --------------------------------------------------------
    # Final checkpoint
    # --------------------------------------------------------

    final_text = container.inner_text()

    print("\n")
    print("=" * 72)
    print("                  ARCHIVE FINISHED")
    print("=" * 72)

    print(
        f"\nTotal archived characters: {total_chars:,}"
    )

    print(
        f"Total archived lines:      {total_lines:,}"
    )

    print(
        f"History loads detected:    {history_loads:,}"
    )

    print(
        f"Raw snapshots:             {chunk_number:,}"
    )

    print(
        f"\nFULL FILE:"
    )

    print(
        ARCHIVE
    )

    print(
        f"\nRAW BACKUPS:"
    )

    print(
        SNAPSHOT_DIR
    )

    print(
        "\nThe archive contains only conversation text."
    )

    print(
        "No Pass numbers are written into the TXT."
    )

    input("\nPress ENTER to close Firefox...")

    context.close()
