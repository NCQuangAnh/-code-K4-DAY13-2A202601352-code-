"""Streamlit runtime dashboard cho Day 13 — đọc data/logs.jsonl và vẽ đúng 6 panel
theo contract trong config/dashboard.yaml. Chạy: streamlit run scripts/dashboard_app.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"
DASHBOARD_CONFIG_PATH = REPO_ROOT / "config" / "dashboard.yaml"


def load_config() -> dict:
    payload = yaml.safe_load(DASHBOARD_CONFIG_PATH.read_text(encoding="utf-8"))
    return payload["dashboard"]


def load_logs() -> pd.DataFrame:
    records = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    df["ts"] = pd.to_datetime(df["ts"])
    return df


def percentile(series: pd.Series, p: int) -> float:
    if series.empty:
        return 0.0
    return float(series.quantile(p / 100))


def threshold_badge(value: float, threshold: dict) -> str:
    op = threshold["operator"]
    limit = threshold["value"]
    ok = value <= limit if op == "lte" else value >= limit
    return "🟢 đạt" if ok else "🔴 vi phạm"


def main() -> None:
    st.set_page_config(page_title="Day 13 AI Observability", layout="wide")
    config = load_config()

    st.title(config["title"])

    time_range_minutes = config["time_range_minutes"]
    refresh_seconds = config["refresh_seconds"]
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=time_range_minutes)

    st.caption(
        f"Time range: {time_range_minutes} phút (từ {window_start:%H:%M:%S} đến {now:%H:%M:%S} UTC) "
        f"· refresh mỗi {refresh_seconds}s"
    )

    df = load_logs()
    if df.empty:
        st.warning("Chưa có log nào trong data/logs.jsonl. Chạy `python scripts/load_test.py` trước.")
        return

    df = df[df["ts"] >= window_start]
    panels = {p["id"]: p for p in config["panels"]}

    responses = df[df["event"] == "response_sent"]
    requests_ = df[df["event"] == "request_received"]
    failures = df[df["event"] == "request_failed"]

    col1, col2, col3 = st.columns(3)

    # --- Latency ---
    with col1:
        p = panels["latency"]
        st.subheader(f"{p['title']} ({p['unit']})")
        if not responses.empty:
            p50 = percentile(responses["latency_ms"], 50)
            p95 = percentile(responses["latency_ms"], 95)
            p99 = percentile(responses["latency_ms"], 99)
            st.metric("P50", f"{p50:.0f} {p['unit']}")
            st.metric("P95", f"{p95:.0f} {p['unit']}", help=f"Threshold: {p['threshold']['operator']} {p['threshold']['value']}")
            st.metric("P99", f"{p99:.0f} {p['unit']}")
            st.caption(f"Threshold p95 ≤ {p['threshold']['value']}{p['unit']} → {threshold_badge(p95, p['threshold'])}")
            st.line_chart(responses.set_index("ts")["latency_ms"])
        else:
            st.info("Chưa có response_sent")

    # --- Traffic ---
    with col2:
        p = panels["traffic"]
        st.subheader(f"{p['title']} ({p['unit']})")
        count = len(requests_)
        st.metric("Total requests", count)
        if not requests_.empty:
            per_minute = requests_.set_index("ts").resample("1min").size()
            rate = float(per_minute.mean()) if not per_minute.empty else 0.0
            st.caption(f"Threshold rate ≥ {p['threshold']['value']} req/phút → {threshold_badge(rate, p['threshold'])}")
            st.bar_chart(per_minute)
        else:
            st.info("Chưa có request_received")

    # --- Errors ---
    with col3:
        p = panels["errors"]
        st.subheader(f"{p['title']} ({p['unit']})")
        total = len(requests_) + len(failures)
        error_rate_pct = (len(failures) / total * 100) if total else 0.0
        st.metric("Error rate", f"{error_rate_pct:.2f}%")
        st.caption(f"Threshold ≤ {p['threshold']['value']}% → {threshold_badge(error_rate_pct, p['threshold'])}")
        if not failures.empty:
            st.bar_chart(failures["error_type"].value_counts())
        else:
            st.caption("Không có lỗi trong cửa sổ hiện tại")

    col4, col5, col6 = st.columns(3)

    # --- Cost ---
    with col4:
        p = panels["cost"]
        st.subheader(f"{p['title']} ({p['unit']})")
        if not responses.empty:
            total_cost = float(responses["cost_usd"].sum())
            st.metric("Total cost", f"${total_cost:.4f}")
            st.caption(f"Threshold ≤ ${p['threshold']['value']} → {threshold_badge(total_cost, p['threshold'])}")
            cost_by_minute = responses.set_index("ts").resample("1min")["cost_usd"].sum()
            st.bar_chart(cost_by_minute)
        else:
            st.info("Chưa có response_sent")

    # --- Tokens ---
    with col5:
        p = panels["tokens"]
        st.subheader(f"{p['title']} ({p['unit']})")
        if not responses.empty:
            tokens_in = int(responses["tokens_in"].sum())
            tokens_out = int(responses["tokens_out"].sum())
            st.metric("Tokens in", tokens_in)
            st.metric("Tokens out", tokens_out)
            total_tokens = tokens_in + tokens_out
            st.caption(f"Threshold tổng ≤ {p['threshold']['value']} → {threshold_badge(total_tokens, p['threshold'])}")
        else:
            st.info("Chưa có response_sent")

    # --- Quality ---
    with col6:
        p = panels["quality"]
        st.subheader(f"{p['title']} ({p['unit']})")
        if not responses.empty:
            quality_avg = float(responses["quality_score"].mean())
            st.metric("Quality avg", f"{quality_avg:.2f}")
            st.caption(f"Threshold ≥ {p['threshold']['value']} → {threshold_badge(quality_avg, p['threshold'])}")
            st.line_chart(responses.set_index("ts")["quality_score"])
        else:
            st.info("Chưa có response_sent")


if __name__ == "__main__":
    main()
