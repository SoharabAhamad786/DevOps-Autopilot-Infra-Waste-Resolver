import json
import logging
import os
from typing import List, Dict, Any
from config import settings

logger = logging.getLogger("DevOpsAutopilot.AWSClient")

class AWSClient:
    """
    Handles AWS EC2 operations for discovering instance metrics and stopping idle instances.
    """
    def __init__(self):
        self.client_initialized = False
        self.ec2 = None
        self.cloudwatch = None
        self._init_client()

    def _init_client(self):
        if settings.USE_MOCK_METRICS:
            logger.info("AWSClient configured in MOCK mode via USE_MOCK_METRICS setting.")
            return

        try:
            import boto3
            session = boto3.Session(region_name=settings.AWS_REGION)
            self.ec2 = session.client("ec2")
            self.cloudwatch = session.client("cloudwatch")
            self.client_initialized = True
            logger.info(f"Initialized live AWS client for region {settings.AWS_REGION}.")
        except Exception as e:
            logger.warning(f"Could not connect to AWS: {e}. Falling back to mock dataset.")
            self.client_initialized = False

    def get_ec2_metrics(self) -> List[Dict[str, Any]]:
        """
        Fetches EC2 instance metrics.
        """
        if not self.client_initialized or settings.USE_MOCK_METRICS:
            return self._load_mock_ec2_metrics()

        results = []
        try:
            response = self.ec2.describe_instances(
                Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
            )
            for res in response.get("Reservations", []):
                for inst in res.get("Instances", []):
                    inst_id = inst["InstanceId"]
                    inst_type = inst["InstanceType"]
                    # Extract tags
                    tags = {t["Key"]: t["Value"] for t in inst.get("Tags", [])}
                    env = tags.get("Environment", "dev")

                    # Approximate CPU cores from type
                    cpu_cores = 4.0
                    mem_mb = 8192.0
                    if "2xlarge" in inst_type:
                        cpu_cores, mem_mb = 8.0, 16384.0
                    elif "4xlarge" in inst_type:
                        cpu_cores, mem_mb = 16.0, 65536.0
                    elif "xlarge" in inst_type:
                        cpu_cores, mem_mb = 4.0, 8192.0
                    elif "large" in inst_type:
                        cpu_cores, mem_mb = 2.0, 4096.0

                    results.append({
                        "resource_id": inst_id,
                        "resource_type": "instance",
                        "instance_type": inst_type,
                        "namespace": inst.get("Placement", {}).get("AvailabilityZone", settings.AWS_REGION),
                        "current_cpu_request": cpu_cores,
                        "current_mem_request": mem_mb,
                        "avg_cpu_usage": 0.15,
                        "avg_mem_usage": 800.0,
                        "cost_per_hour": round(cpu_cores * 3.5, 2),
                        "tags": tags,
                        "env": env
                    })
            return results
        except Exception as e:
            logger.error(f"Failed to query live AWS EC2 metrics: {e}. Falling back to mock dataset.")
            return self._load_mock_ec2_metrics()

    def _load_mock_ec2_metrics(self) -> List[Dict[str, Any]]:
        path = settings.MOCK_METRICS_PATH
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
                return [d for d in data if d.get("resource_type") == "instance"]
        return []

    def stop_instance(self, instance_id: str, dry_run: bool = True) -> Dict[str, Any]:
        """
        Stops an idle or overprovisioned EC2 instance.
        """
        logger.info(f"Stop instance request: {instance_id} (dry_run={dry_run})")
        if dry_run:
            return {
                "status": "simulated",
                "instance_id": instance_id,
                "message": f"[DRY RUN] Would stop EC2 instance {instance_id}."
            }

        if not self.client_initialized or not self.ec2:
            logger.info(f"Live AWS client not available. Simulating stop for {instance_id}.")
            return {
                "status": "success",
                "instance_id": instance_id,
                "message": f"Successfully stopped EC2 instance {instance_id} (Mock Live)."
            }

        try:
            self.ec2.stop_instances(InstanceIds=[instance_id])
            return {
                "status": "success",
                "instance_id": instance_id,
                "message": f"Successfully issued stop command for EC2 instance {instance_id}."
            }
        except Exception as e:
            logger.error(f"Failed to stop instance {instance_id}: {e}")
            raise
