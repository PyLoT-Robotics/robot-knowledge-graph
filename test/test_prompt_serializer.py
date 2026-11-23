"""PromptSerializer のユニットテスト"""

from pylot_knowledge_graph.graph import KGEdge, KGNode, KnowledgeGraph
from pylot_knowledge_graph.prompt_serializer import PromptSerializer


def _build_sample_graph() -> KnowledgeGraph:
    """テスト用グラフを構築する。"""
    kg = KnowledgeGraph()
    kg.add_node(KGNode("pylot", "robot"))
    kg.add_node(KGNode("entrance", "room"))
    kg.add_node(KGNode("kitchen", "room"))
    kg.add_node(KGNode("kitchen_table", "furniture"))
    kg.add_node(KGNode("apple", "object", {"category": "fruit"}))

    kg.add_bidirectional_edge("connected_to", "entrance", "kitchen")
    kg.add_edge(KGEdge("robot_at", "pylot", "entrance"))
    kg.add_edge(KGEdge("is_in", "kitchen_table", "kitchen"))
    kg.add_edge(KGEdge("on_top_of", "apple", "kitchen_table"))
    return kg


class TestPromptSerializer:
    def test_serialize_full_contains_nodes(self):
        kg = _build_sample_graph()
        prompt = PromptSerializer.serialize_full(kg)
        assert "pylot" in prompt
        assert "entrance" in prompt
        assert "kitchen" in prompt
        assert "apple" in prompt

    def test_serialize_full_contains_relationships(self):
        kg = _build_sample_graph()
        prompt = PromptSerializer.serialize_full(kg)
        assert "connected to" in prompt
        assert "robot at" in prompt
        assert "on top of" in prompt

    def test_serialize_full_contains_properties(self):
        kg = _build_sample_graph()
        prompt = PromptSerializer.serialize_full(kg)
        assert "category=fruit" in prompt

    def test_serialize_context_focus_node(self):
        kg = _build_sample_graph()
        prompt = PromptSerializer.serialize_context(kg, "pylot")
        assert "pylot" in prompt
        assert "entrance" in prompt

    def test_serialize_context_nonexistent(self):
        kg = _build_sample_graph()
        prompt = PromptSerializer.serialize_context(kg, "nonexistent")
        assert "not found" in prompt

    def test_serialize_for_planning(self):
        kg = _build_sample_graph()
        task = "Pick up the apple."
        prompt = PromptSerializer.serialize_for_planning(kg, task)
        assert "Pick up the apple" in prompt
        assert "entrance" in prompt  # ロボットの現在位置
        assert "action plan" in prompt.lower() or "JSON" in prompt

    def test_serialize_for_planning_robot_location(self):
        kg = _build_sample_graph()
        prompt = PromptSerializer.serialize_for_planning(kg, "test task")
        assert "currently at 'entrance'" in prompt

    def test_serialize_for_planning_explicit_robot(self):
        kg = _build_sample_graph()
        prompt = PromptSerializer.serialize_for_planning(
            kg, "test task", robot_name="pylot"
        )
        assert "'pylot'" in prompt

    def test_serialize_empty_graph(self):
        kg = KnowledgeGraph()
        prompt = PromptSerializer.serialize_full(kg)
        assert "Environment Knowledge" in prompt
