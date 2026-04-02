from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8080/index.html")

        page.wait_for_selector("#loading", state="hidden", timeout=15000)

        # Test Logic 1
        page.click("#tab-btn-logic1")
        with open("dummy.csv", "w") as f:
            f.write("FROM_NODE,TO_NODE\n10,20\n")
        page.locator("#l1-upload").set_input_files("dummy.csv")
        page.wait_for_timeout(500)
        logs = []
        page.on("console", lambda msg: logs.append(msg.text))
        page.locator("#l1-btn-convert").click()
        page.wait_for_timeout(1000)
        print("Logic 1 Convert Logs:", logs)

        # Test Logic 4
        logs.clear()
        page.click("#tab-btn-logic4")
        page.locator("#l4-upload").set_input_files("dummy.csv")
        page.wait_for_timeout(500)
        page.locator("#l4-btn-convert").click()
        page.wait_for_timeout(1000)
        print("Logic 4 Convert Logs:", logs)

        browser.close()

if __name__ == "__main__":
    test()
