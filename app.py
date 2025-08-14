from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from ocr_processing import extract_sudoku_grid
from sudoku_solver import solve_sudoku

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)  # Allow cross-origin requests

UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        grid = extract_sudoku_grid(filepath)
        return jsonify({"grid": grid})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/solve', methods=['POST'])
def solve():
    data = request.get_json()
    grid = data.get("grid")
    if not grid:
        return jsonify({"error": "Grid not provided"}), 400

    try:
        solved_grid = solve_sudoku(grid)
        return jsonify({"solved_grid": solved_grid})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
