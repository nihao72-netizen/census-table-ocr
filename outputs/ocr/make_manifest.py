"""실행 환경과 설정을 manifest.json에 기록한다.

실행: .venv\\Scripts\\python.exe outputs\\ocr\\make_manifest.py
"""
import hashlib
import json
import platform
import sys
from datetime import datetime
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "ocr"
MODEL_DIR = Path.home() / ".paddlex" / "official_models"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def model_info(name):
    weights = MODEL_DIR / name / "inference.pdiparams"
    return {
        "name": name,
        "source": "PaddleX official model (자동 다운로드)",
        "weights_sha256": sha256(weights) if weights.exists() else None,
    }


manifest = {
    "task": "B. OCR로 표 이미지를 다시 쓰기 — Census Table 1",
    "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    "source": {
        "title": "Thirteenth Census of the United States, Volume 1 (1910 인구조사 보고서, 1913년 발행)",
        "publisher": "U.S. Census Bureau",
        "url": "https://www2.census.gov/library/publications/decennial/1910/volume-1/volume-1-p3.pdf",
        "pdf_page": 2,
        "printed_page": 22,
        "table": "Table 1 — Area and Population",
        "license": "Public domain (미국 연방정부 발행물)",
        "image_note": "과제에서 제공한 표 부분 이미지(200 dpi 추출)",
    },
    "input": {
        "file": "input/census-table.png",
        "copy": "outputs/ocr/input_census-table.png",
        "size_px": [1050, 505],
        "sha256": sha256(ROOT / "input" / "census-table.png"),
    },
    "run": {
        "location": "로컬 PC (Windows, CPU), 프로젝트 폴더의 .venv 가상환경",
        "os": platform.platform(),
        "python": sys.version.split()[0],
        "device": "cpu",
    },
    "packages": {p: version(p) for p in
                 ["paddlepaddle", "paddleocr", "paddlex", "numpy", "opencv-contrib-python", "pillow"]},
    "models": {
        "text_detection": model_info("PP-OCRv6_medium_det"),
        "text_recognition": model_info("PP-OCRv6_medium_rec"),
        "selected_by": "PaddleOCR(lang='en') 기본값 (모델명을 직접 지정하지 않음)",
    },
    "settings": {
        "lang": "en",
        "use_doc_orientation_classify": False,
        "use_doc_unwarping": False,
        "use_textline_orientation": False,
        "enable_mkldnn": False,
        "env": {"PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK": "True (선택, 모델 서버 연결 확인 생략)"},
        "reasons": {
            "orientation/unwarping off": "스캔 이미지가 이미 똑바로 서 있고 왜곡이 없음",
            "enable_mkldnn=False": "Windows CPU에서 oneDNN(PIR) 경로가 NotImplementedError로 실패해 끔",
        },
    },
    "table_parsing": {
        "script": "outputs/ocr/build_table.py",
        "column_bounds_px": {"label": "< 670", "area": "670–855", "population": ">= 855"},
        "row_tolerance_px": 12,
        "header_max_y": 100,
        "footnote_min_y": 450,
    },
    "pipeline": [
        "outputs/ocr/ocr_run.py      — OCR 실행, 원시 JSON·좌표·시각화 저장",
        "outputs/ocr/build_table.py  — 좌표로 행·열 연결, table_raw.csv, 검산(checks_raw.json)",
        "outputs/ocr/make_crops.py   — 원본 대조용 확대 이미지(crops/)",
        "outputs/ocr/review.py       — 원본 대조 결과 반영: table.csv, document.md, review_overlay.png, checks.json",
        "outputs/ocr/make_manifest.py — 이 파일",
    ],
    "results": {
        "ocr_text_regions": 41,
        "numeric_cells": 22,
        "matched_original": 19,
        "corrected": 2,
        "blank_in_original": 1,
        "unreadable": 0,
        "checks_after_review": json.loads((OUT / "checks.json").read_text(encoding="utf-8")),
    },
    "review": {
        "reviewer": "코딩 에이전트(Claude)가 확대 이미지로 대조 — 제출 전 사용자 최종 확인 필요",
        "record": "outputs/ocr/document.md",
    },
}

(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: manifest[k] for k in ("packages", "models", "run")}, ensure_ascii=False, indent=2))
