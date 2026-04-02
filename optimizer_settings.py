<!DOCTYPE html>
<html>
<head>
    <title>CAESAR II .ACCDB / .CSV to .CII Exporter — Logic 3</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 2rem; max-width: 600px; margin: 0 auto; background: #f5f5f5; }
        .card { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1 { color: #333; margin-top: 0; }
        input[type="file"] { margin-bottom: 1rem; width: 100%; }
        button, input[type="submit"] { background: #007bff; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; margin-right: 1rem; font-size: 14px;}
        button:hover, input[type="submit"]:hover { background: #0056b3; }
        a.btn { background: #28a745; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; text-decoration: none; font-size: 14px;}
        a.btn:hover { background: #218838; }
        .actions { margin-top: 1rem; display: flex; align-items: center; }
        #message { margin-top: 1rem; color: #dc3545; font-weight: bold; }
    </style>
    <!-- mdb-reader for ACCDB parsing (CDN, no server required) -->
    <script type="module">
        import Database from "https://cdn.jsdelivr.net/npm/mdb-reader/+esm";
        import { Buffer } from "https://cdn.jsdelivr.net/npm/buffer/+esm";
        window.mdbReader = { Database: Database };
        window.Buffer = Buffer;
    </script>
    <script src="benchmark_data.js"></script>
    <script src="format_funcs.js"></script>
    <script src="generate_final.js"></script>
</head>
<body>
    <div class="card">
        <h1>Logic 3 — Upload MS Access DB or CSV</h1>
        <p>Select your <b>.ACCDB</b> database or minimal <b>.CSV</b> file to generate the CAESAR II <b>.CII</b> neutral file.</p>
        <p>Missing advanced properties will be automatically calculated via standard code using <code>-1.0101</code> injection.</p>

        <form id="uploadForm">
            <input type="file" id="fileInput" name="file" accept=".accdb,.csv" required>
            <div class="actions">
                <button type="submit">Convert to .CII</button>
                <a href="template.csv" class="btn" download>Download Minimal CSV Template</a>
            </div>
            <div id="message"></div>
            <pre id="logScreen" style="margin-top: 1rem; background: #222; color: #0f0; padding: 1rem; border-radius: 4px; display: none; overflow-x: auto; font-size: 12px;"></pre>
        </form>
    </div>

    <script>
        function parseCSV(text) {
            const lines = text.split(/\r?\n/).filter(l => l.trim() !== '');
            if (lines.length < 2) return [];

            const headers = lines[0].split(',').map(h => h.trim());
            const data = [];

            for (let i = 1; i < lines.length; i++) {
                const row = lines[i].split(',').map(c => c.trim());
                const obj = {};
                for (let j = 0; j < headers.length; j++) {
                    obj[headers[j]] = row[j] !== undefined ? row[j] : "";
                }
                data.push(obj);
            }
            return data;
        }

        document.getElementById('uploadForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const logScreen = document.getElementById('logScreen');
            if (logScreen) {
                logScreen.style.display = 'none';
                logScreen.textContent = '';
            }

            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            const msg = document.getElementById('message');

            if (!file) return;

            if (file.name.toLowerCase().endsWith('.accdb')) {
                msg.textContent = "Processing ACCDB...";
                msg.style.color = "#007bff";

                const reader = new FileReader();
                reader.onload = async function(e) {
                    try {
                        const buffer = e.target.result;

                        // Wait for mdb-reader CDN module to load
                        if (!window.mdbReader || !window.Buffer) {
                            throw new Error("mdb-reader library not yet loaded. Please wait a moment and try again.");
                        }

                        const { Database } = window.mdbReader;
                        let db;
                        try {
                            db = new Database(window.Buffer.from(buffer));
                        } catch (parseErr) {
                            logScreen.style.display = 'block';
                            logScreen.textContent = "FATAL ERROR PARSING .ACCDB:\n" + parseErr.message +
                                "\n\nThe browser-side mdb-reader library could not parse this Access database." +
                                "\n\nPLEASE USE THE MINIMAL CSV WORKFLOW INSTEAD:\n" +
                                "1. Download the Minimal CSV Template.\n" +
                                "2. Fill in FROM_NODE, TO_NODE, and DELTA geometry.\n" +
                                "3. Upload the CSV to auto-calculate defaults.";
                            msg.textContent = "Error processing ACCDB. See log below.";
                            msg.style.color = "#dc3545";
                            return;
                        }

                        const tables = db.getTableNames();
                        console.log("Tables found in ACCDB:", tables);

                        const tableName = "INPUT_BASIC_ELEMENT_DATA";
                        let tableData;
                        try {
                            const table = db.getTable(tableName);
                            tableData = table.getData();
                            console.log("Table rows:", tableData.length);
                        } catch (tableErr) {
                            throw new Error("Failed to read table '" + tableName + "': " + tableErr.message);
                        }

                        if (!tableData || tableData.length === 0) {
                            throw new Error("Table '" + tableName + "' is empty or could not be read.");
                        }

                        const finalCiiText = Logic3_generateFinal(tableData, Logic3_BENCHMARK_BLOCKS);

                        const blob = new Blob([finalCiiText], { type: 'text/plain' });
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'final.cii';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        window.URL.revokeObjectURL(url);

                        msg.textContent = "Conversion successful! Downloading final.cii...";
                        msg.style.color = "#28a745";
                    } catch (err) {
                        msg.textContent = "Error processing ACCDB: " + err.message;
                        msg.style.color = "#dc3545";
                        console.error(err);
                    }
                };
                reader.readAsArrayBuffer(file);

            } else if (file.name.toLowerCase().endsWith('.csv')) {
                msg.textContent = "Processing CSV...";
                msg.style.color = "#007bff";

                const reader = new FileReader();
                reader.onload = function(evt) {
                    try {
                        const csvText = evt.target.result;
                        const rows = parseCSV(csvText);

                        const finalCiiContent = Logic3_generateFinal(rows, Logic3_BENCHMARK_BLOCKS);

                        const blob = new Blob([finalCiiContent], { type: 'text/plain' });
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.style.display = 'none';
                        a.href = url;
                        a.download = 'final.cii';
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);

                        msg.textContent = "Conversion successful! Downloading final.cii...";
                        msg.style.color = "#28a745";
                    } catch (err) {
                        msg.textContent = "Error processing CSV: " + err.message;
                        msg.style.color = "#dc3545";
                    }
                };
                reader.readAsText(file);
            }
        });
    </script>
</body>
</html>
