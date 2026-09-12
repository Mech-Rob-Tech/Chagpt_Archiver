from playwright.sync_api import sync_playwright
import os

URL="https://chatgpt.com/g/g-p-6a94243042c48191809ddc8971ec785d/c/6a94245e-0390-83e8-81e8-f531e1d5251f"
TARGET="Yes. I reviewed the uploaded output and checked the current NIST position as well"
PROFILE="/home/msp-fsp321/chatgpt_archive/firefox_profile"
OUTPUT="/home/msp-fsp321/chatgpt_archive/output/copy_test/TARGET_RESPONSE_TEST.txt"

with sync_playwright() as p:
    print("Opening logged-in Firefox profile...")
    context=p.firefox.launch_persistent_context(
        user_data_dir=PROFILE,
        headless=False
    )

    page=context.pages[0] if context.pages else context.new_page()

    print("Opening target conversation...")
    page.goto(URL,wait_until="domcontentloaded",timeout=60000)
    page.wait_for_timeout(7000)

    print("URL:",page.url)

    if "auth/login" in page.url:
        print("ERROR: PROFILE IS NOT LOGGED IN")
        input("Press ENTER...")
        context.close()
        raise SystemExit

    print("Logged in.")

    target=page.get_by_text(TARGET,exact=False).first
    target.wait_for(state="attached",timeout=30000)
    print("TARGET FOUND")

    container=target
    copy_button=None

    for depth in range(10):
        buttons=container.locator(
            'button[data-testid="copy-turn-action-button"][aria-label="Copy response"]'
        )
        count=buttons.count()
        print(f"depth={depth} | copy buttons={count}")

        if count==1:
            copy_button=buttons.first
            break

        container=container.locator("..")

    if copy_button is None:
        raise RuntimeError("Could not find unique Copy response button")

    print("CORRECT RESPONSE FOUND")

    text=container.inner_text()

    print("LENGTH:",len(text))
    print("LINES:",len(text.splitlines()))
    print("\n--- RESPONSE START ---\n")
    print(text[:3000])
    print("\n--- RESPONSE END ---")

    os.makedirs(os.path.dirname(OUTPUT),exist_ok=True)

    with open(OUTPUT,"w",encoding="utf-8") as f:
        f.write(text)

    print("\nSAVED:",OUTPUT)
    print("TARGET PRESENT:",TARGET in text)

    input("\nPress ENTER to close...")
    context.close()
