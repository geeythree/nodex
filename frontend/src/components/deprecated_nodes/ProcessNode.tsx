import React from 'react';
import { Handle, Position, NodeProps, useReactFlow } from 'reactflow';
import { Settings, Edit3, Trash2 } from 'lucide-react';

interface ProcessNodeData {
    label: string;
    description?: string;
    locked?: boolean;
}

const ProcessNode: React.FC<NodeProps<ProcessNodeData>> = ({ data, selected, id }) => {
    const { setNodes, setEdges } = useReactFlow();

    const handleEdit = (e: React.MouseEvent) => {
        e.stopPropagation();
        const newLabel = prompt('Edit node label:', data.label);
        if (newLabel && newLabel !== data.label) {
            setNodes((nodes) =>
                nodes.map((node) =>
                    node.id === id
                        ? { ...node, data: { ...node.data, label: newLabel } }
                        : node
                )
            );
        }
    };

    const handleDelete = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (confirm('Are you sure you want to delete this node?')) {
            setNodes((nodes) => nodes.filter((node) => node.id !== id));
            setEdges((edges) => edges.filter((edge) => edge.source !== id && edge.target !== id));
        }
    };

    return (
        <div className={`
      relative min-w-[180px] bg-white rounded-lg border-2 border-gray-300 shadow-md
      ${selected ? 'ring-2 ring-blue-400 border-blue-400' : ''}
      hover:shadow-lg transition-all duration-200
    `}>
            {/* Node Content */}
            <div className="p-4">
                <div className="flex items-center space-x-2 mb-2">
                    <Settings className="w-4 h-4 text-gray-600" />
                    <h3 className="font-semibold text-sm text-gray-800">{data.label}</h3>
                </div>

                {data.description && (
                    <p className="text-xs text-gray-600 mb-2">{data.description}</p>
                )}
            </div>

            {/* Action Buttons */}
            {selected && !data.locked && (
                <div className="absolute -top-2 -right-2 flex space-x-1">
                    <button
                        onClick={handleEdit}
                        className="bg-blue-500 text-white p-1 rounded-full hover:bg-blue-600 transition-colors"
                        title="Edit node"
                    >
                        <Edit3 className="w-3 h-3" />
                    </button>
                    <button
                        onClick={handleDelete}
                        className="bg-red-500 text-white p-1 rounded-full hover:bg-red-600 transition-colors"
                        title="Delete node"
                    >
                        <Trash2 className="w-3 h-3" />
                    </button>
                </div>
            )}

            {/* Connection Handles */}
            <Handle
                type="target"
                position={Position.Top}
                className="w-3 h-3 bg-gray-400 border-2 border-white"
            />
            <Handle
                type="source"
                position={Position.Bottom}
                className="w-3 h-3 bg-gray-400 border-2 border-white"
            />
        </div>
    );
};

export default ProcessNode;
