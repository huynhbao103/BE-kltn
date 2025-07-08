from langgraph.graph import StateGraph, END
from typing import Dict, Any, TypedDict, Annotated, Optional, List
from app.graph.nodes.classify_topic_node import check_mode
from app.graph.nodes.calculate_bmi_node import calculate_bmi_from_user_id
from app.graph.nodes.query_neo4j_node import query_neo4j_for_foods
# from app.graph.nodes.llm_check_food_suitability_node import check_food_suitability
from app.graph.nodes.food_rerank_node import rerank_foods_by_suitability
# from app.graph.nodes.fallback_query_node import create_fallback_query
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
                # Sử dụng fallback query
                from app.services.neo4j_service import neo4j_service
                query = fallback_result["query"]
                params = fallback_result["params"]
                
                result = neo4j_service.run_query(query, params)
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
            # Truy vấn Neo4j bình thường với thông tin cảm xúc và phương pháp nấu
            selected_emotion = state.get("selected_emotion")
            selected_cooking_methods = state.get("selected_cooking_methods")
            neo4j_result = query_neo4j_for_foods(user_data, selected_emotion, selected_cooking_methods)
        
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

        # def check_food_suitability_llm(state: WorkflowState) -> WorkflowState:
        #     """ Node 6: Kiểm tra tính phù hợp của thực phẩm bằng LLM """
        #     try:
        #         neo4j_result = state.get("neo4j_result", {})
        #         user_data = state.get("user_data", {})
        #         selected_emotion = state.get("selected_emotion", "")
        #         bmi_result = state.get("bmi_result", {})
        #         fallback_attempt = state.get("fallback_attempt", 0)
                
        #         if not neo4j_result or neo4j_result.get("status") != "success":
        #             return {
        #                 **state,
        #                 "error": "Không có kết quả Neo4j để kiểm tra",
        #                 "step": "llm_check_failed"
        #             }
                
        #         # Tạo context cho LLM
        #         user_context = {
        #             "emotion": selected_emotion,
        #             "bmi_category": bmi_result.get("bmi_category", ""),
        #             "medical_conditions": user_data.get("medicalConditions", [])
        #         }
                
        #         # Kiểm tra tính phù hợp
        #         llm_result = check_food_suitability(neo4j_result, user_context)
        #         llm_response = llm_result.get("response", "").lower().strip()
                
        #         # Nếu LLM trả về "no" và chưa vượt quá 3 lần fallback thì tăng biến
        #         if "yes" in llm_response:
        #             return {
        #                 **state,
        #                 "llm_check_result": llm_result,
        #                 "step": "llm_checked"
        #             }
        #         else:
        #             if fallback_attempt < 3:
        #                 return {
        #                     **state,
        #                     "llm_check_result": llm_result,
        #                     "fallback_attempt": fallback_attempt + 1,
        #                     "step": "llm_checked"
        #                 }
        #             else:
        #                 return {
        #                     **state,
        #                     "llm_check_result": llm_result,
        #                     "step": "llm_checked"
        #                 }
                
        #     except Exception as e:
        #         return {
        #             **state,
        #             "error": f"Lỗi kiểm tra LLM: {str(e)}",
        #             "step": "llm_check_error"
        #         }

def rerank_foods(state: WorkflowState) -> WorkflowState:
    try:
        neo4j_result = state.get("neo4j_result", {})
        user_data = state.get("user_data", {})
        selected_emotion = state.get("selected_emotion", "")
        bmi_result = state.get("bmi_result", {})
        
        print(f"DEBUG RERANK: emotion={selected_emotion}, bmi={bmi_result.get('bmi_category')}, conditions={user_data.get('medicalConditions')}")
        
        if not neo4j_result or neo4j_result.get("status") != "success":
            print("DEBUG RERANK: No neo4j result")
            return {
                **state,
                "error": "Không có kết quả Neo4j để sắp xếp lại",
                "step": "rerank_failed"
            }
        
        user_context = {
            "emotion": selected_emotion,
            "bmi_category": bmi_result.get("bmi_category", ""),
            "medical_conditions": user_data.get("medicalConditions", [])
        }
        
        print(f"DEBUG RERANK: user_context={user_context}")
        
        reranked_result = rerank_foods_by_suitability(neo4j_result, user_context)
        
        print(f"DEBUG RERANK: reranked_result status={reranked_result.get('status')}")
        
        # Chỉ lấy tối đa 3 món cho mỗi tình trạng bệnh
        foods = reranked_result.get("foods", {})
        print(f"DEBUG RERANK: foods keys={list(foods.keys())}")
        
        for condition, food_data in foods.items():
            if isinstance(food_data, dict) and "advanced" in food_data:
                advanced = food_data["advanced"][:300]
                reranked_result["foods"][condition]["advanced"] = advanced
                print(f"DEBUG RERANK: {condition} has {len(advanced)} foods")
        
        return {
            **state,
            "reranked_foods": reranked_result,
            "step": "foods_reranked"
        }
    except Exception as e:
        print(f"DEBUG RERANK ERROR: {str(e)}")
        return {
            **state,
            "error": f"Lỗi sắp xếp lại thực phẩm: {str(e)}",
            "step": "rerank_error"
        }

