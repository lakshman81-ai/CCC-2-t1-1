from playwright.sync_api import sync_playwright
import time
import os

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8080/index.html")

        # Wait for pyodide to load
        page.wait_for_selector("#loading", state="hidden", timeout=25000)

        logs = []
        page.on("console", lambda msg: logs.append(msg.text))
        page.on("pageerror", lambda exc: logs.append(f"PAGE ERROR: {exc}"))

        def run_logic(logic_id, tab_id, btn_id, upload_id):
            print(f"Benchmarking {logic_id} on SAMPLE2.ACCDB...")
            logs.clear()
            page.click(f"#{tab_id}")
            page.wait_for_timeout(500)

            # The input file is "SAMPLE2.ACCDB"
            page.locator(f"#{upload_id}").set_input_files("SAMPLE2.ACCDB")

            # Wait for file to process
            page.wait_for_timeout(8000) # ACCDB parsing takes a few seconds

            page.locator(f"#{btn_id}").click()
            page.wait_for_timeout(5000)

            print(f"{logic_id} Logs:")
            for log in logs:
                print("  ", log)
            print("-" * 40)

        run_logic("Logic 1", "tab-btn-logic1", "l1-btn-convert", "l1-upload")
        run_logic("Logic 2", "tab-btn-logic2", "l2-btn-convert", "l2-upload")
        run_logic("Logic 4", "tab-btn-logic4", "l4-btn-convert", "l4-upload")

        browser.close()

if __name__ == "__main__":
    if not os.path.exists("SAMPLE2.ACCDB"):
        print("SAMPLE2.ACCDB not found!")
    else:
        test()
