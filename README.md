# Smart IT Helpdesk - DevOps Mini Project

## Stack
- Flask + PostgreSQL
- Git/GitHub
- Docker + Docker Compose
- Jenkins
- GitHub Actions
- Jira
- Prometheus + Grafana

## Run locally

```bash
docker compose up -d --build
```

Open:
- App: http://localhost:5000
- Health: http://localhost:5000/health
- Metrics: http://localhost:5000/metrics
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

Grafana login:
- username: admin
- password: admin

The dashboard is provisioned automatically as "Smart Helpdesk Monitoring".
