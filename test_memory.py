from vectra_system import VectraSystem
import json

vectra = VectraSystem()

print("=== VECTRA AI MEMORY TEST ===\n")

print("--- Pesan 1: Tanya Produk ---")
r1 = vectra.process_message("Hi, I want to buy your software. I have a budget of $500.")
print("Hasil:", json.dumps(r1, indent=2))
print("\n---\n")

print("--- Pesan 2: Minta Diskon ---")
r2 = vectra.process_message("Can you give me a 10% discount on that $500?")
print("Hasil:", json.dumps(r2, indent=2))
print("\n---\n")

print("--- Pesan 3: Minta Invoice (Harus ingat harga $450) ---")
r3 = vectra.process_message("Okay, I agree to the discounted price. Please send me the invoice.")
print("Hasil Invoice:", json.dumps(r3, indent=2))