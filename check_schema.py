from app.services.graph_schema_service import GraphSchemaService

if __name__ == "__main__":
    labels = GraphSchemaService.get_all_node_labels()
    print("Node labels:", labels)

    relationships = GraphSchemaService.get_all_relationship_types()
    print("Relationship types:", relationships)