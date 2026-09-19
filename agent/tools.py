import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("DevOpsAutopilot.Tools")

class ResourceMetric(BaseModel):
    resource_id: str
    resource_type: str  # 'pod', 'instance', 'deployment'
    namespace: Optional[str] = "default"
    parent_workload: Optional[str] = None
    workload_type: Optional[str] = "deployment"
    current_cpu_request: float = 1.0
    current_mem_request: float = 1024.0  # MB
    avg_cpu_usage: float = 0.05
    avg_mem_usage: float = 100.0         # MB
    network_rx_kbps: Optional[float] = 0.0
    network_tx_kbps: Optional[float] = 0.0
    replicas: Optional[int] = 1
    cost_per_hour: Optional[float] = 1.50
    has_traffic: Optional[bool] = False
    labels: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, Any]] = None
    waste_score: Optional[float] = 0.0

class WhatIfSimulation(BaseModel):
    predicted_util_pct: float
    risk_score: str  # 'low' | 'medium' | 'high'
    risk_reason: str

class OptimizationProposal(BaseModel):
    resource_id: str
    resource_type: str
    namespace: str
    parent_workload: Optional[str] = None
    issue_type: str  # 'idle' | 'overprovisioned'
    utilization_pct: float
    waste_score: float
    proposed_action: Dict[str, Any]
    estimated_savings_inr_month: float
    what_if: Optional[WhatIfSimulation] = None
    safety_decision: Optional[str] = "auto_approve"  # 'auto_approve' | 'require_approval' | 'reject'
    safety_reason: Optional[str] = None
    approved_by: Optional[str] = "system"

def calculate_waste_score(cpu_util: float, mem_util: float, network_kbps: float) -> float:
    """
    Computes a normalized waste score (0 to 100).
    A score of 100 indicates completely wasted, unused capacity.
    """
    # CPU waste weight: 60%, Memory waste weight: 30%, Network idle weight: 10%
    cpu_waste = max(0.0, 1.0 - cpu_util)
    mem_waste = max(0.0, 1.0 - mem_util)
    net_idle = 1.0 if network_kbps < 5.0 else max(0.0, 1.0 - (network_kbps / 100.0))
    
    score = (cpu_waste * 60.0) + (mem_waste * 30.0) + (net_idle * 10.0)
    return round(min(100.0, max(0.0, score)), 1)
