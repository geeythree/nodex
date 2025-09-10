"""
Intelligent fallback workflow generation when AI systems fail
"""

import re
from typing import List, Dict, Any, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class IntelligentFallbackGenerator:
    """Generate meaningful workflows based on text analysis when AI fails"""
    
    # Domain-specific workflow patterns with actors, sources, and destinations
    WORKFLOW_PATTERNS = {
        'hr': {
            'onboarding': [
                {
                    'label': 'Receive Employee Data', 
                    'type': 'webhook', 
                    'icon': '📧',
                    'actor': 'HR System',
                    'data_source': 'HRIS/ATS (Workday, BambooHR)',
                    'data_destination': 'Employee Database',
                    'api_endpoint': 'POST /api/employee/new',
                    'inputs': ['employee_id', 'name', 'email', 'department', 'start_date', 'manager_id'],
                    'outputs': ['validated_employee_record', 'workflow_id']
                },
                {
                    'label': 'Validate Information', 
                    'type': 'validation', 
                    'icon': '✅',
                    'actor': 'HR Administrator',
                    'data_source': 'Employee Database',
                    'data_destination': 'Validated Records Queue',
                    'api_endpoint': 'PUT /api/employee/{id}/validate',
                    'inputs': ['employee_record', 'required_fields'],
                    'outputs': ['validation_status', 'missing_fields', 'errors']
                },
                {
                    'label': 'Create User Account', 
                    'type': 'database', 
                    'icon': '👤',
                    'actor': 'IT Administrator',
                    'data_source': 'Validated Records Queue',
                    'data_destination': 'Active Directory/LDAP',
                    'api_endpoint': 'POST /api/identity/create-user',
                    'inputs': ['employee_id', 'department', 'role', 'manager_id'],
                    'outputs': ['username', 'temporary_password', 'user_dn', 'groups']
                },
                {
                    'label': 'Send Welcome Email', 
                    'type': 'email', 
                    'icon': '📨',
                    'actor': 'Email System',
                    'data_source': 'Employee Database + AD',
                    'data_destination': 'Employee Email',
                    'api_endpoint': 'POST /api/email/send-template',
                    'inputs': ['employee_email', 'template_id', 'username', 'temp_password'],
                    'outputs': ['email_sent', 'delivery_status', 'tracking_id']
                },
                {
                    'label': 'Assign Manager', 
                    'type': 'assignment', 
                    'icon': '👥',
                    'actor': 'HR Manager',
                    'data_source': 'Employee Database',
                    'data_destination': 'Management Hierarchy System',
                    'api_endpoint': 'PUT /api/employee/{id}/assign-manager',
                    'inputs': ['employee_id', 'manager_id', 'department'],
                    'outputs': ['assignment_confirmed', 'org_chart_updated']
                },
                {
                    'label': 'Schedule Orientation', 
                    'type': 'calendar', 
                    'icon': '📅',
                    'actor': 'HR Coordinator',
                    'data_source': 'Calendar System',
                    'data_destination': 'Employee & Manager Calendars',
                    'api_endpoint': 'POST /api/calendar/schedule-event',
                    'inputs': ['employee_id', 'manager_id', 'orientation_template'],
                    'outputs': ['event_id', 'attendees_notified', 'calendar_blocked']
                },
                {
                    'label': 'Notify IT Department', 
                    'type': 'notification', 
                    'icon': '💻',
                    'actor': 'IT Service Desk',
                    'data_source': 'Employee Record',
                    'data_destination': 'IT Ticketing System',
                    'api_endpoint': 'POST /api/tickets/create',
                    'inputs': ['employee_id', 'equipment_needed', 'access_requirements'],
                    'outputs': ['ticket_id', 'assigned_technician', 'due_date']
                }
            ],
            'performance_review': [
                {'label': 'Schedule Review Trigger', 'type': 'webhook', 'icon': '⏰'},
                {'label': 'Gather Employee Metrics', 'type': 'database', 'icon': '📊'},
                {'label': 'Notify Manager', 'type': 'notification', 'icon': '👔'},
                {'label': 'Send Review Form', 'type': 'form', 'icon': '📝'},
                {'label': 'Collect Feedback', 'type': 'collection', 'icon': '💭'},
                {'label': 'Generate Report', 'type': 'report', 'icon': '📄'},
                {'label': 'Schedule Meeting', 'type': 'calendar', 'icon': '🤝'}
            ],
            'leave_request': [
                {'label': 'Receive Leave Request', 'type': 'webhook', 'icon': '🏖️'},
                {'label': 'Check Leave Balance', 'type': 'validation', 'icon': '⚖️'},
                {'label': 'Manager Approval', 'type': 'approval', 'icon': '✔️'},
                {'label': 'Update Calendar', 'type': 'calendar', 'icon': '📅'},
                {'label': 'Notify Team', 'type': 'notification', 'icon': '👥'},
                {'label': 'Update HR System', 'type': 'database', 'icon': '💾'}
            ]
        },
        'sales': {
            'lead_qualification': [
                {
                    'label': 'Receive Lead Data',
                    'type': 'webhook',
                    'icon': '🎯',
                    'actor': 'Marketing System',
                    'data_source': 'Website Forms/Marketing Automation',
                    'data_destination': 'Lead Database',
                    'api_endpoint': 'POST /api/leads/capture',
                    'inputs': ['name', 'email', 'company', 'phone', 'source', 'campaign_id'],
                    'outputs': ['lead_id', 'initial_score', 'capture_timestamp']
                },
                {
                    'label': 'Score Lead',
                    'type': 'scoring',
                    'icon': '⭐',
                    'actor': 'Lead Scoring Engine',
                    'data_source': 'Lead Database + Enrichment APIs',
                    'data_destination': 'Qualified Leads Queue',
                    'api_endpoint': 'POST /api/leads/{id}/score',
                    'inputs': ['lead_data', 'company_data', 'behavioral_data'],
                    'outputs': ['lead_score', 'qualification_level', 'priority']
                },
                {
                    'label': 'Check Existing Customer',
                    'type': 'database',
                    'icon': '🔍',
                    'actor': 'CRM System',
                    'data_source': 'Customer Database',
                    'data_destination': 'Lead Enrichment',
                    'api_endpoint': 'GET /api/customers/search',
                    'inputs': ['email', 'company_domain', 'phone'],
                    'outputs': ['existing_customer', 'relationship_history', 'account_status']
                },
                {
                    'label': 'Assign to Sales Rep',
                    'type': 'assignment',
                    'icon': '👤',
                    'actor': 'Sales Manager',
                    'data_source': 'Lead Queue + Sales Team Availability',
                    'data_destination': 'Sales Rep Task List',
                    'api_endpoint': 'POST /api/leads/{id}/assign',
                    'inputs': ['lead_id', 'territory', 'product_interest', 'rep_availability'],
                    'outputs': ['assigned_rep', 'assignment_time', 'sla_deadline']
                },
                {
                    'label': 'Send Follow-up Email',
                    'type': 'email',
                    'icon': '📧',
                    'actor': 'Sales Rep',
                    'data_source': 'Lead Profile + Email Templates',
                    'data_destination': 'Prospect Email',
                    'api_endpoint': 'POST /api/email/send-sales-sequence',
                    'inputs': ['lead_email', 'rep_signature', 'personalization_data'],
                    'outputs': ['email_sent', 'open_tracking', 'response_tracking']
                },
                {
                    'label': 'Schedule Call',
                    'type': 'calendar',
                    'icon': '📞',
                    'actor': 'Sales Rep',
                    'data_source': 'Rep Calendar + Lead Preferences',
                    'data_destination': 'Both Calendars + CRM',
                    'api_endpoint': 'POST /api/calendar/schedule-sales-call',
                    'inputs': ['lead_id', 'rep_id', 'preferred_times', 'call_type'],
                    'outputs': ['meeting_id', 'calendar_invite', 'reminder_set']
                },
                {
                    'label': 'Update CRM',
                    'type': 'database',
                    'icon': '💼',
                    'actor': 'CRM System',
                    'data_source': 'Lead Activity + Interaction Data',
                    'data_destination': 'CRM Pipeline',
                    'api_endpoint': 'PUT /api/crm/opportunities/{id}',
                    'inputs': ['lead_id', 'stage', 'activities', 'next_steps'],
                    'outputs': ['opportunity_id', 'pipeline_position', 'forecast_impact']
                }
            ],
            'deal_closure': [
                {'label': 'Proposal Accepted Trigger', 'type': 'webhook', 'icon': '🎉'},
                {'label': 'Generate Contract', 'type': 'document', 'icon': '📋'},
                {'label': 'Legal Review', 'type': 'approval', 'icon': '⚖️'},
                {'label': 'Send for Signature', 'type': 'signature', 'icon': '✍️'},
                {'label': 'Process Payment', 'type': 'payment', 'icon': '💳'},
                {'label': 'Notify Fulfillment', 'type': 'notification', 'icon': '📦'},
                {'label': 'Update Revenue', 'type': 'database', 'icon': '💰'}
            ]
        },
        'finance': {
            'expense_approval': [
                {'label': 'Receive Expense Report', 'type': 'webhook', 'icon': '🧾'},
                {'label': 'Validate Receipts', 'type': 'validation', 'icon': '🔍'},
                {'label': 'Check Policy Compliance', 'type': 'compliance', 'icon': '📏'},
                {'label': 'Manager Approval', 'type': 'approval', 'icon': '👔'},
                {'label': 'Finance Team Review', 'type': 'approval', 'icon': '💼'},
                {'label': 'Process Reimbursement', 'type': 'payment', 'icon': '💸'},
                {'label': 'Update Accounting', 'type': 'database', 'icon': '📚'}
            ],
            'invoice_processing': [
                {'label': 'Receive Invoice', 'type': 'webhook', 'icon': '📄'},
                {'label': 'Extract Data (OCR)', 'type': 'processing', 'icon': '🔍'},
                {'label': 'Match to PO', 'type': 'matching', 'icon': '🔗'},
                {'label': 'Three-way Match', 'type': 'validation', 'icon': '✅'},
                {'label': 'Approval Workflow', 'type': 'approval', 'icon': '📝'},
                {'label': 'Schedule Payment', 'type': 'scheduling', 'icon': '⏰'},
                {'label': 'Record in GL', 'type': 'database', 'icon': '📊'}
            ]
        },
        'it': {
            'incident_response': [
                {'label': 'Incident Reported', 'type': 'webhook', 'icon': '🚨'},
                {'label': 'Categorize Priority', 'type': 'classification', 'icon': '🏷️'},
                {'label': 'Assign to Technician', 'type': 'assignment', 'icon': '👨‍💻'},
                {'label': 'Notify Stakeholders', 'type': 'notification', 'icon': '📢'},
                {'label': 'Track Resolution', 'type': 'monitoring', 'icon': '⏱️'},
                {'label': 'Update Documentation', 'type': 'documentation', 'icon': '📝'},
                {'label': 'Close Incident', 'type': 'closure', 'icon': '✅'}
            ],
            'user_provisioning': [
                {'label': 'New User Request', 'type': 'webhook', 'icon': '👤'},
                {'label': 'Validate Request', 'type': 'validation', 'icon': '🔍'},
                {'label': 'Create AD Account', 'type': 'database', 'icon': '🔐'},
                {'label': 'Assign Permissions', 'type': 'security', 'icon': '🛡️'},
                {'label': 'Send Credentials', 'type': 'email', 'icon': '🔑'},
                {'label': 'Setup Hardware', 'type': 'provisioning', 'icon': '💻'},
                {'label': 'Training Scheduled', 'type': 'calendar', 'icon': '📚'}
            ]
        }
    }
    
    # Keywords that help identify workflow types
    WORKFLOW_KEYWORDS = {
        'onboarding': ['onboard', 'new employee', 'hire', 'join', 'welcome', 'orientation'],
        'performance_review': ['review', 'performance', 'evaluation', 'feedback', 'appraisal'],
        'leave_request': ['leave', 'vacation', 'time off', 'pto', 'absence', 'holiday'],
        'lead_qualification': ['lead', 'prospect', 'qualify', 'sales pipeline', 'crm'],
        'deal_closure': ['deal', 'close', 'contract', 'proposal', 'sale', 'revenue'],
        'expense_approval': ['expense', 'reimburse', 'receipt', 'spend', 'cost'],
        'invoice_processing': ['invoice', 'bill', 'payment', 'vendor', 'ap', 'accounts payable'],
        'incident_response': ['incident', 'issue', 'problem', 'bug', 'outage', 'support'],
        'user_provisioning': ['user', 'account', 'access', 'provision', 'setup', 'create user']
    }
    
    @staticmethod
    def generate_intelligent_workflow(text: str, domain: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Generate an intelligent workflow based on text analysis
        
        Args:
            text: User's workflow description
            domain: Business domain (hr, sales, finance, it, etc.)
            
        Returns:
            Tuple of (nodes, edges)
        """
        text_lower = text.lower()
        
        # Try to identify specific workflow type
        workflow_type = IntelligentFallbackGenerator._identify_workflow_type(text_lower, domain)
        
        # Get the appropriate workflow template
        if domain in IntelligentFallbackGenerator.WORKFLOW_PATTERNS and workflow_type:
            template_steps = IntelligentFallbackGenerator.WORKFLOW_PATTERNS[domain].get(workflow_type, [])
        else:
            # Generic workflow based on common business process patterns
            template_steps = IntelligentFallbackGenerator._generate_generic_workflow(text, domain)
        
        # Create nodes from template with rich metadata
        nodes = []
        for i, step in enumerate(template_steps):
            node_id = f"node_{i+1}"
            
            # Base node data
            node_data = {
                'label': step['label'],
                'nodeType': step['type'],
                'icon': step['icon'],
                'description': f"{step['label']} - {IntelligentFallbackGenerator._get_node_description(step['type'], domain)}",
                'locked': step['type'] in ['compliance', 'audit', 'security'],
                'compliance_reason': 'Required for regulatory compliance' if step['type'] in ['compliance', 'audit'] else None
            }
            
            # Add rich metadata if available
            if isinstance(step, dict) and 'actor' in step:
                node_data.update({
                    'actor': step.get('actor', 'System'),
                    'data_source': step.get('data_source', 'Unknown'),
                    'data_destination': step.get('data_destination', 'Unknown'),
                    'api_endpoint': step.get('api_endpoint', 'Not specified'),
                    'inputs': step.get('inputs', []),
                    'outputs': step.get('outputs', []),
                    'integration_details': {
                        'who': step.get('actor', 'System'),
                        'from': step.get('data_source', 'Unknown'),
                        'to': step.get('data_destination', 'Unknown'),
                        'how': step.get('api_endpoint', 'Manual process')
                    }
                })
                
                # Enhanced description with integration details
                node_data['description'] = f"{step['label']} - Performed by {step.get('actor', 'System')}, gets data from {step.get('data_source', 'source')}, sends to {step.get('data_destination', 'destination')}"
            
            nodes.append({
                'id': node_id,
                'type': 'n8nNode',
                'position': {
                    'x': 150 + (i % 3) * 250,
                    'y': 150 + (i // 3) * 180
                },
                'data': node_data
            })
        
        # Create edges to connect nodes sequentially
        edges = []
        for i in range(len(nodes) - 1):
            edges.append({
                'id': f"edge_{i+1}",
                'source': nodes[i]['id'],
                'target': nodes[i+1]['id']
            })
        
        # Add some parallel branches for more complex workflows
        if len(nodes) > 4:
            # Add a parallel branch from the 2nd node to the 4th node
            edges.append({
                'id': f"edge_parallel_1",
                'source': nodes[1]['id'],
                'target': nodes[3]['id']
            })
        
        logger.info(f"Generated intelligent fallback workflow: {workflow_type or 'generic'} with {len(nodes)} nodes and {len(edges)} edges")
        
        return nodes, edges
    
    @staticmethod
    def _identify_workflow_type(text: str, domain: str) -> str:
        """Identify the specific workflow type from text"""
        
        best_match = None
        best_score = 0
        
        for workflow_type, keywords in IntelligentFallbackGenerator.WORKFLOW_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > best_score:
                best_score = score
                best_match = workflow_type
        
        # Only return if we found a domain-appropriate workflow
        if best_match and domain in IntelligentFallbackGenerator.WORKFLOW_PATTERNS:
            if best_match in IntelligentFallbackGenerator.WORKFLOW_PATTERNS[domain]:
                return best_match
        
        return None
    
    @staticmethod
    def _generate_generic_workflow(text: str, domain: str) -> List[Dict[str, Any]]:
        """Generate a generic workflow when we can't match a specific pattern"""
        
        # Extract action words and entities from the text
        action_words = re.findall(r'\b(?:create|send|update|process|validate|approve|notify|schedule|generate|assign|check|review|manage|handle)\b', text.lower())
        entities = re.findall(r'\b(?:employee|user|customer|invoice|email|report|data|request|form|document|meeting|task)\b', text.lower())
        
        generic_steps = [
            {'label': f'Receive {entities[0] if entities else "Request"}', 'type': 'webhook', 'icon': '📨'},
            {'label': 'Validate Input Data', 'type': 'validation', 'icon': '✅'},
        ]
        
        # Add steps based on detected actions
        if 'create' in action_words:
            generic_steps.append({'label': f'Create {entities[0] if entities else "Record"}', 'type': 'database', 'icon': '➕'})
        if 'send' in action_words or 'notify' in action_words:
            generic_steps.append({'label': 'Send Notification', 'type': 'notification', 'icon': '📧'})
        if 'approve' in action_words:
            generic_steps.append({'label': 'Approval Process', 'type': 'approval', 'icon': '✔️'})
        if 'update' in action_words:
            generic_steps.append({'label': 'Update System', 'type': 'database', 'icon': '🔄'})
        
        # Always add completion step
        generic_steps.append({'label': 'Process Complete', 'type': 'completion', 'icon': '🎉'})
        
        return generic_steps[:7]  # Limit to 7 steps max
    
    @staticmethod
    def _get_node_description(node_type: str, domain: str) -> str:
        """Get appropriate description for a node type"""
        
        descriptions = {
            'webhook': 'Receives incoming data via HTTP webhook',
            'validation': 'Validates and sanitizes input data',
            'database': 'Stores or retrieves data from database',
            'email': 'Sends email notifications',
            'notification': 'Sends notifications to stakeholders', 
            'approval': 'Requires human approval before proceeding',
            'calendar': 'Creates or updates calendar events',
            'assignment': 'Assigns tasks or resources to users',
            'processing': 'Processes and transforms data',
            'compliance': 'Ensures regulatory compliance requirements',
            'security': 'Applies security and access controls',
            'payment': 'Processes financial transactions',
            'document': 'Generates or manages documents',
            'completion': 'Marks the workflow as complete'
        }
        
        return descriptions.get(node_type, f'Performs {node_type} operation')