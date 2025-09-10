import React, { useState, useCallback, useRef, useEffect } from 'react';
import ReactFlow, {
    Node,
    useNodesState,
    useEdgesState,
    Controls,
    Background,
    MiniMap,
    Connection,
    addEdge,
    ReactFlowProvider,
} from 'reactflow';
import 'reactflow/dist/style.css';
import './App.css';
import N8nNode, { N8nNodeData } from './components/N8nNode';
import { generateAPICode } from './utils/apiGenerator';

// NodeTemplate interface for drag and drop functionality
interface NodeTemplate {
    id: string;
    label: string;
    nodeType: string;
    icon: string;
    description: string;
    category: string;
}

// Workflow Template interface
interface WorkflowTemplate {
    id: string;
    name: string;
    description: string;
    category: string;
    icon: string;
    nodes: Array<{
        id: string;
        type: string;
        position: { x: number; y: number };
        data: N8nNodeData;
    }>;
    edges: Array<{
        id: string;
        source: string;
        target: string;
    }>;
}

// Predefined workflow templates
const workflowTemplates: WorkflowTemplate[] = [
    {
        id: 'employee_onboarding',
        name: 'Employee Onboarding',
        description: 'Complete employee onboarding workflow with document collection, validation, and HRIS integration',
        category: 'HR',
        icon: '👋',
        nodes: [
            {
                id: 'trigger_1',
                type: 'n8nNode',
                position: { x: 50, y: 100 },
                data: {
                    label: 'New Employee Form',
                    nodeType: 'trigger',
                    icon: '📝',
                    description: 'Trigger when new employee submits onboarding form',
                    locked: false
                }
            },
            {
                id: 'validate_1',
                type: 'n8nNode',
                position: { x: 280, y: 100 },
                data: {
                    label: 'Validate Documents',
                    nodeType: 'validation',
                    icon: '✅',
                    description: 'Validate employee documents and information',
                    locked: true,
                    compliance_reason: 'Required for HR compliance'
                }
            },
            {
                id: 'action_1',
                type: 'n8nNode',
                position: { x: 510, y: 100 },
                data: {
                    label: 'Create HRIS Record',
                    nodeType: 'action',
                    icon: '👤',
                    description: 'Create employee record in HRIS system',
                    locked: false
                }
            },
            {
                id: 'email_1',
                type: 'n8nNode',
                position: { x: 740, y: 100 },
                data: {
                    label: 'Welcome Email',
                    nodeType: 'email',
                    icon: '📧',
                    description: 'Send welcome email to new employee',
                    locked: false
                }
            }
        ],
        edges: [
            { id: 'e1-2', source: 'trigger_1', target: 'validate_1' },
            { id: 'e2-3', source: 'validate_1', target: 'action_1' },
            { id: 'e3-4', source: 'action_1', target: 'email_1' }
        ]
    },
    {
        id: 'invoice_processing',
        name: 'Invoice Processing',
        description: 'Automated invoice processing with approval workflow and payment processing',
        category: 'Finance',
        icon: '💰',
        nodes: [
            {
                id: 'trigger_1',
                type: 'n8nNode',
                position: { x: 50, y: 100 },
                data: {
                    label: 'Invoice Received',
                    nodeType: 'trigger',
                    icon: '📄',
                    description: 'Trigger when new invoice is received',
                    locked: false
                }
            },
            {
                id: 'validate_1',
                type: 'n8nNode',
                position: { x: 280, y: 100 },
                data: {
                    label: 'Validate Invoice',
                    nodeType: 'validation',
                    icon: '🔍',
                    description: 'Validate invoice data and compliance',
                    locked: true,
                    compliance_reason: 'Required for financial compliance'
                }
            },
            {
                id: 'approval_1',
                type: 'n8nNode',
                position: { x: 510, y: 100 },
                data: {
                    label: 'Manager Approval',
                    nodeType: 'approval',
                    icon: '✍️',
                    description: 'Route to manager for approval',
                    locked: false
                }
            },
            {
                id: 'action_1',
                type: 'n8nNode',
                position: { x: 740, y: 100 },
                data: {
                    label: 'Process Payment',
                    nodeType: 'action',
                    icon: '💳',
                    description: 'Process approved payment',
                    locked: false
                }
            },
            {
                id: 'audit_1',
                type: 'n8nNode',
                position: { x: 970, y: 100 },
                data: {
                    label: 'Audit Log',
                    nodeType: 'audit',
                    icon: '📋',
                    description: 'Log transaction for audit trail',
                    locked: true,
                    compliance_reason: 'Required for financial audit'
                }
            }
        ],
        edges: [
            { id: 'e1-2', source: 'trigger_1', target: 'validate_1' },
            { id: 'e2-3', source: 'validate_1', target: 'approval_1' },
            { id: 'e3-4', source: 'approval_1', target: 'action_1' },
            { id: 'e4-5', source: 'action_1', target: 'audit_1' }
        ]
    },
    {
        id: 'customer_support',
        name: 'Customer Support Ticket',
        description: 'Customer support workflow with auto-categorization, routing, and follow-up',
        category: 'Support',
        icon: '🎧',
        nodes: [
            {
                id: 'trigger_1',
                type: 'n8nNode',
                position: { x: 50, y: 100 },
                data: {
                    label: 'Ticket Created',
                    nodeType: 'trigger',
                    icon: '🎫',
                    description: 'Trigger when customer creates support ticket',
                    locked: false
                }
            },
            {
                id: 'condition_1',
                type: 'n8nNode',
                position: { x: 280, y: 100 },
                data: {
                    label: 'Categorize Issue',
                    nodeType: 'condition',
                    icon: '🏷️',
                    description: 'Auto-categorize ticket by type and priority',
                    locked: false
                }
            },
            {
                id: 'action_1',
                type: 'n8nNode',
                position: { x: 510, y: 50 },
                data: {
                    label: 'Route to Expert',
                    nodeType: 'action',
                    icon: '👨‍💼',
                    description: 'Route to appropriate specialist',
                    locked: false
                }
            },
            {
                id: 'notification_1',
                type: 'n8nNode',
                position: { x: 510, y: 150 },
                data: {
                    label: 'Customer Update',
                    nodeType: 'notification',
                    icon: '📱',
                    description: 'Send status update to customer',
                    locked: false
                }
            },
            {
                id: 'database_1',
                type: 'n8nNode',
                position: { x: 740, y: 100 },
                data: {
                    label: 'Update CRM',
                    nodeType: 'database',
                    icon: '💾',
                    description: 'Update customer record in CRM',
                    locked: false
                }
            }
        ],
        edges: [
            { id: 'e1-2', source: 'trigger_1', target: 'condition_1' },
            { id: 'e2-3', source: 'condition_1', target: 'action_1' },
            { id: 'e2-4', source: 'condition_1', target: 'notification_1' },
            { id: 'e3-5', source: 'action_1', target: 'database_1' },
            { id: 'e4-5', source: 'notification_1', target: 'database_1' }
        ]
    },
    {
        id: 'content_approval',
        name: 'Content Approval',
        description: 'Content creation and approval workflow with review stages and publishing',
        category: 'Marketing',
        icon: '📝',
        nodes: [
            {
                id: 'trigger_1',
                type: 'n8nNode',
                position: { x: 50, y: 100 },
                data: {
                    label: 'Content Submitted',
                    nodeType: 'trigger',
                    icon: '📝',
                    description: 'Trigger when content is submitted for review',
                    locked: false
                }
            },
            {
                id: 'validation_1',
                type: 'n8nNode',
                position: { x: 280, y: 100 },
                data: {
                    label: 'Quality Check',
                    nodeType: 'validation',
                    icon: '🔍',
                    description: 'Validate content quality and guidelines',
                    locked: false
                }
            },
            {
                id: 'approval_1',
                type: 'n8nNode',
                position: { x: 510, y: 100 },
                data: {
                    label: 'Editorial Review',
                    nodeType: 'approval',
                    icon: '👨‍💼',
                    description: 'Editorial team review and approval',
                    locked: false
                }
            },
            {
                id: 'action_1',
                type: 'n8nNode',
                position: { x: 740, y: 100 },
                data: {
                    label: 'Publish Content',
                    nodeType: 'action',
                    icon: '🚀',
                    description: 'Publish approved content',
                    locked: false
                }
            },
            {
                id: 'notification_1',
                type: 'n8nNode',
                position: { x: 970, y: 100 },
                data: {
                    label: 'Notify Team',
                    nodeType: 'notification',
                    icon: '📢',
                    description: 'Notify team of published content',
                    locked: false
                }
            }
        ],
        edges: [
            { id: 'e1-2', source: 'trigger_1', target: 'validation_1' },
            { id: 'e2-3', source: 'validation_1', target: 'approval_1' },
            { id: 'e3-4', source: 'approval_1', target: 'action_1' },
            { id: 'e4-5', source: 'action_1', target: 'notification_1' }
        ]
    },
    {
        id: 'data_processing',
        name: 'Data Processing Pipeline',
        description: 'ETL pipeline with data validation, transformation, and storage',
        category: 'Data',
        icon: '📊',
        nodes: [
            {
                id: 'trigger_1',
                type: 'n8nNode',
                position: { x: 50, y: 100 },
                data: {
                    label: 'Data Source',
                    nodeType: 'trigger',
                    icon: '📡',
                    description: 'Trigger when new data arrives',
                    locked: false
                }
            },
            {
                id: 'validation_1',
                type: 'n8nNode',
                position: { x: 280, y: 100 },
                data: {
                    label: 'Data Validation',
                    nodeType: 'validation',
                    icon: '🔍',
                    description: 'Validate data quality and format',
                    locked: false
                }
            },
            {
                id: 'action_1',
                type: 'n8nNode',
                position: { x: 510, y: 100 },
                data: {
                    label: 'Transform Data',
                    nodeType: 'action',
                    icon: '🔄',
                    description: 'Clean and transform data',
                    locked: false
                }
            },
            {
                id: 'database_1',
                type: 'n8nNode',
                position: { x: 740, y: 100 },
                data: {
                    label: 'Store Data',
                    nodeType: 'database',
                    icon: '💾',
                    description: 'Store processed data in warehouse',
                    locked: false
                }
            },
            {
                id: 'notification_1',
                type: 'n8nNode',
                position: { x: 970, y: 100 },
                data: {
                    label: 'Processing Complete',
                    nodeType: 'notification',
                    icon: '✅',
                    description: 'Notify completion of data processing',
                    locked: false
                }
            }
        ],
        edges: [
            { id: 'e1-2', source: 'trigger_1', target: 'validation_1' },
            { id: 'e2-3', source: 'validation_1', target: 'action_1' },
            { id: 'e3-4', source: 'action_1', target: 'database_1' },
            { id: 'e4-5', source: 'database_1', target: 'notification_1' }
        ]
    },
    {
        id: 'security_incident',
        name: 'Security Incident Response',
        description: 'Security incident detection, response, and remediation workflow',
        category: 'Security',
        icon: '🔒',
        nodes: [
            {
                id: 'trigger_1',
                type: 'n8nNode',
                position: { x: 50, y: 100 },
                data: {
                    label: 'Security Alert',
                    nodeType: 'trigger',
                    icon: '🚨',
                    description: 'Trigger when security incident detected',
                    locked: false
                }
            },
            {
                id: 'validation_1',
                type: 'n8nNode',
                position: { x: 280, y: 100 },
                data: {
                    label: 'Threat Assessment',
                    nodeType: 'validation',
                    icon: '🔍',
                    description: 'Assess threat level and validity',
                    locked: true,
                    compliance_reason: 'Required for security compliance'
                }
            },
            {
                id: 'condition_1',
                type: 'n8nNode',
                position: { x: 510, y: 100 },
                data: {
                    label: 'Risk Classification',
                    nodeType: 'condition',
                    icon: '⚠️',
                    description: 'Classify risk level (low/medium/high)',
                    locked: false
                }
            },
            {
                id: 'action_1',
                type: 'n8nNode',
                position: { x: 740, y: 50 },
                data: {
                    label: 'Auto Remediation',
                    nodeType: 'action',
                    icon: '🛠️',
                    description: 'Automated security response',
                    locked: false
                }
            },
            {
                id: 'notification_1',
                type: 'n8nNode',
                position: { x: 740, y: 150 },
                data: {
                    label: 'Alert Security Team',
                    nodeType: 'notification',
                    icon: '📢',
                    description: 'Notify security team of incident',
                    locked: false
                }
            },
            {
                id: 'audit_1',
                type: 'n8nNode',
                position: { x: 970, y: 100 },
                data: {
                    label: 'Incident Log',
                    nodeType: 'audit',
                    icon: '📋',
                    description: 'Log incident for audit and analysis',
                    locked: true,
                    compliance_reason: 'Required for security audit'
                }
            }
        ],
        edges: [
            { id: 'e1-2', source: 'trigger_1', target: 'validation_1' },
            { id: 'e2-3', source: 'validation_1', target: 'condition_1' },
            { id: 'e3-4', source: 'condition_1', target: 'action_1' },
            { id: 'e3-5', source: 'condition_1', target: 'notification_1' },
            { id: 'e4-6', source: 'action_1', target: 'audit_1' },
            { id: 'e5-6', source: 'notification_1', target: 'audit_1' }
        ]
    }
];

