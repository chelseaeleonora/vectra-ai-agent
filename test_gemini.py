import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Model yang terlihat PUNYA KUOTA di screenshot Rate Limit kamu
# (urutan dari kuota terbesar)
models_to_try = [
    "gemini-3.1-flash-lite",  # 0/15 RPM - kuota terbesar
    "gemini-2.5-flash-lite",  # 0/10 RPM
    "gemini-3-flash",         # 0/5 RPM
    "gemini-3.5-flash",       # 0/5 RPM
    "gemini-2.5-flash",       # 1/5 RPM (sudah terpakai 1)
]

print("Mencoba model yang tersedia berdasarkan Rate Limit...\n")

for model_name in models_to_try:
    print(f"Testing: {model_name}")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Halo, balas HANYA dengan JSON: {\"status\": \"sukses\", \"model\": \"nama_model\"}"
        )
        print(f"✅ BERHASIL dengan {model_name}!")
        print(f"Response: {response.text}")
        print("\n🎉 KONEKSI SUKSES! Kita bisa lanjut coding Multi-Agent.")
        break
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            print(f"   ❌ 404 - Model name mungkin salah atau tidak tersedia")
        elif "429" in error_msg:
            print(f"   ❌ 429 - Kuota habis")
        else:
            print(f"   ❌ Error: {e}")
    print()  # baris kosong