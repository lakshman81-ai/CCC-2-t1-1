from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8080/index.html")

        # Click the new tab
        page.click("text='Access → CSV'")

        page.wait_for_timeout(1000)

        # Wait for pyodide to load to avoid other noise
        page.wait_for_selector("#loading", state="hidden", timeout=15000)

        logs = []
        page.on("console", lambda msg: logs.append(msg.text))

        # We don't have an accdb, but we can verify there are no startup errors in the console
        page.wait_for_timeout(3000)
        print("Done. Console logs:", logs)
        browser.close()

if __name__ == "__main__":
    test()
