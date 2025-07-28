from langgraph.graph import StateGraph, END
from typing import Dict, Any, TypedDict, Annotated, Optional, List
from app.graph.nodes.classify_topic_node import check_mode
from app.graph.nodes.calculate_bmi_node import calculate_bmi_from_user_id
from app.graph.nodes.query_neo4j_node import query_neo4j_for_foods
from app.graph.nodes.aggregate_suitable_foods_node import aggregate_suitable_foods
from app.graph.nodes.rerank_foods_node import rerank_foods
from app.graph.nodes.filter_allergies_node import filter_foods_by_allergies
# from app.graph.nodes.llm_check_food_suitability_node import check_food_suitability
from app.graph.nodes.fallback_query_node import create_fallback_query
from app.graph.nodes.process_cooking_request_node import process_cooking_request
from app.services.mongo_service import mongo_service
import jwt
import os
from datetime import datetime
from app.graph.nodes.select_cooking_method_node import select_cooking_method_node
from app.utils.session_store import save_state_to_redis, load_state_from_redis
from fastapi import HTTPException
# Định nghĩa state cho LangGraph
class WorkflowState(TypedDict):
    user_id: str
    question: str
    user_data: Dict[str, Any]
    topic_classification: str
    bmi_result: Dict[str, Any]
    neo4j_result: Dict[str, Any]
    filtered_result: Optional[Dict[str, Any]]
    aggregated_result: Dict[str, Any]
    rerank_result: Optional[Dict[str, Any]]
    llm_check_result: Optional[Dict[str, Any]]
    reranked_foods: Optional[Dict[str, Any]]
    fallback_attempt: Optional[int]
    final_result: Dict[str, Any]
    error: str
    step: str
    cooking_method_prompt: Optional[dict]
    selected_cooking_methods: Optional[List[str]]
    session_id: Optional[str]
    weather: str
    time_of_day: str
    previous_food_ids: Optional[List[str]]
    analysis_steps: Optional[List[Dict[str, str]]]
    analysis_shown: Optional[bool]
    cooking_request_warning: Optional[str]
    context_analysis_shown: Optional[bool]
    ignore_context_filter: Optional[bool]

# Node kiểm tra session đầu workflow

def check_session(state: WorkflowState) -> WorkflowState:
    """
    Kiểm tra state được truyền vào để quyết định luồng đi.
    State này đã được nạp từ Redis ở entry point nếu có session.
    """
    # Nếu state đã có cooking method (trường hợp tiếp tục luồng)
    if state.get("selected_cooking_methods"):
        return {**state, "step": "session_complete"}

    # Nếu không, đây là một lượt hỏi mới.
    return {**state, "step": "session_not_found"}