const nodeTypes = {
    n8nNode: N8nNode,
};

// Node Edit Form Component
interface NodeEditFormProps {
    node: Node<N8nNodeData>;
    onSave: (data: { label: string; description: string }) => void;
    onCancel: () => void;
}

const NodeEditForm: React.FC<NodeEditFormProps> = ({ node, onSave, onCancel }) => {
    const [label, setLabel] = useState(node.data.label);
    const [description, setDescription] = useState(node.data.description || '');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (label.trim()) {
            onSave({ label: label.trim(), description: description.trim() });
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Escape') {
            onCancel();
        }
    };

    return (
        <form onSubmit={handleSubmit} onKeyDown={handleKeyDown}>
            <div style={{ marginBottom: '16px' }}>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    marginBottom: '16px',
                    padding: '12px',
                    background: 'var(--gray-700)',
                    borderRadius: 'var(--radius)',
                    border: '1px solid var(--gray-600)'
                }}>
                    <span style={{ fontSize: '24px', marginRight: '12px' }}>
                        {node.data.icon}
                    </span>
                    <div>
                        <div style={{ fontSize: '14px', fontWeight: '600', color: 'var(--white)' }}>
                            {node.data.nodeType.charAt(0).toUpperCase() + node.data.nodeType.slice(1)} Node
                        </div>
                        <div style={{ fontSize: '12px', color: 'var(--gray-400)' }}>
                            {node.data.locked ? '🔒 Compliance Node' : 'Editable Node'}
                        </div>
                    </div>
                </div>

                <label className="input-label">Node Name:</label>
                <input
                    type="text"
                    className="input"
                    value={label}
                    onChange={(e) => setLabel(e.target.value)}
                    placeholder="Enter node name..."
                    autoFocus
                    disabled={node.data.locked}
                />
                {node.data.locked && (
                    <div style={{ fontSize: '12px', color: 'var(--gray-400)', marginTop: '4px' }}>
                        ⚠️ Compliance nodes cannot be renamed
                    </div>
                )}
            </div>

            <div style={{ marginBottom: '24px' }}>
                <label className="input-label">Description:</label>
                <textarea
                    className="textarea"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Enter node description..."
                    rows={3}
                />
            </div>

            {node.data.compliance_reason && (
                <div style={{
                    marginBottom: '16px',
                    padding: '12px',
                    background: 'rgba(234, 179, 8, 0.1)',
                    border: '1px solid rgba(234, 179, 8, 0.3)',
                    borderRadius: 'var(--radius)'
                }}>
                    <div style={{ fontSize: '12px', color: 'var(--yellow)', fontWeight: '600' }}>
                        🔒 Compliance Requirement:
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--gray-300)', marginTop: '4px' }}>
                        {node.data.compliance_reason}
                    </div>
                </div>
            )}

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                <button
                    type="button"
                    onClick={onCancel}
                    className="btn btn-secondary"
                >
                    Cancel
                </button>
                <button
                    type="submit"
                    className="btn btn-blue"
                    disabled={!label.trim() || (node.data.locked && label !== node.data.label)}
                >
                    Save Changes
                </button>
            </div>
        </form>
    );
};

