"""GraphLoader のユニットテスト"""

import os
import tempfile

from pylot_knowledge_graph.graph import KGEdge, KGNode, KnowledgeGraph
from pylot_knowledge_graph.graph_loader import GraphLoader


def _build_sample_graph() -> KnowledgeGraph:
    """テスト用グラフを構築する。"""
    kg = KnowledgeGraph()
    kg.add_node(KGNode("pylot", "robot"))
    kg.add_node(KGNode("entrance", "room", {"x": 2.87, "y": 1.36}))
    kg.add_node(KGNode("kitchen", "room"))
    kg.add_edge(KGEdge("connected_to", "entrance", "kitchen"))
    kg.add_edge(KGEdge("robot_at", "pylot", "entrance"))
    return kg


class TestGraphLoader:
    def test_save_and_load_round_trip(self):
        """YAML への保存と読み込みの往復テスト。"""
        original = _build_sample_graph()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            tmp_path = f.name

        try:
            GraphLoader.save_to_yaml(original, tmp_path)
            loaded = GraphLoader.load_from_yaml(tmp_path)

            assert loaded.node_count == original.node_count
            assert loaded.edge_count == original.edge_count

            # ノードの内容を検証
            pylot = loaded.get_node("pylot")
            assert pylot is not None
            assert pylot.node_type == "robot"

            entrance = loaded.get_node("entrance")
            assert entrance is not None
            assert entrance.properties["x"] == 2.87
        finally:
            os.unlink(tmp_path)

    def test_load_sample_config(self):
        """同梱の sample_environment.yaml が正しくロードできること。"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "config",
            "sample_environment.yaml",
        )
        if not os.path.exists(config_path):
            return  # CI 等で config が無い場合はスキップ

        graph = GraphLoader.load_from_yaml(config_path)
        assert graph.node_count > 0
        assert graph.edge_count > 0
        assert graph.has_node("pylot")
        assert graph.has_node("entrance")

    def test_load_empty_file(self):
        """空ファイルを読んでもエラーにならないこと。"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("")
            tmp_path = f.name

        try:
            graph = GraphLoader.load_from_yaml(tmp_path)
            assert graph.node_count == 0
            assert graph.edge_count == 0
        finally:
            os.unlink(tmp_path)

    def test_load_bidirectional_edges(self):
        """bidirectional フラグが正しく処理されること。"""
        yaml_content = """
nodes:
  - name: a
    type: room
  - name: b
    type: room
edges:
  - label: connected_to
    source: a
    target: b
    bidirectional: true
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            tmp_path = f.name

        try:
            graph = GraphLoader.load_from_yaml(tmp_path)
            assert graph.edge_count == 2  # 双方向 = 2 エッジ

            # 両方向のエッジが存在
            ab = graph.query_edges(label="connected_to", source="a", target="b")
            ba = graph.query_edges(label="connected_to", source="b", target="a")
            assert len(ab) == 1
            assert len(ba) == 1
        finally:
            os.unlink(tmp_path)
