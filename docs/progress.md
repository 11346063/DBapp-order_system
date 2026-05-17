# Session Progress & Handoff (Entropy Management)

> **Agentic Harness Engineering**: 此檔案做為跨 Session 的持久化記憶區，用於防止 Agent 的「上下文腐敗（Context Rot）」與「毀滅迴圈（Doom loops）」。每次 Session 結束前，Agent 必須更新此檔案。

## Current State
**最後更新**: 2026-05-17
**目前階段**: Phase 10 OrderItemOptions 結構化重構完成; all 119 tests passing (skipped=1)

### Completed
- [x] 部署 Agentic Harness Engineering 機制
- [x] Phase 0: 修正 harness `core.lock` hash 不一致，`audit` 已通過
- [x] Phase 0: 修正 Django 測試探索衝突，`python manage.py test` 已通過 58 tests
- [x] Phase 1: 修正管理者/員工導覽分流，手機版加入直接登出入口
- [x] Phase 1: 成功訊息加上 3 秒自動消失標記與 JS 行為
- [x] Phase 1: 新增導覽與成功訊息回歸測試，`python manage.py test` 已通過 61 tests
- [x] Phase 2: 加入購物車後顯示「繼續點餐 / 查看購物車」回流操作列
- [x] Phase 2: 首次加購不再 reload，改為動態建立/更新購物車 badge
- [x] Phase 2: 購物車頁新增「返回點餐」按鈕，導回首頁點餐
- [x] Phase 2: 修正點餐頁「繼續點餐」按鈕事件綁定
- [x] Phase 2: 手機版商品詳情 offcanvas 修正版面衝突，加入購物車按鈕可見且面板高度為 50vh
- [x] Phase 2: 手機版購物車有品項時，在底部導覽上方顯示購物車提示與數量
- [x] Phase 2: 桌機/平板版購物車有品項時，右下角常駐購物車摘要卡
- [x] Phase 2: 新增/更新回流與導覽 UI 測試，`python manage.py test` 已通過 69 tests
- [x] Phase 3: 統一訂單管理桌機 sidebar 與手機 tab 的 badge 對齊結構
- [x] Phase 3: 報表頁明確傳入 `current_status=None`
- [x] Phase 3: 新增 staff badge 對齊回歸測試，`python manage.py test` 已通過 65 tests
- [x] Phase 4: 新增/編輯品項支援 multipart 圖片上傳
- [x] Phase 4: 開發環境提供 `MEDIA_URL` / `MEDIA_ROOT` 與 media 路由
- [x] Phase 4: 商品卡片與詳情彈窗優先顯示上傳圖片
- [x] Phase 4: 新增圖片上傳與保留原圖回歸測試，`python manage.py test --keepdb` 已通過 73 tests
- [x] Phase 5: 新增 `seed_report_data` management command 產生報表測試訂單
- [x] Phase 5: seed 指令預設重建同一批標記資料，避免重複執行造成資料膨脹
- [x] Phase 5: README 補上報表測試資料產生方式
- [x] Phase 5: 新增報表 seed 回歸測試，`python manage.py test --keepdb` 已通過 76 tests
- [x] Phase 5 follow-up: 員工不再能新增/編輯品項，管理者仍可新增/編輯，員工保留後台與上下架操作
- [x] Phase 5 follow-up: 新增管理者帳號管理頁，可建立顧客/員工/管理者帳號並篩選所有帳號
- [x] Phase 5 follow-up: 手機版付款頁不再顯示浮動購物車提示，避免遮擋確認送出訂單按鈕
- [x] Phase 5 follow-up: 新增權限、帳號管理與付款頁導覽回歸測試，`python manage.py test --keepdb` 已通過 84 tests
- [x] Phase 5 follow-up: 管理者帳號管理篩選列改成 segmented control 樣式，選中項目使用黃色狀態與數量徽章
- [x] Phase 5 follow-up: 訂單狀態更新 API 回傳最新狀態數字，前端完成/取消/恢復後留在原頁並同步 badge
- [x] Phase 5 follow-up: 訂單狀態更新改用 Bootstrap 確認彈窗，取代瀏覽器原生 confirm
- [x] Phase 5 follow-up: 手機版購物車頁隱藏浮動購物車提示，總金額/前往付款列固定在底部導覽上方
- [x] Phase 5 follow-up: 手機版結帳頁重新整理為訂單明細、顧客資訊、訪客提示、浮動總金額/確認送出列；`payment.css` 已升版至 `?v=8`
- [x] Phase 5 follow-up: 相關局部測試已通過：`test_staff_navigation`、`test_account_management`、`test_cart_feedback`、`test_navigation_messages`、`test_payment_guest`
- [x] HTML component extraction: 將購物車、付款、歷史訂單、登入/註冊欄位、商品詳情彈窗、後台導覽/訂單卡/帳號列表/報表卡拆成可重用 includes；`python manage.py test --keepdb` 已通過 87 tests，harness audit 已通過
- [x] Staff-assisted phone ordering: 員工/管理員可使用前台點餐、購物車與付款流程；員工代客送單需填客人電話並寫入 `Order.customer_phone`，後台訂單卡顯示電話客人與電話；`python manage.py test --keepdb` 已通過 96 tests
- [x] Staff-assisted ordering separation: 新增 `/staff/assisted-ordering/` 代客點餐頁，員工/管理者菜單管理頁不再混入加入購物車操作；代客頁只顯示上架品項與點餐流程，購物車返回點餐會導回代客頁；`python manage.py test --keepdb` 已通過 99 tests
- [x] Guest/staff ordering CSRF fix: 首頁與代客點餐頁使用 `ensure_csrf_cookie`，確保訪客 AJAX 加入購物車會有 `csrftoken`；新增訪客首頁 CSRF cookie 回歸測試；`python manage.py test --keepdb` 已通過 100 tests
- [x] UI skill package: 新增專案本地 Codex skill `.codex/skills/getdesign-ui-starter`，用於專案初期產出 getdesign.md 風格的 `DESIGN.md` UI 規範、文案、色彩 token、按鈕/輸入框/元件樣式與 QA checklist；`quick_validate.py` 已通過，harness audit 已通過
- [x] UI skill package format revision: 依使用者提供的 getdesign.md Figma alpha 範例，將 `.codex/skills/getdesign-ui-starter` 修正為「YAML token front matter + markdown narrative」格式，強制包含 `version/name/description/colors/typography/rounded/spacing/components` 與 Overview、Colors、Typography、Layout、Components、Responsive、Known Gaps 等章節；`quick_validate.py` 已通過
- [x] Phase 6: 新增忘記密碼流程，使用 Django password reset views 搭配專案自訂 `AccountPasswordResetForm` 避免自訂 User model 缺少 `is_active` 欄位造成內建表單查詢失敗；登入頁新增忘記密碼入口，完成申請、寄信、設定新密碼與完成頁模板；`python manage.py test --keepdb` 已通過 105 tests
- [x] Phase 6 email backend fix: 忘記密碼信件不再預設輸出到 terminal，`EMAIL_BACKEND` 改為 SMTP backend，新增 `EMAIL_HOST`、`EMAIL_PORT`、`EMAIL_USE_TLS`、`EMAIL_HOST_USER`、`EMAIL_HOST_PASSWORD`、`DEFAULT_FROM_EMAIL` 環境變數；本機 `.env` 已補 Gmail SMTP 欄位但仍需填入 Gmail App Password；`python manage.py check` 與 `python manage.py test web_app.tests.test_password_reset --keepdb` 已通過
- [x] Phase 7 Django feature requirements: 依使用者要求先跳過 Google 登入，新增功能規劃文件 `docs/2026-05-14-phase-7-django-features.md`；完成 Request/Response demo endpoint、購物車 JSON API 例外處理 decorator、首頁/代客點餐搜尋與分頁、Order 建立 signal logging、Django i18n 基礎設定與首頁模板翻譯標記；`python manage.py test --keepdb` 已通過 115 tests
- [x] Phase 8 DRF + JWT migration: 導入 `djangorestframework`、`djangorestframework-simplejwt`、`drf-spectacular`；新增 `web_app/api/` 模組（utils、permissions、serializers、views、urls）；統一回應格式 `{"status", "message", "data"}`；自訂 `IsEmployee`/`IsAdmin` 權限類對應 identity 欄位；11 個舊 JsonResponse view 全數改寫為 DRF APIView；整合 JWT + SessionAuthentication 雙軌並行；新增 Swagger UI（`/api/docs/`）、ReDoc（`/api/redoc/`）、OpenAPI schema（`/api/schema/`）；前端 JS 同步更新 API 路徑與回應格式解析；修正測試預期行為（401 vs 302、data 包裝層）；`python manage.py test --keepdb` 已通過 119 tests（skipped=1）

