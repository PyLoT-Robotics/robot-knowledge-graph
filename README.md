# Robot Knowledge Graph

English · [日本語](docs/README.ja.md)

A small Python library for managing rooms, objects, people, robots and their
relationships, with YAML/JSON, LLM-oriented text and PDDL problem exports.
The Python core requires neither ROS nor
an LLM service. The ROS package and Python import name remain
`pylot_knowledge_graph` for compatibility.

## Install and use without ROS

Requires Python 3.10+. Run these commands from the repository root.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
python -m pytest -q
python -m pylot_knowledge_graph config/sample_environment.yaml --format summary
python -m pylot_knowledge_graph config/sample_environment.yaml --format prompt --focus kitchen
python -m pylot_knowledge_graph config/sample_environment.yaml --format pddl --output problem.pddl
```

`robot-knowledge-graph` provides the same CLI. With a colcon installation, invoke
it as `ros2 run pylot_knowledge_graph robot-knowledge-graph`.

```python
from pylot_knowledge_graph.graph import KnowledgeGraph, KGNode, KGEdge
from pylot_knowledge_graph.prompt_serializer import PromptSerializer

world = KnowledgeGraph()
world.add_node(KGNode('robot', 'robot'))
world.add_node(KGNode('kitchen', 'room'))
world.add_edge(KGEdge('robot_at', 'robot', 'kitchen'))
print(PromptSerializer.serialize_full(world))
```

The library supports CRUD operations, queries by type or relationship, neighbor
queries, bidirectional edges, removal of incident edges when deleting a node,
and YAML loading/saving. Duplicate nodes in YAML documents are rejected.
Register nodes before adding edges between them.

## PDDL scope

`config/domain.pddl` is the original implementation's sample domain. PDDL export
generates a problem definition; it does not search for plans, execute them or
validate semantic compatibility with a domain. Supply a matching domain yourself.
The exporter checks name/type/predicate symbols, case-insensitive node-name
collisions and inconsistent predicate arities. Self-loops become unary predicates;
other edges become binary predicates. Edges marked `is_goal: true` become goals
rather than initial facts.

Numeric functions, arbitrary predicate arities and temporal constraints are not
supported. Expressions supplied through `--goal` must already be valid PDDL.
Generating LLM-oriented text does not call an LLM.

## Optional ROS 2 adapter

The package builds on ROS 2 Jazzy. Place the repository in a regular ROS workspace's
`src` directory. The adapter requires `rclpy`, `std_msgs`, `std_srvs`, PyYAML and launch.

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select pylot_knowledge_graph
source install/setup.bash
ros2 launch pylot_knowledge_graph knowledge_graph.launch.py
ros2 service call /knowledge_graph_node/query std_srvs/srv/Trigger '{}'
```

Read services: `~/query`, `~/get_prompt`, `~/get_pddl_problem`, `~/get_summary`.
Mutations arrive as JSON in `std_msgs/String` on `~/add_node_request`,
`~/remove_node_request`, `~/add_edge_request` and `~/remove_edge_request`.
Responses are published on `~/operation_response`. This retains the original
node's interface; it has not been migrated to services with request IDs.
Persist changes explicitly with Python's `GraphLoader.save_to_yaml`.

## License and provenance

The original package's MIT license is retained. See [LICENSE](LICENSE) and
[PROVENANCE.md](PROVENANCE.md). Tests and independent pip installation have been
validated without robot hardware or external services.
