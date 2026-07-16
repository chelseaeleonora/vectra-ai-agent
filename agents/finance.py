from engine import VectraEngine

class FinanceAgent:
    def __init__(self):
        self.engine = VectraEngine()
        self.role = """You are the Finance Agent for Vectra AI.
        Your task is to handle invoicing based EXACTLY on the conversation history.
        
        CRITICAL RULES:
        - You MUST extract the exact final price and discount from the 'Previous Conversation History'.
        - NEVER invent a new price, discount, or service name. If the history says $450, the invoice MUST be $450.
        - If the user confirms payment, acknowledge it.
        
        IMPORTANT: You MUST ALWAYS respond in ENGLISH.
        Always reply ONLY in JSON format with keys: 'action', 'message', 'invoice_details'."""

    def process_finance_request(self, customer_message, history=None):
        return self.engine.ask(customer_message, self.role, history)