const App: React.FC = () => {
    // Prompt library data
    const promptLibrary = [
        "Design a process so every time a patient record is updated, the change is double-checked by a compliance nurse and logged for audit.",
        "Whenever an invoice above $10,000 comes in, route it for CFO approval and make sure anti-fraud checks are performed automatically",
        "Set up a workflow so job offer letters can't be sent until the background check and HR approval are complete, and notify the recruiter at each step",
        "Whenever a new employee requests VPN access, require manager approval, log the request, and send the IT admin a summary every Friday",
        "Every time a customer asks for their data to be deleted, make sure the request is reviewed by privacy, then confirm completion by email.",
        "Build a process to enroll a student in a course only after their documents are verified and tuition payment is confirmed",
        "For any software purchase, require security review, procurement approval, and legal sign-off before the vendor gets paid",
        "Whenever a new permit application is submitted, check eligibility, send for supervisor review, and notify the applicant of next steps.",
        "Set up claims processing to flag cases over $5,000 for manual review, then notify the claims manager after the review is done",
        "Make it so all outbound email campaigns are checked for up-to-date unsubscribe lists and logged for compliance review."
    ];

    // State management
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [textInput, setTextInput] = useState('');
    const [uploadedImage, setUploadedImage] = useState<string | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [showExportModal, setShowExportModal] = useState(false);
    const [exportedJson, setExportedJson] = useState('');
    const [workflowId, setWorkflowId] = useState('');

    // API generation settings
    const [isGeneratingAPIs, setIsGeneratingAPIs] = useState(false);
    const [generatedAPIs, setGeneratedAPIs] = useState<any>(null);
    // Removed showCodeModal - not showing code to users
    const [selectedAPI, setSelectedAPI] = useState<any>(null);
    const [showDashboard, setShowDashboard] = useState(false);

    const reactFlowWrapper = useRef<HTMLDivElement>(null);
    const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);
    const [_processingStage, setProcessingStage] = useState('');
    const [detectedDomain] = useState<string | null>(null);
    const [selectedNodes, setSelectedNodes] = useState<string[]>([]);
    const [showTemplateModal, setShowTemplateModal] = useState(false);
    const [showPromptLibrary, setShowPromptLibrary] = useState(false);
    const [editingNode, setEditingNode] = useState<Node<N8nNodeData> | null>(null);
    const [showEditModal, setShowEditModal] = useState(false);
    const pendingPositions = useRef<Array<{ x: number; y: number }>>([]);
    const allPositions = useRef<Array<{ x: number; y: number }>>([]);

    // Sync allPositions with nodes state
    useEffect(() => {
        allPositions.current = nodes.map(node => node.position);
    }, [nodes]);

    // Save workflow to localStorage whenever nodes or edges change (with debounce)
    useEffect(() => {
        // Skip auto-save if we're currently editing a node to prevent conflicts
        if (showEditModal) return;

        const timeoutId = setTimeout(() => {
            if (nodes.length > 0 || edges.length > 0) {
                const workflowData = {
                    nodes,
                    edges,
                    timestamp: Date.now()
                };
                localStorage.setItem('nodex-workflow', JSON.stringify(workflowData));
            }
        }, 500); // 500ms debounce

        return () => clearTimeout(timeoutId);
    }, [nodes, edges, showEditModal]);

    // Load workflow from localStorage on component mount
    useEffect(() => {
        const savedWorkflow = localStorage.getItem('nodex-workflow');
        if (savedWorkflow) {
            try {
                const workflowData = JSON.parse(savedWorkflow);
                if (workflowData.nodes && workflowData.edges) {
                    setNodes(workflowData.nodes);
                    setEdges(workflowData.edges);
                    addChatMessage('system', 'Restored previous workflow from local storage');
                }
            } catch (error) {
                console.error('Failed to restore workflow:', error);
            }
        }
    }, []); // Empty dependency array - only run on mount

    // Processing stages with dynamic messages
    const processingStages = [
        { stage: 'collecting', message: 'Collecting requirements' },
        { stage: 'thinking', message: 'AI agents thinking' },
        { stage: 'planning', message: 'Planning workflow structure' },
        { stage: 'compliance', message: 'Adding compliance checks' },
        { stage: 'generating', message: 'Generating workflow' },
        { stage: 'finalizing', message: 'Finalizing and validating' }
    ];

    // Processing stage management
    useEffect(() => {
        if (isProcessing) {
            let currentStageIndex = 0;
            setProcessingStage(processingStages[0].stage);

            const stageInterval = setInterval(() => {
                currentStageIndex = (currentStageIndex + 1) % processingStages.length;
                setProcessingStage(processingStages[currentStageIndex].stage);
            }, 2500);

            return () => clearInterval(stageInterval);
        } else {
            setProcessingStage('');
        }
    }, [isProcessing, processingStages]);




    // Handle new connections
    const onConnect = useCallback((params: Connection) => {
        setEdges((eds) => addEdge(params, eds));
    }, [setEdges]);

    // Add chat message
    const addChatMessage = useCallback((_role: 'user' | 'assistant' | 'system', _content: string) => {
        // Placeholder for chat functionality
        // Could implement actual chat UI here in the future
    }, []);

    // Handle drag over
    const onDragOver = useCallback((event: React.DragEvent) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
    }, []);

    // Handle drop
    const onDrop = useCallback(
        (event: React.DragEvent) => {
            event.preventDefault();

            const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
            const nodeTemplate = JSON.parse(
                event.dataTransfer.getData('application/reactflow')
            ) as NodeTemplate;

            if (nodeTemplate && reactFlowInstance && reactFlowBounds) {
                const position = reactFlowInstance.project({
                    x: event.clientX - reactFlowBounds.left,
                    y: event.clientY - reactFlowBounds.top,
                });

                const newNode: Node<N8nNodeData> = {
                    id: `${nodeTemplate.id}_${Date.now()}`,
                    type: 'n8nNode',
                    position,
                    data: {
                        label: nodeTemplate.label,
                        nodeType: nodeTemplate.nodeType as 'trigger' | 'action' | 'condition' | 'webhook' | 'http' | 'schedule' | 'manual' | 'database' | 'email' | 'validation' | 'approval' | 'notification' | 'audit' | 'monitoring' | 'security',
                        icon: nodeTemplate.icon,
                        description: nodeTemplate.description,
                        locked: nodeTemplate.category === 'Compliance',
                        compliance_reason: nodeTemplate.category === 'Compliance' ? 'Required for regulatory compliance' : undefined,
                    },
                };

                setNodes((nds) => nds.concat(newNode));
                addChatMessage('system', `Added ${nodeTemplate.label} node to workflow`);
            }
        },
        [reactFlowInstance, setNodes, addChatMessage]
    );


    // Process text workflow
    const processTextWorkflow = useCallback(async () => {
        if (!textInput.trim()) return;

        setIsProcessing(true);

        // Generate workflow ID immediately
        const newWorkflowId = `workflow_${Date.now()}`;
        setWorkflowId(newWorkflowId);

        try {
            const response = await fetch('http://localhost:8000/api/interpret', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: textInput,
                    domain: 'hr',
                    workflow_id: newWorkflowId
                }),
            });

            if (response.ok) {
                const result = await response.json();

                // Convert backend nodes to n8n-style nodes with intelligent positioning
                let n8nNodes: Node<N8nNodeData>[] = result.nodes.map((node: any) => ({
                    id: node.id,
                    type: 'n8nNode',
                    position: node.position, // Will be overridden by intelligent arrangement
                    data: {
                        label: node.data.label,
                        nodeType: node.data.nodeType,
                        icon: node.data.icon,
                        description: node.data.description,
                        locked: node.data.locked,
                        compliance_reason: node.data.compliance_reason,
                        hasError: node.data.hasError,
                    },
                }));

                // Apply intelligent positioning to prevent overlaps
                n8nNodes = arrangeNodesIntelligently(n8nNodes);
                setNodes(n8nNodes);
                console.log('DEBUG: Setting edges from API:', result.edges);
                setEdges(result.edges || []);
                console.log('DEBUG: Edges set, current length:', result.edges?.length || 0);
                addChatMessage('assistant', `Generated workflow with ${result.nodes?.length || 0} nodes and ${result.compliance_info?.compliance_nodes_added || 0} compliance checks for ${result.compliance_info?.domain || 'general'} domain.`);
            } else {
                throw new Error('Failed to process text');
            }
        } catch (error) {
            addChatMessage('system', 'Error: Failed to generate workflow from text');
            // Error already handled by user-facing message
        } finally {
            setIsProcessing(false);
            setWorkflowId('');
        }
    }, [textInput, setNodes, setEdges, addChatMessage]);

    // Debug edge changes
    useEffect(() => {
        console.log('DEBUG: Edges state changed:', edges.length, edges);
    }, [edges]);

    // Poll backend for real-time progress updates
    useEffect(() => {
        if (isProcessing && workflowId) {
            // Starting progress polling

            const pollProgress = async () => {
                try {
                    const response = await fetch(`http://localhost:8000/api/progress/${workflowId}`);
                    if (response.ok) {
                        const progress = await response.json();
                        // Progress received
                        setProcessingStage(progress.stage);
                    }
                } catch (error) {
                    // Progress polling failed
                }
            };

            // Poll immediately and then every 500ms for faster updates
            pollProgress();
            const interval = setInterval(pollProgress, 500);
            return () => clearInterval(interval);
        }
    }, [isProcessing, workflowId]);

    // Handle image upload
    const handleImageUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
        // Clear the file input
        event.target.value = '';

        // Show message about limited processing power
        alert('⚠️ We currently cannot support image uploads due to limited processing power. Please create your workflow using the one of the templates instead.');
    }, []);

    // Process uploaded image
    const processImageWorkflow = useCallback(async () => {
        if (!uploadedImage) return;

        setIsProcessing(true);
        addChatMessage('system', 'Analyzing workflow diagram...');

        try {

            const response = await fetch('http://localhost:8000/api/parse-image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    image: uploadedImage,
                    domain: 'general'
                }),
            });


            if (response.ok) {
                const result = await response.json();

                // Convert backend nodes to n8n-style nodes with intelligent positioning
                let n8nNodes: Node<N8nNodeData>[] = result.nodes.map((node: any) => ({
                    id: node.id,
                    type: 'n8nNode',
                    position: node.position, // Will be overridden by intelligent arrangement
                    data: {
                        label: node.data.label,
                        nodeType: node.data.nodeType,
                        icon: node.data.icon,
                        description: node.data.description,
                        locked: node.data.locked,
                        compliance_reason: node.data.compliance_reason,
                        hasError: node.data.hasError,
                    },
                }));

                // Apply intelligent positioning to prevent overlaps
                n8nNodes = arrangeNodesIntelligently(n8nNodes);
                setNodes(n8nNodes);
                console.log('DEBUG: Setting edges from image API:', result.edges);
                setEdges(result.edges || []);
                console.log('DEBUG: Image edges set, current length:', result.edges?.length || 0);
                addChatMessage('assistant', `Extracted workflow from image: ${result.nodes?.length || 0} nodes with ${result.compliance_info?.compliance_nodes_added || 0} compliance checks.`);
            } else {
                throw new Error('Failed to process image');
            }
        } catch (error) {
            addChatMessage('system', 'Error: Failed to analyze workflow diagram');
            // Error already handled by user-facing message
        } finally {
            setIsProcessing(false);
            setUploadedImage(null);
        }
    }, [uploadedImage, setNodes, setEdges, addChatMessage]);

    // Generate APIs from workflow
    const generateAPIs = useCallback(async () => {
        console.log('Generate APIs clicked!', { nodeCount: nodes.length });

        if (nodes.length === 0) {
            alert('Create some workflow nodes first!');
            return;
        }

        setIsGeneratingAPIs(true);
        console.log('Starting API generation...');

        try {
            // Show immediate loading feedback
            console.log('Calling generateAPICode...');

            const result = await generateAPICode(nodes, edges);
            console.log('API generation completed:', result);

            setGeneratedAPIs(result);

            // Show only dashboard - no code viewing
            setShowDashboard(true);

            console.log('Dashboard should now be visible');

        } catch (error) {
            console.error('API generation failed:', error);
            alert('Failed to generate APIs: ' + error);
        } finally {
            setIsGeneratingAPIs(false);
        }
    }, [nodes, edges]);

    // Export generated code
    const exportCode = useCallback(() => {
        console.log('Export code clicked!', { hasGeneratedAPIs: !!generatedAPIs });

        if (!generatedAPIs) {
            alert('No generated code to export. Generate APIs first.');
            return;
        }

        try {
            const exportData = {
                project_info: {
                    name: "Nodex Generated Workflow",
                    created_at: new Date().toISOString(),
                    total_services: generatedAPIs.apis.length + 1, // +1 for orchestrator
                    total_lines: generatedAPIs.totalLines,
                    generation_time: generatedAPIs.executionTime
                },
                apis: generatedAPIs.apis.map((api: any) => ({
                    service_name: api.nodeName,
                    endpoint: api.endpoint,
                    method: api.method,
                    language: api.language,
                    code: api.code,
                    lines_of_code: api.code.split('\n').length
                })),
                orchestrator: {
                    service_name: "WorkflowOrchestrator",
                    code: generatedAPIs.orchestrator,
                    lines_of_code: generatedAPIs.orchestrator.split('\n').length
                },
                deployment: {
                    dockerfile: generatedAPIs.dockerfile,
                    docker_compose: generatedAPIs.deployment,
                    kubernetes_manifests: "Generated K8s manifests included"
                },
                readme: `# Nodex Generated Workflow Project

## Overview
This project contains ${generatedAPIs.apis.length} microservices generated from your visual workflow.

## API Endpoints
${generatedAPIs.apis.map((api: any, i: number) => `- ${api.nodeName}: ${api.method} ${api.endpoint}`).join('\n')}
- Orchestrator: POST /workflow/execute

## Quick Start
\`\`\`bash
# Local development
docker-compose up -d

# Cloud deployment
kubectl apply -f k8s/
\`\`\`

Generated with Nodex - Visual Workflows to Production APIs
`
            };

            setExportedJson(JSON.stringify(exportData, null, 2));
            setShowExportModal(true);
            console.log('Export modal should now be visible');

        } catch (error) {
            console.error('Export failed:', error);
            alert('Failed to export code: ' + error);
        }
    }, [generatedAPIs]);

    // Execute workflow
    const executeWorkflow = useCallback(() => {
        // Simulate execution
        setNodes(nds => nds.map(node => ({
            ...node,
            data: { ...node.data, executed: true }
        })));
        addChatMessage('assistant', 'Workflow executed successfully!');
    }, [setNodes, addChatMessage]);

    // Clear canvas
    const clearCanvas = useCallback(() => {
        setNodes([]);
        setEdges([]);

        // Clear position tracking when canvas is cleared
        allPositions.current = [];
        pendingPositions.current = [];

        localStorage.removeItem('nodex-workflow');
        addChatMessage('system', 'Canvas cleared');
    }, [setNodes, setEdges, addChatMessage]);

    // Validate workflow
    const validateWorkflow = useCallback(() => {
        const issues = [];

        // Check for disconnected nodes
        const connectedNodeIds = new Set();
        edges.forEach(edge => {
            connectedNodeIds.add(edge.source);
            connectedNodeIds.add(edge.target);
        });

        const disconnectedNodes = nodes.filter(node => !connectedNodeIds.has(node.id) && nodes.length > 1);
        if (disconnectedNodes.length > 0) {
            issues.push(`${disconnectedNodes.length} disconnected nodes found`);
        }

        // Check for missing compliance nodes in healthcare/finance workflows
        const complianceNodes = nodes.filter(n => n.data.locked);
        if (nodes.length > 0 && complianceNodes.length === 0) {
            issues.push('No compliance nodes detected - consider adding validation or audit steps');
        }

        // Check for workflows without start/end points
        if (nodes.length > 0) {
            const startNodes = nodes.filter(n => n.data.nodeType === 'trigger' || n.data.nodeType === 'manual');
            const endNodes = nodes.filter(n => n.data.nodeType === 'notification' || n.data.nodeType === 'database');

            if (startNodes.length === 0) {
                issues.push('No trigger/start node found');
            }
            if (endNodes.length === 0) {
                issues.push('No end/output node found');
            }
        }

        if (issues.length === 0) {
            addChatMessage('system', '✅ Workflow validation passed - no issues found');
        } else {
            addChatMessage('system', `⚠️ Validation issues: ${issues.join(', ')}`);
        }
    }, [nodes, edges, addChatMessage]);

    // Find a free position for a new node (avoiding overlaps)
    const findFreePosition = useCallback((preferredX?: number, preferredY?: number) => {
        const nodeWidth = 150;  // Node width
        const nodeHeight = 80;  // Node height
        const minSpacing = 10;  // Minimum 10px between nodes (as requested)

        // Check if a position is free (no overlaps with at least 10px spacing)
        const isPositionFree = (testX: number, testY: number) => {
            // Combine all existing positions (from state) and pending positions
            const allPositionsToCheck = [...allPositions.current, ...pendingPositions.current];
            console.log(`Testing position (${testX}, ${testY}) against ${allPositionsToCheck.length} positions`);

            const hasOverlap = allPositionsToCheck.some(pos => {
                const ex = pos.x;
                const ey = pos.y;

                // Calculate edge-to-edge distances
                const rightEdgeNew = testX + nodeWidth;
                const bottomEdgeNew = testY + nodeHeight;
                const rightEdgeExisting = ex + nodeWidth;
                const bottomEdgeExisting = ey + nodeHeight;

                // Check if rectangles overlap or are too close (less than minSpacing)
                const horizontalOverlap = !(rightEdgeNew + minSpacing <= ex || testX >= rightEdgeExisting + minSpacing);
                const verticalOverlap = !(bottomEdgeNew + minSpacing <= ey || testY >= bottomEdgeExisting + minSpacing);

                const overlaps = horizontalOverlap && verticalOverlap;
                if (overlaps) {
                    console.log(`Position (${testX}, ${testY}) overlaps with existing at (${ex}, ${ey})`);
                }

                return overlaps;
            });

            console.log(`Position (${testX}, ${testY}) is ${hasOverlap ? 'BLOCKED' : 'FREE'}`);
            return !hasOverlap;
        };

        // Start with preferred position or default
        let x = preferredX ?? 100;
        let y = preferredY ?? 100;

        // Try preferred position first
        if (isPositionFree(x, y)) {
            return { x, y };
        }

        // Grid-based search for free position
        const gridSpacing = nodeWidth + minSpacing + 20; // Extra spacing for clean layout
        const startX = 50;
        const startY = 50;

        // Search in expanding grid pattern
        for (let row = 0; row < 10; row++) {
            for (let col = 0; col < 8; col++) {
                x = startX + (col * gridSpacing);
                y = startY + (row * (nodeHeight + minSpacing + 20));

                if (isPositionFree(x, y)) {
                    return { x, y };
                }
            }
        }

        // Final fallback: find any free space by spiral search
        const spiralRadius = 50;
        for (let radius = spiralRadius; radius <= 400; radius += spiralRadius) {
            for (let angle = 0; angle < 360; angle += 45) {
                x = (preferredX ?? 300) + radius * Math.cos(angle * Math.PI / 180);
                y = (preferredY ?? 200) + radius * Math.sin(angle * Math.PI / 180);

                // Ensure position is not negative
                x = Math.max(50, x);
                y = Math.max(50, y);

                if (isPositionFree(x, y)) {
                    return { x, y };
                }
            }
        }

        // Absolute fallback
        return {
            x: Math.max(50, (preferredX ?? 100) + Math.random() * 200),
            y: Math.max(50, (preferredY ?? 100) + Math.random() * 200)
        };
    }, [nodes]);

    // Smart positioning for AI-generated nodes
    const arrangeNodesIntelligently = useCallback((newNodes: any[]) => {
        const nodeWidth = 150;
        const nodeHeight = 80;
        const minSpacing = 10;  // Minimum spacing as requested
        const sectionSpacing = 40; // Extra space between workflow sections

        // Organize by node types for better workflow readability
        const triggers = newNodes.filter(n => n.data.nodeType === 'trigger' || n.data.nodeType === 'manual');
        const actions = newNodes.filter(n => n.data.nodeType === 'action' || n.data.nodeType === 'condition');
        const outputs = newNodes.filter(n => n.data.nodeType === 'database' || n.data.nodeType === 'notification');
        const compliance = newNodes.filter(n => n.data.locked);
        const others = newNodes.filter(n =>
            !triggers.includes(n) && !actions.includes(n) && !outputs.includes(n) && !compliance.includes(n)
        );

        let currentY = 50; // Start position
        const baseX = 50;
        const horizontalSpacing = nodeWidth + minSpacing + 20; // Ensure good spacing
        const verticalSpacing = nodeHeight + minSpacing + 20;

        // Position triggers at the top
        triggers.forEach((node, index) => {
            node.position = {
                x: baseX + (index * horizontalSpacing),
                y: currentY
            };
        });

        if (triggers.length > 0) currentY += verticalSpacing + sectionSpacing;

        // Position actions in the middle (max 4 per row for better readability)
        const actionsPerRow = Math.min(4, Math.max(2, Math.ceil(Math.sqrt(actions.length))));
        actions.forEach((node, index) => {
            const row = Math.floor(index / actionsPerRow);
            const col = index % actionsPerRow;
            node.position = {
                x: baseX + (col * horizontalSpacing),
                y: currentY + (row * verticalSpacing)
            };
        });

        if (actions.length > 0) {
            const rows = Math.ceil(actions.length / actionsPerRow);
            currentY += (rows * verticalSpacing) + sectionSpacing;
        }

        // Position other nodes (validation, email, etc.)
        const othersPerRow = Math.min(3, Math.max(2, Math.ceil(Math.sqrt(others.length))));
        others.forEach((node, index) => {
            const row = Math.floor(index / othersPerRow);
            const col = index % othersPerRow;
            node.position = {
                x: baseX + (col * horizontalSpacing),
                y: currentY + (row * verticalSpacing)
            };
        });

        if (others.length > 0) {
            const rows = Math.ceil(others.length / othersPerRow);
            currentY += (rows * verticalSpacing) + sectionSpacing;
        }

        // Position outputs at the bottom
        outputs.forEach((node, index) => {
            node.position = {
                x: baseX + (index * horizontalSpacing),
                y: currentY
            };
        });

        // Position compliance nodes on the right side, but ensure no overlaps
        const complianceStartX = baseX + (Math.max(actionsPerRow, othersPerRow, outputs.length) * horizontalSpacing) + sectionSpacing;
        compliance.forEach((node, index) => {
            node.position = {
                x: complianceStartX,
                y: 50 + (index * verticalSpacing)
            };
        });

        return newNodes;
    }, []);

    // Add prebuilt node
    const addPrebuiltNode = useCallback((nodeType: string, label: string, icon: string) => {
        console.log('Adding prebuilt node:', label);
        console.log('Current nodes count:', nodes.length);
        console.log('Current allPositions:', allPositions.current.length);

        const position = findFreePosition();
        console.log('Found position:', position);

        const newNode = {
            id: `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            type: 'n8nNode',
            position,
            data: {
                label,
                nodeType: nodeType as any,
                icon,
                description: `${label} - Prebuilt node`,
                locked: false
            }
        };

        console.log('Creating node with id:', newNode.id);

        setNodes(nds => {
            console.log('setNodes called, current length:', nds.length);
            const updated = [...nds, newNode];
            console.log('New nodes array length:', updated.length);

            // Immediately update allPositions to prevent further conflicts
            allPositions.current = updated.map(node => node.position);

            return updated;
        });

        addChatMessage('system', `Added ${label} node to canvas`);
    }, [findFreePosition, setNodes, addChatMessage, nodes.length]);

    // Auto-fix workflow issues
    const autoFixWorkflow = useCallback(() => {
        let newNodes = [...nodes];
        let newEdges = [...edges];
        let changes = [];

        // Add a trigger node if missing
        const hasStartNode = newNodes.some(n => n.data.nodeType === 'trigger' || n.data.nodeType === 'manual');
        if (newNodes.length > 0 && !hasStartNode) {
            const position = findFreePosition(50, 100);
            const triggerNode = {
                id: `trigger_${Date.now()}`,
                type: 'n8nNode',
                position,
                data: {
                    label: 'Start Trigger',
                    nodeType: 'trigger' as any,
                    icon: '⚡',
                    description: 'Workflow trigger - auto-added',
                    locked: false
                }
            };
            newNodes.unshift(triggerNode);
            changes.push('Added trigger node');
        }

        // Add validation node for compliance
        const hasValidation = newNodes.some(n => n.data.nodeType === 'validation');
        if (newNodes.length > 1 && !hasValidation) {
            const position = findFreePosition();
            const validationNode = {
                id: `validation_${Date.now()}`,
                type: 'n8nNode',
                position,
                data: {
                    label: 'Validation Check',
                    nodeType: 'validation' as any,
                    icon: '✅',
                    description: 'Data validation - auto-added',
                    locked: true,
                    compliance_reason: 'Added for workflow compliance'
                }
            };
            newNodes.push(validationNode);
            changes.push('Added validation node');
        }

        if (changes.length > 0) {
            setNodes(newNodes);
            setEdges(newEdges);
            addChatMessage('system', `Auto-fix applied: ${changes.join(', ')}`);
        } else {
            addChatMessage('system', 'No auto-fixes needed');
        }
    }, [nodes, edges, setNodes, setEdges, addChatMessage]);

    // Auto-arrange existing nodes to fix overlaps
    const autoArrangeNodes = useCallback(() => {
        if (nodes.length === 0) {
            addChatMessage('system', 'No nodes to arrange');
            return;
        }

        const arrangedNodes = arrangeNodesIntelligently([...nodes]);
        setNodes(arrangedNodes);
        addChatMessage('system', `Arranged ${nodes.length} nodes to prevent overlaps`);
    }, [nodes, arrangeNodesIntelligently, setNodes, addChatMessage]);

    // Handle node selection changes
    const onSelectionChange = useCallback((params: any) => {
        setSelectedNodes(params.nodes.map((node: any) => node.id));
    }, []);

    // Handle node double-click for editing
    const onNodeDoubleClick = useCallback((event: React.MouseEvent, node: Node) => {
        event.preventDefault();
        event.stopPropagation();

        // Find the node in current state to ensure we have the latest version
        const currentNode = nodes.find(n => n.id === node.id);
        if (currentNode) {
            setEditingNode(currentNode as Node<N8nNodeData>);
            setShowEditModal(true);
        }
    }, [nodes]);

    // Save edited node
    const saveEditedNode = useCallback((updatedData: { label: string; description: string }) => {
        if (!editingNode) return;

        // Direct update using setNodes - this is the correct ReactFlow pattern
        setNodes(currentNodes =>
            currentNodes.map(node =>
                node.id === editingNode.id
                    ? {
                        ...node,
                        data: {
                            ...node.data,
                            label: updatedData.label,
                            description: updatedData.description
                        }
                    }
                    : node
            )
        );

        setShowEditModal(false);
        setEditingNode(null);
        addChatMessage('system', `Updated node: ${updatedData.label}`);
    }, [editingNode, setNodes, addChatMessage]);

    // Cancel node editing
    const cancelNodeEdit = useCallback(() => {
        setShowEditModal(false);
        setEditingNode(null);
    }, []);

    // Delete selected nodes
    const deleteSelectedNodes = useCallback(() => {
        if (selectedNodes.length === 0) {
            addChatMessage('system', 'No nodes selected for deletion');
            return;
        }

        // Check if trying to delete locked compliance nodes
        const selectedNodeData = nodes.filter(n => selectedNodes.includes(n.id));
        const lockedNodes = selectedNodeData.filter(n => n.data.locked);

        if (lockedNodes.length > 0) {
            addChatMessage('system', `⚠️ Cannot delete ${lockedNodes.length} compliance node(s) - they are locked`);
            return;
        }

        // Remove nodes and connected edges
        const newNodes = nodes.filter(n => !selectedNodes.includes(n.id));
        const newEdges = edges.filter(e =>
            !selectedNodes.includes(e.source) && !selectedNodes.includes(e.target)
        );

        setNodes(newNodes);
        setEdges(newEdges);
        setSelectedNodes([]);

        addChatMessage('system', `Deleted ${selectedNodes.length} node(s) and connected edges`);
    }, [selectedNodes, nodes, edges, setNodes, setEdges, addChatMessage]);

    // Handle keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            // Delete key or Backspace
            if ((event.key === 'Delete' || event.key === 'Backspace') && selectedNodes.length > 0) {
                event.preventDefault();
                deleteSelectedNodes();
            }
        };

        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [selectedNodes, deleteSelectedNodes]);

    // Load template workflow
    const loadTemplate = useCallback((template: WorkflowTemplate) => {
        // Create nodes with unique IDs based on timestamp
        const timestamp = Date.now();
        const templateNodes = template.nodes.map((node, index) => ({
            ...node,
            id: `${node.id}_${timestamp}_${index}`,
            data: { ...node.data }
        }));

        // Create edges with updated node IDs
        const templateEdges = template.edges.map((edge, index) => ({
            ...edge,
            id: `${edge.id}_${timestamp}_${index}`,
            source: `${edge.source}_${timestamp}_${template.nodes.findIndex(n => n.id === edge.source)}`,
            target: `${edge.target}_${timestamp}_${template.nodes.findIndex(n => n.id === edge.target)}`
        }));

        // Clear existing workflow and load template
        setNodes(templateNodes);
        setEdges(templateEdges);

        // Immediately update allPositions to prevent collision detection issues
        allPositions.current = templateNodes.map(node => node.position);

        // Clear any pending positions to avoid conflicts
        pendingPositions.current = [];

        setShowTemplateModal(false);
        addChatMessage('system', `Loaded ${template.name} template with ${templateNodes.length} nodes`);
    }, [setNodes, setEdges, addChatMessage]);

    // Copy prompt to input and close modal
    const copyPromptToInput = useCallback((prompt: string) => {
        setTextInput(prompt);
        setShowPromptLibrary(false);
        addChatMessage('system', 'Prompt copied to input. Click "Generate Workflow" to see it in action!');
    }, [addChatMessage]);

    return (
        <ReactFlowProvider>
            <div className="app">
                {/* Header */}
                <header className="header">
                    <div className="header-content">
                        <div className="brand">
                            <div className="brand-title">🚀 Nodex</div>
                            <div className="brand-subtitle">AI-Powered Workflow Intelligence</div>
                        </div>
                        <div className="flex gap-3">
                            <button
                                className="btn btn-secondary"
                                onClick={() => setShowTemplateModal(true)}
                            >
                                📋 Templates
                            </button>
                            <button
                                className="btn btn-secondary"
                                onClick={() => setShowPromptLibrary(true)}
                            >
                                💡 Prompt Library
                            </button>
                            { /* <button
                                onClick={executeWorkflow}
                                className="btn btn-green"
                            >
                                ▶️ Execute
                            </button> */ }
                            <button
                                onClick={generateAPIs}
                                className="btn btn-blue"
                                disabled={isGeneratingAPIs}
                                title="AI generates production-ready APIs from your workflow"
                            >
                                {isGeneratingAPIs ? '🤖 Generating APIs...' : '🤖 Generate APIs'}
                            </button>

                            {/* Quick Demo Button */}
                            {nodes.length === 0 && (
                                <button
                                    onClick={() => {
                                        // Quick demo with mock nodes
                                        const mockNodes = [
                                            {
                                                id: '1',
                                                type: 'n8nNode',
                                                position: { x: 100, y: 100 },
                                                data: { label: 'Webhook Trigger', nodeType: 'trigger', description: 'Receives incoming requests' }
                                            },
                                            {
                                                id: '2',
                                                type: 'n8nNode',
                                                position: { x: 300, y: 100 },
                                                data: { label: 'Data Processing', nodeType: 'action', description: 'Processes incoming data' }
                                            },
                                            {
                                                id: '3',
                                                type: 'n8nNode',
                                                position: { x: 500, y: 100 },
                                                data: { label: 'Send Notification', nodeType: 'notification', description: 'Sends email notification' }
                                            }
                                        ];
                                        const mockEdges = [
                                            { id: 'e1-2', source: '1', target: '2' },
                                            { id: 'e2-3', source: '2', target: '3' }
                                        ];
                                        setNodes(mockNodes);
                                        setEdges(mockEdges);
                                    }}
                                    className="btn btn-green"
                                    title="Quick demo with sample workflow"
                                >
                                    ⚡ Quick Demo
                                </button>
                            )}
                            {generatedAPIs && (
                                <button
                                    onClick={() => setShowDashboard(true)}
                                    className="btn btn-green"
                                    title="View project dashboard with endpoints"
                                >
                                    📊 View Project Dashboard
                                </button>
                            )}
                        </div>
                    </div>
                </header>

                <main className="main-layout">
                    {/* Left Panel - Input & Tools */}
                    <div className="left-panel">
                        <div className="panel-header">Input & Configuration</div>
                        <div className="panel-content">
                            {/* Text Input Section */}
                            <div className="input-section">
                                <label className="input-label">Describe your workflow:</label>
                                <textarea
                                    className="textarea"
                                    value={textInput}
                                    onChange={(e) => setTextInput(e.target.value)}
                                    placeholder="e.g., Employee onboarding: collect documents, validate identity, create HRIS record..."
                                    rows={4}
                                />
                                <button
                                    onClick={processTextWorkflow}
                                    disabled={!textInput.trim() || isProcessing}
                                    className="btn btn-green btn-full mt-3"
                                >
                                    {isProcessing ? 'Processing...' : '🚀 Generate Workflow'}
                                </button>
                            </div>

                            {/* File Upload Section */}
                            <div className="input-section">
                                <label className="input-label">Or upload diagram:</label>
                                <div
                                    className="file-upload"
                                    onClick={() => alert('⚠️ We cannot process images right now due to limited compute. Please use the visual builder instead.')}
                                >
                                    <div className="file-upload-text">
                                        📁 Click to upload diagram
                                    </div>
                                </div>
                                {uploadedImage && (
                                    <div className="mt-3">
                                        <img
                                            src={uploadedImage}
                                            alt="Uploaded workflow"
                                            style={{ width: '100%', maxHeight: '200px', objectFit: 'contain', borderRadius: 'var(--radius)' }}
                                        />
                                        <button
                                            onClick={processImageWorkflow}
                                            disabled={isProcessing}
                                            className="btn btn-blue btn-full mt-3"
                                        >
                                            {isProcessing ? 'Analyzing...' : '🔍 Analyze Diagram'}
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Center - Workflow Canvas */}
                    <div className="canvas-area" ref={reactFlowWrapper}>
                        <ReactFlow
                            nodes={nodes}
                            edges={edges}
                            onNodesChange={onNodesChange}
                            onEdgesChange={onEdgesChange}
                            onConnect={onConnect}
                            onSelectionChange={onSelectionChange}
                            onNodeDoubleClick={onNodeDoubleClick}
                            onInit={setReactFlowInstance}
                            onDrop={onDrop}
                            onDragOver={onDragOver}
                            nodeTypes={nodeTypes}
                            fitView
                        >
                            <Background color="#f8f9fa" gap={20} />
                            <Controls />
                            <MiniMap
                                nodeColor={(node) => {
                                    const data = node.data as N8nNodeData;
                                    return data.locked ? '#eab308' : '#6b7280';
                                }}
                            />
                        </ReactFlow>

                        {/* Canvas Instructions */}
                        {nodes.length > 0 && (
                            <div style={{
                                position: 'absolute',
                                bottom: '16px',
                                right: '16px',
                                background: 'rgba(0, 0, 0, 0.7)',
                                color: 'var(--gray-300)',
                                padding: '8px 12px',
                                borderRadius: 'var(--radius)',
                                fontSize: '12px',
                                backdropFilter: 'blur(4px)',
                                border: '1px solid var(--gray-700)'
                            }}>
                                💡 Double-click nodes to edit • Click to select • Drag to move
                            </div>
                        )}

                        {/* Processing Overlay */}
                        {isProcessing && (
                            <div className="processing-overlay">
                                <div className="processing-content">
                                    <div className="spinner"></div>
                                    <div className="processing-title">Processing Workflow</div>
                                    {/* <div className="processing-message">{getCurrentProcessingMessage()}</div> */}
                                    <div className="processing-message">Sit back and relax while we cook...</div>

                                </div>
                            </div>
                        )}
                    </div>

                    {/* Right Panel - Tools & Results */}
                    <div className="right-panel">
                        <div className="panel-header">Tools & Components</div>
                        <div className="panel-content">
                            {/* Prebuilt Nodes */}
                            <div className="tools-section">
                                <h4 className="mb-3">📦 Node Library</h4>
                                <div className="node-grid">
                                    <button
                                        className="node-button trigger"
                                        onClick={() => addPrebuiltNode('trigger', 'Start Trigger', '⚡')}
                                        title="Add trigger node"
                                    >
                                        ⚡ Trigger
                                    </button>
                                    <button
                                        className="node-button action"
                                        onClick={() => addPrebuiltNode('action', 'Process Data', '⚙️')}
                                        title="Add action node"
                                    >
                                        ⚙️ Action
                                    </button>
                                    <button
                                        className="node-button condition"
                                        onClick={() => addPrebuiltNode('condition', 'Decision Point', '❓')}
                                        title="Add condition node"
                                    >
                                        ❓ Decision
                                    </button>
                                    <button
                                        className="node-button validation"
                                        onClick={() => addPrebuiltNode('validation', 'Validate', '✅')}
                                        title="Add validation node"
                                    >
                                        ✅ Validate
                                    </button>
                                    <button
                                        className="node-button database"
                                        onClick={() => addPrebuiltNode('database', 'Save Data', '💾')}
                                        title="Add database node"
                                    >
                                        💾 Database
                                    </button>
                                    <button
                                        className="node-button email"
                                        onClick={() => addPrebuiltNode('email', 'Send Email', '📧')}
                                        title="Add email node"
                                    >
                                        📧 Email
                                    </button>
                                    <button
                                        className="node-button notification"
                                        onClick={() => addPrebuiltNode('notification', 'Notify', '🔔')}
                                        title="Add notification node"
                                    >
                                        🔔 Notify
                                    </button>
                                    <button
                                        className="node-button audit"
                                        onClick={() => addPrebuiltNode('audit', 'Audit Log', '📋')}
                                        title="Add audit node"
                                    >
                                        📋 Audit
                                    </button>
                                </div>
                            </div>

                            {/* Workflow Tools */}
                            <div className="tools-section">
                                <h4 className="mb-3">🔧 Workflow Tools</h4>
                                <button
                                    className="btn btn-purple btn-full mb-2"
                                    onClick={validateWorkflow}
                                >
                                    🔍 Validate Workflow
                                </button>
                                <button
                                    className="btn btn-orange btn-full mb-2"
                                    onClick={autoFixWorkflow}
                                >
                                    🛠️ Auto-Fix Issues
                                </button>
                                <button
                                    className="btn btn-blue btn-full mb-2"
                                    onClick={autoArrangeNodes}
                                >
                                    📐 Arrange Nodes
                                </button>
                                <button
                                    className="btn btn-red btn-full mb-2"
                                    onClick={clearCanvas}
                                >
                                    🧹 Clear Canvas
                                </button>
                                {localStorage.getItem('nodex-workflow') && (
                                    <div style={{
                                        fontSize: '12px',
                                        color: 'var(--green)',
                                        textAlign: 'center',
                                        padding: '8px',
                                        background: 'rgba(34, 197, 94, 0.1)',
                                        border: '1px solid rgba(34, 197, 94, 0.3)',
                                        borderRadius: 'var(--radius)',
                                        marginBottom: '8px'
                                    }}>
                                        💾 Workflow auto-saved
                                    </div>
                                )}
                                {selectedNodes.length === 1 && (
                                    <button
                                        className="btn btn-purple btn-full mb-2"
                                        onClick={() => {
                                            const nodeToEdit = nodes.find(n => n.id === selectedNodes[0]);
                                            if (nodeToEdit) {
                                                setEditingNode(nodeToEdit);
                                                setShowEditModal(true);
                                            }
                                        }}
                                        title="Edit selected node"
                                    >
                                        ✏️ Edit Node
                                    </button>
                                )}
                                {selectedNodes.length > 0 && (
                                    <button
                                        className="btn btn-red btn-full mb-2"
                                        onClick={deleteSelectedNodes}
                                        title={`Delete ${selectedNodes.length} selected node(s)`}
                                    >
                                        🗑️ Delete Selected ({selectedNodes.length})
                                    </button>
                                )}
                            </div>

                            {/* Domain Detection */}
                            {detectedDomain && (
                                <div className="tools-section">
                                    <h4 className="mb-3">🎯 Domain Info</h4>
                                    <div className="tool-item">
                                        <div className={`domain-badge ${detectedDomain}`}>
                                            {detectedDomain === 'healthcare' && '🏥 Healthcare'}
                                            {detectedDomain === 'finance' && '🏦 Finance'}
                                            {detectedDomain === 'creator' && '🎨 Creator'}
                                        </div>
                                        <div style={{ fontSize: '12px', color: 'var(--gray-400)' }}>
                                            AI-detected domain
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Workflow Stats */}
                            {nodes.length > 0 && (
                                <div className="tools-section">
                                    <h4 className="mb-3">📊 Statistics</h4>
                                    <div className="stats-grid">
                                        <div className="stat-item">
                                            <div className="stat-number">{nodes.length}</div>
                                            <div className="stat-label">Nodes</div>
                                        </div>
                                        <div className="stat-item">
                                            <div className="stat-number">{edges.length}</div>
                                            <div className="stat-label">Connections</div>
                                        </div>
                                        <div className="stat-item">
                                            <div className="stat-number">{nodes.filter(n => n.data.locked).length}</div>
                                            <div className="stat-label">Compliance</div>
                                        </div>
                                        <div className="stat-item">
                                            <div className="stat-number">{nodes.filter(n => n.data.executed).length}</div>
                                            <div className="stat-label">Executed</div>
                                        </div>
                                        {selectedNodes.length > 0 && (
                                            <div className="stat-item selected">
                                                <div className="stat-number">{selectedNodes.length}</div>
                                                <div className="stat-label">Selected</div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </main>

                {/* Template Selection Modal */}
                {showTemplateModal && (
                    <div className="processing-overlay">
                        <div className="processing-content" style={{ maxWidth: '900px', width: '90%', maxHeight: '80vh', overflow: 'auto' }}>
                            <div className="flex items-center justify-between mb-4">
                                <h2>📋 Workflow Templates</h2>
                                <button
                                    onClick={() => setShowTemplateModal(false)}
                                    className="btn btn-secondary"
                                    style={{ padding: '8px 12px' }}
                                >
                                    ×
                                </button>
                            </div>
                            <p style={{ color: 'var(--gray-400)', marginBottom: '24px' }}>
                                Choose from pre-built workflow templates to get started quickly
                            </p>
                            <div style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                                gap: '16px'
                            }}>
                                {workflowTemplates.map(template => (
                                    <div
                                        key={template.id}
                                        onClick={() => loadTemplate(template)}
                                        style={{
                                            background: 'var(--gray-700)',
                                            border: '1px solid var(--gray-600)',
                                            borderRadius: 'var(--radius)',
                                            padding: '16px',
                                            cursor: 'pointer',
                                            transition: 'all 0.2s ease'
                                        }}
                                        className="template-card"
                                    >
                                        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
                                            <span style={{ fontSize: '24px', marginRight: '12px' }}>
                                                {template.icon}
                                            </span>
                                            <div>
                                                <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '600' }}>
                                                    {template.name}
                                                </h3>
                                                <div style={{
                                                    fontSize: '12px',
                                                    color: 'var(--gray-400)',
                                                    background: 'var(--gray-800)',
                                                    padding: '2px 8px',
                                                    borderRadius: '4px',
                                                    display: 'inline-block',
                                                    marginTop: '4px'
                                                }}>
                                                    {template.category}
                                                </div>
                                            </div>
                                        </div>
                                        <p style={{
                                            fontSize: '14px',
                                            color: 'var(--gray-300)',
                                            lineHeight: '1.4',
                                            margin: '0 0 12px 0'
                                        }}>
                                            {template.description}
                                        </p>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <div style={{ fontSize: '12px', color: 'var(--gray-400)' }}>
                                                {template.nodes.length} nodes • {template.edges.length} connections
                                            </div>
                                            <div style={{
                                                color: 'var(--blue)',
                                                fontSize: '12px',
                                                fontWeight: '500'
                                            }}>
                                                Load Template →
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Prompt Library Modal */}
                {showPromptLibrary && (
                    <div className="processing-overlay" style={{ background: 'rgba(0, 0, 0, 0.9)' }}>
                        <div className="processing-content" style={{ 
                            maxWidth: '800px', 
                            width: '90%', 
                            maxHeight: '80vh', 
                            overflow: 'auto',
                            background: '#000',
                            color: '#fff',
                            border: '1px solid #333'
                        }}>
                            <div className="flex items-center justify-between mb-4">
                                <h2 style={{ color: '#fff' }}>💡 Prompt Library</h2>
                                <button
                                    onClick={() => setShowPromptLibrary(false)}
                                    className="btn btn-secondary"
                                    style={{ padding: '8px 12px', background: '#333', color: '#fff' }}
                                >
                                    ×
                                </button>
                            </div>
                            <p style={{ color: '#ccc', marginBottom: '24px' }}>
                                Copy and paste any of these prompts to see workflows generated automatically
                            </p>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                {promptLibrary.map((prompt, index) => (
                                    <div
                                        key={index}
                                        onClick={() => copyPromptToInput(prompt)}
                                        style={{
                                            background: '#111',
                                            border: '1px solid #333',
                                            borderRadius: '8px',
                                            padding: '16px',
                                            cursor: 'pointer',
                                            transition: 'all 0.2s ease',
                                            color: '#fff'
                                        }}
                                        onMouseEnter={(e) => {
                                            e.currentTarget.style.background = '#222';
                                            e.currentTarget.style.borderColor = '#555';
                                        }}
                                        onMouseLeave={(e) => {
                                            e.currentTarget.style.background = '#111';
                                            e.currentTarget.style.borderColor = '#333';
                                        }}
                                    >
                                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                                            <span style={{ 
                                                fontSize: '20px', 
                                                flexShrink: 0,
                                                marginTop: '2px'
                                            }}>
                                                📋
                                            </span>
                                            <div style={{ flex: 1 }}>
                                                <p style={{ 
                                                    margin: 0, 
                                                    lineHeight: '1.5',
                                                    fontSize: '14px'
                                                }}>
                                                    {prompt}
                                                </p>
                                                <div style={{ 
                                                    marginTop: '8px', 
                                                    fontSize: '12px', 
                                                    color: '#888',
                                                    fontStyle: 'italic'
                                                }}>
                                                    Click to copy to input
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Node Edit Modal */}
                {showEditModal && editingNode && (
                    <div className="processing-overlay">
                        <div className="processing-content" style={{ maxWidth: '500px', width: '90%' }}>
                            <div className="flex items-center justify-between mb-4">
                                <h2>✏️ Edit Node</h2>
                                <button
                                    onClick={cancelNodeEdit}
                                    className="btn btn-secondary"
                                    style={{ padding: '8px 12px' }}
                                >
                                    ×
                                </button>
                            </div>

                            <NodeEditForm
                                node={editingNode}
                                onSave={saveEditedNode}
                                onCancel={cancelNodeEdit}
                            />
                        </div>
                    </div>
                )}

                {/* Project Dashboard */}
                {showDashboard && generatedAPIs && (
                    <div className="processing-overlay">
                        <div className="processing-content" style={{ maxWidth: '1400px', width: '95%', maxHeight: '90vh', overflow: 'auto' }}>
                            <div className="flex items-center justify-between mb-6">
                                <h1 className="text-2xl font-bold">🚀 Nodex Project Dashboard</h1>
                                <button
                                    onClick={() => setShowDashboard(false)}
                                    className="btn btn-secondary"
                                    style={{ padding: '8px 12px' }}
                                >
                                    ×
                                </button>
                            </div>

                            {/* Project Overview */}
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                    <div className="text-2xl font-bold text-blue-600">{generatedAPIs.apis.length}</div>
                                    <div className="text-sm text-blue-800">Microservices</div>
                                </div>
                                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                                    <div className="text-2xl font-bold text-green-600">{generatedAPIs.totalLines}</div>
                                    <div className="text-sm text-green-800">Lines of Code</div>
                                </div>
                                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                                    <div className="text-2xl font-bold text-purple-600">{generatedAPIs.executionTime.toFixed(1)}s</div>
                                    <div className="text-sm text-purple-800">Generation Time</div>
                                </div>
                                <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                                    <div className="text-2xl font-bold text-orange-600">100%</div>
                                    <div className="text-sm text-orange-800">Production Ready</div>
                                </div>
                            </div>

                            {/* API Endpoints Table */}
                            <div className="bg-white border rounded-lg mb-6">
                                <div className="p-4 border-b bg-gray-50">
                                    <h2 className="text-lg font-semibold">🌐 API Endpoints</h2>
                                </div>
                                <div className="overflow-x-auto">
                                    <table className="w-full">
                                        <thead className="bg-gray-50">
                                            <tr>
                                                <th className="text-left p-3 font-medium">Service</th>
                                                <th className="text-left p-3 font-medium">Method</th>
                                                <th className="text-left p-3 font-medium">Endpoint</th>
                                                <th className="text-left p-3 font-medium">Status</th>
                                                <th className="text-left p-3 font-medium">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {generatedAPIs.apis.map((api: any, index: number) => (
                                                <tr key={api.nodeId} className="border-b hover:bg-gray-50">
                                                    <td className="p-3">
                                                        <div className="font-medium">{api.nodeName}</div>
                                                        <div className="text-sm text-gray-500">
                                                            Port: 800{index + 1}
                                                        </div>
                                                    </td>
                                                    <td className="p-3">
                                                        <span className={`px-2 py-1 rounded text-xs font-medium ${api.method === 'POST' ? 'bg-blue-100 text-blue-800' :
                                                            api.method === 'GET' ? 'bg-green-100 text-green-800' :
                                                                'bg-gray-100 text-gray-800'
                                                            }`}>
                                                            {api.method}
                                                        </span>
                                                    </td>
                                                    <td className="p-3">
                                                        <code className="bg-gray-100 px-2 py-1 rounded text-sm">
                                                            {api.method} {api.endpoint}
                                                        </code>
                                                    </td>
                                                    <td className="p-3">
                                                        <span className="px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                                                            ✅ Ready
                                                        </span>
                                                    </td>
                                                    <td className="p-3">
                                                        <div className="flex gap-2">
                                                            <button
                                                                onClick={() => {
                                                                    const endpointInfo = `${api.method} ${api.endpoint}`;
                                                                    navigator.clipboard.writeText(endpointInfo);
                                                                    alert('Endpoint URL copied to clipboard!');
                                                                }}
                                                                className="text-xs px-2 py-1 bg-gray-100 text-gray-800 rounded hover:bg-gray-200"
                                                            >
                                                                Copy URL
                                                            </button>
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))}
                                            {/* Orchestrator Row */}
                                            <tr className="border-b bg-blue-50">
                                                <td className="p-3">
                                                    <div className="font-medium text-blue-800">🎯 Orchestrator</div>
                                                    <div className="text-sm text-blue-600">Main coordination service</div>
                                                </td>
                                                <td className="p-3">
                                                    <span className="px-2 py-1 rounded text-xs font-medium bg-blue-200 text-blue-800">
                                                        POST
                                                    </span>
                                                </td>
                                                <td className="p-3">
                                                    <code className="bg-white px-2 py-1 rounded text-sm border">
                                                        POST /workflow/execute
                                                    </code>
                                                </td>
                                                <td className="p-3">
                                                    <span className="px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                                                        ✅ Ready
                                                    </span>
                                                </td>
                                                <td className="p-3">
                                                    <div className="flex gap-2">
                                                    </div>
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            {/* Deployment Commands */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="bg-gray-50 border rounded-lg p-4">
                                    <h3 className="font-semibold mb-3 text-gray-800">🐳 Local Development</h3>
                                    <div className="space-y-2 text-sm">
                                        <div className="bg-black text-green-400 p-3 rounded font-mono text-xs">
                                            <div>$ docker-compose up -d</div>
                                            <div className="text-gray-400"># All services will be available</div>
                                        </div>
                                        <div className="text-xs text-gray-600">
                                            Starts all {generatedAPIs.apis.length + 1} services with database and monitoring
                                        </div>
                                    </div>
                                </div>

                                <div className="bg-gray-50 border rounded-lg p-4">
                                    <h3 className="font-semibold mb-3 text-gray-800">☁️ Cloud Deployment</h3>
                                    <div className="space-y-2 text-sm">
                                        <div className="bg-black text-green-400 p-3 rounded font-mono text-xs">
                                            <div>$ kubectl apply -f k8s/</div>
                                            <div className="text-gray-400"># Deploys to Kubernetes cluster</div>
                                        </div>
                                        <div className="text-xs text-gray-600">
                                            Production-ready with auto-scaling and load balancing
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="mt-6 flex gap-4 justify-center">
                                <button
                                    onClick={exportCode}
                                    className="btn btn-green"
                                >
                                    📦 Download Project
                                </button>
                                <button
                                    onClick={() => alert('⚠️ Cloud deployment is currently unavailable due to limited space. Please download the project and deploy manually to your preferred cloud provider.')}
                                    className="btn btn-purple"
                                    style={{ backgroundColor: '#8B5CF6', color: 'white' }}
                                >
                                    🚀 Deploy to Cloud
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Generated Code View Modal */}
                {false && generatedAPIs && (
                    <div className="processing-overlay">
                        <div className="processing-content" style={{ maxWidth: '1200px', width: '95%', maxHeight: '90vh', overflow: 'auto' }}>
                            <div className="flex items-center justify-between mb-4">
                                <h2>🤖 Generated API Services</h2>
                                <button
                                    onClick={() => setShowCodeModal(false)}
                                    className="btn btn-secondary"
                                    style={{ padding: '8px 12px' }}
                                >
                                    ×
                                </button>
                            </div>

                            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                                <div className="flex items-center gap-4">
                                    <div>
                                        <strong>✅ Generated {generatedAPIs.apis.length} Microservices</strong>
                                        <div className="text-sm text-gray-600">
                                            {generatedAPIs.totalLines} lines of production-ready code in {generatedAPIs.executionTime.toFixed(1)}s
                                        </div>
                                    </div>
                                    <div className="ml-auto">
                                        <div className="text-xs text-gray-500">FastAPI • Docker • Tests • Docs</div>
                                    </div>
                                </div>
                            </div>

                            <div className="grid gap-4">
                                {/* API Services Grid */}
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    {generatedAPIs.apis.map((api: any, index: number) => (
                                        <div key={api.nodeId} className="border rounded-lg p-4 hover:shadow-lg transition-shadow">
                                            <div className="flex items-center justify-between mb-2">
                                                <h3 className="font-semibold">{api.nodeName}</h3>
                                                <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                                                    {api.method}
                                                </span>
                                            </div>
                                            <div className="text-sm text-gray-600 mb-2">
                                                {api.endpoint}
                                            </div>
                                            <div className="text-xs text-gray-500 mb-3">
                                                {api.code.split('\n').length} lines • Python FastAPI
                                            </div>
                                            <button
                                                onClick={() => setSelectedAPI(api)}
                                                className="w-full text-xs btn btn-secondary"
                                                style={{ padding: '6px 12px' }}
                                            >
                                                View Code
                                            </button>
                                        </div>
                                    ))}
                                </div>

                                {/* Orchestrator Service */}
                                <div className="border-2 border-blue-200 rounded-lg p-4 bg-blue-50">
                                    <div className="flex items-center justify-between mb-2">
                                        <h3 className="font-semibold text-blue-800">🎯 Workflow Orchestrator</h3>
                                        <span className="text-xs bg-blue-200 text-blue-800 px-2 py-1 rounded">
                                            Main Service
                                        </span>
                                    </div>
                                    <div className="text-sm text-gray-700 mb-2">
                                        Manages workflow execution and coordinates all microservices
                                    </div>
                                    <div className="text-xs text-gray-600 mb-3">
                                        {generatedAPIs.orchestrator.split('\n').length} lines • Central coordinator
                                    </div>
                                    <button
                                        onClick={() => setSelectedAPI({
                                            nodeName: 'Orchestrator',
                                            code: generatedAPIs.orchestrator,
                                            language: 'python'
                                        })}
                                        className="w-full text-xs btn btn-blue"
                                        style={{ padding: '6px 12px' }}
                                    >
                                        View Orchestrator Code
                                    </button>
                                </div>
                            </div>

                            {/* Deployment Section */}
                            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                                <h3 className="font-semibold mb-3">🚀 Ready to Deploy</h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                                    <div>
                                        <strong>Local Development:</strong>
                                        <code className="block bg-white p-2 rounded mt-1">
                                            docker-compose up
                                        </code>
                                    </div>
                                    <div>
                                        <strong>Cloud Deployment:</strong>
                                        <code className="block bg-white p-2 rounded mt-1">
                                            kubectl apply -f k8s/
                                        </code>
                                    </div>
                                    <div>
                                        <strong>API Endpoints:</strong>
                                        <div className="bg-white p-2 rounded mt-1 text-xs">
                                            {generatedAPIs.apis.slice(0, 2).map((api: any) => (
                                                <div key={api.nodeId}>POST {api.endpoint}</div>
                                            ))}
                                            {generatedAPIs.apis.length > 2 && <div>... and {generatedAPIs.apis.length - 2} more</div>}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Individual API Code Modal */}
                {false && selectedAPI && (
                    <div className="processing-overlay">
                        <div className="processing-content" style={{ maxWidth: '1000px', width: '95%', maxHeight: '90vh', overflow: 'auto' }}>
                            <div className="flex items-center justify-between mb-4">
                                <h2>📝 {selectedAPI.nodeName} Service Code</h2>
                                <button
                                    onClick={() => setSelectedAPI(null)}
                                    className="btn btn-secondary"
                                    style={{ padding: '8px 12px' }}
                                >
                                    ×
                                </button>
                            </div>

                            <pre style={{
                                background: 'var(--bg-dark)',
                                color: 'var(--text-light)',
                                padding: '16px',
                                borderRadius: '6px',
                                fontSize: '12px',
                                overflow: 'auto',
                                maxHeight: '70vh',
                                lineHeight: '1.4'
                            }}>
                                {selectedAPI.code}
                            </pre>

                            <div className="mt-4 flex gap-2">
                                <button
                                    onClick={() => {
                                        navigator.clipboard.writeText(selectedAPI.code);
                                        alert('Code copied to clipboard!');
                                    }}
                                    className="btn btn-blue"
                                >
                                    📋 Copy Code
                                </button>
                                <button
                                    onClick={() => setSelectedAPI(null)}
                                    className="btn btn-secondary"
                                >
                                    Close
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Export Code Modal */}
                {showExportModal && (
                    <div className="processing-overlay">
                        <div className="processing-content" style={{ maxWidth: '800px', width: '95%', maxHeight: '90vh', overflow: 'auto' }}>
                            <div className="flex items-center justify-between mb-4">
                                <h2>📄 Export Generated Code</h2>
                                <button
                                    onClick={() => setShowExportModal(false)}
                                    className="btn btn-secondary"
                                    style={{ padding: '8px 12px' }}
                                >
                                    ×
                                </button>
                            </div>

                            {exportedJson && (() => {
                                try {
                                    const projectData = JSON.parse(exportedJson);
                                    return (
                                        <div>
                                            <div style={{ marginBottom: '24px' }}>
                                                <h3 style={{ color: 'var(--green)', marginBottom: '16px' }}>
                                                    ✅ Project Export Ready!
                                                </h3>
                                                <div style={{
                                                    background: 'var(--gray-700)',
                                                    padding: '12px',
                                                    borderRadius: 'var(--radius)',
                                                    marginBottom: '16px'
                                                }}>
                                                    <strong>Project:</strong> {projectData.project_info?.name || 'Nodex Workflow'}<br />
                                                    <strong>Services:</strong> {projectData.project_info?.total_services || 0}<br />
                                                    <strong>Total Code:</strong> {projectData.project_info?.total_lines || 0} lines<br />
                                                    <strong>Generated in:</strong> {projectData.project_info?.generation_time || 0}s
                                                </div>
                                            </div>

                                            <div style={{ marginBottom: '24px' }}>
                                                <h4 style={{ marginBottom: '12px' }}>🚀 Deployment Options</h4>
                                                <div style={{
                                                    display: 'grid',
                                                    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                                                    gap: '16px',
                                                    marginBottom: '16px'
                                                }}>
                                                    <div style={{
                                                        background: 'var(--gray-700)',
                                                        padding: '12px',
                                                        borderRadius: 'var(--radius)'
                                                    }}>
                                                        <strong>🐳 Docker (Recommended)</strong><br />
                                                        <code style={{ fontSize: '12px' }}>docker-compose up -d</code><br />
                                                        <small>All services + database + monitoring</small>
                                                    </div>
                                                    <div style={{
                                                        background: 'var(--gray-700)',
                                                        padding: '12px',
                                                        borderRadius: 'var(--radius)'
                                                    }}>
                                                        <strong>☁️ Kubernetes</strong><br />
                                                        <code style={{ fontSize: '12px' }}>kubectl apply -f k8s/</code><br />
                                                        <small>Production deployment with auto-scaling</small>
                                                    </div>
                                                </div>
                                            </div>

                                            <div style={{ marginBottom: '24px' }}>
                                                <h4 style={{ marginBottom: '12px' }}>📦 Download Project</h4>
                                                <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
                                                    <button
                                                        onClick={() => {
                                                            const blob = new Blob([exportedJson], { type: 'application/json' });
                                                            const url = URL.createObjectURL(blob);
                                                            const a = document.createElement('a');
                                                            a.href = url;
                                                            a.download = 'nodex-project.json';
                                                            a.click();
                                                            URL.revokeObjectURL(url);
                                                        }}
                                                        className="btn btn-blue"
                                                    >
                                                        💾 Download JSON
                                                    </button>
                                                    <button
                                                        onClick={() => {
                                                            navigator.clipboard.writeText(exportedJson);
                                                            alert('Project data copied to clipboard!');
                                                        }}
                                                        className="btn btn-green"
                                                    >
                                                        📋 Copy All
                                                    </button>
                                                </div>
                                            </div>

                                            <div style={{ marginBottom: '24px' }}>
                                                <h4 style={{ marginBottom: '12px' }}>📋 Project Structure</h4>
                                                <div style={{
                                                    background: 'var(--gray-700)',
                                                    padding: '16px',
                                                    borderRadius: 'var(--radius)',
                                                    fontSize: '14px',
                                                    fontFamily: 'monospace'
                                                }}>
                                                    {[
                                                        'nodex-project/',
                                                        '├── services/',
                                                        ...(projectData.apis?.map((api: any) => [
                                                            `│   ├── ${api.service_name.toLowerCase()}/`,
                                                            `│   │   ├── main.py (${api.lines_of_code} lines)`,
                                                            `│   │   ├── Dockerfile`,
                                                            `│   │   └── requirements.txt`
                                                        ]).flat() || []),
                                                        '├── orchestrator/',
                                                        `│   ├── main.py (${projectData.orchestrator?.lines_of_code || 0} lines)`,
                                                        '│   ├── Dockerfile',
                                                        '│   └── requirements.txt',
                                                        '├── deployment/',
                                                        '│   ├── docker-compose.yml',
                                                        '│   ├── Dockerfile',
                                                        '│   └── k8s/',
                                                        '│       ├── deployment.yml',
                                                        '│       └── service.yml',
                                                        '└── README.md'
                                                    ].join('\n')}
                                                </div>
                                            </div>

                                            <div style={{ marginBottom: '16px' }}>
                                                <h4 style={{ marginBottom: '8px' }}>📊 Project JSON Preview</h4>
                                                <div style={{ fontSize: '12px', color: 'var(--gray-400)', marginBottom: '8px' }}>
                                                    Contains all service code, deployment configs, and documentation
                                                </div>
                                            </div>

                                            <pre style={{
                                                background: 'var(--black)',
                                                color: 'var(--green)',
                                                padding: '16px',
                                                borderRadius: '6px',
                                                fontSize: '11px',
                                                overflow: 'auto',
                                                maxHeight: '300px',
                                                border: '1px solid var(--gray-600)'
                                            }}>
                                                {JSON.stringify(projectData, null, 2).substring(0, 500)}...
                                            </pre>

                                            <div style={{
                                                marginTop: '16px',
                                                padding: '12px',
                                                background: 'rgba(34, 197, 94, 0.1)',
                                                border: '1px solid rgba(34, 197, 94, 0.3)',
                                                borderRadius: 'var(--radius)',
                                                fontSize: '12px'
                                            }}>
                                                <strong>🎉 Success!</strong> Your workflow has been converted to {projectData.project_info?.total_services} production-ready microservices with {projectData.project_info?.total_lines} lines of code.
                                            </div>
                                        </div>
                                    );
                                } catch (e) {
                                    return (
                                        <pre style={{
                                            background: 'var(--black)',
                                            color: 'var(--white)',
                                            padding: '16px',
                                            borderRadius: '6px',
                                            fontSize: '12px',
                                            overflow: 'auto',
                                            maxHeight: '400px'
                                        }}>
                                            {exportedJson}
                                        </pre>
                                    );
                                }
                            })()}
                        </div>
                    </div>
                )}

            </div>
        </ReactFlowProvider>
    );
};

export default App;