def analyze_and_generate_prompts(state: WorkflowState) -> WorkflowState:
    """
    Node thực hiện phân tích, lọc cooking method, và tạo prompt cho người dùng.
    Đây là điểm dừng của bước đầu tiên.
    """
    try:
        analysis_steps = []
        user_data = state.get("user_data", {})
        bmi_result = state.get("bmi_result", {})
        from app.services.graph_schema_service import GraphSchemaService
        from app.graph.nodes.classify_topic_node import extract_cooking_methods

        # --- PHÂN TÍCH BỆNH, BMI, CONTEXT ---
        medical_conditions = [c for c in user_data.get("medicalConditions", []) if c not in ["Không có", "Bình thường"]]
        cooking_methods_after_disease_filter = set()
        if medical_conditions:
            for condition in medical_conditions:
                diet_recs = GraphSchemaService.get_diet_recommendations_by_disease(condition)
                diet_details_msg = [f"{d['name']}: {d.get('description', '(Không có mô tả)')}" for d_name in diet_recs if (d := GraphSchemaService.get_diet_details_by_name(d_name))]
                analysis_steps.append({"step": "disease_analysis", "message": f"Đối với bệnh '{condition}', các chế độ ăn được khuyến nghị là: {'; '.join(diet_details_msg) if diet_details_msg else 'Chưa có.'}"})
                methods = GraphSchemaService.get_cook_methods_by_disease(condition)
                if methods:
                    cooking_methods_after_disease_filter.update(methods)
            analysis_steps.append({"step": "cooking_method_filter_disease", "message": f"Dựa trên bệnh, các phương pháp nấu phù hợp ban đầu là: {', '.join(cooking_methods_after_disease_filter) if cooking_methods_after_disease_filter else 'Không có.'}"})
        else:
            analysis_steps.append({"step": "disease_analysis", "message": "Bạn không có bệnh lý nền nào được ghi nhận."})
            cooking_methods_after_disease_filter.update(GraphSchemaService.get_all_cooking_methods())

        bmi_category = bmi_result.get("bmi_category")
        cooking_methods_after_bmi_filter = set()
        analysis_steps.append({"step": "bmi_analysis", "message": f"Chỉ số BMI của bạn được phân loại là '{bmi_category}'. Hệ thống sẽ tiếp tục lọc các phương pháp nấu."})
        if bmi_category:
            methods_for_bmi = GraphSchemaService.get_cook_methods_by_bmi(bmi_category)
            if methods_for_bmi:
                cooking_methods_after_bmi_filter = cooking_methods_after_disease_filter.intersection(methods_for_bmi)
                analysis_steps.append({"step": "cooking_method_filter_bmi", "message": f"Sau khi lọc theo BMI, các phương pháp nấu còn lại: {', '.join(cooking_methods_after_bmi_filter) if cooking_methods_after_bmi_filter else 'Không có.'}"})
            else:
                cooking_methods_after_bmi_filter = cooking_methods_after_disease_filter
        else:
            cooking_methods_after_bmi_filter = cooking_methods_after_disease_filter

        weather = state.get("weather")
        time_of_day = state.get("time_of_day")
        context_analysis_shown = state.get("context_analysis_shown", False)
        ignore_context_filter = state.get("ignore_context_filter", False)
        cooking_methods_after_context_filter = set()
        context_name, suggested_methods = None, None
        
        # Chỉ áp dụng context filter khi user không chọn lọc theo context (ignore_context_filter = True)
        # hoặc khi user chưa chọn cooking methods cụ thể
        should_apply_context = (weather and time_of_day and 
                              not ignore_context_filter and 
                              not state.get("selected_cooking_methods"))
        
        if should_apply_context:
            context_name, suggested_methods = GraphSchemaService.get_context_and_cook_methods(weather, time_of_day)
            if context_name and suggested_methods:
                analysis_steps.append({"step": "context_analysis", "message": f"Dựa theo nhiệt độ hiện tại {context_name} gợi ý các cách chế biến phù hợp là: {', '.join(suggested_methods)}."})
                cooking_methods_after_context_filter = cooking_methods_after_bmi_filter.intersection(suggested_methods)
                context_analysis_shown = True
            else:
                analysis_steps.append({"step": "context_analysis_failed", "message": f"Không tìm thấy gợi ý đặc biệt cho thời tiết '{weather}' và thời điểm '{time_of_day}'. Giữ nguyên danh sách trước đó."})
                cooking_methods_after_context_filter = cooking_methods_after_bmi_filter
        else:
            cooking_methods_after_context_filter = cooking_methods_after_bmi_filter
            context_analysis_shown = False

        # --- TRÍCH XUẤT PHƯƠNG PHÁP NẤU TỪ CÂU HỎI ---
        question = state.get("question", "")
        extracted_methods = extract_cooking_methods(question)
        # Nếu detect được phương pháp nấu từ câu hỏi, bỏ qua prompt chọn phương pháp nấu, trả về luôn analysis_steps
        if extracted_methods:
            return {
                **state,
                "analysis_steps": analysis_steps,
                "selected_cooking_methods": extracted_methods,
                "context_analysis_shown": context_analysis_shown,
                "step": "analysis_complete",
                "final_result": {
                    "status": "analysis_complete",
                    "analysis_steps": analysis_steps,
                    "selected_cooking_methods": extracted_methods,
                    "context_analysis_shown": context_analysis_shown,
                    "session_id": state.get("session_id")
                }
            }

        # Nếu không detect được phương pháp nấu, trả về prompt chọn phương pháp nấu như cũ
        final_cooking_methods = list(cooking_methods_after_context_filter)
        if not final_cooking_methods:
            analysis_steps.append({"step": "fallback_cooking_methods", "message": "Không có phương pháp nấu nào phù hợp với tất cả các tiêu chí. Hệ thống sẽ hiển thị tất cả các lựa chọn."})
            final_cooking_methods = GraphSchemaService.get_all_cooking_methods()

        cooking_method_prompt = {
            "prompt_type": "select",
            "message": "Dựa trên phân tích, hãy chọn phương pháp chế biến bạn muốn:",
            "options": final_cooking_methods
        }

        current_state = {**state, "analysis_steps": analysis_steps, "cooking_method_prompt": cooking_method_prompt, "analysis_shown": False, "context_analysis_shown": context_analysis_shown, "selected_cooking_methods": None}
        session_id = save_state_to_redis(current_state)
        current_state["session_id"] = session_id

        return {
            **current_state,
            "step": "analysis_complete",
            "final_result": {
                "status": "analysis_complete",
                "analysis_steps": analysis_steps,
                "cooking_method_prompt": cooking_method_prompt,
                "session_id": session_id,
                "context_analysis_shown": context_analysis_shown
            }
        }
    except Exception as e:
        return {**state, "error": f"Lỗi trong bước phân tích: {str(e)}", "step": "analysis_error"}


