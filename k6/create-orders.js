import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const BASE_URL = 'http://localhost:8000';

export const options = {
  duration: '30s',
  vus: 100,
  thresholds: {
    http_req_failed:   ['rate<0.05'],
    http_req_duration: ['p(95)<300'],
    create_errors:     ['rate<0.05'],
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
    'status 202':      (r) => r.status === 202,
    'tem id':          (r) => !!JSON.parse(r.body).id,
    'status accepted': (r) => JSON.parse(r.body).status === 'accepted',
  });

  errorRate.add(!ok);

  sleep(0.1);
}