"""
SecureAI API - Vercel Compatible Version
Proper ASGI handler for Vercel serverless functions.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import json

# Initialize FastAPI app
app = FastAPI(
    title="SecureAI API",
    version="1.0.0",
    description="Lightweight workflow builder API"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Pydantic models
class TextInput(BaseModel):
    text: str

# Basic domain detection function
def detect_domain(text: str) -> str:
    """Simple domain detection based on keywords."""
    if not text:
        return 'general'
    
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['patient', 'medical', 'health', 'hipaa', 'clinical']):
        return 'healthcare'
    elif any(word in text_lower for word in ['invoice', 'payment', 'financial', 'transaction', 'fraud']):
        return 'finance'
    elif any(word in text_lower for word in ['employee', 'hiring', 'hr', 'personnel', 'onboard']):
        return 'hr'
    elif any(word in text_lower for word in ['customer', 'lead', 'sales', 'marketing', 'campaign']):
        return 'sales'
    elif any(word in text_lower for word in ['security', 'access', 'it', 'system', 'vpn']):
        return 'it'
    else:
        return 'general'

# Workflow templates
WORKFLOW_TEMPLATES = {
    'healthcare': [
        {'label': 'Receive Patient Data', 'type': 'trigger', 'icon': '🏥'},
        {'label': 'HIPAA Compliance Check', 'type': 'compliance', 'icon': '🛡️'},
        {'label': 'Process Medical Records', 'type': 'action', 'icon': '⚙️'},
        {'label': 'Audit Log Entry', 'type': 'compliance', 'icon': '📝'}
    ],
    'finance': [
        {'label': 'Receive Financial Data', 'type': 'trigger', 'icon': '💰'},
        {'label': 'Fraud Detection', 'type': 'compliance', 'icon': '🛡️'},
        {'label': 'Process Transaction', 'type': 'action', 'icon': '⚙️'},
        {'label': 'Audit Trail', 'type': 'compliance', 'icon': '📝'}
    ],
    'hr': [
        {'label': 'Receive Employee Data', 'type': 'trigger', 'icon': '👤'},
        {'label': 'Background Check', 'type': 'compliance', 'icon': '🛡️'},
        {'label': 'Process Application', 'type': 'action', 'icon': '⚙️'},
        {'label': 'HR Audit Log', 'type': 'compliance', 'icon': '📝'}
    ],
    'sales': [
        {'label': 'Receive Lead Data', 'type': 'trigger', 'icon': '🎯'},
        {'label': 'GDPR Consent Check', 'type': 'compliance', 'icon': '🛡️'},
        {'label': 'Process Lead', 'type': 'action', 'icon': '⚙️'},
        {'label': 'CRM Update', 'type': 'action', 'icon': '📊'}
    ],
    'it': [
        {'label': 'Receive IT Request', 'type': 'trigger', 'icon': '💻'},
        {'label': 'Security Scan', 'type': 'compliance', 'icon': '🛡️'},
        {'label': 'Process Request', 'type': 'action', 'icon': '⚙️'},
        {'label': 'Access Log', 'type': 'compliance', 'icon': '📝'}
    ],
    'general': [
        {'label': 'Process Input', 'type': 'trigger', 'icon': '📥'},
        {'label': 'Validate Data', 'type': 'action', 'icon': '✅'},
        {'label': 'Generate Output', 'type': 'action', 'icon': '📤'}
    ]
}

def generate_workflow(text: str) -> Dict[str, Any]:
    """Generate a workflow structure."""
    try:
        domain = detect_domain(text)
        steps = WORKFLOW_TEMPLATES.get(domain, WORKFLOW_TEMPLATES['general'])
        
        # Generate nodes
        nodes = []
        edges = []
        
        for i, step in enumerate(steps):
            node = {
                'id': f'node_{i}',
                'type': 'n8nNode',
                'position': {'x': 150 + (i * 250), 'y': 150},
                'data': {
                    'label': step['label'],
                    'nodeType': step['type'],
                    'icon': step.get('icon', '⚙️'),
                    'locked': step['type'] == 'compliance',
                    'description': f"{step['type'].title()} step",
                    'compliance_reason': "Required for compliance" if step['type'] == 'compliance' else None
                }
            }
            nodes.append(node)
            
            # Create edges between consecutive nodes
            if i > 0:
                edge = {
                    'id': f'edge_{i-1}_{i}',
                    'source': f'node_{i-1}',
                    'target': f'node_{i}'
                }
                edges.append(edge)
        
        return {
            'nodes': nodes,
            'edges': edges,
            'compliance_info': {
                'domain': domain,
                'compliance_nodes_added': len([s for s in steps if s['type'] == 'compliance']),
                'rules_applied': get_compliance_rules(domain)
            },
            'workflow_id': f'wf_{abs(hash(text)) % 100000}'
        }
    except Exception as e:
        # Return a simple fallback workflow
        return {
            'nodes': [{
                'id': 'node_0',
                'type': 'n8nNode',
                'position': {'x': 150, 'y': 150},
                'data': {
                    'label': 'Simple Workflow Step',
                    'nodeType': 'action',
                    'icon': '⚙️',
                    'locked': False
                }
            }],
            'edges': [],
            'compliance_info': {
                'domain': 'general',
                'compliance_nodes_added': 0,
                'rules_applied': []
            },
            'workflow_id': 'wf_fallback'
        }

def get_compliance_rules(domain: str) -> List[str]:
    """Get compliance rules for a domain."""
    rules_map = {
        'healthcare': ['HIPAA', 'HITECH'],
        'finance': ['PCI-DSS', 'SOX'],
        'hr': ['GDPR', 'CCPA', 'EEOC'],
        'sales': ['GDPR', 'CCPA', 'CAN-SPAM'],
        'it': ['ISO 27001', 'SOC 2', 'NIST']
    }
    return rules_map.get(domain, [])

# Routes
@app.get("/")
async def root():
    return {
        "message": "SecureAI Lightweight API",
        "status": "online",
        "version": "1.0.0",
        "endpoints": ["/health", "/api/interpret", "/api/test-edges"]
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "SecureAI Lightweight",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.post("/api/interpret")
async def interpret_text(input_data: TextInput):
    """Process text input and generate workflow."""
    try:
        workflow = generate_workflow(input_data.text)
        return workflow
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/api/parse-image")
async def parse_image():
    """Mock image processing endpoint."""
    try:
        sample_workflow = generate_workflow("process image workflow")
        return sample_workflow
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")

@app.get("/api/test-edges")
async def test_edges():
    """Test endpoint for edge generation."""
    return {
        "nodes": [
            {
                "id": "1",
                "type": "n8nNode",
                "position": {"x": 100, "y": 100},
                "data": {"label": "Test Node 1", "nodeType": "trigger", "icon": "🎯"}
            },
            {
                "id": "2", 
                "type": "n8nNode",
                "position": {"x": 300, "y": 100},
                "data": {"label": "Test Node 2", "nodeType": "action", "icon": "⚙️"}
            }
        ],
        "edges": [
            {"id": "e1-2", "source": "1", "target": "2"}
        ],
        "workflow_id": "test_workflow",
        "compliance_info": {
            "domain": "test",
            "compliance_nodes_added": 0
        }
    }

@app.get("/api/progress/{workflow_id}")
async def get_progress(workflow_id: str):
    """Mock progress endpoint."""
    return {
        "workflow_id": workflow_id,
        "status": "completed",
        "progress": 100,
        "stage": "finished"
    }

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)