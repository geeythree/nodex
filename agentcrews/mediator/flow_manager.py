import asyncio
import json
import uuid
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from loguru import logger

from .models import (
    ReactFlowGraph, FlowNode, FlowEdge, NodeType, NodeData, Position,
    WorkflowState, DomainType, MediatorSession
)
from .domain_inference import DomainInferenceEngine

class FlowManager:
    """Manages React Flow diagrams with real-time updates and compliance enforcement"""
    
    def __init__(self):
        self.domain_engine = DomainInferenceEngine()
        self.active_sessions: Dict[str, MediatorSession] = {}
        self.update_callbacks: Dict[str, List[Callable]] = {}
        
    def register_update_callback(self, session_id: str, callback: Callable):
        """Register callback for flow updates"""
        if session_id not in self.update_callbacks:
            self.update_callbacks[session_id] = []
        self.update_callbacks[session_id].append(callback)
    
    async def notify_updates(self, session_id: str, update_data: Dict[str, Any]):
        """Notify all registered callbacks of flow updates"""
        if session_id in self.update_callbacks:
            for callback in self.update_callbacks[session_id]:
                try:
                    await callback(update_data)
                except Exception as e:
                    logger.error(f"Error in update callback: {str(e)}")
    
    def create_initial_flow(self, user_input: str, user_id: str) -> ReactFlowGraph:
        """Create initial flow from user input"""
        # Infer domain from user input
        domain_info = self.domain_engine.infer_domain(user_input)
        domain = domain_info['primary_domain']
        
        # Create basic input node
        input_node = FlowNode(
            id=f"input_{uuid.uuid4().hex[:8]}",
            type=NodeType.INPUT,
            data=NodeData(
                label="User Input",
                description=user_input[:100] + "..." if len(user_input) > 100 else user_input
            ),
            position=Position(x=100, y=100)
        )
        
        # Create initial nodes list
        nodes = [input_node]
        edges = []
        
        # Add compliance nodes if domain requires them
        if domain != DomainType.GENERIC:
            compliance_nodes = self.domain_engine.create_compliance_nodes(
                domain, Position(x=300, y=100)
            )
            nodes.extend(compliance_nodes)
            
            # Create edges from input to first compliance node
            if compliance_nodes:
                edge = FlowEdge(
                    id=f"edge_{input_node.id}_{compliance_nodes[0].id}",
                    source=input_node.id,
                    target=compliance_nodes[0].id
                )
                edges.append(edge)
                
                # Chain compliance nodes
                for i in range(len(compliance_nodes) - 1):
                    edge = FlowEdge(
                        id=f"edge_{compliance_nodes[i].id}_{compliance_nodes[i+1].id}",
                        source=compliance_nodes[i].id,
                        target=compliance_nodes[i+1].id
                    )
                    edges.append(edge)
        
        return ReactFlowGraph(nodes=nodes, edges=edges)
    
    def add_node(self, flow: ReactFlowGraph, node_data: Dict[str, Any]) -> Optional[FlowNode]:
        """Add a new node to the flow and return the new node"""
        try:
            new_node = FlowNode(
                id=node_data.get('id', f"node_{uuid.uuid4().hex[:8]}"),
                type=NodeType(node_data.get('type', NodeType.PROCESS)),
                data=NodeData(
                    label=node_data['label'],
                    description=node_data.get('description', ''),
                    locked=node_data.get('locked', False)
                ),
                position=Position(
                    x=node_data.get('x', 100),
                    y=node_data.get('y', 100)
                )
            )
            
            flow.nodes.append(new_node)
            return new_node
        except Exception as e:
            logger.error(f"Error creating node: {e}")
            return None
    
    def remove_node(self, flow: ReactFlowGraph, node_id: str, domain: DomainType) -> Dict[str, Any]:
        """Remove a node from the flow with compliance validation"""
        # Find the node to remove
        node_to_remove = None
        for node in flow.nodes:
            if node.id == node_id:
                node_to_remove = node
                break
        
        if not node_to_remove:
            return {
                "success": False,
                "error": "Node not found",
                "flow": flow
            }
        
        # Check if node is locked (compliance node)
        if node_to_remove.data.locked:
            return {
                "success": False,
                "error": f"Cannot remove compliance node: {node_to_remove.data.label}",
                "explanation": "This node is required for compliance and cannot be removed.",
                "flow": flow
            }
        
        # Remove the node
        flow.nodes = [node for node in flow.nodes if node.id != node_id]
        
        # Remove associated edges
        flow.edges = [
            edge for edge in flow.edges 
            if edge.source != node_id and edge.target != node_id
        ]
        
        return {
            "success": True,
            "flow": flow,
            "removed_node": node_to_remove.dict()
        }
    
    def update_node(self, flow: ReactFlowGraph, node_id: str, updates: Dict[str, Any]) -> ReactFlowGraph:
        """Update a node in the flow"""
        for node in flow.nodes:
            if node.id == node_id:
                # Don't allow updating locked nodes' core properties
                if node.data.locked:
                    # Only allow position updates for locked nodes
                    if 'x' in updates or 'y' in updates:
                        if 'x' in updates:
                            node.position.x = updates['x']
                        if 'y' in updates:
                            node.position.y = updates['y']
                else:
                    # Allow full updates for unlocked nodes
                    if 'label' in updates:
                        node.data.label = updates['label']
                    if 'description' in updates:
                        node.data.description = updates['description']
                    if 'x' in updates:
                        node.position.x = updates['x']
                    if 'y' in updates:
                        node.position.y = updates['y']
                break
        
        return flow
    
    def add_edge(self, flow: ReactFlowGraph, source_id: str, target_id: str) -> Optional[FlowEdge]:
        """Add an edge between two nodes and return the new edge"""
        # Check if edge already exists
        for edge in flow.edges:
            if edge.source == source_id and edge.target == target_id:
                return None  # Edge already exists, return None
        
        new_edge = FlowEdge(
            id=f"edge_{source_id}_{target_id}",
            source=source_id,
            target=target_id
        )
        
        flow.edges.append(new_edge)
        return new_edge
    
    def remove_edge(self, flow: ReactFlowGraph, edge_id: str) -> ReactFlowGraph:
        """Remove an edge from the flow"""
        flow.edges = [edge for edge in flow.edges if edge.id != edge_id]
        return flow
    
    def validate_flow_compliance(self, flow: ReactFlowGraph, domain: DomainType) -> Dict[str, Any]:
        """Validate flow against compliance requirements"""
        return self.domain_engine.validate_compliance(flow.nodes, domain)
    
    def auto_fix_compliance(self, flow: ReactFlowGraph, domain: DomainType) -> ReactFlowGraph:
        """Automatically fix compliance issues in the flow"""
        fixed_nodes = self.domain_engine.auto_fix_compliance(flow.nodes, domain)
        flow.nodes = fixed_nodes
        return flow
    
    async def process_flow_delta(
        self, 
        session_id: str, 
        delta: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process incremental changes to the flow"""
        if session_id not in self.active_sessions:
            return {
                "success": False,
                "error": "Session not found"
            }
        
        session = self.active_sessions[session_id]
        flow = session.workflow_state.flow_graph
        domain = session.workflow_state.domain
        
        try:
            # Process different types of deltas
            if delta['type'] == 'node_added':
                new_node = self.add_node(flow, delta['data'])
                if new_node:
                    delta['data'] = new_node.dict()
                else:
                    return {
                        "success": False,
                        "error": "Failed to add node"
                    }
            elif delta['type'] == 'node_removed':
                result = self.remove_node(flow, delta['node_id'], domain)
                if not result['success']:
                    return result
                flow = result['flow']
            elif delta['type'] == 'node_updated':
                flow = self.update_node(flow, delta['node_id'], delta['updates'])
            elif delta['type'] == 'edge_added':
                flow = self.add_edge(flow, delta['source'], delta['target'])
            elif delta['type'] == 'edge_removed':
                flow = self.remove_edge(flow, delta['edge_id'])
            elif delta['type'] == 'viewport_changed':
                flow.viewport = delta['viewport']
            
            # Validate compliance after changes
            compliance_result = self.validate_flow_compliance(flow, domain)
            
            # Auto-fix compliance if needed
            if not compliance_result['is_compliant']:
                flow = self.auto_fix_compliance(flow, domain)
                compliance_result = self.validate_flow_compliance(flow, domain)
            
            # Update session
            session.workflow_state.flow_graph = flow
            session.workflow_state.updated_at = datetime.utcnow()
            session.workflow_state.version += 1
            
            # Notify subscribers
            await self.notify_updates(session_id, {
                "type": "flow_updated",
                "flow": flow.dict(),
                "compliance": compliance_result,
                "version": session.workflow_state.version
            })
            
            return {
                "success": True,
                "flow": flow,
                "compliance": compliance_result,
                "version": session.workflow_state.version
            }
            
        except Exception as e:
            logger.error(f"Error processing flow delta: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_session(
        self, 
        user_id: str, 
        user_input: str, 
        title: str = "New Workflow"
    ) -> MediatorSession:
        """Create a new mediator session with initial flow"""
        session_id = str(uuid.uuid4())
        
        # Infer domain
        domain_info = self.domain_engine.infer_domain(user_input)
        domain = domain_info['primary_domain']
        
        # Create initial flow
        initial_flow = self.create_initial_flow(user_input, user_id)
        
        # Create workflow state
        workflow_state = WorkflowState(
            id=str(uuid.uuid4()),
            user_id=user_id,
            domain=domain,
            title=title,
            description=user_input,
            flow_graph=initial_flow,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Create session
        session = MediatorSession(
            session_id=session_id,
            user_id=user_id,
            workflow_state=workflow_state,
            last_interaction=datetime.utcnow(),
            context={
                "domain_info": domain_info,
                "initial_input": user_input
            }
        )
        
        self.active_sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[MediatorSession]:
        """Get an active session"""
        return self.active_sessions.get(session_id)
    
    def update_session_context(self, session_id: str, context_updates: Dict[str, Any]):
        """Update session context"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].context.update(context_updates)
            self.active_sessions[session_id].last_interaction = datetime.utcnow()
    
    def export_flow_json(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Export flow as JSON for external use (e.g., n8n)"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        flow = session.workflow_state.flow_graph
        
        return {
            "workflow_id": session.workflow_state.id,
            "domain": session.workflow_state.domain.value,
            "title": session.workflow_state.title,
            "nodes": [node.dict() for node in flow.nodes],
            "edges": [edge.dict() for edge in flow.edges],
            "viewport": flow.viewport,
            "version": session.workflow_state.version,
            "created_at": session.workflow_state.created_at.isoformat(),
            "updated_at": session.workflow_state.updated_at.isoformat()
        }
    
    def cleanup_session(self, session_id: str):
        """Clean up session resources"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        if session_id in self.update_callbacks:
            del self.update_callbacks[session_id]
