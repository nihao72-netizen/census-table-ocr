"""원본 대조 결과(사람이 정한 수정)를 표 초안에 적용해 table.csv, document.md, 검토 시각화를 만든다.

- table_raw.csv : OCR이 읽은 그대로의 구조화 초안 (수정하지 않고 보존)
- CORRECTIONS   : 원본 확대 이미지(crops/)로 대조해 정한 수정 목록. 수정 근거를 함께 둔다.
실행: .venv\\Scripts\\python.exe outputs\\ocr\\review.py
"""
import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent

with open(OUT / "table_raw.csv", encoding="utf-8-sig") as f:
    raw_rows = list(csv.DictReader(f))


def num(s):
    return int(s) if s not in ("", None) else None


# ---- 원본 대조로 정한 수정 / 메모 -------------------------------------------
CORRECTIONS = {
    ("Philippine Islands", "population"): {
        "raw": "17,635,426", "fixed": 7635426, "footnote": "1",
        "reason": "원본의 위첨자 각주 기호 ¹이 숫자 앞에 붙어 '1'로 인식됨. 확대 이미지에서 ¹이 숫자보다 작고 위에 있음.",
        "evidence": "crops/philippine_pop.png",
    },
    ("Panama Canal Zone", "population"): {
        "raw": "262,810", "fixed": 62810, "footnote": "2",
        "reason": "원본의 위첨자 각주 기호 ²가 숫자 앞에 붙어 '2'로 인식됨. 확대 이미지에서 ²가 숫자보다 작고 위에 있음.",
        "evidence": "crops/panama_pop.png",
    },
}
BLANK = {
    ("Military and naval service abroad", "area"): {
        "reason": "원본 면적 칸에는 숫자 없이 점선만 있음. 0이 아니라 '값 없음(해당 없음)'으로 둔다.",
        "evidence": "crops/military_area.png",
    },
}
FOOTNOTE_YEAR = {"1": 1903, "2": 1912}   # 각주: ¹ Population in 1903. ² Population in 1912.

rows = []
for r in raw_rows:
    name = r["region"]
    area, pop = num(r["area_sq_mi"]), num(r["population_1910"])
    footnote, notes = "", []
    status_area = "원본 일치" if area is not None else "값 없음"
    status_pop = "원본 일치"
    c = CORRECTIONS.get((name, "population"))
    if c:
        pop, footnote, status_pop = c["fixed"], c["footnote"], "수정"
        notes.append(f"인구는 {FOOTNOTE_YEAR[footnote]}년 값(각주 {footnote})")
    if "estimated" in name:
        notes.append("원문에 추정치로 표기")
    rows.append({
        "region": name,
        "level": r["level"],
        "area_sq_mi": "" if area is None else area,
        "population": pop,
        "population_year": FOOTNOTE_YEAR.get(footnote, 1910),
        "footnote": footnote,
        "area_status": status_area,
        "population_status": status_pop,
        "note": "; ".join(notes),
        "area_ocr_id": r["area_ocr_id"],
        "pop_ocr_id": r["pop_ocr_id"],
    })

