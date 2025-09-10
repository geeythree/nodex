import { Node, Edge } from 'reactflow';
import { N8nNodeData } from '../components/N8nNode';

interface GeneratedAPI {
  nodeId: string;
  nodeName: string;
  endpoint: string;
  method: string;
  code: string;
  language: string;
}

interface APIGenerationResult {
  apis: GeneratedAPI[];
  orchestrator: string;
  dockerfile: string;
  deployment: string;
  totalLines: number;
  executionTime: number;
}

const generateNodeAPI = (node: Node<N8nNodeData>): GeneratedAPI => {
  const { nodeType, label } = node.data;
  const nodeName = label.replace(/\s+/g, '');
  const endpoint = `/${nodeType}/${label.toLowerCase().replace(/\s+/g, '-')}`;

  let code = '';
  let method = 'POST';

  switch (nodeType) {
    case 'trigger':
      method = 'POST';
      code = `from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import uuid

app = FastAPI(title="${nodeName} Trigger Service")

class TriggerRequest(BaseModel):
    data: dict
    source: str = "webhook"
    
class TriggerResponse(BaseModel):
    trigger_id: str
    status: str
    timestamp: datetime
    next_nodes: list

@app.post("${endpoint}")
async def handle_${nodeName.toLowerCase()}_trigger(request: TriggerRequest):
    """
    ${label} - Webhook trigger endpoint
    Processes incoming requests and initiates workflow
    """
    try:
        trigger_id = str(uuid.uuid4())
        
        # Process trigger data
        processed_data = {
            "trigger_id": trigger_id,
            "original_data": request.data,
            "processed_at": datetime.now().isoformat(),
            "source": request.source
        }
        
        # Queue for next workflow step
        await queue_next_step(trigger_id, processed_data)
        
        return TriggerResponse(
            trigger_id=trigger_id,
            status="triggered",
            timestamp=datetime.now(),
            next_nodes=["action_node", "validation_node"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trigger failed: {str(e)}")

async def queue_next_step(trigger_id: str, data: dict):
    # Queue data for next workflow nodes
    print(f"Queuing {trigger_id} for next step with data: {data}")
    # In production: send to message queue (Redis, RabbitMQ, etc.)
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)`;
      break;

    case 'action':
      code = `from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import httpx
import json
from typing import Optional

app = FastAPI(title="${nodeName} Action Service")

class ActionRequest(BaseModel):
    trigger_id: str
    data: dict
    context: Optional[dict] = {}

class ActionResponse(BaseModel):
    action_id: str
    status: str
    result: dict
    execution_time: float

@app.post("${endpoint}")
async def execute_${nodeName.toLowerCase()}_action(
    request: ActionRequest, 
    background_tasks: BackgroundTasks
):
    """
    ${label} - Action processing endpoint
    Executes business logic and processes data
    """
    import time
    start_time = time.time()
    
    try:
        action_id = f"{request.trigger_id}-action-{int(time.time())}"
        
        # Execute action logic
        result = await process_action_logic(request.data, request.context)
        
        # Background task to notify next nodes
        background_tasks.add_task(
            notify_next_nodes, 
            action_id, 
            result
        )
        
        execution_time = time.time() - start_time
        
        return ActionResponse(
            action_id=action_id,
            status="completed",
            result=result,
            execution_time=execution_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Action execution failed: {str(e)}"
        )

async def process_action_logic(data: dict, context: dict) -> dict:
    """
    Core business logic for ${label}
    Customize this function based on your requirements
    """
    
    # Example: API call action
    if "${label.toLowerCase()}" in ["api call", "http request"]:
        async with httpx.AsyncClient() as client:
            # Make external API call
            response = await client.post(
                "https://api.example.com/process",
                json=data,
                headers={"Authorization": "Bearer YOUR_API_KEY"}
            )
            return {"api_response": response.json(), "status_code": response.status_code}
    
    # Example: Data transformation
    elif "${label.toLowerCase()}" in ["transform", "process"]:
        transformed_data = {
            "original": data,
            "processed": {k: str(v).upper() if isinstance(v, str) else v for k, v in data.items()},
            "metadata": {"processed_by": "${nodeName}", "timestamp": time.time()}
        }
        return transformed_data
    
    # Default processing
    return {
        "input_data": data,
        "processed_by": "${nodeName}",
        "context": context,
        "success": True
    }

async def notify_next_nodes(action_id: str, result: dict):
    """Send results to next workflow nodes"""
    print(f"Action {action_id} completed. Notifying next nodes with result: {result}")
    # In production: HTTP calls to next services or message queue
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)`;
      break;

    case 'condition':
      method = 'GET';
      code = `from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
import operator

app = FastAPI(title="${nodeName} Condition Service")

class ConditionRequest(BaseModel):
    trigger_id: str
    data: dict
    conditions: list = []

class ConditionResponse(BaseModel):
    condition_id: str
    result: bool
    matched_condition: str
    next_path: str
    details: dict

@app.post("${endpoint}/evaluate")
async def evaluate_${nodeName.toLowerCase()}_condition(request: ConditionRequest):
    """
    ${label} - Condition evaluation endpoint
    Evaluates conditions and determines workflow path
    """
    try:
        condition_id = f"{request.trigger_id}-condition-{int(time.time())}"
        
        # Default conditions if none provided
        if not request.conditions:
            request.conditions = [
                {"field": "status", "operator": "equals", "value": "success"},
                {"field": "amount", "operator": "greater_than", "value": 100},
                {"field": "type", "operator": "contains", "value": "premium"}
            ]
        
        result, matched_condition, details = await evaluate_conditions(
            request.data, 
            request.conditions
        )
        
        # Determine next workflow path
        next_path = "success_path" if result else "failure_path"
        
        return ConditionResponse(
            condition_id=condition_id,
            result=result,
            matched_condition=matched_condition,
            next_path=next_path,
            details=details
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Condition evaluation failed: {str(e)}"
        )

async def evaluate_conditions(data: dict, conditions: list) -> tuple:
    """
    Evaluate multiple conditions against data
    Returns: (overall_result, matched_condition, details)
    """
    operators_map = {
        "equals": operator.eq,
        "not_equals": operator.ne,
        "greater_than": operator.gt,
        "less_than": operator.lt,
        "contains": lambda x, y: y in str(x),
        "starts_with": lambda x, y: str(x).startswith(str(y))
    }
    
    results = []
    details = {"evaluated_conditions": []}
    
    for condition in conditions:
        field = condition.get("field")
        op = condition.get("operator", "equals")
        expected_value = condition.get("value")
        
        actual_value = data.get(field)
        
        if op in operators_map:
            condition_result = operators_map[op](actual_value, expected_value)
            results.append(condition_result)
            
            details["evaluated_conditions"].append({
                "field": field,
                "operator": op,
                "expected": expected_value,
                "actual": actual_value,
                "result": condition_result
            })
            
            if condition_result:
                matched_condition = f"{field} {op} {expected_value}"
                return True, matched_condition, details
    
    return len(results) > 0 and any(results), "no_match", details

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)`;
      break;

    case 'validation':
      code = `from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from typing import Any, Dict, List
import re
from datetime import datetime

app = FastAPI(title="${nodeName} Validation Service")

class ValidationRequest(BaseModel):
    trigger_id: str
    data: dict
    validation_rules: List[dict] = []

class ValidationResponse(BaseModel):
    validation_id: str
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    validated_data: dict

@app.post("${endpoint}")
async def validate_${nodeName.toLowerCase()}_data(request: ValidationRequest):
    """
    ${label} - Data validation endpoint
    Validates incoming data against defined rules
    """
    try:
        validation_id = f"{request.trigger_id}-validation-{int(time.time())}"
        
        # Default validation rules
        if not request.validation_rules:
            request.validation_rules = [
                {"field": "email", "type": "email", "required": True},
                {"field": "phone", "type": "phone", "required": False},
                {"field": "age", "type": "number", "min": 18, "max": 120},
                {"field": "name", "type": "string", "min_length": 2, "max_length": 50}
            ]
        
        errors, warnings, validated_data = await validate_data(
            request.data,
            request.validation_rules
        )
        
        is_valid = len(errors) == 0
        
        return ValidationResponse(
            validation_id=validation_id,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            validated_data=validated_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )

async def validate_data(data: dict, rules: List[dict]) -> tuple:
    """
    Validate data against rules
    Returns: (errors, warnings, validated_data)
    """
    errors = []
    warnings = []
    validated_data = data.copy()
    
    for rule in rules:
        field = rule.get("field")
        field_type = rule.get("type", "string")
        required = rule.get("required", False)
        
        value = data.get(field)
        
        # Check required fields
        if required and (value is None or value == ""):
            errors.append(f"Field '{field}' is required")
            continue
            
        # Skip validation for optional empty fields
        if value is None or value == "":
            continue
        
        # Type-specific validation
        if field_type == "email":
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, str(value)):
                errors.append(f"Field '{field}' must be a valid email")
                
        elif field_type == "phone":
            phone_pattern = r'^\+?1?\d{9,15}$'
            if not re.match(phone_pattern, re.sub(r'[^\d+]', '', str(value))):
                warnings.append(f"Field '{field}' may not be a valid phone number")
                
        elif field_type == "number":
            try:
                num_value = float(value)
                validated_data[field] = num_value
                
                if "min" in rule and num_value < rule["min"]:
                    errors.append(f"Field '{field}' must be >= {rule['min']}")
                if "max" in rule and num_value > rule["max"]:
                    errors.append(f"Field '{field}' must be <= {rule['max']}")
            except (ValueError, TypeError):
                errors.append(f"Field '{field}' must be a number")
                
        elif field_type == "string":
            str_value = str(value)
            if "min_length" in rule and len(str_value) < rule["min_length"]:
                errors.append(f"Field '{field}' must be at least {rule['min_length']} characters")
            if "max_length" in rule and len(str_value) > rule["max_length"]:
                errors.append(f"Field '{field}' must be at most {rule['max_length']} characters")
    
    return errors, warnings, validated_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)`;
      break;

    case 'notification':
      code = `from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import smtplib
import json
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any

app = FastAPI(title="${nodeName} Notification Service")

class NotificationRequest(BaseModel):
    trigger_id: str
    recipient: str
    subject: str
    message: str
    channel: str = "email"  # email, slack, webhook, sms
    template_data: Optional[Dict[str, Any]] = {}

class NotificationResponse(BaseModel):
    notification_id: str
    status: str
    channel: str
    recipient: str
    sent_at: str

@app.post("${endpoint}")
async def send_${nodeName.toLowerCase()}_notification(
    request: NotificationRequest,
    background_tasks: BackgroundTasks
):
    """
    ${label} - Notification sending endpoint
    Sends notifications via multiple channels
    """
    try:
        notification_id = f"{request.trigger_id}-notification-{int(time.time())}"
        
        # Add background task for actual sending
        background_tasks.add_task(
            send_notification,
            notification_id,
            request.channel,
            request.recipient,
            request.subject,
            request.message,
            request.template_data
        )
        
        return NotificationResponse(
            notification_id=notification_id,
            status="queued",
            channel=request.channel,
            recipient=request.recipient,
            sent_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Notification queuing failed: {str(e)}"
        )

async def send_notification(
    notification_id: str,
    channel: str,
    recipient: str,
    subject: str,
    message: str,
    template_data: dict
):
    """
    Actually send the notification
    """
    try:
        if channel == "email":
            await send_email(recipient, subject, message, template_data)
            
        elif channel == "slack":
            await send_slack_message(recipient, subject, message, template_data)
            
        elif channel == "webhook":
            await send_webhook(recipient, subject, message, template_data)
            
        elif channel == "sms":
            await send_sms(recipient, message, template_data)
            
        print(f"Notification {notification_id} sent successfully via {channel}")
        
    except Exception as e:
        print(f"Failed to send notification {notification_id}: {str(e)}")

async def send_email(recipient: str, subject: str, message: str, template_data: dict):
    """Send email notification"""
    # In production: use proper SMTP configuration
    print(f"📧 Sending email to {recipient}: {subject}")
    print(f"Message: {message}")
    # Simulate email sending delay
    import asyncio
    await asyncio.sleep(1)

async def send_slack_message(channel: str, subject: str, message: str, template_data: dict):
    """Send Slack notification"""
    slack_payload = {
        "channel": channel,
        "text": f"*{subject}*\n{message}",
        "username": "${nodeName} Bot"
    }
    print(f"💬 Sending Slack message to {channel}: {slack_payload}")

async def send_webhook(url: str, subject: str, message: str, template_data: dict):
    """Send webhook notification"""
    payload = {
        "subject": subject,
        "message": message,
        "data": template_data,
        "timestamp": datetime.now().isoformat()
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        print(f"🔗 Webhook sent to {url}: {response.status_code}")

async def send_sms(phone: str, message: str, template_data: dict):
    """Send SMS notification"""
    print(f"📱 Sending SMS to {phone}: {message}")
    # In production: integrate with Twilio, AWS SNS, etc.

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)`;
      break;

    default:
      code = `from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="${nodeName} Service")

class ${nodeName}Request(BaseModel):
    trigger_id: str
    data: dict

class ${nodeName}Response(BaseModel):
    result: dict
    status: str

@app.post("${endpoint}")
async def process_${nodeName.toLowerCase()}(request: ${nodeName}Request):
    """
    ${label} - Custom processing endpoint
    """
    try:
        # Custom processing logic here
        result = {
            "processed_by": "${nodeName}",
            "input_data": request.data,
            "trigger_id": request.trigger_id,
            "success": True
        }
        
        return ${nodeName}Response(
            result=result,
            status="completed"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)`;
  }

  return {
    nodeId: node.id,
    nodeName,
    endpoint,
    method,
    code,
    language: 'python'
  };
};

