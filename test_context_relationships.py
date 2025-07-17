import pytest
from app.services.graph_schema_service import GraphSchemaService



@pytest.mark.parametrize("label1, label2, rel_type", [
    ("Context", "Context", None),
    ("Context", "Dish", None),
    ("Context", "TimeOfDay", None),
    ("Context", "Weather", None),
])
def test_relationships_between_labels(label1, label2, rel_type):
    # Xây dựng query động
    if rel_type:
        query = f"""
        MATCH (a:{label1})-[r:{rel_type}]->(b:{label2})
        RETURN a, r, b LIMIT 5
        """
    else:
        query = f"""
        MATCH (a:{label1})-[r]->(b:{label2})
        RETURN a, type(r) as rel_type, b LIMIT 5
        """
    results = GraphSchemaService.run_custom_query(query)
    print(f"\n---\n{label1} -> {label2} relationships:")
    for record in results:
        print(record)
    # Không assert để chỉ kiểm tra và in ra kết quả


def test_relationship_mo_ta():
    query = """
    MATCH p=()-[:`MÔ_TẢ`]->() RETURN p LIMIT 25
    """
    results = GraphSchemaService.run_custom_query(query)
    print("\n---\nRelationship MÔ_TẢ:")
    for record in results:
        print(record)


def test_relationship_thoi_diem():
    query = """
    MATCH p=()-[:`THỜI_ĐIỂM`]->() RETURN p LIMIT 25
    """
    results = GraphSchemaService.run_custom_query(query)
    print("\n---\nRelationship THỜI_ĐIỂM:")
    for record in results:
        print(record)


def test_relationship_weather_timeofday():
    print("\n---\nWeather -> TimeOfDay relationships:")
    query1 = """
    MATCH (w:Weather)-[r]->(t:TimeOfDay) RETURN w, type(r) as rel_type, t 
    """
    results1 = GraphSchemaService.run_custom_query(query1)
    for record in results1:
        print(record)
    print("\n---\nTimeOfDay -> Weather relationships:")
    query2 = """
    MATCH (t:TimeOfDay)-[r]->(w:Weather) RETURN t, type(r) as rel_type, w 
    """
    results2 = GraphSchemaService.run_custom_query(query2)
    for record in results2:
        print(record)


def test_weather_timeofday_to_context():
    print("\n---\nWeather + TimeOfDay -> Context:")
    query = """
    MATCH (w:Weather)-[r1]->(ctx:Context)<-[r2]-(t:TimeOfDay)
    RETURN w, type(r1) as rel1, ctx, type(r2) as rel2, t
    """
    results = GraphSchemaService.run_custom_query(query)
    for record in results:
        print(record)


def test_cook_methods_by_weather_timeofday():
    print("\n---\nCookMethods by Weather + TimeOfDay:")
    test_cases = [
        ("Trời nắng", "sáng "),
        ("Trời nắng", "trưa"),
        ("Trời nắng", "chiều"),
        ("Trời nắng", "tối"),
        ("Trời Mưa", "sáng "),
        ("Trời Mưa", "trưa"),
        ("Trời Mưa", "chiều"),
        ("Trời Mưa", "tối"),
    ]
    for weather, time_of_day in test_cases:
        print(f"\nWeather: {weather}, TimeOfDay: {time_of_day}")
        results = GraphSchemaService.get_cook_methods_by_weather_timeofday(weather, time_of_day)
        if not results:
            print("  Không có cách chế biến phù hợp.")
        else:
            for record in results:
                name = record.get("cook_method", "")
                cmid = record.get("cook_method_id", "")
                print(f"  - Cách chế biến: {name} (ID: {cmid})")


def test_context_and_cook_methods_by_weather_timeofday():
    print("\n---\nContext và CookMethod theo Weather + TimeOfDay:")
    test_cases = [
        ("Lạnh", "sáng "),
        ("Bình thường", "sáng "),
        ("Nóng ", "sáng "),
        ("Lạnh", "trưa"),
        ("Bình thường", "trưa"),
        ("Nóng ", "trưa"),
        ("Lạnh", "chiều"),
        ("Bình thường", "chiều"),
        ("Nóng ", "chiều"),
        ("Lạnh", "tối"),
        ("Bình thường", "tối"),
        ("Nóng ", "tối"),
    ]
    for weather, time_of_day in test_cases:
        print(f"\nWeather: {weather}, TimeOfDay: {time_of_day}")
        # Tìm các Context phù hợp
        query_ctx = '''
        MATCH (w:Weather {name: $weather})-[:MÔ_TẢ]->(ctx:Context)<-[:THỜI_ĐIỂM]-(t:TimeOfDay {name: $time_of_day})
        RETURN ctx.name AS context_name, ctx.id AS context_id, ctx.desciption AS context_desc
        '''
        ctxs = GraphSchemaService.run_custom_query(query_ctx, {"weather": weather, "time_of_day": time_of_day})
        if not ctxs:
            print("  Không có Context phù hợp.")
            continue
        for ctx in ctxs:
            ctx_name = ctx.get("context_name", "")
            ctx_id = ctx.get("context_id", "")
            ctx_desc = ctx.get("context_desc", "")
            print(f"  Context: {ctx_name} (ID: {ctx_id}) - Mô tả: {ctx_desc}")
            # Tìm các CookMethod của Context này
            query_cm = '''
            MATCH (ctx:Context {id: $ctx_id})-[:PHÙ_HỢP_CHẾ_BIẾNG_BẰNG]->(cm:CookMethod)
            RETURN cm.name AS cook_method, cm.id AS cook_method_id
            '''
            cms = GraphSchemaService.run_custom_query(query_cm, {"ctx_id": ctx_id})
            if not cms:
                print("    Không có cách chế biến phù hợp.")
            else:
                for cm in cms:
                    name = cm.get("cook_method", "")
                    cmid = cm.get("cook_method_id", "")
                    print(f"    - Cách chế biến: {name} (ID: {cmid})")

if __name__ == "__main__":
    # Chạy test cũ
    for label1, label2 in [
        ("Context", "Context"),
        ("Context", "Dish"),
        ("Context", "TimeOfDay"),
        ("Context", "Weather"),
    ]:
        test_relationships_between_labels(label1, label2, None)
    # Chạy test relationship đặc biệt
    test_relationship_mo_ta()
    test_relationship_thoi_diem()
    test_relationship_weather_timeofday()
    test_weather_timeofday_to_context()
    test_cook_methods_by_weather_timeofday()
    test_context_and_cook_methods_by_weather_timeofday() 