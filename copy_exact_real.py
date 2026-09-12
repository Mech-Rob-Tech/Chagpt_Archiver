from playwright.sync_api import sync_playwright
from pathlib import Path
import subprocess
import time
import math

PROFILE = "/home/msp-fsp321/chatgpt_archive/firefox_profile"

CHAT_URL = (
    "https://chatgpt.com/g/g-p-6a94243042c48191809ddc8971ec785d/"
    "c/6a94245e-0390-83e8-81e8-f531e1d5251f"
)

OUT = Path(
    "/home/msp-fsp321/chatgpt_archive/output/copy_test"
)
OUT.mkdir(parents=True, exist_ok=True)

OUTPUT = OUT / "REAL_ASSISTANT_RESPONSE.txt"

TARGET = (
    "Yes. I reviewed the uploaded output and checked "
    "the current NIST position as well."
)


def clipboard():
    return subprocess.run(
        ["xclip", "-selection", "clipboard", "-o"],
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout


with sync_playwright() as p:

    print("=" * 70)
    print("       REAL ASSISTANT RESPONSE COPY TEST")
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

    # --------------------------------------------------
    # FIND THE ACTUAL TARGET TEXT
    # --------------------------------------------------

    target_text = page.get_by_text(
        TARGET,
        exact=False
    )

    if target_text.count() == 0:
        raise RuntimeError(
            "Target assistant text is not currently mounted."
        )

    target_text = target_text.first

    print(
        "\n✓ Target assistant text found"
    )

    # Get the actual target text position.
    target_box = target_text.bounding_box()

    if not target_box:
        raise RuntimeError(
            "Could not determine target text position."
        )

    target_x = target_box["x"]
    target_y = target_box["y"]
    target_bottom = (
        target_box["y"] +
        target_box["height"]
    )

    print(
        f"Target position: "
        f"x={target_x:.0f}, "
        f"y={target_y:.0f}, "
        f"bottom={target_bottom:.0f}"
    )

    # --------------------------------------------------
    # FIND ALL REAL "COPY MESSAGE" BUTTONS
    # --------------------------------------------------

    buttons = page.locator(
        'button[aria-label="Copy message"]'
    )

    count = buttons.count()

    print(
        f"\nCopy message buttons currently mounted: {count}"
    )

    if count == 0:
        raise RuntimeError(
            "No Copy message buttons found."
        )

    candidates = []

    for i in range(count):

        button = buttons.nth(i)

        try:
            box = button.bounding_box()

            if not box:
                continue

            bx = box["x"]
            by = box["y"]

            # We want a Copy button below the target text.
            if by < target_bottom:
                continue

            vertical_distance = by - target_bottom

            horizontal_distance = abs(
                bx - target_x
            )

            # Prefer buttons reasonably aligned with
            # the target response.
            score = (
                vertical_distance
                + horizontal_distance * 0.15
            )

            candidates.append(
                (
                    score,
                    i,
                    bx,
                    by,
                    vertical_distance,
                    horizontal_distance
                )
            )

        except Exception:
            pass

    print("\nCANDIDATE COPY BUTTONS")
    print("-" * 70)

    for item in sorted(candidates):

        score, i, bx, by, vd, hd = item

        print(
            f"button={i:02d} "
            f"x={bx:.0f} "
            f"y={by:.0f} "
            f"vertical_distance={vd:.0f} "
            f"horizontal_distance={hd:.0f} "
            f"score={score:.0f}"
        )

    if not candidates:
        raise RuntimeError(
            "No Copy button found below target response."
        )

    # --------------------------------------------------
    # SELECT CLOSEST COPY BUTTON BELOW TARGET
    # --------------------------------------------------

    candidates.sort()

    (
        score,
        button_index,
        bx,
        by,
        vd,
        hd
    ) = candidates[0]

    target_button = buttons.nth(
        button_index
    )

    print()
    print(
        f"✓ Selected Copy button #{button_index}"
    )

    print(
        f"  distance below target: {vd:.0f}px"
    )

    # --------------------------------------------------
    # CLEAR CLIPBOARD
    # --------------------------------------------------

    sentinel = "__ECDAT_CLIPBOARD_SENTINEL__"

    subprocess.run(
        ["xclip", "-selection", "clipboard"],
        input=sentinel,
        text=True,
        check=True
    )

    # --------------------------------------------------
    # CLICK
    # --------------------------------------------------

    print(
        "\nClicking selected Copy message button..."
    )

    target_button.scroll_into_view_if_needed()

    target_button.click(
        force=True
    )

    # --------------------------------------------------
    # WAIT FOR CLIPBOARD CHANGE
    # --------------------------------------------------

    copied = sentinel

    for _ in range(20):

        time.sleep(0.25)

        copied = clipboard()

        if copied != sentinel:
            break

    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------

    OUTPUT.write_text(
        copied,
        encoding="utf-8"
    )

    print("\n" + "=" * 70)
    print("RESULT")
    print("=" * 70)

    print(
        f"Characters: {len(copied):,}"
    )

    print(
        f"Lines:      {len(copied.splitlines()):,}"
    )

    print(
        f"File:       {OUTPUT}"
    )

    # --------------------------------------------------
    # REAL VERIFICATION
    # --------------------------------------------------

    first_500 = copied[:500].lower()

    if TARGET.lower() in first_500:

        print(
            "\n✅ CORRECT ASSISTANT RESPONSE COPIED"
        )

    else:

        print(
            "\n❌ WRONG RESPONSE COPIED"
        )

    print("\nFIRST 20 LINES")
    print("-" * 70)

    print(
        "\n".join(
            copied.splitlines()[:20]
        )
    )

    print("\nLAST 10 LINES")
    print("-" * 70)

    print(
        "\n".join(
            copied.splitlines()[-10:]
        )
    )

    input(
        "\nPress ENTER to close Firefox..."
    )

    context.close()
