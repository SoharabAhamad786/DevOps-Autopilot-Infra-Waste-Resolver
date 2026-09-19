import os
from typing import List

class Settings:
    # App & Server
    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
    PORT: int = int(os.getenv("PORT", "5000"))
    SECRET_KEY: str = os.getenv("SECRET_KEY", "devops-autopilot-secret-key-2026")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///devops_autopilot.db")

    # LLM Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")  # openai | mock

    # Pricing Parameters (INR)
    PRICE_PER_CORE_MONTH_INR: float = float(os.getenv("PRICE_PER_CORE_MONTH_INR", "800.0"))
    PRICE_PER_GB_MEM_MONTH_INR: float = float(os.getenv("PRICE_PER_GB_MEM_MONTH_INR", "250.0"))
    DEFAULT_POD_COST_MONTH_INR: float = float(os.getenv("DEFAULT_POD_COST_MONTH_INR", "1200.0"))

    # Multi-Agent Safety & Governance Policies
    DRY_RUN_DEFAULT: bool = os.getenv("DRY_RUN_DEFAULT", "true").lower() in ("true", "1", "yes")
    ALLOWED_NAMESPACES: List[str] = [
        ns.strip() for ns in os.getenv("ALLOWED_NAMESPACES", "staging,dev,demo").split(",") if ns.strip()
    ]
    MAX_ACTIONS_PER_RUN: int = int(os.getenv("MAX_ACTIONS_PER_RUN", "10"))
    MAX_REPLICA_REDUCTION_PCT: float = float(os.getenv("MAX_REPLICA_REDUCTION_PCT", "0.50"))
    PREVENT_PROD_EXECUTION: bool = os.getenv("PREVENT_PROD_EXECUTION", "true").lower() in ("true", "1", "yes")
    
    # Change Windows (e.g. Prod changes allowed only in 02:00-04:00 IST)
    CHANGE_WINDOW_START_HOUR: int = int(os.getenv("CHANGE_WINDOW_START_HOUR", "2"))
    CHANGE_WINDOW_END_HOUR: int = int(os.getenv("CHANGE_WINDOW_END_HOUR", "4"))
    
    # SLO & What-If Thresholds
    SLO_MAX_CPU_UTIL_PCT: float = float(os.getenv("SLO_MAX_CPU_UTIL_PCT", "80.0"))
    MIN_REPLICAS_TRAFFIC: int = int(os.getenv("MIN_REPLICAS_TRAFFIC", "2"))

    # Integrations
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
    SLACK_SIGNING_SECRET: str = os.getenv("SLACK_SIGNING_SECRET", "mock-signing-secret")
    USE_MOCK_METRICS: bool = os.getenv("USE_MOCK_METRICS", "true").lower() in ("true", "1", "yes")
    MOCK_METRICS_PATH: str = os.getenv("MOCK_METRICS_PATH", os.path.join(os.path.dirname(__file__), "integrations", "sample_metrics.json"))
    KUBECONFIG_PATH: str = os.getenv("KUBECONFIG_PATH", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "ap-south-1")

settings = Settings()
