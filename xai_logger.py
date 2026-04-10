class ExplainableAILogger:
    def __init__(self):
        self.logs = []
        self.total_tokens = 0

    def log_reasoning(self, agent_name: str, context: str, reasoning: str, action: str):
        log_entry = {
            "agent": agent_name,
            "context": context,
            "reasoning": reasoning,
            "action": action
        }
        self.logs.append(log_entry)
        print(f"\n======================================")
        print(f"[{agent_name} XAI LOG]")
        if context:
            print(f" - Context: {context}")
        print(f" - Reasoning: {reasoning}")
        print(f" - Action Intent: {action}")
        print(f"======================================\n")

    def log_metrics(self, token_usage: int, latency_ms: float):
        self.total_tokens += token_usage
        print(f"[METRICS] Tokens Used: {token_usage} (Total: {self.total_tokens}) | Latency: {latency_ms:.2f}ms")

xai_logger = ExplainableAILogger()
