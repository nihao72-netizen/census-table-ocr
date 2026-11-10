"""Census Table 1 이미지를 PaddleOCR(영어)로 읽고 원시 결과를 저장한다.

실행: .venv\\Scripts\\python.exe outputs\\ocr\\ocr_run.py
"""
import csv
import json
import shutil
from pathlib import Path

from paddleocr import PaddleOCR

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "input" / "census-table.png"
OUT = ROOT / "outputs" / "ocr"
OUT.mkdir(parents=True, exist_ok=True)

# 입력 사본 보존
shutil.copy2(SRC, OUT / "input_census-table.png")

# 스캔 이미지가 이미 똑바로 서 있으므로 문서 방향/왜곡 보정은 끈다.
ocr = PaddleOCR(
    lang="en",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    # Windows CPU에서 oneDNN(PIR) 경로가 NotImplementedError를 내므로 끈다.
    enable_mkldnn=False,
)

results = ocr.predict(str(SRC))
res = results[0]

# 1) 원시 JSON (PaddleOCR 그대로) + 2) 영역 시각화 이미지
res.save_to_json(str(OUT))
res.save_to_img(str(OUT))

# 원시 JSON의 입력 경로를 PC 절대경로 대신 프로젝트 기준 상대경로로 기록한다(값·좌표는 그대로).
json_path = OUT / "census-table_res.json"
saved = json.loads(json_path.read_text(encoding="utf-8"))
saved["input_path"] = SRC.relative_to(ROOT).as_posix()
json_path.write_text(json.dumps(saved, ensure_ascii=False, indent=4), encoding="utf-8")

# 3) 텍스트·좌표 표 (사람이 읽기 쉬운 형태)
data = res.json["res"]
rows = []
for i, (text, score, box) in enumerate(
    zip(data["rec_texts"], data["rec_scores"], data["rec_boxes"])
):
    x1, y1, x2, y2 = [int(v) for v in box]
    rows.append({"id": i, "text": text, "score": round(float(score), 4),
                 "x1": x1, "y1": y1, "x2": x2, "y2": y2})

with open(OUT / "ocr_lines.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

print(f"인식된 텍스트 영역: {len(rows)}개")
for r in rows:
    print(f"{r['id']:>3} {r['score']:.3f} ({r['x1']},{r['y1']})-({r['x2']},{r['y2']}) {r['text']}")
