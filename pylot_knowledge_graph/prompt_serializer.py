"""
ナレッジグラフを LLM 向けプロンプト文字列に変換するシリアライザ

KnowledgeGraph の内容を自然言語テキストに変換し、
ChatGPT 等の LLM に渡しやすい形式にする。
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from pylot_knowledge_graph.graph import KnowledgeGraph


class PromptSerializer:
    """KnowledgeGraph を LLM 向けプロンプト文字列に変換するユーティリティ。"""

    @staticmethod
    def serialize_full(graph: KnowledgeGraph) -> str:
        """
        グラフ全体を構造化テキストに変換する。

        Args:
            graph: 変換対象のナレッジグラフ

        Returns:
            LLM 向けプロンプト文字列
        """
        sections: List[str] = ["## Environment Knowledge"]

        # --- ノードをタイプ別にグループ化 ---
        type_groups: dict[str, list] = defaultdict(list)
        for node in graph.get_all_nodes():
            type_groups[node.node_type].append(node)

        for node_type, nodes in sorted(type_groups.items()):
            section_title = f"### {node_type.replace('_', ' ').title()}s"
            items = []
            for node in sorted(nodes, key=lambda n: n.name):
                props_str = ""
                if node.properties:
                    props_parts = [
                        f"{k}={v}" for k, v in sorted(node.properties.items())
                    ]
                    props_str = f" ({', '.join(props_parts)})"
                items.append(f"- {node.name}{props_str}")
            sections.append(section_title)
            sections.extend(items)

        # --- エッジをラベル別にグループ化 ---
        label_groups: dict[str, list] = defaultdict(list)
        for edge in graph.get_all_edges():
            label_groups[edge.label].append(edge)

        if label_groups:
            sections.append("### Relationships")
            for label, edges in sorted(label_groups.items()):
                readable_label = label.replace("_", " ")
                for edge in sorted(edges, key=lambda e: (e.source, e.target)):
                    sections.append(
                        f"- {edge.source} [{readable_label}] {edge.target}"
                    )

        return "\n".join(sections)

    @staticmethod
    def serialize_context(
        graph: KnowledgeGraph,
        focus_node: str,
        max_depth: int = 2,
    ) -> str:
        """
        特定ノードの周辺コンテキストをテキスト化する。

        Args:
            graph: ナレッジグラフ
            focus_node: 着目するノード名
            max_depth: 探索する深さの上限

        Returns:
            着目ノード周辺の情報を含むプロンプト文字列
        """
        node = graph.get_node(focus_node)
        if node is None:
            return f"Node '{focus_node}' not found in the knowledge graph."

        sections: List[str] = [
            f"## Context for '{focus_node}' (type: {node.node_type})"
        ]

        if node.properties:
            props = ", ".join(
                f"{k}={v}" for k, v in sorted(node.properties.items())
            )
            sections.append(f"Properties: {props}")

        # BFS で周辺を探索
        visited = {focus_node}
        current_layer = [focus_node]

        for depth in range(1, max_depth + 1):
            next_layer: List[str] = []
            depth_relations: List[str] = []

            for current_name in current_layer:
                for edge in graph.get_outgoing_edges(current_name):
                    target = graph.get_node(edge.target)
                    if target is None:
                        continue
                    readable = edge.label.replace("_", " ")
                    depth_relations.append(
                        f"- {current_name} [{readable}] "
                        f"{target.name} (type: {target.node_type})"
                    )
                    if target.name not in visited:
                        visited.add(target.name)
                        next_layer.append(target.name)

            if depth_relations:
                sections.append(f"### Depth {depth}")
                sections.extend(depth_relations)

            current_layer = next_layer

        return "\n".join(sections)

    @staticmethod
    def serialize_for_planning(
        graph: KnowledgeGraph,
        task_description: str,
        robot_name: Optional[str] = None,
    ) -> str:
        """
        タスクプランニング向けのプロンプトを生成する。

        ロボットの現在位置、環境情報、タスク指示をまとめて
        LLM がアクションプランを生成しやすい形式にする。

        Args:
            graph: ナレッジグラフ
            task_description: ユーザーからのタスク指示
            robot_name: ロボットノードの名前 (None の場合は自動検出)

        Returns:
            プランニング向けプロンプト文字列
        """
        sections: List[str] = []

        # ロボットを特定
        if robot_name is None:
            robots = graph.get_nodes_by_type("robot")
            if robots:
                robot_name = robots[0].name

        # ロボットの現在位置を取得
        if robot_name:
            robot_at_edges = graph.query_edges(label="robot_at", source=robot_name)
            if robot_at_edges:
                location = robot_at_edges[0].target
                sections.append(
                    f"The robot '{robot_name}' is currently at '{location}'."
                )

        # 環境全体の情報
        sections.append("")
        sections.append(PromptSerializer.serialize_full(graph))

        # タスク指示
        sections.append("")
        sections.append("## Task")
        sections.append(task_description)

        # プランニング指示
        sections.append("")
        sections.append("## Instructions")
        sections.append(
            "Based on the environment knowledge above, "
            "create a step-by-step action plan to accomplish the task. "
            "Each step should specify: action name, target object/location, "
            "and any relevant parameters. "
            "Output the plan as a JSON array of action objects."
        )

        return "\n".join(sections)