- [x] Phase 8 patch (2026-05-16): 新增 `/api/openapi.json` 端點（`OpenApiJsonRenderer`，永遠回傳 JSON）；根目錄產出靜態 `openapi.json`；修正 `CartAddSerializer.price` 誤設 `default=80` 造成缺少 price 時仍回傳 200 的 bug；`python manage.py test --keepdb` 已通過 119 tests

- [x] Phase 9 雞排切法 + 結帳辣度/加料選項 (2026-05-17):
  - **切法選項**：`detail.js` 對「炸雞排」「碳烤香雞排」「烤雞排」注入「切/不切」radio（無預選，必填）；加入購物車前若未選則顯示紅字錯誤阻擋送出；選項隨 cart options 儲存（id=0 偽選項）並顯示於購物車/付款明細
  - **結帳頁辣度選擇**：`payment_submit_card.html` 加入辣度 radio（不辣/小辣/中辣/大辣），辣度**永遠**寫入 order.remark（即使選不辣也記錄）
  - **結帳頁加料步進器**：加蒜頭、加九層塔各有 +/− 步進器（最小 0 份），每份 +$10；JS 即時更新顯示總金額；金額寫入 `price_total`，份數寫入 remark（如「加蒜頭x2」）
  - **後台訂單卡**：remark 改為黃色左邊框區塊；品項旁顯示 `（切）`/`（不切）` 等選項文字
  - **OrderItem.notes 欄位**：新增 migration `0010_orderitem_notes`；`order_submit()` 將 cart item options 組成字串存入 `OrderItem.notes`
  - **代客點餐切法支援**：`assisted_ordering` 頁面改為 include 完整 `item_detail_modal.html`；雞排品項按 + 開 modal（顯示切法）；按 − 呼叫新 API `POST /api/cart/remove-by-menu/`（依 menu_id 刪最後一筆）；加入成功後同步更新卡片計數
  - **新 API 端點**：`CartRemoveByMenuAPIView` + `CartRemoveByMenuSerializer`；URL：`/api/cart/remove-by-menu/`
  - **CSS 調整**：`payment.css` 加入 `.spicy-options`、`.spicy-opt`、`.extra-row`、`.extra-ctrl`、`.extra-qty-btn`、`.extra-price`、`.payment-total-row` 自訂 class；移除手機版 `d-flex: block !important` 破壞性覆寫；`padding-bottom: 88px` 確保送出按鈕不被底部導覽遮蓋
  - **靜態檔版本**：`detail.js?v=11`、`payment.js?v=2`、`payment.css?v=10`、`detail.css?v=11`
  - `python manage.py test --keepdb` 已通過 119 tests（skipped=1）

