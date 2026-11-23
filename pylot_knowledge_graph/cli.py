"""Inspect and export robot environment graphs without ROS or an LLM service."""
import argparse
import json
from pathlib import Path
import sys
import yaml
from .graph_loader import GraphLoader
from .pddl_serializer import PddlSerializer
from .prompt_serializer import PromptSerializer


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('graph', type=Path, help='Environment YAML file')
    parser.add_argument('--format', choices=['json', 'prompt', 'pddl', 'summary'], default='summary')
    parser.add_argument('--focus', help='Only export prompt context around this node')
    parser.add_argument('--depth', type=int, default=2)
    parser.add_argument('--goal', action='append', default=[], help='Additional PDDL goal expression')
    parser.add_argument('--problem', default='robot_problem')
    parser.add_argument('--domain', default='pylot_domain')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    if args.depth < 0:
        parser.error('--depth must be nonnegative')
    try:
        graph = GraphLoader.load_from_yaml(args.graph)
        if args.format == 'json':
            result = json.dumps(graph.to_dict(), indent=2, ensure_ascii=False, allow_nan=False)
        elif args.format == 'prompt':
            if args.focus and not graph.has_node(args.focus):
                raise ValueError('Unknown focus node: ' + args.focus)
            result = (PromptSerializer.serialize_context(graph, args.focus, args.depth) if args.focus
                      else PromptSerializer.serialize_full(graph))
        elif args.format == 'pddl':
            result = PddlSerializer.serialize_problem(graph, args.problem, args.domain, args.goal)
        else:
            result = graph.summary()
        if args.output:
            args.output.write_text(result + '\n', encoding='utf-8')
        else:
            print(result)
    except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError) as error:
        print(f'robot-knowledge-graph: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
