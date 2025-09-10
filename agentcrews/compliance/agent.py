import asyncio
import json
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from loguru import logger
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from ..mediator.models import (
    DomainType, FlowNode, FlowEdge, ReactFlowGraph, 
    ComplianceRequirement, WorkflowState
)
from ..mediator.domain_inference import DomainInferenceEngine

class ComplianceViolation(BaseModel):
    """Represents a compliance violation found in a workflow"""
    id: str
    severity: str = Field(..., description="critical, high, medium, low")
    violation_type: str
    description: str
    affected_nodes: List[str] = Field(default_factory=list)
    regulation: str
    remediation: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ComplianceReport(BaseModel):
    """Comprehensive compliance report for a workflow"""
    workflow_id: str
    domain: DomainType
    compliance_score: float = Field(..., ge=0, le=100)
    violations: List[ComplianceViolation] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

class ComplianceValidationTool(BaseTool):
    """Tool for validating workflow compliance"""
    name: str = "compliance_validator"
    description: str = "Validates workflows against regulatory compliance requirements"
    model_config = {"arbitrary_types_allowed": True}
    
    def __init__(self, domain_engine: DomainInferenceEngine, **kwargs):
        super().__init__(name="compliance_validator", description="Validates workflows against regulatory compliance requirements", **kwargs)
        object.__setattr__(self, 'domain_engine', domain_engine)
    
    def _run(self, workflow_data: str) -> str:
        """Validate workflow compliance"""
        try:
            data = json.loads(workflow_data)
            domain = DomainType(data.get('domain', 'generic'))
            nodes = [FlowNode(**node) for node in data.get('nodes', [])]
            
            # Skip compliance validation if no nodes are present
            if not nodes:
                return json.dumps({
                    "compliance_required": False,
                    "message": "No nodes present - compliance validation skipped",
                    "violations": [],
                    "score": 100.0
                })
            
            validation_result = self.domain_engine.validate_compliance(nodes, domain)
            return json.dumps(validation_result)
        except Exception as e:
            return f"Validation error: {str(e)}"

class ComplianceEnforcementTool(BaseTool):
    """Tool for enforcing compliance requirements"""
    name: str = "compliance_enforcer"
    description: str = "Automatically fixes compliance violations in workflows"
    model_config = {"arbitrary_types_allowed": True}
    
    def __init__(self, domain_engine: DomainInferenceEngine, **kwargs):
        super().__init__(name="compliance_enforcer", description="Automatically fixes compliance violations in workflows", **kwargs)
        object.__setattr__(self, 'domain_engine', domain_engine)
    
    def _run(self, workflow_data: str) -> str:
        """Enforce compliance by auto-fixing violations"""
        try:
            data = json.loads(workflow_data)
            domain = DomainType(data.get('domain', 'generic'))
            nodes = [FlowNode(**node) for node in data.get('nodes', [])]
            
            fixed_nodes = self.domain_engine.auto_fix_compliance(nodes, domain)
            return json.dumps([node.dict() for node in fixed_nodes])
        except Exception as e:
            return f"Enforcement error: {str(e)}"

