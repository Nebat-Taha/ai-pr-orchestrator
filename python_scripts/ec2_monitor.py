import time
import argparse
import boto3
from prometheus_client import start_http_server, Gauge

EC2_STATUS = Gauge('ec2_instance_state', 'State of instance (1=running, 0=other)', ['instance_id', 'name'])

def fetch_ec2_metrics():
    ec2 = boto3.resource('ec2', region_name='us-east-1')
    instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running', 'stopped']}])
    
    for inst in instances:
        name_tag = next((tag['Value'] for tag in inst.tags if tag['Key'] == 'Name'), inst.id)
        state_val = 1 if inst.state['Name'] == 'running' else 0
        EC2_STATUS.labels(instance_id=inst.id, name=name_tag).set(state_val)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=9202)
    args = parser.parse_args()

    start_http_server(args.port)
    while True:
        try:
            fetch_ec2_metrics()
        except Exception as e:
            print(f"EC2 Error: {e}")
        time.sleep(60)