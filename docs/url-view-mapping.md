# URL Patterns 與 Views 功能對照表

> 更新：2026-06-23  
> 對應檔案：`order_system/urls.py`、`web_app/urls.py`、`web_app/api/urls.py`

---

## 一、Web UI（HTML 頁面）

| URL Pattern | View Function / Class | 權限 | 功能說明 |
|-------------|----------------------|------|---------|
| `/` | `home_view` | 全部 | 首頁菜單列表；訪客可瀏覽，登入可加購物車 |
| `/staff/assisted-ordering/` | `assisted_ordering_view` | E / A | 員工代客點餐 POS 介面（雙欄，直接建立已接單訂單） |
| `/cart/` | `cart_view` | 全部 | 購物車頁；顯示品項、數量、小計；支援價格異動提示 |
| `/payment/` | `payment_view` | 全部 | 結帳確認頁；顯示訂單摘要與聯絡電話欄位 |
| `/order/submit/` | `order_submit` | 全部 | POST：送出訂單，建立 Order；檢查營業時間/今日售完 |
| `/order/<pk>/waiting/` | `order_waiting_view` | 全部 | 訂單等待確認頁；每 3 秒 polling 等待員工接單 |
| `/orders/` | `order_history_view` | C / A | 顧客歷史訂單列表；含訂單狀態、取餐號碼、拒單原因 |
| `/profile/` | `profile_view` | C | 個人資料編輯（姓名、Email、地址） |
| `/login/` | `login_view` | 未登入 | 手機號碼 + 密碼 + CAPTCHA 登入；支援 Google OAuth |
| `/register/` | `register_view` | 未登入 | 以手機號碼註冊顧客帳號 |
| `/logout/` | `logout_view` | 已登入 | 登出並清除 session |
| `/oauth/google/` | `google_oauth_initiate` | 未登入 | 發起 Google OAuth 2.0 授權流程 |
| `/oauth/google/callback/` | `google_oauth_callback` | — | Google OAuth 回呼；建立/連結帳號 |
| `/oauth/phone-required/` | `oauth_phone_required` | 已登入（無電話） | Google 登入後補填手機號碼 |
| `/password-reset/` | `PasswordResetView` | 未登入 | 忘記密碼：輸入 Email 或手機號碼 |
| `/password-reset/done/` | `PasswordResetDoneView` | — | 發送重設信件完成提示頁 |
| `/password-reset/<uidb64>/<token>/` | `PasswordResetConfirmView` | — | 點擊郵件連結後設定新密碼 |
| `/password-reset/complete/` | `PasswordResetCompleteView` | — | 密碼重設完成頁 |
| `/staff/orders/` | `staff_order_list` | E / A | 後台訂單管理（看板視圖：等待/備餐/可取餐三欄） |
| `/staff/report/` | `staff_report` | E / A | 後台報表（日期區間銷售、熱銷排行、日結概覽） |
| `/staff/report/export/` | `staff_report_export` | E / A | CSV 匯出報表（UTF-8 BOM） |
| `/staff/accounts/` | `account_management` | A | 帳號管理（新增/停用員工與管理員帳號） |
| `/staff/settings/` | `staff_settings_view` | A | 系統設定（加料單價、選項名稱、營業時間） |
| `/type/create/` | `typeCreate` | A | 建立菜單分類 |

**權限說明**：`A` = 管理員、`E` = 員工、`C` = 顧客、全部 = 未登入訪客也可存取

---

## 二、RESTful API（DRF）

### 認證 & 文件（`order_system/urls.py`）

| URL Pattern | View / Class | HTTP Method | 功能說明 |
|-------------|-------------|-------------|---------|
| `/api/token/` | `TokenObtainPairView` | POST | 取得 JWT access + refresh token |
| `/api/token/refresh/` | `TokenRefreshView` | POST | 以 refresh token 換發新 access token |
| `/api/schema/` | `SpectacularAPIView` | GET | OpenAPI YAML schema |
| `/api/openapi.json` | `SpectacularAPIView` | GET | OpenAPI JSON schema |
| `/api/docs/` | `SpectacularSwaggerView` | GET | Swagger UI 互動文件 |
| `/api/redoc/` | `SpectacularRedocView` | GET | ReDoc 閱讀型文件 |
| `/captcha/` | `captcha.urls` | GET/POST | CAPTCHA 圖片生成與驗證 |
| `/i18n/` | `django.conf.urls.i18n` | POST | Django 語言切換（`set_language`） |

### 菜單 API（`/api/menu/...`）

| URL Pattern | View Class | HTTP Method | 權限 | 功能說明 |
|-------------|------------|-------------|------|---------|
| `/api/menu/<pk>/` | `MenuDetailAPIView` | GET | 全部 | 取得單一菜單品項詳細資訊（含選項） |
| `/api/menu/<pk>/toggle/` | `MenuToggleAPIView` | PATCH | E / A | 切換品項上架/下架狀態 |
| `/api/menu/<pk>/edit/` | `MenuUpdateAPIView` | PATCH | E / A | 更新品項資訊（名稱、價格、圖片） |
| `/api/menu/<pk>/sold-out-today/` | `MenuSoldOutTodayAPIView` | POST | E / A | 標記/取消今日售完 |
| `/api/menu/create/` | `MenuCreateAPIView` | POST | A | 建立新菜單品項 |

