# 🚀 SecureAI - AI-Powered Workflow Intelligence

**Nodex** is a production-ready workflow builder that transforms text descriptions and images into intelligent, compliant business workflows with automatic domain detection and regulatory enforcement.

## ✨ Features

### 🎯 Core Capabilities
- **Text-to-Workflow**: Convert natural language descriptions into executable workflows
- **Image-to-Workflow**: Extract workflows from uploaded diagrams using GPT-4o Vision
- **Smart Domain Detection**: Automatically identifies business verticals (HR, Finance, Healthcare, etc.)
- **Compliance Enforcement**: Auto-injection of regulatory requirements (GDPR, HIPAA, PCI-DSS, SOX, etc.)
- **Interactive Canvas**: React Flow-powered visual workflow editor
- **Prompt Library**: Pre-built prompts for common business scenarios

### 🧠 AI-Powered Processing
- **CrewAI Multi-Agent System**: Specialized agents for different business domains
- **GPT-4o Vision Integration**: Intelligent diagram analysis and workflow extraction
- **Intelligent Fallbacks**: Domain-specific workflow templates with rich metadata
- **Real-time Processing**: Async execution with progress tracking

### 🛡️ Enterprise Security
- **Input Sanitization**: XSS and injection attack prevention
- **CORS Configuration**: Secure cross-origin resource sharing
- **Compliance Validation**: Automated regulatory requirement checking
- **Audit Trails**: Comprehensive logging for compliance tracking

## 🏗️ Architecture

### Backend (`agentcrews/mediator/`)
```
hackathon_backend.py       # Main FastAPI server
├── workflow_processor.py  # CrewAI output processing
├── async_crew_executor.py # Async agent execution
├── domain_identifier.py   # Business domain detection
├── crew_factory.py        # Agent orchestration
├── vertical_agents.py     # Domain-specific agents
├── intelligent_fallback.py # Smart workflow templates
├── cache_manager.py       # In-memory caching
└── security.py           # Input sanitization & security
```

### Frontend (`frontend/src/`)
```
App.tsx                    # Main React application
├── components/
│   ├── N8nNode.tsx       # Workflow node component
│   └── NodePalette.tsx   # Drag-and-drop palette
└── styles/               # CSS styling
```

### Configuration (`config/compliance/`)
```
hr.yaml                   # HR compliance rules
finance.yaml              # Financial compliance rules
sales.yaml                # Sales compliance rules
it.yaml                   # IT security compliance
operations.yaml           # Operations compliance
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**
- **Node.js 18+**

### 1. Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd SecureAI

# Create environment file
cp .env.example .env
```

**Required Environment Variables:**
```env
OPENAI_API_KEY=your_openai_api_key_here
CREWAI_MODEL=gpt-4o  # Optional, defaults to gpt-4o
```

### 2. Backend Setup

```bash
pip install -r requirements.txt

# Start the API server
python run_mediator.py
```

Server starts at: **http://localhost:8000**
- API Documentation: **http://localhost:8000/docs**
- Health Check: **http://localhost:8000/health**

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

Frontend available at: **http://localhost:3001**

## 📡 API Reference

### Core Endpoints

#### Process Text Input
```bash
POST /api/interpret
Content-Type: application/json

{
  "text": "Create employee onboarding workflow with background checks"
}
```

#### Process Image Input
```bash
POST /api/parse-image
Content-Type: multipart/form-data

{
  "image": <file_upload>
}
```

#### Convert to n8n Format
```bash
POST /api/convert-and-execute
Content-Type: application/json

{
  "nodes": [...],
  "edges": [...]
}
```

#### Progress Tracking
```bash
GET /api/progress/{workflow_id}
```

#### Test Endpoints
```bash
GET /api/test-edges        # Test edge generation
GET /health               # Health check
```

### Response Format

```json
{
  "nodes": [
    {
      "id": "node_0",
      "type": "n8nNode",
      "position": { "x": 150, "y": 150 },
      "data": {
        "label": "Gather Employee Information",
        "nodeType": "httpRequest",
        "icon": "⚙️",
        "description": "Automated httpRequest step",
        "locked": false,
        "compliance_reason": null,
        "actor": "HR System",
        "data_source": "HRIS (Workday, BambooHR)",
        "data_destination": "Employee Database",
        "api_endpoint": "POST /api/employee/new"
      }
    }
  ],
  "edges": [
    {
      "id": "edge_0",
      "source": "node_0",
      "target": "node_1"
    }
  ],
  "compliance_info": {
    "domain": "hr",
    "compliance_nodes_added": 3,
    "rules_applied": ["GDPR", "CCPA", "EEOC"]
  }
}
```

## 🎯 Usage Examples

### Example 1: HR Onboarding Workflow
```javascript
const response = await fetch('http://localhost:8000/api/interpret', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: "Set up a workflow so job offer letters can't be sent until the background check and HR approval are complete, and notify the recruiter at each step"
  })
});
```

**Result**: Automatic detection as HR domain with GDPR compliance nodes injected.

### Example 2: Financial Approval Process
```javascript
const response = await fetch('http://localhost:8000/api/interpret', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: "Whenever an invoice above $10,000 comes in, route it for CFO approval and make sure anti-fraud checks are performed automatically"
  })
});
```

**Result**: Finance domain with PCI-DSS compliance and fraud detection nodes.

### Example 3: Image Upload Processing
```javascript
const formData = new FormData();
formData.append('image', imageFile);

const response = await fetch('http://localhost:8000/api/parse-image', {
  method: 'POST',
  body: formData
});
```

**Result**: GPT-4o Vision extracts workflow from diagram with automatic compliance injection.

## 🛡️ Compliance Domains

