"""
Ultra-lightweight SecureAI API for Vercel deployment.
This version stays under 250MB by excluding heavy AI dependencies.
"""

import os
import json
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import base64

# Initialize FastAPI app
app = FastAPI(
    title="SecureAI API - Lightweight",
    version="1.0.0",
    description="Lightweight workflow builder API"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class TextInput(BaseModel):
    text: str

class WorkflowResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    compliance_info: Dict[str, Any]
    workflow_id: str

# Basic domain detection
def detect_domain(text: str) -> str:
    """Simple domain detection based on keywords."""
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

# Generate basic workflow
def generate_basic_workflow(text: str) -> Dict[str, Any]:
    """Generate a basic workflow structure without AI."""
    domain = detect_domain(text)
    
    # Basic workflow templates
    workflows = {
        'healthcare': [
            {'label': 'Receive Patient Data', 'type': 'trigger'},
            {'label': 'HIPAA Compliance Check', 'type': 'compliance'},
            {'label': 'Process Medical Records', 'type': 'action'},
            {'label': 'Audit Log Entry', 'type': 'compliance'}
        ],
        'finance': [
            {'label': 'Receive Financial Data', 'type': 'trigger'},
            {'label': 'Fraud Detection', 'type': 'compliance'},
            {'label': 'Process Transaction', 'type': 'action'},
            {'label': 'Audit Trail', 'type': 'compliance'}
        ],
        'hr': [
            {'label': 'Receive Employee Data', 'type': 'trigger'},
            {'label': 'Background Check', 'type': 'compliance'},
            {'label': 'Process Application', 'type': 'action'},
            {'label': 'HR Audit Log', 'type': 'compliance'}
        ],
        'general': [
            {'label': 'Process Input', 'type': 'trigger'},
            {'label': 'Validate Data', 'type': 'action'},
            {'label': 'Generate Output', 'type': 'action'}
        ]
    }
    
    steps = workflows.get(domain, workflows['general'])
    
    # Generate nodes
    nodes = []
    edges = []
    
    for i, step in enumerate(steps):
        node = {
            'id': f'node_{i}',
            'type': 'n8nNode',
            'position': {'x': 150 + (i * 200), 'y': 150},
            'data': {
                'label': step['label'],
                'nodeType': step['type'],
                'icon': '⚙️' if step['type'] == 'action' else '🛡️',
                'locked': step['type'] == 'compliance'
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
            'compliance_nodes_added': len([s for s in steps if s['type'] == 'compliance'])
        },
        'workflow_id': f'wf_{hash(text) % 100000}'
    }

@app.get("/")
async def root():
    return {
        "message": "SecureAI Lightweight API",
        "status": "online",
        "version": "1.0.0",
        "note": "This is a lightweight version optimized for Vercel deployment"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "SecureAI Lightweight"}

@app.post("/api/interpret")
async def interpret_text(input_data: TextInput):
    """Process text input and generate workflow."""
    try:
        workflow = generate_basic_workflow(input_data.text)
        return workflow
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/api/parse-image")
async def parse_image(image: UploadFile = File(...)):
    """Basic image processing - returns sample workflow."""
    try:
        # For now, return a basic workflow since we can't include OpenAI Vision
        sample_workflow = generate_basic_workflow("process image workflow")
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
                "data": {"label": "Test Node 1", "nodeType": "trigger"}
            },
            {
                "id": "2", 
                "type": "n8nNode",
                "position": {"x": 300, "y": 100},
                "data": {"label": "Test Node 2", "nodeType": "action"}
            }
        ],
        "edges": [
            {"id": "e1-2", "source": "1", "target": "2"}
        ]
    }

@app.get("/api/progress/{workflow_id}")
async def get_progress(workflow_id: str):
    """Mock progress endpoint."""
    return {
        "workflow_id": workflow_id,
        "status": "completed",
        "progress": 100
    }

# Vercel handler
def handler(request):
    return app(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)