import { Node, Edge } from 'reactflow';
import { N8nNodeData } from '../components/N8nNode';
import { N8nWorkflowConverter } from './n8nConverter';

interface N8nConfig {
  baseUrl: string;
  apiKey?: string;
  username?: string;
  password?: string;
}

interface N8nCredential {
  id: string;
  name: string;
  type: string;
}

interface N8nWorkflowResponse {
  id: string;
  name: string;
  active: boolean;
  createdAt: string;
  updatedAt: string;
}

export class N8nApiClient {
  private config: N8nConfig;
  private converter: N8nWorkflowConverter;

  constructor(config: N8nConfig, nodes: Node<N8nNodeData>[], edges: Edge[]) {
    this.config = config;
    this.converter = new N8nWorkflowConverter(nodes, edges);
  }

  private async makeRequest(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<any> {
    const url = `${this.config.baseUrl}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    };

    // Authentication
    if (this.config.apiKey) {
      headers['X-N8N-API-KEY'] = this.config.apiKey;
    } else if (this.config.username && this.config.password) {
      const auth = btoa(`${this.config.username}:${this.config.password}`);
      headers['Authorization'] = `Basic ${auth}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`n8n API Error: ${response.status} - ${errorText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw new Error(`Failed to connect to n8n: ${error.message}`);
      }
      throw error;
    }
  }

  async testConnection(): Promise<boolean> {
    try {
      await this.makeRequest('/workflows', { method: 'GET' });
      return true;
    } catch {
      return false;
    }
  }

  async deployWorkflow(): Promise<N8nWorkflowResponse> {
    const workflow = this.converter.convert();
    
    try {
      // First, create the workflow
      const response = await this.makeRequest('/workflows', {
        method: 'POST',
        body: JSON.stringify(workflow),
      });

      return response;
    } catch (error) {
      throw new Error(`Failed to deploy workflow: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async activateWorkflow(workflowId: string): Promise<void> {
    try {
      await this.makeRequest(`/workflows/${workflowId}/activate`, {
        method: 'POST',
      });
    } catch (error) {
      throw new Error(`Failed to activate workflow: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getWorkflows(): Promise<N8nWorkflowResponse[]> {
    try {
      const response = await this.makeRequest('/workflows', { method: 'GET' });
      return response.data || [];
    } catch (error) {
      throw new Error(`Failed to fetch workflows: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async deleteWorkflow(workflowId: string): Promise<void> {
    try {
      await this.makeRequest(`/workflows/${workflowId}`, {
        method: 'DELETE',
      });
    } catch (error) {
      throw new Error(`Failed to delete workflow: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getCredentials(): Promise<N8nCredential[]> {
    try {
      const response = await this.makeRequest('/credentials', { method: 'GET' });
      return response.data || [];
    } catch (error) {
      throw new Error(`Failed to fetch credentials: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async createCredential(credentialData: any): Promise<N8nCredential> {
    try {
      const response = await this.makeRequest('/credentials', {
        method: 'POST',
        body: JSON.stringify(credentialData),
      });
      return response;
    } catch (error) {
      throw new Error(`Failed to create credential: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async executeWorkflow(workflowId: string, data?: any): Promise<any> {
    try {
      const response = await this.makeRequest(`/workflows/${workflowId}/execute`, {
        method: 'POST',
        body: JSON.stringify({ data: data || {} }),
      });
      return response;
    } catch (error) {
      throw new Error(`Failed to execute workflow: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getExecutionHistory(workflowId: string): Promise<any[]> {
    try {
      const response = await this.makeRequest(`/executions?workflowId=${workflowId}`, {
        method: 'GET',
      });
      return response.data || [];
    } catch (error) {
      throw new Error(`Failed to fetch execution history: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  generateWebhookUrls(): string[] {
    const webhookNodes = this.converter['nodes'].filter(n => 
      n.data.nodeType === 'trigger' && 
      n.data.label.toLowerCase().includes('webhook')
    );

    return webhookNodes.map(node => 
      `${this.config.baseUrl}/webhook/nodex-${node.id}`
    );
  }
}

// Hook for React components to use n8n API
export const useN8nApi = (config: N8nConfig, nodes: Node<N8nNodeData>[], edges: Edge[]) => {
  const client = new N8nApiClient(config, nodes, edges);

  return {
    client,
    testConnection: () => client.testConnection(),
    deployWorkflow: () => client.deployWorkflow(),
    activateWorkflow: (id: string) => client.activateWorkflow(id),
    getWorkflows: () => client.getWorkflows(),
    deleteWorkflow: (id: string) => client.deleteWorkflow(id),
    getCredentials: () => client.getCredentials(),
    executeWorkflow: (id: string, data?: any) => client.executeWorkflow(id, data),
    getExecutionHistory: (id: string) => client.getExecutionHistory(id),
    generateWebhookUrls: () => client.generateWebhookUrls(),
  };
};

// Default configurations for common n8n setups
export const N8N_CONFIGS = {
  local: {
    baseUrl: 'http://localhost:5678/api/v1',
  },
  cloud: {
    baseUrl: 'https://app.n8n.cloud/api/v1',
  },
  custom: (url: string) => ({
    baseUrl: `${url}/api/v1`,
  }),
};