### 購物車 API（`/api/cart/...`）

| URL Pattern | View Class | HTTP Method | 權限 | 功能說明 |
|-------------|------------|-------------|------|---------|
| `/api/cart/` | `CartDetailAPIView` | GET | 全部 | 取得目前購物車內容 |
| `/api/cart/add/` | `CartAddAPIView` | POST | 全部 | 加入品項至購物車（含選項） |
| `/api/cart/adjust/` | `CartAdjustAPIView` | POST | 全部 | 以 `menu_id` + `delta` 相對增減數量（菜單頁用） |
| `/api/cart/update/` | `CartUpdateAPIView` | POST | 全部 | 以陣列 index 直接設定絕對數量（購物車頁用） |
| `/api/cart/remove/` | `CartRemoveAPIView` | POST | 全部 | 移除指定 index 品項 |
| `/api/cart/remove-by-menu/` | `CartRemoveByMenuAPIView` | POST | 全部 | 以 `menu_id` 移除購物車內所有該品項 |
| `/api/cart/validate-prices/` | `CartValidatePricesAPIView` | GET | 全部 | 比對購物車與最新 DB 價格，回傳異動品項 |
| `/api/cart/sync-prices/` | `CartSyncPricesAPIView` | POST | 全部 | 將購物車價格同步為最新 DB 價格 |

### 訂單 API（`/api/orders/...`）

| URL Pattern | View Class | HTTP Method | 權限 | 功能說明 |
|-------------|------------|-------------|------|---------|
| `/api/orders/<pk>/status/` | `OrderStatusAPIView` | PATCH | E / A | 更新訂單狀態（含狀態機白名單驗證） |
| `/api/orders/<pk>/ready/` | `OrderReadyAPIView` | POST | E / A | 通知顧客取餐（ACCEPTED → READY） |
| `/api/orders/<pk>/accept/` | `OrderAcceptAPIView` | POST | E / A | 接受訂單（SUBMITTED → ACCEPTED，輸入等待時間） |
| `/api/orders/<pk>/payment/` | `OrderPaymentAPIView` | POST | E / A | 記錄收款（冪等；僅 ACCEPTED/READY/COMPLETED 可收款） |
| `/api/orders/<pk>/customer-status/` | `OrderCustomerStatusAPIView` | GET | C / 訪客 | 顧客查詢訂單狀態（等待頁 polling 用） |
| `/api/orders/<pk>/customer-cancel/` | `CustomerCancelOrderAPIView` | POST | C / 訪客 | 顧客取消尚未接單的訂單（SUBMITTED 才可） |
| `/api/orders/<pk>/reprint/` | `OrderReprintAPIView` | POST | E / A | 重印訂單出單（建立新 PrintJob） |
| `/api/orders/reorder/` | `ReorderAPIView` | POST | C | 再次訂購（複製歷史訂單品項至購物車） |
| `/api/v1/orders/staff/` | `StaffOrderCreateAPIView` | POST | E / A | 代客點餐直接建立已接單訂單（不經購物車） |

### 出單機列印 API（`/api/print/...`）

| URL Pattern | View Class | HTTP Method | 權限 | 功能說明 |
|-------------|------------|-------------|------|---------|
| `/api/print/pending/` | `PrintPendingAPIView` | GET | Print Token | 出單機代理拉取待列印的 PrintJob |
| `/api/print/<pk>/ack/` | `PrintAckAPIView` | POST | Print Token | 出單機代理確認指定 PrintJob 已列印完成 |

---

## 三、REST 資源設計說明

### URL 命名原則

本系統 RESTful API 遵循以下設計原則：

| 原則 | 說明 | 範例 |
|------|------|------|
| **資源名稱用複數名詞** | URL 以名詞描述資源，不含動詞 | `/api/orders/`、`/api/menu/` |
| **動作用 HTTP Method 區分** | GET 讀取、POST 建立、PATCH 更新、DELETE 刪除 | `PATCH /api/menu/<pk>/toggle/` |
| **子資源動作用巢狀路徑** | 狀態變更等動作作為子路徑 | `/api/orders/<pk>/accept/`、`/api/orders/<pk>/payment/` |
| **版本以路徑前綴標示** | 需要版本管控的端點加 `/v1/` 前綴 | `/api/v1/cart/`、`/api/v1/orders/staff/` |
| **統一回應格式** | 所有 API 回傳 `{"status", "message", "data"}` | - |

### Web UI vs RESTful API 分工

```
Web UI（Template Views）      RESTful API（DRF APIView）
─────────────────────         ──────────────────────────
渲染 HTML 頁面                  回傳 JSON 資料
Session 認證                   JWT / Session 雙模式認證
完整表單送出                    前端 AJAX / 外部系統呼叫
頁面導向（redirect）             無狀態（每次帶 token）
```

### 身份權限對照

| identity | 說明 | 可呼叫 API 範圍 |
|----------|------|--------------|
| `A`（管理員） | 最高權限 | 全部端點 |
| `E`（員工） | 操作訂單與餐點 | 菜單切換/售完、訂單狀態、收款、代客點餐、列印 |
| `C`（顧客） | 一般使用者 | 購物車、訂單查詢/取消、再次訂購 |
| 未登入（訪客） | `G` | 購物車（session）、訂單狀態查詢（token-less） |
| Print Agent | X-Print-Token | 出單機列印代理端點 |
