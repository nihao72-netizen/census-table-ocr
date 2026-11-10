"""원본 대조용 확대 이미지를 만든다. 각 칸의 원본 영역을 4배 확대해 crops/에 저장한다.

실행: .venv\\Scripts\\python.exe outputs\\ocr\\make_crops.py
"""
from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parent
img = Image.open(OUT / "input_census-table.png").convert("RGB")
(OUT / "crops").mkdir(exist_ok=True)

# (파일명, (x1, y1, x2, y2)) - 원본 픽셀 좌표, OCR 박스보다 조금 넓게 잡는다
CROPS = [
    ("philippine_pop", (900, 333, 1045, 370)),   # OCR id 29: '17,635,426'
    ("panama_pop", (900, 356, 1045, 392)),       # OCR id 32: '262,810'
    ("military_area", (672, 312, 858, 348)),     # 면적 칸: OCR 결과 없음
    ("footnotes", (150, 462, 910, 497)),         # 각주 1·2
    ("header", (670, 15, 1045, 90)),             # 열 제목
]

for name, box in CROPS:
    c = img.crop(box)
    c = c.resize((c.width * 4, c.height * 4), Image.LANCZOS)
    c.save(OUT / "crops" / f"{name}.png")
    print("saved", name, box)
