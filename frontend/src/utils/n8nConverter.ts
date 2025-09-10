import { Node, Edge } from 'reactflow';
import { N8nNodeData } from '../components/N8nNode';

// n8n node type mappings
const N8N_NODE_MAPPINGS = {
  trigger: {
    webhook: 'n8n-nodes-base.webhook',
    schedule: 'n8n-nodes-base.cron',
    manual: 'n8n-nodes-base.manualTrigger'
  },
  action: {
    http_request: 'n8n-nodes-base.httpRequest',
    email: 'n8n-nodes-base.emailSend',
    database: 'n8n-nodes-base.postgres',
    llm_call: 'n8n-nodes-base.openAi',
    code: 'n8n-nodes-base.code'
  },
  condition: 'n8n-nodes-base.if',
  validation: 'n8n-nodes-base.function',
  notification: 'n8n-nodes-base.slack',
  audit: 'n8n-nodes-base.function'
};

interface N8nWorkflow {
  name: string;
  nodes: N8nNode[];
  connections: N8nConnections;
  active: boolean;
  settings: any;
  staticData: any;
}

interface N8nNode {
  id: string;
  name: string;
  type: string;
  typeVersion: number;
  position: [number, number];
  parameters: any;
  webhookId?: string;
  credentials?: any;
}

interface N8nConnections {
  [key: string]: {
    main: Array<Array<{ node: string; type: string; index: number }>>;
  };
}

export class N8nWorkflowConverter {
  private nodes: Node<N8nNodeData>[];
  private edges: Edge[];

  constructor(nodes: Node<N8nNodeData>[], edges: Edge[]) {
    this.nodes = nodes;
    this.edges = edges;
  }

  convert(): N8nWorkflow {
    const n8nNodes = this.convertNodes();
    const connections = this.convertConnections();

    return {
      name: this.generateWorkflowName(),
      nodes: n8nNodes,
      connections,
      active: false, // User will activate manually
      settings: {
        executionOrder: 'v1'
      },
      staticData: {}
    };
  }

  private generateWorkflowName(): string {
    const triggerNode = this.nodes.find(n => n.data.nodeType === 'trigger');
    const timestamp = new Date().toISOString().split('T')[0];
    
    if (triggerNode) {
      return `${triggerNode.data.label} - ${timestamp}`;
    }
    
    return `Nodex Workflow - ${timestamp}`;
  }

  private convertNodes(): N8nNode[] {
    return this.nodes.map(node => this.convertNode(node));
  }

  private convertNode(node: Node<N8nNodeData>): N8nNode {
    const baseNode: N8nNode = {
      id: node.id,
      name: node.data.label,
      type: this.getN8nNodeType(node),
      typeVersion: 1,
      position: [node.position.x, node.position.y],
      parameters: this.getNodeParameters(node)
    };

    // Add webhook-specific properties
    if (node.data.nodeType === 'trigger' && 
        node.data.label.toLowerCase().includes('webhook')) {
      baseNode.webhookId = this.generateWebhookId();
      baseNode.parameters = {
        ...baseNode.parameters,
        httpMethod: 'POST',
        path: `nodex-${node.id}`,
        responseMode: 'onReceived',
        responseData: '{ "success": true, "message": "Workflow triggered" }'
      };
    }

    return baseNode;
  }

