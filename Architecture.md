# Architecture

Created by: Gayathri Satheesh
Created time: September 5, 2025 2:19 PM
Category: MVP
Last edited by: Gayathri Satheesh
Last updated time: September 5, 2025 11:01 PM

---

## **1. Agent(s) mediate between user, voice, and flow editor**

**What to do:**

- Use **CrewAI** as your agent orchestrator (“crew” includes: Interpreter, Planner, Visualizer agents).
- Inputs:
    - **Voice/text intent:** Pipecat streams STT (using ElevenLabs) to backend/API endpoint.
    - **Manual visual edits:** Listen for changes/events from React Flow on frontend; emit as “edit deltas” or new “spec” to backend.
- **Agent pipeline:**
    - Interpreter agent: Parses user requirement (voice/text input, Pipecat).
    - Planner agent: Plans workflow steps/structure.
    - Visualizer agent: Outputs/updates React Flow JSON.
- Handle “delta” (manual UI edits):
    - When the user moves/adds/deletes a node, React Flow emits an event → send the new graph (or diff) to Planner agent so it can validate, replan, or update internal spec as needed.
- **Sync between agent and UI:** On every change (voice or manual), keep a canonical graph so both UI and backend are consistent.

---

## **2. Agent(s) auto-add compliance, security, legal modules**

**What to do:**

- Add a specialized **Compliance Agent** (part of your crew), with knowledge of your manifests/templates for legal/PII/risk flows.
- Capability:
    - On initial plan or any graph update, Compliance Agent reads the requirement/domain (“healthcare”, “finance”, etc.) and:
        - Looks up the domain’s required modules (PII Redaction, Audit, DPDP, etc.).
        - Auto-injects them (locked nodes) into the graph and manifests them in UI (uneditable/removable unless allowed).
        - If user removes a required node, agent auto-restores/recommends its addition.
        - Surfaces compliance reasons/explanations in workflow UI (“PHI redaction required; can’t be removed”).
- Uses a knowledge base (manifest/config) of policies per domain.

---

## **3. Agent(s) convert workflow to n8n + send jobs**

**What to do:**

- Add a **Converter Agent** to the crew:
    - Reads the in-memory React Flow graph (JSON).
    - Translates it to [n8n workflow JSON](https://docs.n8n.io/automation/workflow-structure/) (mapping each node and edge to n8n’s format).
    - Sends this via REST API to n8n (`POST /workflows`, then execute).
- Flow:
    - React Flow “Run” → API `/convert-and-execute`
    - Converter Agent produces n8n JSON, backend POSTs it, polls for job status.
    - All compliance/locked modules are preserved as mandatory n8n steps.

---

## **4. Make n8n workflow output usable as an application**

**What to do:**

- After n8n has executed the workflow:
    - Backend fetches output/results/logs via n8n REST API.
    - Parses and feeds results back to the frontend/dashboard:
        - For workflows that output data (e.g., summary, report): Display in app UI, allow download/email/integration.
        - For flows that cause actions (e.g., send email, update file): Surface result status (success/failure/audit) immediately.
    - Optionally, augment the UI with:
        - An “App Run History” dashboard.
        - Live results/log panes (output, logs, metrics).
        - Buttons to re-run steps, download audit/export, or “explain this step.”
    - For workflows that require user follow-up: UI prompts next action (e.g., “Doctor must approve,” “Patient must sign,” etc.), triggered by job/state from n8n’s output.

---

# **In Practice: Sequence of Events**

1. **User (voice or text) describes app →** Pipecat/ElevenLabs → Interpreter Agent (CrewAI)
2. **Planner/Compliance Agents** produce/augment the React Flow graph, inject required nodes.
3. **User edits/adds/removes nodes in UI** (React Flow events) → backend → agents update plan; compliance re-validates graph.
4. **“Run/Deploy” clicked →** Converter Agent transforms React Flow JSON to n8n JSON → n8n workflow created and executed via API.
5. **n8n runs workflow** (including agent-locked compliance/approval steps), status and results polled by backend.
6. **Results shown in dashboard/app**; UI reflects state, allows further actions, audit/export, and explanation.
7. **All steps, agent decisions, actions, and outputs traced and visualized via Maxim (observability layer).**

---

## **Tips for Each Step**

- **All agent actions** are explainable; surface “why” compliance steps exist in UI.
- **Monitor/sync**: Every edit or action triggers a check: compliance included? graph valid? RBAC enforced?
- **n8n input/output**: Carefully map your internal node types/params to n8n’s node and credential schema.
- **Demo focus**: Prepare a handful of “golden” flows for each domain; showcase what happens when user tries to circumvent compliance (agent restores, UI explains).
- **Observability**: Use Maxim SDK to log all agentic/actionable steps and user interventions.