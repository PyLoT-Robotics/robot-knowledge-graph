"""
knowledge_graph.launch.py

ナレッジグラフノードの起動ファイル。
config_file パラメータでグラフ初期状態の YAML を指定する。
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory("pylot_knowledge_graph")

    config_file_arg = DeclareLaunchArgument(
        "config_file",
        default_value=os.path.join(
            package_share, "config", "sample_environment.yaml"
        ),
        description="Path to the knowledge graph YAML config file",
    )

    knowledge_graph_node = Node(
        package="pylot_knowledge_graph",
        executable="knowledge_graph_node",
        name="knowledge_graph_node",
        parameters=[
            {"config_file": LaunchConfiguration("config_file")},
        ],
        output="screen",
    )

    return LaunchDescription(
        [
            config_file_arg,
            knowledge_graph_node,
        ]
    )
