import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Play, ArrowRight } from 'lucide-react';

interface InputNodeData {
    label: string;
    description?: string;
    input_type?: string;
}

const InputNode: React.FC<NodeProps<InputNodeData>> = ({ data, selected }) => {
    return (
        <div className={`
      relative min-w-[160px] bg-green-50 rounded-lg border-2 border-green-400 shadow-md
      ${selected ? 'ring-2 ring-blue-400' : ''}
      hover:shadow-lg transition-all duration-200
    `}>
            {/* Start Badge */}
            <div className="absolute -top-2 -left-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full flex items-center space-x-1">
                <Play className="w-3 h-3" />
                <span>START</span>
            </div>

            {/* Node Content */}
            <div className="p-4">
                <div className="flex items-center space-x-2 mb-2">
                    <ArrowRight className="w-4 h-4 text-green-600" />
                    <h3 className="font-semibold text-sm text-green-800">{data.label}</h3>
                </div>

                {data.description && (
                    <p className="text-xs text-green-700 mb-2">{data.description}</p>
                )}

                {data.input_type && (
                    <div className="text-xs font-medium text-green-600">
                        Type: {data.input_type}
                    </div>
                )}
            </div>

            {/* Connection Handle - Only source */}
            <Handle
                type="source"
                position={Position.Bottom}
                className="w-3 h-3 bg-green-500 border-2 border-white"
            />
        </div>
    );
};

export default InputNode;
