# Навантажувальний тест

Потрібен [k6](https://k6.io/docs/get-started/installation/).

```bash
k6 run loadtest/script.js
```

За замовчуванням 80 віртуальних користувачів на плато й поточна адреса ALB. З іншими параметрами: `k6 run -e BASE_URL=http://<alb-dns> -e VUS=80 loadtest/script.js` (VUS не більше 99).
Опис і результати — у [docs/LOADTEST.md](../docs/LOADTEST.md).
