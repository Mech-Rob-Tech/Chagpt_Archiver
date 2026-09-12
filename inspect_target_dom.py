from playwright.sync_api import sync_playwright
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

with sync_playwright() as p:

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
    time.sleep(10)

    # Find exact target text.
    target = page.get_by_text(
        TARGET,
        exact=False
    )

    print(
        f"\nTarget matches: {target.count()}"
    )

    if target.count() == 0:
        raise RuntimeError(
            "Target text not found."
        )

    target = target.first

    # IMPORTANT:
    # Put the target response ON SCREEN first.
    target.scroll_into_view_if_needed()

    time.sleep(2)

    print(
        "\n✓ Target scrolled into view."
    )

    box = target.bounding_box()

    print(
        f"Target box: {box}"
    )

    # --------------------------------------------------
    # WALK REAL DOM ANCESTORS
    # --------------------------------------------------

    result = target.evaluate("""
    el => {

        const rows = [];

        let node = el;

        for (let depth = 0; depth < 18 && node; depth++, node=node.parentElement) {

            const copies = node.querySelectorAll(
                'button[aria-label="Copy message"]'
            );

            const allButtons = node.querySelectorAll('button');

            rows.push({

                depth,

                tag: node.tagName,

                id: node.id || "",

                classes: (
                    typeof node.className === "string"
                    ? node.className.substring(0, 300)
                    : ""
                ),

                testid:
                    node.getAttribute("data-testid") || "",

                role:
                    node.getAttribute("role") || "",

                author:
                    node.getAttribute(
                        "data-message-author-role"
                    ) || "",

                turn:
                    node.getAttribute(
                        "data-turn-id"
                    ) || "",

                copy_count:
                    copies.length,

                button_count:
                    allButtons.length,

                text_length:
                    (node.innerText || "").length,

                text_start:
                    (node.innerText || "")
                        .substring(0, 300)

            });

        }

        return rows;
    }
    """)

    print("\n")
    print("=" * 90)
    print("TARGET DOM ANCESTOR STRUCTURE")
    print("=" * 90)

    for r in result:

        print(
            f"\nDEPTH {r['depth']}"
        )

        print(
            f"TAG       : {r['tag']}"
        )

        print(
            f"ID        : {r['id']}"
        )

        print(
            f"TESTID    : {r['testid']}"
        )

        print(
            f"ROLE      : {r['role']}"
        )

        print(
            f"AUTHOR    : {r['author']}"
        )

        print(
            f"TURN ID   : {r['turn']}"
        )

        print(
            f"COPY BTN  : {r['copy_count']}"
        )

        print(
            f"BUTTONS   : {r['button_count']}"
        )

        print(
            f"TEXT LEN  : {r['text_length']}"
        )

        print(
            f"TEXT      : {r['text_start'][:150]!r}"
        )

    # --------------------------------------------------
    # NOW SHOW ALL COPY BUTTONS INSIDE THE TARGET
    # ANCESTOR CANDIDATES
    # --------------------------------------------------

    print("\n")
    print("=" * 90)
    print("VISIBLE COPY BUTTONS AFTER TARGET IS SCROLLED INTO VIEW")
    print("=" * 90)

    buttons = page.locator(
        'button[aria-label="Copy message"]'
    )

    print(
        f"\nTotal Copy buttons: {buttons.count()}"
    )

    for i in range(buttons.count()):

        b = buttons.nth(i)

        try:

            bb = b.bounding_box()

            if not bb:
                continue

            print(
                f"\nBUTTON {i}"
            )

            print(
                f"position: "
                f"x={bb['x']:.0f} "
                f"y={bb['y']:.0f}"
            )

            print(
                "testid:",
                b.get_attribute("data-testid")
            )

            print(
                "aria:",
                b.get_attribute("aria-label")
            )

            # Print immediate useful ancestor information.
            info = b.evaluate("""
            el => {

                let rows = [];

                let n = el;

                for (
                    let d = 0;
                    d < 10 && n;
                    d++, n=n.parentElement
                ) {

                    rows.push({

                        depth: d,

                        tag: n.tagName,

                        testid:
                            n.getAttribute("data-testid") || "",

                        role:
                            n.getAttribute("role") || "",

                        author:
                            n.getAttribute(
                                "data-message-author-role"
                            ) || "",

                        turn:
                            n.getAttribute(
                                "data-turn-id"
                            ) || "",

                        text_length:
                            (n.innerText || "").length

                    });

                }

                return rows;
            }
            """)

            for x in info:

                print(
                    "  "
                    f"d{x['depth']} "
                    f"{x['tag']} "
                    f"testid={x['testid']!r} "
                    f"author={x['author']!r} "
                    f"turn={x['turn']!r} "
                    f"text={x['text_length']}"
                )

        except Exception as e:

            print(
                "ERROR:",
                e
            )

    print("\n")
    print("=" * 90)
    print("NO BUTTON WAS CLICKED")
    print("=" * 90)

    input(
        "\nPress ENTER to close Firefox..."
    )

    context.close()
