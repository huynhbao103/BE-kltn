# Format Dữ Liệu Trả Về Đã Tối Ưu Hóa

## Tổng Quan
Dữ liệu trả về đã được tối ưu hóa để giảm thiểu kích thước và chỉ chứa thông tin cần thiết cho frontend.

## Cấu Trúc Dữ Liệu Mới

### 1. Kết Quả Thành Công (status: "success")

```json
{
  "status": "success",
  "message": "Cảm xúc: Vui vẻ | BMI: 18.11 (Gầy) | Thông tin: bảo, 21 tuổi, 60kg, 182cm | Tình trạng bệnh: Cao huyết áp | (Đã sắp xếp lại theo mức độ phù hợp) | Đã tìm thấy 20 món ăn phù hợp nhất",
  "foods": [
    {
      "name": "Cá hấp",
      "id": "dish_001",
      "description": "Cá hấp ít muối, tốt cho người cao huyết áp",
      "category": "condition_Cao huyết áp",
      "cook_method": "Hấp",
      "diet": "Chế độ ăn giảm muối",
      "score": 8
    },
    {
      "name": "Thịt heo luộc",
      "id": "dish_002", 
      "description": "Thịt luộc ít dầu mỡ, phù hợp với cảm xúc vui vẻ",
      "category": "emotion_Vui vẻ",
      "cook_method": "Luộc",
      "diet": "Chế độ ăn giàu chất xơ",
      "score": 7
    }
  ],
  "user_info": {
    "name": "Nguyễn Văn A",
    "age": 25,
    "bmi": 22.5,
    "bmi_category": "Bình thường",
    "medical_conditions": ["Tiểu đường"]
  },
  "selected_emotion": "Vui vẻ",
  "selected_cooking_methods": ["Hấp", "Luộc"],
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

### 2. Cần Chọn Cảm Xúc (status: "need_emotion")

```json
{
  "status": "need_emotion",
  "emotion_prompt": {
    "message": "Bạn đang cảm thấy như thế nào?",
    "options": ["Vui vẻ", "Mệt mỏi", "Tức giận", "Bình thường"]
  },
  "session_id": "session_abc123"
}
```

### 3. Cần Chọn Phương Pháp Nấu (status: "need_cooking_method")

```json
{
  "status": "need_cooking_method", 
  "cooking_method_prompt": {
    "message": "Bạn thích phương pháp nấu nào?",
    "options": ["Luộc", "Hấp", "Nướng", "Xào", "Kho"]
  },
  "session_id": "session_abc123"
}
```

### 4. Câu Hỏi Không Thuộc Chủ Đề (status: "rejected")

```json
{
  "status": "rejected",
  "message": "Câu hỏi không thuộc chủ đề dinh dưỡng | Thông tin: Nguyễn Văn A, 25 tuổi, 65kg, 170cm | Tình trạng bệnh: Tiểu đường",
  "user_info": {
    "name": "Nguyễn Văn A",
    "age": 25,
    "weight": 65,
    "height": 170,
    "medical_conditions": ["Tiểu đường"]
  },
  "question": "Thời tiết hôm nay thế nào?",
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

### 5. Lỗi (status: "error")

```json
{
  "status": "error",
  "message": "Không tìm thấy user với ID: 507f1f77bcf86cd799439011",
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

## Thay Đổi Chính

### Trước Đây (Dữ liệu quá nhiều):
- `neo4j_data`: Toàn bộ dữ liệu từ Neo4j (rất lớn)
- `reranked_data`: Toàn bộ dữ liệu đã sắp xếp (rất lớn)
- `detailed_analysis`: Phân tích chi tiết (không cần thiết)
- `statistics`: Thống kê chi tiết (không cần thiết)
- `step`: Thông tin debug (không cần thiết)
- **Vấn đề 1**: Trả về tất cả món ăn từ mỗi bước lọc riêng biệt (bệnh lý, cảm xúc, BMI, phương pháp nấu)
- **Vấn đề 2**: Trả về món ăn không phù hợp với bệnh lý của user (ví dụ: gỏi cho người cao huyết áp)

### Bây Giờ (Dữ liệu tối ưu):
- `foods`: **Chỉ top 20 món ăn phù hợp nhất** đã được lọc tổng hợp theo tất cả tiêu chí
- `user_info`: Thông tin user cần thiết
- `selected_emotion`: Cảm xúc đã chọn
- `selected_cooking_methods`: Phương pháp nấu đã chọn
- `timestamp`: Thời gian tạo kết quả
- **Cải tiến 1**: Sắp xếp theo điểm số tổng hợp và chỉ trả về món ăn cuối cùng
- **Cải tiến 2**: **Chỉ trả về món ăn từ bệnh lý của user**, sau đó mới tính điểm theo cảm xúc và phương pháp nấu

## Lợi Ích

1. **Giảm kích thước dữ liệu**: Từ ~50KB xuống ~5KB
2. **Tăng tốc độ truyền tải**: Dữ liệu nhẹ hơn, load nhanh hơn
3. **Dễ xử lý frontend**: Cấu trúc đơn giản, rõ ràng
4. **Bảo mật**: Không lộ dữ liệu nội bộ không cần thiết
5. **Hiệu suất**: Giảm tải cho server và network
6. **Chất lượng kết quả**: Chỉ trả về món ăn phù hợp nhất thay vì tất cả món từ mỗi bước lọc
7. **Trải nghiệm người dùng**: Không bị quá tải thông tin, dễ chọn lựa
8. **Độ chính xác**: Chỉ trả về món ăn phù hợp với bệnh lý của user, không có món ăn không phù hợp
9. **An toàn sức khỏe**: Đảm bảo món ăn được khuyến nghị an toàn cho tình trạng bệnh lý

## Cách Sử Dụng Frontend

```javascript
// Xử lý kết quả thành công
if (response.status === 'success') {
  const foods = response.foods;
  const userInfo = response.user_info;
  const emotion = response.selected_emotion;
  const cookingMethods = response.selected_cooking_methods;
  
  // Hiển thị danh sách món ăn
  foods.forEach(food => {
    console.log(`${food.name} - ${food.cook_method} - ${food.diet}`);
  });
}

// Xử lý cần chọn cảm xúc
if (response.status === 'need_emotion') {
  const sessionId = response.session_id;
  const emotionOptions = response.emotion_prompt.options;
  // Hiển thị dialog chọn cảm xúc
}

// Xử lý cần chọn phương pháp nấu  
if (response.status === 'need_cooking_method') {
  const sessionId = response.session_id;
  const cookingOptions = response.cooking_method_prompt.options;
  // Hiển thị dialog chọn phương pháp nấu
}
``` 