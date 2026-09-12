from playwright.sync_api import sync_playwright
import os, time, hashlib

URL = "https://chatgpt.com/g/g-p-6a94243042c48191809ddc8971ec785d/c/6a94245e-0390-83e8-81e8-f531e1d5251f"
PROFILE = "/home/msp-fsp321/chatgpt_archive/firefox_profile"
OUTPUT = "/home/msp-fsp321/chatgpt_archive/output/FINAL_CONVERSATION.txt"

def response_text(button):
    el = button
    for _ in range(10):
        el = el.locator("..")
        try:
            buttons = el.locator(
                'button[data-testid="copy-turn-action-button"][aria-label="Copy response"]'
            )
            if buttons.count() == 1:
                text = el.inner_text().strip()
                if len(text) > 50:
                    return text
        except:
            pass
    return None

def collect(page):
    results = []
    buttons = page.locator(
        'button[data-testid="copy-turn-action-button"][aria-label="Copy response"]'
    )
    count = buttons.count()

    for i in range(count):
        try:
            text = response_text(buttons.nth(i))
            if text:
                results.append(text)
        except Exception:
            pass

    return results

with sync_playwright() as p:
    print("Opening logged-in Firefox profile...")

    context = p.firefox.launch_persistent_context(
        user_data_dir=PROFILE,
        headless=False
    )

    page = context.pages[0] if context.pages else context.new_page()

    print("Opening conversation...")
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(7000)

    if "auth/login" in page.url:
        print("ERROR: NOT LOGGED IN")
        input("Press ENTER...")
        context.close()
        raise SystemExit

    print("Logged in.")
    print("Waiting for conversation...")
    page.wait_for_timeout(3000)

    # Find actual ChatGPT conversation scroll root
    root = page.locator("div.group\\/scroll-root").first

    if root.count() == 0:
        raise RuntimeError("Conversation scroll root not found")

    print("SCROLL ROOT FOUND")

    collected = {}
    no_new_rounds = 0
    round_no = 0

    while True:
        round_no += 1

        # Collect currently mounted assistant responses
        texts = collect(page)

        new_count = 0

        for text in texts:
            key = hashlib.sha256(text.encode("utf-8")).hexdigest()

            if key not in collected:
                collected[key] = text
                new_count += 1

        print(
            f"ROUND {round_no}: "
            f"visible={len(texts)} "
            f"new={new_count} "
            f"total={len(collected)}"
        )

        # Save continuously in chronological order
        ordered = list(reversed(collected.values()))

        os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

        with open(OUTPUT, "w", encoding="utf-8") as f:
            f.write("\n\n" + ("\n\n".join(ordered)) + "\n")

        # Scroll upward
        before = root.evaluate("(e) => e.scrollTop")

        root.evaluate(
            "(e) => { e.scrollTop = 0; e.dispatchEvent(new Event('scroll', {bubbles:true})); }"
        )

        page.wait_for_timeout(1800)

        after = root.evaluate("(e) => e.scrollTop")

        # Give lazy loading another moment if we reached the top
        if after == 0 or before == 0:
            page.wait_for_timeout(1800)

        # Collect again immediately after loading
        texts_after = collect(page)

        added_after = 0

        for text in texts_after:
            key = hashlib.sha256(text.encode("utf-8")).hexdigest()

            if key not in collected:
                collected[key] = text
                added_after += 1

        if added_after:
            no_new_rounds = 0
        elif new_count == 0:
            no_new_rounds += 1
        else:
            no_new_rounds = 0

        print(
            f"          after-scroll-new={added_after} "
            f"stalled={no_new_rounds}"
        )

        # Several consecutive rounds with nothing new means
        # we are probably at the beginning.
        if no_new_rounds >= 5:
            print("\nNO NEW RESPONSES AFTER 5 ROUNDS.")
            print("Assuming beginning of conversation reached.")
            break

    # Final save
    ordered = list(reversed(collected.values()))

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n\n".join(ordered))
        f.write("\n")

    total_chars = sum(len(x) for x in ordered)
    total_lines = sum(len(x.splitlines()) for x in ordered)

    print("\n========================================")
    print("ARCHIVE COMPLETE")
    print("========================================")
    print("Assistant responses:", len(ordered))
    print("Total characters:", total_chars)
    print("Total lines:", total_lines)
    print("Output:", OUTPUT)
    print("========================================")

    input("\nPress ENTER to close...")
    context.close()
