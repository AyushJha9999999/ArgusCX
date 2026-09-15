# ArgusCX Integration Guide

This is the partner-facing setup contract for connecting a company to ArgusCX.

## 1. What you need

### Required platform configuration

| Variable | Purpose | Where it belongs |
|---|---|---|
| `ARGUSCX_MASTER_KEY` | Bootstraps the local dashboard or creates platform access | ArgusCX backend only |
| `APP_SECRET_KEY` | Signs application-level secrets | ArgusCX backend only |
| `ALLOWED_ORIGINS` | Browser origins allowed to call the API | ArgusCX backend |
| `GROQ_API_KEY` | Enables the configured live LLM path | ArgusCX backend only |

If no `GROQ_API_KEY` is present, the system uses deterministic/heuristic fallbacks for some agent steps. That is useful for demos, but it is not the same as autonomous production reasoning.

### Company provider credentials

Configure only the systems a company uses. Never put these in a browser bundle, ticket payload, public repository, or `NEXT_PUBLIC_*` variable.

| System | Variables | What ArgusCX can do now |
|---|---|---|
| Shopify | `SHOPIFY_ACCESS_TOKEN`, `SHOPIFY_SHOP_DOMAIN` | Read orders and customer history |
| Stripe | `STRIPE_SECRET_KEY` | Read payment intents and customers |
| Razorpay | `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET` | Read orders and payments |
| Slack | `SLACK_WEBHOOK_URL` | Send escalation alerts |

For refunds, ticket writes, CRM synchronization, WhatsApp, email, voice, Zendesk, Intercom, Salesforce, HubSpot, and custom company websites, add an adapter with the same `BaseConnector` contract or send normalized cases to the ticket API/webhook layer. A credential alone does not create an integration.

## 2. Authenticate API requests

Create a platform key from a trusted server or use the configured bootstrap key during local development:

```bash
curl -X POST http://localhost:8000/api/v1/api-keys \
  -H "X-ArgusCX-Key: $ARGUSCX_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"company_name":"Acme Support","rate_limit_per_minute":120}'
```

Use the returned key from your backend:

```bash
curl http://localhost:8000/api/v1/agents \
  -H "X-ArgusCX-Key: acx_live_replace_me"
```

The header is `X-ArgusCX-Key`. Query-string keys are retained only for easy local testing and should not be used in production because they leak through logs and browser history.

## 3. Submit a support case

```bash
curl -X POST http://localhost:8000/api/v1/tickets \
  -H "X-ArgusCX-Key: acx_live_replace_me" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name":"Priya Sharma",
    "customer_email":"priya@example.com",
    "customer_id":"cus_123",
    "subject":"Order arrived damaged",
    "message":"The earbuds arrived damaged and I would like a refund.",
    "channel":"web",
    "category":"order_refund",
    "evidence_file_ids":[],
    "evidence_urls":[]
  }'
```

The response includes the ticket status, confidence and risk scores, evidence analysis, retrieved policy context, agent steps, and a case file when escalation is required.

## 4. Real-time events

Connect to `ws://localhost:8000/ws/tickets` to receive ticket lifecycle events. The current WebSocket is a broadcast channel for local/demo deployments. Production deployments should add tenant-aware authorization and a durable pub/sub layer before exposing it to multiple companies.

## 5. OpenAPI documentation

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

Swagger now exposes the `ArgusCXKey` and `BearerAuth` security schemes. Click **Authorize**, enter a platform key, and try the protected routes.

## 6. Production hardening checklist

- Store API keys hashed in a durable database, not process memory.
- Replace the demo login token with a real identity provider and tenant-aware sessions.
- Encrypt provider credentials at rest and scope them per company.
- Add webhook signature verification and idempotency keys for inbound events.
- Move uploads from local disk to private object storage with signed URLs and malware scanning.
- Add refund/write operations only behind explicit policy and human approval controls.
- Add tenant isolation to tickets, analytics, WebSockets, rate limits, and logs.
- Rotate any credential that has ever been committed to a repository or shared in chat.