def identify_user(state: WorkflowState) -> WorkflowState:
    """Node 1: Xác định user từ user_id """
    try:
        # Lấy user_id từ state (được truyền từ API)
        user_id = state.get("user_id")
        if not user_id:
            return {
                **state,
                "error": "Không có user_id được cung cấp",
                "step": "user_identification_failed"
            }
        
        # Kiểm tra format user_id (phải là ObjectId hợp lệ)
        if "@" in user_id:
            return {
                **state,
                "error": "Chỉ chấp nhận user_id, không chấp nhận email",
                "step": "invalid_user_format"
            }
        
        # Lấy thông tin user đầy đủ bằng user_id
        user_data = mongo_service.get_user_health_data(user_id)
        
        if not user_data:
            return {
                **state,
                "error": f"Không tìm thấy user với ID: {user_id}",
                "step": "user_not_found"
            }
        
        return {
            **state,
            "user_data": user_data,
            "step": "user_identified"
        }
        
    except Exception as e:
        return {
            **state,
            "error": f"Lỗi xác định user: {str(e)}",
            "step": "user_identification_error"
        }

def classify_topic(state: WorkflowState) -> WorkflowState:
    """Node 2: Phân loại chủ đề câu hỏi"""
    try:
        question = state.get("question", "")
        if not question:
            return {
                **state,
                "error": "Không có câu hỏi được cung cấp",
                "step": "topic_classification_failed"
            }
        # Phân loại chủ đề
        classification = check_mode(question)
        # Nếu là cooking_request thì reset selected_cooking_methods nếu detect được phương pháp nấu mới
        if classification == "cooking_request":
            from app.graph.nodes.classify_topic_node import extract_cooking_methods
            new_methods = extract_cooking_methods(question)
            # Nếu detect được phương pháp nấu mới hoặc user hỏi "tất cả", reset selected_cooking_methods
            if new_methods or (isinstance(new_methods, list) and new_methods == ["ALL"]):
                return {
                    **state,
                    "topic_classification": classification,
                    "selected_cooking_methods": None,  # Reset để process_cooking_request xử lý lại
                    "step": "topic_classified"
                }
        return {
            **state,
            "topic_classification": classification,
            "step": "topic_classified"
        }
    except Exception as e:
        return {
            **state,
            "error": f"Lỗi phân loại chủ đề: {str(e)}",
            "step": "topic_classification_error"
        }

def calculate_bmi(state: WorkflowState) -> WorkflowState:
    """ Node 5: Tính BMI cho user """
    try:
        user_id = state.get("user_id")
        if not user_id:
            return {
                **state,
                "error": "Không có user_id để tính BMI",
                "step": "bmi_calculation_failed"
            }
        
        # Tính BMI
        bmi_result = calculate_bmi_from_user_id(user_id)
        if "error" in bmi_result:
            return {
                **state,
                "error": f"Lỗi tính BMI: {bmi_result['error']}",
                "step": "bmi_calculation_error"
            }
        
        return {
            **state,
            "bmi_result": bmi_result,
            "step": "bmi_calculated"
        }
        
    except Exception as e:
        return {
            **state,
            "error": f"Lỗi tính BMI: {str(e)}",
            "step": "bmi_calculation_error"
        }