- [x] Phase 10 OrderItemOptions 結構化重構 (2026-05-17):
  - **Schema 修改**：`OrderItemOptions` 新增 `order_item`（nullable FK → OrderItem）、`order` 改為 nullable、移除 `unique_together`；`OrderItem.notes` 欄位移除
  - **Migration 0011**：Schema 變更（含移除 notes 欄位）
  - **Migration 0012**：資料遷移，建立 Options 種子（辣度/加蒜/九層塔/切）及 OptGroup 關聯（炸雞排/碳烤香雞排/烤雞排 → 切）
  - **payment.py 重構**：order_submit 改寫；切法寫入 `OrderItemOptions.order_item`；辣度/加蒜/九層塔寫入 `OrderItemOptions.order`；移除 remark 拼接邏輯
  - **detail.js 重構**：切法 radio 改從 `data.options`（OptGroup 真實 ID）驅動，不再 hardcode item 名稱；選項加入 `level` 欄位（0=不切, 1=切）
  - **staff.py**：`staff_order_list` 改用 `prefetch_related`，附加 `order.order_opts`（格式化的 order-level 選項字串）
  - **order_card.html**：移除 `item.notes` 顯示；改讀 `item.orderitemoptions_set.all` 顯示切法；order-level 選項（辣度/加蒜/九層塔）從 `order.order_opts` 顯示，舊訂單 fallback 讀 `order.remark`
  - **測試修正**：`test_home_view.py` 移除與 Phase 9 modal 行為矛盾的 `assertNotContains(response, "加入購物車")`
  - `python manage.py test --keepdb` 已通過 119 tests（skipped=1）

