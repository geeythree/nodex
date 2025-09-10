import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from loguru import logger

from .agent import ComplianceAgent, ComplianceReport
from ..mediator.models import WorkflowState, DomainType
from ..mediator.flow_manager import FlowManager

class ComplianceCheckRequest(BaseModel):
    workflow_id: str
    session_id: str
    enforce_immediately: bool = False

class ComplianceEnforcementRequest(BaseModel):
    workflow_id: str
    session_id: str
    auto_fix: bool = True

class AuditReportRequest(BaseModel):
    workflow_id: str
    session_id: str
    include_recommendations: bool = True

class ComplianceAPIIntegration:
    """Integration layer between Compliance Agent and the main API"""
    
    def __init__(self, flow_manager: FlowManager):
        self.compliance_agent = ComplianceAgent()
        self.flow_manager = flow_manager
        self.router = APIRouter(prefix="/api/compliance", tags=["compliance"])
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes for compliance operations"""
        
        @self.router.post("/validate")
        async def validate_compliance(request: ComplianceCheckRequest):
            """Validate workflow compliance"""
            try:
                session = self.flow_manager.get_session(request.session_id)
                if not session:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                # Run compliance validation
                report = await self.compliance_agent.validate_workflow(session.workflow_state)
                
                # If enforcement is requested and violations found
                if request.enforce_immediately and report.violations:
                    enforcement_result = await self.compliance_agent.enforce_compliance(
                        session.workflow_state
                    )
                    return {
                        "validation_report": report.dict(),
                        "enforcement_applied": True,
                        "enforcement_result": enforcement_result
                    }
                
                return {
                    "validation_report": report.dict(),
                    "enforcement_applied": False
                }
                
            except Exception as e:
                logger.error(f"Compliance validation failed: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/enforce")
        async def enforce_compliance(request: ComplianceEnforcementRequest):
            """Enforce compliance requirements"""
            try:
                session = self.flow_manager.get_session(request.session_id)
                if not session:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                result = await self.compliance_agent.enforce_compliance(session.workflow_state)
                
                # Update the session with enforced changes
                if result["success"]:
                    # Notify WebSocket clients of the changes
                    await self.flow_manager.notify_updates(request.session_id, {
                        "type": "compliance_enforced",
                        "flow": session.workflow_state.flow_graph.dict(),
                        "compliance_result": result,
                        "version": session.workflow_state.version
                    })
                
                return result
                
            except Exception as e:
                logger.error(f"Compliance enforcement failed: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/audit-report")
        async def generate_audit_report(request: AuditReportRequest):
            """Generate comprehensive audit report"""
            try:
                session = self.flow_manager.get_session(request.session_id)
                if not session:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                report = await self.compliance_agent.generate_audit_report(session.workflow_state)
                
                if request.include_recommendations:
                    # Also run validation to get current recommendations
                    validation_report = await self.compliance_agent.validate_workflow(
                        session.workflow_state
                    )
                    report["recommendations"] = validation_report.recommendations
                
                return report
                
            except Exception as e:
                logger.error(f"Audit report generation failed: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/status/{session_id}")
        async def get_compliance_status(session_id: str):
            """Get current compliance status for a workflow"""
            try:
                session = self.flow_manager.get_session(session_id)
                if not session:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                # Quick compliance check
                validation = self.compliance_agent.domain_engine.validate_compliance(
                    session.workflow_state.flow_graph.nodes,
                    session.workflow_state.domain
                )
                
                return {
                    "session_id": session_id,
                    "domain": session.workflow_state.domain.value,
                    "is_compliant": validation["is_compliant"],
                    "violations_count": len(validation.get("violations", [])),
                    "workflow_version": session.workflow_state.version,
                    "last_updated": session.workflow_state.updated_at.isoformat()
                }
                
            except Exception as e:
                logger.error(f"Compliance status check failed: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/auto-monitor/{session_id}")
        async def enable_auto_monitoring(session_id: str, background_tasks: BackgroundTasks):
            """Enable automatic compliance monitoring for a workflow"""
            try:
                session = self.flow_manager.get_session(session_id)
                if not session:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                # Add background task for continuous monitoring
                background_tasks.add_task(
                    self._monitor_compliance_continuously, 
                    session_id
                )
                
                return {
                    "success": True,
                    "message": f"Auto-monitoring enabled for session {session_id}",
                    "monitoring_interval": "30 seconds"
                }
                
            except Exception as e:
                logger.error(f"Auto-monitoring setup failed: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _monitor_compliance_continuously(self, session_id: str):
        """Background task for continuous compliance monitoring"""
        logger.info(f"Starting continuous compliance monitoring for session {session_id}")
        
        try:
            while True:
                session = self.flow_manager.get_session(session_id)
                if not session:
                    logger.info(f"Session {session_id} no longer exists, stopping monitoring")
                    break
                
                # Check compliance
                validation = self.compliance_agent.domain_engine.validate_compliance(
                    session.workflow_state.flow_graph.nodes,
                    session.workflow_state.domain
                )
                
                # If violations found, notify via WebSocket
                if not validation["is_compliant"]:
                    await self.flow_manager.notify_updates(session_id, {
                        "type": "compliance_violation_detected",
                        "violations": validation["violations"],
                        "timestamp": asyncio.get_event_loop().time()
                    })
                    
                    logger.warning(f"Compliance violations detected in session {session_id}")
                
                # Wait before next check
                await asyncio.sleep(30)
                
        except Exception as e:
            logger.error(f"Compliance monitoring error for session {session_id}: {str(e)}")

    def get_router(self) -> APIRouter:
        """Get the FastAPI router for compliance endpoints"""
        return self.router
