"""
ナレッジグラフの ROS2 ノード

他のノードからサービス経由でグラフの CRUD 操作を行えるようにする。
起動時に YAML で定義された環境情報をロードし、
実行中にサービスでノード/エッジの追加・削除・クエリが可能。
"""

import json

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
from std_msgs.msg import String

from pylot_knowledge_graph.graph import KGEdge, KGNode, KnowledgeGraph
from pylot_knowledge_graph.graph_loader import GraphLoader
from pylot_knowledge_graph.prompt_serializer import PromptSerializer
from pylot_knowledge_graph.pddl_serializer import PddlSerializer


class KnowledgeGraphNode(Node):
    """
    ナレッジグラフを管理する ROS2 ノード。

    サービス:
        ~/add_node     : ノード追加 (JSON)
        ~/remove_node  : ノード削除 (JSON)
        ~/add_edge     : エッジ追加 (JSON)
        ~/remove_edge  : エッジ削除 (JSON)
        ~/query        : グラフ全体を JSON で返す
        ~/get_prompt   : LLM 向けプロンプト文字列を返す
        ~/get_pddl_problem : PDDL 問題定義 (Problem) を返す

    パラメータ:
        config_file : 初期グラフ定義の YAML ファイルパス
    """

    def __init__(self) -> None:
        super().__init__("knowledge_graph_node")

        # パラメータ
        self.declare_parameter("config_file", "")

        # グラフの初期化
        config_file = (
            self.get_parameter("config_file").get_parameter_value().string_value
        )
        if config_file:
            self.get_logger().info(f"Loading graph from: {config_file}")
            self.graph = GraphLoader.load_from_yaml(config_file)
        else:
            self.get_logger().info("Starting with empty knowledge graph")
            self.graph = KnowledgeGraph()

        self.get_logger().info(
            f"Knowledge graph initialized: {self.graph.summary()}"
        )

        # サービス作成
        # add_node / remove_node: std_msgs/String の Request/Response がないため
        # Trigger を使い、追加情報は別トピックで受け取る方式ではなく、
        # Callback 内で JSON パース方式を取る。
        # ※ 初期版では Trigger (引数なし → 結果のみ) は query/prompt に使い、
        #   ノード/エッジ操作は topic (String) 経由のリクエスト・レスポンスとする。

        # --- 情報取得系サービス (引数なし) ---
        self.create_service(Trigger, "~/query", self._handle_query)
        self.create_service(Trigger, "~/get_prompt", self._handle_get_prompt)
        self.create_service(Trigger, "~/get_pddl_problem", self._handle_get_pddl)
        self.create_service(Trigger, "~/get_summary", self._handle_get_summary)

        # --- 操作系: Topic で JSON を受け取り、レスポンスを Topic で返す ---
        self.create_subscription(
            String, "~/add_node_request", self._handle_add_node, 10
        )
        self.create_subscription(
            String, "~/remove_node_request", self._handle_remove_node, 10
        )
        self.create_subscription(
            String, "~/add_edge_request", self._handle_add_edge, 10
        )
        self.create_subscription(
            String, "~/remove_edge_request", self._handle_remove_edge, 10
        )

        # レスポンス用パブリッシャー
        self._response_pub = self.create_publisher(
            String, "~/operation_response", 10
        )

        self.get_logger().info("KnowledgeGraphNode is ready.")

    # ==================================================================
    # サービスハンドラ
    # ==================================================================

    def _handle_query(
        self, request: Trigger.Request, response: Trigger.Response
    ) -> Trigger.Response:
        """グラフ全体を JSON で返す。"""
        response.success = True
        response.message = json.dumps(
            self.graph.to_dict(), ensure_ascii=False, indent=2
        )
        return response

    def _handle_get_prompt(
        self, request: Trigger.Request, response: Trigger.Response
    ) -> Trigger.Response:
        """LLM 向けプロンプト文字列を返す。"""
        response.success = True
        response.message = PromptSerializer.serialize_full(self.graph)
        return response

    def _handle_get_pddl(
        self, request: Trigger.Request, response: Trigger.Response
    ) -> Trigger.Response:
        """PDDL 問題定義 (Problem) 文字列を返す。"""
        try:
            response.message = PddlSerializer.serialize_problem(self.graph)
            response.success = True
        except ValueError as error:
            response.success = False
            response.message = str(error)
        return response

    def _handle_get_summary(
        self, request: Trigger.Request, response: Trigger.Response
    ) -> Trigger.Response:
        """グラフの概要を返す。"""
        response.success = True
        response.message = self.graph.summary()
        return response

    # ==================================================================
    # トピックハンドラ (操作系)
    # ==================================================================

    def _handle_add_node(self, msg: String) -> None:
        """
        ノード追加。

        JSON format: {"name": "kitchen", "type": "room", "properties": {...}}
        """
        try:
            data = json.loads(msg.data)
            if not isinstance(data, dict):
                raise ValueError("Request must be a JSON object")
            node = KGNode(
                name=data["name"],
                node_type=data["type"],
                properties=data.get("properties", {}),
            )
            success = self.graph.add_node(node)
            self._publish_response(success, f"add_node: {node.name}")
        except (ValueError, KeyError, TypeError) as e:
            self._publish_response(False, f"add_node error: {e}")

    def _handle_remove_node(self, msg: String) -> None:
        """
        ノード削除。

        JSON format: {"name": "kitchen"}
        """
        try:
            data = json.loads(msg.data)
            if not isinstance(data, dict):
                raise ValueError("Request must be a JSON object")
            success = self.graph.remove_node(data["name"])
            self._publish_response(success, f"remove_node: {data['name']}")
        except (ValueError, KeyError, TypeError) as e:
            self._publish_response(False, f"remove_node error: {e}")

    def _handle_add_edge(self, msg: String) -> None:
        """
        エッジ追加。

        JSON format:
            {"label": "connected_to", "source": "kitchen", "target": "entrance",
             "bidirectional": true, "properties": {...}}
        """
        try:
            data = json.loads(msg.data)
            if not isinstance(data, dict):
                raise ValueError("Request must be a JSON object")
            bidirectional = data.get("bidirectional", False)

            if bidirectional:
                success = self.graph.add_bidirectional_edge(
                    label=data["label"],
                    node_a=data["source"],
                    node_b=data["target"],
                    properties=data.get("properties"),
                )
            else:
                edge = KGEdge(
                    label=data["label"],
                    source=data["source"],
                    target=data["target"],
                    properties=data.get("properties", {}),
                )
                success = self.graph.add_edge(edge)

            self._publish_response(
                success,
                f"add_edge: {data['source']} --[{data['label']}]--> {data['target']}",
            )
        except (ValueError, KeyError, TypeError) as e:
            self._publish_response(False, f"add_edge error: {e}")

    def _handle_remove_edge(self, msg: String) -> None:
        """
        エッジ削除。

        JSON format: {"label": "connected_to", "source": "kitchen", "target": "entrance"}
        """
        try:
            data = json.loads(msg.data)
            if not isinstance(data, dict):
                raise ValueError("Request must be a JSON object")
            success = self.graph.remove_edge(
                label=data["label"],
                source=data["source"],
                target=data["target"],
            )
            self._publish_response(
                success,
                f"remove_edge: {data['source']} --[{data['label']}]--> {data['target']}",
            )
        except (ValueError, KeyError, TypeError) as e:
            self._publish_response(False, f"remove_edge error: {e}")

    # ==================================================================
    # ヘルパー
    # ==================================================================

    def _publish_response(self, success: bool, message: str) -> None:
        """操作結果をレスポンストピックにパブリッシュする。"""
        msg = String()
        msg.data = json.dumps(
            {"success": success, "message": message}, ensure_ascii=False
        )
        self._response_pub.publish(msg)
        if success:
            self.get_logger().info(message)
        else:
            self.get_logger().warning(message)


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = KnowledgeGraphNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
