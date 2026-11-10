"""OCR 원시 결과(census-table_res.json)의 좌표로 행·열을 연결해 표 초안을 만든다.

사람의 수정은 넣지 않는다. 결과는 OCR이 읽은 그대로의 구조화 초안이다.
실행: .venv\\Scripts\\python.exe outputs\\ocr\\build_table.py
"""
import csv
import json
import re
from pathlib import Path

OUT = Path(__file__).resolve().parent
raw = json.loads((OUT / "census-table_res.json").read_text(encoding="utf-8"))

items = []
for i, (t, s, b) in enumerate(zip(raw["rec_texts"], raw["rec_scores"], raw["rec_boxes"])):
    x1, y1, x2, y2 = b
    items.append({"id": i, "text": t, "score": s, "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                  "yc": (y1 + y2) / 2})

# 원본 이미지의 세로 괘선 위치(픽셀, 1050px 폭 기준)로 열 경계를 정한다.
COL_LABEL_MAX = 670   # 이보다 왼쪽: 지역명
COL_AREA_MAX = 855    # 670~855: 면적 열, 그 오른쪽: 인구 열
HEADER_MAX_Y = 100    # 머리글 아래 가로선
FOOTNOTE_MIN_Y = 450  # 표 아래 테두리


def col_of(it):
    xc = (it["x1"] + it["x2"]) / 2
    if xc < COL_LABEL_MAX:
        return "label"
    return "area" if xc < COL_AREA_MAX else "pop"


body = [it for it in items if HEADER_MAX_Y < it["yc"] < FOOTNOTE_MIN_Y]
labels = sorted([it for it in body if col_of(it) == "label"], key=lambda it: it["yc"])


def nearest(col, yc, tol=12):
    """같은 행(세로 중심 차이 tol 픽셀 이내)에서 해당 열 값 하나를 찾는다."""
    cands = [it for it in body if col_of(it) == col and abs(it["yc"] - yc) <= tol]
    return min(cands, key=lambda it: abs(it["yc"] - yc)) if cands else None


def to_int(s):
    digits = re.sub(r"[^0-9]", "", s or "")
    return int(digits) if digits else None


rows = []
for lb in labels:
    a, p = nearest("area", lb["yc"]), nearest("pop", lb["yc"])
    name = lb["text"].rstrip(". ").strip()
    # 들여쓰기(x1)로 계층 구분: 가운데 굵은 줄=합계, 들여쓴 줄=세부, 왼쪽 줄=구분
    lvl = "합계" if lb["x1"] > 85 else ("세부" if lb["x1"] > 50 else "구분")
    rows.append({
        "region": name,
        "level": lvl,
        "area_sq_mi": to_int(a["text"]) if a else None,
        "population_1910": to_int(p["text"]) if p else None,
        "area_ocr_text": a["text"] if a else "",
        "area_ocr_score": round(a["score"], 3) if a else "",
        "area_ocr_id": a["id"] if a else "",
        "pop_ocr_text": p["text"] if p else "",
        "pop_ocr_score": round(p["score"], 3) if p else "",
        "pop_ocr_id": p["id"] if p else "",
        "label_ocr_id": lb["id"],
    })

# 표 초안 저장
with open(OUT / "table_raw.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)


def fmt(v):
    return "" if v is None else f"{v:,}"


md = ["| 지역 | 수준 | 면적(sq mi) | 인구 1910 |", "|---|---|---:|---:|"]
md += [f"| {r['region']} | {r['level']} | {fmt(r['area_sq_mi'])} | {fmt(r['population_1910'])} |"
       for r in rows]
(OUT / "table_raw.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("\n".join(md))

# 표 안의 합계 관계로 자동 검산 (원본 대조할 곳을 좁히는 용도)
by = {r["region"]: r for r in rows}
detail = [r for r in rows if r["level"] == "세부"]
checks = []
for key, label in [("area_sq_mi", "면적"), ("population_1910", "인구")]:
    s = sum(r[key] or 0 for r in detail)
    sub = by["Outlying possessions"][key]
    checks.append((f"{label}: 세부 {len(detail)}행 합 = 'Outlying possessions'", s, sub))
    tot = by["United States, with outlying possessions"][key]
    ex = by["United States, exclusive of outlying possessions"][key]
    checks.append((f"{label}: exclusive + Outlying = with outlying", ex + sub, tot))

print("\n검산")
result = []
for name, got, expect in checks:
    ok = got == expect
    print(f"  {'OK ' if ok else 'NG '} {name}: {got:,} vs {expect:,}" + ("" if ok else f" (차이 {got - expect:+,})"))
    result.append({"check": name, "computed": got, "table_value": expect, "ok": ok})
(OUT / "checks_raw.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