with open(OUT / "table.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

# ---- 수정 후 검산 -----------------------------------------------------------
by = {r["region"]: r for r in rows}
detail = [r for r in rows if r["level"] == "세부"]
checks = []
for key, label in [("area_sq_mi", "면적"), ("population", "인구")]:
    val = lambda r: int(r[key]) if r[key] != "" else 0
    sub, tot, ex = by["Outlying possessions"], by["United States, with outlying possessions"], \
        by["United States, exclusive of outlying possessions"]
    checks.append((f"{label}: 세부 {len(detail)}행 합 = Outlying possessions", sum(val(r) for r in detail), val(sub)))
    checks.append((f"{label}: exclusive + Outlying = with outlying", val(ex) + val(sub), val(tot)))
check_result = [{"check": n, "computed": a, "table_value": b, "ok": a == b} for n, a, b in checks]
(OUT / "checks.json").write_text(json.dumps(check_result, ensure_ascii=False, indent=2), encoding="utf-8")
raw_checks = json.loads((OUT / "checks_raw.json").read_text(encoding="utf-8"))

# ---- 검토 시각화: 원본 위에 칸별 상태 표시 -------------------------------
res = json.loads((OUT / "census-table_res.json").read_text(encoding="utf-8"))
boxes = res["rec_boxes"]
img = Image.open(OUT / "input_census-table.png").convert("RGB")
d = ImageDraw.Draw(img)
GREEN, ORANGE, GRAY = (0, 160, 0), (230, 110, 0), (120, 120, 120)
for r in rows:
    for col in ("area", "pop"):
        oid = r[f"{col}_ocr_id"]
        status = r["area_status"] if col == "area" else r["population_status"]
        if oid != "":
            x1, y1, x2, y2 = boxes[int(oid)]
            color = ORANGE if status == "수정" else GREEN
            d.rectangle([x1 - 2, y1 - 1, x2 + 2, y2 + 1], outline=color, width=3 if color == ORANGE else 2)
# 값 없음 칸 (원본 좌표에서 직접 지정)
d.rectangle([676, 318, 852, 344], outline=GRAY, width=2)
d.text((8, img.height - 14), "green=matched original  orange=corrected  gray=blank in original", fill=(0, 0, 0))
img.save(OUT / "review_overlay.png")

# ---- document.md -----------------------------------------------------------
def fmt(v):
    return "" if v in ("", None) else f"{int(v):,}"


L = []
L.append("# Census Table 1 — Area and Population (1910) OCR 복원\n")
L.append("- 출처: 미국 인구조사국, *Thirteenth Census of the United States, Volume 1* (1913년 발행), "
         "PDF 2쪽 · 인쇄 22쪽 — 퍼블릭 도메인")
L.append("  - 원문: https://www2.census.gov/library/publications/decennial/1910/volume-1/volume-1-p3.pdf")
L.append("- 입력: `input/census-table.png` (과제 제공, 200 dpi 추출, 1050×505)")
L.append("- 처리: PaddleOCR 3.7.0 (PP-OCRv6_medium_det / PP-OCRv6_medium_rec, lang=en, CPU) → "
         "좌표로 행·열 연결 → 합계 검산 → 원본 확대 대조\n")
L.append("## 복원한 표\n")
L.append("| 지역 | 수준 | 총면적(육지+수역, sq mi) | 인구 | 인구 기준연도 | 비고 |")
L.append("|---|---|---:|---:|---:|---|")
for r in rows:
    pop = fmt(r["population"]) + (f" ⁽{r['footnote']}⁾" if r["footnote"] else "")
    area = fmt(r["area_sq_mi"]) if r["area_sq_mi"] != "" else "— (원문 값 없음)"
    name = ("**" + r["region"] + "**") if r["level"] == "합계" else (
        "&nbsp;&nbsp;" + r["region"] if r["level"] == "세부" else r["region"])
    L.append(f"| {name} | {r['level']} | {area} | {pop} | {r['population_year']} | {r['note']} |")
L.append("\n¹ Population in 1903. ² Population in 1912. (원문 각주)\n")

L.append("## 수정 내역 (원시 OCR → 원본 대조 후)\n")
L.append("| 위치 (행 / 열) | 원시 OCR | 수정값 | 이유 | 근거 이미지 |")
L.append("|---|---|---|---|---|")
for (name, col), c in CORRECTIONS.items():
    L.append(f"| {name} / 인구 | `{c['raw']}` | {c['fixed']:,} + 각주 {c['footnote']} | {c['reason']} | `{c['evidence']}` |")
for (name, col), c in BLANK.items():
    L.append(f"| {name} / 면적 | (인식 없음) | 값 없음 | {c['reason']} | `{c['evidence']}` |")
L.append("")
L.append("두 오류 모두 OCR 점수가 높았습니다(0.989, 0.945). 점수로는 걸러지지 않았고, "
         "아래 합계 검산에서 차이가 나서 발견했습니다.\n")

L.append("## 검산\n")
L.append("| 검산 항목 | 수정 전 | 수정 후 |")
L.append("|---|---|---|")
for rc, c in zip(raw_checks, check_result):
    before = "OK" if rc["ok"] else f"NG ({rc['computed']:,} vs {rc['table_value']:,}, 차이 {rc['computed'] - rc['table_value']:+,})"
    after = "OK" if c["ok"] else f"NG ({c['computed']:,} vs {c['table_value']:,})"
    L.append(f"| {c['check']} | {before} | {after} |")
L.append("")

L.append("## 확인 필요 · 한계\n")
L.append("- **판독 불가 칸: 없음.** 22개 숫자 칸 중 21개는 OCR 값이 원본과 일치했고, "
         "2개(위 수정 내역)는 원본 대조로 고쳤으며, 1개는 원문에 값이 없습니다.")
L.append("- **확인 필요 — 열 제목과 실제 연도 불일치:** 열 제목은 'Population: 1910'이지만 "
         "Philippine Islands(1903년)와 Panama Canal Zone(1912년)은 다른 해의 값입니다. "
         "그런데 원문 소계 9,143,221과 총계 101,115,487에는 이 값들이 그대로 더해져 있습니다. "
         "이 표를 '1910년 인구'로 쓸 때는 이 점을 함께 적어야 합니다.")
L.append("- **추정치:** Guam과 Samoa는 원문에 'population estimated'로 적혀 있습니다.")
L.append("- 'Porto Rico'는 원문 표기(당시 공식 명칭)를 그대로 두었습니다.")
L.append("- 지역명의 끝 점선과 마침표는 표 구조상 의미가 없어 제거했습니다. 숫자의 띄어쓰기 "
         "(`3, 743, 306`)는 천 단위 쉼표로 보고 CSV에는 쉼표 없는 정수로 저장했습니다.")
L.append("- **검토자:** 원본 대조는 코딩 에이전트(Claude)가 확대 이미지로 수행했습니다. "
         "제출 전에 사용자가 `review_overlay.png`와 `crops/`를 직접 열어 최종 확인해야 합니다.\n")

L.append("## 파일\n")
L.append("| 파일 | 내용 |")
L.append("|---|---|")
for fn, desc in [
    ("table.csv", "최종 표 (수정 반영, 칸별 상태와 OCR id 포함)"),
    ("table_raw.csv / table_raw.md", "OCR 그대로의 구조화 초안 (보존)"),
    ("census-table_res.json", "PaddleOCR 원시 결과 (문자열·점수·좌표)"),
    ("ocr_lines.csv", "인식 문자열 41개와 박스 좌표"),
    ("census-table_ocr_res_img.png", "OCR 글자 영역 시각화"),
    ("review_overlay.png", "검토 시각화: 초록=원본 일치, 주황=수정, 회색=원문 값 없음"),
    ("crops/", "원본 대조에 쓴 4배 확대 이미지"),
    ("checks_raw.json / checks.json", "수정 전·후 검산 결과"),
]:
    L.append(f"| `{fn}` | {desc} |")

(OUT / "document.md").write_text("\n".join(L) + "\n", encoding="utf-8")

print("table.csv rows:", len(rows))
for c in check_result:
    print(("OK " if c["ok"] else "NG ") + c["check"])
