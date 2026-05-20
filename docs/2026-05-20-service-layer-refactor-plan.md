# Phase 12 規劃：建立 Service Layer，拆薄 HTML / API Controllers

日期：2026-05-20

## 背景與現況

目前專案在 Phase 8 已導入 Django REST Framework，形成兩組 controller：

- `web_app/views/`：傳統 Django HTML views，負責 render template、redirect、messages。
- `web_app/api/views/`：DRF API views，負責 JSON endpoint、serializer validation、permission_classes、OpenAPI 文件。

這個分法類似 Spring Boot：

| Django 專案 | Spring Boot 類比 | 責任 |
|-------------|------------------|------|
| `web_app/views/` | `@Controller` | HTML 頁面流程 |
| `web_app/api/views/` | `@RestController` | JSON API |
| `web_app/api/serializers/` | DTO + validation | 驗證 request / response 結構 |
| `web_app/api/permissions.py` | Security rule | API 權限規則 |
| `web_app/models/` | Entity + ORM | 資料模型 |
| `web_app/services/` | `@Service` | 業務邏輯 |

目前問題不是 `api/` 和 `views/` 不該分開，而是兩邊 controller 都放了部分業務邏輯，導致架構看起來相近且混雜。

## 目標

新增 `web_app/services/`，把可重用、可測試、與 HTTP 呈現無關的邏輯抽離 controller。

重構後的責任邊界：

```text
web_app/views/         HTML Controllers
web_app/api/views/     REST Controllers
web_app/services/      Business Services
web_app/models/        ORM Models
```

controller 只處理 HTTP 外殼：

- HTML view：`request.POST`、`render()`、`redirect()`、`messages`
- API view：serializer、permission、`api_success()` / `api_error()`

service 處理真正業務規則：

- 操作 session cart
- 計算價格與小計
- 建立訂單與訂單品項
- 寫入 `OrderItemOptions`
- 更新訂單狀態
- 再次訂購
- 權限以外的業務限制

## 建議目錄

```text
web_app/
└── services/
    ├── __init__.py
    ├── cart.py       # session cart 操作與金額計算
    ├── order.py      # 建立訂單、再次訂購、狀態流程
    ├── menu.py       # 菜單上下架、編輯、新增相關 domain logic
    └── authz.py      # 可選：共用 identity 判斷 helper
```

## 盤點結果（2026-05-20）

這次規劃先盤點現有 controller 內的業務邏輯，避免抽象層只是搬家。

| 區塊 | 目前位置 | 需要抽到 service 的邏輯 | 保留在 controller 的邏輯 |
|------|----------|--------------------------|---------------------------|
| Cart | `web_app/api/views/cart.py`、`web_app/views/cart.py` | session cart 讀寫、count / total、加入、加減量、依 index 更新/刪除、依 menu_id 刪最後一筆 | serializer validation、OpenAPI、`api_success/api_error`、template context |
| Checkout / Order create | `web_app/views/payment.py` | 空購物車檢查、代客電話規則、辣度/加料解析、總價計算、建立 `Order` / `OrderItem` / `OrderItemOptions`、清空 cart | `POST` method guard、`messages`、redirect、form 欄位收集 |
| Order status | `web_app/api/views/order.py`、`web_app/views/staff.py` | 更新狀態、狀態數量統計、order-level options 格式化 | API permission、serializer、staff template render |
| Reorder | `web_app/api/views/order.py` | 判斷訂單歸屬、略過已刪除 menu、把歷史品項轉回 cart payload | 登入/身份回應碼、serializer、OpenAPI |
| Menu | `web_app/api/views/menu.py`、`web_app/views/menu_manage.py`、`web_app/views/home.py` | 圖片格式檢查、菜單 payload、create / update / toggle、可見菜單查詢與搜尋 | 權限 decorator / permission、JSON/DRF response 包裝、template render |

### 優先處理的重複點

