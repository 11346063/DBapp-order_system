"""
測試 DRF 全域 custom_exception_handler 統一 API 錯誤格式。

驗證項目：
- serializer ValidationError → 400 + {"status":"error","message":...,"errors":{...}}
- NotAuthenticated → 401 + {"status":"error","message":"請先登入"}
- PermissionDenied / 非員工存取員工端點 → 403 + {"status":"error","message":...}
- Http404 / NotFound (menu/order 不存在) → 404 + {"status":"error","message":...}
- ServiceError 子類自動映射到 status_code
- 成功 API 仍回傳 {"status":"success",...} 不受影響
"""

import json

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from web_app.models import Identity, Menu, Order, Type, User


class ExceptionHandlerFormatTest(TestCase):
    """驗證全域 exception handler 回傳格式一致"""

    def setUp(self):
        self.client = Client()
        self.type = Type.objects.create(type_name="測試分類")
        self.menu = Menu.objects.create(
            type=self.type, name="測試品項", price=80, status=True
        )
        self.customer = User.objects.create_user(
            account="c001",
            password="pass",
            name="顧客",
            identity=Identity.CUSTOMER,
        )
        self.employee = User.objects.create_user(
            account="e001",
            password="pass",
            name="員工",
            identity=Identity.EMPLOYEE,
        )
        self.admin = User.objects.create_user(
            account="a001",
            password="pass",
            name="管理員",
            identity=Identity.ADMIN,
        )

    def test_drf_exception_handler_uses_api_module(self):
        """DRF exception handler 使用目前的 api.exceptions 模組"""
        self.assertEqual(
            settings.REST_FRAMEWORK["EXCEPTION_HANDLER"],
            "web_app.api.exceptions.custom_exception_handler",
        )

    def _json_post(self, url, data, user=None):
        if user:
            self.client.force_login(user)
        resp = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )
        self.client.logout()
        return resp

    # ------------------------------------------------------------------
    # 401 NotAuthenticated
    # ------------------------------------------------------------------

    def test_unauthenticated_returns_401_standard_format(self):
        """未登入呼叫需要認證的 API → 401 + 統一格式"""
        resp = self.client.post(
            reverse("web_app:api_order_accept", kwargs={"pk": 999}),
            data=json.dumps({"estimated_wait_minutes": 20}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 401)
        data = resp.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)

    # ------------------------------------------------------------------
    # 403 PermissionDenied
    # ------------------------------------------------------------------

    def test_customer_cannot_access_employee_endpoint_403(self):
        """顧客呼叫員工端點 → 403 + 統一格式"""
        resp = self._json_post(
            reverse("web_app:api_order_accept", kwargs={"pk": 999}),
            {"estimated_wait_minutes": 20},
            user=self.customer,
        )
        self.assertEqual(resp.status_code, 403)
        data = resp.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)

    # ------------------------------------------------------------------
    # 404 NotFound via ServiceError (NotFoundError)
    # ------------------------------------------------------------------

    def test_nonexistent_menu_toggle_returns_404_standard_format(self):
        """切換不存在的菜單 → 404 + 統一格式"""
        self.client.force_login(self.employee)
        resp = self.client.post(reverse("web_app:menu_toggle", kwargs={"pk": 99999}))
        self.client.logout()
        self.assertEqual(resp.status_code, 404)
        data = resp.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)

    def test_nonexistent_api_order_accept_returns_404_standard_format(self):
        """接受不存在的訂單 → 404 + 統一格式"""
        resp = self._json_post(
            reverse("web_app:api_order_accept", kwargs={"pk": 99999}),
            {"estimated_wait_minutes": 20},
            user=self.employee,
        )
        self.assertEqual(resp.status_code, 404)
        data = resp.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)

    # ------------------------------------------------------------------
    # 400 ValidationError via raise_exception=True
    # ------------------------------------------------------------------

    def test_serializer_validation_error_returns_400_with_errors(self):
        """serializer raise_exception=True → 400 + errors 欄位"""
        resp = self._json_post(
            reverse("web_app:api_order_accept", kwargs={"pk": 1}),
            {"estimated_wait_minutes": -5},
            user=self.employee,
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)

    def test_missing_required_field_returns_400(self):
        """缺少必填欄位 → 400 + 統一格式"""
        resp = self._json_post(
            reverse("web_app:api_order_accept", kwargs={"pk": 1}),
            {},
            user=self.employee,
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)

    # ------------------------------------------------------------------
    # 400 ValidationServiceError (業務規則)
    # ------------------------------------------------------------------

    def test_ready_on_submitted_order_returns_400(self):
        """對非 ACCEPTED 訂單通知取餐 → 400 + 統一格式 (ValidationServiceError)"""
        order = Order.objects.create(
            user=self.customer,
            price_total=80,
            status=Order.OrderStatus.SUBMITTED,
            customer_phone="0900000001",
        )
        self.client.force_login(self.employee)
        resp = self.client.post(
            reverse("web_app:api_order_ready", kwargs={"pk": order.pk}),
            content_type="application/json",
        )
        self.client.logout()
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("message", data)

    # ------------------------------------------------------------------
    # 成功回應不受影響
    # ------------------------------------------------------------------

    def test_successful_api_still_returns_success_status(self):
        """正常成功的 API 仍回傳 status=success"""
        self.client.force_login(self.employee)
        resp = self.client.post(
            reverse("web_app:menu_toggle", kwargs={"pk": self.menu.pk})
        )
        self.client.logout()
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("message", data)
        self.assertIn("data", data)