### Healthcare
- **Triggers**: "patient", "medical", "health", "HIPAA"
- **Rules**: HIPAA, HITECH
- **Auto-injected**: Data encryption, audit logging, PHI protection

### Finance
- **Triggers**: "payment", "invoice", "financial", "transaction"
- **Rules**: PCI-DSS, SOX, GDPR
- **Auto-injected**: Fraud detection, transaction validation, audit trails

### Human Resources
- **Triggers**: "employee", "hiring", "HR", "personnel"
- **Rules**: GDPR, CCPA, EEOC, Fair Labor Standards Act
- **Auto-injected**: Data privacy controls, background checks, audit trails

### Sales & Marketing
- **Triggers**: "customer", "lead", "sales", "marketing"
- **Rules**: GDPR, CCPA, CAN-SPAM, FTC Guidelines
- **Auto-injected**: Consent management, data validation, unsubscribe handling

### IT & Security
- **Triggers**: "security", "access", "IT", "system"
- **Rules**: ISO 27001, SOC 2, NIST, CIS Controls
- **Auto-injected**: Security scans, access controls, change management

## 💡 Prompt Library

The system includes 10 pre-built prompts covering common business scenarios:

1. **Healthcare**: Patient record compliance workflow
2. **Finance**: Invoice approval with fraud detection
3. **HR**: Job offer approval process
4. **IT**: VPN access request workflow
5. **Privacy**: Data deletion request handling
6. **Education**: Student enrollment verification
7. **Procurement**: Software purchase approval
8. **Government**: Permit application processing
9. **Insurance**: Claims review workflow
10. **Marketing**: Email campaign compliance

## 🔧 Configuration

### Domain Detection
Customize domain detection in `agentcrews/mediator/domain_identifier.py`:

```python
DOMAIN_PATTERNS = {
    'hr': ['employee', 'hiring', 'onboard', 'personnel'],
    'finance': ['invoice', 'payment', 'transaction', 'financial'],
    'healthcare': ['patient', 'medical', 'health', 'clinical']
}
```

### Compliance Rules
Add custom compliance requirements in `config/compliance/`:

```yaml
# custom_domain.yaml
domain: custom
required_steps:
  - compliance_type: custom_check
    label: Custom Validation
    reason: Required for custom compliance
    locked: true
compliance_rules:
  - Custom Regulation
  - Industry Standard
stakeholders:
  - user
  - compliance_officer
```

### Caching Configuration
Adjust cache settings in `agentcrews/mediator/cache_manager.py`:

```python
cache_manager = CacheManager(
    ttl_seconds=1800,  # 30 minutes
    max_entries=1000
)
```

## 📊 Monitoring & Observability

### Structured Logging
All events are logged with structured data:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "event": "workflow_processed",
  "workflow_id": "wf_abc123",
  "domain": "finance",
  "nodes_count": 8,
  "compliance_nodes": 3,
  "processing_time_ms": 2500
}
```

### Performance Metrics
- **Agent Execution Time**: Tracked per CrewAI agent
- **API Response Time**: End-to-end request processing
- **Cache Hit Rate**: In-memory cache effectiveness
- **Compliance Validation Time**: Regulatory check duration

### Health Monitoring
```bash
# Check system health
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "dependencies": {
    "openai": "connected",
    "crewai": "operational",
    "cache": "active"
  }
}
```

## 🔒 Security Features

### Input Sanitization
- HTML entity escaping
- XSS prevention
- SQL injection protection
- Suspicious pattern detection

### CORS Security
```python
allow_origins=["http://localhost:3000", "http://localhost:3001"]
allow_credentials=True
allow_methods=["GET", "POST", "PUT", "DELETE"]
```

### API Key Management
- Environment-based configuration
- Secure key validation
- Rate limiting (configurable)

## 🧪 Testing

### Backend Testing
```bash
# Test API endpoints
curl -X POST "http://localhost:8000/api/interpret" \
  -H "Content-Type: application/json" \
  -d '{"text": "Create a simple workflow"}'

# Test health endpoint
curl "http://localhost:8000/health"
```

### Frontend Testing
```bash
cd frontend
npm run test
```

### Integration Testing
```bash
# Test full pipeline
curl -X POST "http://localhost:8000/api/interpret" \
  -H "Content-Type: application/json" \
  -d '{"text": "Process patient data with HIPAA compliance"}' | \
  jq '.compliance_info.domain'
# Expected: "healthcare"
```

## 📦 Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Services:
# - Backend: localhost:8000
# - Frontend: localhost:3001
```

### Environment Variables for Production
```env
OPENAI_API_KEY=prod_key_here
CREWAI_MODEL=gpt-4o
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=https://your-domain.com
```

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines
- Follow existing code patterns
- Add tests for new features
- Update documentation
- Ensure compliance rules are maintained

## 🔮 Roadmap

### Phase 1 (Current)
- [x] Text-to-workflow conversion
- [x] Image-to-workflow processing
- [x] Domain detection and compliance injection
- [x] Interactive React Flow canvas
- [x] Prompt library

### Phase 2 (Planned)
- [ ] n8n workflow execution
- [ ] Advanced workflow templates
- [ ] Multi-tenant architecture
- [ ] Workflow versioning
- [ ] Advanced analytics dashboard

### Phase 3 (Future)
- [ ] Enterprise SSO integration
- [ ] Advanced compliance templates
- [ ] Workflow marketplace
- [ ] Mobile application
- [ ] API monetization features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Frontend**: http://localhost:3001

### Troubleshooting
- Check logs in console output
- Verify environment variables are set
- Ensure OpenAI API key has sufficient credits
- Check CORS settings for cross-origin issues