- `_order_status_counts()` 同時存在 `api/views/order.py` 與 `views/staff.py`。
- `_validate_uploaded_image()` 同時存在 `api/views/menu.py` 與 `views/menu_manage.py`。
- menu create/update 的必填、價格、分類、名稱重複規則在 HTML JSON view 與 DRF API view 重複。
- cart session dict 結構只存在 controller 內，沒有集中契約，未來 Cart DB model 化會比較難切換。

## 分層規則

### `web_app/views/`

只放 HTML 頁面流程：

- 回傳 `render(...)`
- 成功或失敗後 `redirect(...)`
- 使用 `django.contrib.messages`
- 組 template context
- 呼叫 service，不直接承擔複雜業務規則

### `web_app/api/views/`

只放 API 流程：

- `APIView`
- `permission_classes`
- serializer validation
- OpenAPI schema (`extend_schema`)
- 呼叫 service
- 包裝 JSON response

### `web_app/services/`

只放業務邏輯：

- 不回傳 `render()` / `redirect()`
- 不使用 `messages`
- 不直接依賴 DRF `Response`
- 可以接收 `request.session`、`user`、validated data、model instance
- 回傳 Python dict、model instance，或丟出明確 exception

### Service 例外模型

建議先建立一組輕量 domain exception，讓 HTML 與 API controller 各自轉換成適合的 response：

```python
# web_app/services/exceptions.py
class ServiceError(Exception):
    message = "操作失敗"
    status_code = 400


class EmptyCartError(ServiceError): ...
class StaffCustomerPhoneRequired(ServiceError): ...
class NotFoundError(ServiceError):
    status_code = 404
class PermissionBusinessError(ServiceError):
    status_code = 403
class ValidationServiceError(ServiceError): ...
```

規則：

- serializer / form 可以攔的格式錯誤，仍放 serializer / form。
- 涉及資料狀態、訂單歸屬、購物車是否可送出、菜單是否存在等 domain rule，放 service。
- service 不直接 import `api_success`、`JsonResponse`、`messages` 或 `redirect`。
- 第一階段可以只在 order/menu 使用 exception；cart service 若目前 controller 已完成 serializer validation，可先回傳 dict，降低改動量。

## Service API 契約草案

### `web_app/services/cart.py`

```python
def get_cart(session) -> list[dict]: ...
def replace_cart(session, cart: list[dict]) -> None: ...
def cart_count(cart: list[dict]) -> int: ...
def cart_total(cart: list[dict]) -> int: ...
def summarize_cart(cart: list[dict]) -> dict: ...

def add_item(session, data: dict) -> dict:
    """回傳 {"cart_count": int}。"""

def adjust_item(session, data: dict) -> dict:
    """調整無選項品項，回傳 {"cart_count": int, "item_quantity": int}。"""

def update_item_quantity(session, index: int, quantity: int) -> dict:
    """依 index 更新，維持現有 index 超界靜默忽略行為。"""

def remove_item(session, index: int) -> dict:
    """依 index 移除，維持現有 index 超界靜默忽略行為。"""

def remove_last_item_by_menu(session, menu_id: int) -> dict:
    """移除最後一筆 menu_id 相符品項，回傳 cart_count 與該 menu 剩餘數量。"""

def append_menu_item(cart: list[dict], menu, quantity: int, options=None) -> int:
    """供 reorder/order 相關服務重用，回傳本次加入數量。"""
```

Cart item dict 需要明文化，避免前端、API、order 建立各自假設：

```python
{
    "menu_id": int,
    "name": str,
    "base_price": int,
    "options": list[dict],
    "options_price": int,
    "unit_price": int,
    "quantity": int,
    "subtotal": int,
}
```

### `web_app/services/order.py`

