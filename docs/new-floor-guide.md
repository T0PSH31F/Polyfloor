# Company Templates

Polyfloor does not hardcode the same departments into every company. Intake
selects a **template**; HR materializes the org graph for that tenant. A
**company is the tenant** — templates are about org shape, not isolation (which
is always `company_id`).

## 1. Pick a template

| Template | Default teams | Hard gates |
| --- | --- | --- |
| Digital products *(MVP reference)* | R&D, product/writing, creative, marketing, distribution, customer ops | Marketplace publish, paid assets |
| Freelance agency | Intake/sales, delivery, QA, client success, finance | Client send, deadline change |
| E-commerce / dropship | Research, supplier ops, storefront, creative, marketing, support | Purchase, ad spend, listing, refund |
| Creator / influencer | Strategy, production, editing, distribution, community | Public post, sponsor reply |
| Investment research | Research, risk, data, compliance | Any trade/execution stays human-approved |
| CAD / 3D assets | Design, production, rendering, QA, marketplace | Publish, paid compute |

Custom/oddball prompts still produce a template-like org: goal, teams,
policies, model routes, WIP, required capabilities.

## 2. Create the company

Via the 1F intake wizard, or directly:

```bash
curl -X POST http://127.0.0.1:8001/api/companies \
  -H 'Content-Type: application/json' \
  -d '{ "name": "Lumin Press", "goal": "Ship a digital product", "template_id": "digital-products" }'
```

Creating a company materializes the CEO, HR, C-suite, team leads, rooms, desks,
and the gated research → spec → draft → QA → marketing → publish pipeline, plus
a publish approval. See [`API_CONTRACT.md`](./API_CONTRACT.md).

## 3. Add teams / workers via HR

Team leads **request** specialists; they never spawn agents or grant tools
directly. HR creates workers after policy/budget checks:

```bash
# request_hire -> PENDING approval
# execute_hire -> HR creates the worker (see API_CONTRACT.md Actions)
```

## 4. Multi-floor growth inside one company

If a company outgrows one lobby, keep the same `company_id` and add
`company_floors` with color-coded tabs. Never put two companies on one visual
floor. See SPEC §3.4.
