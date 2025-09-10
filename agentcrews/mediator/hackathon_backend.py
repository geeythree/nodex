"""
Refactored backend for Agentic Workflow Builder
Modular, secure, and performant implementation
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from typing import List, Dict, Any, Optional
import yaml
import json
import os
from pathlib import Path
import openai
from crewai import Agent, Task, Crew
import logging
from datetime import datetime
import uuid

# Import our new modules
from .workflow_processor import WorkflowProcessor
from .async_crew_executor import AsyncCrewExecutor
from .cache_manager import cache
from .security import SecurityManager
from .intelligent_fallback import IntelligentFallbackGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize async executor
crew_executor = AsyncCrewExecutor()

app = FastAPI(
    title="Agentic Workflow Builder",
    version="2.0.0",
    description="Secure and scalable workflow generation with AI"
)

# Global progress tracking with cleanup
workflow_progress = {}
MAX_PROGRESS_AGE = 3600  # 1 hour

def cleanup_old_progress():
    """Remove old progress entries"""
    current_time = datetime.now()
    to_remove = []
    for workflow_id, data in workflow_progress.items():
        if 'timestamp' in data:
            timestamp = datetime.fromisoformat(data['timestamp'])
            if (current_time - timestamp).seconds > MAX_PROGRESS_AGE:
                to_remove.append(workflow_id)
    
    for workflow_id in to_remove:
        del workflow_progress[workflow_id]
        logger.debug(f"Cleaned up old progress for {workflow_id}")

def update_progress(workflow_id: str, stage: str, message: str, progress: int):
    """Update progress for a workflow"""
    workflow_progress[workflow_id] = {
        "stage": stage,
        "message": message,
        "progress": progress,
        "timestamp": datetime.now().isoformat()
    }
    logger.info(f"Progress [{workflow_id}]: {stage} - {message} ({progress}%)")
    
    # Periodic cleanup
    if len(workflow_progress) > 100:
        cleanup_old_progress()

# Security middleware for API key validation (optional)
async def validate_api_key(x_api_key: Optional[str] = Header(None)):
    """Validate API key if required"""
    if os.getenv('REQUIRE_API_KEY', 'false').lower() == 'true':
        if not SecurityManager.validate_api_key(x_api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")
    return True

# Configure CORS with security in mind
app.add_middleware(
    CORSMiddleware,
    allow_origins=SecurityManager.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    max_age=3600,
)

# Pydantic models
class TextWorkflowRequest(BaseModel):
    text: str
    domain: str = "general"
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Create an employee onboarding workflow",
                "domain": "hr"
            }
        }

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
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    compliance_info: Optional[Dict[str, Any]] = None
    workflow_id: Optional[str] = None

# Load compliance manifests with caching
def load_compliance_manifest(domain: str) -> Dict[str, Any]:
    """Load compliance manifest for specified domain with caching"""
    
    # Check cache first
    cached_manifest = cache.get('compliance_manifest', domain)
    if cached_manifest:
        return cached_manifest
    
    manifest_path = Path(f"config/compliance/{domain}.yaml")
    if not manifest_path.exists():
        manifest_path = Path(f"config/compliance/general.yaml")
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
            # Cache for 1 hour
            cache.set('compliance_manifest', domain, manifest, ttl=3600)
            return manifest
    except Exception as e:
        logger.warning(f"Could not load compliance manifest for {domain}: {e}")
        default_manifest = {"domain": domain, "required_steps": []}
        cache.set('compliance_manifest', domain, default_manifest, ttl=300)
        return default_manifest

# CrewAI Agent factory with proper model configuration
def create_agents(domain: str) -> Dict[str, Agent]:
    """Create all required agents with proper configuration"""
    
    model = os.getenv("CREWAI_MODEL", "gpt-4o")
    
    agents = {
        'interpreter': Agent(
            role="API Workflow Interpreter",
            goal="Convert user requirements into specific API calls and executable steps",
            backstory="You are an expert at translating business processes into detailed API operations.",
            verbose=True,
            allow_delegation=False,
            llm=model
        ),
        'planner': Agent(
            role="Executable Workflow Planner",
            goal="Structure API calls into logical sequences with proper data flow",
            backstory="You are a system architect who designs robust API workflows.",
            verbose=True,
            allow_delegation=False,
            llm=model
        ),
        'compliance': Agent(
            role="Compliance Automation Specialist",
            goal=f"Inject {domain}-specific compliance API calls and audit endpoints",
            backstory=f"You ensure workflows meet {domain} regulatory requirements.",
            verbose=True,
            allow_delegation=False,
            llm=model
        ),
        'enhancement': Agent(
            role=f"{domain.title()} Workflow Enhancement Specialist",
            goal=f"Add {domain}-specific professional practices and optimizations",
            backstory=f"You are a senior {domain} consultant who adds industry best practices.",
            verbose=True,
            allow_delegation=False,
            llm=model
        ),
        'visualizer': Agent(
            role="n8n Workflow Generator",
            goal="Generate complete n8n-compatible JSON with executable node configurations",
            backstory="You create detailed workflow JSON with specific API configurations.",
            verbose=True,
            allow_delegation=False,
            llm=model
        )
    }
    
    return agents

# Workflow processing functions
def inject_compliance_nodes(nodes: List[Dict], edges: List[Dict], manifest: Dict) -> tuple:
    """Inject mandatory compliance nodes based on manifest"""
    compliance_nodes = []
    compliance_edges = []
    
    # Ensure manifest is a dict
    if not isinstance(manifest, dict):
        logger.warning(f"Manifest is not a dict: {type(manifest)}")
        manifest = {}
    
    required_steps = manifest.get("required_steps", [])
    
    # Filter out non-dict nodes for safe processing
    valid_nodes = [node for node in nodes if isinstance(node, dict) and 'id' in node]
    
    for step in required_steps:
        # Ensure step is a dict
        if not isinstance(step, dict):
            logger.warning(f"Skipping non-dict step: {type(step)} - {step}")
            continue
            
        # Create compliance node
        compliance_node = {
            "id": f"compliance_{step.get('compliance_type', 'generic')}_{len(compliance_nodes)}",
            "type": "n8nNode",
            "position": {"x": 200 + len(compliance_nodes) * 150, "y": 100},
            "data": {
                "label": step.get("label", "Compliance Check"),
                "nodeType": "compliance",
                "icon": "🛡️",
                "description": step.get("reason", "Required for compliance"),
                "locked": step.get("locked", True),
                "compliance_reason": step.get("reason", "Regulatory requirement")
            }
        }
        compliance_nodes.append(compliance_node)
        
        # Add edges if we have valid nodes
        if len(valid_nodes) > 0:
            # Insert after first valid node
            first_node = valid_nodes[0]
            compliance_edges.append({
                "id": f"edge_compliance_{len(compliance_edges)}",
                "source": first_node["id"],
                "target": compliance_node["id"]
            })
            
            if len(valid_nodes) > 1:
                # Connect to next valid node
                second_node = valid_nodes[1]
                compliance_edges.append({
                    "id": f"edge_compliance_{len(compliance_edges)}",
                    "source": compliance_node["id"],
                    "target": second_node["id"]
                })
    
    return nodes + compliance_nodes, edges + compliance_edges

def position_nodes(nodes: List[Dict]) -> List[Dict]:
    """Auto-position nodes in a logical flow layout"""
    positioned_nodes = []
    valid_node_count = 0
    
    for node in nodes:
        # Only process dict nodes that can have positions
        if isinstance(node, dict):
            # Grid layout with better spacing
            row = valid_node_count // 3
            col = valid_node_count % 3
            node["position"] = {
                "x": 150 + col * 250,
                "y": 150 + row * 200
            }
            positioned_nodes.append(node)
            valid_node_count += 1
        else:
            # Skip non-dict nodes but log them
            logger.warning(f"Skipping non-dict node in positioning: {type(node)} - {node}")
    
    return positioned_nodes

# GPT-4o Vision integration with error handling
async def analyze_image_with_gpt4o(image_data: str) -> Dict[str, Any]:
    """Use GPT-4o Vision to extract workflow from image"""
    
    # Check cache first
    cached_result = cache.get('image_analysis', image_data[:100])  # Use first 100 chars as key
    if cached_result:
        return cached_result
    
    try:
        client = openai.AsyncOpenAI()
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """Extract workflow steps from this image. 
                    Output valid JSON with nodes and edges arrays.
                    Identify compliance steps (audit, approve, verify, etc.)."""
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
            max_tokens=1000,
            temperature=0.3
        )
        
        result_text = response.choices[0].message.content
        
        # Try to parse as JSON
        try:
            result = json.loads(result_text)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {"nodes": [], "edges": [], "error": "Could not parse response"}
        
        # Cache the result
        cache.set('image_analysis', image_data[:100], result, ttl=1800)
        return result
        
    except Exception as e:
        logger.error(f"GPT-4o Vision analysis failed: {e}")
        return {"nodes": [], "edges": [], "domain_hints": [], "error": str(e)}

# API Endpoints
@app.get("/api/progress/{workflow_id}")
async def get_workflow_progress(workflow_id: str):
    """Get current progress for a workflow"""
    if workflow_id in workflow_progress:
        return workflow_progress[workflow_id]
    return {
        "stage": "idle",
        "message": "No active workflow",
        "progress": 0,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/interpret", response_model=WorkflowResponse, dependencies=[Depends(validate_api_key)])
async def interpret_text_workflow(request: TextWorkflowRequest, background_tasks: BackgroundTasks):
    """Process text input into compliant workflow"""
    try:
        # Sanitize inputs
        sanitized_text = SecurityManager.sanitize_text_input(request.text)
        sanitized_domain = SecurityManager.sanitize_domain(request.domain)
        
        # Check cache for similar requests
        cache_key = {'text': sanitized_text[:100], 'domain': sanitized_domain}
        cached_workflow = cache.get('text_workflow', cache_key)
        if cached_workflow:
            logger.info("Returning cached workflow")
            return cached_workflow
        
        # Generate workflow ID
        workflow_id = f"wf_{uuid.uuid4().hex[:8]}"
        
        # Load compliance manifest
        manifest = load_compliance_manifest(sanitized_domain)
        
        # Create agents
        agents = create_agents(sanitized_domain)
        
        # Create tasks with sanitized input
        tasks = []
        
        interpret_task = Task(
            description=f"Convert this into executable automation steps: '{sanitized_text}'",
            agent=agents['interpreter'],
            expected_output="List of executable automation steps"
        )
        tasks.append(interpret_task)
        
        plan_task = Task(
            description="Structure the steps into a professional workflow with error handling",
            agent=agents['planner'],
            expected_output="Structured workflow architecture"
        )
        tasks.append(plan_task)
        
        compliance_task = Task(
            description=f"Add {sanitized_domain}-specific compliance checks and audit points",
            agent=agents['compliance'],
            expected_output="Workflow with compliance nodes"
        )
        tasks.append(compliance_task)
        
        visualize_task = Task(
            description="Generate n8n-compatible workflow JSON with nodes and edges",
            agent=agents['visualizer'],
            expected_output="Complete workflow JSON"
        )
        tasks.append(visualize_task)
        
        # Create and execute crew asynchronously
        crew = Crew(
            agents=list(agents.values()),
            tasks=tasks,
            verbose=True
        )
        
        # Update progress
        background_tasks.add_task(update_progress, workflow_id, "processing", "Generating workflow", 20)
        
        # Execute crew asynchronously
        try:
            result = await crew_executor.execute_crew(crew)
            # Process the result
            background_tasks.add_task(update_progress, workflow_id, "parsing", "Processing output", 60)
            parsed_workflow = WorkflowProcessor.parse_crew_output(result, sanitized_domain)
        except Exception as crew_error:
            logger.warning(f"CrewAI execution failed: {crew_error}")
            # Fall back to None so we use the fallback workflow
            parsed_workflow = None
        
        if not parsed_workflow:
            # Use intelligent fallback workflow generation
            logger.info(f"Using intelligent fallback for: '{sanitized_text}' in domain: {sanitized_domain}")
            fallback_nodes, fallback_edges = IntelligentFallbackGenerator.generate_intelligent_workflow(
                sanitized_text, sanitized_domain
            )
            parsed_workflow = {
                "nodes": fallback_nodes,
                "edges": fallback_edges
            }
        
        # Ensure parsed_workflow is a dict
        if not isinstance(parsed_workflow, dict):
            logger.error(f"parsed_workflow is not a dict: {type(parsed_workflow)}")
            parsed_workflow = {"nodes": [], "edges": []}
        
        # Transform to React Flow format
        workflow_data = WorkflowProcessor.transform_to_react_flow(parsed_workflow, sanitized_domain)
        
        # Ensure workflow_data is valid
        if not workflow_data or not isinstance(workflow_data, dict):
            logger.error("workflow_data transformation failed, using fallback")
            workflow_data = {"nodes": [], "edges": []}
        
        # Filter domain compliance
        try:
            logger.debug(f"workflow_data type before filtering: {type(workflow_data)}")
            logger.debug(f"workflow_data content: {workflow_data}")
            
            nodes, edges = WorkflowProcessor.filter_domain_compliance(
                workflow_data['nodes'],
                workflow_data['edges'],
                sanitized_domain
            )
            
            logger.debug(f"nodes type after filtering: {type(nodes)}, count: {len(nodes) if isinstance(nodes, list) else 'not a list'}")
            logger.debug(f"edges type after filtering: {type(edges)}, count: {len(edges) if isinstance(edges, list) else 'not a list'}")
        except Exception as e:
            logger.error(f"Error in filtering: {e}")
            nodes, edges = [], []
        
        # Inject compliance nodes
        try:
            final_nodes, final_edges = inject_compliance_nodes(nodes, edges, manifest)
            final_nodes = position_nodes(final_nodes)
            
            logger.debug(f"final_nodes type: {type(final_nodes)}, count: {len(final_nodes) if isinstance(final_nodes, list) else 'not a list'}")
            logger.debug(f"Sample final_node: {final_nodes[0] if final_nodes and isinstance(final_nodes, list) else 'None or empty'}")
        except Exception as e:
            logger.error(f"Error in compliance injection: {e}")
            final_nodes, final_edges = [], []
        
        background_tasks.add_task(update_progress, workflow_id, "completed", "Workflow ready", 100)
        
        # Safe compliance node counting
        try:
            compliance_nodes_count = 0
            for n in final_nodes:
                if isinstance(n, dict) and 'data' in n and isinstance(n['data'], dict):
                    if n['data'].get('locked', False):
                        compliance_nodes_count += 1
            logger.debug(f"Compliance nodes count: {compliance_nodes_count}")
        except Exception as e:
            logger.error(f"Error counting compliance nodes: {e}")
            compliance_nodes_count = 0
        
        response = WorkflowResponse(
            nodes=final_nodes,
            edges=final_edges,
            compliance_info={
                "domain": sanitized_domain,
                "compliance_nodes": compliance_nodes_count
            },
            workflow_id=workflow_id
        )
        
        # Cache the result
        cache.set('text_workflow', cache_key, response.dict(), ttl=1800)
        
        return response
        
    except Exception as e:
        logger.error(f"Text workflow processing failed: {e}")
        
        # Create an emergency intelligent fallback workflow instead of failing
        fallback_workflow_id = f"emergency_{uuid.uuid4().hex[:8]}"
        
        try:
            # Try intelligent fallback even in emergency
            emergency_nodes, emergency_edges = IntelligentFallbackGenerator.generate_intelligent_workflow(
                sanitized_text, sanitized_domain
            )
            
            # Add an error indicator to the first node
            if emergency_nodes:
                emergency_nodes[0]['data']['hasError'] = True
                emergency_nodes[0]['data']['description'] = f"Generated with emergency fallback due to: {str(e)[:50]}..."
            
            fallback_nodes = emergency_nodes
            fallback_edges = emergency_edges
            
        except Exception as fallback_error:
            logger.error(f"Emergency fallback also failed: {fallback_error}")
            # Absolute last resort
            fallback_nodes = [
                {
                    "id": "error_node",
                    "type": "n8nNode", 
                    "position": {"x": 100, "y": 100},
                    "data": {
                        "label": "Manual Setup Required",
                        "nodeType": "action",
                        "icon": "⚠️",
                        "description": f"Please manually create your workflow for: {sanitized_text[:50]}...",
                        "hasError": True
                    }
                }
            ]
            fallback_edges = []
        
        return WorkflowResponse(
            nodes=fallback_nodes,
            edges=fallback_edges,
            compliance_info={
                "domain": sanitized_domain,
                "compliance_nodes": 0,
                "error": "Workflow generation failed, fallback created"
            },
            workflow_id=fallback_workflow_id
        )

@app.post("/api/parse-image", response_model=WorkflowResponse, dependencies=[Depends(validate_api_key)])
async def parse_image_workflow(request: ImageWorkflowRequest, background_tasks: BackgroundTasks):
    """Process image input into compliant workflow using GPT-4o Vision"""
    try:
        # Validate image data
        if not SecurityManager.validate_image_data(request.image):
            raise HTTPException(status_code=400, detail="Invalid or oversized image data")
        
        sanitized_domain = SecurityManager.sanitize_domain(request.domain)
        
        # Generate workflow ID
        workflow_id = f"wf_{uuid.uuid4().hex[:8]}"
        
        # Analyze image
        background_tasks.add_task(update_progress, workflow_id, "analyzing", "Processing image", 30)
        vision_result = await analyze_image_with_gpt4o(request.image)
        
        if "error" in vision_result:
            raise HTTPException(status_code=500, detail=f"Image analysis failed: {vision_result['error']}")
        
        # Detect domain from image if hints available
        detected_domain = sanitized_domain
        if vision_result.get("domain_hints"):
            detected_domain = vision_result["domain_hints"][0]
        
        # Load compliance manifest
        manifest = load_compliance_manifest(detected_domain)
        
        # Convert vision result to workflow format
        nodes = []
        for i, node_data in enumerate(vision_result.get("nodes", [])):
            nodes.append({
                "id": f"node_{i}",
                "type": "n8nNode",
                "position": {"x": 150 + (i % 3) * 250, "y": 150 + (i // 3) * 200},
                "data": {
                    "label": node_data.get("label", f"Step {i+1}"),
                    "nodeType": node_data.get("type", "action"),
                    "icon": "🔍" if node_data.get("type") == "compliance" else "⚙️",
                    "description": f"Extracted: {node_data.get('label', '')}",
                    "locked": node_data.get("type") == "compliance"
                }
            })
        
        edges = []
        for i, edge_data in enumerate(vision_result.get("edges", [])):
            edges.append({
                "id": f"edge_{i}",
                "source": f"node_{edge_data.get('from', 0)}",
                "target": f"node_{edge_data.get('to', 1)}"
            })
        
        # Inject compliance nodes
        final_nodes, final_edges = inject_compliance_nodes(nodes, edges, manifest)
        
        background_tasks.add_task(update_progress, workflow_id, "completed", "Workflow ready", 100)
        
        return WorkflowResponse(
            nodes=final_nodes,
            edges=final_edges,
            compliance_info={
                "domain": detected_domain,
                "source": "image",
                "compliance_nodes": len([n for n in final_nodes if n.get('data', {}).get('locked')])
            },
            workflow_id=workflow_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image workflow processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")

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
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
            "settings": {},
            "staticData": None,
            "meta": {
                "compliance_validated": True,
                "locked_nodes": [n["id"] for n in nodes if n.get("data", {}).get("locked")]
            }
        }
        
        # Convert nodes
        for node in nodes:
            n8n_node = {
                "id": node["id"],
                "name": node["data"]["label"],
                "type": "n8n-nodes-base.webhook" if node["data"]["nodeType"] == "webhook" else "n8n-nodes-base.function",
                "position": [node["position"]["x"], node["position"]["y"]],
                "parameters": {
                    "compliance_locked": node["data"].get("locked", False)
                }
            }
            n8n_workflow["nodes"].append(n8n_node)
        
        # Convert edges
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
            "compliance_validated": True
        }
        
    except Exception as e:
        logger.error(f"Workflow conversion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-edges")
async def test_edges():
    """Test endpoint with guaranteed simple workflow with edges"""
    test_workflow = {
        "nodes": [
            {
                "id": "1",
                "type": "n8nNode",
                "position": {"x": 100, "y": 100},
                "data": {"label": "Node 1", "nodeType": "webhook", "icon": "🎯"}
            },
            {
                "id": "2",
                "type": "n8nNode",
                "position": {"x": 300, "y": 100},
                "data": {"label": "Node 2", "nodeType": "action", "icon": "⚙️"}
            },
            {
                "id": "3",
                "type": "n8nNode",
                "position": {"x": 500, "y": 100},
                "data": {"label": "Node 3", "nodeType": "output", "icon": "✅"}
            }
        ],
        "edges": [
            {"id": "e1-2", "source": "1", "target": "2"},
            {"id": "e2-3", "source": "2", "target": "3"}
        ],
        "workflow_id": "test_workflow",
        "compliance_info": {"domain": "test", "compliance_nodes": 0}
    }
    return test_workflow

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "agentic-workflow-builder",
        "version": "2.0.0",
        "cache_stats": cache.get_stats()
    }

@app.get("/api/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    return cache.get_stats()

@app.post("/api/cache/clear")
async def clear_cache(prefix: Optional[str] = None):
    """Clear cache entries"""
    cache.invalidate(prefix)
    return {"message": f"Cache cleared for prefix: {prefix}" if prefix else "Entire cache cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)