```python
SPICY_LEVEL_MAP = {"不辣": 0, "小辣": 1, "中辣": 2, "大辣": 3}

def normalize_checkout_data(data: dict) -> dict: ...
def create_order_from_cart(user, session, checkout_data: dict) -> Order: ...
def reorder_to_cart(user, session, order_id: int) -> dict: ...
def update_order_status(order_id: int, status: int) -> dict: ...
def order_status_counts() -> dict: ...
def format_order_options(raw_opts) -> str: ...
def attach_order_display_data(orders: list[Order]) -> list[Order]: ...
```

`create_order_from_cart()` 的最小責任：

1. 從 session 取 cart，空 cart 丟 `EmptyCartError`。
2. 判斷員工/管理者代客點餐，缺電話丟 `StaffCustomerPhoneRequired`。
3. 正規化辣度與加料數量，計算 `extra_cost` 與 `price_total`。
4. 建立 `Order`，逐筆 cart item 建立 `OrderItem`。
5. 將 item-level options 寫入 `OrderItemOptions(order_item=...)`。
6. 將 order-level 辣度/加蒜/九層塔寫入 `OrderItemOptions(order=...)`。
7. 清空 cart。

交易邊界：此函式應使用 `transaction.atomic()`，避免訂單建立一半失敗時留下孤立資料。

### `web_app/services/menu.py`

```python
def validate_uploaded_image(uploaded_file): ...
def menu_payload(menu) -> dict: ...
def get_menu_detail(menu_id: int) -> Menu: ...
def toggle_menu_status(menu_id: int) -> dict: ...
def create_menu_item(data: dict, uploaded_image=None) -> Menu: ...
def update_menu_item(menu_id: int, data: dict, uploaded_image=None) -> Menu: ...
def get_visible_menus(user, query: str = "", assisted: bool = False): ...
```

Menu service 初期可以保留 `MenuSerializer(menu).data` 在 API controller，service 回傳 model 或簡單 dict 即可。不要讓 service 依賴 DRF serializer，避免 service 層反向依賴 API 層。

## 優先重構目標

### 1. Cart Service

目前主要混雜位置：

- `web_app/api/views/cart.py`
- `web_app/views/cart.py`
- `web_app/static/js/detail.js` 對 cart API response 有耦合

建議新增：

```python
# web_app/services/cart.py
def get_cart(session): ...
def cart_count(cart): ...
def cart_total(cart): ...
def add_item(session, data): ...
def adjust_item(session, data): ...
def update_item_quantity(session, index, quantity): ...
def remove_item(session, index): ...
def remove_last_item_by_menu(session, menu_id): ...
```

API view 改成：

```python
serializer.is_valid(raise_exception=True)
result = cart_service.add_item(request.session, serializer.validated_data)
return api_success(result)
```

HTML view 改成：

```python
cart = cart_service.get_cart(request.session)
total = cart_service.cart_total(cart)
```

### 2. Order Service

目前主要混雜位置：

- `web_app/views/payment.py`
- `web_app/api/views/order.py`
- `web_app/views/staff.py`
- `web_app/views/order_history.py`

建議新增：

```python
# web_app/services/order.py
def create_order_from_cart(user, session, checkout_data): ...
def reorder_to_cart(user, session, order_id): ...
def update_order_status(order, status): ...
def get_order_status_counts(): ...
def format_order_options(order): ...
```

`payment.order_submit()` 應只負責：

1. 確認 method 是 POST。
2. 從 form 讀取 checkout data。
3. 呼叫 `create_order_from_cart(...)`。
4. 根據結果顯示 messages 並 redirect。

`ReorderAPIView` 應只負責：

1. permission / serializer。
2. 呼叫 `reorder_to_cart(...)`。
3. 回傳 `api_success(...)`。

### 3. Menu Service

目前主要混雜位置：

- `web_app/api/views/menu.py`
- `web_app/views/menu_manage.py`
- `web_app/views/home.py`

建議新增：

```python
# web_app/services/menu.py
def toggle_menu_status(menu): ...
def create_menu_item(data, image=None): ...
def update_menu_item(menu, data, image=None): ...
def get_available_menus(...): ...
```

