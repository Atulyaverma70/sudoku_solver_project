from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from sudoku_solver import solve_sudoku
from ocr_processing import extract_sudoku_grid
import os

# Create Flask app with correct folder paths
app = Flask(
    __name__,
    static_folder='static',        # For CSS, JS, images
    template_folder='templates'    # For HTML files
)

# Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*"}})

# Folder for uploaded images
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Home page
@app.route('/')
def home():
    return render_template('index.html')


# Solve Sudoku API
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


# Upload Sudoku image and extract grid API
@app.route('/upload', methods=['POST'])
def api_upload():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename.strip() == '':
            return jsonify({'error': 'Empty file'}), 400

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp.jpg')
        file.save(file_path)

        grid = extract_sudoku_grid(file_path)
        if not grid or len(grid) != 9 or any(len(row) != 9 for row in grid):
            return jsonify({'error': 'OCR failed to detect Sudoku grid'}), 400

        return jsonify({'grid': grid})

    except Exception as e:
        return jsonify({'error': f'Upload error: {str(e)}'}), 500


# Run Flask app
if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)

