from fastapi import FastAPI
from pydantic import BaseModel
from agentcrews.mediator.crew import MediatorCrew

app = FastAPI()
mediator_crew = MediatorCrew().crew()  # instantiate once for efficiency

class IntentRequest(BaseModel):
    intent: str

@app.post("/agent/interpret")
async def interpret_intent(data: IntentRequest):
    """
    Receives voice/text intent, returns a workflow graph (nodes/edges).
    """
    inputs = {"input": data.intent}
    result = mediator_crew.kickoff(inputs=inputs)
    # Try to find the final visualization output if split
    try:
        # could be result.artifacts["visualize_task"] if CrewAI >= 0.30
        return result.raw  # fallback: the last output should be Graph JSON
    except Exception:
        return {"error": "Workflow interpreter failed."}

# For manual UI edit update, add as needed:
class UpdateRequest(BaseModel):
    intent: str  # Pass latest intent, or extend for graph as needed

@app.post("/agent/update")
async def update_graph(data: UpdateRequest):
    """
    For now, just rerun main pipeline with latest intent
    (Could be extended to include UI graph deltas as extra context)
    """
    inputs = {"input": data.intent}
    result = mediator_crew.kickoff(inputs=inputs)
    try:
        return result.raw
    except Exception:
        return {"error": "Workflow interpreter failed on update."}
