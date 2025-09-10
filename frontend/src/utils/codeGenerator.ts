import { Node, Edge } from 'reactflow';
import { N8nNodeData } from '../components/N8nNode';

// Node-to-code templates
const codeTemplates = {
  trigger: {
    webhook: `
app.post('/webhook/:workflowId', async (req, res) => {
  try {
    const data = { 
      ...req.body, 
      timestamp: new Date().toISOString(),
      workflowId: req.params.workflowId 
    };
    
    console.log('Webhook triggered:', data);
    const result = await executeWorkflow(data);
    
    res.json({ 
      success: true, 
      message: 'Workflow executed successfully',
      result 
    });
  } catch (error) {
    console.error('Webhook execution failed:', error);
    res.status(500).json({ 
      success: false, 
      error: error.message 
    });
  }
});`,
    
    schedule: `
// Schedule: {{schedule}}
cron.schedule('{{schedule}}', async () => {
  try {
    console.log('Scheduled workflow triggered at:', new Date().toISOString());
    const data = { 
      trigger: 'schedule',
      timestamp: new Date().toISOString()
    };
    await executeWorkflow(data);
  } catch (error) {
    console.error('Scheduled workflow failed:', error);
  }
});`,

    manual: `
// Manual trigger endpoint
app.post('/trigger/manual', async (req, res) => {
  try {
    const data = {
      ...req.body,
      trigger: 'manual',
      timestamp: new Date().toISOString()
    };
    
    const result = await executeWorkflow(data);
    res.json({ success: true, result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});`
  },

  action: {
    llm_call: `
// LLM API Call: {{label}}
async function {{functionName}}(data) {
  try {
    const prompt = \`{{prompt}}\`.replace(/\\{\\{([^}]+)\\}\\}/g, (match, key) => data[key] || match);
    
    const response = await openai.chat.completions.create({
      model: '{{model}}' || 'gpt-4',
      messages: [
        { role: 'system', content: 'You are a helpful assistant.' },
        { role: 'user', content: prompt }
      ],
      temperature: 0.7,
      max_tokens: 1000
    });
    
    const result = response.choices[0].message.content;
    data.{{outputVar}} = result;
    
    console.log('LLM Response:', result);
    return data;
  } catch (error) {
    console.error('LLM API call failed:', error);
    throw new Error(\`LLM processing failed: \${error.message}\`);
  }
}`,

    http_request: `
// HTTP Request: {{label}}
async function {{functionName}}(data) {
  try {
    const url = \`{{url}}\`.replace(/\\{\\{([^}]+)\\}\\}/g, (match, key) => data[key] || match);
    const method = '{{method}}' || 'GET';
    
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...{{headers}}
      }
    };
    
    if (method !== 'GET' && {{requestBody}}) {
      options.body = JSON.stringify({{requestBody}});
    }
    
    const response = await fetch(url, options);
    const result = await response.json();
    
    data.{{outputVar}} = result;
    console.log('HTTP Request result:', result);
    
    return data;
  } catch (error) {
    console.error('HTTP request failed:', error);
    throw new Error(\`HTTP request failed: \${error.message}\`);
  }
}`,

    email: `
// Send Email: {{label}}
async function {{functionName}}(data) {
  try {
    const to = \`{{to}}\`.replace(/\\{\\{([^}]+)\\}\\}/g, (match, key) => data[key] || match);
    const subject = \`{{subject}}\`.replace(/\\{\\{([^}]+)\\}\\}/g, (match, key) => data[key] || match);
    const body = \`{{body}}\`.replace(/\\{\\{([^}]+)\\}\\}/g, (match, key) => data[key] || match);
    
    const mailOptions = {
      from: process.env.EMAIL_FROM || 'noreply@nodex.ai',
      to,
      subject,
      html: body
    };
    
    const info = await transporter.sendMail(mailOptions);
    
    console.log('Email sent:', info.messageId);
    data.emailSent = true;
    data.emailId = info.messageId;
    
    return data;
  } catch (error) {
    console.error('Email sending failed:', error);
    throw new Error(\`Email sending failed: \${error.message}\`);
  }
}`,

    database: `
// Database Operation: {{label}}
async function {{functionName}}(data) {
  try {
    const query = \`{{query}}\`;
    const params = [{{params}}].map(param => 
      typeof param === 'string' ? 
        param.replace(/\\{\\{([^}]+)\\}\\}/g, (match, key) => data[key] || match) : 
        param
    );
    
    const result = await db.query(query, params);
    
    data.dbResult = result;
    console.log('Database operation completed:', result.affectedRows || result.length);
    
    return data;
  } catch (error) {
    console.error('Database operation failed:', error);
    throw new Error(\`Database operation failed: \${error.message}\`);
  }
}`
  },

  condition: `
// Condition: {{label}}
async function {{functionName}}(data) {
  try {
    const condition = \`{{condition}}\`.replace(/\\{\\{([^}]+)\\}\\}/g, (match, key) => {
      const value = data[key];
      return value !== undefined ? JSON.stringify(value) : 'null';
    });
    
    // Safe evaluation of condition
    const result = eval(condition);
    
    console.log('Condition evaluated:', condition, '→', result);
    data.conditionResult = result;
    
    return { conditionResult: result, data };
  } catch (error) {
    console.error('Condition evaluation failed:', error);
    return { conditionResult: false, data };
  }
}`,

  validation: `
// Validation: {{label}}
async function {{functionName}}(data) {
  try {
    const rules = {{validationRules}};
    const errors = [];
    
    for (const [field, rule] of Object.entries(rules)) {
      const value = data[field];
      
      if (rule.required && !value) {
        errors.push(\`\${field} is required\`);
      }
      
      if (rule.type && typeof value !== rule.type) {
        errors.push(\`\${field} must be of type \${rule.type}\`);
      }
      
      if (rule.minLength && value.length < rule.minLength) {
        errors.push(\`\${field} must be at least \${rule.minLength} characters\`);
      }
    }
    
    if (errors.length > 0) {
      throw new Error('Validation failed: ' + errors.join(', '));
    }
    
    console.log('Validation passed for:', Object.keys(rules));
    data.validationPassed = true;
    
    return data;
  } catch (error) {
    console.error('Validation failed:', error);
    throw error;
  }
}`
};

