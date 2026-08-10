(function () {
  function rebrand() {
    const header = document.querySelector("header");

    if (!header) return;

    // Jangan membuat branding dua kali
    if (header.querySelector(".vectra-brand")) {
      document.title = "Vectra AI — Autonomous CRO";
      return;
    }

    // Cari elemen yang mengandung tulisan Chainlit
    const elements = header.querySelectorAll("*");

    for (const el of elements) {
      if (
        el.children.length === 0 &&
        el.textContent.trim() === "Chainlit"
      ) {
        const parent = el.closest("a") || el.parentElement;

        if (!parent) continue;

        // Buat branding Vectra
        const brand = document.createElement("div");
        brand.className = "vectra-brand";

        // Logo Vectra
        const img = document.createElement("img");
        img.src = "/public/logo_vectra.svg";
        img.alt = "Vectra AI";

        // Text
        const text = document.createElement("span");
        text.textContent = "Vectra AI";

        brand.appendChild(img);
        brand.appendChild(text);

        // Ganti branding Chainlit
        parent.replaceWith(brand);

        break;
      }
    }

    // Browser tab title
    document.title = "Vectra AI — Autonomous CRO";
  }

  // Jalankan pertama kali
  rebrand();

  // Chainlit menggunakan React, sehingga DOM bisa berubah
  // setelah halaman selesai dimuat.
  const observer = new MutationObserver(() => {
    rebrand();
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
})();