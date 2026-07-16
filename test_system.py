from vectra_system import VectraSystem

vectra = VectraSystem()

print("=== VECTRA AI MULTI-AGENT SYSTEM TEST ===\n")

print("--- Skenario 1: Pelanggan baru bertanya ---")
hasil1 = vectra.process_message("Hi, I run a small bakery and I'm looking for a way to automate my sales.")
print("Final Response:", hasil1)

print("\n--- Skenario 2: Pelanggan menawar harga ---")
hasil2 = vectra.process_message("Your software looks good, but $500 is too expensive. Can you give me a 15% discount?")
print("Final Response:", hasil2)

print("\n--- Skenario 3: Pelanggan minta invoice ---")
hasil3 = vectra.process_message("I agree to the price. Please send me the invoice.")
print("Final Response:", hasil3)