def generate_final_result(state: WorkflowState) -> WorkflowState:
    """ Node 8: Tạo kết quả cuối cùng """
    try:
        user_data = state.get("user_data", {})
        question = state.get("question", "")
        topic_classification = state.get("topic_classification", "")
        bmi_result = state.get("bmi_result", {})
        neo4j_result = state.get("neo4j_result", {})
        # llm_check_result = state.get("llm_check_result", {})
        reranked_foods = state.get("reranked_foods", {})
        # fallback_attempt = state.get("fallback_attempt", 0)
        selected_emotion = state.get("selected_emotion")

        # Tạo message chi tiết với các chỉ số
        message_parts = []
        
        # # Thêm cảm xúc vào message nếu có
        # if selected_emotion:
        #     message_parts.append(f"Cảm xúc: {selected_emotion}")

        # if bmi_result:
        #     bmi = bmi_result.get("bmi", "N/A")
        #     bmi_category = bmi_result.get("bmi_category", "N/A")
            
        #     message_parts.append(f"BMI: {bmi} ({bmi_category})")
        
        # # Thêm thông tin user
        # user_name = user_data.get("name", "Unknown")
        # user_age = user_data.get("age", "N/A")
        # user_weight = user_data.get("weight", "N/A")
        # user_height = user_data.get("height", "N/A")
        # medical_conditions = user_data.get("medicalConditions", [])
        
        # message_parts.append(f"Thông tin: {user_name}, {user_age} tuổi, {user_weight}kg, {user_height}cm")
        
        # # Thêm thông tin bệnh nếu có
        # if medical_conditions and medical_conditions != ["Không có"]:
        #     conditions_str = ", ".join(medical_conditions)
        #     message_parts.append(f"Tình trạng bệnh: {conditions_str}")
        
        # Trích xuất danh sách món ăn cuối cùng đã được lọc tổng hợp
        final_foods = []
        if neo4j_result and neo4j_result.get("status") == "success":
            foods = neo4j_result.get("foods", {})
            statistics = neo4j_result.get("statistics", {})
            # message_parts.append("(Đã lọc theo tất cả tiêu chí)")

            # Lọc món ăn phù hợp với tất cả tiêu chí: bệnh lý + phương pháp nấu (nếu có)
            medical_conditions = user_data.get("medicalConditions", [])
            selected_cooking_methods = state.get("selected_cooking_methods", [])

            for condition, food_data in foods.items():
                is_medical_condition = any(med_condition in condition for med_condition in medical_conditions)
                if is_medical_condition:
                    if isinstance(food_data, dict) and "advanced" in food_data:
                        advanced_foods = food_data.get("advanced", [])
                        for food in advanced_foods:
                            # Nếu có chọn phương pháp nấu, chỉ lấy món đúng phương pháp
                            if selected_cooking_methods:
                                if food.get("cook_method", "").lower() not in [m.lower() for m in selected_cooking_methods]:
                                    continue
                            final_foods.append({
                                "name": food.get("dish_name", "Unknown"),
                                "id": food.get("dish_id", ""),
                                "description": food.get("description", ""),
                                "category": condition,
                                "cook_method": food.get("cook_method", ""),
                                "diet": food.get("diet_name", "")
                            })
                    else:
                        # Dữ liệu cũ
                        for food in food_data:
                            if selected_cooking_methods:
                                if food.get("cook_method", "").lower() not in [m.lower() for m in selected_cooking_methods]:
                                    continue
                            final_foods.append({
                                "name": food.get("dish_name", food.get("name", "Unknown")),
                                "id": food.get("dish_id", food.get("id", "")),
                                "description": food.get("description", ""),
                                "category": condition,
                                "cook_method": food.get("cook_method", ""),
                                "diet": food.get("diet_name", "")
                            })

            # Hiển thị số lượng món ăn đã được lọc tổng hợp
            if final_foods:
                # message_parts.append(f"Đã tìm thấy {len(final_foods)} món ăn phù hợp nhất")
                food_names = [food.get("name", "Unknown") for food in final_foods]
                message_parts.append(f"Danh sách món ăn: {', '.join(food_names)}")
            else:
                message_parts.append("Không có món ăn phù hợp với các tiêu chí của bạn")
                if statistics:
                    total_foods = statistics.get("total_foods", 0)
                    total_diets = statistics.get("total_diets", 0)
                    total_cook_methods = statistics.get("total_cook_methods", 0)
                    if total_foods > 0:
                        message_parts.append(f"Tổng: {total_foods} món, {total_diets} chế độ ăn, {total_cook_methods} phương pháp nấu")

            # # Thêm thông tin chế độ ăn và phương pháp nấu
            # diet_recommendations = neo4j_result.get("diet_recommendations", {})
            # cook_methods = neo4j_result.get("cook_methods", {})
            
            # if diet_recommendations:
            #     all_diets = set()
            #     for diets in diet_recommendations.values():
            #         all_diets.update(diets)
            #     if all_diets:
            #         message_parts.append(f"Chế độ ăn: {', '.join(list(all_diets)[:300])}")
            
            # if cook_methods:
            #     all_methods = set()
            #     for methods in cook_methods.values():
            #         all_methods.update(methods)
            #     if all_methods:
            #         message_parts.append(f"Phương pháp nấu: {', '.join(list(all_methods)[:300])}")
        
        # Kiểm tra nếu đã thử hết fallback mà vẫn không có kết quả
        # if fallback_attempt >= 3 and (not foods or not any(foods.values())):
        #     detailed_message = "Nhóm đang phát triển và chưa có món ăn phù hợp cho trường hợp của bạn. Vui lòng thử lại sau."
        #     final_result = {
        #         "status": "no_suitable_food",
        #         "message": detailed_message,
        #         "fallback_attempts": fallback_attempt,
        #         "timestamp": datetime.now().isoformat(),
        #         "step": "no_suitable_food_found"
        #     }
        # else:
        #     ...

        # Tạo message hoàn chỉnh
        detailed_message = " | ".join(message_parts)
        
        # Debug: Kiểm tra final_foods
        print(f"DEBUG: final_foods length = {len(final_foods)}")
        if not final_foods:
            print("DEBUG: final_foods is empty!")
            print(f"DEBUG: neo4j_result status = {neo4j_result.get('status') if neo4j_result else 'None'}")
            print(f"DEBUG: reranked_foods status = {reranked_foods.get('status') if reranked_foods else 'None'}")
            
            # Debug chi tiết hơn
            if neo4j_result and neo4j_result.get("status") == "success":
                foods = neo4j_result.get("foods", {})
                print(f"DEBUG: neo4j foods keys = {list(foods.keys())}")
                
                medical_conditions = user_data.get("medicalConditions", [])
                print(f"DEBUG: medical_conditions = {medical_conditions}")
                
                for condition, food_data in foods.items():
                    is_medical_condition = any(med_condition in condition for med_condition in medical_conditions)
                    print(f"DEBUG: condition '{condition}' is_medical = {is_medical_condition}")
                    
                    if isinstance(food_data, dict) and "advanced" in food_data:
                        advanced_count = len(food_data.get("advanced", []))
                        print(f"DEBUG: {condition} has {advanced_count} advanced foods")
                    else:
                        basic_count = len(food_data) if isinstance(food_data, list) else 0
                        print(f"DEBUG: {condition} has {basic_count} basic foods")
        
        # Kết quả cuối cùng chỉ chứa thông tin cần thiết
        final_result = {
            "status": "success",
            "message": detailed_message,
            "foods": final_foods,
            "user_info": {
                "name": user_data.get("name", "Unknown"),
                "age": user_data.get("age", "N/A"),
                "bmi": bmi_result.get("bmi", "N/A") if bmi_result else "N/A",
                "bmi_category": bmi_result.get("bmi_category", "N/A") if bmi_result else "N/A",
                "medical_conditions": medical_conditions if medical_conditions and medical_conditions != ["Không có"] else []
            },
            "selected_emotion": selected_emotion,
            "selected_cooking_methods": state.get("selected_cooking_methods", []),
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
    workflow.add_node("rerank_foods", rerank_foods)
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

# Legacy function để tương thích - Cập nhật thành luồng hoàn chỉnh
# def run_graph_flow(input_text: str, user_id: str = None) -> dict:
#     """
#     Luồng hoàn chỉnh: Phân loại topic + Tính BMI + Tạo kết quả
#     """
#     try:
#         # Nếu không có user_id, chỉ phân loại topic
#         if not user_id:
#             classification = check_mode(input_text)
            
#             if classification == "no":
#                 return {
#                     "status": "rejected",
#                     "message": "Câu hỏi không thuộc chủ đề dinh dưỡng."
#                 }
            
#             return {
#                 "status": "accepted",
#                 "message": "Câu hỏi thuộc chủ đề dinh dưỡng. Vui lòng cung cấp user_id để tính BMI.",
#                 "topic_classification": classification
#             }
        
#         # Nếu có user_id, chạy luồng hoàn chỉnh
#         try:
#             return run_langgraph_workflow_until_emotion(user_id, input_text)
#         except HTTPException as e:
#             return {"status": "error", "message": e.detail}
#         except Exception as e:
#             return {"status": "error", "message": str(e)}
        
#     except Exception as e:
#         return {
#             "status": "error",
#             "message": f"Lỗi xử lý: {str(e)}"
#         }
