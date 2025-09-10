import asyncio
import json
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from loguru import logger
import uuid
from datetime import datetime
from .flow_manager import FlowManager
from .pipecat_voice_handler import PipecatVoiceHandler
import tempfile
import os
from ..compliance import ComplianceAPIIntegration
from pydantic import BaseModel
from .services import SpeechToTextService, TextToSpeechService
from .domain_identifier import DomainIdentificationAgent
from .crew_factory import create_vertical_crew
from .workflow_templates import get_template, list_available_templates

app = FastAPI(
    title="SecureAI Mediator API",
    description="AI-powered workflow builder with voice interaction and compliance enforcement",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:5173",
        "http://localhost:4173",  # Vite preview port
        "http://127.0.0.1:4173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VoiceSessionRequest(BaseModel):
    user_id: str
    session_id: str

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.active_processing_sessions = set()
        self.conversation_history: Dict[str, list] = {}
        self.workflow_states: Dict[str, Dict[str, Any]] = {}  # Track workflow state per session

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        # Initialize conversation history for new sessions
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        # Initialize workflow state for new sessions
        if session_id not in self.workflow_states:
            self.workflow_states[session_id] = {"nodes": [], "edges": []}
        logger.info(f"WebSocket connected for session: {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session: {session_id}")

    async def send_personal_message(self, message: dict, session_id: str):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
                logger.info(f"Message sent to session {session_id}: {message.get('type', 'unknown')}")
                
                # Track agent responses in conversation history
                if message.get('type') == 'agent_response':
                    if session_id not in self.conversation_history:
                        self.conversation_history[session_id] = []
                    self.conversation_history[session_id].append({
                        'role': 'assistant',
                        'message': message.get('message', ''),
                        'timestamp': str(datetime.now())
                    })
            except Exception as e:
                logger.error(f"Failed to send message to {session_id}: {e}")
                self.disconnect(session_id)

    def add_user_message(self, session_id: str, message: str):
        """Add user message to conversation history"""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        self.conversation_history[session_id].append({
            'role': 'user',
            'message': message,
            'timestamp': str(datetime.now())
        })

    def get_workflow_state(self, session_id: str) -> Dict[str, Any]:
        """Get current workflow state for a session"""
        return self.workflow_states.get(session_id, {"nodes": [], "edges": []})

    def update_workflow_state(self, session_id: str, nodes: list, edges: list):
        """Update workflow state for a session"""
        if session_id not in self.workflow_states:
            self.workflow_states[session_id] = {"nodes": [], "edges": []}
        self.workflow_states[session_id]["nodes"] = nodes
        self.workflow_states[session_id]["edges"] = edges

class TextProcessRequest(BaseModel):
    user_input: str
    user_id: str
    session_id: str

class TemplateLoadRequest(BaseModel):
    domain: str
    template_name: str
    user_id: str
    session_id: str

manager = ConnectionManager()

# Initialize components
stt_service = SpeechToTextService()
tts_service = TextToSpeechService()
domain_agent = DomainIdentificationAgent()

async def generate_workflow_and_notify(session_id: str, user_id: str, transcribed_text: str):
    """Vertical-aware multi-agent workflow processing."""
    logger.info(f"Starting vertical-aware workflow generation for: '{transcribed_text}'")
    
    # Prevent duplicate processing for the same session
    processing_key = f"{session_id}:{transcribed_text}"
    if processing_key in manager.active_processing_sessions:
        logger.warning(f"Duplicate processing detected for session {session_id}, skipping")
        return
    
    manager.active_processing_sessions.add(processing_key)
    
    # Add user message to conversation history
    manager.add_user_message(session_id, transcribed_text)

    try:
        # Step 1: Identify the business domain
        domain_classification = await domain_agent.identify_domain(transcribed_text)
        domain = domain_classification.domain
        logger.info(f"Domain identified: {domain} (confidence: {domain_classification.confidence})")

        # Step 2: Create vertical-specific agent crew
        agent_crew = create_vertical_crew(domain)
        logger.info(f"Created agent crew with {len(agent_crew)} agents for domain: {domain}")

        # Step 3: Execute agents in sequence
        processing_context = {
            "original_text": transcribed_text, 
            "user_id": user_id,
            "domain": domain,
            "confidence": domain_classification.confidence,
            "conversation_history": manager.conversation_history.get(session_id, [])
        }
        final_result = {}

        for agent in agent_crew:
            logger.info(f"Executing agent: {agent.name}")
            # Pass the output of the previous agent as context to the next
            agent_result = await agent.process(transcribed_text, processing_context)
            processing_context.update(agent_result)
            
            # Check if ConversationalRequirementsAgent needs more info
            if agent.name == "Conversational Requirements Agent" and agent_result.get("needs_more_info"):
                logger.info("Requirements agent needs more information - stopping pipeline")
                
                # Send the requirements gathering response immediately
                response_data = {
                    "type": "agent_response",
                    "message": agent_result.get("message", "I need more information to create your workflow."),
                    "domain": domain,
                    "confidence": domain_classification.confidence,
                    "needs_more_info": True,
                    "suggested_questions": agent_result.get("suggested_questions", [])
                }
                
                # Generate TTS for the requirements question
                try:
                    voice_response = await tts_service.generate_speech(response_data["message"], user_id)
                    if voice_response.get("success") and voice_response.get("audio_url"):
                        response_data["audio_url"] = voice_response["audio_url"]
                except Exception as e:
                    logger.warning(f"TTS generation failed: {str(e)}")

                await manager.send_personal_message(response_data, session_id)
                return  # Stop processing here to wait for user response
        
        final_result = processing_context

        # Step 4: Send the final result back to the frontend
        agent_response = final_result.get("message", "Workflow processed successfully.")
        response_data = {
            "type": "agent_response",
            "message": agent_response,
            "domain": domain,
            "confidence": domain_classification.confidence
        }

        # Add workflow data if the visualizer agent ran
        if 'nodes' in final_result and 'edges' in final_result:
            response_data.update({
                "workflow_updated": True,
                "nodes": final_result['nodes'],
                "edges": final_result['edges']
            })

        # Generate TTS for the final agent response
        try:
            voice_response = await tts_service.generate_speech(agent_response, user_id)
            if voice_response.get("success") and voice_response.get("audio_url"):
                response_data["audio_url"] = voice_response["audio_url"]
        except Exception as e:
            logger.warning(f"TTS generation failed: {str(e)}")

        await manager.send_personal_message(response_data, session_id)

    except Exception as e:
        logger.error(f"Vertical-aware processing failed: {str(e)}")
        await manager.send_personal_message({
            "type": "agent_response",
            "message": "I encountered an error processing your request. Could you please try again?",
            "error": True
        }, session_id)
    finally:
        # Always remove the processing key when done
        manager.active_processing_sessions.discard(processing_key)

@app.get("/")
async def root():
    return {
        "message": "SecureAI Mediator API",
        "status": "running",
        "version": "1.0.0",
        "features": [
            "Voice interaction via Pipecat",
            "Real-time React Flow updates",
            "Compliance enforcement",
            "Domain inference",
            "WebSocket support"
        ]
    }

@app.get("/api/audio/{filename}")
async def serve_audio_file(filename: str):
    """Serve audio files for voice responses"""
    try:
        # Construct file path (audio files are in temp directory)
        file_path = f"/tmp/{filename}"
        
        # Check if file exists
        if not os.path.exists(file_path):
            return JSONResponse(
                status_code=404,
                content={"error": "Audio file not found"}
            )
        
        return FileResponse(
            file_path,
            media_type="audio/mpeg",
            headers={"Content-Disposition": f"inline; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error serving audio file {filename}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to serve audio file"}
        )

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    logger.info(f"WebSocket connection attempt for session: {session_id}")
    try:
        await manager.connect(websocket, session_id)
        logger.info(f"WebSocket successfully connected for session: {session_id}")
        logger.info(f"Active connections after connect: {list(manager.active_connections.keys())}")
        
        # Send initial connection confirmation
        await manager.send_personal_message({"type": "connection_established"}, session_id)
        
        while True:
            try:
                # Use a timeout to prevent hanging indefinitely
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)
                logger.info(f"Received WebSocket message from {session_id}: {message}")
                
                if message.get("type") == "ping":
                    logger.info(f"Responding to ping from session {session_id}")
                    await manager.send_personal_message({"type": "pong"}, session_id)
                elif message.get("type") == "delete_workflow":
                    include_compliance = message.get("includeCompliance", False)
                    await manager.handle_workflow_deletion(session_id, include_compliance)
                elif message.get("type") == "undo_operation":
                    state = message.get("state")
                    await manager.handle_undo_operation(session_id, state)
                elif message.get("type") == "flow_change":
                    # Handle other flow changes
                    changes = message.get("changes", [])
                    logger.info(f"Processing flow changes: {changes}")
                elif message.get("type") == "user_message":
                    user_message = message.get("message", "")
                    manager.add_user_message(session_id, user_message)
                    
            except asyncio.TimeoutError:
                # Send a keepalive ping to check if connection is still alive
                try:
                    await manager.send_personal_message({"type": "keepalive"}, session_id)
                except:
                    # Connection is broken, exit the loop
                    break
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnect detected for session: {session_id}")
        manager.disconnect(session_id)
        logger.info(f"Active connections after disconnect: {list(manager.active_connections.keys())}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        manager.disconnect(session_id)

@app.post("/api/voice/process")
async def process_voice_input(
    audio: UploadFile = File(...),
    user_id: str = Form(...),
    session_id: Optional[str] = Form(None)
):
    """Process voice input and update workflow"""
    temp_file_path = None
    try:
        # Use the session_id from the form data (sent by frontend)
        if not session_id:
            logger.warning("No session_id provided in voice input")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "session_id is required"
                }
            )
        
        logger.info(f"Processing voice input for existing session {session_id}")
        
        # Save uploaded audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file_path = temp_file.name
            audio_data = await audio.read()
            temp_file.write(audio_data)
        
        # Process voice input
        voice_interaction = await stt_service.transcribe_audio(
            temp_file_path, user_id
        )
        
        if not voice_interaction.get("success"):
            raise Exception(voice_interaction.get("error", "STT failed"))

        # Asynchronously generate workflow and notify the client (this handles TTS)
        asyncio.create_task(generate_workflow_and_notify(session_id, user_id, voice_interaction["content"]))
        
        # Return a simple acknowledgment immediately
        return JSONResponse(content={
            "success": True,
            "message": "Voice input received and is being processed.",
            "transcription": voice_interaction["content"]
        })
        
    except Exception as e:
        logger.error(f"Error processing voice input: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
        )
    finally:
        # Cleanup temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {e}")

