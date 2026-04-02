from playwright.sync_api import sync_playwright
import time

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8080/index.html")
        page.wait_for_selector("#loading", state="hidden", timeout=25000)

        print("Testing Logic 4:")
        page.click("#tab-btn-logic4")

        with open("dummy.accdb", "w") as f:
            f.write("dummy binary accdb content")

        page.locator("#l4-upload").set_input_files("dummy.accdb")

        # Wait for the diagnostic panel to appear since dummy.accdb is corrupted/not-an-accdb
        page.wait_for_selector("#diagnostics-panel:not(.hidden)", timeout=15000)

        text = page.locator("#diagnostics-content").text_content()
        print("Diagnostics text:", text[:300])

        page.screenshot(path="diagnostics_panel_test.png")
        print("Done")
        browser.close()

if __name__ == "__main__":
    test()
