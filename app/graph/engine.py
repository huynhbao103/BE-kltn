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
        # Gọi node rerank
        rerank_result = rerank_foods(state)
        
        # Debug: Kiểm tra kết quả từ rerank_foods
        print(f"DEBUG: rerank_result keys = {rerank_result.keys()}")
        
        # Lấy rerank_result từ kết quả
        reranked_result = rerank_result.get("rerank_result", {})
        
        # Debug: Kiểm tra reranked_result
        print(f"DEBUG: reranked_result status = {reranked_result.get('status')}")
        print(f"DEBUG: reranked_result total_count = {reranked_result.get('total_count', 0)}")
        
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

        # Tạo message chi tiết với các chỉ số
        message_parts = []
        
        # Lấy thông tin medical_conditions từ user_data
        medical_conditions = user_data.get("medicalConditions", [])
        
        # Trích xuất danh sách món ăn đã được rerank
        final_foods = []
        if rerank_result and rerank_result.get("status") == "success":
            ranked_foods = rerank_result.get("ranked_foods", [])
            rerank_criteria = rerank_result.get("rerank_criteria", {})
            total_count = rerank_result.get("total_count", 0)
            selected_cooking_methods = state.get("selected_cooking_methods", [])
 
            # Debug: Kiểm tra ranked_foods
            print(f"DEBUG: ranked_foods count = {len(ranked_foods)}")
            print(f"DEBUG: total_count = {total_count}")
            
            # Xử lý danh sách món ăn đã được rerank
            for food in ranked_foods:
                final_foods.append({
                    "name": food.get("dish_name", "Unknown"),
                    "id": food.get("dish_id", ""),
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
 
            # Hiển thị số lượng món ăn đã được rerank
            if final_foods:
                # Chỉ hiển thị 5 món đầu tiên trong message
                food_names = [food.get("name", "Unknown") for food in final_foods[:5]]
                if len(final_foods) > 5:
                    # food_names.append(f"... và {len(final_foods) - 5} món khác")
                    food_names = [food.get("name", "Unknown") for food in final_foods]
                message_parts.append(f"Danh sách món ăn phù hợp: {', '.join(food_names)}")
                
                # # Thêm thông tin về tiêu chí đã sử dụng
                # if rerank_criteria:
                #     criteria_info = []
                #     if rerank_criteria.get("bmi_category"):
                #         criteria_info.append(f"BMI: {rerank_criteria['bmi_category']}")
                #     if rerank_criteria.get("cooking_methods"):
                #         criteria_info.append(f"Cách chế biến: {', '.join(rerank_criteria['cooking_methods'])}")
                #     if rerank_criteria.get("medical_conditions"):
                #         criteria_info.append(f"Bệnh: {', '.join(rerank_criteria['medical_conditions'])}")
                #     if rerank_criteria.get("emotion"):
                #         criteria_info.append(f"Cảm xúc: {rerank_criteria['emotion']}")
                    
                #     if criteria_info:
                #         message_parts.append(f"Tiêu chí: {' | '.join(criteria_info)}")
                
                # # Thêm thông tin tổng số món
                message_parts.append(f"Tổng cộng: {total_count} món ăn")
            else:
                message_parts.append("Không có món ăn phù hợp với các tiêu chí của bạn")

        # Tạo message hoàn chỉnh
        detailed_message = " | ".join(message_parts)
        
        # Debug: Kiểm tra final_foods
        print(f"DEBUG: final_foods length = {len(final_foods)}")
        if not final_foods:
            print("DEBUG: final_foods is empty!")
            print(f"DEBUG: rerank_result status = {rerank_result.get('status') if rerank_result else 'None'}")
            
            if rerank_result and rerank_result.get("status") == "success":
                print(f"DEBUG: ranked_foods count = {len(rerank_result.get('ranked_foods', []))}")
                print(f"DEBUG: rerank_criteria = {rerank_result.get('rerank_criteria', {})}")
                print(f"DEBUG: total_count = {rerank_result.get('total_count', 0)}")
        
        # Kết quả cuối cùng chỉ chứa thông tin cần thiết
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
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            **state,
            "final_result": final_result,
            "step": "result_generated"
        }
    except Exception as e:
        return {
            **state,
            "error": f"Lỗi tạo kết quả: {str(e)}",
            "step": "result_generation_error"
        }

def should_continue(state: WorkflowState) -> str:
    if state.get("error"):
        return "end_with_error"
    step = state.get("step", "")
    if step == "user_identified":
        return "classify_topic"
    elif step == "topic_classified":
        if state.get("topic_classification") == "no":
            return "end_rejected"
        return "select_emotion"
    elif step == "emotion_prompt_generated":
        # Dừng lại để chờ user chọn cảm xúc
        return "end_success"
    elif step == "emotion_selected":
        return "select_cooking_method"
    elif step == "cooking_method_prompt_generated":
        # Dừng lại để chờ user chọn phương pháp nấu
        return "end_success"
    elif step == "cooking_method_selected":
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

def end_with_error(state: WorkflowState) -> WorkflowState:
    """Kết thúc với lỗi"""
    return {
        **state,
        "final_result": {
            "status": "error",
            "message": state.get("error", "Lỗi không xác định"),
            "timestamp": datetime.now().isoformat()
        }
    }

def end_rejected(state: WorkflowState) -> WorkflowState:
    """Kết thúc khi câu hỏi không thuộc chủ đề"""
    user_data = state.get("user_data", {})
    question = state.get("question", "")
    
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
            "timestamp": datetime.now().isoformat()
        }
    }

