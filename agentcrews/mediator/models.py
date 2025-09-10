from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Literal
from enum import Enum
from datetime import datetime

class DomainType(str, Enum):
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    PRODUCTIVITY = "productivity"
    GENERIC = "generic"
    ENTERPRISE = "enterprise"
    EDUCATION = "education"
    GOVERNMENT = "government"

class NodeType(str, Enum):
    INPUT = "input"
    PROCESS = "process"
    OUTPUT = "output"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    APPROVAL = "approval"
    AUDIT = "audit"

class VoiceInteractionType(str, Enum):
    USER_INPUT = "user_input"
    AGENT_RESPONSE = "agent_response"
    CLARIFICATION = "clarification"
    CONFIRMATION = "confirmation"

class Position(BaseModel):
    x: float
    y: float

class NodeData(BaseModel):
    label: str
    description: Optional[str] = None
    domain_required: bool = False
    compliance_type: Optional[str] = None
    locked: bool = False
    parameters: Dict[str, Any] = Field(default_factory=dict)

class FlowNode(BaseModel):
    id: str
    type: NodeType
    data: NodeData
    position: Position
    draggable: bool = True
    selectable: bool = True
    deletable: bool = True

class FlowEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str = "default"
    animated: bool = False
    label: Optional[str] = None

class ReactFlowGraph(BaseModel):
    nodes: List[FlowNode]
    edges: List[FlowEdge]
    viewport: Dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0, "zoom": 1})

class VoiceInteraction(BaseModel):
    id: str
    type: VoiceInteractionType
    content: str
    timestamp: datetime
    audio_url: Optional[str] = None
    transcription_confidence: Optional[float] = None
    user_id: str

class WorkflowState(BaseModel):
    id: str
    user_id: str
    domain: DomainType
    title: str
    description: Optional[str] = None
    flow_graph: ReactFlowGraph
    voice_history: List[VoiceInteraction] = Field(default_factory=list)
    compliance_nodes: List[str] = Field(default_factory=list)  # IDs of locked compliance nodes
    created_at: datetime
    updated_at: datetime
    version: int = 1

class UserIntent(BaseModel):
    raw_input: str
    processed_intent: str
    confidence: float
    domain: Optional[DomainType] = None
    entities: Dict[str, Any] = Field(default_factory=dict)
    workflow_steps: List[str] = Field(default_factory=list)

class AgentResponse(BaseModel):
    agent_name: str
    response_type: str
    content: str
    graph_updates: Optional[ReactFlowGraph] = None
    voice_response: Optional[str] = None
    requires_user_input: bool = False
    clarification_needed: Optional[str] = None

class ComplianceRequirement(BaseModel):
    domain: DomainType
    required_nodes: List[Dict[str, Any]]
    mandatory_flows: List[Dict[str, str]]
    restrictions: List[str]
    explanation: str

class MediatorSession(BaseModel):
    session_id: str
    user_id: str
    workflow_state: WorkflowState
    current_agent: Optional[str] = None
    is_voice_active: bool = False
    last_interaction: datetime
    context: Dict[str, Any] = Field(default_factory=dict)
