"""KnowledgeGraph のユニットテスト"""

import pytest

from pylot_knowledge_graph.graph import KGEdge, KGNode, KnowledgeGraph


# ======================================================================
# KGNode テスト
# ======================================================================


class TestKGNode:
    def test_create_node(self):
        node = KGNode("kitchen", "room")
        assert node.name == "kitchen"
        assert node.node_type == "room"
        assert node.properties == {}

    def test_create_node_with_properties(self):
        node = KGNode("kitchen", "room", {"x": 2.87, "y": 1.36})
        assert node.properties["x"] == 2.87

    def test_node_equality(self):
        """同名ノードは等価。"""
        n1 = KGNode("kitchen", "room")
        n2 = KGNode("kitchen", "room", {"x": 1.0})
        assert n1 == n2

    def test_node_inequality(self):
        n1 = KGNode("kitchen", "room")
        n2 = KGNode("bedroom", "room")
        assert n1 != n2

    def test_node_hash(self):
        n1 = KGNode("kitchen", "room")
        n2 = KGNode("kitchen", "room")
        assert hash(n1) == hash(n2)

    def test_node_serialization(self):
        node = KGNode("kitchen", "room", {"x": 1.0})
        d = node.to_dict()
        restored = KGNode.from_dict(d)
        assert restored.name == "kitchen"
        assert restored.node_type == "room"
        assert restored.properties["x"] == 1.0


# ======================================================================
# KGEdge テスト
# ======================================================================


class TestKGEdge:
    def test_create_edge(self):
        edge = KGEdge("connected_to", "kitchen", "entrance")
        assert edge.label == "connected_to"
        assert edge.source == "kitchen"
        assert edge.target == "entrance"

    def test_edge_equality(self):
        e1 = KGEdge("connected_to", "kitchen", "entrance")
        e2 = KGEdge("connected_to", "kitchen", "entrance")
        assert e1 == e2

    def test_edge_inequality_label(self):
        e1 = KGEdge("connected_to", "kitchen", "entrance")
        e2 = KGEdge("is_in", "kitchen", "entrance")
        assert e1 != e2

    def test_edge_serialization(self):
        edge = KGEdge("is_in", "apple", "kitchen", {"confidence": 0.9})
        d = edge.to_dict()
        restored = KGEdge.from_dict(d)
        assert restored.label == "is_in"
        assert restored.properties["confidence"] == 0.9


# ======================================================================
# KnowledgeGraph テスト
# ======================================================================


