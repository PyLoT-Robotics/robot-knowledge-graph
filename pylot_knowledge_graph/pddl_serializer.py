"""
ナレッジグラフを PDDL (Planning Domain Definition Language) 問題定義ファイルに変換するシリアライザ
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional
import re

if TYPE_CHECKING:
    from pylot_knowledge_graph.graph import KnowledgeGraph


class PddlSerializer:
    """KnowledgeGraph を PDDL 問題定義 (Problem) 文字列に変換するユーティリティ。"""

    @staticmethod
    def serialize_problem(
        graph: KnowledgeGraph,
        problem_name: str = "pylot_problem",
        domain_name: str = "pylot_domain",
        goals: Optional[List[str]] = None,
    ) -> str:
        """
        グラフ全体を PDDL の Problem 定義に変換する。

        Args:
            graph: 変換対象のナレッジグラフ
            problem_name: PDDL 問題名 (デフォルト: pylot_problem)
            domain_name: 対応する PDDL ドメイン名 (デフォルト: pylot_domain)
            goals: 追加の PDDL ゴール条件のリスト (例: ["(robot_at pylot bedroom)"])。
                   KGEdge の `is_goal=True` であるエッジも自動的にゴールに追加されます。

        Returns:
            PDDL の Problem 定義文字列
        """
        # PDDL symbols cannot contain whitespace or expression syntax. PDDL is
        # case-insensitive, so differently cased node IDs must not collapse.
        symbols = [problem_name, domain_name]
        names = [node.name for node in graph.get_all_nodes()]
        if len({name.casefold() for name in names}) != len(names):
            raise ValueError("PDDL node names must be unique ignoring case")
        for node in graph.get_all_nodes():
            symbols.extend([node.name, node.node_type])
        arities = {}
        for edge in graph.get_all_edges():
            symbols.append(edge.label)
            arity = 1 if edge.source == edge.target else 2
            label = edge.label.casefold()
            if label in arities and arities[label] != arity:
                raise ValueError("PDDL predicate has inconsistent arity: " + edge.label)
            arities[label] = arity
        if any(not isinstance(value, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", value)
               for value in symbols):
            raise ValueError("Invalid PDDL symbol; use letters, digits, underscores and hyphens")
        lines = []
        lines.append(f"(define (problem {problem_name})")
        lines.append(f"  (:domain {domain_name})")
        lines.append("")

        # --- Objects ---
        lines.append("  (:objects")

        # PDDLのオブジェクトは種類(type)ごとにまとめるのが一般的
        type_groups: dict[str, list[str]] = {}
        for node in graph.get_all_nodes():
            if node.node_type not in type_groups:
                type_groups[node.node_type] = []
            type_groups[node.node_type].append(node.name)

        for node_type, names in sorted(type_groups.items()):
            names_str = " ".join(sorted(names))
            lines.append(f"    {names_str} - {node_type}")

        lines.append("  )")
        lines.append("")

        # Init facts (is_goal が False のものを追加)
        lines.append("  (:init")
        for edge in sorted(graph.get_all_edges(), key=lambda e: (e.label, e.source, e.target)):
            if not edge.is_goal:
                if edge.source == edge.target:
                    # 1項述語 (単一引数)
                    lines.append(f"    ({edge.label} {edge.source})")
                else:
                    # 2項述語 (複数引数)
                    lines.append(f"    ({edge.label} {edge.source} {edge.target})")
        lines.append("  )")
        lines.append("")

        # --- Goal ---

        # graph 内の is_goal=True なエッジを収集
        graph_goals = []
        for edge in sorted(graph.get_all_edges(), key=lambda e: (e.label, e.source, e.target)):
            if edge.is_goal:
                if edge.source == edge.target:
                    graph_goals.append(f"({edge.label} {edge.source})")
                else:
                    graph_goals.append(f"({edge.label} {edge.source} {edge.target})")

        all_goals = []
        if goals:
            all_goals.extend(goals)
        all_goals.extend(graph_goals)

        if all_goals:
            lines.append("  (:goal (and")
            for goal in all_goals:
                lines.append(f"    {goal}")
            lines.append("  ))")
        else:
            lines.append("  (:goal (and))")

        lines.append(")")
        return "\n".join(lines)
