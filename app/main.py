from fastapi import FastAPI
from app.routes.classify_topic import router as classify_router
from app.routes.bmi_calculation import router as bmi_router
from app.routes.langgraph_workflow import router as langgraph_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS để gọi từ Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Hoặc ["http://localhost:3000"] nếu bạn dùng Next.js dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký router
app.include_router(classify_router, prefix="/api")
app.include_router(bmi_router, prefix="/api/bmi")
app.include_router(langgraph_router, prefix="/api/langgraph")
