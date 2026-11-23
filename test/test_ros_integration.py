"""Optional real DDS test. Synthetic knowledge only; no robot or LLM calls."""
import json
import os
import signal
import subprocess
import sys
import time
import pytest
rclpy=pytest.importorskip('rclpy')
from rclpy.context import Context
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import Trigger


def test_ros_mutations_exports_and_bad_request_recovery(tmp_path):
    source=tmp_path/'world.yaml';source.write_text('nodes: [{name: robot, type: robot}]\nedges: []\n')
    context=Context();rclpy.init(context=context,domain_id=95)
    helper=Node('knowledge_graph_test',context=context)
    executor=SingleThreadedExecutor(context=context);executor.add_node(helper)
    responses=[]
    helper.create_subscription(String,'/knowledge_graph_node/operation_response',lambda m:responses.append(json.loads(m.data)),10)
    publisher=helper.create_publisher(String,'/knowledge_graph_node/add_node_request',10)
    query=helper.create_client(Trigger,'/knowledge_graph_node/query')
    env=dict(os.environ,ROS_DOMAIN_ID='95')
    process=subprocess.Popen([sys.executable,'-m','pylot_knowledge_graph.knowledge_graph_node',
        '--ros-args','-p',f'config_file:={source}'],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)

    def wait(predicate,timeout=8):
        deadline=time.monotonic()+timeout
        while not predicate() and time.monotonic()<deadline:
            assert process.poll() is None,process.stdout.read().decode()
            executor.spin_once(timeout_sec=.02)
        assert predicate()

    def mutate(payload):
        responses.clear();publisher.publish(String(data=json.dumps(payload)))
        wait(lambda:bool(responses))
        return responses[-1]

    try:
        wait(lambda:query.service_is_ready() and publisher.get_subscription_count()>0)
        # A malformed JSON shape must not terminate the ROS executor.
        assert mutate([])['success'] is False
        assert mutate({'name':'kitchen','type':'room'})['success'] is True
        future=query.call_async(Trigger.Request());wait(future.done)
        assert future.result().success
        assert {n['name'] for n in json.loads(future.result().message)['nodes']}=={'robot','kitchen'}
    finally:
        try:os.killpg(process.pid,signal.SIGINT)
        except ProcessLookupError:pass
        try:process.wait(timeout=4)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=2)
        output=process.stdout.read().decode();process.stdout.close()
        executor.shutdown();helper.destroy_node();rclpy.shutdown(context=context)
    assert process.returncode==0,output