  private getN8nNodeType(node: Node<N8nNodeData>): string {
    const { nodeType } = node.data;
    
    // Handle triggers
    if (nodeType === 'trigger') {
      if (node.data.label.toLowerCase().includes('webhook')) {
        return N8N_NODE_MAPPINGS.trigger.webhook;
      } else if (node.data.label.toLowerCase().includes('schedule')) {
        return N8N_NODE_MAPPINGS.trigger.schedule;
      }
      return N8N_NODE_MAPPINGS.trigger.manual;
    }

    // Handle actions
    if (nodeType === 'action') {
      const label = node.data.label.toLowerCase();
      
      if (label.includes('llm') || label.includes('ai') || label.includes('gpt')) {
        return N8N_NODE_MAPPINGS.action.llm_call;
      } else if (label.includes('email')) {
        return N8N_NODE_MAPPINGS.action.email;
      } else if (label.includes('database') || label.includes('db')) {
        return N8N_NODE_MAPPINGS.action.database;
      } else if (label.includes('http') || label.includes('api')) {
        return N8N_NODE_MAPPINGS.action.http_request;
      }
      
      return N8N_NODE_MAPPINGS.action.code; // Default to code node for custom logic
    }

    // Handle conditions
    if (nodeType === 'condition') {
      return N8N_NODE_MAPPINGS.condition;
    }

    // Handle notifications
    if (nodeType === 'notification') {
      return N8N_NODE_MAPPINGS.notification;
    }

    // Default to function node
    return 'n8n-nodes-base.function';
  }

  private getNodeParameters(node: Node<N8nNodeData>): any {
    const { nodeType } = node.data;

    switch (nodeType) {
      case 'trigger':
        return this.getTriggerParameters(node);
      
      case 'action':
        return this.getActionParameters(node);
      
      case 'condition':
        return this.getConditionParameters(node);
      
      case 'validation':
        return this.getValidationParameters(node);

      default:
        return {
          functionCode: `// ${node.data.label}\nreturn items;`
        };
    }
  }

  private getTriggerParameters(node: Node<N8nNodeData>): any {
    const label = node.data.label.toLowerCase();

    if (label.includes('webhook')) {
      return {
        httpMethod: 'POST',
        path: `nodex-${node.id}`,
        responseMode: 'onReceived'
      };
    }

    if (label.includes('schedule')) {
      return {
        rule: {
          interval: [{
            field: 'cronExpression',
            cronExpression: '0 9 * * *' // Default: daily at 9am
          }]
        }
      };
    }

    // Manual trigger
    return {};
  }

  private getActionParameters(node: Node<N8nNodeData>): any {
    const label = node.data.label.toLowerCase();
    const description = node.data.description || '';

    if (label.includes('llm') || label.includes('ai') || label.includes('gpt')) {
      return {
        resource: 'chat',
        operation: 'create',
        model: 'gpt-4',
        messages: {
          values: [{
            role: 'user',
            content: `=${description || 'Process the input data: {{ $json }}'}`
          }]
        },
        options: {
          temperature: 0.7,
          maxTokens: 1000
        }
      };
    }

    if (label.includes('email')) {
      return {
        fromEmail: '={{$node["Trigger"].json["email"] || "noreply@example.com"}}',
        toEmail: '={{$node["Trigger"].json["recipient"] || "user@example.com"}}',
        subject: `=${label}`,
        message: `=${description || 'Automated message from Nodex workflow'}`,
        format: 'html'
      };
    }

    if (label.includes('database') || label.includes('db')) {
      return {
        operation: 'insert',
        schema: 'public',
        table: 'workflow_data',
        columns: 'data, timestamp',
        values: '={{$json}}, {{new Date().toISOString()}}'
      };
    }

    if (label.includes('http') || label.includes('api')) {
      return {
        method: 'POST',
        url: 'https://api.example.com/webhook',
        sendBody: true,
        bodyContentType: 'json',
        jsonBody: '={{$json}}',
        options: {}
      };
    }

    // Default code node
    return {
      functionCode: `// ${label}\n// ${description}\nreturn items.map(item => {\n  // Process item here\n  return item.json;\n});`
    };
  }

  private getConditionParameters(_node: Node<N8nNodeData>): any {
    return {
      conditions: {
        boolean: [{
          value1: '={{$json.status}}',
          operation: 'equal',
          value2: 'success'
        }]
      }
    };
  }