def query_neo4j(state: WorkflowState) -> WorkflowState:
    """ Node 6: Truy vấn Neo4j để tìm thực phẩm phù hợp """
    try:
        user_data = state.get("user_data", {})
        if not user_data:
            return {
                **state,
                "error": "Không có thông tin user để truy vấn Neo4j",
                "step": "neo4j_query_failed"
            }
        
        # Kiểm tra xem có phải fallback query không
        fallback_attempt = state.get("fallback_attempt", 0)
        
        if fallback_attempt > 0:
            # Tạo fallback query
            fallback_result = create_fallback_query(user_data, fallback_attempt)
            if fallback_result["status"] == "success":
                # Sử dụng fallback query với GraphSchemaService
                from app.services.graph_schema_service import GraphSchemaService
                query = fallback_result["query"]
                params = fallback_result["params"]
                
                result = GraphSchemaService.run_custom_query(query, params)
                neo4j_result = {
                    "status": "success",
                    "data": result,
                    "fallback_level": fallback_attempt,
                    "message": f"Kết quả từ fallback query level {fallback_attempt}"
                }
            else:
                return {
                    **state,
                    "error": f"Lỗi tạo fallback query: {fallback_result['message']}",
                    "step": "fallback_query_error"
                }
        else:
            # Truy vấn Neo4j bình thường với state đầy đủ
            query_result = query_neo4j_for_foods(state)
            # Lấy kết quả từ query_result vì hàm trả về {"query_result": result}
            neo4j_result = query_result.get("query_result", query_result)
        
        return {
            **state,
            "neo4j_result": neo4j_result,
            "step": "neo4j_queried"
        }
        
    except Exception as e:
        return {
            **state,
            "error": f"Lỗi truy vấn Neo4j: {str(e)}",
            "step": "neo4j_query_error"
        }

def filter_allergies(state: WorkflowState) -> WorkflowState:
    """ Node 7: Lọc món ăn theo dị ứng của người dùng """
    try:
        # Gọi node lọc dị ứng
        filter_result = filter_foods_by_allergies(state)
        
        # Lấy filtered_result từ kết quả
        filtered_result = filter_result.get("filtered_result", {})
        
        return {
            **state,
            "filtered_result": filtered_result,
            "step": "allergies_filtered"
        }
        
    except Exception as e:
        return {
            **state,
            "error": f"Lỗi lọc món ăn theo dị ứng: {str(e)}",
            "step": "allergy_filter_error"
        }

def aggregate_foods(state: WorkflowState) -> WorkflowState:
    """ Node 8: Tổng hợp các món ăn phù hợp """
    try:
        # Sử dụng filtered_result thay vì neo4j_result
        filtered_result = state.get("filtered_result", {})
        if filtered_result:
            # Cập nhật state để sử dụng filtered_result
            state["query_result"] = filtered_result
        
        # Gọi node tổng hợp
        aggregate_result = aggregate_suitable_foods(state)
        
        # Lấy aggregated_result từ kết quả
        aggregated_result = aggregate_result.get("aggregated_result", {})
        
        return {
            **state,
            "aggregated_result": aggregated_result,
            "step": "foods_aggregated"
        }
        
    except Exception as e:
        return {
            **state,
            "error": f"Lỗi tổng hợp món ăn: {str(e)}",
            "step": "aggregation_error"
        }

def rerank_foods_wrapper(state: WorkflowState) -> WorkflowState:
    """ Node 9: Rerank các món ăn sử dụng LLM """
    try:
        rerank_result_from_node = rerank_foods(state)
        reranked_result = rerank_result_from_node.get("rerank_result", {})

        # Nếu LLM rerank và trả về danh sách rỗng, KHÔNG fallback sang aggregated foods nữa
        if reranked_result.get("status") == "success" and not reranked_result.get("ranked_foods"):
            reranked_result["message"] = "Không có món ăn nào đáp ứng yêu cầu của bạn."
            reranked_result["total_count"] = 0
            # KHÔNG fallback sang aggregated_foods

        return {
            **state,
            "rerank_result": reranked_result,
            "step": "foods_reranked"
        }
    except Exception as e:
        return {
            **state,
            "error": f"Lỗi rerank món ăn: {str(e)}",
            "step": "rerank_error"
        }



