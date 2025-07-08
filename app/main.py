from fastapi import FastAPI
from app.routes.classify_topic import router as classify_router
from app.routes.langgraph_workflow import router as langgraph_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Nutrition Assistant API",
    description="API cho hệ thống tư vấn dinh dưỡng với LangGraph workflow",
    version="1.0.0"
)

# CORS để gọi từ frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký router
app.include_router(classify_router, prefix="/api", tags=["Classification"])
app.include_router(langgraph_router, prefix="/api/langgraph", tags=["Workflow"])
