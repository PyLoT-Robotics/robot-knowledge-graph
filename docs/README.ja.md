# Robot Knowledge Graph

[English](../README.md) · 日本語

部屋・物体・人物・ロボットと関係を管理し、YAML/JSON、LLM用テキスト、PDDL問題へ
変換する小さなPythonライブラリです。独立したOSSとして切り出しています。
PythonコアはROS・LLMサービスに依存しません。既存のROSパッケージ名
`pylot_knowledge_graph` とPython import名を保持しています。

## ROSなしでの利用

Python 3.10+。リポジトリのルートで実行します。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
python -m pytest -q
python -m pylot_knowledge_graph config/sample_environment.yaml --format summary
python -m pylot_knowledge_graph config/sample_environment.yaml --format prompt --focus kitchen
python -m pylot_knowledge_graph config/sample_environment.yaml --format pddl --output problem.pddl
```

`robot-knowledge-graph` も同じCLIです。ROSのcolconでインストールした場合は
`ros2 run pylot_knowledge_graph robot-knowledge-graph` から呼べます。

```python
from pylot_knowledge_graph.graph import KnowledgeGraph, KGNode, KGEdge
from pylot_knowledge_graph.prompt_serializer import PromptSerializer

world = KnowledgeGraph()
world.add_node(KGNode('robot', 'robot'))
world.add_node(KGNode('kitchen', 'room'))
world.add_edge(KGEdge('robot_at', 'robot', 'kitchen'))
print(PromptSerializer.serialize_full(world))
```

CRUD、種類・関係ごとの検索、隣接ノード検索、双方向エッジ、ノード削除時の関連エッジ削除、
YAML読み書きに対応します。YAML文書の重複ノードはエラーにします。
ノードを先に登録してからエッジを追加してください。

## PDDL出力の対応範囲

`config/domain.pddl` は元実装のサンプルドメインです。PDDL出力は問題生成であり、
計画探索・実行・ドメインとの意味的整合性検証は行いません。対応するドメインを
自分で用意してください。名前・型・述語の記号、名前の大文字小文字衝突、述語の
引数個数の混在を検査します。自己ループは1項述語、その他のエッジは2項述語として
出力し、`is_goal: true` のエッジは初期事実でなくゴールに使います。
数値関数・任意個数の引数・時間制約は扱いません。`--goal` で渡す式は呼び出し側で
正しいPDDLにしてください。LLM向けテキスト出力にLLM呼び出しは含まれません。

## ROS 2アダプタ

ROS 2 Jazzy上でビルドできます。ROSを使用する場合は通常のROSワークスペースのsrcに
このリポジトリを置いてください。`rclpy`、`std_msgs`、`std_srvs`、PyYAMLとlaunchが必要です。

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select pylot_knowledge_graph
source install/setup.bash
ros2 launch pylot_knowledge_graph knowledge_graph.launch.py
ros2 service call /knowledge_graph_node/query std_srvs/srv/Trigger '{}'
```

取得サービス: `~/query`, `~/get_prompt`, `~/get_pddl_problem`, `~/get_summary`。
更新入力は `std_msgs/String` のJSONトピック `~/add_node_request`, `~/remove_node_request`,
`~/add_edge_request`, `~/remove_edge_request`。結果は `~/operation_response` に返ります。
元ノードとの互換性を保持し、リクエストID付きサービスへの変更は行っていません。
永続化はPythonの `GraphLoader.save_to_yaml` で明示的に行います。

## ライセンスと出典

元パッケージのMIT表記を引き継いでいます。詳細は [LICENSE](../LICENSE) と
[PROVENANCE.md](../PROVENANCE.md)。実機接続や外部サービスを必要としないテストと、
独立したpipインストールを検証しています。
