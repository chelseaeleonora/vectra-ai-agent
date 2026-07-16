import json
from google import genai
from config import GEMINI_API_KEY, MODEL_NAME

class VectraEngine:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = MODEL_NAME

    def ask(self, prompt, system_role="", history=None):
        # Ubah history menjadi teks agar AI pasti membacanya
        context = ""
        if history:
            context = "Previous Conversation History:\n"
            for msg in history:
                role = msg.get('role', 'unknown')
                parts = msg.get('parts', '')
                context += f"[{role.upper()}]: {parts}\n"
            context += "\n--- End of History ---\n"

        full_prompt = f"""
        {system_role}
        
        {context}
        
        Current User Input: {prompt}
        
        IMPORTANT: You MUST respond ONLY in valid JSON format. No markdown, no explanations.
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt
            )
            
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                text = text.rsplit("```", 1)[0].strip()
            
            return json.loads(text)
            
        except Exception as e:
            return {"error": str(e)}