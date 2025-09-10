"""
SecureAI Compliance Agent Module

This module provides comprehensive compliance validation, enforcement, and audit capabilities
for workflow automation systems. It supports multiple regulatory frameworks including:

- HIPAA (Healthcare)
- PCI-DSS (Finance)
- FERPA (Education)
- FISMA (Government)
- SOX (Enterprise)

Key Components:
- ComplianceAgent: Main orchestrator with CrewAI integration
- ComplianceAPIIntegration: REST API endpoints for compliance operations
- Real-time compliance monitoring and enforcement
- Automated audit trail generation
"""

from .agent import ComplianceAgent, ComplianceReport, ComplianceViolation
from .api_integration import ComplianceAPIIntegration

__all__ = [
    'ComplianceAgent',
    'ComplianceReport', 
    'ComplianceViolation',
    'ComplianceAPIIntegration'
]

__version__ = "1.0.0"