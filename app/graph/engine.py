from langgraph.graph import StateGraph, END
from typing import Dict, Any, TypedDict, Annotated, Optional, List
from app.graph.nodes.classify_topic_node import check_mode
from app.graph.nodes.calculate_bmi_node import calculate_bmi_from_user_id
from app.graph.nodes.query_neo4j_node import query_neo4j_for_foods
from app.graph.nodes.aggregate_suitable_foods_node import aggregate_suitable_foods
from app.graph.nodes.rerank_foods_node import rerank_foods
# from app.graph.nodes.llm_check_food_suitability_node import check_food_suitability
from app.graph.nodes.fallback_query_node import create_fallback_query
from app.services.mongo_service import mongo_service
import jwt
import os
from datetime import datetime
from app.graph.nodes.select_emotion_node import select_emotion_node
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
    aggregated_result: Dict[str, Any]
    rerank_result: Optional[Dict[str, Any]]
    llm_check_result: Optional[Dict[str, Any]]
    reranked_foods: Optional[Dict[str, Any]]
    fallback_attempt: Optional[int]
    final_result: Dict[str, Any]
    error: str
    step: str
    emotion_prompt: Optional[dict]
    selected_emotion: Optional[str]
    cooking_method_prompt: Optional[dict]
    selected_cooking_methods: Optional[List[str]]
    session_id: Optional[str]
    weather: str
    time_of_day: str
    previous_food_ids: Optional[List[str]]

# Node kiểm tra session đầu workflow

def check_session(state: WorkflowState) -> WorkflowState:
    """
    Kiểm tra state được truyền vào để quyết định luồng đi.
    State này đã được nạp từ Redis ở entry point nếu có session.
    """
    # Nếu state đã có emotion và cooking method (trường hợp tiếp tục luồng từ `continue_...`)
    if state.get("selected_emotion") and state.get("selected_cooking_methods"):
        print("DEBUG: [check_session] State contains selections. Continuing to calculation.")
        return {**state, "step": "session_complete"}

    # Nếu không, đây là một lượt hỏi mới, cần bắt đầu luồng xác định người dùng.
    # Logic nạp session đã được xử lý ở `run_langgraph_workflow_until_selection`.
    print("DEBUG: [check_session] No selections in state. Starting new user identification flow.")
    return {**state, "step": "session_not_found"}

def identify_user(state: WorkflowState) -> WorkflowState:
    """Node 1: Xác định user từ user_id """
    print(f"DEBUG: identify_user - Starting with user_id: {state.get('user_id')}")
    print(f"DEBUG: identify_user - Question: {state.get('question')}")
    print(f"DEBUG: identify_user - Current step: {state.get('step')}")
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
    print(f"DEBUG: classify_topic - Starting with question: {state.get('question')}")
    print(f"DEBUG: classify_topic - User data: {state.get('user_data', {}).get('name', 'Unknown')}")
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

def select_emotion_node_wrapper(state: WorkflowState) -> WorkflowState:
    """ Node 3: Yêu cầu người dùng chọn cảm xúc hiện tại """
    try:
        # Kiểm tra xem đã có selected_emotion chưa
        if state.get("selected_emotion"):
            # Nếu đã chọn cảm xúc, tiếp tục đến node tiếp theo
            return {
                **state,
                "step": "emotion_selected"
            }
        else:
            # Nếu chưa chọn, tạo prompt và dừng lại
            emotion_prompt = select_emotion_node()
            return {
                **state,
                "emotion_prompt": emotion_prompt,
                "step": "emotion_prompt_generated"
            }
    except Exception as e:
        return {
            **state,
            "error": f"Lỗi chọn cảm xúc: {str(e)}",
            "step": "emotion_selection_error"
        }

