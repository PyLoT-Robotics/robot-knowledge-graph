from glob import glob
from setuptools import setup, find_packages
setup(name='pylot_knowledge_graph', version='0.1.0', description='Robot environment knowledge graphs with YAML, text and PDDL export',
      packages=find_packages(exclude=['test']), python_requires='>=3.10',
      install_requires=['PyYAML>=6'], extras_require={'test':['pytest']},
      license='MIT', maintainer='PyLoT Robotics', maintainer_email='163533636+PyLoT-Robotics@users.noreply.github.com',
      data_files=[('share/ament_index/resource_index/packages',['resource/pylot_knowledge_graph']),('share/pylot_knowledge_graph',['package.xml']),('share/pylot_knowledge_graph/config',glob('config/*')),('share/pylot_knowledge_graph/launch',glob('launch/*.py'))],
      entry_points={'console_scripts':['robot-knowledge-graph = pylot_knowledge_graph.cli:main', 'knowledge_graph_node = pylot_knowledge_graph.knowledge_graph_node:main']})
