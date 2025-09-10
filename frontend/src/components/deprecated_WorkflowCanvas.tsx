import React, { useState, useCallback, useRef, useEffect } from 'react';
import ReactFlow, {
    Node,
    Edge,
    useNodesState,
    useEdgesState,
    Controls,
    Background,
    MiniMap,
    Connection,
    addEdge,
} from 'reactflow';
import 'reactflow/dist/style.css';

// Define the props interface for the component
interface WorkflowCanvasProps {
    sessionId: string;
    userId: string;
    onFlowChange?: (nodes: Node[], edges: Edge[]) => void;
    onVoiceInput?: (audioBlob: Blob) => void;
}

// Define the types for conversation history roles and agent status
type ConversationRole = 'user' | 'assistant' | 'system';
type AgentStatus = 'disconnected' | 'connecting' | 'connected' | 'speaking' | 'listening' | 'error';

// Template definitions for quick selection
const WORKFLOW_TEMPLATES: Record<string, Record<string, string>> = {
    hr: {
        'employee_onboarding': 'Employee Onboarding Process',
        'employee_offboarding': 'Employee Offboarding Process'
    },
    finance: {
        'expense_approval': 'Expense Approval Workflow',
        'vendor_invoice_processing': 'Vendor Invoice Processing',
        'procurement_po': 'Procurement and Purchase Order'
    },
    sales: {
        'lead_qualification': 'Lead Qualification Process',
        'lead_routing': 'Lead Routing Process'
    },
    it: {
        'incident_management': 'IT Incident Management',
        'data_access_request': 'Data Pipeline Access Request'
    },
    operations: {
        'document_approval': 'Document Approval & Publishing',
        'customer_support_escalation': 'Customer Support Escalation'
    }
};

