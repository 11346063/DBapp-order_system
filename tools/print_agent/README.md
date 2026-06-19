# 店內出單機列印代理（XP-N160II）

把雲端訂單系統的「待印工作」送到店內 Wi-Fi 熱感應出單機（芯燁 XP-N160II，ESC/POS）。

## 為什麼需要這個代理

印表機是 Wi-Fi 機、在店內區網（私有 IP）；雲端伺服器在外網**連不進來**。
因此由一支在店內執行、與印表機同網段的小程式「主動連出」雲端輪詢工作，
再於區網內把單據送到印表機。不需在店裡開 port 或申請固定對外 IP。

```
雲端 Django  ──(HTTPS 輪詢, agent 主動連出)──>  本代理(店內 PC)
  產生 PrintJob                                    │ ESC/POS over TCP:9100（區網）
                                                   ▼
                                              XP-N160II 出單
```

## 出單時機

顧客訂單在後台**接單時**自動建立列印工作（此時取餐號已產生）。
後台訂單卡的「印表機」按鈕可**重印**。

## 安裝

在店內電腦（Windows/Mac/Linux 皆可，需與印表機同 Wi-Fi）：

```bash
pip install -r requirements.txt
```

## 設定

1. 後端設定環境變數 `PRINT_AGENT_TOKEN`（任意長亂數），重啟服務。
2. 在出單機按自我測試（通常長按進紙鍵開機）印出機器資訊，取得**印表機 IP**。
3. 代理端設定相同 token 與印表機 IP：

```bash
# Windows PowerShell 範例
$env:CLOUD_BASE_URL="https://your-app.example.com"
$env:PRINT_AGENT_TOKEN="與後端相同的密鑰"
$env:PRINTER_IP="192.168.1.100"
python agent.py
```

| 變數 | 說明 | 預設 |
|------|------|------|
| `CLOUD_BASE_URL` | 雲端網址 | `http://127.0.0.1:8000` |
| `PRINT_AGENT_TOKEN` | 與後端相同的密鑰（必填） | 空 |
| `PRINTER_IP` | 印表機區網 IP | `192.168.1.100` |
| `PRINTER_PORT` | ESC/POS raw port | `9100` |
| `POLL_INTERVAL` | 輪詢秒數 | `5` |

## 對應的後端 API

| 端點 | 方法 | 驗證 | 用途 |
|------|------|------|------|
| `/api/print/pending/` | GET | `X-Print-Token` | 取得待印工作（含單據資料） |
| `/api/print/<id>/ack/` | POST | `X-Print-Token` | 回報列印成功/失敗 |
| `/api/orders/<id>/reprint/` | POST | 員工 JWT | 後台重印按鈕 |

## 疑難排解

- **印不出來**：先 `ping 印表機IP`；確認代理電腦與印表機同網段、port 9100 通。
- **403**：`PRINT_AGENT_TOKEN` 與後端不一致，或後端未設定。
- **中文亂碼**：確認 `python-escpos` 版本，必要時於 `agent.py` 的 `printer.set()` 調整字碼頁。
- **開機自動執行**：Windows 可用工作排程器、Linux 可用 systemd 服務常駐。
```
