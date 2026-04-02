
from flask import Flask, request, send_file, render_template_string
import os
import full_exporter_final

app = Flask(__name__)

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _read_html():
    html_path = os.path.join(_BASE_DIR, 'optimizer_settings.py')
    with open(html_path, 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/')
def index():
    return _read_html()

@app.route('/benchmark_data.js')
def benchmark_data_js():
    return send_file(os.path.join(_BASE_DIR, 'benchmark_data.js'), mimetype='application/javascript')

@app.route('/format_funcs.js')
def format_funcs_js():
    return send_file(os.path.join(_BASE_DIR, 'format_funcs.js'), mimetype='application/javascript')

@app.route('/generate_final.js')
def generate_final_js():
    return send_file(os.path.join(_BASE_DIR, 'generate_final.js'), mimetype='application/javascript')

@app.route('/dist/bundle.js')
def bundle_js():
    return send_file(os.path.join(_BASE_DIR, 'dist', 'bundle.js'), mimetype='application/javascript')

@app.route('/template')
def download_template():
    return send_file('template.csv', as_attachment=True, download_name='template.csv')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
        
    os.makedirs("/tmp/uploads", exist_ok=True)
    db_path = os.path.join("/tmp/uploads", file.filename)
    file.save(db_path)
    
    out_file = os.path.join("/tmp/uploads", "final.cii")
    try:
        full_exporter_final.generate_final(db_path, "benchmark.cii", out_file)
        return send_file(out_file, as_attachment=True, download_name="final.cii")
    except Exception as e:
        return f"Error processing file: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
