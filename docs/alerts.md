# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: High P95 Latency
- Severity: Warning (nâng Critical nếu duy trì >15 phút hoặc P95 chạm trần SLO 3000ms)
- SLI/SLO liên quan: `latency_p95_ms` (objective ≤3000ms, target 99.0% — `config/slo.yaml`)
- Điều kiện và thời gian duy trì: P95 latency > **1000ms** duy trì liên tục **≥5 phút**. Căn cứ: baseline đo trên dashboard `scripts/dashboard_app.py` là P95=158ms; khi bật `python scripts/inject_incident.py --scenario rag_slow` và load test lại, P95 đo được **2665.7ms** — 1000ms nằm giữa baseline và trần SLO 3000ms, đủ nhạy để bắt sớm sự cố thật nhưng không sát trần đến mức trễ.
- Ảnh hưởng tới người dùng: Chờ câu trả lời lâu hơn hẳn bình thường, cảm giác app bị đơ, có thể bỏ ngang phiên hỏi đáp.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Latency trên dashboard, xem P50/P95/P99 và thời điểm bắt đầu tăng.
  2. Mở trace tương ứng (Langfuse), tìm span chiếm nhiều thời gian nhất — thường là bước retrieval/RAG hoặc LLM call.
  3. Đối chiếu log theo `correlation_id` của các request chậm, kiểm tra có timeout/retry kèm theo không.
- Mitigation tạm thời: Giảm `top_k`/phạm vi retrieval, bật cache câu trả lời gần giống, hoặc tăng timeout để tránh lỗi dây chuyền sang panel Errors.
- Owner: Tracing & Prompt Version (người đọc span), phối hợp Dashboard/SLO & Alert nếu cần đổi threshold.

## Alert 2

- Tên: Elevated Error Rate
- Severity: Critical (lỗi chặn trực tiếp người dùng nhận câu trả lời)
- SLI/SLO liên quan: `error_rate_pct` (objective ≤2%, target 99.5% — `config/slo.yaml`)
- Điều kiện và thời gian duy trì: Error rate vượt ngưỡng cảnh báo (thấp hơn trần SLO 2% để có thời gian phản ứng) duy trì ≥5 phút. *Số chính xác chốt ở bước sau bằng dữ liệu thật.*
- Ảnh hưởng tới người dùng: Request trả lỗi thay vì câu trả lời, mất niềm tin vào tính năng, có thể mất luôn phiên làm việc.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Errors, xem `error_type` breakdown để biết loại lỗi chiếm đa số.
  2. Mở trace của các `request_failed` gần nhất, tìm span raise exception (tool call, LLM call, retrieval...).
  3. Grep log theo `correlation_id` của các request lỗi để đọc message/stack chi tiết.
- Mitigation tạm thời: Bật retry có giới hạn số lần, tạm tắt tool đang lỗi (nếu là sự cố kiểu `tool_fail`), hoặc trả fallback response an toàn thay vì lỗi trực tiếp.
- Owner: Logging & PII (đọc log chi tiết) phối hợp Incident, Report & Demo khi cần điều tra root cause.

## Alert 3

- Tên: Daily Cost Spike
- Severity: Warning (ảnh hưởng ngân sách, không chặn người dùng ngay lập tức)
- SLI/SLO liên quan: `daily_cost_usd` (objective ≤2.5 USD/ngày, target 100% — `config/slo.yaml`)
- Điều kiện và thời gian duy trì: Tốc độ tiêu cost trong cửa sổ ngắn (ví dụ 10-15 phút) vượt tốc độ dự kiến để giữ dưới trần ngày, duy trì liên tục thay vì chỉ 1 lần tăng đột biến. *Số chính xác chốt ở bước sau bằng dữ liệu thật.*
- Ảnh hưởng tới người dùng: Không ảnh hưởng trực tiếp ngay, nhưng có thể dẫn tới việc đội ngũ phải throttle/tắt tính năng đột ngột nếu vượt ngân sách — ảnh hưởng gián tiếp tới trải nghiệm.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Cost/Tokens, xác định thời điểm cost bắt đầu tăng bất thường.
  2. Mở trace của các request cost cao, kiểm tra `tokens_in`/`tokens_out` bất thường hoặc model bị đổi.
  3. Kiểm tra log request tương ứng có prompt/input bất thường (quá dài, lặp lại do retry loop...) không.
- Mitigation tạm thời: Giới hạn tạm `max_tokens`, rate-limit input bất thường, hoặc chuyển tạm sang model rẻ hơn.
- Owner: Dashboard, SLO & Alert (chủ sở hữu threshold cost).
