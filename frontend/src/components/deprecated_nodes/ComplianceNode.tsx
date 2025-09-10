import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Shield, Lock } from 'lucide-react';

interface ComplianceNodeData {
    label: string;
    description?: string;
    compliance_type: string;
    locked: boolean;
    standard?: string;
}

const ComplianceNode: React.FC<NodeProps<ComplianceNodeData>> = ({ data, selected }) => {
    const getComplianceColor = (type: string) => {
        switch (type.toLowerCase()) {
            case 'hipaa':
            case 'hipaa_phi_redaction':
                return 'bg-red-100 border-red-500 text-red-800';
            case 'pci_dss':
                return 'bg-orange-100 border-orange-500 text-orange-800';
            case 'sox':
                return 'bg-purple-100 border-purple-500 text-purple-800';
            case 'fisma':
                return 'bg-blue-100 border-blue-500 text-blue-800';
            case 'ferpa':
                return 'bg-green-100 border-green-500 text-green-800';
            default:
                return 'bg-red-100 border-red-500 text-red-800';
        }
    };

    const getStandardLabel = (type: string) => {
        switch (type.toLowerCase()) {
            case 'hipaa':
            case 'hipaa_phi_redaction':
                return 'HIPAA';
            case 'pci_dss':
                return 'PCI-DSS';
            case 'sox':
                return 'SOX';
            case 'fisma':
                return 'FISMA';
            case 'ferpa':
                return 'FERPA';
            default:
                return 'COMPLIANCE';
        }
    };

    return (
        <div className={`
      relative min-w-[200px] rounded-lg border-2 shadow-lg
      ${getComplianceColor(data.compliance_type)}
      ${selected ? 'ring-2 ring-blue-400' : ''}
      transition-all duration-200
    `}>
            {/* Compliance Badge */}
            <div className="absolute -top-2 -right-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full flex items-center space-x-1">
                <Shield className="w-3 h-3" />
                <span>{getStandardLabel(data.compliance_type)}</span>
            </div>

            {/* Lock Icon for Non-deletable */}
            <div className="absolute -top-2 -left-2 bg-gray-700 text-white p-1 rounded-full">
                <Lock className="w-3 h-3" />
            </div>

            {/* Node Content */}
            <div className="p-4">
                <div className="flex items-center space-x-2 mb-2">
                    <Shield className="w-5 h-5" />
                    <h3 className="font-semibold text-sm">{data.label}</h3>
                </div>

                {data.description && (
                    <p className="text-xs opacity-80 mb-2">{data.description}</p>
                )}

                {data.standard && (
                    <div className="text-xs font-medium opacity-90">
                        Standard: {data.standard}
                    </div>
                )}
            </div>

            {/* Connection Handles */}
            <Handle
                type="target"
                position={Position.Top}
                className="w-3 h-3 bg-red-500 border-2 border-white"
            />
            <Handle
                type="source"
                position={Position.Bottom}
                className="w-3 h-3 bg-red-500 border-2 border-white"
            />

            {/* Warning Message on Hover */}
            <div className="absolute inset-0 bg-red-500 bg-opacity-90 text-white text-xs p-2 rounded-lg opacity-0 hover:opacity-100 transition-opacity duration-200 flex items-center justify-center text-center">
                <div>
                    <Lock className="w-4 h-4 mx-auto mb-1" />
                    <div>Protected Compliance Node</div>
                    <div className="text-xs opacity-80">Cannot be deleted</div>
                </div>
            </div>
        </div>
    );
};

export default ComplianceNode;