這一階段可以排在 cart/order 之後，因為 menu 邏輯目前重複程度較低。

## 權限與業務限制的區分

權限判斷放 controller / permission：

- 是否登入
- 是否為顧客
- 是否為員工或管理員
- 是否為管理員

業務限制放 service：

- 訂單不屬於目前使用者
- 訂單狀態不可被更新
- 購物車是空的
- 菜單已刪除所以略過
- 代客點餐必須填電話

例如「再次訂購」：

- `IsCustomer`：判斷只有顧客可用。
- `reorder_to_cart()`：判斷訂單是否存在且屬於該顧客，並把可用餐點加入 cart。

## 任務拆解

### Phase 12.0：重構前保護網

- [ ] 新增 `web_app/tests/test_services_cart.py`，先用現有行為寫 characterisation tests。
- [ ] 新增 `web_app/tests/test_services_order.py`，覆蓋訪客、顧客、員工代客、空購物車、加料、切法。
- [ ] 新增 `web_app/tests/test_services_menu.py`，覆蓋圖片格式、價格驗證、分類不存在、名稱重複。
- [ ] 先跑目標測試，確認目前 baseline 穩定：`python manage.py test web_app.tests.test_cart_feedback web_app.tests.test_payment_guest web_app.tests.test_menu_create web_app.tests.test_menu_edit web_app.tests.test_menu_toggle --keepdb`
- [ ] 若現有測試已足夠，可先不新增所有 service tests，但每搬一個 service 至少補一組 direct service test。

### Phase 12.1：建立服務層骨架與 Cart Service

- [ ] 新增 `web_app/services/__init__.py`
- [ ] 新增 `web_app/services/cart.py`
- [ ] 新增 `web_app/services/exceptions.py`
- [ ] 搬移 cart count / total 計算
- [ ] 搬移 `CartAddAPIView` 的加入購物車邏輯
- [ ] 搬移 `CartAdjustAPIView` 的快速增減邏輯
- [ ] 搬移 `CartUpdateAPIView` / `CartRemoveAPIView` 的索引操作邏輯
- [ ] 搬移 `CartRemoveByMenuAPIView` 的依 `menu_id` 移除邏輯
- [ ] 更新 `cart_view()` 改用 cart service
- [ ] 新增或調整 cart service 單元測試
- [ ] 跑 `python manage.py test web_app.tests.test_cart_feedback --keepdb`

### Phase 12.2：建立 Order Service

- [ ] 新增 `web_app/services/order.py`
- [ ] 搬移 `payment.order_submit()` 的訂單建立邏輯
- [ ] 將訂單建立包進 `transaction.atomic()`
- [ ] 搬移 spicy / extras / item options 寫入邏輯
- [ ] 搬移 `ReorderAPIView` 的再次訂購邏輯
- [ ] 搬移 `_order_status_counts()`
- [ ] 搬移 `_format_order_opts()` 並讓 staff list/report 共用
- [ ] 讓 `staff_order_list()` 只處理 pagination 與 render
- [ ] 讓 `OrderStatusAPIView` 只做 serializer + service call
- [ ] 新增 order service 測試
- [ ] 跑 `python manage.py test web_app.tests.test_payment_guest web_app.tests.test_order_history --keepdb`

### Phase 12.3：整理 API 權限與例外格式

- [ ] `ReorderAPIView` 改用 `IsCustomer` 或專用 permission
- [ ] 檢查 `permissions.py` 與 `decorators.py` 的重複 identity 判斷
- [ ] 視需要新增 `web_app/services/authz.py` 或 `web_app/authz.py`
- [ ] 修正 `decorators.py` 註解中「員工（B）」與實際 `identity=E` 不一致
- [ ] 評估是否接續 Phase 11 的 DRF global exception handler
- [ ] 更新 OpenAPI response 文件

