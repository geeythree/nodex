import { Node, Edge } from 'reactflow';
import { N8nNodeData } from '../components/N8nNode';

interface OpenHandsConfig {
  baseUrl: string; // OpenHands Cloud API or local instance
  apiKey?: string;
  model?: string; // GPT-4, Claude, etc.
}

interface OpenHandsConversation {
  id: string;
  title: string;
  status: 'created' | 'in_progress' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
}

interface OpenHandsTask {
  nodeId: string;
  nodeType: string;
  label: string;
  description: string;
  connections: string[];
  code_prompt: string;
  language: 'python' | 'nodejs' | 'go' | 'java';
  framework: 'fastapi' | 'express' | 'gin' | 'spring';
}

interface GeneratedAPI {
  nodeId: string;
  endpoint: string;
  method: string;
  code: string;
  dockerfile?: string;
  tests?: string;
  documentation?: string;
  dependencies: string[];
}

export class OpenHandsApiClient {
  private config: OpenHandsConfig;
  private nodes: Node<N8nNodeData>[];
  private edges: Edge[];

  constructor(config: OpenHandsConfig, nodes: Node<N8nNodeData>[], edges: Edge[]) {
    this.config = config;
    this.nodes = nodes;
    this.edges = edges;
  }

  private async makeRequest(endpoint: string, options: RequestInit = {}): Promise<any> {
    const url = `${this.config.baseUrl}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    };

    if (this.config.apiKey) {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`OpenHands API Error: ${response.status} - ${errorText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(`Failed to connect to OpenHands: ${error.message}`);
      }
      throw error;
    }
  }

  async testConnection(): Promise<boolean> {
    try {
      await this.makeRequest('/conversations', { method: 'GET' });
      return true;
    } catch {
      return false;
    }
  }

  async generateAPIsFromWorkflow(): Promise<{
    conversationId: string;
    apis: GeneratedAPI[];
    orchestrator: {
      code: string;
      dockerfile: string;
      deployment: any;
    };
  }> {
    // Step 1: Create conversation with OpenHands
    const conversation = await this.createConversation();
    
    // Step 2: Analyze workflow and generate tasks
    const tasks = this.analyzeWorkflowNodes();
    
    // Step 3: Generate APIs for each node
    const apis: GeneratedAPI[] = [];
    for (const task of tasks) {
      const api = await this.generateAPIForNode(conversation.id, task);
      apis.push(api);
    }
    
    // Step 4: Generate orchestrator service
    const orchestrator = await this.generateOrchestrator(conversation.id, tasks, apis);
    
    return {
      conversationId: conversation.id,
      apis,
      orchestrator
    };
  }

  private async createConversation(): Promise<OpenHandsConversation> {
    const workflowName = `nodex-workflow-${Date.now()}`;
    
    return await this.makeRequest('/conversations', {
      method: 'POST',
      body: JSON.stringify({
        title: workflowName,
        model: this.config.model || 'gpt-4-turbo',
        initial_message: this.generateInitialPrompt()
      })
    });
  }

  private generateInitialPrompt(): string {
    const nodeCount = this.nodes.length;
    const edgeCount = this.edges.length;
    
    return `I need to convert a visual workflow with ${nodeCount} nodes and ${edgeCount} connections into a microservices architecture with REST APIs.

WORKFLOW OVERVIEW:
- Nodes represent different operations (triggers, actions, conditions, validations)
- Edges represent data flow between operations
- Need to generate individual API services for each node
- Need an orchestrator service to manage the workflow execution

REQUIREMENTS:
- Generate FastAPI services for Python or Express.js for Node.js
- Include proper error handling, logging, and monitoring
- Create Docker containers for each service
- Generate docker-compose.yml for local development
- Include unit tests and API documentation
- Implement secure inter-service communication

Please confirm you understand and are ready to generate the microservices architecture.`;
  }

  private analyzeWorkflowNodes(): OpenHandsTask[] {
    return this.nodes.map(node => {
      const connections = this.edges
        .filter(edge => edge.source === node.id)
        .map(edge => this.nodes.find(n => n.id === edge.target)?.data.label || 'unknown');

      return {
        nodeId: node.id,
        nodeType: node.data.nodeType,
        label: node.data.label,
        description: node.data.description || '',
        connections,
        code_prompt: this.generateCodePrompt(node),
        language: this.determineLanguage(node),
        framework: this.determineFramework(node)
      };
    });
  }

  private generateCodePrompt(node: Node<N8nNodeData>): string {
    const { nodeType, label, description } = node.data;
    
    const basePrompt = `Generate a ${this.determineFramework(node)} API service for:
NODE TYPE: ${nodeType}
LABEL: ${label}
DESCRIPTION: ${description}

REQUIREMENTS:
- Create REST API endpoint with appropriate HTTP method
- Include request/response models with Pydantic or TypeScript interfaces
- Add proper error handling and status codes
- Include logging and monitoring hooks
- Add input validation and sanitization
- Generate unit tests
- Create Dockerfile for containerization
- Include API documentation (OpenAPI/Swagger)
`;

    switch (nodeType) {
      case 'trigger':
        return basePrompt + `
SPECIFIC REQUIREMENTS FOR TRIGGER:
- Create webhook endpoint that accepts POST requests
- Store incoming data in queue/database for processing
- Return immediate acknowledgment to caller
- Trigger next services in workflow chain
- Handle authentication if required
`;

      case 'action':
        return basePrompt + `
SPECIFIC REQUIREMENTS FOR ACTION:
- Create endpoint that processes input data
- Implement the business logic for: ${label}
- Call external APIs if needed (provide configuration)
- Transform data according to requirements
- Pass results to next service in chain
- Handle retries and timeouts
`;

      case 'condition':
        return basePrompt + `
SPECIFIC REQUIREMENTS FOR CONDITION:
- Create endpoint that evaluates boolean conditions
- Return different responses based on condition result
- Support multiple condition types (equals, contains, greater than, etc.)
- Route to different services based on result
- Log decision outcomes for debugging
`;

      case 'validation':
        return basePrompt + `
SPECIFIC REQUIREMENTS FOR VALIDATION:
- Create endpoint that validates input data
- Implement schema validation rules
- Return detailed error messages for invalid data
- Support multiple validation rules
- Allow data through on success, reject on failure
`;

      case 'notification':
        return basePrompt + `
SPECIFIC REQUIREMENTS FOR NOTIFICATION:
- Create endpoint that sends notifications
- Support multiple channels (email, slack, webhook, etc.)
- Template support for notification content
- Delivery confirmation and retry logic
- Rate limiting to prevent spam
`;

      default:
        return basePrompt + `
SPECIFIC REQUIREMENTS FOR CUSTOM NODE:
- Implement the functionality described in: ${description}
- Create appropriate API interface
- Handle input/output data transformation
- Add custom business logic as needed
`;
    }
  }

  private determineLanguage(node: Node<N8nNodeData>): 'python' | 'nodejs' | 'go' | 'java' {
    const { nodeType, label } = node.data;
    
    // AI/ML nodes prefer Python
    if (label.toLowerCase().includes('ai') || 
        label.toLowerCase().includes('llm') || 
        label.toLowerCase().includes('ml')) {
      return 'python';
    }
    
    // High-performance nodes prefer Go
    if (nodeType === 'condition' || label.toLowerCase().includes('performance')) {
      return 'go';
    }
    
    // Default to Python for most use cases
    return 'python';
  }

  private determineFramework(node: Node<N8nNodeData>): 'fastapi' | 'express' | 'gin' | 'spring' {
    const language = this.determineLanguage(node);
    
    switch (language) {
      case 'python':
        return 'fastapi';
      case 'nodejs':
        return 'express';
      case 'go':
        return 'gin';
      case 'java':
        return 'spring';
      default:
        return 'fastapi';
    }
  }

  private async generateAPIForNode(conversationId: string, task: OpenHandsTask): Promise<GeneratedAPI> {
    // Send detailed prompt to OpenHands for this specific node
    await this.makeRequest(`/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify({
        content: task.code_prompt,
        role: 'user'
      })
    });

    // Wait for OpenHands to complete the task
    await this.waitForCompletion(conversationId);

    // Extract generated code from conversation
    const conversation = await this.makeRequest(`/conversations/${conversationId}`);
    const generatedCode = this.extractCodeFromConversation(conversation);

    return {
      nodeId: task.nodeId,
      endpoint: this.generateEndpoint(task),
      method: this.determineHttpMethod(task.nodeType),
      code: generatedCode.main,
      dockerfile: generatedCode.dockerfile,
      tests: generatedCode.tests,
      documentation: generatedCode.docs,
      dependencies: this.extractDependencies(generatedCode.main)
    };
  }

  private generateEndpoint(task: OpenHandsTask): string {
    return `/${task.nodeType}/${task.label.toLowerCase().replace(/\s+/g, '-')}`;
  }

  private determineHttpMethod(nodeType: string): string {
    switch (nodeType) {
      case 'trigger':
        return 'POST'; // Webhooks typically use POST
      case 'action':
        return 'POST'; // Actions process data
      case 'condition':
        return 'GET';  // Conditions evaluate data
      case 'validation':
        return 'POST'; // Validation processes data
      case 'notification':
        return 'POST'; // Notifications send data
      default:
        return 'POST';
    }
  }

  private async generateOrchestrator(
    conversationId: string, 
    tasks: OpenHandsTask[], 
    apis: GeneratedAPI[]
  ): Promise<{
    code: string;
    dockerfile: string;
    deployment: any;
  }> {
    const orchestratorPrompt = `Generate an orchestrator service that manages the workflow execution:

WORKFLOW DETAILS:
${tasks.map(task => `- ${task.nodeType}: ${task.label} (${task.connections.join(', ')})`).join('\n')}

GENERATED APIS:
${apis.map(api => `- ${api.method} ${api.endpoint} (Node: ${api.nodeId})`).join('\n')}

ORCHESTRATOR REQUIREMENTS:
- FastAPI service that manages workflow execution
- Accept initial webhook/trigger requests
- Route data through the workflow based on connections
- Handle parallel and sequential execution
- Implement retry logic and error handling
- Store execution state and logs
- Provide workflow status API
- Create docker-compose.yml for all services
- Include monitoring and health checks
- Generate deployment manifests for Kubernetes

Please create the complete orchestrator service with all supporting files.`;

    await this.makeRequest(`/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify({
        content: orchestratorPrompt,
        role: 'user'
      })
    });

    await this.waitForCompletion(conversationId);

    const conversation = await this.makeRequest(`/conversations/${conversationId}`);
    const orchestratorCode = this.extractCodeFromConversation(conversation);

    return {
      code: orchestratorCode.main,
      dockerfile: orchestratorCode.dockerfile,
      deployment: orchestratorCode.deployment
    };
  }

  private async waitForCompletion(conversationId: string): Promise<void> {
    let attempts = 0;
    const maxAttempts = 30; // 5 minutes max
    
    while (attempts < maxAttempts) {
      const conversation = await this.makeRequest(`/conversations/${conversationId}`);
      
      if (conversation.status === 'completed') {
        return;
      }
      
      if (conversation.status === 'failed') {
        throw new Error('OpenHands task failed');
      }
      
      await new Promise(resolve => setTimeout(resolve, 10000)); // Wait 10 seconds
      attempts++;
    }
    
    throw new Error('OpenHands task timed out');
  }

  private extractCodeFromConversation(conversation: any): {
    main: string;
    dockerfile: string;
    tests: string;
    docs: string;
    deployment?: any;
  } {
    // This would parse the conversation messages to extract generated code
    // For now, return a placeholder structure
    return {
      main: '# Generated code will be extracted here',
      dockerfile: '# Generated Dockerfile',
      tests: '# Generated tests',
      docs: '# Generated documentation',
      deployment: {}
    };
  }

  private extractDependencies(code: string): string[] {
    // Extract dependencies from generated code
    const dependencies: string[] = [];
    
    // Python imports
    const pythonImports = code.match(/from\s+(\w+)|import\s+(\w+)/g);
    if (pythonImports) {
      pythonImports.forEach(imp => {
        const match = imp.match(/from\s+(\w+)|import\s+(\w+)/);
        if (match) {
          dependencies.push(match[1] || match[2]);
        }
      });
    }
    
    return [...new Set(dependencies)];
  }

  // Deployment helpers
  async deployToLocal(): Promise<string> {
    return 'docker-compose up -d';
  }

  async deployToCloud(provider: 'aws' | 'gcp' | 'azure'): Promise<{
    commands: string[];
    urls: string[];
  }> {
    return {
      commands: [`kubectl apply -f deployment-${provider}.yml`],
      urls: ['https://your-workflow.cloud.provider.com']
    };
  }

  generateDeploymentInstructions(): any {
    return {
      title: "Deploy with OpenHands",
      steps: [
        {
          step: 1,
          title: "Connect to OpenHands",
          description: "Configure OpenHands API connection",
          action: "Set up API key and endpoint"
        },
        {
          step: 2,
          title: "Generate APIs",
          description: "AI generates microservices for each node",
          action: "Click 'Generate APIs' to start code generation"
        },
        {
          step: 3,
          title: "Review Code",
          description: "Review generated APIs and orchestrator",
          action: "Inspect code quality and make adjustments"
        },
        {
          step: 4,
          title: "Deploy Services",
          description: "Deploy to local or cloud environment",
          action: "Choose deployment target and execute"
        },
        {
          step: 5,
          title: "Monitor Workflow",
          description: "Track workflow execution and performance",
          action: "Use provided monitoring dashboards"
        }
      ],
      advantages: [
        "AI-generated, production-ready code",
        "Full microservices architecture",
        "Automatic testing and documentation",
        "Scalable and maintainable deployment",
        "Custom business logic implementation"
      ]
    };
  }
}

// Hook for React components
export const useOpenHandsApi = (config: OpenHandsConfig, nodes: Node<N8nNodeData>[], edges: Edge[]) => {
  const client = new OpenHandsApiClient(config, nodes, edges);

  return {
    client,
    testConnection: () => client.testConnection(),
    generateAPIs: () => client.generateAPIsFromWorkflow(),
    deployLocal: () => client.deployToLocal(),
    deployCloud: (provider: 'aws' | 'gcp' | 'azure') => client.deployToCloud(provider),
    getInstructions: () => client.generateDeploymentInstructions(),
  };
};

// Default configurations
export const OPENHANDS_CONFIGS = {
  cloud: {
    baseUrl: 'https://api.all-hands.dev/v1',
  },
  local: {
    baseUrl: 'http://localhost:3000/api',
  },
  custom: (url: string) => ({
    baseUrl: `${url}/api`,
  }),
};