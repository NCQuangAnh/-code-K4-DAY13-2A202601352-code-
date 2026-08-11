# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: A4-2222
- Repository URL: https://github.com/NCQuangAnh/-code-K4-DAY13-2A202601352-code-
- Commit SHA cuối:
- Thành viên và vai trò:

| # | Thành viên | MSSV | Vai trò |
|---|---|---|---|
| 1 | Nguyễn Cao Quang Anh | 2A202601352 | P1: Logging & PII |
| 2 | Nguyễn Thị Nam Phương | 2A202601720 | P2: Tracing & Prompt Version |
| 3 | Vũ Đình Huy | 2A202601288 | P3: Dashboard & SLO |
| 4 | Lê Quang Trung | 2A202601158 | P4: Alert & Runbook |
| 5 | Lê Tuấn Minh | 2A202601390 | P5: Incident, Test & Submission |

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: **100/100** (sau khi hoàn thiện P1: `middleware.py`, `pii.py`, `logging_config.py`, `main.py`), baseline trước khi sửa là 30/100.
- Tổng số traces: ≥10 (xem `submission/evidence/p2-01-traces-list-10plus.png`)
- Số PII leak còn lại: 0 (validator xác nhận `+ [PASSED] PII scrubbing`, không phát hiện email/phone/CCCD/thẻ tín dụng nguyên văn)
- Link/đường dẫn dashboard: xem `submission/evidence/p3-dashboard-baseline.png`, `p3-dashboard-baseline1.png` (dashboard build trên nguồn `data/logs.jsonl` theo `config/dashboard.yaml`)

## 3. Logging và tracing

- Evidence correlation ID: `submission/evidence/p5-01-challenge-logs.jsonl`, mỗi request có `correlation_id` dạng `req-<8 hex>` xuyên suốt `request_received` → `response_sent`.
- Evidence PII redaction: log request `req-8d3df6ed` ghi `"What is the policy for PII and credit card [REDACTED_CREDIT_CARD]?"`, số thẻ test đã bị che trước khi ghi log.
- Evidence trace waterfall: `submission/evidence/p2-02-trace-baseline-v1.png` (v1), `p2-03-trace-candidate-v2.png` (v2)
- Giải thích một span đáng chú ý: span `generation` bao trọn `LabAgent.run()` (retrieve + prompt + LLM call), khi incident `rag_slow` bật, thời lượng span này tăng từ baseline ~1.3s lên ~3.6–3.75s, khớp với `time.sleep(2.5)` bị inject trong `mock_rag.retrieve()`. Lưu ý: `retrieve()` hiện **không có span riêng** (chỉ `agent.run` được `@observe`), nên trace một mình không tách được retrieval khỏi LLM call, phải đối chiếu thêm log/code để xác định chính xác điểm nghẽn.

## 4. Prompt versioning

- Prompt name: `day13-chat` (biến bắt buộc `feature`, `docs`, `message`)
- Version/label baseline: **v1**, label `baseline` + `production`, tạo lúc 8/11/2026 3:48:27 PM. Nội dung: `Feature={{feature}} / Docs={{docs}} / Question={{message}}`.
- Version/label candidate: **v2**, label `candidate` (+ `latest`), tạo lúc 8/11/2026 4:03:17 PM. Thay đổi nhỏ so với v1: thêm dòng `Answer in 2-3 concise sentences.` để giới hạn độ dài câu trả lời. Evidence: `submission/evidence/p2-06-prompt-versions-list.png`.
- Trace ID của mỗi version (chạy cùng input, đổi `LANGFUSE_PROMPT_LABEL`):
  - Baseline (v1): session `s-prompt-baseline`, 2026-08-11 15:51:09, `prompt_version=1`, `prompt_label=baseline`, `prompt_source=langfuse`, cost $0.002067, `submission/evidence/p2-02-trace-baseline-v1.png`
  - Candidate (v2): session `s-prompt-candidate`, 2026-08-11 16:04:22, `prompt_version=2`, `prompt_label=candidate`, `prompt_source=langfuse`, cost $0.002169, `submission/evidence/p2-03-trace-candidate-v2.png`