### Phase 12.4：建立 Menu Service

- [ ] 新增 `web_app/services/menu.py`
- [ ] 合併 `api/views/menu.py` 與 `views/menu_manage.py` 的 `_validate_uploaded_image()`
- [ ] 合併 menu create/update 的價格、分類、名稱重複規則
- [ ] 保留 `_parse_menu_request()`、`_json()`、權限檢查在 HTML JSON controller
- [ ] 搬移 menu create / update / toggle 的核心邏輯
- [ ] 搬移 home/assisted ordering 的可見菜單查詢與搜尋
- [ ] 讓 `api/views/menu.py` 只處理 serializer、permission、response
- [ ] 讓 `views/menu_manage.py` 只處理 HTML form、messages、redirect
- [ ] 新增 menu service 測試
- [ ] 跑 `python manage.py test web_app.tests.test_menu_create web_app.tests.test_menu_edit web_app.tests.test_menu_toggle --keepdb`

### Phase 12.5：收尾驗證

- [ ] 跑完整測試：`python manage.py test --keepdb`
- [ ] 更新 `openapi.json` 靜態快照
- [ ] 更新 `docs/progress.md`
- [ ] 若 harness 可用，跑 `python scripts/harness/harness_orchestrator.py --action audit`
- [ ] 補 change log
- [ ] 原子化 commit

## 驗收標準

- `web_app/api/views/` 不再直接操作大量 session cart 結構。
- `web_app/views/payment.py` 不再直接承擔完整訂單建立流程。
- cart / order 主要邏輯可在不經過 HTTP request 的情況下測試。
- HTML JSON endpoints（`menu_manage.py`）與 DRF API endpoints 使用同一組 menu domain rules。
- `_order_status_counts()`、`_validate_uploaded_image()` 不再重複定義。
- API response 格式與既有前端 JS 相容。
- HTML 頁面 redirect / messages 行為維持不變。
- 完整測試通過。

## 風險與注意事項

- 購物車目前存在 Django session，service 仍需接收並更新 `request.session`；這不是最終純 domain service，但可先降低 controller 複雜度。
- 重構時不要一次搬完所有 domain，先從 cart 開始，因為 cart 測試範圍清楚、回歸成本最低。
- `order_submit()` 同時影響訪客、顧客、員工代客點餐與 OrderItemOptions，應獨立成一個 phase 處理。
- 若改用 DRF permission class，401 / 403 錯誤文字可能改變，需同步調整測試與 OpenAPI 文件。
- 不要把 `messages`、`redirect`、`api_success`、`api_error` 放進 service，避免 service 再次綁死特定 HTTP 介面。
- `create_order_from_cart()` 會接觸多張表，務必使用 transaction，並確認失敗時不清空 cart。
- `ReorderAPIView` 目前不複製原訂單選項，規劃先維持此行為，避免 scope 擴大。
- `CartUpdateAPIView` / `CartRemoveAPIView` 對 index 超界目前是靜默成功；第一輪重構維持既有行為，不改成 404/400。
- `menu_manage.py` 是傳統 JsonResponse endpoint，不是 DRF；重構時不要一次強迫改成 DRF，避免前端與測試雙重變更。

## 建議實作順序

1. **先 Cart**：純 session dict 操作，最容易用 direct unit test 鎖行為，也能讓 API views 立刻變薄。
2. **再 Order create**：影響面最大，獨立一個 commit，搭配 transaction 與 checkout tests。
3. **再 Order status / reorder**：抽掉 `_order_status_counts()` 重複，讓 API 與 staff view 共用。
4. **最後 Menu**：同步 HTML JSON endpoint 與 DRF endpoint 的規則，避免一開始就牽動圖片、multipart、serializer 文件。

每個 phase 完成後建議原子化 commit；若工作區仍有使用者既有未提交變更，提交前先確認只 stage 本 phase 涉及檔案。