  private getValidationParameters(node: Node<N8nNodeData>): any {
    return {
      functionCode: `// Validation: ${node.data.label}
// ${node.data.description}

const errors = [];

for (const item of items) {
  const data = item.json;
  
  // Add validation logic here
  if (!data.email) {
    errors.push('Email is required');
  }
  
  if (!data.name) {
    errors.push('Name is required');
  }
}

if (errors.length > 0) {
  throw new Error('Validation failed: ' + errors.join(', '));
}

return items;`
    };
  }

  private convertConnections(): N8nConnections {
    const connections: N8nConnections = {};

    // Initialize connections for all nodes
    this.nodes.forEach(node => {
      connections[node.data.label] = {
        main: [[]]
      };
    });

    // Add edge connections
    this.edges.forEach(edge => {
      const sourceNode = this.nodes.find(n => n.id === edge.source);
      const targetNode = this.nodes.find(n => n.id === edge.target);

      if (sourceNode && targetNode) {
        const sourceLabel = sourceNode.data.label;
        
        if (!connections[sourceLabel]) {
          connections[sourceLabel] = { main: [[]] };
        }

        connections[sourceLabel].main[0].push({
          node: targetNode.data.label,
          type: 'main',
          index: 0
        });
      }
    });

    return connections;
  }

  private generateWebhookId(): string {
    return 'nodex-' + Math.random().toString(36).substr(2, 9);
  }

  // Generate deployment instructions
  generateDeploymentInstructions(): any {
    const workflow = this.convert();
    
    return {
      workflow,
      instructions: {
        title: "Deploy to n8n",
        steps: [
          {
            step: 1,
            title: "Set up n8n",
            description: "Install and run n8n instance",
            commands: [
              "npm install n8n -g",
              "n8n start"
            ],
            notes: "n8n will be available at http://localhost:5678"
          },
          {
            step: 2,
            title: "Import Workflow",
            description: "Copy the workflow JSON and import to n8n",
            action: "Go to n8n → Click '+' → 'Import from JSON' → Paste workflow"
          },
          {
            step: 3,
            title: "Configure Credentials",
            description: "Set up API keys and credentials",
            credentials: this.getRequiredCredentials()
          },
          {
            step: 4,
            title: "Activate Workflow",
            description: "Turn on the workflow to start processing",
            action: "Toggle the workflow switch to 'Active'"
          },
          {
            step: 5,
            title: "Test Workflow",
            description: "Send a test request to verify it works",
            testEndpoints: this.generateTestEndpoints()
          }
        ],
        cloudOptions: [
          {
            name: "n8n Cloud",
            url: "https://n8n.cloud",
            description: "Managed n8n hosting"
          },
          {
            name: "Railway",
            url: "https://railway.app",
            description: "Deploy n8n with one-click"
          }
        ]
      }
    };
  }

  private getRequiredCredentials(): string[] {
    const credentials: string[] = [];
    
    this.nodes.forEach(node => {
      const label = node.data.label.toLowerCase();
      
      if (label.includes('llm') || label.includes('ai') || label.includes('gpt')) {
        credentials.push('OpenAI API Key');
      }
      if (label.includes('email')) {
        credentials.push('SMTP/Email Credentials');
      }
      if (label.includes('database')) {
        credentials.push('Database Connection');
      }
    });

    return Array.from(new Set(credentials)); // Remove duplicates
  }

  private generateTestEndpoints(): any[] {
    const webhookNodes = this.nodes.filter(n => 
      n.data.nodeType === 'trigger' && 
      n.data.label.toLowerCase().includes('webhook')
    );

    return webhookNodes.map(node => ({
      method: 'POST',
      url: `http://localhost:5678/webhook/nodex-${node.id}`,
      body: {
        test: 'data',
        timestamp: new Date().toISOString()
      },
      description: `Test endpoint for ${node.data.label}`
    }));
  }
}

// Quick conversion function
export const convertToN8n = (nodes: Node<N8nNodeData>[], edges: Edge[]) => {
  const converter = new N8nWorkflowConverter(nodes, edges);
  return converter.generateDeploymentInstructions();
};