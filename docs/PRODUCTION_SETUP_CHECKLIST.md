# ArgusCX owner workflow

ArgusCX is designed to sit behind your company’s backend. Browser clients use the dashboard; your backend owns every provider credential, web hook secret, and customer-data connection.

## 1. Deploy for your company

1. Choose an application hostname, such as `support.your-company-domain`.
2. Set `DASHBOARD_BASE_URL` and `ALLOWED_ORIGINS` to that HTTPS hostname.
3. Keep `ARGUSCX_API_URL` server-only in the Next.js deployment. The browser calls `/api/v1` through the same-origin proxy.
4. Create unique administrator and JWT secrets in `backend/.env`. Never commit that file.
5. Point `MONGO_URI` at your managed MongoDB instance. Add PostgreSQL and Redis before enabling durable multi-worker processing.

## 2. Connect human support

Configure outbound handoff email in `backend/.env`:

```env
SMTP_HOST=<mail-provider-host>
SMTP_PORT=<mail-provider-port>
SMTP_USERNAME=<mail-provider-username>
SMTP_PASSWORD=<mail-provider-password-or-app-password>
SMTP_FROM_EMAIL=<approved-from-address>
SUPPORT_HANDOFF_EMAIL=<your-support-team-inbox>
SMTP_USE_TLS=true
```

ArgusCX sends the support team an email only when SMTP is configured. Otherwise the handoff stays visible in the authenticated API with an explicit `not_configured` delivery status.

For a helpdesk or custom support application, configure a signed webhook:

```env
HUMAN_HANDOFF_WEBHOOK_URL=<your-helpdesk-or-backend-endpoint>
HUMAN_HANDOFF_WEBHOOK_SECRET=<long-random-shared-secret>
```

The payload has event `support.handoff.created` and contains the ticket, customer contact data, evidence references, AI confidence/risk, policy context, agent steps, and the recommended next action. Verify the `X-ArgusCX-Signature` HMAC-SHA256 header before accepting it.

## 3. Bring in real customer support work

1. Sign in to `/dashboard/api` and create one server credential for your environment.
2. Ingest approved company policies through `POST /api/v1/knowledge/documents`. Until a relevant policy exists, ArgusCX routes cases to people.
3. Have your backend post customer cases to `POST /api/v1/tickets`, including the real order and payment references when you have them.
4. For email support, configure your mail provider’s inbound-webhook feature to call `POST /api/v1/channels/email/inbound` with the same server credential. Do not expose that credential in the email client.
5. When a case needs a person, ArgusCX automatically creates a `support.handoff.created` context packet. Operators can also create one with `POST /api/v1/handoffs`.
6. A human resolves the case via `PATCH /api/v1/tickets/{ticket_id}/resolve`; the ticket retains the operator identity, notes, and outcome.

## 4. SecondHome launch sequence

- Run the readiness assessment at `/getstarted` using your actual channels and support platform.
- Start with one workflow—for example, order questions or return requests—not every support topic at once.
- Add your current approved policies and a real support inbox before inviting customers.
- Configure only the live provider connectors you use. An unconfigured Shopify, Stripe, or Razorpay connector returns `not_configured`; it never manufactures order or payment data.
- Monitor `/dashboard/settings` until MongoDB, AI reasoning, SMTP, and the required human-handoff path show the intended state.
- Keep a human approval rule for refunds, account security actions, payment disputes, and any low-confidence outcome during the pilot.

## 5. Required external inputs

To finish a real deployment, the owner must provide the mail provider details above and, if using one, the human-support destination/webhook. Domain ownership by itself cannot create an SMTP service; those credentials are issued by the mail provider you select.
