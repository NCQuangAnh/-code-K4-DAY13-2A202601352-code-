# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`:
- Tổng số traces:
- Số PII leak còn lại:
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- Evidence correlation ID:
- Evidence PII redaction:
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract.`
- Evidence dashboard: `submission/evidence/p3-dashboard-baseline.png`, `p3-dashboard-baseline1.png` (baseline, 6 panel + threshold badge). *Cần bổ sung ảnh chụp lúc incident (`rag_slow`) cho thấy panel Latency vượt threshold — chưa có do chưa chụp màn hình runtime.*
- SLO đã chọn và lý do (`config/slo.yaml`): `latency_p95_ms` ≤3000ms, `error_rate_pct` ≤2%, `daily_cost_usd` ≤2.5, `quality_score_avg` ≥0.75 — giữ nguyên 4 SLI mặc định vì đã bao phủ đủ 3 khía cạnh (trải nghiệm, tin cậy, chi phí) cho một app chat có mock LLM; không hạ thấp target vì baseline đo được còn cách xa trần rất nhiều (P95 158ms, error 0%, quality 0.88, cost $0.08/60'), đủ dư địa cảnh báo sớm trước khi vi phạm SLO thật.
- Alert rules và runbook (`config/alert_rules.yaml` + `docs/alerts.md`): 3 alert symptom-based, mỗi alert map 1 kịch bản practice để kiểm chứng bằng dữ liệu thật thay vì số đoán:
  - `high_p95_latency`: P95 >1000ms, 2 lần refresh (~1 phút). Baseline 158ms → đo được 2665.7ms khi bật `inject_incident.py --scenario rag_slow`.
  - `elevated_error_rate`: error rate >1%, 2 lần refresh. Baseline 0% → đo được 100% (cô lập) / 14.3% (cả cửa sổ) khi bật `--scenario tool_fail`.
  - `cost_per_request_spike`: cost trung bình >$0.005/request, 2 lần refresh. Baseline $0.0019 → đo được $0.0077 (4.02x) khi bật `--scenario cost_spike`. Đổi từ ngưỡng tổng $/60 phút sang trung bình/request vì tổng không đủ nhạy ở traffic thấp của lab (đo thật chỉ đạt $0.18/60' dù có spike).
  - Runbook đầy đủ (ảnh hưởng người dùng, 3 bước kiểm tra, mitigation, owner) cho từng alert nằm trong `docs/alerts.md`.

## 6. Điều tra challenge

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| | | | |