def generate_final_result(state: WorkflowState) -> WorkflowState:
    """ Node 10: Tạo kết quả cuối cùng """
    try:
        user_data = state.get("user_data", {})
        question = state.get("question", "")
        topic_classification = state.get("topic_classification", "")
        bmi_result = state.get("bmi_result", {})
        rerank_result = state.get("rerank_result", {})
        previous_food_ids = state.get("previous_food_ids", [])
        session_id = state.get("session_id")

        message_parts = []
        medical_conditions = user_data.get("medicalConditions", [])
        final_foods = []
        newly_suggested_food_ids = []
        
        # Thêm warning message nếu có cooking request
        cooking_request_warning = state.get("cooking_request_warning")
        if cooking_request_warning:
            message_parts.append(f"💡 Lưu ý: {cooking_request_warning}")
        
        # Thêm thông tin cảnh báo dị ứng
        filtered_result = state.get("filtered_result", {})
        allergy_warnings = filtered_result.get("allergy_warnings", {})
        if allergy_warnings:
            warning_messages = []
            for source_key, warnings in allergy_warnings.items():
                for warning in warnings:
                    dish_name = warning.get("dish_name", "Unknown")
                    warning_text = ", ".join(warning.get("warnings", []))
                    if warning_text:
                        warning_messages.append(f"⚠️ {dish_name}: {warning_text}")
            
            if warning_messages:
                message_parts.append("Cảnh báo dị ứng: " + " | ".join(warning_messages))

        if rerank_result and rerank_result.get("status") == "success":
            ranked_foods = rerank_result.get("ranked_foods", [])
            rerank_criteria = rerank_result.get("rerank_criteria", {})
            total_count = rerank_result.get("total_count", 0)
            selected_cooking_methods = state.get("selected_cooking_methods", [])

            # Chỉ giữ lại log kiểm tra duplicate
            for food in ranked_foods:
                food_id = food.get("dish_id", "")
                if food_id:
                    newly_suggested_food_ids.append(food_id)
                final_foods.append({
                    "name": food.get("dish_name", "Unknown"),
                    "id": food_id,
                    "description": food.get("description", ""),
                    "category": "ranked",
                    "cook_method": food.get("cook_method", ""),
                    "diet": food.get("diet_name", ""),
                    "bmi_category": food.get("bmi_category", ""),
                    "calories": food.get("calories", 0),
                    "protein": food.get("protein", 0),
                    "fat": food.get("fat", 0),
                    "carbs": food.get("carbs", 0)
                })

            # Log kiểm tra duplicate trong foods trả về
            for food in final_foods:
                if food.get("id") in previous_food_ids:
                    pass # Tạm thời vô hiệu hóa log

            if final_foods:
                food_names = [food.get("name", "Unknown") for food in final_foods]
                message_parts.append(f"Đây là những món ăn phù hợp với yêu cầu của bạn: {', '.join(food_names)}")
                # message_parts.append(f"Tổng cộng có {total_count} món ăn để bạn lựa chọn")
            else:
                if previous_food_ids:
                    message_parts.append("Chúng tôi đã gợi ý hết các món ăn phù hợp với yêu cầu của bạn rồi.")
                else:
                    message_parts.append("Xin lỗi, chúng tôi không tìm thấy món ăn nào phù hợp với yêu cầu của bạn")

        detailed_message = " | ".join(message_parts)

        final_result = {
            "status": "success",
            "message": detailed_message,
            "foods": final_foods,
            "total_count": len(final_foods),
            "user_info": {
                "name": user_data.get("name", "Unknown"),
                "age": user_data.get("age", "N/A"),
                "bmi": bmi_result.get("bmi", "N/A") if bmi_result else "N/A",
                "bmi_category": bmi_result.get("bmi_category", "N/A") if bmi_result else "N/A",
                "medical_conditions": medical_conditions if medical_conditions and medical_conditions != ["Không có"] else [],
                "allergies": user_data.get("allergies", [])
            },
            "selected_cooking_methods": state.get("selected_cooking_methods", []),
            "rerank_criteria": rerank_result.get("rerank_criteria", {}) if rerank_result else {},
            "allergy_info": {
                "user_allergies": user_data.get("allergies", []),
                "original_food_count": filtered_result.get("original_food_count", 0),
                "filtered_food_count": filtered_result.get("filtered_food_count", 0),
                "allergy_warnings": allergy_warnings
            },
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        }

        previous_food_ids = set(state.get("previous_food_ids", []))
        previous_food_names = set(state.get("previous_food_names", []))
        # Lọc lại final_foods để không trùng id, dish_id hoặc name
        filtered_final_foods = []
        for food in final_foods:
            food_id = food.get("id")
            dish_id = food.get("dish_id")
            name = food.get("name")
            if (
                (food_id and food_id in previous_food_ids) or
                (dish_id and dish_id in previous_food_ids) or
                (name and name in previous_food_names)
            ):
                continue
            filtered_final_foods.append(food)
        # Cập nhật previous_food_ids và previous_food_names
        newly_suggested_food_ids = []
        newly_suggested_food_names = []
        for food in filtered_final_foods:
            if food.get("id"):
                newly_suggested_food_ids.append(food.get("id"))
            if food.get("dish_id"):
                newly_suggested_food_ids.append(food.get("dish_id"))
            if food.get("name"):
                newly_suggested_food_names.append(food.get("name"))
        updated_previous_food_ids = list(previous_food_ids.union(newly_suggested_food_ids))
        updated_previous_food_names = list(previous_food_names.union(newly_suggested_food_names))
        # DEBUG: Log các id và tên đã gợi ý
        print("[DEBUG] previous_food_ids:", previous_food_ids)
        print("[DEBUG] previous_food_names:", previous_food_names)
        print("[DEBUG] newly_suggested_food_ids:", newly_suggested_food_ids)
        print("[DEBUG] newly_suggested_food_names:", newly_suggested_food_names)
        print("[DEBUG] updated_previous_food_ids:", updated_previous_food_ids)
        print("[DEBUG] updated_previous_food_names:", updated_previous_food_names)
        print("[DEBUG] ids các món trả về:", [food.get("id") or food.get("dish_id") for food in filtered_final_foods])
        print("[DEBUG] names các món trả về:", [food.get("name") for food in filtered_final_foods])

        # Lưu lại state mới vào Redis để đảm bảo loại trừ món đã gợi ý
        if session_id:
            try:
                save_state_to_redis({**state, "previous_food_ids": updated_previous_food_ids, "previous_food_names": updated_previous_food_names}, session_id)
            except Exception as e:
                # Log lỗi ra console phía server, không trả về cho client
                print(f"ERROR: [generate_final_result] Failed to save updated previous_food_ids to Redis: {e}")

        return {
            **state,
            "final_result": final_result,
            "previous_food_ids": updated_previous_food_ids,
            "previous_food_names": updated_previous_food_names,
            "step": "result_generated"
        }
    except Exception as e:
        session_id = state.get("session_id")
        return {
            **state,
            "error": f"Lỗi tạo kết quả: {str(e)}",
            "step": "result_generation_error"
        }