class ComplianceAgent:
    """Main Compliance Agent that orchestrates compliance validation and enforcement"""
    
    COMPLIANCE_FRAMEWORKS = {
        'HIPAA': {
            'name': 'Health Insurance Portability and Accountability Act',
            'region': 'United States',
            'domain': 'Healthcare',
            'requirements': [
                'PHI protection and redaction',
                'Access controls and authentication',
                'Audit trails for all PHI access',
                'Data encryption in transit and at rest',
                'Business associate agreements',
                'Breach notification procedures'
            ]
        },
        'DISHA': {
            'name': 'Digital Information Security in Healthcare Act',
            'region': 'India',
            'domain': 'Healthcare',
            'requirements': [
                'Digital health data protection',
                'Consent management for health data',
                'Data localization requirements',
                'Healthcare provider certification',
                'Patient data portability rights',
                'Cybersecurity framework compliance'
            ]
        },
        'CLINICAL_ESTABLISHMENTS_ACT': {
            'name': 'Clinical Establishments (Registration and Regulation) Act',
            'region': 'India',
            'domain': 'Healthcare',
            'requirements': [
                'Clinical establishment registration',
                'Quality standards compliance',
                'Patient safety protocols',
                'Medical record maintenance',
                'Staff qualification verification',
                'Regular compliance audits'
            ]
        },
        'PDPB': {
            'name': 'Personal Data Protection Bill',
            'region': 'India',
            'domain': 'General',
            'requirements': [
                'Data processing consent',
                'Data localization for sensitive data',
                'Data fiduciary obligations',
                'Data subject rights (access, correction, deletion)',
                'Data breach notification',
                'Cross-border data transfer restrictions'
            ]
        },
        'RBI_GUIDELINES': {
            'name': 'Reserve Bank of India Guidelines',
            'region': 'India',
            'domain': 'Finance',
            'requirements': [
                'Data localization for payment data',
                'Cybersecurity framework',
                'Incident reporting to RBI',
                'Customer data protection',
                'Third-party risk management',
                'Business continuity planning'
            ]
        },
        'IT_ACT_2000': {
            'name': 'Information Technology Act 2000',
            'region': 'India',
            'domain': 'General',
            'requirements': [
                'Digital signature compliance',
                'Cybercrime prevention measures',
                'Data protection and privacy',
                'Electronic records management',
                'Cyber incident reporting',
                'Reasonable security practices'
            ]
        },
        'PCI-DSS': {
            'name': 'Payment Card Industry Data Security Standard',
            'region': 'Global',
            'domain': 'Finance',
            'requirements': [
                'Cardholder data protection',
                'Access controls and authentication',
                'Network security and segmentation',
                'Vulnerability management and patching',
                'Incident response and breach notification',
                'Regular security audits and risk assessments'
            ]
        },
        'FERPA': {
            'name': 'Family Educational Rights and Privacy Act',
            'region': 'United States',
            'domain': 'Education',
            'requirements': [
                'Student data protection',
                'Parental consent for data sharing',
                'Directory information management',
                'Student record maintenance',
                'Data breach notification procedures',
                'Annual FERPA notification'
            ]
        },
        'FISMA': {
            'name': 'Federal Information Security Management Act',
            'region': 'United States',
            'domain': 'Government',
            'requirements': [
                'Risk management framework',
                'Security controls and continuous monitoring',
                'Incident response and breach notification',
                'System and information integrity',
                'Security awareness and training',
                'Annual FISMA reporting'
            ]
        },
        'SOX': {
            'name': 'Sarbanes-Oxley Act',
            'region': 'United States',
            'domain': 'Enterprise',
            'requirements': [
                'Financial reporting and disclosure',
                'Internal controls and risk management',
                'Audit committee and auditor independence',
                'Code of ethics and whistleblower protection',
                'Disclosure controls and procedures',
                'Annual SOX certification'
            ]
        }
    }
    
    def __init__(self):
        self.domain_engine = DomainInferenceEngine()
        self.validation_tool = ComplianceValidationTool(self.domain_engine)
        self.enforcement_tool = ComplianceEnforcementTool(self.domain_engine)
        
        # Initialize CrewAI agents
        self.compliance_validator = Agent(
            role='Compliance Validator',
            goal='Ensure all workflows meet regulatory compliance requirements',
            backstory="""You are an expert compliance officer with deep knowledge of 
            regulatory frameworks including HIPAA, PCI-DSS, FERPA, FISMA, and SOX. 
            Your mission is to identify compliance violations and ensure workflows 
            meet all necessary regulatory standards.""",
            tools=[self.validation_tool],
            verbose=True,
            allow_delegation=False
        )
        
        self.compliance_enforcer = Agent(
            role='Compliance Enforcer',
            goal='Automatically fix compliance violations and enforce regulatory standards',
            backstory="""You are an automated compliance enforcement system that 
            takes immediate action to fix violations. You add required compliance 
            nodes, enforce mandatory data flows, and ensure no critical compliance 
            requirements are bypassed.""",
            tools=[self.enforcement_tool],
            verbose=True,
            allow_delegation=False
        )
        
        self.audit_specialist = Agent(
            role='Audit Trail Specialist',
            goal='Generate comprehensive audit trails and compliance reports',
            backstory="""You are responsible for maintaining detailed audit trails 
            of all compliance activities. You generate reports that satisfy regulatory 
            auditors and provide clear documentation of compliance measures.""",
            verbose=True,
            allow_delegation=False
        )
        
        # Create the compliance crew
        self.crew = Crew(
            agents=[self.compliance_validator, self.compliance_enforcer, self.audit_specialist],
            process=Process.sequential,
            verbose=True
        )
    
    async def validate_workflow(self, workflow_state: WorkflowState) -> ComplianceReport:
        """Validate a workflow against compliance requirements"""
        logger.info(f"Validating workflow {workflow_state.id} for {workflow_state.domain} compliance")
        
        # Create validation task
        validation_task = Task(
            description=f"""
            Validate the workflow for {workflow_state.domain.value} compliance.
            
            Workflow Details:
            - Domain: {workflow_state.domain.value}
            - Title: {workflow_state.title}
            - Nodes: {len(workflow_state.flow_graph.nodes)}
            - Description: {workflow_state.description}
            
            Check for:
            1. Required compliance nodes are present
            2. Mandatory data flows are implemented
            3. No prohibited operations exist
            4. All regulatory requirements are met
            
            Provide a detailed compliance assessment.
            """,
            agent=self.compliance_validator,
            expected_output="Detailed compliance validation report with violations and recommendations"
        )
        
        # Execute validation
        try:
            result = await asyncio.to_thread(self.crew.kickoff, tasks=[validation_task])
            
            # Generate compliance report
            violations = self._extract_violations(workflow_state, result)
            compliance_score = self._calculate_compliance_score(violations)
            
            report = ComplianceReport(
                workflow_id=workflow_state.id,
                domain=workflow_state.domain,
                compliance_score=compliance_score,
                violations=violations,
                recommendations=self._generate_recommendations(workflow_state.domain, violations),
                audit_trail=[{
                    "action": "compliance_validation",
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent": "compliance_validator",
                    "result": "completed",
                    "details": str(result)
                }]
            )
            
            logger.info(f"Compliance validation completed. Score: {compliance_score}/100")
            return report
            
        except Exception as e:
            logger.error(f"Compliance validation failed: {str(e)}")
            raise
    
    async def enforce_compliance(self, workflow_state: WorkflowState) -> Dict[str, Any]:
        """Automatically enforce compliance requirements"""
        logger.info(f"Enforcing compliance for workflow {workflow_state.id}")
        
        enforcement_task = Task(
            description=f"""
            Automatically enforce {workflow_state.domain.value} compliance requirements.
            
            Current Workflow:
            - Nodes: {[node.dict() for node in workflow_state.flow_graph.nodes]}
            - Edges: {[edge.dict() for edge in workflow_state.flow_graph.edges]}
            
            Actions to take:
            1. Add any missing required compliance nodes
            2. Ensure mandatory data flows are present
            3. Remove or modify any non-compliant elements
            4. Apply security and audit requirements
            
            Return the corrected workflow structure.
            """,
            agent=self.compliance_enforcer,
            expected_output="Corrected workflow with all compliance requirements enforced"
        )
        
        try:
            result = await asyncio.to_thread(self.crew.kickoff, tasks=[enforcement_task])
            
            # Apply enforcement results
            fixed_nodes = self.domain_engine.auto_fix_compliance(
                workflow_state.flow_graph.nodes, 
                workflow_state.domain
            )
            
            # Update workflow state
            workflow_state.flow_graph.nodes = fixed_nodes
            workflow_state.updated_at = datetime.utcnow()
            workflow_state.version += 1
            
            return {
                "success": True,
                "message": "Compliance enforcement completed",
                "nodes_added": len(fixed_nodes) - len(workflow_state.flow_graph.nodes),
                "enforcement_result": str(result),
                "updated_workflow": workflow_state.dict()
            }
            
        except Exception as e:
            logger.error(f"Compliance enforcement failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_audit_report(self, workflow_state: WorkflowState) -> Dict[str, Any]:
        """Generate comprehensive audit report"""
        logger.info(f"Generating audit report for workflow {workflow_state.id}")
        
        audit_task = Task(
            description=f"""
            Generate a comprehensive audit report for this {workflow_state.domain.value} workflow.
            
            Include:
            1. Compliance status summary
            2. Regulatory requirements checklist
            3. Risk assessment
            4. Audit trail of all compliance activities
            5. Recommendations for improvement
            6. Certification status
            
            Make it suitable for regulatory auditors and compliance officers.
            """,
            agent=self.audit_specialist,
            expected_output="Professional audit report suitable for regulatory review"
        )
        
        try:
            result = await asyncio.to_thread(self.crew.kickoff, tasks=[audit_task])
            
            return {
                "success": True,
                "report": str(result),
                "generated_at": datetime.utcnow().isoformat(),
                "workflow_id": workflow_state.id,
                "domain": workflow_state.domain.value
            }
            
        except Exception as e:
            logger.error(f"Audit report generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_violations(self, workflow_state: WorkflowState, validation_result: str) -> List[ComplianceViolation]:
        """Extract compliance violations from validation result"""
        violations = []
        
        # Use domain engine to get actual violations
        validation = self.domain_engine.validate_compliance(
            workflow_state.flow_graph.nodes, 
            workflow_state.domain
        )
        
        for violation in validation.get('violations', []):
            violations.append(ComplianceViolation(
                id=f"violation_{len(violations)}",
                severity="high",
                violation_type=violation.get('type', 'unknown'),
                description=violation.get('description', 'Compliance violation detected'),
                regulation=self._get_regulation_for_domain(workflow_state.domain),
                remediation=f"Add required {violation.get('label', 'compliance')} node"
            ))
        
        return violations
    
    def _calculate_compliance_score(self, violations: List[ComplianceViolation]) -> float:
        """Calculate compliance score based on violations"""
        if not violations:
            return 100.0
        
        # Deduct points based on violation severity
        score = 100.0
        for violation in violations:
            if violation.severity == "critical":
                score -= 25
            elif violation.severity == "high":
                score -= 15
            elif violation.severity == "medium":
                score -= 10
            elif violation.severity == "low":
                score -= 5
        
        return max(0.0, score)
    
    def _generate_recommendations(self, domain: DomainType, violations: List[ComplianceViolation]) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        if violations:
            recommendations.append(f"Address {len(violations)} compliance violations immediately")
            recommendations.append(f"Ensure all {domain.value} regulatory requirements are met")
        
        # Domain-specific recommendations
        if domain == DomainType.HEALTHCARE:
            recommendations.extend([
                "Implement PHI redaction for all patient data",
                "Enable comprehensive HIPAA audit logging",
                "Ensure end-to-end encryption for health information"
            ])
        elif domain == DomainType.FINANCE:
            recommendations.extend([
                "Validate PCI-DSS compliance for payment data",
                "Implement fraud detection mechanisms",
                "Enable transaction audit trails"
            ])
        
        return recommendations
    
    def _get_regulation_for_domain(self, domain: DomainType) -> str:
        """Get primary regulation for domain"""
        regulation_map = {
            DomainType.HEALTHCARE: "HIPAA",
            DomainType.FINANCE: "PCI-DSS",
            DomainType.EDUCATION: "FERPA",
            DomainType.GOVERNMENT: "FISMA",
            DomainType.ENTERPRISE: "SOX"
        }
        return regulation_map.get(domain, "General Compliance")
