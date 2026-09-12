from playwright.sync_api import sync_playwright
from pathlib import Path
import subprocess
import time

PROFILE = "/home/msp-fsp321/chatgpt_archive/firefox_profile"

CHAT_URL = (
    "https://chatgpt.com/g/g-p-6a94243042c48191809ddc8971ec785d/"
    "c/6a94245e-0390-83e8-81e8-f531e1d5251f"
)

TARGET = (
    "Yes. I reviewed the uploaded output and checked "
    "the current NIST position as well."
)

OUT = Path(
    "/home/msp-fsp321/chatgpt_archive/output/copy_test"
)

OUT.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT = OUT / "ACCESSIBILITY_COPY_TEST.txt"


def clipboard():
    return subprocess.check_output(
        ["xclip", "-selection", "clipboard", "-o"],
        text=True,
        errors="replace"
    )


with sync_playwright() as p:

    print("=" * 70)
    print("EXACT ASSISTANT RESPONSE — ACCESSIBILITY TEST")
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

    print("\nOpening ChatGPT...")

    page.goto(
        CHAT_URL,
        wait_until="domcontentloaded",
        timeout=120000
    )

    print("Waiting for ChatGPT...")
    time.sleep(10)

    # --------------------------------------------------
    # FIND TARGET TEXT
    # --------------------------------------------------

    target = page.get_by_text(
        TARGET,
        exact=False
    )

    print(
        f"\nTarget matches: {target.count()}"
    )

    if target.count() == 0:
        raise RuntimeError(
            "Target response text was not found."
        )

    target = target.first

    # Bring target into the viewport.
    target.scroll_into_view_if_needed()

    time.sleep(2)

    print(
        "✓ Target response located."
    )

    # --------------------------------------------------
    # WALK UP DOM AND FIND RESPONSE ACTIONS
    # --------------------------------------------------

    print("\nSearching ancestor hierarchy...")

    ancestor = target

    found = None

    for depth in range(20):

        buttons = ancestor.get_by_role(
            "button",
            name="Copy response",
            exact=True
        )

        count = buttons.count()

        text = ""

        try:
            text = ancestor.inner_text()
        except:
            pass

        print(
            f"depth={depth:02d} "
            f"copy_buttons={count} "
            f"text={len(text)}"
        )

        if count == 1:

            found = ancestor

            print(
                f"\n✓ FOUND UNIQUE RESPONSE CONTAINER "
                f"at depth {depth}"
            )

            break

        ancestor = ancestor.locator("..")

    if found is None:

        raise RuntimeError(
            "\nCould not find a unique "
            "'Copy response' button belonging "
            "to the target response."
        )

    # --------------------------------------------------
    # GET THE COPY RESPONSE BUTTON
    # --------------------------------------------------

    copy_button = found.get_by_role(
        "button",
        name="Copy response",
        exact=True
    )

    print(
        "\nCopy response buttons inside "
        f"target container: {copy_button.count()}"
    )

    if copy_button.count() != 1:

        raise RuntimeError(
            "Expected exactly ONE Copy response "
            "button inside target response."
        )

    # --------------------------------------------------
    # SHOW CONTAINER INFORMATION
    # --------------------------------------------------

    container_text = found.inner_text()

    print(
        "\nTarget response container:"
    )

    print("-" * 70)

    print(
        f"Characters: {len(container_text):,}"
    )

    print(
        f"Lines:      {len(container_text.splitlines()):,}"
    )

    print(
        "\nFIRST 10 LINES:"
    )

    print(
        "\n".join(
            container_text.splitlines()[:10]
        )
    )

    print("-" * 70)

    # --------------------------------------------------
    # CLEAR CLIPBOARD WITH SENTINEL
    # --------------------------------------------------

    sentinel = "__ECDAT_CLIPBOARD_SENTINEL__"

    subprocess.run(
        [
            "xclip",
            "-selection",
            "clipboard"
        ],
        input=sentinel,
        text=True,
        check=True
    )

    print(
        "\nClipboard cleared with sentinel."
    )

    # --------------------------------------------------
    # SCROLL TARGET INTO VIEW AGAIN
    # --------------------------------------------------

    copy_button.scroll_into_view_if_needed()

    time.sleep(1)

    print(
        "✓ Copy response button is in viewport."
    )

    # --------------------------------------------------
    # CLICK EXACT BUTTON
    # --------------------------------------------------

    print(
        "\nClicking EXACT 'Copy response' button..."
    )

    copy_button.click(force=True)
    time.sleep(1)

    # --------------------------------------------------
    # READ CLIPBOARD
    # --------------------------------------------------

    copied = clipboard()

    print("\n")
    print("=" * 70)
    print("RESULT")
    print("=" * 70)

    print(
        f"Characters: {len(copied):,}"
    )

    print(
        f"Lines:      {len(copied.splitlines()):,}"
    )

    OUTPUT.write_text(
        copied,
        encoding="utf-8"
    )

    print(
        f"File: {OUTPUT}"
    )

    # --------------------------------------------------
    # VALIDATE SENTINEL
    # --------------------------------------------------

    if copied == sentinel:

        print(
            "\n❌ COPY FAILED"
        )

    elif not copied.strip():

        print(
            "\n❌ CLIPBOARD EMPTY"
        )

    elif TARGET not in copied:

        print(
            "\n❌ WRONG RESPONSE COPIED"
        )

    else:

        print(
            "\n✅ CORRECT ASSISTANT RESPONSE COPIED"
        )

    print("\nFIRST 15 LINES:")
    print("-" * 70)

    print(
        "\n".join(
            copied.splitlines()[:15]
        )
    )

    print("\nLAST 10 LINES:")
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
