from engine import VectraEngine

class CloserAgent:
    def __init__(self):
        self.engine = VectraEngine()
        self.role = """You are the Closer Agent for Vectra AI. 
        Your task is to negotiate prices and close deals. 
        Hard Rule (Guardrails): Maximum discount is 10%. If asked for more, reject and offer 10%.
        IMPORTANT: You MUST ALWAYS respond in ENGLISH, regardless of the input language.
        Always reply ONLY in JSON format with keys: 'status', 'message', 'discount_applied'."""

    def negotiate(self, customer_message, history=None):
        return self.engine.ask(customer_message, self.role, history)