const WorkflowCanvas: React.FC<WorkflowCanvasProps> = ({ sessionId, userId, onFlowChange, onVoiceInput }) => {
    // React Flow state management
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [selectedNode, setSelectedNode] = useState<Node | null>(null);

    // State for backend communication
    const [agentStatus, setAgentStatus] = useState<AgentStatus>('disconnected');
    const [conversationHistory, setConversationHistory] = useState<Array<{ role: ConversationRole, content: string, timestamp: Date }>>([]);
    const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);
    const [wsConnected, setWsConnected] = useState(false);

    // UI State
    const [isLoading, setIsLoading] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState('');
    const [showTemplates, setShowTemplates] = useState(true);
    const [showNodeDetails, setShowNodeDetails] = useState(false);
    const [showConfigModal, setShowConfigModal] = useState(false);
    const [contextMenu, setContextMenu] = useState<{ show: boolean; x: number; y: number; node: Node | null }>({ show: false, x: 0, y: 0, node: null });
    const [nodeToolbarPosition, setNodeToolbarPosition] = useState({ x: 0, y: 0 });
    const [showNodeToolbar, setShowNodeToolbar] = useState(false);

    // Image to Workflow State
    const [showImageUpload, setShowImageUpload] = useState(false);
    const [uploadedImage, setUploadedImage] = useState<string | null>(null);
    const [isProcessingImage, setIsProcessingImage] = useState(false);
    const [imageProcessingProgress, setImageProcessingProgress] = useState(0);

    // Memoized function to update node details
    const updateNodeDetails = useCallback((id: string, data: any) => {
        setNodes((currentNodes) => {
            const updatedNodes = currentNodes.map(node => node.id === id ? { ...node, data: { ...node.data, ...data } } : node);
            if (onFlowChange) onFlowChange(updatedNodes, edges);
            return updatedNodes;
        });
    }, [setNodes, edges, onFlowChange]);

    // Memoized function to copy text to clipboard
    const copyToClipboard = useCallback(async (text: string) => {
        try {
            await navigator.clipboard.writeText(text);
            // You could add a toast notification here
        } catch (error) {
            console.error('Failed to copy to clipboard:', error);
        }
    }, []);

    // Memoized function to add a new node to the canvas
    const addNode = useCallback((type: string, position?: { x: number; y: number }) => {
        const nodeTypes = {
            'input': { label: 'Input', color: '#10b981' },
            'process': { label: 'Process', color: '#3b82f6' },
            'decision': { label: 'Decision', color: '#f59e0b' },
            'compliance': { label: 'Compliance', color: '#ef4444' },
            'output': { label: 'Output', color: '#8b5cf6' },
            'approval': { label: 'Approval', color: '#06b6d4' }
        };

        const nodeType = nodeTypes[type as keyof typeof nodeTypes] || nodeTypes['process'];
        const newNode: Node = {
            id: `${type}-${Date.now()}`,
            type: 'default',
            position: position || { x: Math.random() * 400 + 100, y: Math.random() * 300 + 100 },
            data: { label: nodeType.label, description: `${nodeType.label} node`, locked: type === 'compliance', nodeType: type },
            style: {
                background: nodeType.color,
                color: 'white',
                border: '1px solid #222',
                borderRadius: '8px',
                padding: '10px',
                minWidth: '120px',
                fontSize: '12px',
                fontWeight: '600'
            }
        };
        setNodes((currentNodes) => {
            const updatedNodes = [...currentNodes, newNode];
            if (onFlowChange) onFlowChange(updatedNodes, edges);
            return updatedNodes;
        });
    }, [setNodes, edges, onFlowChange]);

    // Memoized function to load a workflow template
    const loadWorkflowTemplate = useCallback(async (domain: string, templateName: string) => {
        try {
            setIsLoading(true);
            setLoadingMessage('Loading template...');
            const response = await fetch('http://localhost:8000/api/templates/load', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    domain: domain,
                    template_name: templateName,
                    user_id: userId,
                    session_id: sessionId
                }),
            });

            if (response.ok) {
                const result = await response.json();
                console.log(`Loading ${domain} ${templateName} template:`, result);
                setShowTemplates(false);
                setConversationHistory(prev => [...prev, {
                    role: 'user',
                    content: `Load ${domain} ${templateName.replace('_', ' ')} template`,
                    timestamp: new Date()
                }]);
            } else {
                const error = await response.json();
                console.error('Error loading template:', error);
                setConversationHistory(prev => [...prev, {
                    role: 'system',
                    content: `Failed to load template: ${error.error || 'Unknown error'}`,
                    timestamp: new Date()
                }]);
            }
        } catch (error) {
            console.error('Error loading template:', error);
            setConversationHistory(prev => [...prev, {
                role: 'system',
                content: 'Failed to connect to server for template loading',
                timestamp: new Date()
            }]);
        } finally {
            setIsLoading(false);
            setLoadingMessage('');
        }
    }, [userId, sessionId]);

    // Memoized function to duplicate a node
    const duplicateNode = useCallback((node: Node) => {
        const newNode: Node = {
            ...node,
            id: `${node.id}-copy-${Date.now()}`,
            position: { x: node.position.x + 150, y: node.position.y + 50 },
            data: { ...node.data, label: `${node.data.label} (Copy)` }
        };
        setNodes((currentNodes) => {
            const updatedNodes = [...currentNodes, newNode];
            if (onFlowChange) onFlowChange(updatedNodes, edges);
            return updatedNodes;
        });
    }, [setNodes, edges, onFlowChange]);

    // Memoized function to delete a node
    const deleteNode = useCallback((nodeId: string) => {
        setNodes((currentNodes) => {
            const updatedNodes = currentNodes.filter(node => node.id !== nodeId);
            if (onFlowChange) onFlowChange(updatedNodes, edges);
            return updatedNodes;
        });
        setEdges((currentEdges) => currentEdges.filter(edge => edge.source !== nodeId && edge.target !== nodeId));
        setShowNodeDetails(false);
        setShowNodeToolbar(false);
    }, [setNodes, setEdges, edges, onFlowChange]);

    // Memoized function to change node type
    const changeNodeType = useCallback((nodeId: string, newType: string) => {
        const nodeTypes = {
            'input': { label: 'Input', color: '#10b981' },
            'process': { label: 'Process', color: '#3b82f6' },
            'decision': { label: 'Decision', color: '#f59e0b' },
            'compliance': { label: 'Compliance', color: '#ef4444' },
            'output': { label: 'Output', color: '#8b5cf6' },
            'approval': { label: 'Approval', color: '#06b6d4' }
        };

        const nodeType = nodeTypes[newType as keyof typeof nodeTypes] || nodeTypes['process'];
        setNodes((currentNodes) => {
            const updatedNodes = currentNodes.map(node =>
                node.id === nodeId
                    ? {
                        ...node,
                        data: { ...node.data, nodeType: newType, label: nodeType.label },
                        style: {
                            ...node.style,
                            background: nodeType.color
                        }
                    }
                    : node
            );
            if (onFlowChange) onFlowChange(updatedNodes, edges);
            return updatedNodes;
        });
    }, [setNodes, edges, onFlowChange]);

    // Memoized function for handling new connections between nodes
    const onConnect = useCallback((params: Connection) => {
        setEdges((eds) => {
            const newEdges = addEdge(params, eds);
            if (onFlowChange) onFlowChange(nodes, newEdges);
            return newEdges;
        });
    }, [setEdges, nodes, onFlowChange]);

    // Event handlers
    const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
        setSelectedNode(node);
        setShowNodeDetails(true);
        setShowNodeToolbar(true);
        setNodeToolbarPosition({ x: event.clientX, y: event.clientY });
    }, []);

    const onNodeContextMenu = useCallback((event: React.MouseEvent, node: Node) => {
        event.preventDefault();
        setSelectedNode(node);
        setContextMenu({
            show: true,
            x: event.clientX,
            y: event.clientY,
            node: node
        });
    }, []);

    const onPaneClick = useCallback(() => {
        setShowNodeDetails(false);
        setShowNodeToolbar(false);
        setContextMenu({ show: false, x: 0, y: 0, node: null });
    }, []);

    // Context menu handlers
    const handleEditProperties = useCallback(() => {
        if (contextMenu.node) {
            setSelectedNode(contextMenu.node);
            setShowNodeDetails(true);
        }
        setContextMenu({ show: false, x: 0, y: 0, node: null });
    }, [contextMenu.node]);

    const handleDuplicate = useCallback(() => {
        if (contextMenu.node) {
            duplicateNode(contextMenu.node);
        }
        setContextMenu({ show: false, x: 0, y: 0, node: null });
    }, [contextMenu.node, duplicateNode]);

    const handleChangeType = useCallback((newType: string) => {
        if (contextMenu.node) {
            changeNodeType(contextMenu.node.id, newType);
        }
        setContextMenu({ show: false, x: 0, y: 0, node: null });
    }, [contextMenu.node, changeNodeType]);

    const handleDelete = useCallback(() => {
        if (contextMenu.node && !contextMenu.node.data.locked) {
            deleteNode(contextMenu.node.id);
        }
        setContextMenu({ show: false, x: 0, y: 0, node: null });
    }, [contextMenu.node, deleteNode]);

    const handleConfigureNode = useCallback(() => {
        if (contextMenu.node) {
            setSelectedNode(contextMenu.node);
            setShowConfigModal(true);
        }
        setContextMenu({ show: false, x: 0, y: 0, node: null });
    }, [contextMenu.node]);

    // WebSocket connection and message handling
    useEffect(() => {
        if (!sessionId) return;

        const wsUrl = `ws://localhost:8000/ws/${sessionId}`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('WebSocket connected');
            setWsConnected(true);
            setAgentStatus('connected');
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('WebSocket message received:', data);

                if (data.type === 'workflow_update') {
                    if (data.nodes && data.edges) {
                        setNodes(data.nodes);
                        setEdges(data.edges);
                        if (onFlowChange) onFlowChange(data.nodes, data.edges);
                    }
                } else if (data.type === 'agent_response') {
                    setConversationHistory(prev => [...prev, {
                        role: 'assistant',
                        content: data.message,
                        timestamp: new Date()
                    }]);
                    setAgentStatus('connected');
                } else if (data.type === 'agent_status') {
                    setAgentStatus(data.status);
                } else if (data.type === 'error') {
                    console.error('WebSocket error:', data.message);
                    setConversationHistory(prev => [...prev, {
                        role: 'system',
                        content: `Error: ${data.message}`,
                        timestamp: new Date()
                    }]);
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
            setWsConnected(false);
            setAgentStatus('disconnected');
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            setWsConnected(false);
            setAgentStatus('error');
        };

        setWsConnection(ws);

        return () => {
            ws.close();
        };
    }, [sessionId, onFlowChange, setNodes, setEdges]);

    // Voice and text input handlers
    const sendTextMessage = useCallback(async (message: string) => {
        if (!message.trim()) return;

        setConversationHistory(prev => [...prev, {
            role: 'user',
            content: message,
            timestamp: new Date()
        }]);

        setAgentStatus('listening');

        try {
            const response = await fetch('http://localhost:8000/api/process-text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    user_id: userId,
                    session_id: sessionId
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Text processing result:', result);
        } catch (error) {
            console.error('Error sending text message:', error);
            setConversationHistory(prev => [...prev, {
                role: 'system',
                content: 'Failed to process message. Please try again.',
                timestamp: new Date()
            }]);
            setAgentStatus('connected');
        }
    }, [userId, sessionId]);

    // Image upload handlers
    const handleImageUpload = useCallback(async (file: File) => {
        try {
            setIsProcessingImage(true);
            setImageProcessingProgress(10);

            // Convert file to base64
            const reader = new FileReader();
            reader.onload = async (e) => {
                const base64Image = e.target?.result as string;
                setUploadedImage(base64Image);
                setImageProcessingProgress(30);

                try {
                    // Send to backend for processing
                    const response = await fetch('http://localhost:8000/api/parse-image', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            image: base64Image,
                            domain: 'general'
                        })
                    });

                    setImageProcessingProgress(70);

                    if (!response.ok) {
                        throw new Error('Failed to process image');
                    }

                    const workflowData = await response.json();
                    setImageProcessingProgress(90);

                    // Update workflow with processed data
                    setNodes(workflowData.nodes);
                    setEdges(workflowData.edges);

                    // Add to conversation history
                    setConversationHistory(prev => [...prev, {
                        role: 'assistant',
                        content: `Successfully processed workflow image! Generated ${workflowData.nodes.length} nodes with ${workflowData.compliance_info.compliance_nodes_added} compliance steps for ${workflowData.compliance_info.domain} domain.`,
                        timestamp: new Date()
                    }]);

                    setImageProcessingProgress(100);
                    setTimeout(() => {
                        setShowImageUpload(false);
                        setIsProcessingImage(false);
                        setImageProcessingProgress(0);
                    }, 1000);

                } catch (error) {
                    console.error('Image processing error:', error);
                    setConversationHistory(prev => [...prev, {
                        role: 'assistant',
                        content: `Failed to process image: ${error instanceof Error ? error.message : 'Unknown error'}`,
                        timestamp: new Date()
                    }]);
                    setIsProcessingImage(false);
                    setImageProcessingProgress(0);
                }
            };
            reader.readAsDataURL(file);
        } catch (error) {
            console.error('File reading error:', error);
            setIsProcessingImage(false);
            setImageProcessingProgress(0);
        }
    }, [setNodes, setEdges, setConversationHistory]);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();

        const files = Array.from(e.dataTransfer.files);
        const imageFile = files.find(file => file.type.startsWith('image/'));

        if (imageFile) {
            handleImageUpload(imageFile);
        }
    }, [handleImageUpload]);

    // Node configuration modal content
    const configModalContent = selectedNode ? (
        <div className="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-gray-700 pb-4">
                <h2 className="text-xl font-semibold text-white">Node Configuration</h2>
                <button
                    onClick={() => setShowConfigModal(false)}
                    className="text-gray-400 hover:text-white"
                >
                    ✕
                </button>
            </div>

            {/* Notice */}
            <div className="bg-amber-900/30 border border-amber-600 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                    <div className="text-amber-500 text-lg">⚠️</div>
                    <div>
                        <h3 className="text-amber-200 font-medium">Read-Only Configuration</h3>
                        <p className="text-amber-100 text-sm mt-1">
                            Interactive editing is under construction. To modify node configurations,
                            please edit the workflow files manually in your code editor.
                        </p>
                    </div>
                </div>
            </div>

            {/* Basic Node Details */}
            <div className="space-y-4">
                <h3 className="text-lg font-medium text-white border-b border-gray-700 pb-2">Node Details</h3>
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">Node ID</label>
                        <div className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-gray-300 text-sm">
                            {selectedNode.id}
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">Node Type</label>
                        <div className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-gray-300 text-sm">
                            {selectedNode.data.nodeType || 'default'}
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">Label</label>
                        <div className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-gray-300 text-sm">
                            {selectedNode.data.label}
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">Status</label>
                        <div className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-gray-300 text-sm">
                            {selectedNode.data.locked ? 'Locked' : 'Editable'}
                        </div>
                    </div>
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
                    <div className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-gray-300 text-sm">
                        {selectedNode.data.description || 'No description provided'}
                    </div>
                </div>
            </div>

            {/* Node-Specific Settings */}
            <div className="space-y-4">
                <h3 className="text-lg font-medium text-white border-b border-gray-700 pb-2">Node-Specific Settings</h3>

                {selectedNode.data.nodeType === 'compliance' && (
                    <div className="bg-red-900/20 border border-red-600 rounded-lg p-4">
                        <h4 className="text-red-200 font-medium mb-2">Compliance Settings</h4>
                        <div className="space-y-2 text-sm">
                            <div>Compliance Type: {selectedNode.data.compliance_type || 'General'}</div>
                            <div>Regulatory Framework: {selectedNode.data.framework || 'Not specified'}</div>
                            <div>Validation Rules: {Array.isArray(selectedNode.data.rules) ? selectedNode.data.rules.length : 0} configured</div>
                        </div>
                    </div>
                )}

                {selectedNode.data.nodeType === 'input' && (
                    <div className="bg-green-900/20 border border-green-600 rounded-lg p-4">
                        <h4 className="text-green-200 font-medium mb-2">Input Settings</h4>
                        <div className="space-y-2 text-sm">
                            <div>Input Type: {selectedNode.data.input_type || 'Manual'}</div>
                            <div>Data Format: {selectedNode.data.format || 'JSON'}</div>
                            <div>Required Fields: {Array.isArray(selectedNode.data.required_fields) ? selectedNode.data.required_fields.length : 0}</div>
                        </div>
                    </div>
                )}

                {selectedNode.data.nodeType === 'process' && (
                    <div className="bg-blue-900/20 border border-blue-600 rounded-lg p-4">
                        <h4 className="text-blue-200 font-medium mb-2">Process Settings</h4>
                        <div className="space-y-2 text-sm">
                            <div>Process Type: {selectedNode.data.process_type || 'Standard'}</div>
                            <div>Timeout: {selectedNode.data.timeout || '30s'}</div>
                            <div>Retry Count: {selectedNode.data.retry_count || 3}</div>
                        </div>
                    </div>
                )}

                {selectedNode.data.nodeType === 'decision' && (
                    <div className="bg-yellow-900/20 border border-yellow-600 rounded-lg p-4">
                        <h4 className="text-yellow-200 font-medium mb-2">Decision Settings</h4>
                        <div className="space-y-2 text-sm">
                            <div>Decision Logic: {selectedNode.data.logic || 'Rule-based'}</div>
                            <div>Conditions: {Array.isArray(selectedNode.data.conditions) ? selectedNode.data.conditions.length : 0} configured</div>
                            <div>Default Path: {selectedNode.data.default_path || 'Continue'}</div>
                        </div>
                    </div>
                )}
            </div>

            {/* Validation Settings */}
            <div className="space-y-4">
                <h3 className="text-lg font-medium text-white border-b border-gray-700 pb-2">Validation Settings</h3>
                <div className="bg-gray-800 rounded-lg p-4">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <span className="text-gray-300">Input Validation:</span>
                            <span className="ml-2 text-white">{selectedNode.data.validate_input ? 'Enabled' : 'Disabled'}</span>
                        </div>
                        <div>
                            <span className="text-gray-300">Output Validation:</span>
                            <span className="ml-2 text-white">{selectedNode.data.validate_output ? 'Enabled' : 'Disabled'}</span>
                        </div>
                        <div>
                            <span className="text-gray-300">Error Handling:</span>
                            <span className="ml-2 text-white">{selectedNode.data.error_handling || 'Default'}</span>
                        </div>
                        <div>
                            <span className="text-gray-300">Logging Level:</span>
                            <span className="ml-2 text-white">{selectedNode.data.log_level || 'INFO'}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Raw JSON Data */}
            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <h3 className="text-lg font-medium text-white border-b border-gray-700 pb-2">Raw Configuration Data</h3>
                    <button
                        onClick={() => copyToClipboard(JSON.stringify(selectedNode, null, 2))}
                        className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
                    >
                        Copy JSON
                    </button>
                </div>
                <div className="bg-gray-900 border border-gray-600 rounded-lg p-4 overflow-x-auto">
                    <pre className="text-xs text-gray-300 whitespace-pre-wrap">
                        {JSON.stringify(selectedNode, null, 2)}
                    </pre>
                </div>
            </div>
        </div>
    ) : null;

    // Render the config modal
    {
        showConfigModal && (
            <div className="fixed top-0 left-0 w-full h-full bg-slate-900 bg-opacity-50 flex items-center justify-center">
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 w-1/2">
                    {configModalContent}
                </div>
            </div>
        )
    }

    return (
        <div className="flex h-full bg-gray-900">
            {/* Left Panel - Voice Command Center */}
            <div className="w-80 bg-gray-800 border-r border-gray-700 flex flex-col">
                {/* Header */}
                <div className="p-4 border-b border-gray-700">
                    <h2 className="text-lg font-semibold text-white mb-2">Voice Command Center</h2>
                    <div className="flex items-center space-x-2">
                        <div className={`w-3 h-3 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                        <span className="text-sm text-gray-300">
                            {wsConnected ? 'Connected' : 'Disconnected'}
                        </span>
                    </div>
                </div>

                {/* Voice Assistant */}
                <div className="p-4 border-b border-gray-700">
                    <div className="bg-gray-700 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                            <span className="text-white font-medium">Voice Assistant</span>
                            <div className={`px-2 py-1 rounded text-xs ${agentStatus === 'listening' ? 'bg-blue-600 text-white' :
                                agentStatus === 'speaking' ? 'bg-yellow-600 text-white' :
                                    'bg-gray-600 text-gray-300'
                                }`}>
                                {agentStatus}
                            </div>
                        </div>

                        {agentStatus === 'listening' && (
                            <div className="w-full bg-gray-600 rounded-full h-2 mb-3">
                                <div className="bg-blue-500 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                            </div>
                        )}

                        <button
                            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded transition-colors"
                            disabled={agentStatus === 'speaking'}
                        >
                            {agentStatus === 'listening' ? 'Stop Listening' : 'Start Voice Command'}
                        </button>
                    </div>
                </div>

                {/* Workflow Management */}
                <div className="p-4 border-b border-gray-700">
                    <h3 className="text-white font-medium mb-3">Workflow Management</h3>
                    <div className="space-y-2">
                        <button
                            onClick={() => setShowTemplates(true)}
                            className="w-full bg-gray-700 hover:bg-gray-600 text-white py-2 px-3 rounded text-sm transition-colors"
                        >
                            Load Template
                        </button>
                        <button
                            onClick={() => {
                                setNodes([]);
                                setEdges([]);
                                if (onFlowChange) onFlowChange([], []);
                            }}
                            className="w-full bg-red-600 hover:bg-red-700 text-white py-2 px-3 rounded text-sm transition-colors"
                        >
                            Clear Workflow
                        </button>
                        <button
                            onClick={() => setShowImageUpload(true)}
                            className="w-full bg-gray-700 hover:bg-gray-600 text-white py-2 px-3 rounded text-sm transition-colors"
                        >
                            Upload Image
                        </button>
                    </div>
                </div>

                {/* Conversation History */}
                <div className="flex-1 p-4 overflow-hidden">
                    <h3 className="text-white font-medium mb-3">Conversation</h3>
                    <div className="bg-gray-700 rounded-lg p-3 h-64 overflow-y-auto">
                        {conversationHistory.length === 0 ? (
                            <p className="text-gray-400 text-sm">Start a conversation...</p>
                        ) : (
                            <div className="space-y-2">
                                {conversationHistory.map((msg, index) => (
                                    <div key={index} className={`text-sm p-2 rounded ${msg.role === 'user' ? 'bg-blue-600 text-white ml-4' :
                                        msg.role === 'assistant' ? 'bg-gray-600 text-white mr-4' :
                                            'bg-yellow-600 text-white'
                                        }`}>
                                        <div className="font-medium text-xs opacity-75 mb-1">
                                            {msg.role === 'user' ? 'You' : msg.role === 'assistant' ? 'Assistant' : 'System'}
                                        </div>
                                        {msg.content}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Text Input */}
                    <div className="mt-3">
                        <div className="flex space-x-2">
                            <input
                                type="text"
                                placeholder="Type a message..."
                                className="flex-1 bg-gray-600 text-white px-3 py-2 rounded text-sm"
                                onKeyPress={(e) => {
                                    if (e.key === 'Enter') {
                                        sendTextMessage(e.currentTarget.value);
                                        e.currentTarget.value = '';
                                    }
                                }}
                            />
                            <button
                                onClick={(e) => {
                                    const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                                    sendTextMessage(input.value);
                                    input.value = '';
                                }}
                                className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded text-sm transition-colors"
                            >
                                Send
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Canvas */}
            <div className="flex-1 relative">
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={onConnect}
                    onNodeClick={onNodeClick}
                    onNodeContextMenu={onNodeContextMenu}
                    onPaneClick={onPaneClick}
                    fitView
                    className="bg-gray-900"
                >
                    <Controls className="bg-gray-800 border-gray-600" />
                    <MiniMap className="bg-gray-800 border-gray-600" />
                    <Background color="#374151" gap={16} />
                </ReactFlow>

                {/* Loading Overlay */}
                {isLoading && (
                    <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                        <div className="bg-gray-800 rounded-lg p-6 text-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
                            <p className="text-white">{loadingMessage}</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Right Panel - Node Details */}
            {showNodeDetails && selectedNode && (
                <div className="w-80 bg-gray-800 border-l border-gray-700 p-4">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-white">Node Details</h3>
                        <button
                            onClick={() => setShowNodeDetails(false)}
                            className="text-gray-400 hover:text-white"
                        >
                            ✕
                        </button>
                    </div>

                    {/* Node Toolbar */}
                    <div className="flex space-x-2 mb-4">
                        <button
                            onClick={() => duplicateNode(selectedNode)}
                            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-3 rounded text-sm transition-colors"
                        >
                            Duplicate
                        </button>
                        <button
                            onClick={() => deleteNode(selectedNode.id)}
                            disabled={selectedNode.data.locked}
                            className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white py-2 px-3 rounded text-sm transition-colors"
                        >
                            Delete
                        </button>
                    </div>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">Label</label>
                            <input
                                type="text"
                                value={selectedNode.data.label}
                                onChange={(e) => updateNodeDetails(selectedNode.id, { label: e.target.value })}
                                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
                            <textarea
                                value={selectedNode.data.description || ''}
                                onChange={(e) => updateNodeDetails(selectedNode.id, { description: e.target.value })}
                                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-20"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">Node Type</label>
                            <select
                                value={selectedNode.data.nodeType || 'process'}
                                onChange={(e) => changeNodeType(selectedNode.id, e.target.value)}
                                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                            >
                                <option value="input">Input</option>
                                <option value="process">Process</option>
                                <option value="decision">Decision</option>
                                <option value="compliance">Compliance</option>
                                <option value="output">Output</option>
                                <option value="approval">Approval</option>
                            </select>
                        </div>

                        {selectedNode.data.locked && (
                            <div className="bg-red-900/30 border border-red-600 rounded-lg p-3">
                                <p className="text-red-200 text-sm">
                                    🔒 This node is locked and cannot be deleted to maintain compliance requirements.
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Context Menu */}
            {contextMenu.show && (
                <div
                    className="fixed bg-gray-800 border border-gray-600 rounded-lg shadow-lg py-2 z-50"
                    style={{ left: contextMenu.x, top: contextMenu.y }}
                >
                    <button
                        onClick={handleEditProperties}
                        className="w-full text-left px-4 py-2 text-white hover:bg-gray-700 text-sm"
                    >
                        Edit Properties
                    </button>
                    <button
                        onClick={handleConfigureNode}
                        className="w-full text-left px-4 py-2 text-white hover:bg-gray-700 text-sm"
                    >
                        Configure Node
                    </button>
                    <button
                        onClick={handleDuplicate}
                        className="w-full text-left px-4 py-2 text-white hover:bg-gray-700 text-sm"
                    >
                        Duplicate
                    </button>
                    <div className="border-t border-gray-600 my-1"></div>
                    <div className="px-4 py-1">
                        <span className="text-xs text-gray-400">Change Type:</span>
                    </div>
                    {['input', 'process', 'decision', 'compliance', 'output', 'approval'].map(type => (
                        <button
                            key={type}
                            onClick={() => handleChangeType(type)}
                            className="w-full text-left px-6 py-1 text-white hover:bg-gray-700 text-sm capitalize"
                        >
                            {type}
                        </button>
                    ))}
                    <div className="border-t border-gray-600 my-1"></div>
                    <button
                        onClick={handleDelete}
                        disabled={contextMenu.node?.data.locked}
                        className="w-full text-left px-4 py-2 text-red-400 hover:bg-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed text-sm"
                    >
                        Delete
                    </button>
                </div>
            )}

            {/* Node Configuration Modal */}
            {showConfigModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
                        {configModalContent}
                    </div>
                </div>
            )}

            {/* Image Upload Modal */}
            {showImageUpload && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4">
                        <div className="p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-xl font-semibold text-white">Upload Image</h2>
                                <button
                                    onClick={() => setShowImageUpload(false)}
                                    className="text-gray-400 hover:text-white"
                                >
                                    ✕
                                </button>
                            </div>

                            <div className="bg-gray-700 rounded-lg p-4">
                                <div className="flex items-center justify-between mb-3">
                                    <span className="text-white font-medium">Upload Image</span>
                                    <div className={`px-2 py-1 rounded text-xs ${isProcessingImage ? 'bg-blue-600 text-white' : 'bg-gray-600 text-gray-300'}`}>
                                        {isProcessingImage ? 'Processing...' : 'Upload'}
                                    </div>
                                </div>

                                <div className="w-full bg-gray-600 rounded-full h-2 mb-3">
                                    <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${imageProcessingProgress}%` }}></div>
                                </div>

                                <input
                                    type="file"
                                    accept="image/*"
                                    onChange={(e) => handleImageUpload(e.target.files![0])}
                                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                                />
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Templates Modal */}
            {showTemplates && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4">
                        <div className="p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-xl font-semibold text-white">Load Workflow Template</h2>
                                <button
                                    onClick={() => setShowTemplates(false)}
                                    className="text-gray-400 hover:text-white"
                                >
                                    ✕
                                </button>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                {Object.entries(WORKFLOW_TEMPLATES).flatMap(([domain, templates]) =>
                                    Object.entries(templates).map(([templateName, templateLabel]) => (
                                        <button
                                            key={`${domain}-${templateName}`}
                                            onClick={() => loadWorkflowTemplate(domain, templateName)}
                                            className="p-4 bg-gray-700 hover:bg-gray-600 rounded-lg text-left transition-colors"
                                        >
                                            <div className="text-white font-medium">{templateLabel}</div>
                                            <div className="text-gray-400 text-sm capitalize">{domain}</div>
                                        </button>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default WorkflowCanvas;
