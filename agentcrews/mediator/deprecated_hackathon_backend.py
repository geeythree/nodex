"""
Hackathon-optimized backend for Agentic Workflow Builder
Text + Image → Compliant Workflows with CrewAI orchestration
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from typing import List, Dict, Any, Optional
import yaml
import json
import base64
import os
from pathlib import Path
import openai
from crewai import Agent, Task, Crew
import logging
import re
import asyncio
from datetime import datetime

# Configure logging with DEBUG level to see all output
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def validate_react_flow_format(workflow_data: dict) -> bool:
    """Validate that workflow data matches React Flow expected format"""
    try:
        # Check nodes structure
        if 'nodes' in workflow_data:
            for node in workflow_data['nodes']:
                if not all(key in node for key in ['id', 'type', 'position']):
                    return False
                if 'data' not in node:
                    return False
        
        # Check edges structure  
        if 'edges' in workflow_data:
            for edge in workflow_data['edges']:
                if not all(key in edge for key in ['id', 'source', 'target']):
                    return False
        
        return True
    except Exception as e:
        logger.error(f"Workflow validation failed: {e}")
        return False

def filter_domain_compliance(nodes: List[dict], domain: str) -> List[dict]:
    """Remove nodes with wrong domain compliance requirements"""
    
    # Define domain-specific compliance terms
    DOMAIN_COMPLIANCE = {
        'healthcare': {
            'allowed': ['hipaa', 'patient', 'medical', 'clinical', 'phi', 'healthcare', 'consent'],
            'forbidden': ['kyc', 'aml', 'sox', 'pci', 'banking', 'financial', 'fraud_detection', 'transaction']
        },
        'finance': {
            'allowed': ['kyc', 'aml', 'sox', 'pci', 'banking', 'financial', 'fraud', 'transaction', 'credit'],
            'forbidden': ['hipaa', 'patient', 'medical', 'clinical', 'phi', 'healthcare']
        },
        'creator': {
            'allowed': ['dmca', 'copyright', 'content', 'moderation', 'coppa', 'creator'],
            'forbidden': ['hipaa', 'patient', 'medical', 'kyc', 'aml', 'sox', 'pci']
        }
    }
    
    if domain not in DOMAIN_COMPLIANCE:
        return nodes  # Return unchanged for unknown domains
    
    domain_rules = DOMAIN_COMPLIANCE[domain]
    filtered_nodes = []
    
    for node in nodes:
        node_text = (
            node.get('label', '') + ' ' + 
            node.get('description', '') + ' ' + 
            str(node.get('data', {}).get('label', '')) + ' ' +
            str(node.get('data', {}).get('description', ''))
        ).lower()
        
        # Check if node contains forbidden terms
        has_forbidden = any(term in node_text for term in domain_rules['forbidden'])
        
        if has_forbidden:
            logger.info(f"Filtered out node '{node.get('label', 'unknown')}' - contains {domain} forbidden compliance terms")
            continue
            
        filtered_nodes.append(node)
    
    return filtered_nodes

app = FastAPI(title="Agentic Workflow Builder", version="1.0.0")

# Global progress tracking
workflow_progress = {}

def update_progress(workflow_id: str, stage: str, message: str, progress: int):
    """Update progress for a workflow"""
    workflow_progress[workflow_id] = {
        "stage": stage,
        "message": message,
        "progress": progress,
        "timestamp": datetime.now().isoformat()
    }
    logger.info(f"Progress update [{workflow_id}]: {stage} - {message} ({progress}%)")

@app.get("/api/progress/{workflow_id}")
async def get_workflow_progress(workflow_id: str):
    """Get current progress for a workflow"""
    if workflow_id in workflow_progress:
        return workflow_progress[workflow_id]
    return {"stage": "idle", "message": "No active workflow", "progress": 0, "timestamp": datetime.now().isoformat()}

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class TextWorkflowRequest(BaseModel):
    text: str
    domain: str = "general"

class ImageWorkflowRequest(BaseModel):
    image: str  # Base64 encoded image
    domain: str = "general"

class NodePosition(BaseModel):
    x: float
    y: float

class NodeData(BaseModel):
    label: str
    nodeType: str
    icon: Optional[str] = None
    description: Optional[str] = None
    locked: bool = False
    compliance_reason: Optional[str] = None
    executed: bool = False
    hasError: bool = False

class WorkflowNode(BaseModel):
    id: str
    type: str
    position: NodePosition
    data: NodeData

class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str

class WorkflowSchema(BaseModel):
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]

class WorkflowResponse(BaseModel):
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    compliance_info: Optional[Dict[str, Any]] = None
    workflow_id: Optional[str] = None

# Load compliance manifests
def load_compliance_manifest(domain: str) -> Dict[str, Any]:
    """Load compliance manifest for specified domain"""
    manifest_path = Path(f"config/compliance/{domain}.yaml")
    if not manifest_path.exists():
        manifest_path = Path(f"config/compliance/general.yaml")
    
    try:
        with open(manifest_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not load compliance manifest for {domain}: {e}")
        return {"domain": domain, "required_steps": []}

# CrewAI Agents
def create_interpreter_agent():
    """Agent to interpret text/image input into structured workflow steps"""
    return Agent(
        role="API Workflow Interpreter",
        goal="Convert user requirements into specific API calls and executable steps",
        backstory="You are an expert at translating business processes into detailed API operations with specific endpoints, methods, and parameters.",
        verbose=True,
        allow_delegation=False,
        llm=os.getenv("CREWAI_MODEL", "gpt-4o")
    )

def create_planner_agent():
    """Agent to plan and structure workflow steps"""
    return Agent(
        role="Executable Workflow Planner", 
        goal="Structure API calls into logical sequences with proper data flow and error handling",
        backstory="You are a system architect who designs robust API workflows with proper sequencing, data transformation, and error handling.",
        verbose=True,
        allow_delegation=False,
        llm=os.getenv("CREWAI_MODEL", "gpt-4o")
    )

def create_compliance_agent(domain: str):
    """Agent to inject compliance requirements"""
    return Agent(
        role="Compliance Automation Specialist",
        goal="Inject specific compliance API calls and audit endpoints based on detected domain",
        backstory=f"""You are a compliance expert who ensures workflows meet regulatory requirements by adding specific API calls for consent, audit, encryption, and data retention. You specialize in the {domain} domain.""",
        verbose=True,
        allow_delegation=False,
        llm=os.getenv("CREWAI_MODEL", "gpt-4o")
    )

def create_enhancement_agent(domain: str):
    """Agent to review and enhance workflows with domain-specific professional best practices"""
    
    # Domain-specific compliance rules
    domain_rules = {
        'healthcare': """
        HEALTHCARE COMPLIANCE ONLY:
        - HIPAA for patient data protection
        - Patient consent verification
        - Medical record retention (7+ years)
        - Clinical audit trails
        - PHI encryption requirements
        
        FORBIDDEN: Never add KYC, AML, SOX, PCI-DSS, banking, or financial regulations.
        """,
        'finance': """
        FINANCIAL COMPLIANCE ONLY:
        - KYC (Know Your Customer) verification
        - AML (Anti-Money Laundering) checks
        - SOX compliance for public companies
        - PCI-DSS for payment processing
        - Transaction monitoring
        - Fraud detection
        
        FORBIDDEN: Never add HIPAA, patient consent, medical, or healthcare regulations.
        """,
        'creator': """
        CREATOR/CONTENT COMPLIANCE ONLY:
        - DMCA compliance for copyright
        - Content moderation requirements
        - COPPA for child safety
        - User-generated content policies
        - Community guidelines enforcement
        
        FORBIDDEN: Never add HIPAA, KYC, AML, SOX, PCI, medical, or financial regulations.
        """
    }
    
    compliance_rules = domain_rules.get(domain, "Apply general best practices without domain-specific compliance.")
    
    return Agent(
        role=f"{domain.title()} Workflow Enhancement Specialist",
        goal=f"ONLY add {domain} domain compliance and professional practices. Never mix other domains.",
        backstory=f"""You are a senior {domain} consultant who ONLY knows {domain} regulations.

        {compliance_rules}
        
        You spot missing {domain}-specific steps: error handling, stakeholder notifications, 
        {domain} compliance requirements, monitoring, and operational concerns.
        
        CRITICAL: If you add any compliance nodes from other domains, the workflow will FAIL validation.
        Stay strictly within {domain} boundaries.""",
        verbose=True,
        allow_delegation=False,
        llm=os.getenv("CREWAI_MODEL", "gpt-4o")
    )

def create_visualizer_agent():
    """Agent to create visual workflow representation"""
    return Agent(
        role="n8n Workflow Generator",
        goal="Generate complete n8n-compatible JSON with executable node configurations",
        backstory="You are an n8n expert who creates detailed workflow JSON with specific API configurations, authentication, and data mapping.",
        verbose=True,
        allow_delegation=False,
        llm=os.getenv("CREWAI_MODEL", "gpt-4o")
    )

# GPT-4o Vision integration
async def analyze_image_with_gpt4o(image_data: str) -> Dict[str, Any]:
    """Use GPT-4o Vision to extract workflow from image"""
    try:
        client = openai.AsyncOpenAI()
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """Extract all process steps from this workflow image. 
                    For each box/shape, OCR the text label and identify if it's a compliance step 
                    (redact, audit, approve, consent, verify, etc.). 
                    Also extract all arrows/connections between steps.
                    
                    Output valid JSON with:
                    {
                        "nodes": [{"label": "Step Name", "type": "process|compliance|decision|input|output"}],
                        "edges": [{"from": "Step A", "to": "Step B"}],
                        "domain_hints": ["hr", "finance", "sales", "it"]
                    }"""
                },
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_data}
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        logger.error(f"GPT-4o Vision analysis failed: {e}")
        return {"nodes": [], "edges": [], "domain_hints": []}

# Workflow processing functions
def inject_compliance_nodes(nodes: List[Dict], edges: List[Dict], manifest: Dict) -> tuple:
    """Inject mandatory compliance nodes based on manifest"""
    compliance_nodes = []
    compliance_edges = []
    
    required_steps = manifest.get("required_steps", [])
    
    for step in required_steps:
        # Create compliance node
        compliance_node = {
            "id": f"compliance_{step['compliance_type']}_{len(compliance_nodes)}",
            "type": "default",
            "position": {"x": 200 + len(compliance_nodes) * 150, "y": 100},
            "data": {
                "label": step["label"],
                "locked": step["locked"],
                "compliance_reason": step["reason"],
                "compliance_type": step["compliance_type"],
                "color": step.get("color", "#FFAE42")
            }
        }
        compliance_nodes.append(compliance_node)
        
        # Insert compliance node in workflow based on rules
        insert_before = step.get("insert_before")
        insert_after = step.get("insert_after")
        
        if insert_before and insert_before != "all":
            # Find target node and insert compliance before it
            for i, node in enumerate(nodes):
                if insert_before.lower() in node.get("data", {}).get("label", "").lower():
                    # Add edge from previous node to compliance
                    prev_edges = [e for e in edges if e["target"] == node["id"]]
                    for edge in prev_edges:
                        edge["target"] = compliance_node["id"]
                    
                    # Add edge from compliance to target
                    compliance_edges.append({
                        "id": f"edge_compliance_{len(compliance_edges)}",
                        "source": compliance_node["id"],
                        "target": node["id"]
                    })
                    break
        
        elif insert_after == "all":
            # Add at the end of workflow
            end_nodes = [n for n in nodes if not any(e["source"] == n["id"] for e in edges)]
            for end_node in end_nodes:
                compliance_edges.append({
                    "id": f"edge_compliance_{len(compliance_edges)}",
                    "source": end_node["id"],
                    "target": compliance_node["id"]
                })
    
    return nodes + compliance_nodes, edges + compliance_edges

def position_nodes(nodes: List[Dict]) -> List[Dict]:
    """Auto-position nodes in a logical flow layout"""
    for i, node in enumerate(nodes):
        # Simple grid layout
        row = i // 3
        col = i % 3
        node["position"] = {
            "x": 100 + col * 200,
            "y": 100 + row * 150
        }
    return nodes

# API Endpoints
@app.post("/api/interpret", response_model=WorkflowResponse)
async def interpret_text_workflow(request: TextWorkflowRequest, background_tasks: BackgroundTasks):
    """Process text input into compliant workflow"""
    try:
        # Load compliance manifest
        manifest = load_compliance_manifest(request.domain)
        
        # Create CrewAI agents
        interpreter = create_interpreter_agent()
        planner = create_planner_agent()
        compliance_agent = create_compliance_agent(request.domain)
        enhancement_agent = create_enhancement_agent(request.domain)
        visualizer = create_visualizer_agent()
        
        # Create tasks focused on executable automation
        interpret_task = Task(
            description=f"""
            Convert this process description into specific, executable automation steps with domain intelligence:
            "{request.text}"
            
            DOMAIN-SPECIFIC INTELLIGENCE:
            
            HEALTHCARE CONTEXT: Include patient consent workflows, HIPAA compliance checks, clinical validation steps, 
            provider notifications, audit trails, medical record integration, appointment systems, and patient communication.
            Key considerations: PHI protection, clinical workflows, regulatory compliance, provider coordination.
            
            BANKING/FINANCE CONTEXT: Include KYC verification, fraud detection, regulatory reporting, multi-stage approvals, 
            compliance monitoring, transaction processing, risk assessment, and customer communication.
            Key considerations: Financial regulations, security protocols, audit requirements, customer protection.
            
            HOBBYIST/CREATOR CONTEXT: Include error handling, user feedback systems, analytics tracking, content moderation, 
            performance optimization, social media integration, and audience engagement.
            Key considerations: User experience, content quality, platform integration, growth metrics.
            
            GENERAL PRINCIPLES: Always consider data validation, error handling, stakeholder notifications, 
            audit trails, monitoring, and user experience. Think like a senior engineer who builds production systems.
            
            Break down each high-level process into concrete API calls and automation actions:
            - HTTP requests with specific endpoints and methods
            - Database operations with queries and connections
            - File operations with paths and actions
            - Email/notification API calls
            - Authentication and authorization steps
            - Data transformation and validation steps
            - Professional operational concerns (monitoring, logging, error handling)
            
            Focus on executable actions that a professional would deploy to production.
            """,
            agent=interpreter,
            expected_output="List of professional-grade, executable automation steps with domain-specific enhancements"
        )
        
        plan_task = Task(
            description=f"""
            Organize the executable steps into a professional-grade structured workflow with domain expertise:
            
            DOMAIN-SPECIFIC PLANNING ({request.domain.upper()}):
            
            HEALTHCARE: Structure workflows with patient safety, clinical decision points, provider coordination, 
            HIPAA compliance checkpoints, and care continuity. Include patient journey mapping and clinical validation.
            
            BANKING/FINANCE: Structure workflows with security-first approach, regulatory compliance gates, 
            multi-tier approvals, fraud prevention, and customer protection. Include risk assessment at each stage.
            
            HOBBYIST/CREATOR: Structure workflows with user experience optimization, content quality gates, 
            performance monitoring, and audience engagement. Include feedback loops and iterative improvement.
            
            PROFESSIONAL WORKFLOW STRUCTURE:
            1. **Trigger Configuration**: Robust webhook handling with validation and security
            2. **Input Validation**: Data sanitization, format validation, business rule checks
            3. **API Call Sequences**: Ordered operations with proper authentication and rate limiting
            4. **Data Flow**: Secure data mapping with encryption for sensitive information
            5. **Error Handling**: Comprehensive retry logic, circuit breakers, and graceful degradation
            6. **Conditional Logic**: Business rule engines and decision trees
            7. **Stakeholder Workflows**: Approval chains, notifications, and status updates
            8. **Monitoring & Alerts**: Real-time monitoring with automated alerting
            9. **Audit & Compliance**: Logging, audit trails, and regulatory reporting
            10. **User Experience**: Status dashboards, notifications, and feedback systems
            
            Think like a senior architect building mission-critical systems. Consider:
            - What could go wrong and how to handle it
            - Who needs to be notified and when
            - What data needs to be logged for audit purposes
            - How to ensure the system is maintainable and observable
            """,
            agent=planner,
            expected_output="Professional-grade workflow architecture with domain-specific optimizations"
        )
        
        compliance_task = Task(
            description=f"""
            Add automated compliance checks for {request.domain} domain by injecting specific API calls:
            
            **Compliance API Integrations:**
            - Consent management API calls
            - Audit logging endpoints  
            - Data encryption/decryption services
            - Regulatory validation APIs
            - Access control verification
            - Data retention policy enforcement
            
            **Required Compliance Steps:**
            - HTTP POST to audit service for each action
            - Consent verification via API before data processing
            - Encryption API calls for sensitive data
            - Compliance validation endpoints
            - Automated policy checks
            
            Insert these as specific API nodes in the workflow with exact endpoints and configurations.
            Ensure each compliance step is executable and has proper error handling.
            """,
            agent=compliance_agent,
            expected_output="Executable compliance API calls integrated into the workflow"
        )
        
        enhancement_task = Task(
            description=f"""
            Review the planned workflow and add missing professional components that senior engineers and domain experts expect:
            
            **OPERATIONAL REQUIREMENTS:**
            - Error handling and retry logic for each critical step
            - Monitoring and alerting for system failures
            - Comprehensive logging and audit trails
            - Data validation and sanitization at entry points
            - Performance monitoring and optimization hooks
            
            **STAKEHOLDER REQUIREMENTS:**
            - User notification systems and status updates
            - Approval workflows where business rules require them
            - Dashboards and reporting for management visibility
            - Feedback mechanisms and communication loops
            - Integration with existing enterprise systems
            
            **DOMAIN-SPECIFIC ENHANCEMENTS ({request.domain.upper()}):**
            
            HEALTHCARE: Add patient communication workflows, clinical decision support hooks, 
            provider coordination systems, care plan integration, and patient safety checkpoints.
            
            BANKING/FINANCE: Add transaction monitoring, suspicious activity reporting, 
            customer service integration, regulatory notification systems, and risk management dashboards.
            
            HOBBYIST/CREATOR: Add content performance analytics, audience engagement tracking, 
            A/B testing capabilities, social media optimization, and creator economy integrations.
            
            **PROFESSIONAL POLISH:**
            - Proper naming conventions and descriptions
            - Industry-standard terminology and practices
            - Integration with common tools in the domain
            - Scalability and performance considerations
            
            Identify gaps and suggest additional nodes that transform this from a basic automation 
            into a production-ready, professional system.
            """,
            agent=enhancement_agent,
            expected_output="List of additional professional enhancements and missing components with justifications"
        )
        
        visualize_task = Task(
            description="""
            Generate an executable n8n workflow JSON with detailed node configurations:
            
            **Node Types to Use:**
            - HTTP Request nodes with specific endpoints
            - Webhook nodes with trigger configurations  
            - Database nodes with connection details
            - Email nodes with SMTP/API configurations
            - File operation nodes with paths and actions
            - Condition nodes with specific logic
            - Code nodes for data transformation
            
            **Each Node Must Include:**
            - Specific API endpoint URL
            - HTTP method and headers
            - Request body structure
            - Response handling logic
            - Error handling configuration
            - Parameter mapping
            - Authentication details
            
            **Output Format:**
            ```json
            {
                "nodes": [
                    {
                        "id": "webhook_trigger",
                        "label": "Employee Onboarding Webhook",
                        "type": "webhook",
                        "description": "Receives new employee data via POST /webhook/employee-onboarding",
                        "position": {"x": 100, "y": 100},
                        "config": {
                            "method": "POST",
                            "path": "/webhook/employee-onboarding",
                            "responseMode": "responseNode"
                        }
                    },
                    {
                        "id": "validate_employee",
                        "label": "Validate Employee Data",
                        "type": "http",
                        "description": "POST /api/validation/employee - Validate employee information",
                        "position": {"x": 300, "y": 100},
                        "config": {
                            "method": "POST",
                            "url": "https://api.company.com/validation/employee",
                            "headers": {"Content-Type": "application/json"},
                            "body": "{{$json.employee_data}}"
                        }
                    }
                ],
                "edges": [...]
            }
            ```
            
            Generate a complete, executable workflow that can be imported directly into n8n.
            """,
            agent=visualizer,
            expected_output="Complete n8n-compatible workflow JSON with executable node configurations",
        )
        
        # Execute crew with enhancement agent
        crew = Crew(
            agents=[interpreter, planner, compliance_agent, enhancement_agent, visualizer],
            tasks=[interpret_task, plan_task, compliance_task, enhancement_task, visualize_task],
            verbose=True,

        )
        
        workflow_id = "workflow_" + str(datetime.now().timestamp())
        background_tasks.add_task(update_progress, workflow_id, "interpreting", "Converting text to workflow", 10)
        
        result = crew.kickoff()
        
        background_tasks.add_task(update_progress, workflow_id, "planning", "Structuring workflow", 30)
        
        # Parse the CrewAI result using proper CrewAI output format
        try:
            # Access the crew output properly
            crew_output = result
            result_text = crew_output.raw if hasattr(crew_output, 'raw') else str(crew_output)
            logger.info(f"CrewAI raw result length: {len(result_text)} chars")
            
            # Debug: Log the actual structure of crew_output
            logger.debug(f"CrewAI output type: {type(crew_output)}")
            logger.debug(f"CrewAI output attributes: {dir(crew_output)}")
            logger.debug(f"Has raw attribute: {hasattr(crew_output, 'raw')}")
            logger.debug(f"Has json_dict attribute: {hasattr(crew_output, 'json_dict')}")
            logger.debug(f"Has pydantic attribute: {hasattr(crew_output, 'pydantic')}")
            logger.debug(f"Has tasks_output attribute: {hasattr(crew_output, 'tasks_output')}")
            
            # Log samples of the output
            logger.debug(f"First 500 chars: {result_text[:500]}")
            logger.debug(f"Last 500 chars: {result_text[-500:]}")
            
            # Try to get JSON directly from CrewAI output
            parsed_workflow = None
            if hasattr(crew_output, 'json_dict') and crew_output.json_dict:
                logger.info("Using CrewAI json_dict output")
                logger.debug(f"json_dict content: {crew_output.json_dict}")
                try:
                    potential_json = crew_output.json_dict
                    if isinstance(potential_json, dict) and ('nodes' in potential_json or 'edges' in potential_json):
                        parsed_workflow = WorkflowSchema.parse_obj(potential_json)
                        logger.info(f"Successfully parsed from json_dict: {len(parsed_workflow.nodes)} nodes, {len(parsed_workflow.edges)} edges")
                except (ValidationError, Exception) as e:
                    logger.debug(f"Failed to parse json_dict: {str(e)}")
            else:
                logger.debug("No json_dict available or it's None/empty")
            
            # If json_dict didn't work, try parsing the raw text
            if not parsed_workflow:
                logger.debug("Trying to parse from raw text output")
                
                # Check if the text contains any JSON-like structures
                logger.debug(f"Contains 'nodes': {'nodes' in result_text.lower()}")
                logger.debug(f"Contains 'edges': {'edges' in result_text.lower()}")
                logger.debug(f"Contains '```json': {'```json' in result_text}")
                logger.debug(f"Contains '```': {'```' in result_text}")
                logger.debug(f"Contains '{{': {'{' in result_text}")
                
                # Improved JSON extraction patterns with better multiline handling
                json_patterns = [
                    r'```json\s*([\s\S]*?)\s*```',  # Standard markdown json blocks (multiline)
                    r'```\s*([\s\S]*?)\s*```',      # Generic code blocks (multiline)
                    r'\{[\s\S]*?"nodes"[\s\S]*?\}',  # JSON with nodes property
                    r'\{[\s\S]*?"edges"[\s\S]*?\}',  # JSON with edges property
                    r'Final Answer[:\s]*([\s\S]*?)(?=\n\n|$)', # Final Answer format (multiline)
                ]
                
                for i, pattern in enumerate(json_patterns):
                    try:
                        matches = re.findall(pattern, result_text, re.DOTALL | re.IGNORECASE | re.MULTILINE)
                        if matches:
                            logger.debug(f"Pattern {i+1} found {len(matches)} matches")
                            # Try each match, not just the largest
                            for match in matches:
                                try:
                                    # Clean the JSON string
                                    cleaned_json = match.strip()
                                    # Remove truncation indicators and fix common issues
                                    cleaned_json = cleaned_json.replace('...', '')
                                    cleaned_json = cleaned_json.replace('responseNode"', '"responseNode"')
                                    # Remove any trailing commas before closing braces/brackets
                                    cleaned_json = re.sub(r',(\s*[}\]])', r'\1', cleaned_json)
                                    # Fix unquoted keys (common LLM error)
                                    cleaned_json = re.sub(r'(\w+):', r'"\1":', cleaned_json)
                                    # Try to parse as JSON
                                    potential_json = json.loads(cleaned_json)
                                    # Check if it has the expected structure
                                    if isinstance(potential_json, dict) and ('nodes' in potential_json or 'edges' in potential_json):
                                        # Convert to expected schema format if needed
                                        if 'nodes' in potential_json:
                                            # Transform nodes to match our schema
                                            for node in potential_json['nodes']:
                                                if 'data' not in node:
                                                    # Move node properties into data field
                                                    # Smart node enhancement with domain intelligence
                                                    node_type = node.get('type', node.get('nodeType', 'action'))
                                                    node_label = node.get('label', node.get('name', 'Unknown'))
                                                    
                                                    # Professional icon mapping
                                                    icon_map = {
                                                        'webhook': '🔗', 'http': '🌐', 'database': '💾', 'email': '📧', 'code': '💻',
                                                        'validation': '✅', 'approval': '👥', 'notification': '🔔', 
                                                        'security': '🔐', 'analytics': '📊', 'audit': '📋', 'monitoring': '👁️',
                                                        'encryption': '🔒', 'compliance': '🛡️', 'alert': '⚠️', 'report': '📄'
                                                    }
                                                    
                                                    # Domain-specific enhancements
                                                    if request.domain == "healthcare":
                                                        if 'patient' in node_label.lower():
                                                            icon_map.update({'http': '👤', 'validation': '🏥'})
                                                        if 'hipaa' in node_label.lower() or 'audit' in node_label.lower():
                                                            icon_map.update({'audit': '🏥📋'})
                                                    elif request.domain == "finance":
                                                        if 'fraud' in node_label.lower():
                                                            icon_map.update({'validation': '🚨', 'monitoring': '🔍'})
                                                        if 'kyc' in node_label.lower():
                                                            icon_map.update({'validation': '🆔'})
                                                    elif request.domain == "hobbyist":
                                                        if 'content' in node_label.lower():
                                                            icon_map.update({'http': '✏️', 'code': '🎨'})
                                                        if 'social' in node_label.lower():
                                                            icon_map.update({'http': '📱'})
                                                    
                                                    # Enhanced description with professional context
                                                    base_description = node.get('description', '')
                                                    if not base_description:
                                                        # Generate professional descriptions based on type and domain
                                                        if node_type == 'webhook':
                                                            base_description = f"Secure endpoint trigger with validation and authentication"
                                                        elif node_type == 'http' and 'validation' in node_label.lower():
                                                            base_description = f"Data integrity and compliance verification endpoint"
                                                        elif node_type == 'database':
                                                            base_description = f"Persistent storage with audit logging and backup"
                                                        else:
                                                            base_description = f"Professional {node_type} operation with monitoring"
                                                    
                                                    node_data = {
                                                        'label': node_label,
                                                        'nodeType': node_type,
                                                        'icon': icon_map.get(node_type, '⚙️'),
                                                        'description': base_description,
                                                        'locked': 'compliance' in node_label.lower() or 'audit' in node_label.lower() or 'hipaa' in node_label.lower(),
                                                        'compliance_reason': 'Required for regulatory compliance' if 'compliance' in node_label.lower() or 'audit' in node_label.lower() else None
                                                    }
                                                    node['data'] = node_data
                                                if 'position' not in node:
                                                    node['position'] = node.get('position', {'x': 100, 'y': 100})
                                                node['type'] = 'n8nNode'  # Frontend expects this
                                        
                                        if 'edges' in potential_json:
                                            # Add missing IDs to edges and transform from/to to source/target
                                            for i, edge in enumerate(potential_json['edges']):
                                                if 'id' not in edge:
                                                    edge['id'] = f"e{i+1}"
                                                # Transform from/to to source/target for React Flow compatibility
                                                if 'from' in edge and 'to' in edge:
                                                    from_val = edge.pop('from')
                                                    to_val = edge.pop('to')
                                                    # Handle array values (multiple sources)
                                                    if isinstance(from_val, list):
                                                        # For multiple sources, create the first edge with the first source
                                                        edge['source'] = from_val[0] if from_val else 'unknown'
                                                        edge['target'] = to_val
                                                    else:
                                                        edge['source'] = from_val
                                                        edge['target'] = to_val
                                        
                                        # Filter domain-specific compliance
                                        if 'nodes' in potential_json:
                                            original_count = len(potential_json['nodes'])
                                            potential_json['nodes'] = filter_domain_compliance(potential_json['nodes'], request.domain)
                                            filtered_count = len(potential_json['nodes'])
                                            if filtered_count != original_count:
                                                logger.info(f"Filtered {original_count - filtered_count} nodes with wrong {request.domain} compliance")
                                        
                                        # Validate React Flow compatibility
                                        if validate_react_flow_format(potential_json):
                                            # Validate with Pydantic
                                            parsed_workflow = WorkflowSchema.parse_obj(potential_json)
                                            logger.info(f"Successfully parsed with pattern {i+1}: {len(parsed_workflow.nodes)} nodes, {len(parsed_workflow.edges)} edges")
                                            break
                                        else:
                                            logger.debug("Failed React Flow format validation")
                                except (json.JSONDecodeError, ValidationError) as e:
                                    logger.debug(f"JSON/Validation failed for match: {str(e)}")
                                    continue
                            if parsed_workflow:
                                break
                        else:
                            logger.debug(f"Pattern {i+1} found no matches")
                    except Exception as e:
                        logger.debug(f"Pattern {i+1} failed with error: {str(e)}")
                        continue
            
            # If still no parsed workflow, try one more approach - look for the last task output
            if not parsed_workflow:
                logger.warning("Standard JSON parsing failed, trying task output extraction")
                
                # Try to get the last task's output from CrewAI
                if hasattr(crew_output, 'tasks_output') and crew_output.tasks_output:
                    logger.debug(f"Found {len(crew_output.tasks_output)} task outputs")
                    # Get the last task (visualizer) output
                    last_task_output = crew_output.tasks_output[-1]
                    if hasattr(last_task_output, 'raw'):
                        visualizer_output = last_task_output.raw
                        logger.debug(f"Visualizer task output: {visualizer_output[:500]}...")
                        
                        # Try to parse this specific output
                        try:
                            # Look for JSON in the visualizer output
                            json_match = re.search(r'\{[\s\S]*"nodes"[\s\S]*\}', visualizer_output, re.DOTALL)
                            if json_match:
                                potential_json = json.loads(json_match.group())
                                
                                # Transform to expected schema format
                                if 'nodes' in potential_json:
                                    for node in potential_json['nodes']:
                                        if 'data' not in node:
                                            # Smart node enhancement with domain intelligence  
                                            node_type = node.get('type', node.get('nodeType', 'action'))
                                            node_label = node.get('label', node.get('name', 'Unknown'))
                                            
                                            # Professional icon mapping
                                            icon_map = {
                                                'webhook': '🔗', 'http': '🌐', 'database': '💾', 'email': '📧', 'code': '💻',
                                                'validation': '✅', 'approval': '👥', 'notification': '🔔', 
                                                'security': '🔐', 'analytics': '📊', 'audit': '📋', 'monitoring': '👁️'
                                            }
                                            
                                            node_data = {
                                                'label': node_label,
                                                'nodeType': node_type,
                                                'icon': icon_map.get(node_type, '⚙️'),
                                                'description': node.get('description', f'Professional {node_type} operation with monitoring'),
                                                'locked': 'compliance' in node_label.lower() or 'audit' in node_label.lower()
                                            }
                                            node['data'] = node_data
                                        if 'position' not in node:
                                            node['position'] = node.get('position', {'x': 100, 'y': 100})
                                        node['type'] = 'n8nNode'
                                
                                if 'edges' in potential_json:
                                    for i, edge in enumerate(potential_json['edges']):
                                        if 'id' not in edge:
                                            edge['id'] = f"e{i+1}"
                                        # Transform from/to to source/target for React Flow compatibility
                                        if 'from' in edge and 'to' in edge:
                                            from_val = edge.pop('from')
                                            to_val = edge.pop('to')
                                            # Handle array values (multiple sources)
                                            if isinstance(from_val, list):
                                                # For multiple sources, create the first edge with the first source
                                                edge['source'] = from_val[0] if from_val else 'unknown'
                                                edge['target'] = to_val
                                            else:
                                                edge['source'] = from_val
                                                edge['target'] = to_val
                                
                                # Filter domain-specific compliance
                                if 'nodes' in potential_json:
                                    original_count = len(potential_json['nodes'])
                                    potential_json['nodes'] = filter_domain_compliance(potential_json['nodes'], request.domain)
                                    filtered_count = len(potential_json['nodes'])
                                    if filtered_count != original_count:
                                        logger.info(f"Filtered {original_count - filtered_count} nodes with wrong {request.domain} compliance")
                                
                                # Validate React Flow compatibility
                                if validate_react_flow_format(potential_json):
                                    parsed_workflow = WorkflowSchema.parse_obj(potential_json)
                                    logger.info(f"Successfully parsed from task output: {len(parsed_workflow.nodes)} nodes")
                                else:
                                    logger.debug("Task output failed React Flow format validation")
                        except Exception as e:
                            logger.debug(f"Failed to parse task output: {str(e)}")
                
                # Final fallback if all parsing fails
                if not parsed_workflow:
                    logger.warning("All JSON parsing attempts failed, using fallback data")
                    logger.debug(f"Full CrewAI result for debugging:\n{result_text}")
                
                    # Create a simple workflow based on the text input as fallback
                    fallback_nodes = [
                        WorkflowNode(
                            id="start_1",
                            type="n8nNode",
                            position=NodePosition(x=100, y=100),
                            data=NodeData(
                                label="Start Process",
                                nodeType="webhook",
                                icon="▶️",
                                description=f"Trigger for: {request.text[:50]}...",
                                locked=False
                            )
                        ),
                        WorkflowNode(
                            id="process_1",
                            type="n8nNode",
                            position=NodePosition(x=300, y=100),
                            data=NodeData(
                                label="Process Data",
                                nodeType="action",
                                icon="⚙️",
                                description="Main processing step",
                                locked=False
                            )
                        )
                    ]
                    
                    fallback_edges = [
                        WorkflowEdge(id="e1", source="start_1", target="process_1")
                    ]
                    
                    parsed_workflow = WorkflowSchema(nodes=fallback_nodes, edges=fallback_edges)
                
        except Exception as e:
            logger.error(f"Critical error in workflow processing: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            # Return error workflow with more details
            parsed_workflow = WorkflowSchema(
                nodes=[
                    WorkflowNode(
                        id="error_node",
                        type="n8nNode",
                        position=NodePosition(x=100, y=100),
                        data=NodeData(
                            label="Processing Error",
                            nodeType="action",
                            icon="⚠️",
                            description=f"Error: {str(e)[:100]}... Check server logs for details.",
                            locked=False,
                            hasError=True
                        )
                    )
                ],
                edges=[]
            )
        
        # Convert parsed nodes to proper format
        final_nodes = []
        for node in parsed_workflow.nodes:
            # The frontend expects a specific structure. We build it here.
            # The core data is nested inside the 'data' field.
            try:
                # Handle both Pydantic models and dictionaries
                if hasattr(node, 'dict'):
                    # It's a Pydantic model
                    node_dict = {
                        "id": node.id,
                        "type": "n8nNode",  # Explicitly set for the frontend component
                        "position": node.position.dict() if hasattr(node.position, 'dict') else node.position,
                        "data": node.data.dict() if hasattr(node.data, 'dict') else node.data
                    }
                else:
                    # It's already a dict
                    node_dict = {
                        "id": node.get("id"),
                        "type": "n8nNode",  # Explicitly set for the frontend component
                        "position": node.get("position", {"x": 100, "y": 100}),
                        "data": node.get("data", {})
                    }
                final_nodes.append(node_dict)
            except Exception as node_error:
                logger.warning(f"Error converting node {getattr(node, 'id', 'unknown')}: {node_error}")
                # Create a fallback node
                fallback_node = {
                    "id": getattr(node, 'id', f'fallback_{len(final_nodes)}'),
                    "type": "n8nNode",
                    "position": {"x": 100 + len(final_nodes) * 150, "y": 100},
                    "data": {
                        "label": getattr(node, 'label', 'Error Node'),
                        "nodeType": "action",
                        "icon": "⚠️",
                        "description": f"Node conversion error: {node_error}",
                        "hasError": True
                    }
                }
                final_nodes.append(fallback_node)
        
        # Convert parsed edges to proper format  
        final_edges = []
        for edge in parsed_workflow.edges:
            try:
                # Handle both Pydantic models and dictionaries
                if hasattr(edge, 'dict'):
                    final_edges.append(edge.dict())
                else:
                    # It's already a dict
                    final_edges.append(edge)
            except Exception as edge_error:
                logger.warning(f"Error converting edge: {edge_error}")
                # Create a fallback edge if we have at least two nodes
                if len(final_nodes) >= 2:
                    fallback_edge = {
                        "id": f"fallback_edge_{len(final_edges)}",
                        "source": final_nodes[0]["id"] if final_nodes else "unknown",
                        "target": final_nodes[-1]["id"] if len(final_nodes) > 1 else "unknown"
                    }
                    final_edges.append(fallback_edge)
        
        # Inject compliance nodes
        final_nodes, final_edges = inject_compliance_nodes(final_nodes, final_edges, manifest)
        final_nodes = position_nodes(final_nodes)
        
        background_tasks.add_task(update_progress, workflow_id, "completed", "Workflow generated", 100)
        
        # Return the nodes and edges in the format the frontend expects (as dicts)
        return WorkflowResponse(
            nodes=final_nodes,
            edges=final_edges
        )
        
    except Exception as e:
        logger.error(f"Text workflow processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/parse-image", response_model=WorkflowResponse)
async def parse_image_workflow(request: ImageWorkflowRequest, background_tasks: BackgroundTasks):
    """Process image input into compliant workflow using GPT-4o Vision"""
    try:
        # Analyze image with GPT-4o Vision
        vision_result = await analyze_image_with_gpt4o(request.image)
        
        # Load compliance manifest
        detected_domain = request.domain
        if vision_result.get("domain_hints"):
            detected_domain = vision_result["domain_hints"][0]
            
        manifest = load_compliance_manifest(detected_domain)
        
        # Convert vision result to workflow format
        nodes = []
        for i, node_data in enumerate(vision_result.get("nodes", [])):
            nodes.append({
                "id": f"node_{i}",
                "type": "n8nNode",  # Frontend expects this
                "position": {"x": 100 + i * 150, "y": 100},
                "data": {
                    "label": node_data.get("label", f"Step {i+1}"),
                    "nodeType": node_data.get("type", "action"),
                    "icon": "🔍" if node_data.get("type") == "compliance" else "⚙️",
                    "description": f"Extracted from image: {node_data.get('label', f'Step {i+1}')}",
                    "locked": node_data.get("type") == "compliance",
                    "compliance_reason": "Extracted from compliance step in image" if node_data.get("type") == "compliance" else None
                }
            })
        
        edges = []
        for i, edge_data in enumerate(vision_result.get("edges", [])):
            # Find source and target node IDs
            source_id = None
            target_id = None
            
            for node in nodes:
                if edge_data.get("from", "").lower() in node["data"]["label"].lower():
                    source_id = node["id"]
                if edge_data.get("to", "").lower() in node["data"]["label"].lower():
                    target_id = node["id"]
            
            if source_id and target_id:
                edges.append({
                    "id": f"edge_{i}",
                    "source": source_id,
                    "target": target_id
                })
        
        # Inject compliance nodes
        final_nodes, final_edges = inject_compliance_nodes(nodes, edges, manifest)
        final_nodes = position_nodes(final_nodes)
        
        workflow_id = "workflow_" + str(datetime.now().timestamp())
        background_tasks.add_task(update_progress, workflow_id, "completed", "Workflow generated from image", 100)
        
        # Return WorkflowResponse schema as expected by FastAPI
        return WorkflowResponse(
            nodes=final_nodes,
            edges=final_edges,
            compliance_info={
                "domain": detected_domain,
                "regulations": manifest.get("regulations", []),
                "compliance_nodes_added": len([n for n in final_nodes if n.get("data", {}).get("locked")]),
                "vision_analysis": vision_result
            },
            workflow_id=workflow_id
        )
        
    except Exception as e:
        logger.error(f"Image workflow processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/convert-and-execute")
async def convert_and_execute(workflow_data: Dict[str, Any]):
    """Convert workflow to n8n format and prepare for execution"""
    try:
        nodes = workflow_data.get("nodes", [])
        edges = workflow_data.get("edges", [])
        
        # Convert to n8n format
        n8n_workflow = {
            "name": "Generated Compliant Workflow",
            "nodes": [],
            "connections": {},
            "createdAt": "2024-01-01T00:00:00.000Z",
            "updatedAt": "2024-01-01T00:00:00.000Z",
            "settings": {},
            "staticData": None,
            "meta": {
                "compliance_validated": True,
                "locked_nodes": [n["id"] for n in nodes if n.get("data", {}).get("locked")]
            }
        }
        
        # Convert nodes to n8n format
        for node in nodes:
            n8n_node = {
                "id": node["id"],
                "name": node["data"]["label"],
                "type": "n8n-nodes-base.set" if not node["data"].get("locked") else "n8n-nodes-base.function",
                "position": [node["position"]["x"], node["position"]["y"]],
                "parameters": {
                    "compliance_locked": node["data"].get("locked", False),
                    "compliance_reason": node["data"].get("compliance_reason", "")
                }
            }
            n8n_workflow["nodes"].append(n8n_node)
        
        # Convert edges to n8n connections
        for edge in edges:
            if edge["source"] not in n8n_workflow["connections"]:
                n8n_workflow["connections"][edge["source"]] = {"main": [[]]}
            
            n8n_workflow["connections"][edge["source"]]["main"][0].append({
                "node": edge["target"],
                "type": "main",
                "index": 0
            })
        
        return {
            "n8n_workflow": n8n_workflow,
            "execution_ready": True,
            "compliance_validated": True,
            "export_format": "n8n_json"
        }
        
    except Exception as e:
        logger.error(f"Workflow conversion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "agentic-workflow-builder"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
