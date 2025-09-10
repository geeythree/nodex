# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend (Python)
- **Start API server**: `python run_mediator.py`
- **Install dependencies**: `pip install -r requirements.txt`
- **Set up environment**: Create `.env` file with required API keys (see README.md)

### Frontend (React + Vite)
- **Start development server**: `cd frontend && npm start` or `npm run dev`
- **Build for production**: `cd frontend && npm run build`
- **Run tests**: `cd frontend && npm run test`
- **Install dependencies**: `cd frontend && npm install`

### Required Environment Variables
```env
OPENAI_API_KEY=your_openai_api_key_here
CREWAI_MODEL=gpt-4o  # Optional, defaults to gpt-4o

# Optional security settings
CORS_ORIGINS=http://localhost:3000,http://localhost:3001  # Comma-separated list
REQUIRE_API_KEY=false  # Set to true to require API key authentication
API_KEYS=key1,key2,key3  # Comma-separated list of valid API keys (if REQUIRE_API_KEY=true)
ENVIRONMENT=development  # Set to 'production' for stricter security
```

## Current Architecture (Image/Text-based Workflow Creation)

### Backend Structure (`agentcrews/mediator/`)
- **Primary Backend**: `hackathon_backend.py` - Refactored FastAPI server with modular architecture
- **Workflow Processing**: `workflow_processor.py` - Clean JSON parsing and React Flow transformation
- **Async Execution**: `async_crew_executor.py` - Non-blocking CrewAI execution
- **Caching**: `cache_manager.py` - In-memory caching with TTL support
- **Security**: `security.py` - Input sanitization, CORS management, API key validation
- **Multi-agent orchestration**: CrewAI for workflow generation from text descriptions
- **Image processing**: GPT-4o Vision API for workflow extraction from uploaded diagrams
- **Domain detection**: Automatic classification into business verticals (HR, sales, finance, etc.)
- **Compliance enforcement**: Auto-injection of domain-specific compliance nodes

### Frontend Structure (`frontend/src/`)
- **Main UI**: `App.tsx` - Complete interface with text input and image upload
- **Workflow canvas**: React Flow integration for interactive workflow editing
- **Node components**: `N8nNode.tsx` for workflow step visualization
- **Node palette**: `NodePalette.tsx` for drag-and-drop workflow building

### Core Processing Flow

#### 1. Text-to-Workflow Pipeline (`/api/interpret`)
1. **Domain Identification** (`domain_identifier.py`): Classifies text into business domains
2. **CrewAI Agent Chain**: 
   - **Interpreter Agent**: Converts text to executable API steps
   - **Planner Agent**: Structures steps into logical sequences
   - **Compliance Agent**: Injects domain-specific compliance requirements
   - **Visualizer Agent**: Generates n8n-compatible workflow JSON
3. **Compliance Injection**: Automatic addition of locked regulatory nodes
4. **React Flow Output**: JSON structure compatible with frontend canvas

#### 2. Image-to-Workflow Pipeline (`/api/parse-image`)
1. **GPT-4o Vision Analysis**: Extracts workflow steps and connections from uploaded diagrams
2. **Step Recognition**: OCR of text labels and identification of compliance steps
3. **Flow Reconstruction**: Converts visual elements to structured workflow
4. **Domain Detection**: Infers business domain from extracted content
5. **Compliance Enhancement**: Same compliance injection as text pipeline

#### 3. Vertical Agent System (`crew_factory.py`)
- **Domain-specific crews**: Different agent combinations per business vertical
- **Specialized planners**: HR, Sales, Finance-specific workflow planning
- **Conversational agents**: Handle incomplete requirements with follow-up questions

### Key API Endpoints (`hackathon_backend.py`)
- **`POST /api/interpret`**: Process text descriptions into workflows
- **`POST /api/parse-image`**: Process uploaded workflow diagrams  
- **`POST /api/convert-and-execute`**: Convert to n8n format for execution
- **`GET /api/progress/{workflow_id}`**: Real-time progress tracking
- **`GET /health`**: Service health check

### Compliance System
Automatic compliance enforcement based on detected domains:
- **HR**: Employee data protection, GDPR compliance, audit trails
- **Finance**: PCI-DSS validation, fraud detection, transaction auditing
- **Sales**: CRM compliance, lead data protection
- **Operations**: Process auditing, quality controls
- **IT**: Security compliance, access controls

Compliance nodes are:
- Automatically injected based on domain detection
- Visually distinct (locked/colored differently)
- Cannot be removed by users
- Include explanatory tooltips

### Data Flow
1. **Text Input**: User description → Domain classification → CrewAI agent pipeline → Compliance injection → React Flow JSON
2. **Image Input**: Uploaded diagram → GPT-4o Vision → Step extraction → Domain inference → Compliance enhancement → React Flow JSON  
3. **Frontend Rendering**: JSON workflow → React Flow canvas → Interactive editing (non-compliance nodes only)
4. **Export**: Final workflow → n8n format → Ready for execution

### File Organization (Active Files Only)
- **Main entry**: `run_mediator.py` (FastAPI server startup)
- **Primary backend**: `agentcrews/mediator/hackathon_backend.py`
- **Domain detection**: `agentcrews/mediator/domain_identifier.py`
- **Agent factory**: `agentcrews/mediator/crew_factory.py` 
- **Vertical agents**: `agentcrews/mediator/vertical_agents.py`
- **Main frontend**: `frontend/src/App.tsx`
- **Node components**: `frontend/src/components/N8nNode.tsx`, `NodePalette.tsx`

### Deprecated/Unused Files
- All voice-related files (`voice_handler.py`, `pipecat_voice_handler.py`, `services/stt_service.py`, `services/tts_service.py`)
- Old API file (`api.py` - replaced by `hackathon_backend.py`)
- Legacy crew files (`crew.py`, `main.py` - replaced by `hackathon_backend.py`)
- Old canvas (`WorkflowCanvas.tsx` - functionality moved to `App.tsx`)

## Development Notes

- GPT-4o Vision API is used for image analysis (requires OPENAI_API_KEY)
- CrewAI orchestrates multiple specialized agents for workflow generation
- Compliance rules are automatically applied based on domain detection
- Frontend uses React Flow v11 for interactive workflow visualization
- All processing is asynchronous with progress tracking
- No voice functionality - focus is purely on text and image input
- Workflow export targets n8n format for real-world execution