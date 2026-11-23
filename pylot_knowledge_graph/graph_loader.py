"""
YAML ファイルからナレッジグラフを読み込み・書き出しするローダー
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from pylot_knowledge_graph.graph import KGEdge, KGNode, KnowledgeGraph

if TYPE_CHECKING:
    pass


class GraphLoader:
    """YAML ファイルと KnowledgeGraph の相互変換を行うユーティリティ。"""

    @staticmethod
    def load_from_yaml(filepath: str) -> KnowledgeGraph:
        """
        YAML ファイルからナレッジグラフを構築する。

        YAML フォーマット:
            nodes:
              - name: kitchen
                type: room
                properties:
                  x: 2.87
                  y: 1.36
            edges:
              - label: connected_to
                source: kitchen
                target: entrance
                bidirectional: true  # オプション

        Args:
            filepath: YAML ファイルのパス

        Returns:
            構築された KnowledgeGraph
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data is None:
            return KnowledgeGraph()

        return KnowledgeGraph.from_dict(data)

    @staticmethod
    def save_to_yaml(graph: KnowledgeGraph, filepath: str) -> None:
        """
        ナレッジグラフを YAML ファイルに保存する。

        Args:
            graph: 保存するグラフ
            filepath: 出力先ファイルパス
        """
        data = graph.to_dict()
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(
                data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
