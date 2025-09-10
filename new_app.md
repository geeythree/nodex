Here’s a detailed, **hackathon-optimized architecture**, **tech map**, and clear **agent/stack interaction plan** for a text + image → compliant workflow MVP—so you can **confidently implement and demo** in under 24 hours.

***

# 🚀 HACKATHON MVP: AGENTIC/COMPLIANT WORKFLOW PLATFORM (TEXT + IMAGE INPUT)

***

## 1. **Tech Stack (Best Speed/Robustness/“Wow”)**

**Frontend:**
- **React** (JS/TS) with **React Flow** for workflow graphs.
- Use built-in React state. No need for user auth.
- [Ant Design](https://ant.design/) (optional) or plain CSS for quick modals/tooltips.
- File input for image uploads (“Upload a diagram”); plain textarea for text input.
- “Run/Export” button, “Load Example” button for safety.

**Backend:**
- **FastAPI** (Python)
- **CrewAI** for orchestrating agents (Interpreter → Planner → Compliance → Visualizer)
- **OpenAI GPT-4o** for both text and image interpretation (Vision API)
- Use local YAML/JSON for compliance manifests/templates.
- n8n integration: REST POST or export JSON for demo

***

## 2. **Frontend Flow**

- **App Layout:**  
  - Top:  
    - Textarea (“Describe your workflow...”)  
    - “Upload image/sketch” (accepts PNG/JPG)  
  - Center:  
    - **React Flow canvas** (renders editable graph; compliance nodes locked, colored, tooltip on hover)
  - Bottom/side:  
    - “Run/Export”, “Load Example”, status log, and “Explain Compliance” modal
- **User experience:**  
  - Type a workflow OR upload an image.
  - Graph appears instantly, with compliance steps visually distinct/locked.
  - Drag steps, add new business steps, but **cannot delete/move compliance-labeled nodes**.
  - Export to n8n or just show JSON block for demo safety.

***

## 3. **Agent/Backend Flow**

### **A. Text Input**
1. **Frontend** submits text workflow to `/interpret`
2. **Backend Orchestration:**
   - **Interpreter Agent** (CrewAI + GPT-4o):  
     - Prompt: “Turn the user’s text into an ordered, structured workflow. Flag any compliance steps ‘consent’, ‘pii_redaction’, ‘audit’, etc.”
     - [✅ Handles list parsing, step categorization, ambiguity]
   - **Planner Agent:**  
     - Orders steps, dedupes, clarifies dependencies; splits parallel and serial actions.
   - **Compliance Agent:**  
     - Reads domain from context (e.g., “HR”), loads matching compliance manifest from YAML/JSON.
     - For every mandated step (e.g., “PII Redaction”) missing, **injects node** at the right point, sets `locked=true`, and adds `"compliance_reason"` (for tooltips/explainability).
     - Ensures all compliance steps precede or follow correct business nodes (e.g., redact before email/share).
     - **Auto-restores any removed compliance node** in subsequent edits/updates (enforced in all backend/agent calls).
   - **Visualizer Agent:**  
     - Builds React Flow graph:  
       - Nodes: `id, type, data: {label, locked, compliance_reason}, position`
       - Edges: `id, source, target`
       - Compliance nodes: colored, tooltip-explained, locked for edit/delete.

3. Returns full graph JSON to frontend.

***

### **B. Image Input**
1. **Frontend** uploads workflow diagram image to `/parse-image`.
2. **Backend Orchestration:**
   - Calls **OpenAI GPT-4o Vision API** with this structured prompt:
     ```
     SYSTEM: Extract all process steps from this image (boxes). For each, OCR the text label and note if it’s a compliance step (redact, audit, approve, consent). Also extract all arrows (connections) as step-to-step links. Output a valid JSON array with: 'nodes': [label, type], 'edges': [from, to]. 
     ```
   - **CrewAI Agent Chain** resumes from step listing:
     - **Planner Agent:** orders/makes flow logical.
     - **Compliance Agent:** forcibly adds any missing mandated compliance nodes, locks, annotates.
   - **Visualizer Agent:** builds full React Flow graph as above.
3. Frontend renders resulting editable graph, locks compliance nodes.

***

### **C. Compliance Manifests**

- In `/mediator/config/compliance/hr.yaml` (as YAML or equivalent JSON):
  ```yaml
  domain: HR
  required_steps:
    - label: Consent Gate
      insert_before: Validate Documents
      compliance_type: consent
      locked: true
      reason: "Required by GDPR, DPDP"
    - label: PII Redaction
      insert_before: Create Employee (HRIS)
      compliance_type: pii_redact
      locked: true
      reason: "Required by GDPR Art.30"
    - label: Audit Trail
      insert_after: all
      compliance_type: audit
      locked: true
      reason: "Required by SOX/HIPAA"
  ```
- **Loaded once per run**, dictates compliance agent behavior.
- **Supports custom fields:** Per vertical, tenant, or workflow.

***

### **D. React Flow Compliance Node UX**

- Node data example:
  ```js
  {
    id: "pii-node",
    type: "default",
    data: {
        label: "PII Redaction",
        locked: true,
        compliance_reason: "Required by GDPR Art.30. Cannot be deleted.",
        color: "#FFAE42"
    },
    position: {x: 100, y: 100}
  }
  ```
- UI disables drag/delete on locked nodes.
- Tooltip: on hover, shows `"compliance_reason"` string.

***

### **E. Export/Execution Flow**

- User clicks “Run/Export”.
- Frontend POSTs latest React Flow graph to `/convert-and-execute`.
- Backend:
  - Converts nodes/edges (including compliance, with lock markers) to n8n JSON.
  - (MVP: print/export JSON to frontend, or POST to live n8n if available)
  - Returns logs/audit display to React.

***

### **F. Error/Edge Case Handling**

- **Image parsing fails?** Fallback to “example image”/template.
- **Compliance node missing (removed in text/edit)?** Compliance Agent auto-restores.
- **API quota issues?** Print demo output; note “vision powered by OpenAI GPT-4o, can use Gemini or others.”
- **UI race/lag?** Force canonical state from backend after every update.

***

## **Summary Table**

| Layer       | Tech Used      | Key Functionality                      | Rapid-Dev Advantage      |
|-------------|----------------|----------------------------------------|-------------------------|
| Frontend    | React+ReactFlow| Display/edit workflow; lock/tooltip    | Ready libs, fast setup  |
| Backend     | FastAPI+CrewAI | Pipeline interpreter/compliance/visualizer | Pythonic, glue code    |
| Vision/OCR  | GPT-4o Vision  | Image→ JSON graph, box/arrow detection | One endpoint, multimodal|
| Compliance  | YAML/JSON      | Extensible manifests, “locked” logic   | Config, not code        |
| Orchestration| n8n (export)  | Real-world execution or mock/JSON      | No infra lock-in        |

***

## **What Judges Will See**
- Describe or upload.
- Instantly visualized workflow, compliance always in place.
- Try to “cheat” compliance: can’t.
- One click = export/json, ready for the real w