def should_continue(state: WorkflowState) -> str:
    if state.get("error"):
        return "end_with_error"
    step = state.get("step", "")
    if step == "start":
        return "check_session"
    elif step in ["session_not_found", "session_error"]:
        # Nếu không có session, bắt đầu luồng mới bằng cách xác định người dùng
        return "identify_user"

    elif step == "session_complete":
        # Session có đủ thông tin, đi thẳng đến tính toán
        return "query_neo4j"
    elif step == "user_identified":
        return "classify_topic"
    elif step == "topic_classified":
        # Sau khi phân loại chủ đề, kiểm tra loại yêu cầu
        topic_classification = state.get("topic_classification")
        if topic_classification == "không liên quan":
            return "end_rejected"
        elif topic_classification == "cooking_request":
            return "process_cooking_request" # Xử lý yêu cầu cooking method
        else:
            return "calculate_bmi" # Chuyển đến tính BMI cho yêu cầu tư vấn chung
    elif step == "bmi_calculated":
         return "analyze_and_generate_prompts" # Chuyển đến phân tích sau khi tính BMI
    elif step == "analysis_complete":
        return "end_success" # Dừng lại sau khi phân tích

    elif step == "cooking_request_processed":
        # Sau khi xử lý cooking request, đi thẳng đến query neo4j
        return "query_neo4j"
    elif step == "cooking_method_selected":
        # Step này chỉ được gọi khi FE gửi lên cả emotion và cooking method
        return "query_neo4j"
    elif step == "neo4j_queried":
        return "filter_allergies"
    elif step == "allergies_filtered":
        return "aggregate_foods"
    elif step == "foods_aggregated":
        return "rerank_foods"
    elif step == "foods_reranked":
        return "generate_result"
    elif step == "result_generated":
        return "end_success"
    return "end_with_error"

# Node end_need_emotion_and_cooking

def end_with_error(state: WorkflowState) -> WorkflowState:
    """Kết thúc với lỗi"""
    session_id = state.get("session_id")
    return {
        **state,
        "final_result": {
            "status": "error",
            "message": state.get("error", "Lỗi không xác định"),
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        }
    }

