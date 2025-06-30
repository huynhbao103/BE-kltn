from langgraph.graph import StateGraph, END
from typing import Dict, Any, TypedDict, Annotated
from app.graph.nodes.classify_topic_node import check_mode
from app.graph.nodes.calculate_bmi_node import calculate_bmi_from_user_id
from app.services.mongo_service import mongo_service
import jwt
import os
from datetime import datetime

# Định nghĩa state cho LangGraph
class WorkflowState(TypedDict):
    user_id: str
    question: str
    user_data: Dict[str, Any]
    topic_classification: str
    bmi_result: Dict[str, Any]
    final_result: Dict[str, Any]
    error: str
    step: str

def identify_user(state: WorkflowState) -> WorkflowState:
    """
    Node 1: Xác định user từ user_id (chỉ từ token, không từ email)
    """
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
    """
    Node 2: Phân loại chủ đề câu hỏi
    """
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

def calculate_bmi(state: WorkflowState) -> WorkflowState:
    """
    Node 3: Tính BMI cho user
    """
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

def generate_final_result(state: WorkflowState) -> WorkflowState:
    """
    Node 4: Tạo kết quả cuối cùng
    """
    try:
        user_data = state.get("user_data", {})
        question = state.get("question", "")
        topic_classification = state.get("topic_classification", "")
        bmi_result = state.get("bmi_result", {})
        
        # Tạo message chi tiết với các chỉ số
        message_parts = []
        
        if bmi_result:
            bmi = bmi_result.get("bmi", "N/A")
            bmi_category = bmi_result.get("bmi_category", "N/A")
            
            message_parts.append(f"BMI: {bmi} ({bmi_category})")
        
        # Thêm thông tin user
        user_name = user_data.get("name", "Unknown")
        user_age = user_data.get("age", "N/A")
        user_weight = user_data.get("weight", "N/A")
        user_height = user_data.get("height", "N/A")
        medical_conditions = user_data.get("medicalConditions", [])
        
        message_parts.append(f"Thông tin: {user_name}, {user_age} tuổi, {user_weight}kg, {user_height}cm")
        
        # Thêm thông tin bệnh nếu có
        if medical_conditions and medical_conditions != ["Không có"]:
            conditions_str = ", ".join(medical_conditions)
            message_parts.append(f"Tình trạng bệnh: {conditions_str}")
        
        # Tạo message hoàn chỉnh
        detailed_message = " | ".join(message_parts)
        
        final_result = {
            "status": "success",
            "message": detailed_message,
            "user_info": {
                "name": user_name,
                "user_id": state.get("user_id"),
                "authenticated": True,
                "age": user_age,
                "weight": user_weight,
                "height": user_height,
                "medical_conditions": medical_conditions
            },
            "question": question,
            "topic_classification": topic_classification,
            "bmi_data": bmi_result,
            "timestamp": datetime.now().isoformat(),
            "step": "complete"
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
    """
    Router: Quyết định bước tiếp theo dựa trên state
    """
    # Nếu có lỗi, dừng
    if state.get("error"):
        return "end_with_error"
    
    step = state.get("step", "")
    
    if step == "user_identified":
        return "classify_topic"
    elif step == "topic_classified":
        # Nếu không thuộc chủ đề dinh dưỡng, dừng
        if state.get("topic_classification") == "no":
            return "end_rejected"
        return "calculate_bmi"
    elif step == "bmi_calculated":
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
            "step": state.get("step", "unknown_error")
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
                "authenticated": True,
                "age": user_age,
                "weight": user_weight,
                "height": user_height,
                "medical_conditions": medical_conditions
            },
            "question": question,
            "step": "topic_rejected"
        }
    }

def end_success(state: WorkflowState) -> WorkflowState:
    """Kết thúc thành công"""
    return state

# Tạo LangGraph workflow
def create_workflow() -> StateGraph:
    """Tạo LangGraph workflow"""
    
    # Tạo graph
    workflow = StateGraph(WorkflowState)
    
    # Thêm nodes
    workflow.add_node("identify_user", identify_user)
    workflow.add_node("classify_topic", classify_topic)
    workflow.add_node("calculate_bmi", calculate_bmi)
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
            "calculate_bmi": "calculate_bmi",
            "end_rejected": "end_rejected",
            "end_with_error": "end_with_error"
        }
    )
    
    workflow.add_conditional_edges(
        "calculate_bmi",
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

def run_langgraph_workflow(user_id: str, question: str) -> Dict[str, Any]:
    """
    Chạy LangGraph workflow với user_id và question
    """
    try:
        # Khởi tạo state
        initial_state = {
            "user_id": user_id,
            "question": question,
            "user_data": {},
            "topic_classification": "",
            "bmi_result": {},
            "final_result": {},
            "error": "",
            "step": "start"
        }
        
        # Chạy workflow
        result = workflow_graph.invoke(initial_state)
        
        # Trả về kết quả cuối cùng
        return result.get("final_result", {
            "status": "error",
            "message": "Không có kết quả"
        })
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Lỗi chạy workflow: {str(e)}"
        }

# Legacy function để tương thích - Cập nhật thành luồng hoàn chỉnh
def run_graph_flow(input_text: str, user_id: str = None) -> dict:
    """
    Luồng hoàn chỉnh: Phân loại topic + Tính BMI + Tạo kết quả
    """
    try:
        # Nếu không có user_id, chỉ phân loại topic
        if not user_id:
            classification = check_mode(input_text)
            
            if classification == "no":
                return {
                    "status": "rejected",
                    "message": "Câu hỏi không thuộc chủ đề dinh dưỡng."
                }
            
            return {
                "status": "accepted",
                "message": "Câu hỏi thuộc chủ đề dinh dưỡng. Vui lòng cung cấp user_id để tính BMI.",
                "topic_classification": classification
            }
        
        # Nếu có user_id, chạy luồng hoàn chỉnh
        return run_langgraph_workflow(user_id, input_text)
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Lỗi xử lý: {str(e)}"
        }
