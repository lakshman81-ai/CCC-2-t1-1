from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8080/index.html")
        page.wait_for_selector("#loading", state="hidden", timeout=15000)

        with open("dummy.csv", "w") as f:
            f.write("FROM_NODE,TO_NODE\n10,20\n")

        print("Testing Logic 4:")
        page.click("#tab-btn-logic4")
        page.locator("#l4-upload").set_input_files("dummy.csv")
        page.wait_for_timeout(1000)

        # Click the convert button and check if event listener works
        page.evaluate("""
            document.addEventListener('l4-convert', () => {
                console.log('EVENT l4-convert fired!');
            });
        """)

        logs = []
        page.on("console", lambda msg: logs.append(msg.text))
        page.locator("#l4-btn-convert").click()
        page.wait_for_timeout(2000)
        print("Console:", logs)

        browser.close()

if __name__ == "__main__":
    test()
