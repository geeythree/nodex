import React, { useState } from 'react';

export type NodeTemplate = {
    id: string;
    label: string;
    nodeType: 'trigger' | 'action' | 'condition' | 'webhook' | 'http' | 'schedule' | 'manual';
    icon: string;
    category: string;
    description: string;
};

const nodeTemplates: NodeTemplate[] = [
    // Triggers
    { id: 'webhook', label: 'Webhook Trigger', nodeType: 'webhook', icon: '🔗', category: 'Triggers', description: 'HTTP POST/GET endpoint trigger' },
    { id: 'schedule', label: 'Cron Schedule', nodeType: 'schedule', icon: '⏰', category: 'Triggers', description: 'Time-based trigger with cron expression' },
    { id: 'manual', label: 'Manual Trigger', nodeType: 'manual', icon: '👆', category: 'Triggers', description: 'Manual workflow execution' },

    // API Actions
    { id: 'http_request', label: 'HTTP Request', nodeType: 'http', icon: '🌐', category: 'Actions', description: 'GET/POST/PUT/DELETE API calls' },
    { id: 'rest_api', label: 'REST API Call', nodeType: 'http', icon: '🔌', category: 'Actions', description: 'RESTful API integration' },
    { id: 'graphql', label: 'GraphQL Query', nodeType: 'http', icon: '📊', category: 'Actions', description: 'GraphQL API requests' },
    { id: 'soap_api', label: 'SOAP API', nodeType: 'http', icon: '🧼', category: 'Actions', description: 'SOAP web service calls' },

    // Database Operations
    { id: 'mysql', label: 'MySQL Query', nodeType: 'action', icon: '🗄️', category: 'Actions', description: 'MySQL database operations' },
    { id: 'postgres', label: 'PostgreSQL Query', nodeType: 'action', icon: '🐘', category: 'Actions', description: 'PostgreSQL database operations' },
    { id: 'mongodb', label: 'MongoDB Operation', nodeType: 'action', icon: '🍃', category: 'Actions', description: 'MongoDB document operations' },
    { id: 'redis', label: 'Redis Cache', nodeType: 'action', icon: '🔴', category: 'Actions', description: 'Redis cache operations' },

    // Communication
    { id: 'send_email', label: 'Send Email (SMTP)', nodeType: 'action', icon: '📧', category: 'Actions', description: 'SMTP email sending' },
    { id: 'email_api', label: 'Email API (SendGrid)', nodeType: 'action', icon: '📮', category: 'Actions', description: 'SendGrid/Mailgun API' },
    { id: 'slack_message', label: 'Slack Message', nodeType: 'action', icon: '💬', category: 'Actions', description: 'Send Slack notifications' },
    { id: 'teams_message', label: 'Teams Message', nodeType: 'action', icon: '👥', category: 'Actions', description: 'Microsoft Teams notifications' },

    // File Operations
    { id: 'read_file', label: 'Read File', nodeType: 'action', icon: '📖', category: 'Actions', description: 'Read file from filesystem/cloud' },
    { id: 'write_file', label: 'Write File', nodeType: 'action', icon: '✍️', category: 'Actions', description: 'Write file to filesystem/cloud' },
    { id: 's3_upload', label: 'S3 Upload', nodeType: 'action', icon: '☁️', category: 'Actions', description: 'Upload files to AWS S3' },
    { id: 'ftp_transfer', label: 'FTP Transfer', nodeType: 'action', icon: '📁', category: 'Actions', description: 'FTP file operations' },

    // Logic & Control
    { id: 'if_condition', label: 'IF Condition', nodeType: 'condition', icon: '❓', category: 'Logic', description: 'Conditional branching logic' },
    { id: 'switch_case', label: 'Switch Case', nodeType: 'condition', icon: '🔀', category: 'Logic', description: 'Multiple condition routing' },
    { id: 'merge_data', label: 'Merge Data', nodeType: 'action', icon: '🔗', category: 'Logic', description: 'Combine multiple data streams' },
    { id: 'split_data', label: 'Split Data', nodeType: 'action', icon: '✂️', category: 'Logic', description: 'Split data into multiple paths' },
    { id: 'loop', label: 'Loop/Iterate', nodeType: 'action', icon: '🔄', category: 'Logic', description: 'Loop through data arrays' },
    { id: 'delay', label: 'Wait/Delay', nodeType: 'action', icon: '⏸️', category: 'Logic', description: 'Add delays between steps' },

    // Data Processing
    { id: 'json_transform', label: 'JSON Transform', nodeType: 'action', icon: '🔧', category: 'Logic', description: 'Transform JSON data structure' },
    { id: 'csv_parse', label: 'CSV Parser', nodeType: 'action', icon: '📊', category: 'Logic', description: 'Parse CSV data' },
    { id: 'xml_parse', label: 'XML Parser', nodeType: 'action', icon: '📄', category: 'Logic', description: 'Parse XML documents' },
    { id: 'regex_extract', label: 'Regex Extract', nodeType: 'action', icon: '🔍', category: 'Logic', description: 'Extract data using regex' },

    // Compliance & Security
    { id: 'consent_check', label: 'Consent Verification API', nodeType: 'action', icon: '🔒', category: 'Compliance', description: 'GDPR consent verification' },
    { id: 'audit_log', label: 'Audit Log API', nodeType: 'action', icon: '📋', category: 'Compliance', description: 'Log actions for compliance' },
    { id: 'encrypt_data', label: 'Data Encryption API', nodeType: 'action', icon: '🔐', category: 'Compliance', description: 'Encrypt sensitive data' },
    { id: 'pii_detection', label: 'PII Detection API', nodeType: 'action', icon: '🔍', category: 'Compliance', description: 'Detect personally identifiable information' },
    { id: 'access_control', label: 'Access Control API', nodeType: 'action', icon: '🛡️', category: 'Compliance', description: 'Verify user permissions' },
    { id: 'data_retention', label: 'Data Retention API', nodeType: 'action', icon: '🗂️', category: 'Compliance', description: 'Manage data lifecycle' },

    // Authentication
    { id: 'oauth2', label: 'OAuth2 Authentication', nodeType: 'action', icon: '🔑', category: 'Actions', description: 'OAuth2 token management' },
    { id: 'jwt_verify', label: 'JWT Verification', nodeType: 'action', icon: '🎫', category: 'Actions', description: 'Verify JWT tokens' },
    { id: 'api_key_auth', label: 'API Key Auth', nodeType: 'action', icon: '🗝️', category: 'Actions', description: 'API key authentication' },
];

