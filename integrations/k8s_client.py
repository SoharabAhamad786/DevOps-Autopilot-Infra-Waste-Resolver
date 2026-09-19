import json
import logging
import os
from typing import List, Dict, Any, Optional
from config import settings

logger = logging.getLogger("DevOpsAutopilot.K8sClient")

class K8sClient:
    """
    Handles Kubernetes API operations for discovering resource utilization
    and scaling deployments safely.
    """
    def __init__(self):
        self.client_initialized = False
        self.apps_v1 = None
        self.core_v1 = None
        self.custom_api = None
        self._init_client()

    def _init_client(self):
        if settings.USE_MOCK_METRICS:
            logger.info("K8sClient configured in MOCK mode via USE_MOCK_METRICS setting.")
            return

        try:
            from kubernetes import client, config
            if settings.KUBECONFIG_PATH and os.path.exists(os.path.expanduser(settings.KUBECONFIG_PATH)):
                config.load_kube_config(config_file=os.path.expanduser(settings.KUBECONFIG_PATH))
                logger.info(f"Loaded kubeconfig from {settings.KUBECONFIG_PATH}")
            else:
                try:
                    config.load_incluster_config()
                    logger.info("Loaded in-cluster Kubernetes config.")
                except Exception:
                    config.load_kube_config()
                    logger.info("Loaded default ~/.kube/config.")

            self.apps_v1 = client.AppsV1Api()
            self.core_v1 = client.CoreV1Api()
            self.custom_api = client.CustomObjectsApi()
            self.client_initialized = True
        except Exception as e:
            logger.warning(f"Could not connect to live Kubernetes cluster: {e}. Falling back to mock dataset.")
            self.client_initialized = False

    def get_pod_metrics(self) -> List[Dict[str, Any]]:
        """
        Fetches pod resource requests and usage. Returns list of resource metrics.
        """
        if not self.client_initialized or settings.USE_MOCK_METRICS:
            return self._load_mock_k8s_metrics()

        results = []
        try:
            # 1. Fetch Pod metrics from Metrics Server (metrics.k8s.io)
            pod_metrics_data = self.custom_api.list_cluster_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                plural="pods"
            )
            usage_map = {}
            for item in pod_metrics_data.get("items", []):
                p_name = item["metadata"]["name"]
                ns = item["metadata"]["namespace"]
                total_cpu_nano = 0
                total_mem_kb = 0
                for c in item.get("containers", []):
                    cpu_str = c["usage"]["cpu"]
                    mem_str = c["usage"]["memory"]
                    # Parse cpu (e.g. 15m or 1000000n)
                    if cpu_str.endswith("n"):
                        total_cpu_nano += int(cpu_str[:-1])
                    elif cpu_str.endswith("m"):
                        total_cpu_nano += int(cpu_str[:-1]) * 1000000
                    else:
                        total_cpu_nano += int(float(cpu_str) * 1e9)

                    # Parse mem (e.g. 120Mi, 100Ki)
                    if mem_str.endswith("Ki"):
                        total_mem_kb += int(mem_str[:-2])
                    elif mem_str.endswith("Mi"):
                        total_mem_kb += int(mem_str[:-2]) * 1024
                    elif mem_str.endswith("Gi"):
                        total_mem_kb += int(mem_str[:-2]) * 1024 * 1024
                    else:
                        total_mem_kb += int(int(mem_str) / 1024)

                usage_map[(ns, p_name)] = {
                    "cpu_cores": total_cpu_nano / 1e9,
                    "mem_mb": total_mem_kb / 1024
                }

            # 2. Fetch Pod specs to read resource requests
            pods = self.core_v1.list_pod_for_all_namespaces()
            for pod in pods.items:
                ns = pod.metadata.namespace
                p_name = pod.metadata.name
                owner_kind = "deployment"
                owner_name = p_name
                if pod.metadata.owner_references:
                    owner_name = pod.metadata.owner_references[0].name
                    owner_kind = pod.metadata.owner_references[0].kind.lower()

                total_req_cpu = 0.0
                total_req_mem = 0.0
                for c in pod.spec.containers:
                    if c.resources and c.resources.requests:
                        reqs = c.resources.requests
                        if "cpu" in reqs:
                            cpu_v = reqs["cpu"]
                            total_req_cpu += float(cpu_v[:-1])/1000 if cpu_v.endswith("m") else float(cpu_v)
                        if "memory" in reqs:
                            mem_v = reqs["memory"]
                            if mem_v.endswith("Mi"):
                                total_req_mem += float(mem_v[:-2])
                            elif mem_v.endswith("Gi"):
                                total_req_mem += float(mem_v[:-2]) * 1024
                            elif mem_v.endswith("Ki"):
                                total_req_mem += float(mem_v[:-2]) / 1024

                # Fallback defaults if requests not explicitly set
                total_req_cpu = max(total_req_cpu, 0.25)
                total_req_mem = max(total_req_mem, 256.0)

                usage = usage_map.get((ns, p_name), {"cpu_cores": 0.01, "mem_mb": 50.0})
                results.append({
                    "resource_id": p_name,
                    "resource_type": "pod",
                    "parent_workload": owner_name,
                    "workload_type": owner_kind,
                    "namespace": ns,
                    "current_cpu_request": total_req_cpu,
                    "current_mem_request": total_req_mem,
                    "avg_cpu_usage": usage["cpu_cores"],
                    "avg_mem_usage": usage["mem_mb"],
                    "cost_per_hour": round((total_req_cpu * (settings.PRICE_PER_CORE_MONTH_INR / 720.0)), 2),
                    "replicas": 1
                })
            return results
        except Exception as e:
            logger.error(f"Failed to query live K8s metrics: {e}. Falling back to mock dataset.")
            return self._load_mock_k8s_metrics()

    def _load_mock_k8s_metrics(self) -> List[Dict[str, Any]]:
        path = settings.MOCK_METRICS_PATH
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
                return [d for d in data if d.get("resource_type") == "pod"]
        return []

    def scale_deployment(self, namespace: str, deployment_name: str, target_replicas: int, dry_run: bool = True) -> Dict[str, Any]:
        """
        Scales a Kubernetes deployment to target_replicas.
        """
        logger.info(f"Scale deployment request: {namespace}/{deployment_name} -> {target_replicas} replicas (dry_run={dry_run})")
        if dry_run:
            return {
                "status": "simulated",
                "namespace": namespace,
                "deployment": deployment_name,
                "target_replicas": target_replicas,
                "message": f"[DRY RUN] Would scale {namespace}/{deployment_name} to {target_replicas} replicas."
            }

        if not self.client_initialized or not self.apps_v1:
            logger.info(f"Live K8s client not available. Simulating live scale for {deployment_name}.")
            return {
                "status": "success",
                "namespace": namespace,
                "deployment": deployment_name,
                "target_replicas": target_replicas,
                "message": f"Successfully scaled {namespace}/{deployment_name} to {target_replicas} replicas (Mock Live)."
            }

        try:
            body = {"spec": {"replicas": target_replicas}}
            self.apps_v1.patch_namespaced_deployment_scale(
                name=deployment_name,
                namespace=namespace,
                body=body
            )
            return {
                "status": "success",
                "namespace": namespace,
                "deployment": deployment_name,
                "target_replicas": target_replicas,
                "message": f"Successfully scaled {namespace}/{deployment_name} to {target_replicas} replicas."
            }
        except Exception as e:
            logger.error(f"Error scaling deployment {deployment_name} in {namespace}: {e}")
            raise
