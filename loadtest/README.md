# Навантажувальний тест

Потрібен [k6](https://k6.io/docs/get-started/installation/).

```bash
k6 run loadtest/script.js
```

З параметрами: `k6 run -e BASE_URL=http://<alb-dns> -e VUS=40 loadtest/script.js`.
Опис і результати — у [docs/LOADTEST.md](../docs/LOADTEST.md).
