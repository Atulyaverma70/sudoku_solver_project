from flask import Flask, render_template, request, jsonify
import os
from sudoku_solver import solve_sudoku
from ocr_processing import extract_sudoku_grid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def solve():
    data = request.get_json()
    grid = data.get('grid')
    if not grid:
        return jsonify({"error": "No grid provided"}), 400

    if solve_sudoku(grid):
        return jsonify({"solved_grid": grid})
    else:
        return jsonify({"error": "Unable to solve Sudoku"}), 400

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    try:
        grid = extract_sudoku_grid(file_path)
        return jsonify({"grid": grid})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
