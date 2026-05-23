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
        script = f"""
        const assert = require('node:assert/strict');
        const cartJs = {json.dumps(cart_js)};

        const button = {{
          disabled: false,
          innerHTML: '',
          listeners: {{}},
          addEventListener(event, handler) {{ this.listeners[event] = handler; }},
        }};
        let syncCalls = 0;
        let reloadCalls = 0;

        global.document = {{
          addEventListener(event, handler) {{ if (event === 'DOMContentLoaded') handler(); }},
          getElementById(id) {{ return id === 'acceptCartPriceChanges' ? button : null; }},
        }};
        global.location = {{ reload() {{ reloadCalls += 1; }} }};
        global.postJSON = (url, payload) => {{
          assert.equal(url, '/api/v1/cart/sync-prices/');
          assert.deepEqual(payload, {{}});
          syncCalls += 1;
          return Promise.resolve({{ status: 'success', data: {{ total: 50 }} }});
        }};

        eval(cartJs);
        button.listeners.click();
        setImmediate(() => {{
          assert.equal(syncCalls, 1);
          assert.equal(reloadCalls, 1);
          assert.equal(button.disabled, true);
        }});
        """

        _run_node(script)

    def test_payment_submit_shows_modal_then_syncs_and_submits(self):
        payment_js = (ROOT / "web_app/static/js/payment.js").read_text(encoding="utf-8")
        script = f"""
        const assert = require('node:assert/strict');
        const paymentJs = {json.dumps(payment_js)};

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
          BASE_TOTAL: 50,
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
            }}[id] || null;
          }},
          createElement() {{
            return {{
              _text: '',
              set textContent(value) {{ this._text = String(value); }},
              get innerHTML() {{
                return this._text
                  .replaceAll('&', '&amp;')
                  .replaceAll('<', '&lt;')
                  .replaceAll('>', '&gt;');
              }},
            }};
          }},
        }};
        global.postJSON = (url, payload) => {{
          calls.push(url);
          assert.deepEqual(payload, {{}});
          if (url === '/api/v1/cart/validate-prices/') {{
            return Promise.resolve({{
              data: {{
                has_changes: true,
                new_total: 55,
                price_changes: [{{
                  name: '報表測試薯條',
                  quantity: 1,
                  old_unit_price: 50,
                  new_unit_price: 55,
                }}],
              }},
            }});
          }}
          if (url === '/api/v1/cart/sync-prices/') {{
            return Promise.resolve({{ data: {{ total: 55 }} }});
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
          assert.match(listEl.innerHTML, /報表測試薯條/);
          assert.match(listEl.innerHTML, /\\$50/);
          assert.match(listEl.innerHTML, /\\$55/);
          assert.equal(totalEl.textContent, '$55');

          acceptButton.listeners.click();
          setImmediate(() => {{
            assert.deepEqual(calls, [
              '/api/v1/cart/validate-prices/',
              '/api/v1/cart/sync-prices/',
            ]);
            assert.equal(modalHidden, 1);
            assert.equal(form.submitted, 1);
            assert.equal(window.BASE_TOTAL, 55);
            assert.equal(submitButton.disabled, true);
          }});
        }});
        """

        _run_node(textwrap.dedent(script))