const generateOrchestrator = (nodes: Node<N8nNodeData>[], edges: Edge[]): string => {
  const nodeConnections = edges.map(edge => {
    const source = nodes.find(n => n.id === edge.source)?.data.label || 'unknown';
    const target = nodes.find(n => n.id === edge.target)?.data.label || 'unknown';
    return { source, target };
  });

  return `from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import httpx
import asyncio
from typing import Dict, List, Any
import uuid
from datetime import datetime

app = FastAPI(title="Workflow Orchestrator", description="Manages workflow execution")

class WorkflowRequest(BaseModel):
    data: dict
    workflow_id: str = None

class WorkflowResponse(BaseModel):
    execution_id: str
    status: str
    started_at: str
    workflow_map: Dict[str, str]

# Workflow node configuration
WORKFLOW_NODES = {
${nodes.map(node => `    "${node.data.label}": {
        "service_url": "http://localhost:800${nodes.indexOf(node) + 1}",
        "endpoint": "${generateNodeAPI(node).endpoint}",
        "method": "${generateNodeAPI(node).method}",
        "type": "${node.data.nodeType}"
    }`).join(',\n')}
}

# Workflow connections (execution order)
WORKFLOW_CONNECTIONS = [
${nodeConnections.map(conn => `    {"source": "${conn.source}", "target": "${conn.target}"}`).join(',\n')}
]

@app.post("/workflow/execute")
async def execute_workflow(
    request: WorkflowRequest, 
    background_tasks: BackgroundTasks
):
    """
    Execute the complete workflow
    """
    execution_id = str(uuid.uuid4())
    
    # Start workflow execution in background
    background_tasks.add_task(
        execute_workflow_chain,
        execution_id,
        request.data,
        request.workflow_id
    )
    
    return WorkflowResponse(
        execution_id=execution_id,
        status="started",
        started_at=datetime.now().isoformat(),
        workflow_map=WORKFLOW_NODES
    )

async def execute_workflow_chain(execution_id: str, data: dict, workflow_id: str):
    """
    Execute workflow nodes in sequence based on connections
    """
    try:
        print(f"🚀 Starting workflow execution: {execution_id}")
        
        # Start with trigger nodes
        trigger_nodes = [node for node, config in WORKFLOW_NODES.items() 
                        if config["type"] == "trigger"]
        
        current_data = data
        execution_log = []
        
        for trigger_node in trigger_nodes:
            result = await execute_node(trigger_node, current_data, execution_id)
            execution_log.append(result)
            current_data = result.get("result", current_data)
            
            # Execute connected nodes
            await execute_connected_nodes(trigger_node, current_data, execution_id, execution_log)
        
        print(f"✅ Workflow {execution_id} completed successfully")
        print(f"📊 Execution summary: {len(execution_log)} nodes executed")
        
    except Exception as e:
        print(f"❌ Workflow {execution_id} failed: {str(e)}")

async def execute_connected_nodes(
    current_node: str, 
    data: dict, 
    execution_id: str, 
    execution_log: list
):
    """
    Execute nodes connected to the current node
    """
    connections = [conn for conn in WORKFLOW_CONNECTIONS if conn["source"] == current_node]
    
    for connection in connections:
        target_node = connection["target"]
        
        if target_node in WORKFLOW_NODES:
            result = await execute_node(target_node, data, execution_id)
            execution_log.append(result)
            
            # Recursively execute connected nodes
            await execute_connected_nodes(target_node, result.get("result", data), execution_id, execution_log)

async def execute_node(node_name: str, data: dict, execution_id: str) -> dict:
    """
    Execute a single workflow node
    """
    node_config = WORKFLOW_NODES[node_name]
    
    try:
        async with httpx.AsyncClient() as client:
            url = f"{node_config['service_url']}{node_config['endpoint']}"
            method = node_config['method'].toLowerCase()
            
            payload = {
                "trigger_id": execution_id,
                "data": data
            }
            
            print(f"🔄 Executing {node_name} -> {method.upper()} {url}")
            
            if method == "get":
                response = await client.get(url, params=payload)
            else:
                response = await client.post(url, json=payload)
            
            result = response.json()
            
            print(f"✅ {node_name} completed: {response.status_code}")
            
            return {
                "node": node_name,
                "status": "success",
                "result": result,
                "execution_time": 0.5  # Mock execution time
            }
            
    except Exception as e:
        print(f"❌ {node_name} failed: {str(e)}")
        return {
            "node": node_name,
            "status": "failed",
            "error": str(e),
            "execution_time": 0.1
        }

@app.get("/workflow/status/{execution_id}")
async def get_workflow_status(execution_id: str):
    """
    Get workflow execution status
    """
    # In production: query execution status from database
    return {
        "execution_id": execution_id,
        "status": "completed",
        "nodes_executed": len(WORKFLOW_NODES),
        "total_execution_time": 2.3,
        "success_rate": "100%"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)`;
};

