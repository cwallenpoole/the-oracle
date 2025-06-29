import os
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import pytesseract
import re

# Configuration
url = "https://commons.wikimedia.org/w/index.php?search=Omega-cards&title=Special%3AMediaSearch&type=image"
output_dir = "downloaded_images"
os.makedirs(output_dir, exist_ok=True)
image_urls = [f'https://upload.wikimedia.org/wikipedia/commons/e/ee/Omega-cards-{i}.png' for i in range(1, 72)]

# Step 2: Download, OCR, and rename
for i, img_url in enumerate(image_urls):
    try:
        img_resp = requests.get(img_url)

        temp = os.path.join(output_dir, f"image-{i}.png")
        img = Image.open(BytesIO(img_resp.content))

        # Optional: preprocess image for better OCR results
        img = img.convert("L")  # grayscale
        text = pytesseract.image_to_string(img).strip()

        # Clean the text for filenames
        safe_text = re.sub(r"[^\w\- ]", "", text) or f"image_{i}"
        filename = os.path.join(output_dir, f"{safe_text[:50]}.png")

        # Save the image with new name
        img.save(filename)
        print(f"Saved: {filename}")
    except Exception as e:
        print(f"Error processing {img_url}: {e}")
