# POLYFLOOR ARCHITECTURAL SPECIFICATION & PRD

**Autonomous Multi-Floor Enterprise Engine with GBA/DS Pixel Art Orchestration**

---

## 1. System Vision & Metaphor

Polyfloor models an autonomous business as a multi-floor department store / corporate skyscraper inspired by classic 16-bit handheld games (Pokemon Gen 3 GBA / Gen 4 NDS).
Users interact with a corporate hierarchy through a retro dual-screen interface:

- **Top Screen (Canvas Viewport):** 2D orthogonal top-down pixel tilemap ($16\\times16$ grid, $320\\times240$ base virtual resolution scaled $3\\times$ or $4\\times$). Shows floors, team suites, furniture, desks, and animated agent sprites.
- **Bottom Screen (Interactive Console / Pokétch):** Multi-modal telemetry console with high-res character bust portraits (Visual Novel / Fire Emblem style), text dialogue boxes, approval buttons, and real-time activity feeds.

---

## 2. Floor Architecture & Functional Topology

```
+=======================================================================================+
| ROOFTOP: Telemetry, Ingress Gateways & External Notification Relays                   |
+=======================================================================================+
| 5F: C-SUITE & EXECUTIVE BOARDROOM                                                     |
| - CEO: Oversees company strategy, maintains direct user comms (SMS/Twilio/Telegram).   |
| - CFO: Manages finances, tracks token cost vs revenue, enforces spending caps.         |
| - CTO / CHO: Prompts/model optimization, error mitigation, stack health.              |
| - COO: Lean manufacturing auditor, 5S compliance, bottleneck detector.               |
| - QA JUDGING PANEL: Multi-model evaluation gate for final product sign-off.           |
+=======================================================================================+
| 4F: PRODUCT & R&D WING                                                                |
| - R&D Team Lead + Sub-agents (market analysis, viability tests, PRD drafts).         |
| - Writing & Content Team Lead + Sub-agents (drafting, code generation, asset review).|
| - Floor Team Board: Shared Kanban and message thread.                                |
+=======================================================================================+
| 3F: MARKETING, CREATIVE & DISTRIBUTION WING                                           |
| - Marketing Lead + Creative Sub-Agents (copy, posters/art, social campaigns).        |
| - Floor Team Board: Media asset requests to HR and distribution schedule.            |
+=======================================================================================+
| 2F: TALENT OPERATIONS (HR Wing)                                                       |
| - HR Coordinator: Hires sub-agents, provisions floor desks, assigns token budgets.    |
| - Org Tree Registry: Maintains active team leads, sub-agents, and model assignments.  |
+=======================================================================================+
| 1F: MAIN LOBBY & RECEPTION                                                            |
| - Front Desk Receptionist: Onboards new companies/business ideas.                     |
| - Intake Grilling Engine: 4 intensity tiers, interactive choice selection.            |
+=======================================================================================+
| B1: TOOLING & MCP ENGINE ROOM                                                         |
| - Hardware server racks representing active MCP connections (GitHub, Stripe, etc.).   |
+=======================================================================================+
| B2: FOUNDATION & SECRETS VAULT                                                        |
| - Honcho / Brain-Service vector memory pipes, SQLite databases, sops-nix credentials. |
+=======================================================================================+
```

---

## 3. Communication, State & Governance Mechanics

### 3.1 Dual-Board Communication Model

Each operational floor maintains two linked data structures stored in SQLite:

1. **The Floor Message Log (Append-Only Bus):**
   - Cryptographically or token-signed JSON entries from agent team leads and HR.
   - Message schema: `(id, floor_id, author_id, author_role, target_role, message_type, payload, timestamp)`.
   - Used for inter-team requests (e.g., Marketing Lead requesting an image generation worker from HR).
1. **The Floor Kanban Matrix (Lean Task DAG):**
   - Columns: `BACKLOG`, `TODO`, `IN_PROGRESS`, `REVIEW / AWAITING_APPROVAL`, `DONE`.
   - Tasks contain assigned agent IDs, token spend tracking, and artifact links.
   - **WIP (Work-In-Progress) Limit:** Enforced by the COO agent. No team can have more than 3 concurrent tasks in `IN_PROGRESS`.

### 3.2 Human-in-the-Loop Approval & Escalation Engine

- **Low Priority:** Dashboard bottom-screen badge notification.
- **Medium Priority (Telegram):** Budget thresholds reached, marketing releases ready for review, hiring approvals.
- **Critical Priority (Twilio Call / SMS):** Runaway loop detected, financial threshold breach, security or unauthorized I/O error.

---

## 4. Frontend & Game Loop Architecture

### 4.1 Tech Stack

- **Framework:** SvelteKit + TypeScript + Vite
- **Renderer:** Plain HTML5 2D Canvas (zero external game engine dependencies)
- **Styling:** CSS Grid + Tailwind with `image-rendering: pixelated`
- **Transport:** Server-Sent Events (`/api/events`) for unidirectional state streaming + REST POST (`/api/actions`) for user inputs.

### 4.2 Room & Floor Layout Specifications

- **Base Canvas Resolution:** $320 \\times 240$ pixels, scaled with integer nearest-neighbor sampling.
- **Tile Size:** $16 \\times 16$ pixels.
- **Floor Boundaries:** Fixed $20 \\times 15$ tile grid.
- **Room Templates:**
  - Executive Suite (carpet, mahogany desks, podium)
  - Research Lab (whiteboards, server consoles, technical desks)
  - Creative Studio (easels, display screens, media benches)
  - Main Lobby (checkered tiles, reception counter, visitor waiting benches)
- **Desk Population:** Team leads occupy a primary desk. HR pre-allocates up to 5 sub-agent desks per suite. Empty desks show as vacant furniture until an agent is hired.

---

## 5. Execution Workflow & Next Steps

1. **Asset Staging:** Place an orthogonal $16\\times16$ modern interior tileset at `frontend/static/tileset.png`.
1. **Backend Event Bus:** Implement the FastAPI SSE streaming route emitting game state deltas.
1. **Canvas Engine:** Implement the Svelte 2D canvas loop rendering room grids and sprite animations.
1. **Bottom Console:** Build the Pokétch-style communicator component supporting bust portraits and approval flows.
1. **1F Intake Engine:** Build the interactive reception desk questionnaire for corporate initialization.
