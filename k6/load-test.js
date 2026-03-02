import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const BASE_URL = 'http://localhost:8000';

export const options = {
  duration: '30s',
  vus: 10,
  thresholds: {
    http_req_failed:   ['rate<0.05'],   // menos de 5% de erros
    http_req_duration: ['p(95)<500'],   // 95% das requests abaixo de 500ms
  },
};

const errorRate = new Rate('errors');

const CUSTOMERS = ['Alice', 'Bob', 'Carlos', 'Diana', 'Eduardo'];
const STATUSES  = ['pending', 'processing', 'completed'];

function pick(arr)   { return arr[Math.floor(Math.random() * arr.length)]; }
function amount()    { return parseFloat((Math.random() * 990 + 10).toFixed(2)); }

export default function () {
  const headers = { 'Content-Type': 'application/json' };

  // ── 1. Health check ──────────────────────────────────────────────────────
  const health = http.get(`${BASE_URL}/`);
  check(health, { 'health 200': (r) => r.status === 200 });

  // ── 2. Criar pedido ──────────────────────────────────────────────────────
  const body = JSON.stringify({
    customer_name: pick(CUSTOMERS),
    total_amount:  amount(),
    status:        'pending',
    description:   `load-test VU=${__VU} iter=${__ITER}`,
  });

  const created = http.post(`${BASE_URL}/orders`, body, { headers });
  const createOk = check(created, {
    'create 201':  (r) => r.status === 201,
    'create tem id': (r) => !!JSON.parse(r.body).id,
  });

  errorRate.add(!createOk);

  if (!createOk) {
    sleep(1);
    return;
  }

  const orderId = JSON.parse(created.body).id;

  // ── 3. Listar pedidos ────────────────────────────────────────────────────
  const list = http.get(`${BASE_URL}/orders?limit=10`);
  check(list, {
    'list 200':      (r) => r.status === 200,
    'list é array':  (r) => Array.isArray(JSON.parse(r.body)),
  });

  // ── 4. Buscar pedido específico ──────────────────────────────────────────
  const get = http.get(`${BASE_URL}/orders/${orderId}`);
  check(get, {
    'get 200':      (r) => r.status === 200,
    'get id bate':  (r) => JSON.parse(r.body).id === orderId,
  });

  // ── 5. Atualizar pedido ──────────────────────────────────────────────────
  const updateBody = JSON.stringify({
    status:       pick(STATUSES),
    total_amount: amount(),
  });
  const updated = http.put(`${BASE_URL}/orders/${orderId}`, updateBody, { headers });
  check(updated, { 'update 200': (r) => r.status === 200 });

  // ── 6. Deletar pedido ────────────────────────────────────────────────────
  const deleted = http.del(`${BASE_URL}/orders/${orderId}`);
  check(deleted, { 'delete 204': (r) => r.status === 204 });

  sleep(0.5);
}
