# Session Progress & Handoff (Entropy Management)

> **Agentic Harness Engineering**: 此檔案做為跨 Session 的持久化記憶區，用於防止 Agent 的「上下文腐敗（Context Rot）」與「毀滅迴圈（Doom loops）」。每次 Session 結束前，Agent 必須更新此檔案。

## Current State
**最後更新**: 2026-04-29
**目前階段**: Guest/staff ordering CSRF flow fixed; full test suite passed; ready for user review and Phase 6 planning

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

### In Progress
- [ ] 等待使用者 commit 後進入 Phase 6：新增忘記密碼流程

### Next Session Goals / Handoff Notes
- Phase 6 目標：新增忘記密碼流程，需先確認 email 欄位是否在註冊流程中必填或補救既有無 email 帳號。
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