- Bằng chứng đổi label hoặc rollback:
  - Promote v2 → `production`: session `s-prompt-after-promote-2`, 2026-08-11 16:32:14, `prompt_version=2`, `prompt_label=production`, `submission/evidence/p2-04-label-promote-v2.png`
  - Rollback `production` về v1: trace ID **`02f5761171783bd5a14f8ff4649a1841`**, session `s-prompt-rollback`, 2026-08-11 16:43:27, `prompt_version=1`, `prompt_label=production`, `submission/evidence/p2-05-label-rollback-v1.png`
  - Trạng thái cuối xác nhận trên danh sách version (`p2-06`): v1 = `production`+`baseline`, v2 = `latest`+`candidate` → rollback thành công.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract.`
- Evidence dashboard: `submission/evidence/p3-dashboard-baseline.png`, `p3-dashboard-baseline1.png` (baseline, P95=151ms, 6 panel + threshold badge). Lúc incident `rag_slow`: `submission/evidence/p3-dashboard-incident.png`, P95 tăng lên **3162ms** và P99 **3493ms**, badge chuyển đỏ "vi phạm" ngưỡng p95≤3000ms, error rate và cost không đổi bất thường, xác nhận đây là sự cố latency thuần.
- SLO đã chọn và lý do (`config/slo.yaml`): `latency_p95_ms` ≤3000ms, `error_rate_pct` ≤2%, `daily_cost_usd` ≤2.5, `quality_score_avg` ≥0.75, giữ nguyên 4 SLI mặc định vì đã bao phủ đủ 3 khía cạnh (trải nghiệm, tin cậy, chi phí) cho một app chat có mock LLM; không hạ thấp target vì baseline đo được còn cách xa trần rất nhiều (P95 158ms, error 0%, quality 0.88, cost $0.08/60'), đủ dư địa cảnh báo sớm trước khi vi phạm SLO thật.
- Alert rules và runbook (`config/alert_rules.yaml` + `docs/alerts.md`): 3 alert symptom-based, mỗi alert map 1 kịch bản practice để kiểm chứng bằng dữ liệu thật thay vì số đoán:
  - `high_p95_latency`: P95 >1000ms, 2 lần refresh (~1 phút). Baseline 158ms → đo được 2665.7ms khi bật `inject_incident.py --scenario rag_slow`.
  - `elevated_error_rate`: error rate >1%, 2 lần refresh. Baseline 0% → đo được 100% (cô lập) / 14.3% (cả cửa sổ) khi bật `--scenario tool_fail`.
  - `cost_per_request_spike`: cost trung bình >$0.005/request, 2 lần refresh. Baseline $0.0019 → đo được $0.0077 (4.02x) khi bật `--scenario cost_spike`. Đổi từ ngưỡng tổng $/60 phút sang trung bình/request vì tổng không đủ nhạy ở traffic thấp của lab (đo thật chỉ đạt $0.18/60' dù có spike).
  - Runbook đầy đủ (ảnh hưởng người dùng, 3 bước kiểm tra, mitigation, owner) cho từng alert nằm trong `docs/alerts.md`.

## 6. Điều tra challenge

- Challenge ID: `day13-k4-observability-v1` (cohort K4, incident `rag_slow`, threshold 2000ms), xem `config/challenge.json`
- Triệu chứng từ metrics: `GET /metrics`, `latency_p95` tăng từ **1374ms** (baseline, 10 request practice) lên **3753ms** sau khi chạy `inject_incident.py` + `load_test.py --challenge --concurrency 5` (traffic 15). `error_breakdown` và `avg_cost_usd` không đổi → xác nhận đây là sự cố latency thuần, không phải lỗi hay cost. Chi tiết: `submission/evidence/p5-02-metrics-before-after.json`.
- Trace ID liên quan:
  - `k4-challenge-s01`: `a1af50eeef7cb26efac49396e69dafe0` (span 2.651s)
  - `k4-challenge-s02`: `ff8f57a0aab8f15d63a00188ce0d09c3` (span 2.652s)
  - `k4-challenge-s03`: `ec9cad0cfd765bfae46d4b46413c85bd` (span 2.653s)
  - `k4-challenge-s04`: `e4f3519edaf4dd68dc7cfec5b8c7d2c8` (span 2.655s)
  - `k4-challenge-s05`: `a99ef43554a755af94031647f2fefe20` (span 3.688s)
  - Span duration (~2.6-3.7s) khớp baseline + `time.sleep(2.5)` inject trong `rag_slow`, xác nhận đúng root cause ở tầng trace.
- Log line/correlation ID liên quan: 5 correlation ID của các request challenge, latency đo phía server (log `response_sent`): `req-be17461e` (3736ms), `req-d09cd358` (3753ms), `req-1c3cf73c` (3625ms), `req-66716925` (3669ms), `req-a2141938` (3709ms). Log `incident_enabled` (`correlation_id=req-5da2ddb9`, ts `10:27:42`) xác nhận thời điểm `rag_slow` được bật ngay trước 5 request trên. Đầy đủ trong `submission/evidence/p5-01-challenge-logs.jsonl`.
- Root cause: `app/mock_rag.py:18`, khi `STATE["rag_slow"]` bật, `retrieve()` gọi `time.sleep(2.5)` (blocking, đồng bộ). Vì `LabAgent.run()` (gọi `retrieve()`) là hàm sync được gọi trực tiếp, không `await`, không chạy trong threadpool, từ handler `async def chat()` trong `app/main.py`, `time.sleep` này **chặn luôn event loop** của FastAPI. Latency đo phía server mỗi request chỉ ~3.6–3.75s (khớp baseline ~1.3s + 2.5s sleep), nhưng latency client đo được lên tới **11–18.5s** khi có 5 request đồng thời, vì các request phải xếp hàng tuần tự thay vì chạy song song, hiệu ứng khuếch đại do event loop bị block, không đơn thuần là "RAG chậm 2.5 giây".
- Fix action: đổi `retrieve()` sang non-blocking, dùng `await asyncio.sleep(...)` nếu hàm async hoá được, hoặc bọc lệnh gọi `retrieve()` bằng `starlette.concurrency.run_in_threadpool` (hoặc `asyncio.to_thread`) ở `agent.py`/`main.py` để không giữ event loop; đồng thời thêm timeout cho bước retrieval để tránh một request chậm kéo theo cả hàng đợi.
- Preventive measure: bọc `retrieve()` bằng `@observe` riêng để trace tách được span retrieval khỏi LLM call (dễ khoanh vùng lần sau); giữ alert `high_p95_latency` trong `config/alert_rules.yaml` (ngưỡng p95 >1000ms) làm cảnh báo sớm; thêm test tải (concurrency) vào CI/practice để phát hiện hiệu ứng nghẽn event loop trước khi lên production.

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Nguyễn Cao Quang Anh (P1) | Correlation ID (`middleware.py`), bind context (`main.py`), scrub processor (`logging_config.py`), thêm PII pattern passport (`pii.py`) | `856dde2` middleware · `3985c26` bind request context to structlog · `02d2edd` register pii scrub processor · `0153695` add passport, pii patterns | Context của `structlog` phải được `bind_contextvars` **trước** dòng `log.info` đầu tiên thì các log sau trong cùng request mới thừa hưởng; thứ tự processor trong pipeline quyết định PII có bị scrub trước khi ghi file hay không, đặt `scrub_event` sau `merge_contextvars` nhưng trước `JSONRenderer`/ghi file. |
| Nguyễn Thị Nam Phương (P2) | Cấu hình Langfuse, tạo prompt v1/v2, demo đổi label/rollback | `3621d4a` Langfuse traces | SDK Langfuse đọc host qua đúng biến `LANGFUSE_HOST` (không phải tên tự đặt như `LANGFUSE_BASE_URL`), sai tên biến làm SDK fallback về host mặc định và trả lỗi 401 dù key đúng. Prompt được client cache theo `cache_ttl_seconds` (60s) nên đổi label trên UI không phản ánh ngay lập tức, phải đợi cache hết hạn hoặc restart app mới thấy hiệu lực, dễ nhầm là lỗi. |
| Vũ Đình Huy (P3) | Dựng dashboard runtime 6 panel từ `data/logs.jsonl` | `a9dd406` feat(dashboard): add streamlit runtime dashboard | Dashboard phải bám đúng contract (`config/dashboard.yaml`) thay vì tự chọn panel, field `query` trong YAML chỉ là pseudocode, phải tự chuyển sang logic tổng hợp thật (percentile, group by phút) trong code Streamlit. Threshold hiển thị trực tiếp trên panel giúp phát hiện vi phạm SLO nhanh hơn nhìn số thô. |
| Lê Quang Trung (P4) | Định nghĩa 3 alert rule symptom-based có threshold kiểm chứng bằng incident thật | `d99d468` alerts v1 · `b8c7c8c` feat(alerts): define 3 symptom-based alerts with real incident-verified thresholds | Alert phải symptom-based (dựa trên trải nghiệm người dùng: latency, error rate) chứ không dựa tên implementation nội bộ. Threshold phải chốt bằng số đo thật, không đoán: ví dụ ngưỡng cost ban đầu định đặt theo tổng $/60 phút nhưng traffic thấp của lab không bao giờ chạm ngưỡng đó, phải đổi sang cost trung bình/request mới đủ nhạy. |
| Lê Tuấn Minh (P5) | Setup môi trường (Checkpoint 0), chạy challenge chính thức (`inject_incident.py` + `load_test.py --challenge`), điều tra root cause Metrics→Logs, tổng hợp `REPORT.md` + `submission/evidence/` | `f133655` Test and Submission · `7d2756b` Merge branch 'main' | Latency đo phía server (~3.6-3.75s/request) không giải thích được latency client thấy (11-18.5s) khi có 5 request đồng thời, phải hiểu `time.sleep` (blocking, sync) trong handler `async def` chặn luôn event loop của FastAPI, làm các request phải xếp hàng thay vì chạy song song. Kết luận root cause chỉ chắc chắn khi khớp cả ba lớp Metrics → Traces → Logs, không suy diễn từ một lớp. |

`BobbyFischer0` = Nguyễn Cao Quang Anh (P1).*