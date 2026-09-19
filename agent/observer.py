import logging
from typing import List, Dict, Any
from config import settings
from integrations.k8s_client import K8sClient
from integrations.aws_client import AWSClient
from agent.tools import ResourceMetric, calculate_waste_score

logger = logging.getLogger("DevOpsAutopilot.ObserverAgent")

class ObserverAgent:
    """
    Role: Observer Agent
    Continuously discovers cluster workloads, measures multi-dimensional telemetry
    (CPU, memory, network I/O), computes waste scores, and pre-filters candidate resources.
    """
    def __init__(self):
        self.k8s_client = K8sClient()
        self.aws_client = AWSClient()

    def observe_cluster(self, scope: str = "all") -> List[ResourceMetric]:
        logger.info(f"[ObserverAgent] Initiating cluster metric ingestion. Scope filter='{scope}'.")
        raw_items: List[Dict[str, Any]] = []

        # 1. Fetch Kubernetes workloads
        k8s_metrics = self.k8s_client.get_pod_metrics()
        raw_items.extend(k8s_metrics)

        # 2. Fetch AWS EC2 instances
        ec2_metrics = self.aws_client.get_ec2_metrics()
        raw_items.extend(ec2_metrics)

        observed_metrics: List[ResourceMetric] = []

        for item in raw_items:
            ns = item.get("namespace", "default")
            res_id = item.get("resource_id", "unknown")
            res_type = item.get("resource_type", "pod")
            
            # Scope filtering
            if scope != "all" and ns.lower() != scope.lower():
                continue

            cpu_req = max(float(item.get("current_cpu_request", 1.0)), 0.001)
            cpu_usage = float(item.get("avg_cpu_usage", 0.0))
            mem_req = max(float(item.get("current_mem_request", 1024.0)), 1.0)
            mem_usage = float(item.get("avg_mem_usage", 0.0))
            net_rx = float(item.get("network_rx_kbps", 0.0))
            net_tx = float(item.get("network_tx_kbps", 0.0))
            total_net = net_rx + net_tx

            cpu_util = cpu_usage / cpu_req
            mem_util = mem_usage / mem_req
            waste = calculate_waste_score(cpu_util, mem_util, total_net)

            metric = ResourceMetric(
                resource_id=res_id,
                resource_type=res_type,
                namespace=ns,
                parent_workload=item.get("parent_workload"),
                workload_type=item.get("workload_type", "deployment"),
                current_cpu_request=cpu_req,
                current_mem_request=mem_req,
                avg_cpu_usage=cpu_usage,
                avg_mem_usage=mem_usage,
                network_rx_kbps=net_rx,
                network_tx_kbps=net_tx,
                replicas=int(item.get("replicas", 1)),
                cost_per_hour=float(item.get("cost_per_hour", 0.0)),
                has_traffic=bool(item.get("has_traffic", False)),
                labels=item.get("labels", {}),
                tags=item.get("tags", {}),
                waste_score=waste
            )
            observed_metrics.append(metric)

        logger.info(f"[ObserverAgent] Normalized {len(observed_metrics)} infrastructure metrics. Pre-filtering complete.")
        return observed_metrics