def end_rejected(state: WorkflowState) -> WorkflowState:
    """Kết thúc khi câu hỏi không thuộc chủ đề"""
    user_data = state.get("user_data", {})
    question = state.get("question", "")
    session_id = state.get("session_id")
    # Tạo message chi tiết cho trường hợp rejected
    user_name = user_data.get("name", "Unknown")
    user_age = user_data.get("age", "N/A")
    user_weight = user_data.get("weight", "N/A")
    user_height = user_data.get("height", "N/A")
    medical_conditions = user_data.get("medicalConditions", [])
    
    message_parts = [f"Xin lỗi, câu hỏi này không thuộc chủ đề gợi ý món ăn mà tôi có thể tư vấn"]
    # message_parts.append(f"Thông tin của bạn: {user_name}, {user_age} tuổi, {user_weight}kg, {user_height}cm")
    
    # Thêm thông tin bệnh nếu có
    if medical_conditions and medical_conditions != ["Không có"]:
        conditions_str = ", ".join(medical_conditions)
        message_parts.append(f"Tình trạng bệnh: {conditions_str}")
    
    message = " | ".join(message_parts)
    
    return {
        **state,
        "final_result": {
            "status": "rejected",
            "message": message,
            "user_info": {
                "name": user_name,
                "age": user_age,
                "weight": user_weight,
                "height": user_height,
                "medical_conditions": medical_conditions if medical_conditions and medical_conditions != ["Không có"] else []
            },
            "question": question,
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        }
    }


def end_success(state: WorkflowState) -> WorkflowState:
    """
    Kết thúc thành công. Cập nhật lại state vào Redis để lưu lại các món đã gợi ý.
    Luôn trả về session_id trong final_result.
    """
    session_id = state.get("session_id")
    if session_id:
        try:
            save_state_to_redis(state, session_id)
        except Exception as e:
            # Không nên raise lỗi ở đây để tránh làm hỏng kết quả trả về cho user
            print(f"ERROR: [end_success] Failed to save state to Redis: {e}")
    # Đảm bảo final_result luôn có session_id
    final_result = state.get("final_result", {})
    if isinstance(final_result, dict):
        final_result["session_id"] = session_id
        return {**state, "final_result": final_result}
    else:
        return {**state, "final_result": {"session_id": session_id}}

# Tạo LangGraph workflow
def create_workflow() -> StateGraph:
    """Tạo LangGraph workflow"""
    # Tạo graph
    workflow = StateGraph(WorkflowState)
    # Thêm nodes
    workflow.add_node("check_session", check_session)
    workflow.add_node("identify_user", identify_user)
    workflow.add_node("classify_topic", classify_topic)
    workflow.add_node("calculate_bmi", calculate_bmi)
    workflow.add_node("analyze_and_generate_prompts", analyze_and_generate_prompts) # Thêm node mới
    workflow.add_node("process_cooking_request", process_cooking_request) # Thêm node xử lý cooking request
    workflow.add_node("query_neo4j", query_neo4j)
    workflow.add_node("filter_allergies", filter_allergies)
    workflow.add_node("aggregate_foods", aggregate_foods)
    workflow.add_node("rerank_foods", rerank_foods_wrapper)
    workflow.add_node("generate_result", generate_final_result)
    workflow.add_node("end_with_error", end_with_error)
    workflow.add_node("end_rejected", end_rejected)
    workflow.add_node("end_success", end_success)
    # Thêm router
    workflow.add_conditional_edges(
        "check_session",
        should_continue,
        {
            "identify_user": "identify_user",
            "calculate_bmi": "calculate_bmi",
            "query_neo4j": "query_neo4j"
        }
    )
    workflow.add_conditional_edges(
        "identify_user",
        should_continue,
        {
            "classify_topic": "classify_topic",
            "end_with_error": "end_with_error"
        }
    )
    workflow.add_conditional_edges(
        "classify_topic",
        should_continue,
        {
            "process_cooking_request": "process_cooking_request",
            "calculate_bmi": "calculate_bmi", # Sửa luồng
            "end_rejected": "end_rejected"
        }
    )
 
    
    workflow.add_conditional_edges(
        "calculate_bmi",
        should_continue,
        {
            "analyze_and_generate_prompts": "analyze_and_generate_prompts", # Sửa luồng
            "end_with_error": "end_with_error"
        }
    )

    workflow.add_conditional_edges(
        "analyze_and_generate_prompts", # Thêm điều kiện cho node mới
        should_continue,
        {
            "end_success": "end_success",
            "end_with_error": "end_with_error"
        }
    )



    workflow.add_conditional_edges(
        "process_cooking_request", # Thêm điều kiện cho node xử lý cooking request
        should_continue,
        {
            "query_neo4j": "query_neo4j",
            "end_with_error": "end_with_error"
        }
    )

    workflow.add_conditional_edges(
        "query_neo4j",
        should_continue,
        {
            "filter_allergies": "filter_allergies",
            "end_with_error": "end_with_error"
        }
    )
    workflow.add_conditional_edges(
        "filter_allergies",
        should_continue,
        {
            "aggregate_foods": "aggregate_foods",
            "end_with_error": "end_with_error"
        }
    )
    workflow.add_conditional_edges(
        "aggregate_foods",
        should_continue,
        {
            "rerank_foods": "rerank_foods",
            "end_with_error": "end_with_error"
        }
    )
    workflow.add_conditional_edges(
        "rerank_foods",
        should_continue,
        {
            "generate_result": "generate_result",
            "end_with_error": "end_with_error"
        }
    )
    workflow.add_conditional_edges(
        "generate_result",
        should_continue,
        {
            "end_success": "end_success",
            "end_with_error": "end_with_error"
        }
    )
    # Set entry point
    workflow.set_entry_point("check_session")
    # Add end nodes
    workflow.add_edge("end_with_error", END)
    workflow.add_edge("end_rejected", END)
    workflow.add_edge("end_success", END)
    return workflow

