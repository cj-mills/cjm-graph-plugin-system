import sys
import os
import json
import uuid
from pathlib import Path

# Add path to find local libs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cjm_graph_plugin_system.core import (
    GraphNode, GraphEdge, GraphContext, SourceRef, GraphQuery
)
from cjm_graph_plugin_system.plugin_interface import GraphPlugin

from cjm_graph_plugin_system.utils.mermaid import context_to_mermaid

def title(msg):
    print(f"\n{'='*60}\n{msg}\n{'='*60}")

def verify_dto_serialization():
    title("TEST 1: DTO Serialization & Zero-Copy Transfer")

    # 1. Create Data Objects
    print("Creating Graph Objects...")
    
    # A source reference (The "Link" to the transcription)
    source_ref = SourceRef(
        plugin_name="cjm-transcription-plugin-voxtral-hf",
        table_name="transcriptions",
        row_id=str(uuid.uuid4()),
        segment_slice="timestamp:00:10-00:20"
    )

    # Node 1: An Entity with a source
    node_a = GraphNode(
        id=str(uuid.uuid4()),
        label="Person",
        properties={"name": "Sun Tzu", "era": "Ancient China"},
        sources=[source_ref]
    )

    # Node 2: A Concept (No source)
    node_b = GraphNode(
        id=str(uuid.uuid4()),
        label="Concept",
        properties={"name": "The Art of War", "importance": "Vital"}
    )

    # Edge: Node A -> Node B
    edge = GraphEdge(
        id=str(uuid.uuid4()),
        source_id=node_a.id,
        target_id=node_b.id,
        relation_type="AUTHORED",
        properties={"confidence": 1.0}
    )

    # Create Context Container
    original_ctx = GraphContext(
        nodes=[node_a, node_b],
        edges=[edge],
        metadata={"created_by": "test_script"}
    )

    # 2. Test File Serialization (The "Zero-Copy" mechanism)
    print("\n[Action] Saving GraphContext to temp file...")
    temp_path = original_ctx.to_temp_file()
    print(f"  -> Saved to: {temp_path}")

    # Verify file exists and looks like JSON
    with open(temp_path, 'r') as f:
        raw_json = json.load(f)
        print(f"  -> File content check: Found {len(raw_json['nodes'])} nodes, {len(raw_json['edges'])} edges.")

    # 3. Test Deserialization
    print("\n[Action] Loading GraphContext from file...")
    loaded_ctx = GraphContext.from_file(temp_path)

    # 4. Assertions
    print("\n[Verification] Comparing Original vs Loaded...")
    
    # Check Node count
    assert len(loaded_ctx.nodes) == len(original_ctx.nodes)
    
    # Check Node A integrity (Properties + SourceRef)
    loaded_node_a = next(n for n in loaded_ctx.nodes if n.id == node_a.id)
    assert loaded_node_a.label == "Person"
    assert loaded_node_a.properties["name"] == "Sun Tzu"
    assert len(loaded_node_a.sources) == 1
    
    # Check SourceRef integrity
    loaded_ref = loaded_node_a.sources[0]
    assert loaded_ref.plugin_name == "cjm-transcription-plugin-voxtral-hf"
    assert loaded_ref.segment_slice == "timestamp:00:10-00:20"
    
    # Check Edge integrity
    loaded_edge = loaded_ctx.edges[0]
    assert loaded_edge.source_id == node_a.id
    assert loaded_edge.target_id == node_b.id
    
    print("  -> PASSED: Data survived the round-trip perfectly.")

    # Check Edge integrity
    loaded_edge = loaded_ctx.edges[0]
    assert loaded_edge.source_id == node_a.id
    assert loaded_edge.target_id == node_b.id
    
    print("  -> PASSED: Data survived the round-trip perfectly.")

    # [NEW] Test Mermaid Generation
    print("\n[Visual Check] Generating Mermaid Diagram...")
    diagram = context_to_mermaid(
        loaded_ctx, 
        direction="LR",
        node_color_map={"Person": "#ffaaaa", "Concept": "#aaaaff"}
    )
    print("\n--- Mermaid Code Start ---")
    print(diagram)
    print("--- Mermaid Code End ---\n")
    assert "graph LR" in diagram
    assert "Sun Tzu" in diagram
    assert "-->|AUTHORED|" in diagram
    print("  -> PASSED: Mermaid generation valid.")
    
    # Cleanup
    os.remove(temp_path)


def verify_plugin_interface():
    title("TEST 2: Plugin Interface Implementation Contract")
    
    # Define a Mock class to ensure we implemented all abstract methods
    # If we missed one in the Interface definition or here, Python will error on instantiation.
    
    class MockGraphPlugin(GraphPlugin):
        @property
        def name(self): return "mock-graph"
        @property
        def version(self): return "0.0.1"
        def initialize(self, config): pass
        def cleanup(self): pass
        def get_config_schema(self): return {}
        def get_current_config(self): return {}
        
        # --- Graph Specific Implementation ---
        def add_nodes(self, nodes): return [n.id for n in nodes]
        def add_edges(self, edges): return [e.id for e in edges]
        
        def get_node(self, node_id): return None
        def get_edge(self, edge_id): return None
        def get_context(self, node_id, depth=1, filter_labels=None): return GraphContext([], [])
        
        def find_nodes_by_source(self, source_ref): return []
        def find_nodes_by_label(self, label, limit=100): return []
        
        def execute(self, query, **kwargs): return GraphContext([], [])
        
        def update_node(self, node_id, properties): return True
        def update_edge(self, edge_id, properties): return True
        
        def delete_nodes(self, node_ids, cascade=True): return len(node_ids)
        def delete_edges(self, edge_ids): return len(edge_ids)
        
        def get_schema(self): return {"labels": ["Mock"]}
        def import_graph(self, graph_data, merge_strategy="overwrite"): return {"nodes": 0}
        def export_graph(self, filter_query=None): return GraphContext([], [])

    print("Attempting to instantiate MockGraphPlugin...")
    try:
        plugin = MockGraphPlugin()
        print(f"  -> SUCCESS: Instantiated plugin '{plugin.name}' v{plugin.version}")
        print("  -> PASSED: Interface contract is valid and complete.")
    except TypeError as e:
        print(f"  -> FAILED: Abstract methods missing implementation.\n{e}")
        raise e

if __name__ == "__main__":
    try:
        verify_dto_serialization()
        verify_plugin_interface()
        title("ALL TESTS PASSED")
    except AssertionError as e:
        print(f"\n!!! ASSERTION FAILED !!!\n{e}")
    except Exception as e:
        print(f"\n!!! ERROR !!!\n{e}")