class TestKnowledgeGraph:
    def _build_sample_graph(self) -> KnowledgeGraph:
        """テスト用のサンプルグラフを構築する。"""
        kg = KnowledgeGraph()
        kg.add_node(KGNode("pylot", "robot"))
        kg.add_node(KGNode("entrance", "room"))
        kg.add_node(KGNode("kitchen", "room"))
        kg.add_node(KGNode("living_room", "room"))
        kg.add_node(KGNode("bedroom", "room"))
        kg.add_node(KGNode("bathroom", "room"))

        kg.add_bidirectional_edge("connected_to", "entrance", "living_room")
        kg.add_bidirectional_edge("connected_to", "living_room", "kitchen")
        kg.add_bidirectional_edge("connected_to", "living_room", "bedroom")
        kg.add_bidirectional_edge("connected_to", "bedroom", "bathroom")

        kg.add_edge(KGEdge("robot_at", "pylot", "entrance"))
        return kg

    # --- ノード操作テスト ---

    def test_add_node(self):
        kg = KnowledgeGraph()
        assert kg.add_node(KGNode("kitchen", "room")) is True
        assert kg.node_count == 1

    def test_add_duplicate_node(self):
        kg = KnowledgeGraph()
        kg.add_node(KGNode("kitchen", "room"))
        assert kg.add_node(KGNode("kitchen", "room")) is False
        assert kg.node_count == 1

    def test_remove_node(self):
        kg = KnowledgeGraph()
        kg.add_node(KGNode("kitchen", "room"))
        assert kg.remove_node("kitchen") is True
        assert kg.node_count == 0

    def test_remove_node_cascades_edges(self):
        kg = KnowledgeGraph()
        kg.add_node(KGNode("a", "room"))
        kg.add_node(KGNode("b", "room"))
        kg.add_edge(KGEdge("connected_to", "a", "b"))
        kg.remove_node("a")
        assert kg.edge_count == 0

    def test_remove_nonexistent_node(self):
        kg = KnowledgeGraph()
        assert kg.remove_node("nothing") is False

    def test_get_node(self):
        kg = KnowledgeGraph()
        kg.add_node(KGNode("kitchen", "room"))
        node = kg.get_node("kitchen")
        assert node is not None
        assert node.node_type == "room"

    def test_get_nonexistent_node(self):
        kg = KnowledgeGraph()
        assert kg.get_node("nothing") is None

    def test_has_node(self):
        kg = KnowledgeGraph()
        kg.add_node(KGNode("kitchen", "room"))
        assert kg.has_node("kitchen") is True
        assert kg.has_node("nothing") is False

    def test_get_nodes_by_type(self):
        kg = self._build_sample_graph()
        rooms = kg.get_nodes_by_type("room")
        assert len(rooms) == 5
        robots = kg.get_nodes_by_type("robot")
        assert len(robots) == 1

    def test_update_node(self):
        kg = KnowledgeGraph()
        kg.add_node(KGNode("kitchen", "room"))
        updated = KGNode("kitchen", "room", {"x": 1.0})
        assert kg.update_node(updated) is True
        assert kg.get_node("kitchen").properties["x"] == 1.0

    def test_update_nonexistent_node(self):
        kg = KnowledgeGraph()
        assert kg.update_node(KGNode("nothing", "room")) is False

    # --- エッジ操作テスト ---

    def test_add_edge(self):
        kg = KnowledgeGraph()
        kg.add_node(KGNode("a", "room"))
        kg.add_node(KGNode("b", "room"))
        assert kg.add_edge(KGEdge("connected_to", "a", "b")) is True
        assert kg.edge_count == 1

    def test_add_duplicate_edge(self):
        kg = KnowledgeGraph()
        kg.add_node(KGNode("a", "room"))
        kg.add_node(KGNode("b", "room"))
        kg.add_edge(KGEdge("connected_to", "a", "b"))
        assert kg.add_edge(KGEdge("connected_to", "a", "b")) is False

    def test_add_edge_missing_source(self):
        kg = KnowledgeGraph()
        kg.add_node(KGNode("b", "room"))
        with pytest.raises(ValueError):
            kg.add_edge(KGEdge("connected_to", "a", "b"))

    def test_add_edge_missing_target(self):
        kg = KnowledgeGraph()
        kg.add_node(KGNode("a", "room"))
        with pytest.raises(ValueError):
            kg.add_edge(KGEdge("connected_to", "a", "b"))

    def test_add_bidirectional_edge(self):
        kg = KnowledgeGraph()
        kg.add_node(KGNode("a", "room"))
        kg.add_node(KGNode("b", "room"))
        kg.add_bidirectional_edge("connected_to", "a", "b")
        assert kg.edge_count == 2

    def test_remove_edge(self):
        kg = KnowledgeGraph()
        kg.add_node(KGNode("a", "room"))
        kg.add_node(KGNode("b", "room"))
        kg.add_edge(KGEdge("connected_to", "a", "b"))
        assert kg.remove_edge("connected_to", "a", "b") is True
        assert kg.edge_count == 0

    def test_remove_nonexistent_edge(self):
        kg = KnowledgeGraph()
        assert kg.remove_edge("x", "y", "z") is False

    def test_get_edges_by_label(self):
        kg = self._build_sample_graph()
        connected = kg.get_edges_by_label("connected_to")
        assert len(connected) == 8  # 4 双方向 = 8 エッジ

    def test_get_outgoing_edges(self):
        kg = self._build_sample_graph()
        out = kg.get_outgoing_edges("pylot")
        assert len(out) == 1
        assert out[0].label == "robot_at"

    def test_get_incoming_edges(self):
        kg = self._build_sample_graph()
        inc = kg.get_incoming_edges("entrance")
        labels = {e.label for e in inc}
        assert "robot_at" in labels

    # --- クエリテスト ---

    def test_get_neighbors(self):
        kg = self._build_sample_graph()
        neighbors = kg.get_neighbors("living_room", label="connected_to")
        names = {n.name for n in neighbors}
        assert "entrance" in names
        assert "kitchen" in names
        assert "bedroom" in names

    def test_get_neighbors_no_label_filter(self):
        kg = self._build_sample_graph()
        neighbors = kg.get_neighbors("pylot")
        assert len(neighbors) == 1
        assert neighbors[0].name == "entrance"

    def test_query_edges(self):
        kg = self._build_sample_graph()
        results = kg.query_edges(label="robot_at", source="pylot")
        assert len(results) == 1
        assert results[0].target == "entrance"

    # --- パス探索テスト ---

    def test_find_path_direct(self):
        kg = self._build_sample_graph()
        path = kg.find_path("entrance", "living_room", label="connected_to")
        assert path == ["entrance", "living_room"]

    def test_find_path_multi_hop(self):
        kg = self._build_sample_graph()
        path = kg.find_path("entrance", "bathroom", label="connected_to")
        assert path is not None
        assert path[0] == "entrance"
        assert path[-1] == "bathroom"
        assert len(path) == 4  # entrance → living_room → bedroom → bathroom

    def test_find_path_same_node(self):
        kg = self._build_sample_graph()
        path = kg.find_path("entrance", "entrance")
        assert path == ["entrance"]

    def test_find_path_nonexistent(self):
        kg = KnowledgeGraph()
        assert kg.find_path("a", "b") is None

    def test_find_path_no_route(self):
        kg = KnowledgeGraph()
        kg.add_node(KGNode("a", "room"))
        kg.add_node(KGNode("b", "room"))
        # エッジなし
        assert kg.find_path("a", "b") is None

    # --- シリアライズテスト ---

    def test_round_trip_serialization(self):
        kg = self._build_sample_graph()
        data = kg.to_dict()
        restored = KnowledgeGraph.from_dict(data)
        assert restored.node_count == kg.node_count
        assert restored.edge_count == kg.edge_count

    def test_summary(self):
        kg = self._build_sample_graph()
        summary = kg.summary()
        assert "6 nodes" in summary
        assert "9 edges" in summary