const categories = ['Triggers', 'Actions', 'Logic', 'Compliance'];

interface NodePaletteProps {
    onNodeDrag: (nodeTemplate: NodeTemplate) => void;
}

const NodePalette: React.FC<NodePaletteProps> = ({ onNodeDrag }) => {
    const [activeCategory, setActiveCategory] = useState('Triggers');
    const [searchTerm, setSearchTerm] = useState('');

    const filteredNodes = nodeTemplates.filter(node =>
        (activeCategory === 'All' || node.category === activeCategory) &&
        (searchTerm === '' || node.label.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    const handleDragStart = (event: React.DragEvent, nodeTemplate: NodeTemplate) => {
        event.dataTransfer.setData('application/reactflow', JSON.stringify(nodeTemplate));
        event.dataTransfer.effectAllowed = 'move';
    };

    return (
        <div className="node-palette">
            <div className="palette-header">
                <h3 className="text-sm font-semibold text-gray-300 mb-3">Node Palette</h3>
                <input
                    type="text"
                    placeholder="Search nodes..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm text-white mb-3"
                />
            </div>

            <div className="palette-categories">
                {categories.map(category => (
                    <button
                        key={category}
                        onClick={() => setActiveCategory(category)}
                        className={`category-tab ${activeCategory === category ? 'active' : ''}`}
                    >
                        {category}
                    </button>
                ))}
            </div>

            <div className="palette-nodes">
                {filteredNodes.map(node => (
                    <div
                        key={node.id}
                        className="palette-node"
                        draggable
                        onDragStart={(e) => handleDragStart(e, node)}
                        onClick={() => onNodeDrag(node)}
                    >
                        <div className="palette-node-icon">{node.icon}</div>
                        <div className="palette-node-info">
                            <div className="palette-node-label">{node.label}</div>
                            <div className="palette-node-description">{node.description}</div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default NodePalette;
