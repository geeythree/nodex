import sys
import os
from loguru import logger
from typing import Dict, Any
import json
from datetime import datetime

class StructuredLogger:
    """Structured logging for the Mediator agent system"""
    
    def __init__(self, log_level: str = "INFO", log_file: str = "mediator.log"):
        self.log_level = log_level
        self.log_file = log_file
        self.setup_logging()
    
    def setup_logging(self):
        """Configure loguru with structured logging"""
        # Remove default logger
        logger.remove()
        
        # Console logging with colors
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=self.log_level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        
        # File logging with JSON format
        logger.add(
            self.log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            level=self.log_level,
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            serialize=False,
            backtrace=True,
            diagnose=True
        )
        
        # Structured JSON logging for production
        logger.add(
            "mediator_structured.log",
            format=self._json_formatter,
            level=self.log_level,
            rotation="50 MB",
            retention="90 days",
            compression="zip"
        )
    
    def _json_formatter(self, record):
        """Format log records as JSON"""
        log_entry = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "logger": record["name"],
            "function": record["function"],
            "line": record["line"],
            "message": record["message"],
            "module": record["module"],
            "process": record["process"].id if record["process"] else None,
            "thread": record["thread"].id if record["thread"] else None
        }
        
        # Add extra fields if present
        if "extra" in record:
            log_entry.update(record["extra"])
        
        # Add exception info if present
        if record["exception"]:
            log_entry["exception"] = {
                "type": record["exception"].type.__name__,
                "value": str(record["exception"].value),
                "traceback": record["exception"].traceback
            }
        
        return json.dumps(log_entry) + "\n"
    
    @staticmethod
    def log_voice_interaction(interaction_type: str, user_id: str, content: str, **kwargs):
        """Log voice interactions with structured data"""
        logger.bind(
            event_type="voice_interaction",
            interaction_type=interaction_type,
            user_id=user_id,
            content_length=len(content),
            **kwargs
        ).info(f"Voice interaction: {interaction_type}")
    
    @staticmethod
    def log_flow_update(session_id: str, update_type: str, node_count: int, **kwargs):
        """Log flow diagram updates"""
        logger.bind(
            event_type="flow_update",
            session_id=session_id,
            update_type=update_type,
            node_count=node_count,
            **kwargs
        ).info(f"Flow updated: {update_type}")
    
    @staticmethod
    def log_compliance_check(domain: str, is_compliant: bool, violations: list, **kwargs):
        """Log compliance validation results"""
        logger.bind(
            event_type="compliance_check",
            domain=domain,
            is_compliant=is_compliant,
            violation_count=len(violations),
            violations=violations,
            **kwargs
        ).info(f"Compliance check: {domain} - {'PASS' if is_compliant else 'FAIL'}")
    
    @staticmethod
    def log_agent_execution(agent_name: str, task_name: str, execution_time: float, success: bool, **kwargs):
        """Log agent execution metrics"""
        logger.bind(
            event_type="agent_execution",
            agent_name=agent_name,
            task_name=task_name,
            execution_time=execution_time,
            success=success,
            **kwargs
        ).info(f"Agent execution: {agent_name}.{task_name} - {execution_time:.2f}s")
    
    @staticmethod
    def log_api_request(endpoint: str, method: str, user_id: str, response_time: float, status_code: int, **kwargs):
        """Log API requests"""
        logger.bind(
            event_type="api_request",
            endpoint=endpoint,
            method=method,
            user_id=user_id,
            response_time=response_time,
            status_code=status_code,
            **kwargs
        ).info(f"API {method} {endpoint} - {status_code} ({response_time:.2f}s)")
    
    @staticmethod
    def log_websocket_event(session_id: str, event_type: str, message_type: str, **kwargs):
        """Log WebSocket events"""
        logger.bind(
            event_type="websocket_event",
            session_id=session_id,
            ws_event_type=event_type,
            message_type=message_type,
            **kwargs
        ).info(f"WebSocket {event_type}: {message_type}")
    
    @staticmethod
    def log_error(error_type: str, error_message: str, context: Dict[str, Any] = None, **kwargs):
        """Log errors with context"""
        logger.bind(
            event_type="error",
            error_type=error_type,
            context=context or {},
            **kwargs
        ).error(f"Error [{error_type}]: {error_message}")
    
    @staticmethod
    def log_performance_metric(metric_name: str, value: float, unit: str, context: Dict[str, Any] = None, **kwargs):
        """Log performance metrics"""
        logger.bind(
            event_type="performance_metric",
            metric_name=metric_name,
            value=value,
            unit=unit,
            context=context or {},
            **kwargs
        ).info(f"Metric {metric_name}: {value} {unit}")