def end_success(state: WorkflowState) -> WorkflowState:
    """
    Kết thúc thành công. Node này không làm gì cả, 
    chỉ trả về state hiện tại để giữ nguyên final_result đã được tạo ở node trước.
    """
    return state

# Tạo LangGraph workflow
def create_workflow() -> StateGraph:
    """Tạo LangGraph workflow"""
    # Tạo graph
    workflow = StateGraph(WorkflowState)
    # Thêm nodes
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
    # Thêm router
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
            "select_emotion": "select_emotion",
            "end_rejected": "end_rejected",
            "end_with_error": "end_with_error"
        }
    )
    workflow.add_conditional_edges(
        "select_emotion",
        should_continue,
        {
            "select_cooking_method": "select_cooking_method",
            "end_success": "end_success",
            "end_with_error": "end_with_error"
        }
    )
    workflow.add_conditional_edges(
        "select_cooking_method",
        should_continue,
        {
            "calculate_bmi": "calculate_bmi",
            "end_success": "end_success",
            "end_with_error": "end_with_error"
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
    workflow.set_entry_point("identify_user")
    # Add end nodes
    workflow.add_edge("end_with_error", END)
    workflow.add_edge("end_rejected", END)
    workflow.add_edge("end_success", END)
    return workflow

# Tạo workflow instance
workflow_graph = create_workflow().compile()

def run_langgraph_workflow_until_selection(user_id: str, question: str) -> dict:
    try:
        initial_state = {
            "user_id": user_id,
            "question": question,
            "user_data": {},
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
            "selected_cooking_methods": None
        }
        result = workflow_graph.invoke(initial_state)

        # Nếu workflow dừng lại để hỏi cảm xúc
        if result.get("step") == "emotion_prompt_generated" and result.get("emotion_prompt"):
            try:
                session_id = save_state_to_redis(result)
                return {
                    "status": "need_emotion",
                    "emotion_prompt": result["emotion_prompt"],
                    "session_id": session_id
                }
            except Exception as e:
                print(f"Error saving session state: {str(e)}")
                raise HTTPException(status_code=500, detail="Lỗi lưu trạng thái workflow")

        # Nếu workflow dừng lại để hỏi phương pháp nấu
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
    # Reset step để workflow tiếp tục từ select_emotion
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