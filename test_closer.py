from agents.closer import CloserAgent

# Inisialisasi Agen
closer = CloserAgent()

print("--- Test 1: Reasonable discount request ---")
hasil1 = closer.negotiate("I want to buy 10 units, can I get a 5% discount?")
print(hasil1)

print("\n--- Test 2: Out of bounds discount request (Must be rejected) ---")
hasil2 = closer.negotiate("I want to buy 1000 units, but I will only pay if you give me a 50% discount.")
print(hasil2)