class ErrorHandler:
    """Centralized error handling for the Mediator system"""
    
    @staticmethod
    def handle_voice_processing_error(error: Exception, context: Dict[str, Any] = None):
        """Handle voice processing errors"""
        StructuredLogger.log_error(
            error_type="voice_processing_error",
            error_message=str(error),
            context=context
        )
        return {
            "success": False,
            "error": "Voice processing failed",
            "error_type": "voice_processing_error",
            "details": str(error)
        }
    
    @staticmethod
    def handle_flow_update_error(error: Exception, session_id: str, context: Dict[str, Any] = None):
        """Handle flow update errors"""
        StructuredLogger.log_error(
            error_type="flow_update_error",
            error_message=str(error),
            context={**(context or {}), "session_id": session_id}
        )
        return {
            "success": False,
            "error": "Flow update failed",
            "error_type": "flow_update_error",
            "session_id": session_id,
            "details": str(error)
        }
    
    @staticmethod
    def handle_compliance_error(error: Exception, domain: str, context: Dict[str, Any] = None):
        """Handle compliance validation errors"""
        StructuredLogger.log_error(
            error_type="compliance_error",
            error_message=str(error),
            context={**(context or {}), "domain": domain}
        )
        return {
            "success": False,
            "error": "Compliance validation failed",
            "error_type": "compliance_error",
            "domain": domain,
            "details": str(error)
        }
    
    @staticmethod
    def handle_agent_execution_error(error: Exception, agent_name: str, task_name: str, context: Dict[str, Any] = None):
        """Handle agent execution errors"""
        StructuredLogger.log_error(
            error_type="agent_execution_error",
            error_message=str(error),
            context={**(context or {}), "agent_name": agent_name, "task_name": task_name}
        )
        return {
            "success": False,
            "error": "Agent execution failed",
            "error_type": "agent_execution_error",
            "agent_name": agent_name,
            "task_name": task_name,
            "details": str(error)
        }
    
    @staticmethod
    def handle_api_error(error: Exception, endpoint: str, method: str, context: Dict[str, Any] = None):
        """Handle API errors"""
        StructuredLogger.log_error(
            error_type="api_error",
            error_message=str(error),
            context={**(context or {}), "endpoint": endpoint, "method": method}
        )
        return {
            "success": False,
            "error": "API request failed",
            "error_type": "api_error",
            "endpoint": endpoint,
            "method": method,
            "details": str(error)
        }

class PerformanceMonitor:
    """Performance monitoring utilities"""
    
    @staticmethod
    def time_function(func_name: str):
        """Decorator to time function execution"""
        def decorator(func):
            async def async_wrapper(*args, **kwargs):
                start_time = datetime.utcnow()
                try:
                    result = await func(*args, **kwargs)
                    execution_time = (datetime.utcnow() - start_time).total_seconds()
                    StructuredLogger.log_performance_metric(
                        metric_name=f"{func_name}_execution_time",
                        value=execution_time,
                        unit="seconds",
                        context={"function": func_name, "success": True}
                    )
                    return result
                except Exception as e:
                    execution_time = (datetime.utcnow() - start_time).total_seconds()
                    StructuredLogger.log_performance_metric(
                        metric_name=f"{func_name}_execution_time",
                        value=execution_time,
                        unit="seconds",
                        context={"function": func_name, "success": False, "error": str(e)}
                    )
                    raise
            
            def sync_wrapper(*args, **kwargs):
                start_time = datetime.utcnow()
                try:
                    result = func(*args, **kwargs)
                    execution_time = (datetime.utcnow() - start_time).total_seconds()
                    StructuredLogger.log_performance_metric(
                        metric_name=f"{func_name}_execution_time",
                        value=execution_time,
                        unit="seconds",
                        context={"function": func_name, "success": True}
                    )
                    return result
                except Exception as e:
                    execution_time = (datetime.utcnow() - start_time).total_seconds()
                    StructuredLogger.log_performance_metric(
                        metric_name=f"{func_name}_execution_time",
                        value=execution_time,
                        unit="seconds",
                        context={"function": func_name, "success": False, "error": str(e)}
                    )
                    raise
            
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        return decorator

# Initialize global logger
structured_logger = StructuredLogger(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file=os.getenv("LOG_FILE", "mediator.log")
)
