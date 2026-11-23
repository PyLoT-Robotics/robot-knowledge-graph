"""PddlSerializer のユニットテスト"""

from pylot_knowledge_graph.graph import KGEdge, KGNode, KnowledgeGraph
from pylot_knowledge_graph.pddl_serializer import PddlSerializer


def _build_sample_graph() -> KnowledgeGraph:
    """テスト用グラフを構築する。"""
    kg = KnowledgeGraph()
    kg.add_node(KGNode("pylot", "robot"))
    kg.add_node(KGNode("entrance", "room"))
    kg.add_node(KGNode("kitchen", "room"))
    kg.add_node(KGNode("apple", "object"))

    kg.add_edge(KGEdge("connected_to", "entrance", "kitchen"))
    kg.add_edge(KGEdge("robot_at", "pylot", "entrance"))
    return kg


class TestPddlSerializer:
    def test_serialize_problem_basic(self):
        kg = _build_sample_graph()
        pddl = PddlSerializer.serialize_problem(kg)

        assert "(define (problem pylot_problem)" in pddl
        assert "(:domain pylot_domain)" in pddl

        # Objects
        assert "(:objects" in pddl
        assert "pylot - robot" in pddl
        assert "entrance kitchen - room" in pddl or "kitchen entrance - room" in pddl
        assert "apple - object" in pddl

        # Init facts
        assert "(:init" in pddl
        assert "(connected_to entrance kitchen)" in pddl
        assert "(robot_at pylot entrance)" in pddl

        # Goal is empty
        assert "(:goal (and))" in pddl

    def test_serialize_problem_with_goals(self):
        kg = _build_sample_graph()
        goals = ["(robot_at pylot kitchen)", "(holding pylot apple)"]
        pddl = PddlSerializer.serialize_problem(kg, goals=goals)

        assert "(:goal (and" in pddl
        assert "(robot_at pylot kitchen)" in pddl
        assert "(holding pylot apple)" in pddl

    def test_serialize_empty_graph(self):
        kg = KnowledgeGraph()
        pddl = PddlSerializer.serialize_problem(kg)

        assert "(:objects" in pddl
        assert "- robot" not in pddl
        assert "(:init" in pddl
        assert "(:goal (and))" in pddl

    def test_serialize_problem_with_is_goal_edges(self):
        kg = _build_sample_graph()
        # Add 1-ary predicate
        kg.add_edge(KGEdge("hand_empty", "pylot", "pylot"))

        # Add goal edge (2-ary)
        kg.add_edge(KGEdge("robot_at", "pylot", "kitchen", is_goal=True))
        # Add goal edge (1-ary)
        kg.add_edge(KGEdge("explored", "kitchen", "kitchen", is_goal=True))

        pddl = PddlSerializer.serialize_problem(kg)

        # 1-ary predicate correctly added to init
        assert "(hand_empty pylot)" in pddl
        # Goal correctly extracted from edge.is_goal
        assert "(:goal (and" in pddl
        assert "(robot_at pylot kitchen)" in pddl
        assert "(explored kitchen)" in pddl

    def test_custom_names(self):
        kg = _build_sample_graph()
        pddl = PddlSerializer.serialize_problem(kg, problem_name="my_prob", domain_name="my_dom")
        assert "(define (problem my_prob)" in pddl
        assert "(:domain my_dom)" in pddl
