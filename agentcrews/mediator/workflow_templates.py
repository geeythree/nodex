from typing import Dict, List, Any
from pydantic import BaseModel

class ComplianceNode(BaseModel):
    id: str
    name: str
    type: str  # "consent_gate", "pii_redaction", "access_check", "vendor_check", "audit_trail", "data_retention"
    description: str
    rules: List[str]
    locked: bool = True

class WorkflowStep(BaseModel):
    id: str
    label: str
    type: str  # "user_action", "approval", "system_process", "compliance_check", "output"
    assigned_user: str
    compliance_requirements: List[str] = []
    inputs: List[str] = []
    outputs: List[str] = []
    position: Dict[str, int]
    style: Dict[str, Any]

class WorkflowTemplate(BaseModel):
    name: str
    domain: str
    description: str
    compliance_requirements: List[ComplianceNode] = []
    workflow_steps: List[Dict[str, Any]] = []
    input_structure: Dict[str, str] = {}
    output_structure: Dict[str, Any] = {}
    stakeholders: List[str] = []
    compliance_frameworks: List[str] = []
    steps: List[WorkflowStep] = []
    edges: List[Dict[str, str]] = []

# HR Domain Templates
HR_EMPLOYEE_ONBOARDING = WorkflowTemplate(
    name="Employee Onboarding Process",
    domain="hr",
    description="Complete employee onboarding with background checks, equipment setup, and compliance training",
    stakeholders=["HR Manager", "IT Admin", "Direct Manager", "New Employee", "Compliance Officer"],
    compliance_frameworks=["GDPR", "Employment Law", "Company Policy"],
    steps=[
        WorkflowStep(
            id="start",
            label="Onboarding Request",
            type="user_action",
            assigned_user="HR Manager",
            inputs=["Employee Details", "Position Information"],
            outputs=["Onboarding Ticket"],
            position={"x": 100, "y": 100},
            style={"background": "#10b981", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="background_check",
            label="Background Verification",
            type="compliance_check",
            assigned_user="HR Manager",
            compliance_requirements=["Criminal Background Check", "Employment Verification", "Reference Check"],
            inputs=["Employee Details"],
            outputs=["Background Check Report"],
            position={"x": 300, "y": 100},
            style={"background": "#ef4444", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="it_setup",
            label="IT Equipment & Access",
            type="system_process",
            assigned_user="IT Admin",
            compliance_requirements=["Data Security Policy", "Access Control Policy"],
            inputs=["Employee Details", "Position Requirements"],
            outputs=["User Account", "Equipment Assignment"],
            position={"x": 500, "y": 100},
            style={"background": "#3b82f6", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="manager_assignment",
            label="Manager Introduction",
            type="user_action",
            assigned_user="Direct Manager",
            inputs=["Employee Profile", "Role Expectations"],
            outputs=["Welcome Package", "Initial Goals"],
            position={"x": 700, "y": 100},
            style={"background": "#8b5cf6", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="compliance_training",
            label="Compliance Training",
            type="compliance_check",
            assigned_user="New Employee",
            compliance_requirements=["GDPR Training", "Security Awareness", "Company Policies"],
            inputs=["Training Materials"],
            outputs=["Training Completion Certificate"],
            position={"x": 900, "y": 100},
            style={"background": "#ef4444", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="complete",
            label="Onboarding Complete",
            type="output",
            assigned_user="HR Manager",
            outputs=["Employee Record", "Onboarding Report"],
            position={"x": 1100, "y": 100},
            style={"background": "#059669", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        )
    ],
    edges=[
        {"id": "e1", "source": "start", "target": "background_check"},
        {"id": "e2", "source": "background_check", "target": "it_setup"},
        {"id": "e3", "source": "it_setup", "target": "manager_assignment"},
        {"id": "e4", "source": "manager_assignment", "target": "compliance_training"},
        {"id": "e5", "source": "compliance_training", "target": "complete"}
    ],
    output_structure={
        "employee_record": {
            "employee_id": "string",
            "personal_info": "object",
            "position_details": "object",
            "equipment_assigned": "array",
            "training_completed": "array",
            "manager_assigned": "string"
        },
        "compliance_report": {
            "background_check_status": "boolean",
            "training_completion_date": "date",
            "policy_acknowledgments": "array"
        }
    }
)

# HR Employee Offboarding Template
HR_EMPLOYEE_OFFBOARDING = WorkflowTemplate(
    name="Employee Offboarding Process",
    domain="hr",
    description="Secure employee offboarding with access revocation and asset recovery",
    stakeholders=["HR Manager", "IT Admin", "Direct Manager", "Departing Employee", "Security Team"],
    compliance_frameworks=["GDPR", "Data Retention Policy", "Security Policy"],
    steps=[
        WorkflowStep(
            id="exit_trigger",
            label="Exit Event Trigger",
            type="user_action",
            assigned_user="HR Manager",
            inputs=["HRIS Exit Event", "Asset Register", "IdP User List"],
            outputs=["Offboarding Checklist"],
            position={"x": 100, "y": 100},
            style={"background": "#10b981", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="access_revocation",
            label="Access Revocation Orchestration",
            type="compliance_check",
            assigned_user="IT Admin",
            compliance_requirements=["Access Control Policy", "Shadow-IT Discovery", "RBAC Cleanup"],
            inputs=["User Account Data", "System Access List"],
            outputs=["Access Revocation Report"],
            position={"x": 300, "y": 100},
            style={"background": "#ef4444", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="asset_return",
            label="Asset Return & KT",
            type="user_action",
            assigned_user="Direct Manager",
            inputs=["Asset List", "Knowledge Transfer Checklist"],
            outputs=["Asset Return Confirmation", "KT Documentation"],
            position={"x": 500, "y": 100},
            style={"background": "#3b82f6", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="pii_purge",
            label="PII Purge Plan",
            type="compliance_check",
            assigned_user="Security Team",
            compliance_requirements=["GDPR Right to Erasure", "Data Retention Schedule", "Audit Trail"],
            inputs=["Employee Data Inventory"],
            outputs=["PII Purge Schedule", "Retention Delete Timer"],
            position={"x": 700, "y": 100},
            style={"background": "#ef4444", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="payroll_closure",
            label="Payroll Finalization",
            type="system_process",
            assigned_user="Payroll Team",
            inputs=["Final Timesheet", "Benefits Data"],
            outputs=["Final Pay Calculation", "Benefits Termination"],
            position={"x": 900, "y": 100},
            style={"background": "#8b5cf6", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="audit_archive",
            label="Offboarding Archive",
            type="output",
            assigned_user="HR Manager",
            outputs=["IdP Logs", "Payroll Finalization Record", "Proof of Deletion"],
            position={"x": 1100, "y": 100},
            style={"background": "#059669", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        )
    ],
    edges=[
        {"id": "e1", "source": "exit_trigger", "target": "access_revocation"},
        {"id": "e2", "source": "access_revocation", "target": "asset_return"},
        {"id": "e3", "source": "asset_return", "target": "pii_purge"},
        {"id": "e4", "source": "pii_purge", "target": "payroll_closure"},
        {"id": "e5", "source": "payroll_closure", "target": "audit_archive"}
    ],
    output_structure={
        "offboarding_record": {
            "employee_id": "string",
            "exit_date": "date",
            "access_revoked": "boolean",
            "assets_returned": "array",
            "pii_purged": "boolean"
        },
        "compliance_audit": {
            "gdpr_compliance": "boolean",
            "retention_schedule": "object",
            "proof_of_deletion": "string"
        }
    }
)

# Finance Domain Templates
FINANCE_EXPENSE_APPROVAL = WorkflowTemplate(
    name="Expense Approval Workflow",
    domain="finance",
    description="Multi-level expense approval with compliance checks and reimbursement processing",
    stakeholders=["Employee", "Manager", "Finance Team", "Compliance Officer", "Accounting"],
    compliance_frameworks=["SOX", "Tax Regulations", "Company Policy"],
    steps=[
        WorkflowStep(
            id="submit_expense",
            label="Submit Expense",
            type="user_action",
            assigned_user="Employee",
            inputs=["Expense Details", "Receipts", "Business Justification"],
            outputs=["Expense Report"],
            position={"x": 100, "y": 100},
            style={"background": "#10b981", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="policy_check",
            label="Policy Compliance",
            type="compliance_check",
            assigned_user="System",
            compliance_requirements=["Expense Policy", "Amount Limits", "Category Validation"],
            inputs=["Expense Report"],
            outputs=["Compliance Status"],
            position={"x": 300, "y": 100},
            style={"background": "#ef4444", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="manager_approval",
            label="Manager Review",
            type="approval",
            assigned_user="Manager",
            inputs=["Expense Report", "Compliance Status"],
            outputs=["Manager Approval"],
            position={"x": 500, "y": 100},
            style={"background": "#f59e0b", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="finance_review",
            label="Finance Approval",
            type="approval",
            assigned_user="Finance Team",
            compliance_requirements=["SOX Compliance", "Budget Validation"],
            inputs=["Approved Expense", "Budget Data"],
            outputs=["Finance Approval"],
            position={"x": 700, "y": 100},
            style={"background": "#3b82f6", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="reimbursement",
            label="Process Payment",
            type="system_process",
            assigned_user="Accounting",
            inputs=["Approved Expense"],
            outputs=["Payment Confirmation", "Accounting Entry"],
            position={"x": 900, "y": 100},
            style={"background": "#8b5cf6", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        )
    ],
    edges=[
        {"id": "e1", "source": "submit_expense", "target": "policy_check"},
        {"id": "e2", "source": "policy_check", "target": "manager_approval"},
        {"id": "e3", "source": "manager_approval", "target": "finance_review"},
        {"id": "e4", "source": "finance_review", "target": "reimbursement"}
    ],
    output_structure={
        "expense_record": {
            "expense_id": "string",
            "employee_id": "string",
            "amount": "number",
            "category": "string",
            "approval_chain": "array",
            "payment_status": "string"
        },
        "compliance_audit": {
            "policy_compliance": "boolean",
            "approval_levels": "array",
            "sox_compliance": "boolean"
        }
    }
)

# Finance Vendor Invoice Processing Template
FINANCE_VENDOR_INVOICE = WorkflowTemplate(
    name="Vendor Invoice Processing",
    domain="finance",
    description="Automated vendor invoice processing with 3-way matching and fraud detection",
    compliance_requirements=[
        ComplianceNode(
            id="vendor_verification",
            name="Vendor Verification",
            type="vendor_check",
            description="Verify vendor legitimacy and contract terms",
            rules=["Check vendor master data", "Validate contract existence", "Verify payment terms"],
            locked=True
        ),
        ComplianceNode(
            id="three_way_match",
            name="3-Way Match Validation",
            type="process_validation",
            description="Match invoice, purchase order, and goods receipt",
            rules=["Invoice amount matches PO", "Goods receipt confirms delivery", "Tax calculations accurate"],
            locked=True
        ),
        ComplianceNode(
            id="fraud_detection",
            name="Fraud Detection",
            type="security_check",
            description="AI-powered fraud detection and duplicate invoice check",
            rules=["Duplicate invoice detection", "Anomaly detection", "Vendor risk scoring"],
            locked=True
        ),
        ComplianceNode(
            id="segregation_duties",
            name="Segregation of Duties",
            type="approval_check",
            description="Ensure proper segregation of duties in approval process",
            rules=["Different approvers for PO and invoice", "Manager approval for high amounts", "Finance team final review"],
            locked=True
        ),
        ComplianceNode(
            id="audit_trail",
            name="Audit Trail",
            type="audit_trail",
            description="Complete audit trail for all processing steps",
            rules=["Log all processing steps", "Maintain document versions", "Track approval chain"],
            locked=True
        ),
        ComplianceNode(
            id="retention_policy",
            name="Document Retention",
            type="data_retention",
            description="7-year retention policy for financial documents",
            rules=["Archive processed invoices", "Maintain supporting documents", "Compliance with tax regulations"],
            locked=True
        )
    ],
    workflow_steps=[
        {
            "id": "invoice_receipt",
            "name": "Invoice Receipt",
            "type": "input",
            "description": "Receive vendor invoice via email, portal, or EDI",
            "position": {"x": 100, "y": 100},
            "data_sources": ["Email", "Vendor Portal", "EDI System"],
            "outputs": ["invoice_data", "vendor_id", "invoice_amount"]
        },
        {
            "id": "ocr_processing",
            "name": "OCR & Data Extraction",
            "type": "process",
            "description": "Extract invoice data using OCR and AI",
            "position": {"x": 300, "y": 100},
            "ai_automation": "OCR with line-item extraction",
            "outputs": ["structured_invoice_data", "confidence_scores"]
        },
        {
            "id": "po_matching",
            "name": "PO Matching",
            "type": "process",
            "description": "Match invoice to purchase order and goods receipt",
            "position": {"x": 500, "y": 100},
            "data_sources": ["ERP System", "Purchase Orders", "Goods Receipts"],
            "outputs": ["match_status", "variance_report"]
        },
        {
            "id": "exception_handling",
            "name": "Exception Handling",
            "type": "decision",
            "description": "Route exceptions for manual review",
            "position": {"x": 700, "y": 200},
            "conditions": ["No PO match", "Amount variance > 5%", "Missing goods receipt"],
            "outputs": ["exception_queue", "manual_review_required"]
        },
        {
            "id": "approval_workflow",
            "name": "Approval Workflow",
            "type": "approval",
            "description": "Multi-level approval based on amount and risk",
            "position": {"x": 900, "y": 100},
            "approval_rules": {"<$1000": "Auto-approve", "$1000-$10000": "Manager", ">$10000": "Finance Director"},
            "outputs": ["approval_status", "approver_comments"]
        },
        {
            "id": "payment_processing",
            "name": "Payment Processing",
            "type": "output",
            "description": "Process payment and update accounting records",
            "position": {"x": 1100, "y": 100},
            "dump_location": ["AP Ledger", "Bank System", "Vendor Payment"],
            "outputs": ["payment_confirmation", "accounting_entries"]
        }
    ],
    input_structure={
        "invoice_file": "file",
        "vendor_id": "string",
        "invoice_number": "string",
        "invoice_date": "date",
        "due_date": "date",
        "total_amount": "number",
        "currency": "string",
        "line_items": "array"
    },
    output_structure={
        "processing_status": "string",
        "payment_status": "string",
        "exception_details": "object",
        "audit_log": "array",
        "compliance_status": "boolean",
        "retention_date": "date"
    }
)

# Finance Procurement PO Template
FINANCE_PROCUREMENT_PO = WorkflowTemplate(
    name="Procurement and Purchase Order",
    domain="finance",
    description="End-to-end procurement process with vendor risk assessment and budget approval",
    compliance_requirements=[
        ComplianceNode(
            id="vendor_risk_scoring",
            name="Vendor Risk Assessment",
            type="vendor_check",
            description="Comprehensive vendor risk scoring and due diligence",
            rules=["Financial stability check", "Compliance history review", "Reference verification"],
            locked=True
        ),
        ComplianceNode(
            id="budget_compliance",
            name="Budget Compliance",
            type="approval_check",
            description="Verify budget availability and spending authority",
            rules=["Budget availability check", "Spending limit validation", "Department authorization"],
            locked=True
        ),
        ComplianceNode(
            id="duplicate_detection",
            name="Duplicate Request Detection",
            type="process_validation",
            description="Prevent duplicate purchase requests and orders",
            rules=["Check for similar requests", "Vendor and amount matching", "Time-based duplicate detection"],
            locked=True
        ),
        ComplianceNode(
            id="approver_justification",
            name="Approver Justification",
            type="approval_check",
            description="Require justification for high-value purchases",
            rules=["Business case required >$5000", "ROI analysis for capital items", "Alternative vendor consideration"],
            locked=True
        ),
        ComplianceNode(
            id="audit_trail",
            name="Procurement Audit Trail",
            type="audit_trail",
            description="Complete audit trail for procurement decisions",
            rules=["Log all approval steps", "Maintain vendor communications", "Track contract negotiations"],
            locked=True
        ),
        ComplianceNode(
            id="retention_policy",
            name="Document Retention",
            type="data_retention",
            description="7-year retention for procurement documents",
            rules=["Archive PO and contracts", "Maintain vendor correspondence", "Compliance documentation"],
            locked=True
        )
    ],
    workflow_steps=[
        {
            "id": "purchase_request",
            "name": "Purchase Request",
            "type": "input",
            "description": "Employee submits purchase request with requirements",
            "position": {"x": 100, "y": 100},
            "data_sources": ["Purchase Request Form", "Budget System", "Vendor Master"],
            "outputs": ["request_details", "requested_amount", "business_justification"]
        },
        {
            "id": "vendor_selection",
            "name": "Vendor Selection",
            "type": "process",
            "description": "Select and evaluate potential vendors",
            "position": {"x": 300, "y": 100},
            "ai_automation": "Vendor risk scoring and recommendation",
            "outputs": ["vendor_shortlist", "risk_scores", "pricing_comparison"]
        },
        {
            "id": "budget_approval",
            "name": "Budget Approval",
            "type": "approval",
            "description": "Verify budget availability and get spending approval",
            "position": {"x": 500, "y": 100},
            "approval_rules": {"Department manager approval": "Department manager approval", "Finance approval >$10000": "Finance approval >$10000", "Executive approval >$50000": "Executive approval >$50000"},
            "outputs": ["budget_confirmation", "approval_status"]
        },
        {
            "id": "po_creation",
            "name": "PO Creation",
            "type": "process",
            "description": "Create and send purchase order to vendor",
            "position": {"x": 700, "y": 100},
            "data_sources": ["Vendor Master", "Contract Terms", "Pricing Data"],
            "outputs": ["po_number", "po_document", "vendor_confirmation"]
        },
        {
            "id": "vendor_notification",
            "name": "Vendor Notification",
            "type": "output",
            "description": "Send PO to vendor and update procurement ledger",
            "position": {"x": 900, "y": 100},
            "dump_location": ["Vendor Email", "Procurement Ledger", "ERP System"],
            "outputs": ["notification_status", "tracking_number", "delivery_schedule"]
        }
    ],
    input_structure={
        "request_type": "string",
        "item_description": "string",
        "quantity": "number",
        "estimated_cost": "number",
        "vendor_preference": "string",
        "business_justification": "string",
        "budget_code": "string",
        "urgency": "string"
    },
    output_structure={
        "po_number": "string",
        "vendor_details": "object",
        "total_amount": "number",
        "delivery_date": "date",
        "approval_chain": "array",
        "compliance_status": "boolean"
    }
)

# Sales Domain Templates
SALES_LEAD_QUALIFICATION = WorkflowTemplate(
    name="Lead Qualification Process",
    domain="sales",
    description="Comprehensive lead qualification with scoring and CRM integration",
    stakeholders=["Marketing", "Sales Rep", "Sales Manager", "Customer Success"],
    compliance_frameworks=["GDPR", "CAN-SPAM", "Sales Process"],
    steps=[
        WorkflowStep(
            id="lead_capture",
            label="Lead Capture",
            type="user_action",
            assigned_user="Marketing",
            inputs=["Lead Information", "Source Data"],
            outputs=["Lead Record"],
            position={"x": 100, "y": 100},
            style={"background": "#10b981", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="gdpr_consent",
            label="GDPR Consent Check",
            type="compliance_check",
            assigned_user="System",
            compliance_requirements=["GDPR Consent", "Data Processing Agreement"],
            inputs=["Lead Record"],
            outputs=["Consent Status"],
            position={"x": 300, "y": 100},
            style={"background": "#ef4444", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="lead_scoring",
            label="Lead Scoring",
            type="system_process",
            assigned_user="System",
            inputs=["Lead Record", "Scoring Criteria"],
            outputs=["Lead Score", "Priority Level"],
            position={"x": 500, "y": 100},
            style={"background": "#3b82f6", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="sales_assignment",
            label="Sales Assignment",
            type="user_action",
            assigned_user="Sales Manager",
            inputs=["Qualified Lead", "Sales Team Capacity"],
            outputs=["Assignment Notification"],
            position={"x": 700, "y": 100},
            style={"background": "#f59e0b", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="initial_contact",
            label="Initial Contact",
            type="user_action",
            assigned_user="Sales Rep",
            inputs=["Lead Information", "Contact Strategy"],
            outputs=["Contact Log", "Next Steps"],
            position={"x": 900, "y": 100},
            style={"background": "#8b5cf6", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        )
    ],
    edges=[
        {"id": "e1", "source": "lead_capture", "target": "gdpr_consent"},
        {"id": "e2", "source": "gdpr_consent", "target": "lead_scoring"},
        {"id": "e3", "source": "lead_scoring", "target": "sales_assignment"},
        {"id": "e4", "source": "sales_assignment", "target": "initial_contact"}
    ],
    output_structure={
        "lead_record": {
            "lead_id": "string",
            "contact_info": "object",
            "lead_score": "number",
            "assigned_rep": "string",
            "qualification_status": "string"
        },
        "compliance_record": {
            "gdpr_consent": "boolean",
            "consent_timestamp": "date",
            "data_processing_agreement": "boolean"
        }
    }
)

# Sales Lead Routing Template
SALES_LEAD_ROUTING = WorkflowTemplate(
    name="Lead Routing Process",
    domain="sales",
    description="Intelligent lead routing with enrichment and automated assignment",
    compliance_requirements=[
        ComplianceNode(
            id="consent_validation",
            name="Consent Validation",
            type="consent_gate",
            description="Verify marketing consent and data processing permissions",
            rules=["Check opt-in status", "Validate consent timestamp", "Verify communication preferences"],
            locked=True
        ),
        ComplianceNode(
            id="pii_masking",
            name="PII Data Masking",
            type="pii_redaction",
            description="Mask sensitive personal information in routing process",
            rules=["Mask phone numbers in logs", "Redact email addresses", "Anonymize personal details"],
            locked=True
        ),
        ComplianceNode(
            id="ml_scoring_audit",
            name="ML Scoring Audit",
            type="audit_trail",
            description="Audit trail for ML-based lead scoring decisions",
            rules=["Log scoring criteria", "Track model versions", "Maintain decision rationale"],
            locked=True
        ),
        ComplianceNode(
            id="retention_policy",
            name="Lead Data Retention",
            type="data_retention",
            description="12-month retention policy for lead data",
            rules=["Archive processed leads", "Purge inactive leads", "Maintain consent records"],
            locked=True
        )
    ],
    workflow_steps=[
        {
            "id": "lead_capture",
            "name": "Lead Capture",
            "type": "input",
            "description": "Capture leads from web forms, CRM, and enrichment APIs",
            "position": {"x": 100, "y": 100},
            "data_sources": ["Web Form", "CRM Leads", "Enrichment API"],
            "outputs": ["lead_data", "source_channel", "capture_timestamp"]
        },
        {
            "id": "data_enrichment",
            "name": "Data Enrichment",
            "type": "process",
            "description": "Enrich lead data with company and contact information",
            "position": {"x": 300, "y": 100},
            "ai_automation": "Lead enrichment with external data sources",
            "outputs": ["enriched_profile", "company_data", "contact_details"]
        },
        {
            "id": "lead_scoring",
            "name": "Lead Scoring",
            "type": "process",
            "description": "AI-powered lead scoring based on multiple criteria",
            "position": {"x": 500, "y": 100},
            "ai_automation": "ML scoring model with behavioral and demographic factors",
            "outputs": ["lead_score", "scoring_breakdown", "priority_level"]
        },
        {
            "id": "territory_assignment",
            "name": "Territory Assignment",
            "type": "decision",
            "description": "Assign lead to appropriate sales territory and rep",
            "position": {"x": 700, "y": 100},
            "conditions": ["Geographic territory", "Industry specialization", "Rep capacity"],
            "outputs": ["assigned_rep", "territory_code", "assignment_reason"]
        },
        {
            "id": "intro_email",
            "name": "Introduction Email",
            "type": "output",
            "description": "Send personalized introduction email to lead",
            "position": {"x": 900, "y": 100},
            "dump_location": ["CRM", "Email Logs", "Lead Database"],
            "outputs": ["email_sent", "delivery_status", "tracking_id"]
        }
    ],
    input_structure={
        "lead_source": "string",
        "contact_name": "string",
        "email": "string",
        "phone": "string",
        "company": "string",
        "job_title": "string",
        "industry": "string",
        "lead_notes": "string"
    },
    output_structure={
        "routing_status": "string",
        "assigned_rep": "object",
        "lead_score": "number",
        "enrichment_data": "object",
        "compliance_status": "boolean",
        "retention_date": "date"
    }
)

# IT Incident Management Template
IT_INCIDENT_MANAGEMENT = WorkflowTemplate(
    name="IT Incident Management",
    domain="it",
    description="Comprehensive IT incident management with automated classification and compliance",
    stakeholders=["IT Support", "On-Call Engineer", "Security Team", "Management", "End Users"],
    compliance_frameworks=["RBAC", "Data Privacy", "SLA Management", "Security Audit"],
    steps=[
        WorkflowStep(
            id="incident_capture",
            label="Incident Capture",
            type="user_action",
            assigned_user="IT Support",
            inputs=["Jira/ServiceNow Ticket", "CloudWatch Logs", "User Reports"],
            outputs=["Incident Record"],
            position={"x": 100, "y": 100},
            style={"background": "#10b981", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="severity_classification",
            label="LLM Severity Classification",
            type="system_process",
            assigned_user="System",
            inputs=["Incident Details", "Historical Data"],
            outputs=["Severity Level", "Priority Score"],
            position={"x": 300, "y": 100},
            style={"background": "#3b82f6", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="rbac_check",
            label="RBAC on Raw Logs",
            type="compliance_check",
            assigned_user="Security Team",
            compliance_requirements=["Access Control", "Log Privacy", "Data Masking"],
            inputs=["Raw Logs", "User Permissions"],
            outputs=["Filtered Logs", "Access Audit"],
            position={"x": 500, "y": 100},
            style={"background": "#ef4444", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="oncall_notification",
            label="Page On-Call & Notify",
            type="system_process",
            assigned_user="System",
            inputs=["Severity Level", "On-Call Schedule"],
            outputs=["Notification Sent", "PII Masked Alerts"],
            position={"x": 700, "y": 100},
            style={"background": "#f59e0b", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="incident_resolution",
            label="Resolve & Postmortem",
            type="user_action",
            assigned_user="On-Call Engineer",
            inputs=["Incident Data", "Resolution Steps"],
            outputs=["Resolution Report", "LLM Incident Summary"],
            position={"x": 900, "y": 100},
            style={"background": "#8b5cf6", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        ),
        WorkflowStep(
            id="audit_archive",
            label="Security Audit Trail",
            type="output",
            assigned_user="System",
            compliance_requirements=["1-Year Retention Policy", "Audit Trail"],
            outputs=["Jira Status History", "Confluence Postmortem", "Security Audit Trail"],
            position={"x": 1100, "y": 100},
            style={"background": "#059669", "color": "white", "borderRadius": "8px", "padding": "10px", "minWidth": "140px"}
        )
    ],
    edges=[
        {"id": "e1", "source": "incident_capture", "target": "severity_classification"},
        {"id": "e2", "source": "severity_classification", "target": "rbac_check"},
        {"id": "e3", "source": "rbac_check", "target": "oncall_notification"},
        {"id": "e4", "source": "oncall_notification", "target": "incident_resolution"},
        {"id": "e5", "source": "incident_resolution", "target": "audit_archive"}
    ],
    output_structure={
        "incident_record": {
            "incident_id": "string",
            "severity": "string",
            "resolution_time": "number",
            "assigned_engineer": "string",
            "status": "string"
        },
        "compliance_audit": {
            "rbac_compliance": "boolean",
            "pii_masked": "boolean",
            "retention_scheduled": "date"
        }
    }
)

# IT Data Access Request Template
IT_DATA_ACCESS_REQUEST = WorkflowTemplate(
    name="Data Pipeline Access Request",
    domain="it",
    description="Secure data access request with policy evaluation and time-boxed credentials",
    compliance_requirements=[
        ComplianceNode(
            id="policy_evaluation",
            name="Data Policy Evaluation",
            type="access_check",
            description="Evaluate request against data governance policies",
            rules=["Check data classification", "Validate business justification", "Verify data lineage"],
            locked=True
        ),
        ComplianceNode(
            id="time_boxed_access",
            name="Time-boxed Credentials",
            type="access_check",
            description="Provide temporary, time-limited access credentials",
            rules=["Maximum 90-day access", "Auto-revoke on expiry", "Regular access review"],
            locked=True
        ),
        ComplianceNode(
            id="masking_policy",
            name="Data Masking Policy",
            type="pii_redaction",
            description="Apply appropriate data masking based on sensitivity",
            rules=["PII masking for non-production", "Anonymization for analytics", "Encryption for sensitive data"],
            locked=True
        ),
        ComplianceNode(
            id="auto_revoke",
            name="Auto-revoke Scheduler",
            type="access_check",
            description="Automated access revocation system",
            rules=["Schedule revocation date", "Send expiry notifications", "Audit access usage"],
            locked=True
        ),
        ComplianceNode(
            id="audit_trail",
            name="Access Audit Trail",
            type="audit_trail",
            description="Complete audit trail for data access",
            rules=["Log all access requests", "Track data usage", "Monitor for anomalies"],
            locked=True
        )
    ],
    workflow_steps=[
        {
            "id": "access_request",
            "name": "Data Access Request",
            "type": "input",
            "description": "Submit data access request with business justification",
            "position": {"x": 100, "y": 100},
            "data_sources": ["Request Form", "Data Catalog", "DLP Rules"],
            "outputs": ["request_details", "data_requirements", "business_case"]
        },
        {
            "id": "policy_check",
            "name": "Policy Evaluation",
            "type": "process",
            "description": "Evaluate request against data governance policies",
            "position": {"x": 300, "y": 100},
            "ai_automation": "Policy evaluation engine with risk scoring",
            "outputs": ["policy_compliance", "risk_score", "approval_required"]
        },
        {
            "id": "access_approval",
            "name": "Access Approval",
            "type": "approval",
            "description": "Multi-level approval based on data sensitivity",
            "position": {"x": 500, "y": 100},
            "approval_rules": {"Low risk": "Auto-approve", "Medium risk": "Data owner", "High risk": "Data steward + CISO"},
            "outputs": ["approval_status", "approved_scope", "access_duration"]
        },
        {
            "id": "credential_provision",
            "name": "Credential Provisioning",
            "type": "process",
            "description": "Provision time-boxed credentials with appropriate masking",
            "position": {"x": 700, "y": 100},
            "ai_automation": "Automated credential generation with masking policies",
            "outputs": ["credentials", "access_token", "masking_applied"]
        },
        {
            "id": "catalog_update",
            "name": "Catalog Update",
            "type": "output",
            "description": "Update data catalog and access registry",
            "position": {"x": 900, "y": 100},
            "dump_location": ["IAM Logs", "Catalog Lineage", "Access Registry"],
            "outputs": ["catalog_updated", "lineage_tracked", "registry_entry"]
        }
    ],
    input_structure={
        "requester_id": "string",
        "data_source": "string",
        "access_type": "string",
        "business_justification": "string",
        "requested_duration": "number",
        "data_sensitivity": "string",
        "use_case": "string"
    },
    output_structure={
        "access_granted": "boolean",
        "credentials": "object",
        "expiry_date": "date",
        "masking_applied": "array",
        "compliance_status": "boolean",
        "audit_log": "array"
    }
)

# Operations Document Approval Template
OPS_DOCUMENT_APPROVAL = WorkflowTemplate(
    name="Document Approval & Publishing",
    domain="operations",
    description="Secure document approval workflow with PII scanning and compliance validation",
    compliance_requirements=[
        ComplianceNode(
            id="pii_scan",
            name="PII Detection & Redaction",
            type="pii_redaction",
            description="Scan documents for PII and apply redaction with confidence tags",
            rules=["Detect SSN, credit cards, emails", "Apply confidence-based redaction", "Maintain redaction audit trail"],
            locked=True
        ),
        ComplianceNode(
            id="policy_compliance",
            name="Policy Compliance Check",
            type="process_validation",
            description="Validate document against organizational policies",
            rules=["Check against policy library", "Validate formatting standards", "Ensure regulatory compliance"],
            locked=True
        ),
        ComplianceNode(
            id="parallel_approval",
            name="Parallel Approval Process",
            type="approval_check",
            description="Enable parallel approval workflows for efficiency",
            rules=["Legal and compliance parallel review", "Department head approval", "Final publishing approval"],
            locked=True
        ),
        ComplianceNode(
            id="watermarking",
            name="Document Watermarking",
            type="security_check",
            description="Apply security watermarks and version control",
            rules=["Add approval watermarks", "Version control stamps", "Distribution tracking"],
            locked=True
        ),
        ComplianceNode(
            id="article30_register",
            name="Article 30 Register",
            type="audit_trail",
            description="GDPR Article 30 processing activity register",
            rules=["Log data processing activities", "Maintain legal basis records", "Track data subject rights"],
            locked=True
        )
    ],
    workflow_steps=[
        {
            "id": "document_submission",
            "name": "Document Submission",
            "type": "input",
            "description": "Submit draft document for approval workflow",
            "position": {"x": 100, "y": 100},
            "data_sources": ["Draft Documents", "Policy Library", "Template Repository"],
            "outputs": ["document_content", "metadata", "submission_timestamp"]
        },
        {
            "id": "legal_review",
            "name": "Legal Review",
            "type": "approval",
            "description": "Legal team review for compliance and risk",
            "position": {"x": 300, "y": 100},
            "approval_rules": {"Legal compliance check": "Legal compliance check", "Risk assessment": "Risk assessment", "Regulatory review": "Regulatory review"},
            "outputs": ["legal_approval", "compliance_notes", "risk_rating"]
        },
        {
            "id": "content_approval",
            "name": "Content Approval",
            "type": "approval",
            "description": "Subject matter expert and department head approval",
            "position": {"x": 500, "y": 100},
            "approval_rules": {"SME technical review": "SME technical review", "Department head approval": "Department head approval", "Stakeholder sign-off": "Stakeholder sign-off"},
            "outputs": ["content_approved", "revision_notes", "final_version"]
        },
        {
            "id": "publishing_prep",
            "name": "Publishing Preparation",
            "type": "process",
            "description": "Apply watermarks, version control, and final formatting",
            "position": {"x": 700, "y": 100},
            "ai_automation": "Automated watermarking and formatting",
            "outputs": ["watermarked_document", "version_number", "distribution_list"]
        },
        {
            "id": "document_publish",
            "name": "Document Publishing",
            "type": "output",
            "description": "Publish approved document to CMS and distribution channels",
            "position": {"x": 900, "y": 100},
            "dump_location": ["CMS", "Signed PDF Archive", "Article 30 Register"],
            "outputs": ["published_url", "distribution_confirmation", "archive_location"]
        }
    ],
    input_structure={
        "document_title": "string",
        "document_type": "string",
        "author": "string",
        "department": "string",
        "content": "text",
        "sensitivity_level": "string",
        "target_audience": "array"
    },
    output_structure={
        "publication_status": "string",
        "document_url": "string",
        "version_number": "string",
        "approval_chain": "array",
        "compliance_status": "boolean",
        "watermark_applied": "boolean"
    }
)

# Operations Customer Support Escalation Template
OPS_CUSTOMER_SUPPORT = WorkflowTemplate(
    name="Customer Support Escalation",
    domain="operations",
    description="Intelligent customer support escalation with AI summarization and compliance",
    compliance_requirements=[
        ComplianceNode(
            id="llm_summarization",
            name="LLM Ticket Summarization",
            type="ai_automation",
            description="AI-powered ticket summarization for escalation context",
            rules=["Generate concise summaries", "Extract key issues", "Maintain context accuracy"],
            locked=True
        ),
        ComplianceNode(
            id="severity_classifier",
            name="Severity Classification",
            type="ai_automation",
            description="Automated severity classification using ML",
            rules=["Classify based on impact and urgency", "Consider customer tier", "Factor in SLA requirements"],
            locked=True
        ),
        ComplianceNode(
            id="pii_masking",
            name="PII Masking",
            type="pii_redaction",
            description="Mask customer PII in escalation communications",
            rules=["Redact personal information", "Anonymize in reports", "Protect customer privacy"],
            locked=True
        ),
        ComplianceNode(
            id="oncall_suggestion",
            name="On-call Suggestion Engine",
            type="ai_automation",
            description="AI-powered on-call engineer suggestion based on expertise",
            rules=["Match skills to issue type", "Consider availability", "Factor in workload distribution"],
            locked=True
        ),
        ComplianceNode(
            id="retention_policy",
            name="Support Data Retention",
            type="data_retention",
            description="1-year retention policy for support interactions",
            rules=["Archive resolved tickets", "Maintain customer communication history", "Purge expired data"],
            locked=True
        )
    ],
    workflow_steps=[
        {
            "id": "ticket_intake",
            "name": "Ticket Intake",
            "type": "input",
            "description": "Receive and process customer support tickets",
            "position": {"x": 100, "y": 100},
            "data_sources": ["Helpdesk System", "Product Telemetry", "Customer Database"],
            "outputs": ["ticket_data", "customer_info", "issue_description"]
        },
        {
            "id": "triage_classification",
            "name": "Triage & Classification",
            "type": "process",
            "description": "Automated triage and severity classification",
            "position": {"x": 300, "y": 100},
            "ai_automation": "ML-based severity classification and routing",
            "outputs": ["severity_level", "category", "estimated_effort"]
        },
        {
            "id": "escalation_decision",
            "name": "Escalation Decision",
            "type": "decision",
            "description": "Determine if escalation is required based on severity and SLA",
            "position": {"x": 500, "y": 100},
            "conditions": ["High severity", "SLA breach risk", "Customer tier priority"],
            "outputs": ["escalation_required", "escalation_level", "target_sla"]
        },
        {
            "id": "team_communication",
            "name": "Team Communication",
            "type": "process",
            "description": "Notify appropriate teams and stakeholders",
            "position": {"x": 700, "y": 100},
            "ai_automation": "Automated team notification with context",
            "outputs": ["notifications_sent", "team_assigned", "communication_log"]
        },
        {
            "id": "rca_documentation",
            "name": "RCA Documentation",
            "type": "output",
            "description": "Document root cause analysis and resolution",
            "position": {"x": 900, "y": 100},
            "dump_location": ["Ticket Timeline", "RCA Board", "Audit Log"],
            "outputs": ["rca_report", "resolution_steps", "prevention_measures"]
        }
    ],
    input_structure={
        "ticket_id": "string",
        "customer_id": "string",
        "issue_type": "string",
        "description": "text",
        "priority": "string",
        "customer_tier": "string",
        "product_area": "string"
    },
    output_structure={
        "escalation_status": "string",
        "assigned_team": "object",
        "severity_classification": "string",
        "resolution_time": "number",
        "compliance_status": "boolean",
        "rca_completed": "boolean"
    }
)

# Template Registry
WORKFLOW_TEMPLATES = {
    "hr": {
        "employee_onboarding": HR_EMPLOYEE_ONBOARDING,
        "employee_offboarding": HR_EMPLOYEE_OFFBOARDING,
    },
    "finance": {
        "expense_approval": FINANCE_EXPENSE_APPROVAL,
        "vendor_invoice_processing": FINANCE_VENDOR_INVOICE,
        "procurement_po": FINANCE_PROCUREMENT_PO,
    },
    "sales": {
        "lead_qualification": SALES_LEAD_QUALIFICATION,
        "lead_routing": SALES_LEAD_ROUTING,
    },
    "it": {
        "incident_management": IT_INCIDENT_MANAGEMENT,
        "data_access_request": IT_DATA_ACCESS_REQUEST,
    },
    "operations": {
        "document_approval": OPS_DOCUMENT_APPROVAL,
        "customer_support_escalation": OPS_CUSTOMER_SUPPORT,
    }
}

def get_template(domain: str, template_name: str) -> WorkflowTemplate:
    """Get a specific workflow template by domain and name"""
    return WORKFLOW_TEMPLATES.get(domain, {}).get(template_name)

def get_domain_templates(domain: str) -> Dict[str, WorkflowTemplate]:
    """Get all templates for a specific domain"""
    return WORKFLOW_TEMPLATES.get(domain, {})

def list_available_templates() -> Dict[str, List[str]]:
    """List all available templates by domain"""
    return {domain: list(templates.keys()) for domain, templates in WORKFLOW_TEMPLATES.items()}
