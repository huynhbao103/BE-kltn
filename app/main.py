from fastapi import FastAPI
from app.routes import classify_topic, langgraph_workflow

app = FastAPI()

app.include_router(classify_topic.router, prefix="/api/classify", tags=["Classification"])
app.include_router(langgraph_workflow.router, prefix="/api/langgraph", tags=["LangGraph Workflow"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Nutrition Assistant API"}
