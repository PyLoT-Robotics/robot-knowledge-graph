import json
import pytest
from pylot_knowledge_graph.cli import main
from pylot_knowledge_graph.graph import KnowledgeGraph, KGNode, KGEdge
from pylot_knowledge_graph.pddl_serializer import PddlSerializer


def test_export_cli_without_ros(tmp_path):
    source=tmp_path/'graph.yaml'
    source.write_text('nodes:\n  - {name: robot, type: robot}\n  - {name: kitchen, type: room}\nedges:\n  - {label: robot_at, source: robot, target: kitchen}\n')
    out=tmp_path/'graph.json'
    assert main([str(source),'--format','json','--output',str(out)])==0
    assert len(json.loads(out.read_text())['nodes'])==2
    assert main([str(source),'--format','pddl','--output',str(out)])==0
    assert '(robot_at robot kitchen)' in out.read_text()
    assert main([str(source),'--format','prompt','--focus','missing'])==2


@pytest.mark.parametrize('data',[[], {'nodes':'wrong'}, {'nodes':[{'name':'a','type':'room'},{'name':'a','type':'room'}]}])
def test_malformed_documents_fail(data):
    with pytest.raises(ValueError):KnowledgeGraph.from_dict(data)


def test_pddl_rejects_ambiguous_or_invalid_symbols():
    graph=KnowledgeGraph()
    graph.add_node(KGNode('a','room'));graph.add_node(KGNode('A','room'))
    with pytest.raises(ValueError):PddlSerializer.serialize_problem(graph)
    graph.remove_node('A');graph.add_node(KGNode('b','room'))
    graph.add_edge(KGEdge('at','a','a'));graph.add_edge(KGEdge('at','a','b'))
    with pytest.raises(ValueError):PddlSerializer.serialize_problem(graph)
    with pytest.raises(ValueError):PddlSerializer.serialize_problem(KnowledgeGraph(),problem_name='bad) (name')