const generateDockerfile = (): string => {
  return `# Multi-stage build for production-ready APIs
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' apiuser
RUN chown -R apiuser:apiuser /app
USER apiuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]`;
};

const generateDeploymentConfig = (): string => {
  return `# Docker Compose for local development
version: '3.8'

services:
  orchestrator:
    build: ./orchestrator
    ports:
      - "8000:8000"
    environment:
      - ENV=development
      - LOG_LEVEL=info
    depends_on:
      - redis
      - postgres

  trigger-service:
    build: ./services/trigger
    ports:
      - "8001:8000"
    environment:
      - ORCHESTRATOR_URL=http://orchestrator:8000

  action-service:
    build: ./services/action
    ports:
      - "8002:8000"
    environment:
      - ORCHESTRATOR_URL=http://orchestrator:8000

  condition-service:
    build: ./services/condition
    ports:
      - "8003:8000"

  validation-service:
    build: ./services/validation
    ports:
      - "8004:8000"

  notification-service:
    build: ./services/notification
    ports:
      - "8005:8000"
    environment:
      - SMTP_SERVER=smtp.gmail.com
      - SMTP_PORT=587

  # Infrastructure services
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=workflow_db
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=secret123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Monitoring
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  postgres_data:

# Production Kubernetes deployment
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: workflow-orchestrator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: orchestrator
  template:
    metadata:
      labels:
        app: orchestrator
    spec:
      containers:
      - name: orchestrator
        image: your-registry/workflow-orchestrator:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10`;
};

export const generateAPICode = async (
  nodes: Node<N8nNodeData>[], 
  edges: Edge[]
): Promise<APIGenerationResult> => {
  // Simulate AI generation delay
  await new Promise(resolve => setTimeout(resolve, 3000));
  
  const apis = nodes.map(generateNodeAPI);
  const orchestrator = generateOrchestrator(nodes, edges);
  const dockerfile = generateDockerfile();
  const deployment = generateDeploymentConfig();
  
  const totalLines = apis.reduce((sum, api) => sum + api.code.split('\n').length, 0) 
                   + orchestrator.split('\n').length 
                   + dockerfile.split('\n').length;
  
  return {
    apis,
    orchestrator,
    dockerfile,
    deployment,
    totalLines,
    executionTime: 2.5 + Math.random() * 2 // 2.5-4.5 seconds
  };
};