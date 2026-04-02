from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8080/index.html")

        # Wait for pyodide to load
        page.wait_for_selector("#loading", state="hidden", timeout=15000)

        # Switch to Logic 4
        page.click("#tab-btn-logic4")

        # Upload the dummy CSV file
        with open("dummy.csv", "w") as f:
            f.write("FROM_NODE,TO_NODE\n10,20\n")

        page.locator("#l4-upload").set_input_files("dummy.csv")
        page.wait_for_timeout(1000)

        logs = []
        page.on("console", lambda msg: logs.append(msg.text))

        # Click convert
        page.locator("#l4-btn-convert").click()
        page.wait_for_timeout(3000)

        print("Done. Console logs:", logs)
        browser.close()

if __name__ == "__main__":
    test()
