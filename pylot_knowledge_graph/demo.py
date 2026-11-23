"""
ナレッジグラフのデモスクリプト

omni_plan の knowledge_graph_demo.cpp に相当。
ROS2 なしでもグラフの構築・クエリ・プロンプト生成をテストできる。
"""

import os

from pylot_knowledge_graph.graph import KGEdge, KGNode, KnowledgeGraph
from pylot_knowledge_graph.graph_loader import GraphLoader
from pylot_knowledge_graph.prompt_serializer import PromptSerializer


def demo_manual_construction() -> KnowledgeGraph:
    """手動でグラフを構築するデモ (omni_plan demo 相当)。"""
    print("=" * 60)
    print("Demo 1: Manual Graph Construction")
    print("=" * 60)

    graph = KnowledgeGraph()

    # ロボット
    graph.add_node(KGNode("pylot", "robot", {"description": "PyLoT service robot"}))

    # 部屋
    for room in ["entrance", "kitchen", "living_room", "bedroom", "bathroom"]:
        graph.add_node(KGNode(room, "room"))

    # 部屋の接続 (双方向)
    graph.add_bidirectional_edge("connected_to", "entrance", "living_room")
    graph.add_bidirectional_edge("connected_to", "living_room", "kitchen")
    graph.add_bidirectional_edge("connected_to", "living_room", "bedroom")
    graph.add_bidirectional_edge("connected_to", "bedroom", "bathroom")

    # 家具
    graph.add_node(KGNode("kitchen_table", "furniture"))
    graph.add_edge(KGEdge("is_in", "kitchen_table", "kitchen"))

    # 物体
    graph.add_node(KGNode("apple", "object", {"category": "fruit"}))
    graph.add_edge(KGEdge("on_top_of", "apple", "kitchen_table"))

    # ロボットの位置
    graph.add_edge(KGEdge("robot_at", "pylot", "entrance"))

    # 結果表示
    print(f"\n{graph.summary()}\n")

    print("All nodes:")
    for node in graph.get_all_nodes():
        print(f"  {node}")

    print("\nAll edges:")
    for edge in graph.get_all_edges():
        print(f"  {edge}")

    # パス探索テスト
    print("\n--- Path Finding ---")
    path = graph.find_path("entrance", "bathroom", label="connected_to")
    if path:
        print(f"Path from entrance to bathroom: {' → '.join(path)}")
    else:
        print("No path found from entrance to bathroom")

    path2 = graph.find_path("pylot", "apple")
    if path2:
        print(f"Path from pylot to apple: {' → '.join(path2)}")

    return graph


def demo_yaml_loading() -> None:
    """YAML ファイルからのグラフ読み込みデモ。"""
    print("\n" + "=" * 60)
    print("Demo 2: YAML Loading")
    print("=" * 60)

    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "config",
        "sample_environment.yaml",
    )

    if os.path.exists(config_path):
        graph = GraphLoader.load_from_yaml(config_path)
        print(f"\nLoaded from: {config_path}")
        print(graph.summary())
    else:
        print(f"Config file not found: {config_path}")
        print("Using manual construction instead")
        graph = demo_manual_construction()

    return graph


def demo_prompt_generation(graph: KnowledgeGraph) -> None:
    """LLM 向けプロンプト生成デモ。"""
    print("\n" + "=" * 60)
    print("Demo 3: Prompt Generation")
    print("=" * 60)

    # フルプロンプト
    print("\n--- Full Environment Prompt ---")
    print(PromptSerializer.serialize_full(graph))

    # コンテキストプロンプト
    print("\n--- Context Prompt (focus: pylot) ---")
    print(PromptSerializer.serialize_context(graph, "pylot"))

    # タスクプランニングプロンプト
    print("\n--- Planning Prompt ---")
    task = "Please pick up the apple on the kitchen table and bring it to the bedroom."
    print(PromptSerializer.serialize_for_planning(graph, task))


def main(args=None):
    """デモメイン関数 (ROS2 なしで動作)。"""
    # 手動構築デモ
    graph = demo_manual_construction()

    # YAML 読み込みデモ
    graph_from_yaml = demo_yaml_loading()

    # プロンプト生成デモ
    demo_prompt_generation(graph_from_yaml if graph_from_yaml else graph)

    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