@app.post("/api/text/process")
async def process_text_input(text_request: TextProcessRequest):
    """Process text input and update workflow"""
    try:
        # Asynchronously generate workflow and notify the client
        asyncio.create_task(generate_workflow_and_notify(text_request.session_id, text_request.user_id, text_request.user_input))
        
        return JSONResponse(content={
            "success": True,
            "message": "Text input received and is being processed."
        })
        
    except Exception as e:
        logger.error(f"Error processing text input: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "session_id": text_request.session_id
            }
        )

@app.post("/api/templates/load")
async def load_workflow_template(request: TemplateLoadRequest):
    """Load a specific workflow template and send to frontend via WebSocket"""
    try:
        # Get the template from the workflow_templates module
        template = get_template(request.domain, request.template_name)
        
        if not template:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": f"Template {request.template_name} not found in domain {request.domain}"
                }
            )
        
        # Convert template workflow steps to React Flow format
        nodes = []
        edges = []
        
        # Use 'steps' field which contains WorkflowStep objects
        workflow_steps = template.steps if hasattr(template, 'steps') and template.steps else template.workflow_steps if hasattr(template, 'workflow_steps') else []
        
        for step in workflow_steps:
            # Handle both WorkflowStep objects and dictionary formats
            if hasattr(step, 'id'):  # WorkflowStep object
                step_data = {
                    "id": step.id,
                    "name": step.label,
                    "type": step.type,
                    "position": step.position,
                    "description": f"{step.label} - {step.type}"
                }
            else:  # Dictionary format
                step_data = step
            
            node = {
                "id": step_data["id"],
                "type": "default",
                "position": step_data["position"],
                "data": {
                    "label": step_data["name"] if "name" in step_data else step_data.get("label", "Unknown"),
                    "description": step_data.get("description", ""),
                    "locked": step_data.get("type") == "compliance_check"
                },
                "style": {
                    "background": "#3b82f6" if step_data.get("type") == "system_process" else
                                "#10b981" if step_data.get("type") == "user_action" else
                                "#ef4444" if step_data.get("type") == "compliance_check" else
                                "#f59e0b" if step_data.get("type") == "decision" else
                                "#8b5cf6" if step_data.get("type") == "output" else
                                "#06b6d4" if step_data.get("type") == "approval" else "#6b7280",
                    "color": "white",
                    "border": "1px solid #222",
                    "borderRadius": "8px",
                    "padding": "10px",
                    "minWidth": "120px",
                    "fontSize": "12px",
                    "fontWeight": "600"
                }
            }
            nodes.append(node)
        
        # Create edges from template edges if available, otherwise create sequential edges
        if hasattr(template, 'edges') and template.edges:
            for edge_data in template.edges:
                edge = {
                    "id": edge_data["id"],
                    "source": edge_data["source"],
                    "target": edge_data["target"],
                    "type": "default"
                }
                edges.append(edge)
        else:
            # Create edges between sequential steps
            for i in range(len(workflow_steps) - 1):
                step_id = workflow_steps[i].id if hasattr(workflow_steps[i], 'id') else workflow_steps[i]["id"]
                next_step_id = workflow_steps[i+1].id if hasattr(workflow_steps[i+1], 'id') else workflow_steps[i+1]["id"]
                edge = {
                    "id": f"e{i+1}",
                    "source": step_id,
                    "target": next_step_id,
                    "type": "default"
                }
                edges.append(edge)
        
        # Update workflow state
        manager.update_workflow_state(request.session_id, nodes, edges)
        
        # Send workflow update via WebSocket
        response_data = {
            "type": "flow_update",
            "action": "workflow_updated",
            "nodes": nodes,
            "edges": edges,
            "template_name": template.name,
            "domain": request.domain
        }
        
        await manager.send_personal_message(response_data, request.session_id)
        
        # Also send a confirmation message
        confirmation_message = {
            "type": "agent_response",
            "message": f"Loaded {template.name} template with {len(nodes)} workflow steps.",
            "template_loaded": True
        }
        
        await manager.send_personal_message(confirmation_message, request.session_id)
        
        return JSONResponse(content={
            "success": True,
            "message": f"Template {request.template_name} loaded successfully",
            "nodes_count": len(nodes),
            "edges_count": len(edges)
        })
        
    except Exception as e:
        logger.error(f"Error loading template {request.template_name}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

@app.get("/api/templates")
async def list_templates():
    """List available workflow templates"""
    return list_available_templates()

@app.get("/api/templates/{template_name}")
async def load_template(template_name: str):
    """Load a specific workflow template"""
    return get_template(template_name)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
