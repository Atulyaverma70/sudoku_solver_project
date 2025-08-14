# app.py
import os
import uuid
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from sudoku_solver import solve_sudoku
from ocr_processing import extract_sudoku_grid  # ensure file is named ocr_processing.py

# Create Flask app with correct folders
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app, resources={r"/*": {"origins": "*"}})

# Upload dir
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def api_solve():
    try:
        data = request.get_json()
        if not data or 'grid' not in data:
            return jsonify({'error': 'Invalid request'}), 400

        grid = data['grid']
        if len(grid) != 9 or any(len(row) != 9 for row in grid):
            return jsonify({'error': 'Invalid grid format'}), 400

        grid_copy = [row.copy() for row in grid]
        if solve_sudoku(grid_copy):
            return jsonify({'solved_grid': grid_copy})
        return jsonify({'error': 'No solution'}), 400
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/upload', methods=['POST'])
def api_upload():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        file = request.files['file']
        if not file or file.filename.strip() == '':
            return jsonify({'error': 'Empty file'}), 400

        # Use unique temp name to avoid race conditions
        fname = f"{uuid.uuid4().hex}.jpg"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
        file.save(file_path)

        try:
            grid = extract_sudoku_grid(file_path)
        finally:
            try:
                os.remove(file_path)
            except Exception:
                pass

        if not grid or len(grid) != 9 or any(len(row) != 9 for row in grid):
            return jsonify({'error': 'OCR failed to detect Sudoku grid'}), 400

        return jsonify({'grid': grid})
    except Exception as e:
        return jsonify({'error': f'Upload error: {str(e)}'}), 500

# No need for waitress; gunicorn runs this app: `app:app`
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