### In Progress
- [ ] Google 登入仍暫停；後續可視需求回到 OAuth dependency 評估
- [ ] 購物車 DB model 化（Cart model）：目前購物車存 Django session，JWT 客戶端（React/App）需同時帶 session cookie；若未來接純 JWT 前端，需將 cart 改為 DB model（Phase 10 預留）

### Next Session Goals / Handoff Notes
- Phase 6 已完成：註冊流程的 email 仍維持選填以相容既有資料；忘記密碼只會寄給已綁定 email 且 `status=True`、可用密碼的帳號，未知 email 仍導向同一完成頁避免洩漏帳號存在與否。
- Phase 6 SMTP 注意：若使用 Gmail，`EMAIL_HOST_PASSWORD` 必須填 Google 帳號的 App Password；未填時 Django 會嘗試 SMTP 發信但會被 Gmail 拒絕。
- Google 登入後續若恢復：需先確認是否接受新增 `django-allauth` 或其他 OAuth dependency，並準備 Google OAuth Client ID / Secret 與 callback URL。
- Phase 7 Django feature requirements 本輪新增/修改包含：`docs/2026-05-14-phase-7-django-features.md`、`order_system/settings.py`、`order_system/urls.py`、`web_app/apps.py`、`web_app/exceptions.py`、`web_app/signals.py`、`web_app/views/request_response.py`、`web_app/views/home.py`、`web_app/views/cart.py`、`web_app/urls.py`、`web_app/templates/home.html`、`web_app/templates/includes/components/menu_search.html`、`web_app/templates/includes/components/pagination.html`、`web_app/static/css/home.css`、`web_app/tests/test_django_feature_requirements.py`。
- Phase 2/3 後續修正包含：`order_system/settings.py`、`web_app/templates/base.html`、`web_app/templates/home.html`、`web_app/templates/includes/bottom_nav.html`、`web_app/templates/item_detail_modal.html`、`web_app/static/css/base.css`、`web_app/static/css/detail.css`、`web_app/static/js/detail.js`、`web_app/tests/test_cart_feedback.py`、`web_app/tests/test_navigation_messages.py`、`web_app/templates/staff/base_staff.html`、`web_app/static/css/staff.css`、`web_app/views/staff.py`、`web_app/tests/test_staff_navigation.py`、`docs/progress.md`。
- Phase 4 本輪新增/修改包含：`web_app/views/menu_manage.py`、`web_app/views/home.py`、`order_system/settings.py`、`order_system/urls.py`、`web_app/templates/staff_menu_modal.html`、`web_app/templates/includes/item_card.html`、`web_app/templates/item_detail_modal.html`、`web_app/static/js/base.js`、`web_app/static/js/detail.js`、`web_app/static/js/staff_menu.js`、`web_app/static/css/detail.css`、`web_app/tests/test_menu_create.py`、`web_app/tests/test_menu_edit.py`。
- Phase 5 本輪新增/修改包含：`web_app/management/__init__.py`、`web_app/management/commands/__init__.py`、`web_app/management/commands/seed_report_data.py`、`web_app/tests/test_seed_report_data.py`、`README.md`、`docs/progress.md`。
- Phase 5 follow-up 本輪新增/修改包含：`web_app/forms/register_form.py`、`web_app/views/home.py`、`web_app/views/menu_manage.py`、`web_app/views/staff.py`、`web_app/urls.py`、`web_app/templates/home.html`、`web_app/templates/item_detail_modal.html`、`web_app/templates/includes/navbar.html`、`web_app/templates/includes/bottom_nav.html`、`web_app/templates/staff/base_staff.html`、`web_app/templates/staff/account_management.html`、`web_app/static/css/staff.css`、`web_app/tests/test_account_management.py`、`web_app/tests/test_home_view.py`、`web_app/tests/test_menu_create.py`、`web_app/tests/test_menu_edit.py`、`web_app/tests/test_navigation_messages.py`。
- 本 session 後續 UI 修正包含：`web_app/static/js/staff.js`、`web_app/templates/staff/order_list.html`、`web_app/templates/staff/base_staff.html`、`web_app/static/css/staff.css`、`web_app/static/css/cart.css`、`web_app/templates/cart.html`、`web_app/static/css/payment.css`、`web_app/templates/payment.html`、`web_app/tests/test_staff_navigation.py`、`web_app/tests/test_cart_feedback.py`、`web_app/tests/test_payment_guest.py`、`web_app/tests/test_navigation_messages.py`。
- 下次接續注意：前端靜態檔多次因瀏覽器快取未即時反映而需要升版 query string；目前 `staff.js` 為 `?v=4`、`cart.css` 為 `?v=2`、`payment.css` 為 `?v=8`。
- 本 session HTML 元件化新增/修改包含：`web_app/templates/includes/components/form_field.html`、`cart_item.html`、`cart_total_footer.html`、`payment_order_summary.html`、`customer_info_card.html`、`guest_login_prompt.html`、`payment_submit_card.html`、`order_history_card.html`、`item_detail_media.html`、`quantity_controls.html`、`item_customer_actions.html`、`item_staff_actions.html`、`web_app/templates/includes/staff/status_nav_link.html`、`admin_nav_link.html`、`order_card.html`、`account_filter_group.html`、`account_table_row.html`、`order_status_confirm_modal.html`、`report_chart_card.html`，並更新對應頁面引用。
- Staff-assisted phone ordering 本輪新增/修改包含：`web_app/models/order.py`、`web_app/migrations/0009_order_customer_phone.py`、`web_app/views/cart.py`、`web_app/views/payment.py`、`web_app/templates/includes/navbar.html`、`web_app/templates/includes/bottom_nav.html`、`web_app/templates/item_detail_modal.html`、`web_app/templates/payment.html`、`web_app/templates/includes/components/customer_info_card.html`、`web_app/templates/includes/components/payment_submit_card.html`、`web_app/templates/includes/staff/order_card.html`、`web_app/static/js/detail.js`、`web_app/tests/test_cart_feedback.py`、`web_app/tests/test_payment_guest.py`、`web_app/tests/test_staff_navigation.py`、`web_app/tests/test_navigation_messages.py`。
- Staff-assisted ordering separation 本輪新增/修改包含：`web_app/views/home.py`、`web_app/urls.py`、`web_app/views/cart.py`、`web_app/templates/cart.html`、`web_app/templates/home.html`、`web_app/templates/item_detail_modal.html`、`web_app/templates/includes/navbar.html`、`web_app/templates/includes/bottom_nav.html`、`web_app/tests/test_home_view.py`、`web_app/tests/test_cart_feedback.py`、`web_app/tests/test_navigation_messages.py`。
- Guest/staff ordering CSRF fix 本輪新增/修改包含：`web_app/views/home.py`、`web_app/tests/test_cart_feedback.py`。
- UI skill package 本輪新增/修改包含：`.codex/skills/getdesign-ui-starter/SKILL.md`、`.codex/skills/getdesign-ui-starter/agents/openai.yaml`、`.codex/skills/getdesign-ui-starter/references/design-md-template.md`、`.codex/skills/getdesign-ui-starter/references/ui-system-checklist.md`、`docs/progress.md`。
- UI skill format revision 本輪新增/修改包含：`.codex/skills/getdesign-ui-starter/SKILL.md`、`.codex/skills/getdesign-ui-starter/references/design-md-template.md`、`.codex/skills/getdesign-ui-starter/references/ui-system-checklist.md`、`docs/progress.md`。
- Phase 6 本輪新增/修改包含：`web_app/forms/password_reset_form.py`、`web_app/urls.py`、`order_system/settings.py`、`web_app/templates/auth/login.html`、`web_app/templates/auth/password_reset.html`、`web_app/templates/auth/password_reset_done.html`、`web_app/templates/auth/password_reset_confirm.html`、`web_app/templates/auth/password_reset_complete.html`、`web_app/templates/auth/password_reset_email.html`、`web_app/templates/auth/password_reset_subject.txt`、`web_app/tests/test_password_reset.py`、`docs/progress.md`。
- Phase 6 email backend fix 本輪新增/修改包含：`order_system/settings.py`、`sample.env`、`.env`、`docs/progress.md`。
- Phase 8 DRF + JWT 本輪新增/修改包含：`requirements.txt`、`order_system/settings.py`、`order_system/urls.py`、`web_app/api/__init__.py`、`web_app/api/utils.py`、`web_app/api/permissions.py`、`web_app/api/serializers/__init__.py`、`web_app/api/serializers/menu.py`、`web_app/api/serializers/cart.py`、`web_app/api/serializers/order.py`、`web_app/api/views/__init__.py`、`web_app/api/views/menu.py`、`web_app/api/views/cart.py`、`web_app/api/views/order.py`、`web_app/api/urls.py`、`web_app/urls.py`、`web_app/views/home.py`、`web_app/views/cart.py`、`web_app/views/staff.py`、`web_app/views/order_history.py`、`web_app/static/js/base.js`、`web_app/static/js/detail.js`、`web_app/static/js/cart.js`、`web_app/static/js/staff.js`、`web_app/static/js/staff_menu.js`、`web_app/static/js/order_history.js`、`web_app/tests/test_menu_toggle.py`、`web_app/tests/test_menu_create.py`、`web_app/tests/test_menu_edit.py`、`web_app/tests/test_cart_feedback.py`、`web_app/tests/test_staff_navigation.py`、`web_app/tests/test_django_feature_requirements.py`、`.git/hooks/pre-commit`（pytest → manage.py test）、`docs/progress.md`。
- Phase 9 本輪新增/修改包含：`web_app/static/js/detail.js`（?v=11）、`web_app/static/css/detail.css`（?v=11）、`web_app/static/js/payment.js`（?v=2）、`web_app/static/css/payment.css`（?v=10）、`web_app/templates/payment.html`、`web_app/templates/includes/components/payment_submit_card.html`、`web_app/templates/includes/staff/order_card.html`、`web_app/templates/home.html`（modal include 修正）、`web_app/models/order_item.py`、`web_app/migrations/0010_orderitem_notes.py`、`web_app/views/payment.py`、`web_app/api/serializers/cart.py`（新增 CartRemoveByMenuSerializer）、`web_app/api/views/cart.py`（新增 CartRemoveByMenuAPIView）、`web_app/api/urls.py`（新增 `/api/cart/remove-by-menu/`）、`web_app/tests/test_cart_feedback.py`（更新測試說明）、`docs/progress.md`。
- Phase 9 接續注意：靜態檔目前版本：`detail.js?v=11`、`payment.js?v=2`、`payment.css?v=10`、`detail.css?v=11`、`staff.js?v=4`、`cart.css?v=2`；代客點餐頁雞排按 + 開 modal、按 − 呼叫 `/api/cart/remove-by-menu/`；`OrderItem.notes` 儲存品項選項字串（含切法）；辣度永遠寫入 remark 以供後台確認。
