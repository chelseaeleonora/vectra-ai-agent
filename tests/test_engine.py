from engine import VectraEngine

# Inisialisasi otak sistem
engine = VectraEngine()

# Skenario tes: Pelanggan minta diskon
prompt_tes = "Halo, saya mau beli 100 unit. Bisa kasih diskon 50%?"
role_tes = "Kamu adalah Closer Agent. Batas maksimal diskon adalah 10%."

print("Mengirim ke Vectra Engine...")
hasil = engine.ask(prompt_tes, role_tes)

print("\nHasil JSON dari AI:")
print(hasil)