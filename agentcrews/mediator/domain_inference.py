import re
from typing import Dict, List, Optional, Set, Any
from .models import DomainType, ComplianceRequirement, FlowNode, NodeType, NodeData, Position
from loguru import logger
import uuid

class DomainInferenceEngine:
    """Infers domain from user input and manages compliance requirements"""
    
    def __init__(self):
        self.domain_keywords = {
            DomainType.HEALTHCARE: {
                'keywords': [
                    'patient', 'medical', 'health', 'hospital', 'doctor', 'nurse', 'diagnosis',
                    'treatment', 'prescription', 'medication', 'surgery', 'clinic', 'healthcare',
                    'phi', 'hipaa', 'medical record', 'patient data', 'health information',
                    'electronic health record', 'ehr', 'emr', 'radiology', 'lab results',
                    'disha', 'clinical establishment', 'indian healthcare'
                ],
                'patterns': [
                    r'\b(patient|medical|health)\s+(record|data|information)\b',
                    r'\bhipaa\b',
                    r'\bphi\b',
                    r'\belectronic\s+health\s+record\b',
                    r'\bdisha\b',
                    r'\bclinical\s+establishment\b'
                ]
            },
            DomainType.PRODUCTIVITY: {
                'keywords': [
                    'email', 'todo', 'task', 'llm', 'ai', 'automation', 'workflow', 'productivity',
                    'action items', 'to-do', 'organize', 'schedule', 'reminder', 'notification',
                    'chatgpt', 'gpt', 'claude', 'openai', 'assistant', 'bot', 'nlp', 'text processing',
                    'summarize', 'extract', 'parse', 'analyze', 'generate', 'content', 'document'
                ],
                'patterns': [
                    r'\b(email|emails)\s+(to|into|from)\b',
                    r'\b(todo|to-do)\s+(list|items)\b',
                    r'\b(action\s+items?|task\s+list)\b',
                    r'\b(llm|ai)\s+(app|application|system)\b',
                    r'\b(build|create|make)\s+(an?)\s+(app|application|system)\b'
                ]
            },
            DomainType.FINANCE: {
                'keywords': [
                    'bank', 'financial', 'money', 'payment', 'transaction', 'credit', 'debit',
                    'loan', 'mortgage', 'investment', 'trading', 'portfolio', 'account',
                    'pci', 'pci-dss', 'financial data', 'banking', 'fintech', 'cryptocurrency',
                    'fraud', 'aml', 'kyc', 'compliance', 'regulatory', 'sox', 'gdpr'
                ],
                'patterns': [
                    r'\b(financial|banking|payment)\s+(data|information|system)\b',
                    r'\bpci[-\s]?dss\b',
                    r'\baml\b|\bkyc\b',
                    r'\bsox\b|\bsarbanes[-\s]?oxley\b'
                ]
            },
            DomainType.GOVERNMENT: {
                'keywords': [
                    'government', 'federal', 'state', 'municipal', 'public', 'citizen',
                    'fisma', 'fedramp', 'authority to operate', 'ato', 'nist', 'cybersecurity',
                    'classified', 'sensitive', 'cui', 'pii', 'privacy act'
                ],
                'patterns': [
                    r'\b(government|federal|state)\s+(data|system|information)\b',
                    r'\bfisma\b|\bfedramp\b',
                    r'\bnist\b',
                    r'\bcui\b|\bcontrolled\s+unclassified\s+information\b'
                ]
            },
            DomainType.EDUCATION: {
                'keywords': [
                    'student', 'education', 'school', 'university', 'college', 'academic',
                    'ferpa', 'educational record', 'grade', 'transcript', 'enrollment',
                    'learning', 'course', 'classroom', 'teacher', 'professor'
                ],
                'patterns': [
                    r'\b(student|educational)\s+(record|data|information)\b',
                    r'\bferpa\b',
                    r'\bacademic\s+(record|data)\b'
                ]
            }
        }
        
        self.compliance_templates = self._load_compliance_templates()
    
    def _load_compliance_templates(self) -> Dict[DomainType, ComplianceRequirement]:
        """Load compliance requirements for each domain"""
        return {
            DomainType.HEALTHCARE: ComplianceRequirement(
                domain=DomainType.HEALTHCARE,
                required_nodes=[
                    {
                        "type": NodeType.COMPLIANCE,
                        "label": "PHI Redaction",
                        "description": "Remove or mask Protected Health Information",
                        "compliance_type": "HIPAA_PHI_REDACTION",
                        "locked": True
                    },
                    {
                        "type": NodeType.COMPLIANCE,
                        "label": "DISHA Compliance",
                        "description": "Digital Information Security in Healthcare Act compliance (India)",
                        "compliance_type": "DISHA_COMPLIANCE",
                        "locked": True
                    },
                    {
                        "type": NodeType.AUDIT,
                        "label": "HIPAA Audit Log",
                        "description": "Log all access to patient data",
                        "compliance_type": "HIPAA_AUDIT",
                        "locked": True
                    },
                    {
                        "type": NodeType.AUDIT,
                        "label": "Clinical Establishment Audit",
                        "description": "Audit trail for Clinical Establishments Act (India)",
                        "compliance_type": "CLINICAL_ESTABLISHMENT_AUDIT",
                        "locked": True
                    },
                    {
                        "type": NodeType.SECURITY,
                        "label": "Encryption",
                        "description": "Encrypt data in transit and at rest",
                        "compliance_type": "HIPAA_ENCRYPTION",
                        "locked": True
                    },
                    {
                        "type": NodeType.COMPLIANCE,
                        "label": "PDPB Healthcare Data",
                        "description": "Personal Data Protection Bill compliance for health data (India)",
                        "compliance_type": "PDPB_HEALTHCARE",
                        "locked": True
                    }
                ],
                mandatory_flows=[
                    {"from": "input", "to": "phi_redaction"},
                    {"from": "phi_redaction", "to": "disha_compliance"},
                    {"from": "disha_compliance", "to": "audit_log"}
                ],
                restrictions=[
                    "PHI redaction cannot be removed",
                    "DISHA compliance is mandatory for Indian healthcare",
                    "Clinical Establishment Act audit required",
                    "PDPB healthcare data protection required",
                    "Data must be encrypted"
                ],
                explanation="Healthcare workflows require HIPAA compliance (global) and DISHA/Clinical Establishments Act compliance (India), plus PDPB data protection."
            ),
            DomainType.FINANCE: ComplianceRequirement(
                domain=DomainType.FINANCE,
                required_nodes=[
                    {
                        "type": NodeType.COMPLIANCE,
                        "label": "PCI-DSS Validation",
                        "description": "Validate payment card data security",
                        "compliance_type": "PCI_DSS",
                        "locked": True
                    },
                    {
                        "type": NodeType.SECURITY,
                        "label": "Fraud Detection",
                        "description": "Monitor for fraudulent activities",
                        "compliance_type": "FRAUD_DETECTION",
                        "locked": True
                    },
                    {
                        "type": NodeType.AUDIT,
                        "label": "Transaction Audit",
                        "description": "Log all financial transactions",
                        "compliance_type": "FINANCIAL_AUDIT",
                        "locked": True
                    }
                ],
                mandatory_flows=[
                    {"from": "input", "to": "pci_validation"},
                    {"from": "pci_validation", "to": "fraud_detection"}
                ],
                restrictions=[
                    "PCI-DSS validation is mandatory",
                    "Fraud detection cannot be bypassed",
                    "All transactions must be audited"
                ],
                explanation="Financial workflows require PCI-DSS compliance, fraud detection, and comprehensive audit trails."
            ),
            DomainType.GOVERNMENT: ComplianceRequirement(
                domain=DomainType.GOVERNMENT,
                required_nodes=[
                    {
                        "type": NodeType.SECURITY,
                        "label": "NIST Controls",
                        "description": "Apply NIST cybersecurity framework controls",
                        "compliance_type": "NIST_CSF",
                        "locked": True
                    },
                    {
                        "type": NodeType.COMPLIANCE,
                        "label": "FISMA Compliance",
                        "description": "Federal Information Security Management Act compliance",
                        "compliance_type": "FISMA",
                        "locked": True
                    },
                    {
                        "type": NodeType.AUDIT,
                        "label": "Government Audit",
                        "description": "Comprehensive audit trail for government data",
                        "compliance_type": "GOV_AUDIT",
                        "locked": True
                    }
                ],
                mandatory_flows=[
                    {"from": "input", "to": "nist_controls"},
                    {"from": "nist_controls", "to": "fisma_compliance"}
                ],
                restrictions=[
                    "NIST controls are mandatory",
                    "FISMA compliance cannot be removed",
                    "Government audit trail required"
                ],
                explanation="Government workflows require FISMA compliance, NIST controls, and comprehensive audit trails."
            ),
            DomainType.EDUCATION: ComplianceRequirement(
                domain=DomainType.EDUCATION,
                required_nodes=[
                    {
                        "type": NodeType.COMPLIANCE,
                        "label": "FERPA Protection",
                        "description": "Protect student educational records",
                        "compliance_type": "FERPA",
                        "locked": True
                    },
                    {
                        "type": NodeType.AUDIT,
                        "label": "Educational Audit",
                        "description": "Log access to student records",
                        "compliance_type": "EDU_AUDIT",
                        "locked": True
                    }
                ],
                mandatory_flows=[
                    {"from": "input", "to": "ferpa_protection"}
                ],
                restrictions=[
                    "FERPA protection is mandatory",
                    "Student record access must be audited"
                ],
                explanation="Educational workflows require FERPA compliance to protect student privacy."
            ),
            DomainType.GENERIC: ComplianceRequirement(
                domain=DomainType.GENERIC,
                required_nodes=[
                    {
                        "type": NodeType.SECURITY,
                        "label": "Basic Security",
                        "description": "Basic data protection measures",
                        "compliance_type": "BASIC_SECURITY",
                        "locked": False
                    }
                ],
                mandatory_flows=[],
                restrictions=[],
                explanation="Generic workflows include basic security measures."
            ),
            DomainType.ENTERPRISE: ComplianceRequirement(
                domain=DomainType.ENTERPRISE,
                required_nodes=[
                    {
                        "type": NodeType.SECURITY,
                        "label": "Enterprise Security",
                        "description": "Enterprise-grade security controls",
                        "compliance_type": "ENTERPRISE_SECURITY",
                        "locked": True
                    },
                    {
                        "type": NodeType.AUDIT,
                        "label": "Enterprise Audit",
                        "description": "Enterprise audit and compliance logging",
                        "compliance_type": "ENTERPRISE_AUDIT",
                        "locked": True
                    }
                ],
                mandatory_flows=[
                    {"from": "input", "to": "enterprise_security"}
                ],
                restrictions=[
                    "Enterprise security controls are mandatory"
                ],
                explanation="Enterprise workflows require comprehensive security and audit controls."
            ),
            DomainType.PRODUCTIVITY: ComplianceRequirement(
                domain=DomainType.PRODUCTIVITY,
                required_nodes=[
                    {
                        "type": NodeType.SECURITY,
                        "label": "Data Encryption",
                        "description": "Encrypt data in transit and at rest",
                        "compliance_type": "DATA_ENCRYPTION",
                        "locked": True
                    },
                    {
                        "type": NodeType.AUDIT,
                        "label": "Activity Log",
                        "description": "Log all user activity",
                        "compliance_type": "ACTIVITY_LOG",
                        "locked": True
                    }
                ],
                mandatory_flows=[
                    {"from": "input", "to": "data_encryption"}
                ],
                restrictions=[
                    "Data encryption is mandatory",
                    "Activity log is required"
                ],
                explanation="Productivity workflows require data encryption and activity logging."
            )
        }
    
    def infer_domain(self, user_input: str) -> Dict[str, Any]:
        """Infer the business domain from user input with focus on internal processes"""
        input_lower = user_input.lower()
        
        # Business domain patterns
        domain_patterns = {
            DomainType.HEALTHCARE: [
                'patient', 'medical', 'clinic', 'hospital', 'healthcare', 'hipaa',
                'medical record', 'treatment', 'diagnosis', 'prescription'
            ],
            DomainType.FINANCE: [
                'payment', 'invoice', 'expense', 'budget', 'financial', 'accounting',
                'audit', 'sox', 'revenue', 'cost', 'procurement', 'vendor payment'
            ],
            DomainType.EDUCATION: [
                'student', 'course', 'grade', 'enrollment', 'ferpa', 'academic',
                'training', 'certification', 'learning', 'employee training'
            ],
            DomainType.GOVERNMENT: [
                'compliance', 'regulation', 'audit', 'government', 'public',
                'policy', 'legal', 'regulatory reporting'
            ]
        }
        
        # HR and internal process patterns
        hr_patterns = ['employee', 'onboarding', 'hr', 'hiring', 'performance review', 
                      'leave request', 'payroll', 'benefits', 'termination']
        
        # Document and approval patterns  
        approval_patterns = ['approval', 'review', 'document', 'contract', 'agreement',
                           'sign', 'authorize', 'validate', 'quality check']
        
        # Compliance indicators
        compliance_indicators = {
            'gdpr': ['gdpr', 'data protection', 'privacy', 'personal data', 'consent'],
            'sox': ['sox', 'sarbanes', 'financial reporting', 'internal control'],
            'hipaa': ['hipaa', 'health information', 'medical', 'patient data'],
            'pci': ['pci', 'payment card', 'credit card', 'card data']
        }
        
        detected_domain = DomainType.GENERIC
        confidence = 0.0
        compliance_requirements = []
        
        # Check for specific business domains
        for domain, patterns in domain_patterns.items():
            matches = sum(1 for pattern in patterns if pattern in input_lower)
            domain_confidence = matches / len(patterns)
            
            if domain_confidence > confidence:
                confidence = domain_confidence
                detected_domain = domain
        
        # Check for HR processes
        hr_matches = sum(1 for pattern in hr_patterns if pattern in input_lower)
        if hr_matches > 0:
            detected_domain = DomainType.GENERIC  # HR is cross-domain
            confidence = max(confidence, hr_matches / len(hr_patterns))
        
        # Check for approval workflows
        approval_matches = sum(1 for pattern in approval_patterns if pattern in input_lower)
        if approval_matches > 0:
            confidence = max(confidence, approval_matches / len(approval_patterns))
        
        # Detect compliance requirements
        for compliance_type, indicators in compliance_indicators.items():
            if any(indicator in input_lower for indicator in indicators):
                compliance_requirements.append(compliance_type.upper())
        
        # Auto-add compliance based on domain
        if detected_domain == DomainType.HEALTHCARE and 'HIPAA' not in compliance_requirements:
            compliance_requirements.append('HIPAA')
        elif detected_domain == DomainType.FINANCE and 'SOX' not in compliance_requirements:
            compliance_requirements.append('SOX')
        
        # Always consider GDPR for data processing workflows
        if any(term in input_lower for term in ['data', 'personal', 'customer', 'employee']):
            if 'GDPR' not in compliance_requirements:
                compliance_requirements.append('GDPR')
        
        return {
            'primary_domain': detected_domain,
            'confidence': confidence,
            'compliance_requirements': compliance_requirements,
            'is_internal_process': True,  # Always true for our focus
            'suggested_approvals': approval_matches > 0 or detected_domain in [DomainType.FINANCE, DomainType.HEALTHCARE]
        }
    
    def get_compliance_requirements(self, domain: DomainType) -> ComplianceRequirement:
        """Get compliance requirements for a domain"""
        return self.compliance_templates.get(domain, self.compliance_templates[DomainType.GENERIC])
    
    def create_compliance_nodes(self, domain: DomainType, start_position: Position) -> List[FlowNode]:
        """Create compliance nodes for a domain"""
        requirements = self.get_compliance_requirements(domain)
        nodes = []
        
        for i, node_config in enumerate(requirements.required_nodes):
            node = FlowNode(
                id=f"compliance_{domain.value}_{i}_{uuid.uuid4().hex[:8]}",
                type=NodeType(node_config["type"]),
                data=NodeData(
                    label=node_config["label"],
                    description=node_config["description"],
                    domain_required=True,
                    compliance_type=node_config["compliance_type"],
                    locked=node_config["locked"]
                ),
                position=Position(
                    x=start_position.x + (i * 200),
                    y=start_position.y + 100
                ),
                draggable=not node_config["locked"],
                selectable=True,
                deletable=not node_config["locked"]
            )
            nodes.append(node)
        
        return nodes
    
    def validate_compliance(self, nodes: List[FlowNode], domain: DomainType) -> Dict[str, Any]:
        """Validate that required compliance nodes are present"""
        requirements = self.get_compliance_requirements(domain)
        required_types = {node["compliance_type"] for node in requirements.required_nodes}
        present_types = {
            node.data.compliance_type for node in nodes 
            if node.data.compliance_type and node.data.domain_required
        }
        
        missing_types = required_types - present_types
        violations = []
        
        for missing_type in missing_types:
            # Find the requirement details
            for req_node in requirements.required_nodes:
                if req_node["compliance_type"] == missing_type:
                    violations.append({
                        "type": "missing_compliance_node",
                        "compliance_type": missing_type,
                        "label": req_node["label"],
                        "description": req_node["description"]
                    })
        
        return {
            "is_compliant": len(violations) == 0,
            "violations": violations,
            "domain": domain,
            "explanation": requirements.explanation
        }
    
    def auto_fix_compliance(self, nodes: List[FlowNode], domain: DomainType) -> List[FlowNode]:
        """Automatically add missing compliance nodes"""
        validation = self.validate_compliance(nodes, domain)
        
        if validation["is_compliant"]:
            return nodes
        
        # Find a good position for new nodes
        if nodes:
            max_y = max(node.position.y for node in nodes)
            start_position = Position(x=100, y=max_y + 150)
        else:
            start_position = Position(x=100, y=100)
        
        # Create missing compliance nodes
        new_nodes = self.create_compliance_nodes(domain, start_position)
        
        # Filter out nodes that already exist
        existing_compliance_types = {
            node.data.compliance_type for node in nodes 
            if node.data.compliance_type
        }
        
        filtered_new_nodes = [
            node for node in new_nodes 
            if node.data.compliance_type not in existing_compliance_types
        ]
        
        return nodes + filtered_new_nodes
