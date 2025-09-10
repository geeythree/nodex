import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Flag, CheckCircle } from 'lucide-react';

interface OutputNodeData {
    label: string;
    description?: string;
    output_type?: string;
}

const OutputNode: React.FC<NodeProps<OutputNodeData>> = ({ data, selected }) => {
    return (
        <div className={`
      relative min-w-[160px] bg-blue-50 rounded-lg border-2 border-blue-400 shadow-md
      ${selected ? 'ring-2 ring-blue-400' : ''}
      hover:shadow-lg transition-all duration-200
    `}>
            {/* End Badge */}
            <div className="absolute -top-2 -right-2 bg-blue-500 text-white text-xs px-2 py-1 rounded-full flex items-center space-x-1">
                <Flag className="w-3 h-3" />
                <span>END</span>
            </div>

            {/* Node Content */}
            <div className="p-4">
                <div className="flex items-center space-x-2 mb-2">
                    <CheckCircle className="w-4 h-4 text-blue-600" />
                    <h3 className="font-semibold text-sm text-blue-800">{data.label}</h3>
                </div>

                {data.description && (
                    <p className="text-xs text-blue-700 mb-2">{data.description}</p>
                )}

                {data.output_type && (
                    <div className="text-xs font-medium text-blue-600">
                        Type: {data.output_type}
                    </div>
                )}
            </div>

            {/* Connection Handle - Only target */}
            <Handle
                type="target"
                position={Position.Top}
                className="w-3 h-3 bg-blue-500 border-2 border-white"
            />
        </div>
    );
};

export default OutputNode;
