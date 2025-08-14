import cv2
import numpy as np
import pytesseract
import platform

# Set Tesseract path based on OS
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


def extract_sudoku_grid(image_path):
    """
    Extracts a Sudoku grid from an uploaded image and returns it as a 2D list.
    """

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Unable to read the uploaded image.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, 1, 1, 11, 2)

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("No contours found. Is the Sudoku grid visible in the image?")

    # Find the largest contour (likely the Sudoku board)
    largest_contour = max(contours, key=cv2.contourArea)
    peri = cv2.arcLength(largest_contour, True)
    approx = cv2.approxPolyDP(largest_contour, 0.02 * peri, True)

    if len(approx) != 4:
        raise ValueError("Sudoku grid not detected properly. Please upload a clearer image.")

    # Warp perspective to get a top-down view
    pts = np.float32([point[0] for point in approx])
    side = max([np.linalg.norm(pts[0] - pts[1]),
                np.linalg.norm(pts[1] - pts[2]),
                np.linalg.norm(pts[2] - pts[3]),
                np.linalg.norm(pts[3] - pts[0])])
    dst = np.float32([[0, 0], [side - 1, 0], [side - 1, side - 1], [0, side - 1]])
    matrix = cv2.getPerspectiveTransform(pts, dst)
    warp = cv2.warpPerspective(gray, matrix, (int(side), int(side)))

    # Split into 9x9 grid
    grid = []
    step = warp.shape[0] // 9

    for y in range(9):
        row = []
        for x in range(9):
            cell = warp[y * step:(y + 1) * step, x * step:(x + 1) * step]
            cell = cv2.resize(cell, (28, 28))
            text = pytesseract.image_to_string(cell, config='--psm 10 digits')
            try:
                value = int(text.strip())
            except ValueError:
                value = 0
            row.append(value)
        grid.append(row)

    return grid
