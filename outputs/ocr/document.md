# Census Table 1 — Area and Population (1910) OCR 복원

- 출처: 미국 인구조사국, *Thirteenth Census of the United States, Volume 1* (1913년 발행), PDF 2쪽 · 인쇄 22쪽 — 퍼블릭 도메인
  - 원문: https://www2.census.gov/library/publications/decennial/1910/volume-1/volume-1-p3.pdf
- 입력: `input/census-table.png` (과제 제공, 200 dpi 추출, 1050×505)
- 처리: PaddleOCR 3.7.0 (PP-OCRv6_medium_det / PP-OCRv6_medium_rec, lang=en, CPU) → 좌표로 행·열 연결 → 합계 검산 → 원본 확대 대조

## 복원한 표

| 지역 | 수준 | 총면적(육지+수역, sq mi) | 인구 | 인구 기준연도 | 비고 |
|---|---|---:|---:|---:|---|
| **United States, with outlying possessions** | 합계 | 3,743,306 | 101,115,487 | 1910 |  |
| United States, exclusive of outlying possessions | 구분 | 3,026,789 | 91,972,266 | 1910 |  |
| Outlying possessions | 구분 | 716,517 | 9,143,221 | 1910 |  |
| &nbsp;&nbsp;Alaska | 세부 | 590,884 | 64,356 | 1910 |  |
| &nbsp;&nbsp;Hawaii | 세부 | 6,449 | 191,909 | 1910 |  |
| &nbsp;&nbsp;Porto Rico | 세부 | 3,435 | 1,118,012 | 1910 |  |
| &nbsp;&nbsp;Military and naval service abroad | 세부 | — (원문 값 없음) | 55,608 | 1910 |  |
| &nbsp;&nbsp;Philippine Islands | 세부 | 115,026 | 7,635,426 ⁽1⁾ | 1903 | 인구는 1903년 값(각주 1) |
| &nbsp;&nbsp;Panama Canal Zone | 세부 | 436 | 62,810 ⁽2⁾ | 1912 | 인구는 1912년 값(각주 2) |
| &nbsp;&nbsp;Guam (population estimated) | 세부 | 210 | 9,000 | 1910 | 원문에 추정치로 표기 |
| &nbsp;&nbsp;Samoa (population estimated) | 세부 | 77 | 6,100 | 1910 | 원문에 추정치로 표기 |

¹ Population in 1903. ² Population in 1912. (원문 각주)

## 수정 내역 (원시 OCR → 원본 대조 후)

| 위치 (행 / 열) | 원시 OCR | 수정값 | 이유 | 근거 이미지 |
|---|---|---|---|---|
| Philippine Islands / 인구 | `17,635,426` | 7,635,426 + 각주 1 | 원본의 위첨자 각주 기호 ¹이 숫자 앞에 붙어 '1'로 인식됨. 확대 이미지에서 ¹이 숫자보다 작고 위에 있음. | `crops/philippine_pop.png` |
| Panama Canal Zone / 인구 | `262,810` | 62,810 + 각주 2 | 원본의 위첨자 각주 기호 ²가 숫자 앞에 붙어 '2'로 인식됨. 확대 이미지에서 ²가 숫자보다 작고 위에 있음. | `crops/panama_pop.png` |
| Military and naval service abroad / 면적 | (인식 없음) | 값 없음 | 원본 면적 칸에는 숫자 없이 점선만 있음. 0이 아니라 '값 없음(해당 없음)'으로 둔다. | `crops/military_area.png` |

두 오류 모두 OCR 점수가 높았습니다(0.989, 0.945). 점수로는 걸러지지 않았고, 아래 합계 검산에서 차이가 나서 발견했습니다.

## 검산

| 검산 항목 | 수정 전 | 수정 후 |
|---|---|---|
| 면적: 세부 8행 합 = Outlying possessions | OK | OK |
| 면적: exclusive + Outlying = with outlying | OK | OK |
| 인구: 세부 8행 합 = Outlying possessions | NG (19,343,221 vs 9,143,221, 차이 +10,200,000) | OK |
| 인구: exclusive + Outlying = with outlying | OK | OK |

## 확인 필요 · 한계

- **판독 불가 칸: 없음.** 22개 숫자 칸 중 21개는 OCR 값이 원본과 일치했고, 2개(위 수정 내역)는 원본 대조로 고쳤으며, 1개는 원문에 값이 없습니다.
- **확인 필요 — 열 제목과 실제 연도 불일치:** 열 제목은 'Population: 1910'이지만 Philippine Islands(1903년)와 Panama Canal Zone(1912년)은 다른 해의 값입니다. 그런데 원문 소계 9,143,221과 총계 101,115,487에는 이 값들이 그대로 더해져 있습니다. 이 표를 '1910년 인구'로 쓸 때는 이 점을 함께 적어야 합니다.
- **추정치:** Guam과 Samoa는 원문에 'population estimated'로 적혀 있습니다.
- 'Porto Rico'는 원문 표기(당시 공식 명칭)를 그대로 두었습니다.
- 지역명의 끝 점선과 마침표는 표 구조상 의미가 없어 제거했습니다. 숫자의 띄어쓰기 (`3, 743, 306`)는 천 단위 쉼표로 보고 CSV에는 쉼표 없는 정수로 저장했습니다.
- **검토자:** 원본 대조는 코딩 에이전트(Claude)가 확대 이미지로 수행했습니다. 제출 전에 사용자가 `review_overlay.png`와 `crops/`를 직접 열어 최종 확인해야 합니다.

## 파일

| 파일 | 내용 |
|---|---|
| `table.csv` | 최종 표 (수정 반영, 칸별 상태와 OCR id 포함) |
| `table_raw.csv / table_raw.md` | OCR 그대로의 구조화 초안 (보존) |
| `census-table_res.json` | PaddleOCR 원시 결과 (문자열·점수·좌표) |
| `ocr_lines.csv` | 인식 문자열 41개와 박스 좌표 |
| `census-table_ocr_res_img.png` | OCR 글자 영역 시각화 |
| `review_overlay.png` | 검토 시각화: 초록=원본 일치, 주황=수정, 회색=원문 값 없음 |
| `crops/` | 원본 대조에 쓴 4배 확대 이미지 |
| `checks_raw.json / checks.json` | 수정 전·후 검산 결과 |
