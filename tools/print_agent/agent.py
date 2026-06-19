"""店內出單機列印代理（XP-N160II / ESC/POS）。

在店內任一台電腦（與 Wi-Fi 印表機同網段）執行。
流程：輪詢雲端待印工作 → 以 ESC/POS 送至印表機 → 回報結果。

安裝：
    pip install requests python-escpos

設定（環境變數）：
    CLOUD_BASE_URL     雲端網址，例如 https://your-app.example.com
    PRINT_AGENT_TOKEN  與後端 settings.PRINT_AGENT_TOKEN 相同的密鑰
    PRINTER_IP         印表機區網 IP（在出單機自我測試頁可印出）
    PRINTER_PORT       預設 9100
    POLL_INTERVAL      輪詢秒數，預設 5
"""

import os
import time

import requests
from escpos.printer import Network

CLOUD_BASE_URL = os.getenv("CLOUD_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
PRINT_AGENT_TOKEN = os.getenv("PRINT_AGENT_TOKEN", "")
PRINTER_IP = os.getenv("PRINTER_IP", "192.168.1.100")
PRINTER_PORT = int(os.getenv("PRINTER_PORT", "9100"))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "5"))

HEADERS = {"X-Print-Token": PRINT_AGENT_TOKEN}
LINE_WIDTH = 32  # 80mm 紙標準字寬


def fetch_pending():
    resp = requests.get(
        f"{CLOUD_BASE_URL}/api/print/pending/", headers=HEADERS, timeout=10
    )
    resp.raise_for_status()
    return resp.json()["data"]["jobs"]


def ack(job_id, success, error=""):
    requests.post(
        f"{CLOUD_BASE_URL}/api/print/{job_id}/ack/",
        headers=HEADERS,
        json={"success": success, "error": error},
        timeout=10,
    )


def print_ticket(job):
    printer = Network(PRINTER_IP, port=PRINTER_PORT, timeout=10)
    try:
        printer.set(align="center", bold=True, width=2, height=2)
        printer.text("絕佳食雞\n")
        printer.set(align="center", bold=True, width=3, height=3)
        printer.text(f"#{job['pickup_code'] or '-'}\n")
        printer.set(align="left", bold=False, width=1, height=1)
        printer.text(f"訂單編號: {job['order_id']}\n")
        printer.text(f"時間: {job['created_at']}\n")
        printer.text(f"電話: {job['customer_phone']}\n")
        if job.get("order_options"):
            printer.text(f"全單: {job['order_options']}\n")
        printer.text("-" * LINE_WIDTH + "\n")
        for item in job["items"]:
            printer.text(f"{item['name']} x{item['amount']}\n")
            if item.get("options"):
                printer.text("  " + " / ".join(item["options"]) + "\n")
        printer.text("-" * LINE_WIDTH + "\n")
        printer.set(align="right", bold=True)
        printer.text(f"合計: ${job['price_total']}\n")
        if job.get("remark"):
            printer.set(align="left", bold=False)
            printer.text(f"備註: {job['remark']}\n")
        printer.cut()
    finally:
        try:
            printer.close()
        except Exception:
            pass


def run_once():
    jobs = fetch_pending()
    for job in jobs:
        try:
            print_ticket(job)
            ack(job["job_id"], True)
            print(f"已列印 job={job['job_id']} 取餐號={job['pickup_code']}")
        except Exception as exc:
            ack(job["job_id"], False, str(exc))
            print(f"列印失敗 job={job['job_id']}: {exc}")


def main():
    if not PRINT_AGENT_TOKEN:
        raise SystemExit("請先設定 PRINT_AGENT_TOKEN 環境變數")
    print(
        f"列印代理啟動：雲端 {CLOUD_BASE_URL}，"
        f"印表機 {PRINTER_IP}:{PRINTER_PORT}，每 {POLL_INTERVAL}s 輪詢一次"
    )
    while True:
        try:
            run_once()
        except Exception as exc:
            print(f"輪詢失敗（稍後重試）: {exc}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
