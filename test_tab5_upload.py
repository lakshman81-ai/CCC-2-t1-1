from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8080/index.html")

        # Click the new tab
        page.click("text='Access → CSV'")

        page.wait_for_timeout(1000)
        page.screenshot(path="test_tab5_ui.png")
        print("Done")
        browser.close()

if __name__ == "__main__":
    test()
