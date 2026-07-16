from agents.manager import ManagerAgent
from agents.sdr import SDRAgent
from agents.closer import CloserAgent
from agents.finance import FinanceAgent

class VectraSystem:
    def __init__(self):
        self.manager = ManagerAgent()
        self.sdr = SDRAgent()
        self.closer = CloserAgent()
        self.finance = FinanceAgent()
        self.history = [] # Ini adalah memori sistem

    def process_message(self, user_message):
        # 1. Simpan pesan user ke memori
        self.history.append({"role": "user", "parts": user_message})

        # 2. Manager merutekan pesan (dengan membawa memori)
        routing = self.manager.route_message(user_message, self.history)
        target = routing.get('target_agent', 'SDR')
        
        print(f"-> [Manager] Routing ke: {target}")

        # 3. Agen yang ditunjuk memproses pesan (dengan membawa memori)
        if target == 'SDR':
            response = self.sdr.qualify_lead(user_message, self.history)
        elif target == 'CLOSER':
            response = self.closer.negotiate(user_message, self.history)
        elif target == 'FINANCE':
            response = self.finance.process_finance_request(user_message, self.history)
        else:
            response = {"error": "Unknown agent"}

        # 4. Simpan respon agen ke memori
        self.history.append({"role": "model", "parts": str(response)})
        
        return response