def select_cooking_method_node_wrapper(state: WorkflowState) -> WorkflowState:
    """ Node 4: Yêu cầu người dùng chọn phương pháp nấu """
    try:
        # Kiểm tra xem đã có selected_cooking_methods chưa
        if state.get("selected_cooking_methods"):
            # Nếu đã chọn phương pháp nấu, tiếp tục đến node tiếp theo
            return {
                **state,
                "step": "cooking_method_selected"
            }
        else:
            # Nếu chưa chọn, tạo prompt và dừng lại
            cooking_method_prompt = select_cooking_method_node()
            return {
                **state,
                "cooking_method_prompt": cooking_method_prompt,
                "step": "cooking_method_prompt_generated"
            }
    except Exception as e:
        return {
            **state,
            "error": f"Lỗi chọn phương pháp nấu: {str(e)}",
            "step": "cooking_method_selection_error"
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

def aggregate_foods(state: WorkflowState) -> WorkflowState:
    """ Node 7: Tổng hợp các món ăn phù hợp """
    try:
        # Gọi node tổng hợp
        aggregate_result = aggregate_suitable_foods(state)
        
        # Debug: Kiểm tra kết quả từ aggregate_suitable_foods
        print(f"DEBUG: aggregate_result keys = {aggregate_result.keys()}")
        print(f"DEBUG: aggregate_result type = {type(aggregate_result)}")
        
        # Lấy aggregated_result từ kết quả
        aggregated_result = aggregate_result.get("aggregated_result", {})
        
        # Debug: Kiểm tra aggregated_result
        print(f"DEBUG: aggregated_result status = {aggregated_result.get('status')}")
        print(f"DEBUG: aggregated_result keys = {aggregated_result.keys() if isinstance(aggregated_result, dict) else 'Not a dict'}")
        
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
    """ Node 8: Rerank các món ăn sử dụng LLM """
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
    """ Node 9: Tạo kết quả cuối cùng """
    try:
        user_data = state.get("user_data", {})
        question = state.get("question", "")
        topic_classification = state.get("topic_classification", "")
        bmi_result = state.get("bmi_result", {})
        rerank_result = state.get("rerank_result", {})
        selected_emotion = state.get("selected_emotion")
        previous_food_ids = state.get("previous_food_ids", [])
        session_id = state.get("session_id")

        message_parts = []
        medical_conditions = user_data.get("medicalConditions", [])
        final_foods = []
        newly_suggested_food_ids = []
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
                    print(f"DUPLICATE WARNING: Food '{food.get('name')}' ({food.get('id')}) đã từng được gợi ý!")

            if final_foods:
                food_names = [food.get("name", "Unknown") for food in final_foods[:5]]
                if len(final_foods) > 5:
                    food_names = [food.get("name", "Unknown") for food in final_foods]
                message_parts.append(f"Danh sách món ăn phù hợp: {', '.join(food_names)}")
                message_parts.append(f"Tổng cộng: {total_count} món ăn")
            else:
                if previous_food_ids:
                    message_parts.append("Chúng tôi đã gợi ý hết các món ăn phù hợp với yêu cầu của bạn.")
                else:
                    message_parts.append(" Chúng tôi không có món ăn phù hợp với các tiêu chí của bạn")

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
                "medical_conditions": medical_conditions if medical_conditions and medical_conditions != ["Không có"] else []
            },
            "selected_emotion": selected_emotion,
            "selected_cooking_methods": state.get("selected_cooking_methods", []),
            "rerank_criteria": rerank_result.get("rerank_criteria", {}) if rerank_result else {},
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        }

        previous_food_ids = state.get("previous_food_ids", [])
        newly_suggested_food_ids = [food.get("id") or food.get("dish_id") for food in final_foods if food.get("id") or food.get("dish_id")]
        updated_previous_food_ids = list(set(previous_food_ids + newly_suggested_food_ids))

        # Lưu lại state mới vào Redis để đảm bảo loại trừ món đã gợi ý
        if session_id:
            try:
                save_state_to_redis({**state, "previous_food_ids": updated_previous_food_ids}, session_id)
            except Exception as e:
                print(f"ERROR: [generate_final_result] Failed to save updated previous_food_ids to Redis: {e}")

        return {
            **state,
            "final_result": final_result,
            "previous_food_ids": updated_previous_food_ids,
            "step": "result_generated"
        }
    except Exception as e:
        session_id = state.get("session_id")
        return {
            **state,
            "error": f"Lỗi tạo kết quả: {str(e)}",
            "step": "result_generation_error",
            "final_result": {
                "status": "error",
                "message": f"Lỗi tạo kết quả: {str(e)}",
                "session_id": session_id
            }
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
    elif step == "need_emotion_and_cooking":
        # Dừng lại để FE lấy cả hai prompt
        return "end_need_emotion_and_cooking"
    elif step == "session_complete":
        # Session có đủ thông tin, đi thẳng đến tính toán
        return "calculate_bmi"
    elif step == "user_identified":
        return "classify_topic"
    elif step == "topic_classified":
        # Sau khi phân loại chủ đề, nếu hợp lệ thì yêu cầu nhập liệu
        if state.get("topic_classification") == "không liên quan":
            return "end_rejected"
        # Chuyển đến node trả về cả 2 prompt
        return "end_need_emotion_and_cooking"
    elif step == "cooking_method_selected":
        # Step này chỉ được gọi khi FE gửi lên cả emotion và cooking method
        return "calculate_bmi"
    elif step == "bmi_calculated":
        return "query_neo4j"
    elif step == "neo4j_queried":
        return "aggregate_foods"
    elif step == "foods_aggregated":
        return "rerank_foods"
    elif step == "foods_reranked":
        return "generate_result"
    elif step == "result_generated":
        return "end_success"
    return "end_with_error"

# Node end_need_emotion_and_cooking

def end_need_emotion_and_cooking(state: WorkflowState) -> WorkflowState:
    """Kết thúc để FE lấy cả emotion_prompt và cooking_method_prompt cùng lúc."""
    # Sinh prompt cho cả emotion và cooking method
    emotion_prompt = select_emotion_node()
    cooking_method_prompt = select_cooking_method_node()
    session_id = save_state_to_redis({**state, "emotion_prompt": emotion_prompt, "cooking_method_prompt": cooking_method_prompt})
    return {
        **state,
        "emotion_prompt": emotion_prompt,
        "cooking_method_prompt": cooking_method_prompt,
        "session_id": session_id,
        "final_result": {
            "status": "need_emotion_and_cooking",
            "emotion_prompt": emotion_prompt,
            "cooking_method_prompt": cooking_method_prompt,
            "session_id": session_id
        }
    }

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
    
    message_parts = [f"Câu hỏi không thuộc chủ đề dinh dưỡng"]
    message_parts.append(f"Thông tin: {user_name}, {user_age} tuổi, {user_weight}kg, {user_height}cm")
    
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
            print(f"DEBUG: [end_success] State saved to Redis for session {session_id}")
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
    workflow.add_node("select_emotion", select_emotion_node_wrapper)
    workflow.add_node("select_cooking_method", select_cooking_method_node_wrapper)
    workflow.add_node("calculate_bmi", calculate_bmi)
    workflow.add_node("query_neo4j", query_neo4j)
    workflow.add_node("aggregate_foods", aggregate_foods)
    workflow.add_node("rerank_foods", rerank_foods_wrapper)
    workflow.add_node("generate_result", generate_final_result)
    workflow.add_node("end_with_error", end_with_error)
    workflow.add_node("end_rejected", end_rejected)
    workflow.add_node("end_success", end_success)
    workflow.add_node("end_need_emotion_and_cooking", end_need_emotion_and_cooking)
    # Thêm router
    workflow.add_conditional_edges(
        "check_session",
        should_continue,
        {
            "identify_user": "identify_user",
            "calculate_bmi": "calculate_bmi",
            "end_need_emotion_and_cooking": "end_need_emotion_and_cooking"
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
           
            "end_need_emotion_and_cooking": "end_need_emotion_and_cooking",
            "end_rejected": "end_rejected"
        }
    )
 
    
    workflow.add_conditional_edges(
        "calculate_bmi",
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
    workflow.add_edge("end_need_emotion_and_cooking", END)
    return workflow

# Tạo workflow instance
workflow_graph = create_workflow().compile()

def run_langgraph_workflow_until_selection(user_id: str, question: str, weather: str, time_of_day: str, session_id: str = None) -> dict:
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
            "aggregated_result": {},
            "reranked_foods": None,
            "fallback_attempt": 0,
            "final_result": {},
            "error": "",
            "step": "start",
            "emotion_prompt": None,
            "selected_emotion": None,
            "cooking_method_prompt": None,
            "selected_cooking_methods": None,
            "previous_food_ids": []
        }

        if session_id:
            try:
                loaded_state = load_state_from_redis(session_id)
                # Merge toàn bộ state cũ vào initial_state (ưu tiên giá trị đã lưu nếu trùng key)
                merged_state = {**initial_state, **loaded_state}
                initial_state = merged_state
                print("DEBUG: Loaded state from session", session_id, "previous_food_ids:", initial_state.get("previous_food_ids"))
            except Exception as e:
                print("DEBUG: Could not load state for session", session_id, "Error:", e)

        result = workflow_graph.invoke(initial_state)
        # Nếu workflow dừng lại để hỏi cả cảm xúc và phương pháp nấu
        if result.get("final_result", {}).get("status") == "need_emotion_and_cooking":
            return result["final_result"]
        # Các trường hợp kết thúc khác, trả về final_result
        return result.get("final_result", {
            "status": "error",
            "message": "Không có kết quả hoặc workflow kết thúc bất thường"
        })
    except Exception as e:
        print(f"Error in run_langgraph_workflow_until_selection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi chạy workflow: {str(e)}")

def continue_workflow_with_emotion(session_id: str, emotion: str) -> dict:
    state = load_state_from_redis(session_id)
    state["selected_emotion"] = emotion
  
    state["step"] = "emotion_selected"

    result = workflow_graph.invoke(state)
    
    # Kiểm tra xem workflow có dừng lại để hỏi phương pháp nấu không
    if result.get("step") == "cooking_method_prompt_generated" and result.get("cooking_method_prompt"):
        try:
            session_id = save_state_to_redis(result)
            return {
                "status": "need_cooking_method",
                "cooking_method_prompt": result["cooking_method_prompt"],
                "session_id": session_id
            }
        except Exception as e:
            print(f"Error saving session state: {str(e)}")
            raise HTTPException(status_code=500, detail="Lỗi lưu trạng thái workflow")
    
    # Nếu không dừng lại, trả về kết quả cuối cùng
    return result.get("final_result", {
        "status": "error",
        "message": "Không có kết quả"
    })

def continue_workflow_with_cooking_method(session_id: str, cooking_methods: List[str]) -> dict:
    state = load_state_from_redis(session_id)
    state["selected_cooking_methods"] = cooking_methods
    # Reset step để workflow tiếp tục từ select_cooking_method
    state["step"] = "cooking_method_selected"

    result = workflow_graph.invoke(state)
    
    # Sau khi chọn phương pháp nấu, workflow sẽ tiếp tục đến kết quả cuối cùng
    return result.get("final_result", {
        "status": "error",
        "message": "Không có kết quả"
    })

def continue_workflow_with_emotion_and_cooking(session_id: str, emotion: str, cooking_methods: List[str], user_id: str) -> dict:
    """Tải state, cập nhật emotion và cooking methods, và tiếp tục workflow."""
    try:
        # Tải state từ session
        state = load_state_from_redis(session_id)
        
        # Cập nhật thông tin từ input
        state["selected_emotion"] = emotion
        state["selected_cooking_methods"] = cooking_methods
        
        # Quan trọng: Cập nhật lại user_id từ token hiện tại để đảm bảo bảo mật
        # và lấy đúng dữ liệu user mới nhất nếu cần.
        state["user_id"] = user_id
        
        # Đặt step để workflow tiếp tục từ điểm tính toán
        state["step"] = "cooking_method_selected"
        
        # Gọi invoke để tiếp tục workflow
        result = workflow_graph.invoke(state)
        
        # Trả về kết quả cuối cùng
        return result.get("final_result", {
            "status": "error",
            "message": "Không có kết quả sau khi xử lý."
        })
    except Exception as e:
        print(f"Error in continue_workflow_with_emotion_and_cooking: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi tiếp tục workflow: {str(e)}")