import os
import cv2
import numpy as np
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from flask_cors import CORS

# --- Flask setup ---
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for all routes

# Upload folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB limit

# Allowed image extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


# --- Utils ---
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


import pytesseract
import cv2
import numpy as np

def extract_sudoku_from_image(image_path):
    # Load and preprocess
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    
    sudoku_contour = None
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            sudoku_contour = approx
            break

    if sudoku_contour is None:
        raise ValueError("Sudoku grid not found")

    # Warp perspective
    pts = sudoku_contour.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    side = 450
    dst = np.array([
        [0, 0],
        [side - 1, 0],
        [side - 1, side - 1],
        [0, side - 1]], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warp = cv2.warpPerspective(gray, M, (side, side))

    # Split into 9x9 cells
    cell_w = side // 9
    grid = []
    for y in range(9):
        row = []
        for x in range(9):
            cell = warp[y*cell_w:(y+1)*cell_w, x*cell_w:(x+1)*cell_w]
            cell = cv2.resize(cell, (28, 28))
            _, cell_thresh = cv2.threshold(cell, 128, 255, cv2.THRESH_BINARY_INV)
            text = pytesseract.image_to_string(cell_thresh, config='--psm 10 digits')
            try:
                val = int(text.strip()) if text.strip().isdigit() else 0
            except:
                val = 0
            row.append(val)
        grid.append(row)

    return grid

def solve_sudoku(grid):
    """
    Backtracking Sudoku solver.
    grid: 9x9 list of ints.
    Returns solved grid or None if no solution.
    """

    def is_valid(num, row, col):
        # Check row
        if num in grid[row]:
            return False
        # Check col
        if num in [grid[i][col] for i in range(9)]:
            return False
        # Check box
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(start_row, start_row + 3):
            for j in range(start_col, start_col + 3):
                if grid[i][j] == num:
                    return False
        return True

    def backtrack():
        for i in range(9):
            for j in range(9):
                if grid[i][j] == 0:
                    for num in range(1, 10):
                        if is_valid(num, i, j):
                            grid[i][j] = num
                            if backtrack():
                                return True
                            grid[i][j] = 0
                    return False
        return True

    if backtrack():
        return grid
    return None


# --- Routes ---
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        try:
            grid = extract_sudoku_from_image(filepath)
            return jsonify({"grid": grid})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid file type"}), 400


@app.route("/solve", methods=["POST"])
def solve():
    data = request.get_json(force=True)  # force=True to always parse JSON
    if not data or "grid" not in data:
        return jsonify({"error": "Missing Sudoku grid"}), 400

    grid = data["grid"]

    try:
        solved = solve_sudoku(grid)
        if solved:
            return jsonify({"solved_grid": solved})
        else:
            return jsonify({"error": "No solution found"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# --- Main entry ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
