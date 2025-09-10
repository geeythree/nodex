import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export type N8nNodeData = {
    label: string;
    nodeType: 'trigger' | 'action' | 'condition' | 'webhook' | 'http' | 'schedule' | 'manual' | 'database' | 'email' | 'validation' | 'approval' | 'notification' | 'audit' | 'monitoring' | 'security';
    icon?: string;
    color?: string;
    locked?: boolean;
    compliance_reason?: string;
    description?: string;
    executed?: boolean;
    hasError?: boolean;
    domain?: 'healthcare' | 'finance' | 'creator' | 'general';
    professional?: boolean;
};

const nodeTypeConfig = {
    // Core types
    trigger: { color: '#10b981', icon: '⚡' },
    action: { color: '#3b82f6', icon: '⚙️' },
    condition: { color: '#f59e0b', icon: '❓' },
    webhook: { color: '#8b5cf6', icon: '🔗' },
    http: { color: '#06b6d4', icon: '🌐' },
    schedule: { color: '#ef4444', icon: '⏰' },
    manual: { color: '#6b7280', icon: '👆' },
    // Professional types
    database: { color: '#059669', icon: '💾' },
    email: { color: '#dc2626', icon: '📧' },
    validation: { color: '#16a34a', icon: '✅' },
    approval: { color: '#ca8a04', icon: '👥' },
    notification: { color: '#2563eb', icon: '🔔' },
    audit: { color: '#7c2d12', icon: '📋' },
    monitoring: { color: '#4338ca', icon: '👁️' },
    security: { color: '#dc2626', icon: '🔐' }
};

const N8nNode: React.FC<NodeProps<N8nNodeData>> = ({ data, selected }) => {
    const config = nodeTypeConfig[data.nodeType] || nodeTypeConfig.action;
    const isCompliance = data.locked;
    const isProfessional = data.professional || data.domain;

    // Determine node classes based on domain and type
    const getNodeClasses = () => {
        let classes = 'node-modern';
        
        if (selected) classes += ' node-selected';
        if (isCompliance) classes += ' node-compliance';
        if (data.domain) classes += ` node-${data.domain}`;
        if (data.executed) classes += ' node-executed';
        if (data.hasError) classes += ' node-error';
        if (isProfessional) classes += ' node-professional';
        
        return classes;
    };

    return (
        <div className={getNodeClasses()}>
            {/* Input Handle */}
            {data.nodeType !== 'trigger' && data.nodeType !== 'schedule' && data.nodeType !== 'manual' && (
                <Handle
                    type="target"
                    position={Position.Left}
                    style={{ 
                        background: isCompliance ? '#f59e0b' : config.color,
                        border: '2px solid white',
                        width: '12px',
                        height: '12px'
                    }}
                />
            )}

            {/* Domain Badge */}
            {data.domain && (
                <div className={`domain-badge ${data.domain}`}>
                    {data.domain === 'healthcare' && '🏥'}
                    {data.domain === 'finance' && '🏦'}
                    {data.domain === 'creator' && '🎨'}
                </div>
            )}

            {/* Node Content */}
            <div className="node-header">
                <span className="node-icon">{data.icon || config.icon}</span>
                <span>{data.nodeType.replace('_', ' ')}</span>
                {isCompliance && <span style={{ marginLeft: 'auto' }}>🔒</span>}
                {data.executed && <span style={{ marginLeft: 'auto' }}>✓</span>}
                {data.hasError && <span style={{ marginLeft: 'auto' }}>⚠️</span>}
            </div>

            <div className="node-body">
                <div className="node-label">{data.label}</div>
                
                {data.description && (
                    <div className="node-description">{data.description}</div>
                )}
                
                {isCompliance && (
                    <div className="badge compliance-badge">
                        🛡️ <span>Compliance Required</span>
                    </div>
                )}
                
                {data.compliance_reason && (
                    <div className="compliance-reason">
                        {data.compliance_reason}
                    </div>
                )}
            </div>

            {/* Output Handle */}
            <Handle
                type="source"
                position={Position.Right}
                style={{ 
                    background: isCompliance ? '#f59e0b' : config.color,
                    border: '2px solid white',
                    width: '12px',
                    height: '12px'
                }}
            />

            {/* Professional Enhancement Indicator */}
            {isProfessional && !isCompliance && (
                <div className="professional-indicator">
                    ✨
                </div>
            )}
        </div>
    );
};

export default memo(N8nNode);