# Tạo workflow instance
workflow_graph = create_workflow().compile()

def run_langgraph_workflow_until_selection(user_id: str, question: str, weather: str, time_of_day: str, session_id: str = None, ignore_context_filter: bool = False) -> dict:
    try:
        # State mặc định cho một session hoàn toàn mới
        initial_state = {
            "user_id": user_id,
            "question": question,
            "user_data": {},
            "weather": weather,
            "time_of_day": time_of_day,
            "session_id": session_id,
            "topic_classification": "",
            "bmi_result": {},
            "neo4j_result": {},
            "filtered_result": None,
            "aggregated_result": {},
            "reranked_foods": None,
            "fallback_attempt": 0,
            "final_result": {},
            "error": "",
            "step": "start",
            "cooking_method_prompt": None,
            "selected_cooking_methods": None,
            "previous_food_ids": [],
            "analysis_steps": [],
            "analysis_shown": False,
            "cooking_request_warning": None,
            "context_analysis_shown": False,
            "ignore_context_filter": ignore_context_filter
        }

        if session_id:
            try:
                loaded_state = load_state_from_redis(session_id)
                # Merge toàn bộ state cũ vào initial_state (ưu tiên giá trị đã lưu nếu trùng key)
                merged_state = {**initial_state, **loaded_state}
                initial_state = merged_state
            except Exception as e:
                # Lỗi không tìm thấy session là bình thường, không cần log ồn ào
                pass

        result = workflow_graph.invoke(initial_state)
        # Nếu workflow dừng lại để hỏi cả cảm xúc và phương pháp nấu
        if result.get("final_result", {}).get("status") == "analysis_complete":
            return result["final_result"]
        # Các trường hợp kết thúc khác, trả về final_result
        return result.get("final_result", {
            "status": "error",
            "message": "Không có kết quả hoặc workflow kết thúc bất thường"
        })
    except Exception as e:
        print(f"Error in run_langgraph_workflow_until_selection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi chạy workflow: {str(e)}")

def continue_workflow_with_cooking_method(session_id: str, cooking_methods: List[str], user_id: str) -> dict:
    """Tải state, cập nhật cooking methods, và tiếp tục workflow."""
    try:
        # Tải state từ session
        state = load_state_from_redis(session_id)
        
        # Cập nhật thông tin từ input
        state["selected_cooking_methods"] = cooking_methods
        
        # Quan trọng: Cập nhật lại user_id từ token hiện tại
        state["user_id"] = user_id
        
        # Đặt step để workflow tiếp tục từ điểm tính toán
        state["step"] = "cooking_method_selected" # Bắt đầu từ đây để truy vấn
        
        # Xóa các prompt cũ để tránh nhầm lẫn
        state.pop("cooking_method_prompt", None)
        # Giữ lại analysis_steps để tham khảo

        # Gọi invoke để tiếp tục workflow
        result = workflow_graph.invoke(state)
        
        # Trả về kết quả cuối cùng
        return result.get("final_result", {
            "status": "error",
            "message": "Không có kết quả sau khi xử lý."
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tiếp tục workflow: {str(e)}")

