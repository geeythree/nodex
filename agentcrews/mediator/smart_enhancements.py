"""
Smart Enhancement Rules for Domain-Aware Workflow Generation
Provides professional node intelligence and domain-specific enhancements
"""

from typing import Dict, List, Any

class NodeEnhancer:
    """Enhances workflow nodes with professional intelligence and domain awareness"""
    
    def __init__(self):
        self.icon_map = {
            # Core node types
            'webhook': '🔗', 'http': '🌐', 'database': '💾', 'email': '📧', 'code': '💻',
            # Professional operations
            'validation': '✅', 'approval': '👥', 'notification': '🔔', 
            'security': '🔐', 'analytics': '📊', 'audit': '📋', 'monitoring': '👁️',
            'encryption': '🔒', 'compliance': '🛡️', 'alert': '⚠️', 'report': '📄',
            # Business processes
            'form': '📝', 'upload': '📁', 'download': '💾', 'transform': '🔄',
            'filter': '🔍', 'sort': '📶', 'merge': '🔀', 'split': '↗️'
        }
        
        self.domain_specific_icons = {
            'healthcare': {
                'patient': '👤', 'provider': '👨‍⚕️', 'clinic': '🏥', 'prescription': '💊',
                'appointment': '📅', 'medical': '🩺', 'insurance': '🏥', 'hipaa': '🏥📋'
            },
            'finance': {
                'transaction': '💳', 'account': '🏦', 'payment': '💰', 'fraud': '🚨',
                'kyc': '🆔', 'aml': '🔍', 'credit': '📈', 'loan': '🏦'
            },
            'hobbyist': {
                'content': '✏️', 'social': '📱', 'blog': '📝', 'video': '🎥',
                'image': '🖼️', 'analytics': '📊', 'audience': '👥', 'creator': '🎨'
            }
        }
        
        self.professional_descriptions = {
            'webhook': 'Secure endpoint trigger with validation and authentication',
            'http': 'RESTful API integration with error handling and retry logic',
            'database': 'Persistent storage with audit logging and backup procedures',
            'email': 'Professional email service with template management and delivery tracking',
            'validation': 'Comprehensive data validation with business rule enforcement',
            'approval': 'Multi-stage approval workflow with role-based access control',
            'notification': 'Real-time notification system with multiple delivery channels',
            'audit': 'Compliance audit trail with tamper-proof logging',
            'monitoring': 'Real-time system monitoring with automated alerting',
            'security': 'Security checkpoint with encryption and access control'
        }
        
        self.domain_enhancements = {
            'healthcare': {
                'required_nodes': ['patient_consent', 'hipaa_audit', 'clinical_validation'],
                'stakeholders': ['patient', 'provider', 'administrator', 'compliance_officer'],
                'compliance_focus': ['PHI protection', 'HIPAA compliance', 'clinical workflow']
            },
            'finance': {
                'required_nodes': ['kyc_verification', 'fraud_detection', 'regulatory_reporting'],
                'stakeholders': ['customer', 'advisor', 'compliance_officer', 'risk_manager'],
                'compliance_focus': ['PCI-DSS', 'AML', 'SOX compliance', 'fraud prevention']
            },
            'hobbyist': {
                'required_nodes': ['error_handling', 'user_feedback', 'analytics_tracking'],
                'stakeholders': ['creator', 'audience', 'platform'],
                'compliance_focus': ['user experience', 'content quality', 'performance optimization']
            }
        }

    def enhance_node(self, node: Dict[str, Any], domain: str = "general") -> Dict[str, Any]:
        """Enhance a single node with professional intelligence"""
        node_type = node.get('type', node.get('nodeType', 'action'))
        node_label = node.get('label', node.get('name', 'Unknown'))
        
        # Get domain-specific icons if available
        domain_icons = self.domain_specific_icons.get(domain, {})
        
        # Smart icon selection
        icon = self.icon_map.get(node_type, '⚙️')
        for keyword, domain_icon in domain_icons.items():
            if keyword in node_label.lower():
                icon = domain_icon
                break
        
        # Enhanced description
        base_description = node.get('description', '')
        if not base_description:
            base_description = self.professional_descriptions.get(
                node_type, 
                f"Professional {node_type} operation with monitoring and error handling"
            )
        
        # Compliance detection
        compliance_keywords = ['compliance', 'audit', 'hipaa', 'pci', 'gdpr', 'sox', 'kyc', 'aml']
        is_compliance = any(keyword in node_label.lower() for keyword in compliance_keywords)
        
        # Enhanced node data
        enhanced_node = {
            'id': node.get('id', f"node_{hash(node_label)}"),
            'type': 'n8nNode',
            'position': node.get('position', {'x': 100, 'y': 100}),
            'data': {
                'label': node_label,
                'nodeType': node_type,
                'icon': icon,
                'description': base_description,
                'locked': is_compliance,
                'compliance_reason': 'Required for regulatory compliance' if is_compliance else None,
                'domain': domain,
                'professional': True
            }
        }
        
        return enhanced_node

    def suggest_missing_nodes(self, workflow_nodes: List[Dict], domain: str = "general") -> List[Dict]:
        """Suggest missing professional nodes based on domain and existing workflow"""
        suggestions = []
        existing_types = [node.get('data', {}).get('nodeType', '') for node in workflow_nodes]
        
        # Domain-specific missing node detection
        domain_config = self.domain_enhancements.get(domain, {})
        required_nodes = domain_config.get('required_nodes', [])
        
        # Check for missing professional components
        missing_components = []
        
        # Error handling
        if not any('error' in node_type or 'retry' in node_type for node_type in existing_types):
            missing_components.append({
                'label': 'Error Handling & Retry Logic',
                'nodeType': 'error_handler',
                'description': 'Comprehensive error handling with retry logic and graceful degradation'
            })
        
        # Monitoring
        if not any('monitor' in node_type or 'alert' in node_type for node_type in existing_types):
            missing_components.append({
                'label': 'System Monitoring & Alerts',
                'nodeType': 'monitoring',
                'description': 'Real-time monitoring with automated alerting and health checks'
            })
        
        # Audit logging
        if domain in ['healthcare', 'finance'] and not any('audit' in node_type for node_type in existing_types):
            missing_components.append({
                'label': 'Audit Trail Logging',
                'nodeType': 'audit',
                'description': 'Comprehensive audit logging for regulatory compliance'
            })
        
        # User notifications
        if not any('notif' in node_type or 'email' in node_type for node_type in existing_types):
            missing_components.append({
                'label': 'User Notification System',
                'nodeType': 'notification',
                'description': 'Multi-channel user notifications with delivery confirmation'
            })
        
        # Convert suggestions to enhanced nodes
        for i, component in enumerate(missing_components):
            suggestion = self.enhance_node({
                'id': f"suggested_{i+1}",
                'label': component['label'],
                'type': component['nodeType'],
                'description': component['description'],
                'position': {'x': 100 + i * 200, 'y': 300}  # Position below main workflow
            }, domain)
            suggestions.append(suggestion)
        
        return suggestions

    def get_stakeholder_annotations(self, domain: str) -> Dict[str, str]:
        """Get stakeholder annotations for the domain"""
        domain_config = self.domain_enhancements.get(domain, {})
        stakeholders = domain_config.get('stakeholders', ['user', 'admin'])
        
        stakeholder_icons = {
            'patient': '👤', 'provider': '👨‍⚕️', 'administrator': '👩‍💼', 'compliance_officer': '🛡️',
            'customer': '👤', 'advisor': '👨‍💼', 'risk_manager': '⚖️',
            'creator': '🎨', 'audience': '👥', 'platform': '📱',
            'user': '👤', 'admin': '👩‍💼'
        }
        
        return {stakeholder: stakeholder_icons.get(stakeholder, '👤') for stakeholder in stakeholders}

# Global instance for easy import
node_enhancer = NodeEnhancer()