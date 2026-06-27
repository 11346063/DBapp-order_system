(function () {
  "use strict";

  var RECONNECT_DELAY_MS = 3000;
  var POLL_INTERVAL_MS = 5000;
  var MAX_WS_FAILURES = 3;
  var ws = null;
  var retries = 0;
  var wsFailures = 0;
  var pollTimer = null;

  function connect() {
    var protocol = location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(protocol + "://" + location.host + "/ws/staff/");

    ws.onopen = function () {
      console.debug("[WS-Staff] connected");
      wsFailures = 0;
      if (pollTimer !== null) {
        clearInterval(pollTimer);
        pollTimer = null;
        console.debug("[WS-Staff] WebSocket 重連成功 — 停止輪詢備援");
      }
      var grid = document.getElementById("staffOrderGrid") || document.getElementById("kanbanBoard");
      if (grid && retries > 0) {
        location.reload();
      }
    };

    ws.onclose = function () {
      retries++;
      wsFailures++;
      console.debug("[WS-Staff] disconnected — retry " + retries + " (failures=" + wsFailures + ") in " + RECONNECT_DELAY_MS + "ms");
      if (wsFailures >= MAX_WS_FAILURES && pollTimer === null) {
        console.warn("[WS-Staff] 降級為 5 秒輪詢備援");
        pollTimer = setInterval(function () { location.reload(); }, POLL_INTERVAL_MS);
      }
      setTimeout(connect, RECONNECT_DELAY_MS);
    };

    ws.onerror = function (e) {
      console.error("[WS-Staff] error", e);
    };

    ws.onmessage = function (e) {
      var data;
      try {
        data = JSON.parse(e.data);
      } catch (_) {
        return;
      }
      handleMessage(data);
    };
  }

  function handleMessage(data) {
    switch (data.event) {
      case "new_order":
        showToast("新訂單 #" + data.order_id + "（" + data.customer_phone + "）到了！");
        refreshOrderListIfPresent(data.order_id);
        break;
      case "order_accepted":
        showToast("訂單 #" + data.order_id + " 已接單（取餐號：" + data.pickup_code + "）");
        break;
      case "order_ready":
        showToast("訂單 #" + data.order_id + " 可取餐");
        break;
      case "order_status_changed":
        showToast("訂單 #" + data.order_id + " 狀態已更新");
        if (typeof removeOrderCard === "function") {
          removeOrderCard(data.order_id);
        }
        setTimeout(function () { location.reload(); }, 1500);
        break;
    }
  }

  function showToast(message) {
    var toastEl = document.getElementById("staffWsToast");
    var msgEl = document.getElementById("staffWsToastMsg");
    if (!toastEl || !msgEl) return;
    msgEl.textContent = message;
    var toast = bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 6000 });
    toast.show();
  }

  function refreshOrderListIfPresent(orderId) {
    var isOrderListPage =
      document.getElementById("staffOrderGrid") !== null ||
      document.getElementById("kanbanBoard") !== null ||
      document.getElementById("staffOrderEmptyTemplate") !== null;
    if (!isOrderListPage) return;
    if (document.getElementById("order-" + orderId)) return;
    location.reload();
  }

  connect();
})();