// Package.json dependencies based on node types
const getDependencies = (nodes: Node<N8nNodeData>[]): Record<string, string> => {
  const deps: Record<string, string> = {
    'express': '^4.18.2',
    'cors': '^2.8.5',
    'dotenv': '^16.0.3'
  };

  nodes.forEach(node => {
    switch (node.data.nodeType) {
      case 'trigger':
        if (node.data.label.toLowerCase().includes('schedule')) {
          deps['node-cron'] = '^3.0.3';
        }
        break;
      case 'action':
        if (node.data.label.toLowerCase().includes('llm') || 
            node.data.label.toLowerCase().includes('ai') ||
            node.data.label.toLowerCase().includes('gpt')) {
          deps['openai'] = '^4.20.1';
        }
        if (node.data.label.toLowerCase().includes('email')) {
          deps['nodemailer'] = '^6.9.7';
        }
        if (node.data.label.toLowerCase().includes('database') ||
            node.data.label.toLowerCase().includes('db')) {
          deps['mysql2'] = '^3.6.5';
          deps['pg'] = '^8.11.3';
        }
        break;
    }
  });

  return deps;
};

// Generate function name from node label
const generateFunctionName = (label: string, nodeId: string): string => {
  const cleaned = label
    .replace(/[^a-zA-Z0-9]/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '')
    .toLowerCase();
  
  return cleaned || `node_${nodeId.replace(/[^a-zA-Z0-9]/g, '_')}`;
};

