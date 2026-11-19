// Навантажувальний сценарій: профіль "мало записів, багато читань".
// Один віртуальний користувач за ітерацію: 1 запис + 9 читань.
//
// Запуск однією командою (з кореня репозиторію):
//   k6 run loadtest/script.js
// Свої параметри:
//   k6 run -e BASE_URL=http://<alb-dns> -e VUS=80 loadtest/script.js
//
// Фази: наростання 0 -> N за 3 хв, стале навантаження 5 хв, спад до 0 за 2 хв.

import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://todo-api-alb-725788838.eu-north-1.elb.amazonaws.com';
const N = parseInt(__ENV.VUS || '80'); // користувачі на плато (не більше 99: див. формулу priority нижче)

// priority в таблиці tasks UNIQUE (Integer, максимум 2 147 483 647), тому для кожного
// запису потрібне унікальне число. RUN змінюється щохвилини, тож повторні прогони
// не конфліктують із даними попередніх. Працює для VUS <= 99.
const RUN = Math.floor(Date.now() / 60000) % 2000;

export const options = {
  stages: [
    { duration: '3m', target: N },
    { duration: '5m', target: N },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'],
  },
  summaryTrendStats: ['avg', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
};

const JSON_HEADERS = { headers: { 'Content-Type': 'application/json' } };

export default function () {
  // --- 1 запис ---
  const body = JSON.stringify({
    title: `task ${__VU}-${__ITER}`.slice(0, 30), // title <= 30 символів
    description: 'load test',
    priority: RUN * 1000000 + __VU * 10000 + __ITER,
  });
  const created = http.post(`${BASE_URL}/tasks/`, body, {
    ...JSON_HEADERS,
    tags: { name: 'POST /tasks/' },
  });
  const ok = check(created, { 'create: 200': (r) => r.status === 200 });
  const id = ok ? created.json('id') : null; // id створеного запису (його повертає TaskOut)

  // --- 9 читань ---
  const list = () =>
    http.get(`${BASE_URL}/tasks/`, { tags: { name: 'GET /tasks/' } });
  const one = () =>
    id
      ? http.get(`${BASE_URL}/tasks/${id}`, { tags: { name: 'GET /tasks/{id}' } })
      : list();
  const stats = () =>
    http.get(`${BASE_URL}/stats`, { tags: { name: 'GET /stats' } });

  const reads = [list, one, stats, list, one, list, one, stats, one];
  for (const read of reads) {
    const res = read();
    check(res, { 'read: 200': (r) => r.status === 200 });
    sleep(0.3);
  }
}
