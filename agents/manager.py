from engine import VectraEngine

class ManagerAgent:
    def __init__(self):
        self.engine = VectraEngine()
        self.role = """You are the Manager Agent (Orchestrator) for Vectra AI.
        Analyze the customer's message and route it to the correct specialized agent.
        Rules: General questions -> 'SDR', Price/Discount -> 'CLOSER', Invoice/Payment -> 'FINANCE'.
        IMPORTANT: Always respond in ENGLISH. Reply ONLY in JSON with keys: 'target_agent', 'reason'."""

    def route_message(self, customer_message, history=None):
        return self.engine.ask(customer_message, self.role, history)