CAESAR II Neutral File Generator (Hybrid GitHub Pages Edition)

This package contains the ultimate, unified web tool for generating CAESAR II files.

HOW IT WORKS:
This single `index.html` file operates as a "Hybrid Tool":
1. Serverless CSV Mode: If a user uploads a `.csv` Middle-Layer template, the Python formatting engine runs 100% locally in their browser tab via WebAssembly (Pyodide). No backend server is required!
2. Local ACCDB Mode: MS Access binary `.accdb` files cannot be processed via WebAssembly directly, and standard browser parsing has known limitations. If a user uploads an `.accdb` file and the browser-based parse fails, the webpage will gracefully fallback and attempt to forward the request to `http://127.0.0.1:8000/convert_accdb` (configurable in `ACCESS_IMPORT_CONFIG`). The user must be running the backend (e.g. `python3 app.py`) on their local machine for this to succeed.

HOW TO HOST:
1. Push all these files to your public GitHub repository.
2. Enable "GitHub Pages" pointing to the main branch.
3. Users can navigate to your GitHub Pages URL to process `.csv` files serverless instantly.
4. If users want to process `.accdb` files via your UI, they just need to download `app.py`, run `pip install -r requirements.txt`, and start the `python3 app.py` backend on their own machine while keeping your GitHub Pages tab open.

Enjoy!
