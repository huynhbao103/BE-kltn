from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.routes import classify_topic, langgraph_workflow
# from app.routes.langgraph_workflow import get_user_id_from_token

app = FastAPI()

# CORS configuration - Updated for deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicit methods
    allow_headers=["*"],  # Cho phép tất cả headers bao gồm Authorization
    expose_headers=["*"],  # Expose headers to frontend
)
app.include_router(classify_topic.router, prefix="/api/classify", tags=["Classification"])
app.include_router(langgraph_workflow.router, prefix="/api/langgraph", tags=["LangGraph Workflow"])
