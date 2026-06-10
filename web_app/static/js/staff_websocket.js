(function () {
  "use strict";

  var RECONNECT_DELAY_MS = 3000;
  var ws = null;

  function connect() {
    var protocol = location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(protocol + "://" + location.host + "/ws/staff/");

    ws.onopen = function () {
      console.debug("[WS-Staff] connected");
    };

    ws.onclose = function () {
      console.debug("[WS-Staff] disconnected — retry in " + RECONNECT_DELAY_MS + "ms");
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
    var grid =
      document.getElementById("staffOrderGrid") ||
      document.getElementById("kanbanBoard");
    if (!grid) return;
    if (document.getElementById("order-" + orderId)) return;
    location.reload();
  }

  connect();
})();
