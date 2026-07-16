from agents.sdr import SDRAgent

sdr = SDRAgent()

print("--- Test 1: Serious Buyer ---")
hasil1 = sdr.qualify_lead("Hi, I am looking for an AI sales agent for my company. We have a budget of $500/month.")
print(hasil1)

print("\n--- Test 2: Not Serious / Just Curious ---")
hasil2 = sdr.qualify_lead("Hey, what does your AI do? I'm just browsing, I have no money right now.")
print(hasil2)