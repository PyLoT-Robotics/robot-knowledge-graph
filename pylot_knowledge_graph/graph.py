"""
ナレッジグラフのコアデータ構造

ロボットの環境知識（部屋、物体、人物、関係性）を有向ラベル付きグラフとして表現する。
omni_plan の KnowledgeGraph に着想を得て、純粋な Python 辞書で実装。

使い方:
    graph = KnowledgeGraph()
    graph.add_node(KGNode("kitchen", "room"))
    graph.add_node(KGNode("entrance", "room"))
    graph.add_edge(KGEdge("connected_to", "kitchen", "entrance"))
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class KGNode:
    """
    ナレッジグラフのノード。

    Attributes:
        name: ノードの一意な名前 (例: "kitchen", "apple", "pylot")
        node_type: ノードの種類 (例: "room", "object", "robot", "furniture")
        properties: 任意の付加属性 (例: {"x": 2.87, "y": 1.36, "color": "red"})
    """

    name: str
    node_type: str
    properties: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name or not isinstance(self.node_type, str) or not self.node_type:
            raise ValueError("Node name and type must be nonempty strings")
        if not isinstance(self.properties, dict):
            raise ValueError("Node properties must be a mapping")

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, KGNode):
            return NotImplemented
        return self.name == other.name

    def __repr__(self) -> str:
        return f"KGNode({self.name!r}, type={self.node_type!r})"

    def to_dict(self) -> dict:
        """辞書表現に変換する (YAML/JSON シリアライズ用)。"""
        result: dict = {"name": self.name, "type": self.node_type}
        if self.properties:
            result["properties"] = dict(self.properties)
        return result

    @classmethod
    def from_dict(cls, data: dict) -> KGNode:
        """辞書から KGNode を復元する。"""
        return cls(
            name=data["name"],
            node_type=data["type"],
            properties=dict(data.get("properties", {})),
        )


@dataclass
class KGEdge:
    """
    ナレッジグラフのエッジ（ラベル付き有向辺）。

    Attributes:
        label: 関係のラベル (例: "connected_to", "is_in", "on_top_of", "robot_at")
        source: ソースノード名
        target: ターゲットノード名
        properties: 任意の付加属性 (例: {"distance": 3.5, "confidence": 0.9})
    """

    label: str
    source: str
    target: str
    properties: Dict[str, Any] = field(default_factory=dict)
    is_goal: bool = False

    def __post_init__(self):
        if any(not isinstance(v, str) or not v for v in (self.label,self.source,self.target)):
            raise ValueError("Edge label, source and target must be nonempty strings")
        if not isinstance(self.properties, dict) or not isinstance(self.is_goal, bool):
            raise ValueError("Edge properties must be a mapping and is_goal must be boolean")

    def __hash__(self) -> int:
        return hash((self.label, self.source, self.target))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, KGEdge):
            return NotImplemented
        return (
            self.label == other.label
            and self.source == other.source
            and self.target == other.target
        )

    def __repr__(self) -> str:
        return f"KGEdge({self.source!r} --[{self.label}]--> {self.target!r})"

    def to_dict(self) -> dict:
        """辞書表現に変換する。"""
        result: dict = {
            "label": self.label,
            "source": self.source,
            "target": self.target,
        }
        if self.properties:
            result["properties"] = dict(self.properties)
        if self.is_goal:
            result["is_goal"] = True
        return result

    @classmethod
    def from_dict(cls, data: dict) -> KGEdge:
        """辞書から KGEdge を復元する。"""
        return cls(
            label=data["label"],
            source=data["source"],
            target=data["target"],
            properties=dict(data.get("properties", {})),
            is_goal=data.get("is_goal", False),
        )


class KnowledgeGraph:
    """
    純粋 Python によるナレッジグラフ実装。

    ロボットの周辺環境 (部屋, 物体, 家具, 人物) とそれらの関係性を
    有向ラベル付きグラフとして保持する。

    Example:
        >>> kg = KnowledgeGraph()
        >>> kg.add_node(KGNode("pylot", "robot"))
        >>> kg.add_node(KGNode("kitchen", "room"))
        >>> kg.add_edge(KGEdge("robot_at", "pylot", "kitchen"))
        >>> kg.get_neighbors("pylot")
        [KGNode('kitchen', type='room')]
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, KGNode] = {}
        self._edges: Set[KGEdge] = set()
        # 高速検索用インデックス: source_name -> [edge, ...]
        self._outgoing: Dict[str, List[KGEdge]] = defaultdict(list)
        # 高速検索用インデックス: target_name -> [edge, ...]
        self._incoming: Dict[str, List[KGEdge]] = defaultdict(list)

    # ======================================================================
    # ノード操作
    # ======================================================================

    def add_node(self, node: KGNode) -> bool:
        """
        ノードを追加する。同名のノードが既に存在する場合は False を返す。

        Args:
            node: 追加するノード

        Returns:
            追加できた場合 True、既に存在していた場合 False
        """
        if node.name in self._nodes:
            return False
        self._nodes[node.name] = node
        return True

    def remove_node(self, name: str) -> bool:
        """
        ノードとそれに接続する全エッジを削除する。

        Args:
            name: 削除するノード名

        Returns:
            削除できた場合 True、存在しなかった場合 False
        """
        if name not in self._nodes:
            return False

        # このノードに接続する全エッジを収集して削除
        edges_to_remove = [
            e for e in self._edges if e.source == name or e.target == name
        ]
        for edge in edges_to_remove:
            self._remove_edge_from_indices(edge)
            self._edges.discard(edge)

        del self._nodes[name]
        return True

    def get_node(self, name: str) -> Optional[KGNode]:
        """名前でノードを取得する。存在しない場合は None。"""
        return self._nodes.get(name)

    def has_node(self, name: str) -> bool:
        """ノードが存在するか確認する。"""
        return name in self._nodes

    def get_all_nodes(self) -> List[KGNode]:
        """全ノードをリストで返す。"""
        return list(self._nodes.values())

    def get_nodes_by_type(self, node_type: str) -> List[KGNode]:
        """指定した種類のノードを返す。"""
        return [n for n in self._nodes.values() if n.node_type == node_type]

    def update_node(self, node: KGNode) -> bool:
        """
        既存ノードを更新する（properties を上書き）。

        Args:
            node: 更新するノード (name が一致するノードを上書き)

        Returns:
            更新できた場合 True、存在しなかった場合 False
        """
        if node.name not in self._nodes:
            return False
        self._nodes[node.name] = node
        return True

    # ======================================================================
    # エッジ操作
    # ======================================================================

    def add_edge(self, edge: KGEdge) -> bool:
        """
        エッジを追加する。ソースまたはターゲットのノードが存在しない場合は ValueError。

        Args:
            edge: 追加するエッジ

        Returns:
            追加できた場合 True、同一エッジが既に存在していた場合 False

        Raises:
            ValueError: ソースまたはターゲットノードが存在しない場合
        """
        if edge.source not in self._nodes:
            raise ValueError(
                f"ソースノード '{edge.source}' が存在しません。"
                "先に add_node で追加してください。"
            )
        if edge.target not in self._nodes:
            raise ValueError(
                f"ターゲットノード '{edge.target}' が存在しません。"
                "先に add_node で追加してください。"
            )
        if edge in self._edges:
            return False

        self._edges.add(edge)
        self._outgoing[edge.source].append(edge)
        self._incoming[edge.target].append(edge)
        return True

    def add_bidirectional_edge(
        self,
        label: str,
        node_a: str,
        node_b: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        双方向エッジを追加するヘルパー (connected_to のような対称関係に便利)。

        Returns:
            少なくとも一方のエッジが追加された場合 True
        """
        props = properties or {}
        added_a = self.add_edge(KGEdge(label, node_a, node_b, dict(props)))
        added_b = self.add_edge(KGEdge(label, node_b, node_a, dict(props)))
        return added_a or added_b

    def remove_edge(self, label: str, source: str, target: str) -> bool:
        """
        エッジを削除する。

        Returns:
            削除できた場合 True、存在しなかった場合 False
        """
        edge = KGEdge(label, source, target)
        if edge not in self._edges:
            return False
        self._edges.discard(edge)
        self._remove_edge_from_indices(edge)
        return True

    def get_all_edges(self) -> List[KGEdge]:
        """全エッジをリストで返す。"""
        return list(self._edges)

    def get_edges_by_label(self, label: str) -> List[KGEdge]:
        """指定したラベルのエッジを返す。"""
        return [e for e in self._edges if e.label == label]

    def get_outgoing_edges(self, node_name: str) -> List[KGEdge]:
        """指定ノードから出るエッジを返す。"""
        return list(self._outgoing.get(node_name, []))

    def get_incoming_edges(self, node_name: str) -> List[KGEdge]:
        """指定ノードへ入るエッジを返す。"""
        return list(self._incoming.get(node_name, []))

    # ======================================================================
    # クエリ
    # ======================================================================

    def get_neighbors(self, node_name: str, label: Optional[str] = None) -> List[KGNode]:
        """
        指定ノードの隣接ノード (出方向) を返す。

        Args:
            node_name: 起点ノード名
            label: フィルタするエッジラベル (None なら全ラベル)

        Returns:
            隣接ノードのリスト
        """
        edges = self._outgoing.get(node_name, [])
        if label is not None:
            edges = [e for e in edges if e.label == label]
        return [self._nodes[e.target] for e in edges if e.target in self._nodes]

    def find_path(
        self, source: str, target: str, label: Optional[str] = None
    ) -> Optional[List[str]]:
        """
        BFS で source から target への最短パスを探索する。

        Args:
            source: 起点ノード名
            target: 終点ノード名
            label: エッジラベルでフィルタ (None なら全ラベル)

        Returns:
            パスが見つかった場合はノード名のリスト、見つからなかった場合は None
        """
        if source not in self._nodes or target not in self._nodes:
            return None
        if source == target:
            return [source]

        from collections import deque

        visited: Set[str] = {source}
        queue: deque[List[str]] = deque([[source]])

        while queue:
            path = queue.popleft()
            current = path[-1]

            for neighbor in self.get_neighbors(current, label=label):
                if neighbor.name in visited:
                    continue
                new_path = path + [neighbor.name]
                if neighbor.name == target:
                    return new_path
                visited.add(neighbor.name)
                queue.append(new_path)

        return None

    def query_edges(
        self,
        label: Optional[str] = None,
        source: Optional[str] = None,
        target: Optional[str] = None,
    ) -> List[KGEdge]:
        """
        条件に一致するエッジを検索する。

        引数はすべてオプションで、指定した条件の AND でフィルタされる。
        """
        results = list(self._edges)
        if label is not None:
            results = [e for e in results if e.label == label]
        if source is not None:
            results = [e for e in results if e.source == source]
        if target is not None:
            results = [e for e in results if e.target == target]
        return results

    # ======================================================================
    # シリアライズ
    # ======================================================================

    def to_dict(self) -> dict:
        """グラフ全体を辞書に変換する (YAML/JSON 互換)。"""
        # ノード・エッジをソートしてシリアライズ順序を安定させる
        nodes = sorted(self._nodes.values(), key=lambda n: n.name)
        edges = sorted(self._edges, key=lambda e: (e.label, e.source, e.target))
        return {
            "nodes": [n.to_dict() for n in nodes],
            "edges": [e.to_dict() for e in edges],
        }

    @classmethod
    def from_dict(cls, data: dict) -> KnowledgeGraph:
        """辞書から KnowledgeGraph を復元する。"""
        if not isinstance(data, dict):
            raise ValueError("Graph document must be a mapping")
        if not isinstance(data.get("nodes", []), list) or not isinstance(data.get("edges", []), list):
            raise ValueError("Graph nodes and edges must be lists")
        graph = cls()
        for node_data in data.get("nodes", []):
            node = KGNode.from_dict(node_data)
            if not isinstance(node.name, str) or not node.name or not isinstance(node.node_type, str) or not node.node_type:
                raise ValueError("Node name and type must be nonempty strings")
            if not graph.add_node(node):
                raise ValueError("Duplicate node: " + node.name)
        for edge_data in data.get("edges", []):
            bidirectional = edge_data.get("bidirectional", False)
            if bidirectional:
                graph.add_bidirectional_edge(
                    label=edge_data["label"],
                    node_a=edge_data["source"],
                    node_b=edge_data["target"],
                    properties=edge_data.get("properties"),
                )
            else:
                graph.add_edge(KGEdge.from_dict(edge_data))
        return graph

    # ======================================================================
    # 統計・表示
    # ======================================================================

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(self._edges)

    def summary(self) -> str:
        """グラフの概要を文字列で返す。"""
        type_counts: Dict[str, int] = defaultdict(int)
        for node in self._nodes.values():
            type_counts[node.node_type] += 1

        label_counts: Dict[str, int] = defaultdict(int)
        for edge in self._edges:
            label_counts[edge.label] += 1

        lines = [
            f"KnowledgeGraph: {self.node_count} nodes, {self.edge_count} edges",
            "  Node types: "
            + ", ".join(f"{t}({c})" for t, c in sorted(type_counts.items())),
            "  Edge labels: "
            + ", ".join(f"{l}({c})" for l, c in sorted(label_counts.items())),
        ]
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"KnowledgeGraph(nodes={self.node_count}, edges={self.edge_count})"

    # ======================================================================
    # 内部ヘルパー
    # ======================================================================

    def _remove_edge_from_indices(self, edge: KGEdge) -> None:
        """インデックスからエッジを除去する。"""
        out_list = self._outgoing.get(edge.source, [])
        if edge in out_list:
            out_list.remove(edge)

        in_list = self._incoming.get(edge.target, [])
        if edge in in_list:
            in_list.remove(edge)
