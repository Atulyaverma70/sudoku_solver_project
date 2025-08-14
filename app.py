# app.py (keep the rest as-is)
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from sudoku_solver import solve_sudoku
from ocr_processing import extract_sudoku_grid  # ✅ correct name now
import os
import uuid

# ... existing app init ...

@app.route('/upload', methods=['POST'])
def api_upload():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if not file or file.filename.strip() == '':
            return jsonify({'error': 'Empty file'}), 400

        # Save to a unique temp file to avoid race conditions
        fname = f"{uuid.uuid4().hex}.jpg"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
        file.save(file_path)

        try:
            grid = extract_sudoku_grid(file_path)
        finally:
            # Clean up the temp file
            try:
                os.remove(file_path)
            except Exception:
                pass

        if not grid or len(grid) != 9 or any(len(row) != 9 for row in grid):
            return jsonify({'error': 'OCR failed to detect Sudoku grid'}), 400

        return jsonify({'grid': grid})

    except Exception as e:
        return jsonify({'error': f'Upload error: {str(e)}'}), 500
