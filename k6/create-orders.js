import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const BASE_URL = 'http://localhost:8000';

export const options = {
  duration: '30s',
  vus: 20,
  thresholds: {
    http_req_failed:   ['rate<0.05'],  // menos de 5% de erros
    http_req_duration: ['p(95)<300'],  // 95% abaixo de 300ms
  },
};

const errorRate  = new Rate('create_errors');
const createTime = new Trend('create_duration', true);

const CUSTOMERS = [
  'Alice Silva', 'Bob Santos', 'Carlos Souza',
  'Diana Lima',  'Eduardo Rocha', 'Fernanda Costa',
];

function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
function amount()  { return parseFloat((Math.random() * 990 + 10).toFixed(2)); }

export default function () {
  const payload = JSON.stringify({
    customer_name: pick(CUSTOMERS),
    total_amount:  amount(),
    status:        'pending',
    description:   `load-test VU=${__VU} iter=${__ITER}`,
  });

  const res = http.post(`${BASE_URL}/orders`, payload, {
    headers: { 'Content-Type': 'application/json' },
  });

  createTime.add(res.timings.duration);

  const ok = check(res, {
    'status 201':    (r) => r.status === 201,
    'tem id':        (r) => !!JSON.parse(r.body).id,
    'tem created_at':(r) => !!JSON.parse(r.body).created_at,
  });

  errorRate.add(!ok);

  sleep(0.1);
}
