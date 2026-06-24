import json
import subprocess
import textwrap
from pathlib import Path

from django.test import SimpleTestCase


ROOT = Path(__file__).resolve().parents[2]


def _run_node(script):
    result = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)


class CartPriceFrontendJsTest(SimpleTestCase):
    def test_cart_accept_latest_price_calls_sync_and_reload(self):
        cart_js = (ROOT / "web_app/static/js/cart.js").read_text(encoding="utf-8")
        item = {
            "menu_id": 1,
            "name": "雞排",
            "base_price": 80,
            "options": [],
            "options_price": 0,
            "unit_price": 80,
            "quantity": 1,
            "subtotal": 80,
        }
        script = f"""
        const assert = require('node:assert/strict');
        const cartJs = {json.dumps(cart_js)};
        const item = {json.dumps(item)};

        let validateCalls = 0;
        let syncCalls = 0;
        let reloadCalls = 0;

        const listEl = {{
            _html: '',
            set innerHTML(v) {{ this._html = v; }},
            get innerHTML() {{ return this._html; }},
            firstChild: null,
            insertBefore(child, ref) {{ /* no-op */ }},
        }};
        const footerEl = {{ innerHTML: '' }};
        const acceptBtn = {{
            disabled: false,
            innerHTML: '',
            listeners: {{}},
            addEventListener(event, handler) {{ this.listeners[event] = handler; }},
        }};

        global.localStorage = {{
            _data: JSON.stringify([item]),
            getItem(key) {{ return this._data; }},
            setItem(key, value) {{ this._data = value; }},
        }};
        global.location = {{ reload() {{ reloadCalls += 1; }} }};
        global.document = {{
            addEventListener(event, handler) {{ if (event === 'DOMContentLoaded') handler(); }},
            querySelector(selector) {{ return null; }},
            getElementById(id) {{
                const map = {{
                    cartList: listEl,
                    cartFooter: footerEl,
                    acceptCartPriceChanges: acceptBtn,
                }};
                return map.hasOwnProperty(id) ? map[id] : null;
            }},
            createElement(tag) {{
                const el = {{
                    _html: '',
                    set innerHTML(v) {{ this._html = v; }},
                    get firstChild() {{ return {{ nodeType: 1 }}; }},
                }};
                return el;
            }},
        }};
        global.window = {{}};
        global.postJSON = (url, payload) => {{
            if (url === '/api/v1/cart/validate-prices/') {{
                validateCalls += 1;
                return Promise.resolve({{
                    data: {{
                        has_changes: true,
                        price_changes: [{{
                            name: '雞排',
                            quantity: 1,
                            old_unit_price: 80,
                            new_unit_price: 90,
                        }}],
                    }},
                }});
            }}
            if (url === '/api/v1/cart/sync-prices/') {{
                syncCalls += 1;
                assert.deepEqual(payload, {{ cart: [item] }});
                return Promise.resolve({{
                    data: {{ cart: [Object.assign({{}}, item, {{ unit_price: 90, subtotal: 90 }})] }},
                }});
            }}
            return Promise.reject(new Error('unexpected url: ' + url));
        }};

        eval(cartJs);

        setImmediate(() => {{
            assert.equal(validateCalls, 1, 'validate-prices called once after render');
            assert.ok(acceptBtn.listeners.click, 'click listener registered on acceptBtn');

            acceptBtn.listeners.click();
            setImmediate(() => {{
                assert.equal(syncCalls, 1, 'sync-prices called once after accept');
                assert.equal(acceptBtn.disabled, true, 'accept button disabled after click');
                const saved = JSON.parse(global.localStorage._data);
                assert.equal(saved[0].unit_price, 90, 'localStorage updated with synced price');
            }});
        }});
        """
        _run_node(textwrap.dedent(script))

    def test_payment_submit_shows_modal_then_syncs_and_submits(self):
        payment_js = (ROOT / "web_app/static/js/payment.js").read_text(encoding="utf-8")
        cart_item = {
            "menu_id": 1,
            "name": "香脆炸雞",
            "base_price": 80,
            "options": [],
            "options_price": 0,
            "unit_price": 80,
            "quantity": 1,
            "subtotal": 80,
        }
        script = f"""
        const assert = require('node:assert/strict');
        const paymentJs = {json.dumps(payment_js)};
        const cartItem = {json.dumps(cart_item)};

        const submitButton = {{ disabled: false, innerHTML: '' }};
        const form = {{
          submitted: 0,
          listeners: {{}},
          querySelector(selector) {{ return selector === 'button[type="submit"]' ? submitButton : null; }},
          addEventListener(event, handler) {{ this.listeners[event] = handler; }},
          submit() {{ this.submitted += 1; }},
        }};
        const acceptButton = {{
          disabled: false,
          innerHTML: '',
          listeners: {{}},
          addEventListener(event, handler) {{ this.listeners[event] = handler; }},
        }};
        const listEl = {{ innerHTML: '' }};
        const totalEl = {{ textContent: '' }};
        let modalShown = 0;
        let modalHidden = 0;
        const calls = [];

        global.window = {{
          BASE_TOTAL: 80,
          location: {{ href: '' }},
          getCart: () => [cartItem],
          saveCart: () => {{}},
          cartTotal: () => 80,
          bootstrap: {{
            Modal: {{
              getOrCreateInstance() {{
                return {{
                  show() {{ modalShown += 1; }},
                  hide() {{ modalHidden += 1; }},
                }};
              }},
            }},
          }},
        }};
        global.bootstrap = global.window.bootstrap;
        global.document = {{
          addEventListener(event, handler) {{ if (event === 'DOMContentLoaded') handler(); }},
          querySelector(selector) {{ return selector === 'form[action*="order/submit"]' ? form : null; }},
          getElementById(id) {{
            return {{
              cartPriceChangeModal: {{}},
              acceptPaymentPriceChanges: acceptButton,
              paymentPriceChangeList: listEl,
              paymentPriceChangeTotal: totalEl,
              extra_garlic_qty: {{ value: '0' }},
              extra_basil_qty: {{ value: '0' }},
              displayTotal: {{ textContent: '' }},
              paymentCartSummary: {{ innerHTML: '' }},
              cartJsonInput: {{ value: '' }},
            }}[id] || null;
          }},
          querySelectorAll() {{ return []; }},
        }};
        global.postJSON = (url, payload) => {{
          calls.push(url);
          assert.deepEqual(payload, {{ cart: [cartItem] }});
          if (url === '/api/v1/cart/validate-prices/') {{
            return Promise.resolve({{
              data: {{
                has_changes: true,
                new_total: 90,
                price_changes: [{{
                  name: '香脆炸雞',
                  quantity: 1,
                  old_unit_price: 80,
                  new_unit_price: 90,
                }}],
              }},
            }});
          }}
          if (url === '/api/v1/cart/sync-prices/') {{
            return Promise.resolve({{ data: {{ cart: [cartItem], total: 90 }} }});
          }}
          return Promise.reject(new Error('unexpected url ' + url));
        }};

        eval(paymentJs);
        form.listeners.submit({{ preventDefault() {{ this.prevented = true; }} }});
        form.listeners.submit({{ preventDefault() {{ this.prevented = true; }} }});

        setImmediate(() => {{
            assert.deepEqual(calls, ['/api/v1/cart/validate-prices/']);
            assert.equal(modalShown, 1);
            assert.equal(form.submitted, 0);
            assert.match(listEl.innerHTML, /香脆炸雞/);
            assert.match(listEl.innerHTML, /\\$80/);
            assert.match(listEl.innerHTML, /\\$90/);
            assert.equal(totalEl.textContent, '$90');

            acceptButton.listeners.click();
            setImmediate(() => {{
                assert.deepEqual(calls, [
                    '/api/v1/cart/validate-prices/',
                    '/api/v1/cart/sync-prices/',
                ]);
                assert.equal(modalHidden, 1);
                assert.equal(form.submitted, 1);
                assert.equal(window.BASE_TOTAL, 90);
                assert.equal(submitButton.disabled, true);
            }});
        }});
        """
        _run_node(textwrap.dedent(script))
