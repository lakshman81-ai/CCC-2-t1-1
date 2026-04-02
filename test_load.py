from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8080/index.html")
        page.wait_for_timeout(2000)
        logs = []
        page.on("console", lambda msg: logs.append(msg.text))
        page.wait_for_timeout(3000)
        print("Console logs:", logs)
        browser.close()

if __name__ == "__main__":
    test()
