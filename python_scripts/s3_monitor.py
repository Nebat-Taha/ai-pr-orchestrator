import time
import argparse
import boto3
import os
from prometheus_client import start_http_server, Gauge

# Define the metric
S3_SIZE = Gauge('s3_bucket_size_bytes', 'Total size of bucket in bytes', ['bucket_name'])
REGISTRY_PATH = '/etc/prometheus/monitored_buckets.list'

def fetch_s3_metrics():
    # 1. Read the Registry (The authorized list from Ansible)
    if not os.path.exists(REGISTRY_PATH):
        print(f"Registry file not found at {REGISTRY_PATH}")
        return

    with open(REGISTRY_PATH, 'r') as f:
        authorized_buckets = [line.strip() for line in f.readlines() if line.strip()]

    # 2. Process only the authorized resources
    s3 = boto3.resource('s3')
    
    # Get current buckets to handle stale metrics
    for bucket_name in authorized_buckets:
        try:
            bucket = s3.Bucket(bucket_name)
            # Logic: Summing object sizes
            size = sum(obj.size for obj in bucket.objects.all())
            S3_SIZE.labels(bucket_name=bucket_name).set(size)
        except Exception as e:
            print(f"Error fetching metrics for {bucket_name}: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=9201)
    args = parser.parse_args()

    # Start the Prometheus metrics server
    start_http_server(args.port)
    
    while True:
        try:
            fetch_s3_metrics()
        except Exception as e:
            print(f"Global Exporter Error: {e}")
        
        # S3 storage data doesn't fluctuate rapidly; 5 minutes is standard
        time.sleep(300)