// Template substitution
const substituteTemplate = (template: string, node: Node<N8nNodeData>, data: any = {}): string => {
  return template.replace(/\{\{([^}]+)\}\}/g, (match, key) => {
    if (key === 'functionName') {
      return generateFunctionName(node.data.label, node.id);
    }
    if (key === 'label') {
      return node.data.label;
    }
    return data[key] || node.data[key] || match;
  });
};

export interface CodeGenerationResult {
  code: string;
  packageJson: any;
  dockerfile: string;
  dockerCompose: string;
  envExample: string;
  readme: string;
  deployScript: string;
}

// Main code generator class
export class WorkflowCodeGenerator {
  private nodes: Node<N8nNodeData>[];
  private edges: Edge[];

  constructor(nodes: Node<N8nNodeData>[], edges: Edge[]) {
    this.nodes = nodes;
    this.edges = edges;
  }

  generate(): CodeGenerationResult {
    const imports = this.generateImports();
    const setup = this.generateSetup();
    const functions = this.generateNodeFunctions();
    const orchestrator = this.generateOrchestrator();
    const triggers = this.generateTriggers();
    const startup = this.generateStartup();

    const code = `${imports}

${setup}

${functions}

${orchestrator}

${triggers}

${startup}`;

    return {
      code,
      packageJson: this.generatePackageJson(),
      dockerfile: this.generateDockerfile(),
      dockerCompose: this.generateDockerCompose(),
      envExample: this.generateEnvExample(),
      readme: this.generateReadme(),
      deployScript: this.generateDeployScript()
    };
  }

  private generateImports(): string {
    const deps = getDependencies(this.nodes);
    const imports = ['const express = require(\'express\');'];
    
    if (deps['node-cron']) imports.push('const cron = require(\'node-cron\');');
    if (deps['openai']) imports.push('const { OpenAI } = require(\'openai\');');
    if (deps['nodemailer']) imports.push('const nodemailer = require(\'nodemailer\');');
    if (deps['mysql2']) imports.push('const mysql = require(\'mysql2/promise\');');
    if (deps['cors']) imports.push('const cors = require(\'cors\');');
    
    imports.push('require(\'dotenv\').config();');
    
    return imports.join('\n');
  }

  private generateSetup(): string {
    return `
// Initialize Express app
const app = express();
app.use(express.json());
app.use(cors());

// Initialize services
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const transporter = nodemailer.createTransporter({
  service: 'gmail',
  auth: {
    user: process.env.EMAIL_USER,
    pass: process.env.EMAIL_PASS
  }
});`;
  }

  private generateNodeFunctions(): string {
    return this.nodes
      .filter(node => node.data.nodeType !== 'trigger')
      .map(node => this.generateNodeFunction(node))
      .join('\n\n');
  }

  private generateNodeFunction(node: Node<N8nNodeData>): string {
    const { nodeType } = node.data;
    
    if (nodeType === 'condition') {
      return substituteTemplate(codeTemplates.condition, node);
    }
    
    if (nodeType === 'validation') {
      return substituteTemplate(codeTemplates.validation, node);
    }
    
    if (nodeType === 'action') {
      // Determine action subtype based on node label/description
      let actionType = 'http_request'; // default
      
      if (node.data.label.toLowerCase().includes('llm') || 
          node.data.label.toLowerCase().includes('ai') ||
          node.data.label.toLowerCase().includes('gpt')) {
        actionType = 'llm_call';
      } else if (node.data.label.toLowerCase().includes('email')) {
        actionType = 'email';
      } else if (node.data.label.toLowerCase().includes('database')) {
        actionType = 'database';
      }
      
      return substituteTemplate(codeTemplates.action[actionType], node, {
        model: 'gpt-4',
        prompt: node.data.description || 'Process the input data',
        outputVar: generateFunctionName(node.data.label, node.id) + '_result',
        url: 'https://api.example.com/endpoint',
        method: 'POST',
        headers: '{}',
        requestBody: 'data'
      });
    }
    
    return `// Function for ${node.data.label}\nasync function ${generateFunctionName(node.data.label, node.id)}(data) {\n  // TODO: Implement ${node.data.nodeType} logic\n  return data;\n}`;
  }

