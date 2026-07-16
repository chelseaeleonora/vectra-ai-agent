from agents.manager import ManagerAgent

manager = ManagerAgent()

print("--- Test 1: General Inquiry (Should route to SDR) ---")
hasil1 = manager.route_message("Hi, I run a small bakery and I'm looking for a way to automate my sales.")
print(hasil1)

print("\n--- Test 2: Price Negotiation (Should route to CLOSER) ---")
hasil2 = manager.route_message("Your software looks good, but $500 is too expensive. Can you give me a 15% discount?")
print(hasil2)

print("\n--- Test 3: Payment Request (Should route to FINANCE) ---")
hasil3 = manager.route_message("I agree to the price. Please send me the invoice and payment link.")
print(hasil3)