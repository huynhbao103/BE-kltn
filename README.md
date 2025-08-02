# Nutrition Assistant API

Hệ thống tư vấn dinh dưỡng thông minh sử dụng LangGraph workflow với LLM và Neo4j.

## 🚀 Tính năng chính

- **Phân loại chủ đề**: Tự động phân loại câu hỏi có thuộc chủ đề dinh dưỡng không
- **Workflow thông minh**: LangGraph workflow với LLM check và fallback logic
- **Tư vấn cá nhân hóa**: Dựa trên BMI, cảm xúc, bệnh lý của người dùng
- **Rerank thực phẩm**: Sắp xếp lại món ăn theo mức độ phù hợp
- **Fallback logic**: Tự động thử query đơn giản hơn khi không có kết quả

## 🏗️ Kiến trúc

```
User Input → Identify User → Classify Topic → Select Emotion → Calculate BMI → Query Neo4j → LLM Check → [Rerank | Fallback] → Generate Result
```

### Các Node chính:
- **identify_user**: Xác định user từ JWT token
- **classify_topic**: Phân loại chủ đề câu hỏi
- **select_emotion**: Yêu cầu chọn cảm xúc
- **calculate_bmi**: Tính BMI và phân loại
- **query_neo4j**: Truy vấn thực phẩm phù hợp
- **check_food_suitability_llm**: Kiểm tra tính phù hợp bằng AI
- **rerank_foods**: Sắp xếp lại theo mức độ phù hợp
- **generate_result**: Tạo kết quả cuối cùng

## 📁 Cấu trúc project

```
be-kltn/
├── app/
│   ├── main.py                 # FastAPI app
│   ├── config.py              # Cấu hình database
│   ├── graph/
│   │   ├── engine.py          # LangGraph workflow
│   │   └── nodes/             # Các node của workflow
│   ├── routes/                # API routes
│   ├── services/              # Business logic
│   └── utils/                 # Utilities
├── test_workflow.py           # Test script
├── requirements.txt           # Dependencies
└── README.md                 # Documentation
```

## 🛠️ Cài đặt

1. **Clone repository**:
```bash
git clone <repository-url>
cd be-kltn
```

2. **Tạo virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows
```

3. **Cài đặt dependencies**:
```bash
pip install -r requirements.txt
```

4. **Cấu hình environment variables**:
```bash
# Tạo file .env
OPENAI_API_KEY=your_openai_api_key
JWT_SECRET_KEY=your_jwt_secret
MONGODB_URI=your_mongodb_uri
NEO4J_URI=your_neo4j_uri
NEO4J_USER=your_neo4j_user
NEO4J_PASSWORD=your_neo4j_password
```

## 🚀 Chạy ứng dụng

1. **Chạy server**:
```bash
uvicorn app.main:app --reload
```

2. **Test workflow**:
```bash
python test_workflow.py
```

## 📡 API Endpoints

### 1. Phân loại chủ đề
```http
POST /api/check-mode
Content-Type: application/json

{
    "question": "Tôi nên ăn gì để giảm cân?"
}
```

### 2. Workflow chính
```http
POST /api/langgraph/process
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
    "question": "Tôi nên ăn gì để tốt cho sức khỏe?"
}
```

### 4. Thông tin workflow
```http
GET /api/langgraph/workflow-info
```

## 🔧 Workflow Logic

### Luồng chính:
1. **Query Neo4j** → Lấy thực phẩm phù hợp
2. **LLM Check** → Kiểm tra tính phù hợp
3. **Nếu "yes"** → **Rerank** → **Generate Result**
4. **Nếu "no"** → **Fallback Query** → Quay lại bước 1

### Fallback Logic:
- **Level 1**: Bỏ cảm xúc, giữ chế độ ăn
- **Level 2**: Bỏ cảm xúc + chế độ ăn, chỉ giữ bệnh lý
- **Level 3**: Lấy tất cả món ăn (limit 15)
- **Sau 3 lần**: Trả về "Nhóm đang phát triển và chưa có món ăn phù hợp"

## 🧪 Test

```bash
# Test workflow hoàn chỉnh
python test_workflow.py

# Test riêng lẻ
python -c "from app.graph.nodes.classify_topic_node import check_mode; print(check_mode('Tôi nên ăn gì?'))"
```

## 📊 Kết quả mẫu

### Success Case:
```json
{
    "status": "success",
    "message": "Cảm xúc: Mệt mỏi | BMI: 25.5 (Thừa cân) | Thực phẩm phù hợp: Đái tháo đường: Gỏi gà, Súp gà | (Đã sắp xếp lại theo mức độ phù hợp) | (LLM xác nhận phù hợp)",
    "neo4j_data": {...},
    "llm_check": {"response": "yes", "reasoning": "..."},
    "reranked_data": {"foods": {...}, "scores": {...}},
    "fallback_attempts": 0
}
```

### No Suitable Food Case:
```json
{
    "status": "no_suitable_food",
    "message": "Nhóm đang phát triển và chưa có món ăn phù hợp cho trường hợp của bạn. Vui lòng thử lại sau.",
    "fallback_attempts": 3
}
```

## 🔒 Authentication

API sử dụng JWT token để xác thực:
```http
Authorization: Bearer <JWT_TOKEN>
```

Token phải chứa `user_id` để workflow có thể lấy thông tin user từ MongoDB.

## 📝 Lưu ý

- Đảm bảo MongoDB và Neo4j đã được cấu hình đúng
- OpenAI API key cần có credit để sử dụng LLM
- Session được lưu trong memory (có thể chuyển sang Redis sau)
- Workflow có thể mất vài giây để hoàn thành do LLM check

## 🤝 Đóng góp

1. Fork project
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Tạo Pull Request

## 📄 License

MIT License 