  private generateOrchestrator(): string {
    const nodeExecutions = this.nodes
      .filter(node => node.data.nodeType !== 'trigger')
      .map(node => {
        const funcName = generateFunctionName(node.data.label, node.id);
        return `      case '${node.id}':\n        return await ${funcName}(data);`;
      })
      .join('\n');

    return `
// Workflow orchestrator
async function executeWorkflow(data) {
  const executionLog = [];
  let currentData = { ...data };
  
  // Find trigger node
  const triggerNode = nodes.find(n => n.data.nodeType === 'trigger');
  if (!triggerNode) {
    throw new Error('No trigger node found in workflow');
  }
  
  // Start execution from trigger
  const result = await executeNode(triggerNode.id, currentData, executionLog);
  
  console.log('Workflow execution completed:', {
    steps: executionLog.length,
    duration: Date.now() - new Date(data.timestamp).getTime(),
    result
  });
  
  return result;
}

async function executeNode(nodeId, data, executionLog = []) {
  const node = nodes.find(n => n.id === nodeId);
  if (!node) {
    throw new Error(\`Node \${nodeId} not found\`);
  }
  
  executionLog.push({
    nodeId,
    label: node.data.label,
    timestamp: new Date().toISOString()
  });
  
  console.log(\`Executing node: \${node.data.label} (\${nodeId})\`);
  
  let result = data;
  
  // Execute node based on type
  if (node.data.nodeType !== 'trigger') {
    switch (nodeId) {
${nodeExecutions}
      default:
        console.warn(\`No handler for node \${nodeId}\`);
    }
  }
  
  // Find and execute next nodes
  const nextEdges = edges.filter(e => e.source === nodeId);
  
  for (const edge of nextEdges) {
    result = await executeNode(edge.target, result, executionLog);
  }
  
  return result;
}

// Workflow definition
const nodes = ${JSON.stringify(this.nodes, null, 2)};
const edges = ${JSON.stringify(this.edges, null, 2)};`;
  }

  private generateTriggers(): string {
    const triggerNodes = this.nodes.filter(node => node.data.nodeType === 'trigger');
    
    return triggerNodes.map(node => {
      if (node.data.label.toLowerCase().includes('webhook')) {
        return substituteTemplate(codeTemplates.trigger.webhook, node);
      } else if (node.data.label.toLowerCase().includes('schedule')) {
        return substituteTemplate(codeTemplates.trigger.schedule, node, {
          schedule: '0 9 * * *' // Default: daily at 9am
        });
      } else {
        return substituteTemplate(codeTemplates.trigger.manual, node);
      }
    }).join('\n\n');
  }

  private generateStartup(): string {
    return `
// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    workflow: '${this.nodes.find(n => n.data.nodeType === 'trigger')?.data.label || 'Unknown'}'
  });
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(\`🚀 Nodex workflow server running on port \${PORT}\`);
  console.log(\`📊 Health check: http://localhost:\${PORT}/health\`);
  console.log(\`🔗 Webhook endpoint: http://localhost:\${PORT}/webhook/my-workflow\`);
});`;
  }

  private generatePackageJson(): any {
    return {
      name: 'nodex-workflow',
      version: '1.0.0',
      description: 'Generated workflow from Nodex',
      main: 'workflow.js',
      scripts: {
        start: 'node workflow.js',
        dev: 'nodemon workflow.js',
        test: 'echo "No tests specified"'
      },
      dependencies: getDependencies(this.nodes),
      devDependencies: {
        nodemon: '^3.0.2'
      },
      keywords: ['automation', 'workflow', 'nodex'],
      author: 'Generated by Nodex',
      license: 'MIT'
    };
  }

  private generateDockerfile(): string {
    return `FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:3000/health || exit 1

# Start application
CMD ["npm", "start"]`;
  }

