# Tính năng mới: Chọn cảm xúc và phương pháp nấu

## Tổng quan

Hệ thống tư vấn dinh dưỡng đã được mở rộng với 2 node mới cho phép người dùng chọn:
1. **Cảm xúc hiện tại** (7 lựa chọn)
2. **Phương pháp nấu** (5 lựa chọn)

## Các node mới

### 1. Select Emotion Node (`select_emotion_node.py`)
- **Mục đích**: Yêu cầu người dùng chọn cảm xúc hiện tại
- **Lựa chọn**: 7 cảm xúc
  - Vui vẻ
  - Buồn bã
  - Bình thường
  - Tức giận
  - Mệt mỏi
  - Hạnh phúc
  - Trầm cảm

### 2. Select Cooking Method Node (`select_cooking_method_node.py`)
- **Mục đích**: Yêu cầu người dùng chọn phương pháp nấu
- **Lựa chọn**: 5 phương pháp
  - Luộc
  - Xào
  - Nướng
  - Hấp
  - Chiên
- **Đặc điểm**: Có thể chọn nhiều phương pháp hoặc chọn tất cả

## Workflow mới

Luồng xử lý đã được cập nhật thành:
```
identify_user → classify_topic → select_emotion → select_cooking_method → calculate_bmi → query_neo4j → rerank_foods → generate_result
```

## API Endpoints mới

### 1. `/process` (POST)
- **Mục đích**: Bắt đầu workflow
- **Response có thể**:
  - `status: "need_emotion"` - Yêu cầu chọn cảm xúc
  - `status: "need_diet"` - Yêu cầu chọn chế độ ăn
  - `status: "need_cooking_method"` - Yêu cầu chọn phương pháp nấu
  - `status: "success"` - Kết quả hoàn chỉnh

### 2. `/process-emotion` (POST)
- **Mục đích**: Tiếp tục workflow sau khi chọn cảm xúc
- **Body**:
  ```json
  {
    "session_id": "session_id_from_previous_response",
    "emotion": "Vui vẻ"
  }
  ```

### 3. `/process-diet` (POST)
- **Mục đích**: Tiếp tục workflow sau khi chọn chế độ ăn
- **Body**:
  ```json
  {
    "session_id": "session_id_from_previous_response",
    "diets": ["Chế độ ăn thường", "Chế độ ăn chay"]
  }
  ```

### 4. `/process-cooking-method` (POST)
- **Mục đích**: Tiếp tục workflow sau khi chọn phương pháp nấu
- **Body**:
  ```json
  {
    "session_id": "session_id_from_previous_response",
    "cooking_methods": ["Luộc", "Xào", "Nướng"]
  }
  ```

## Cách sử dụng

### Luồng hoạt động đã sửa:
1. **Bước 1**: Gọi `/process` → Nhận `status: "need_emotion"` + `emotion_prompt` + `session_id`
2. **Bước 2**: Gọi `/process-emotion` → Nhận `status: "need_cooking_method"` + `cooking_method_prompt` + `session_id`
3. **Bước 3**: Gọi `/process-cooking-method` → Nhận kết quả cuối cùng

### Bước 1: Bắt đầu workflow
```bash
curl -X POST "http://localhost:8000/langgraph/process" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Tôi nên ăn gì để giảm cân?"}'
```

**Response:**
```json
{
  "status": "need_emotion",
  "emotion_prompt": {
    "prompt": "Hãy chọn cảm xúc hiện tại của bạn...",
    "emotions": ["Vui vẻ", "Buồn bã", "Bình thường", ...]
  },
  "session_id": "abc123..."
}
```

### Bước 2: Chọn cảm xúc
```bash
curl -X POST "http://localhost:8000/langgraph/process-emotion" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "abc123...", "emotion": "Vui vẻ"}'
```

**Response:**
```json
{
  "status": "need_cooking_method",
  "cooking_method_prompt": {
    "prompt": "Hãy chọn phương pháp nấu bạn muốn...",
    "cooking_methods": ["Luộc", "Xào", "Nướng", ...]
  },
  "session_id": "def456..."
}
```

### Bước 3: Chọn phương pháp nấu
```bash
curl -X POST "http://localhost:8000/langgraph/process-cooking-method" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "def456...", "cooking_methods": ["Luộc", "Hấp"]}'
```

**Response:**
```json
{
  "status": "success",
  "message": "Kết quả tư vấn dinh dưỡng...",
  "data": {...}
}
```

## Testing

Chạy file test để kiểm tra các node mới:
```bash
python test_new_nodes.py
```

## Lưu ý

1. **Session Management**: Mỗi bước trong workflow được lưu trữ trong Redis với session_id
2. **Multiple Selection**: Người dùng có thể chọn nhiều chế độ ăn và phương pháp nấu
3. **Error Handling**: Các lỗi session expired được xử lý tự động
4. **Backward Compatibility**: Các API cũ vẫn hoạt động bình thường
5. **Workflow Flow**: Workflow sẽ dừng lại ở từng bước để chờ user input, không chạy tiếp đến kết quả cuối cùng ngay lập tức

## Files đã thay đổi

1. `app/graph/nodes/select_cooking_method_node.py` - Node mới
2. `app/graph/nodes/__init__.py` - Import các node mới
3. `app/graph/engine.py` - Cập nhật workflow và state
4. `app/routes/langgraph_workflow.py` - Thêm endpoints mới
5. `NEW_FEATURES.md` - Documentation này 