import json
import logging
from typing import List, Dict, Any, Optional
from config import settings

logger = logging.getLogger("DevOpsAutopilot.LLMClient")

# OpenAI Function Calling Tool Schemas
AGENT_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_cluster_metrics",
            "description": "Fetch current CPU, memory, and replica metrics across Kubernetes clusters and AWS instances.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scope": {
                        "type": "string",
                        "description": "Namespace or environment scope to filter metrics (e.g. 'all', 'staging', 'dev', 'demo').",
                        "default": "all"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "propose_optimizations",
            "description": "Analyze raw resource metrics, detect idle/overprovisioned resources, and generate rightsizing/shutdown proposals with estimated monthly INR savings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metrics": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of resource metric objects returned from get_cluster_metrics."
                    }
                },
                "required": ["metrics"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_action",
            "description": "Safely execute or dry-run the optimization action plan on Kubernetes and AWS instances.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action_plan": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of optimization proposal objects to execute."
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, simulates actions without modifying cluster state. If false, executes live scaling.",
                        "default": True
                    }
                },
                "required": ["action_plan"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "post_slack_summary",
            "description": "Post the executive optimization summary report to Slack via webhook.",
            "parameters": {
                "type": "object",
                "properties": {
                    "result": {
                        "type": "object",
                        "description": "Execution result object containing savings, counts, and action details."
                    }
                },
                "required": ["result"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are DevOps Autopilot, an expert Autonomous SRE and Cloud Cost Optimization Agent.
Your objective is to proactively eliminate cloud infrastructure waste while maintaining 100% production safety.

You must follow an autonomous multi-step tool-use loop:
1. Call `get_cluster_metrics` to inspect cluster resources.
2. Call `propose_optimizations` to reason about idle (<5% CPU) and overprovisioned (<30% CPU) resources and calculate monthly INR savings.
3. Call `execute_action` with the proposals and appropriate dry_run flag, respecting guardrails (never modify production, observe max reduction limits).
4. Call `post_slack_summary` to broadcast results to the team.
5. Provide a crisp executive summary of findings and INR savings achieved.
"""

class LLMClient:
    """
    LLM Client supporting native OpenAI Function Calling / Tool Use with graceful
    autonomous fallback for zero-dependency offline hackathon demos.
    """
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.client = None
        self._init_openai()

    def _init_openai(self):
        if self.api_key and self.api_key != "your_openai_api_key_here":
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                logger.info(f"OpenAI client initialized with model '{self.model}'.")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}. Fallback enabled.")
                self.client = None
        else:
            logger.info("No valid OPENAI_API_KEY provided. Using autonomous tool orchestrator mode.")

    def run_agentic_turn(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sends conversational messages and tools to the LLM.
        Returns the assistant message including tool_calls if generated.
        """
        if not self.client:
            return self._heuristic_agent_step(messages)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=AGENT_TOOLS_SCHEMA,
                tool_choice="auto",
                temperature=0.1
            )
            choice = response.choices[0].message
            return {
                "role": "assistant",
                "content": choice.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in (choice.tool_calls or [])
                ]
            }
        except Exception as e:
            logger.warning(f"LLM API call failed ({e}). Reverting to internal agent planner.")
            return self._heuristic_agent_step(messages)

    def _heuristic_agent_step(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Deterministic autonomous planner used for ultra-reliable offline demos
        or when API keys are absent. Guides through the 4 tools sequentially.
        """
        # Count tool responses present in message history
        tool_results = [m for m in messages if m.get("role") == "tool"]

        if len(tool_results) == 0:
            # Step 1: Call get_cluster_metrics
            return {
                "role": "assistant",
                "content": "Analyzing cluster infrastructure metrics to identify idle and oversized workloads...",
                "tool_calls": [
                    {
                        "id": "call_metrics_01",
                        "type": "function",
                        "function": {
                            "name": "get_cluster_metrics",
                            "arguments": json.dumps({"scope": "all"})
                        }
                    }
                ]
            }
        elif len(tool_results) == 1:
            # Step 2: Call propose_optimizations with metrics from step 1
            last_content = tool_results[0].get("content", "[]")
            metrics_data = json.loads(last_content) if isinstance(last_content, str) else last_content
            return {
                "role": "assistant",
                "content": f"Received {len(metrics_data)} resource metrics. Reasoning over utilization patterns to detect waste...",
                "tool_calls": [
                    {
                        "id": "call_propose_02",
                        "type": "function",
                        "function": {
                            "name": "propose_optimizations",
                            "arguments": json.dumps({"metrics": metrics_data})
                        }
                    }
                ]
            }
        elif len(tool_results) == 2:
            # Step 3: Call execute_action with proposals from step 2
            proposals_data = json.loads(tool_results[1].get("content", "[]"))
            # Check user mode from original request
            user_msg = messages[1].get("content", "") if len(messages) > 1 else ""
            dry_run = "live" not in user_msg.lower()

            return {
                "role": "assistant",
                "content": f"Formulated {len(proposals_data)} concrete optimization actions. Enforcing guardrails and executing in {'DRY RUN' if dry_run else 'LIVE'} mode...",
                "tool_calls": [
                    {
                        "id": "call_execute_03",
                        "type": "function",
                        "function": {
                            "name": "execute_action",
                            "arguments": json.dumps({"action_plan": proposals_data, "dry_run": dry_run})
                        }
                    }
                ]
            }
        elif len(tool_results) == 3:
            # Step 4: Call post_slack_summary
            exec_result = json.loads(tool_results[2].get("content", "{}"))
            return {
                "role": "assistant",
                "content": "Actions evaluated successfully. Broadcasting executive report to Slack...",
                "tool_calls": [
                    {
                        "id": "call_slack_04",
                        "type": "function",
                        "function": {
                            "name": "post_slack_summary",
                            "arguments": json.dumps({"result": exec_result})
                        }
                    }
                ]
            }
        else:
            # Conclude with summary text
            exec_result = json.loads(tool_results[2].get("content", "{}"))
            savings = exec_result.get("total_savings_inr_month", 0.0)
            executed = exec_result.get("actions_executed", 0)
            return {
                "role": "assistant",
                "content": f"Optimization cycle completed successfully. Applied {executed} actions with estimated recurring savings of ₹{savings:,.2f} per month.",
                "tool_calls": []
            }