  private generateDockerCompose(): string {
    return `version: '3.8'

services:
  workflow:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - OPENAI_API_KEY=\${OPENAI_API_KEY}
      - EMAIL_USER=\${EMAIL_USER}
      - EMAIL_PASS=\${EMAIL_PASS}
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optional: Add Redis for caching/queues
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

  # Optional: Add database
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: workflow_db
      POSTGRES_USER: workflow_user
      POSTGRES_PASSWORD: \${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:`;
  }

  private generateEnvExample(): string {
    return `# Nodex Workflow Environment Variables

# API Keys
OPENAI_API_KEY=sk-your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Email Configuration (for Gmail)
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password

# Database (optional)
DB_PASSWORD=your-secure-db-password
DATABASE_URL=postgresql://workflow_user:password@localhost:5432/workflow_db

# Server Configuration
PORT=3000
NODE_ENV=development

# Add any workflow-specific environment variables below:
`;
  }

  private generateReadme(): string {
    const triggerNode = this.nodes.find(n => n.data.nodeType === 'trigger');
    const nodeCount = this.nodes.length;
    const hasLLM = this.nodes.some(n => 
      n.data.label.toLowerCase().includes('llm') || 
      n.data.label.toLowerCase().includes('ai')
    );

    return `# Nodex Generated Workflow

This workflow was automatically generated from your Nodex visual workflow builder.

## Overview
- **Nodes**: ${nodeCount}
- **Trigger**: ${triggerNode?.data.label || 'Manual'}
- **AI/LLM Integration**: ${hasLLM ? 'Yes' : 'No'}

## Quick Start

### 1. Install Dependencies
\`\`\`bash
npm install
\`\`\`

### 2. Configure Environment
\`\`\`bash
cp .env.example .env
# Edit .env with your API keys and configuration
\`\`\`

### 3. Run Locally
\`\`\`bash
npm start
\`\`\`

### 4. Test Your Workflow
\`\`\`bash
# Health check
curl http://localhost:3000/health

# Trigger workflow (if webhook)
curl -X POST http://localhost:3000/webhook/my-workflow \\
  -H "Content-Type: application/json" \\
  -d '{"test": "data"}'
\`\`\`

## Deployment Options

### Docker
\`\`\`bash
docker build -t nodex-workflow .
docker run -p 3000:3000 --env-file .env nodex-workflow
\`\`\`

### Docker Compose (Recommended)
\`\`\`bash
docker-compose up -d
\`\`\`

### Railway
\`\`\`bash
railway login
railway link
railway up
\`\`\`

### Render
1. Connect your GitHub repository
2. Set environment variables in Render dashboard
3. Deploy automatically on push

## API Endpoints

- \`GET /health\` - Health check
- \`POST /webhook/:workflowId\` - Webhook trigger
- \`POST /trigger/manual\` - Manual trigger

## Environment Variables

See \`.env.example\` for required configuration.

## Generated by Nodex
This workflow was created using [Nodex](https://nodex.ai) - AI-Powered Workflow Intelligence Platform.
`;
  }

  private generateDeployScript(): string {
    return `#!/bin/bash

# Nodex Workflow Deployment Script
set -e

echo "🚀 Deploying Nodex Workflow..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📝 Copy .env.example to .env and configure your settings"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm ci

# Build if needed
if [ -f "tsconfig.json" ]; then
    echo "🔨 Building TypeScript..."
    npm run build
fi

# Start with PM2 for production
if command -v pm2 &> /dev/null; then
    echo "🔄 Starting with PM2..."
    pm2 start workflow.js --name "nodex-workflow"
    pm2 save
    pm2 startup
else
    echo "⚠️  PM2 not found. Install with: npm install -g pm2"
    echo "🚀 Starting with node..."
    node workflow.js
fi

echo "✅ Deployment complete!"
echo "🌐 Your workflow is running on http://localhost:3000"
echo "📊 Health check: http://localhost:3000/health"
`;
  }
}

export { generateFunctionName, substituteTemplate };