# ocr_processing.py
import cv2
import pytesseract
import numpy as np
import os

# Use OS-appropriate tesseract path ONLY if needed.
# On most Linux Docker images, it's /usr/bin/tesseract after apt install.
if os.name != "nt":
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]      # top-left
    rect[2] = pts[np.argmax(s)]      # bottom-right
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]   # top-right
    rect[3] = pts[np.argmax(diff)]   # bottom-left
    return rect

def extract_sudoku_grid(image_path):
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Invalid image")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            raise ValueError("No grid found")

        largest = max(contours, key=cv2.contourArea)
        epsilon = 0.02 * cv2.arcLength(largest, True)
        approx = cv2.approxPolyDP(largest, epsilon, True)
        if len(approx) != 4:
            raise ValueError("Grid not detected")

        pts = order_points(approx.reshape(4, 2).astype("float32"))
        width = int(max(np.linalg.norm(pts[0]-pts[1]), np.linalg.norm(pts[2]-pts[3])))
        height = int(max(np.linalg.norm(pts[1]-pts[2]), np.linalg.norm(pts[3]-pts[0])))

        dst = np.array([[0,0],[width-1,0],[width-1,height-1],[0,height-1]], dtype="float32")
        M = cv2.getPerspectiveTransform(pts, dst)
        warp = cv2.warpPerspective(gray, M, (width, height))

        grid = []
        cell = width // 9
        margin = cell // 10

        for r in range(9):
            row_vals = []
            for c in range(9):
                x1 = c * cell + margin
                y1 = r * cell + margin
                tile = warp[y1:y1+cell-margin, x1:x1+cell-margin]
                tile = cv2.resize(tile, (48, 48))
                _, tile = cv2.threshold(tile, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                text = pytesseract.image_to_string(
                    tile, config='--psm 10 -c tessedit_char_whitelist=0123456789'
                ).strip()
                row_vals.append(int(text) if text.isdigit() else 0)
            grid.append(row_vals)

        return grid
    except Exception as e:
        raise RuntimeError(f"OCR Error: {str(e)}")
