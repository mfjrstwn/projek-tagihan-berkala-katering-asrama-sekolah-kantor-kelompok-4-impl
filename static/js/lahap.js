/* lahap.in - modal konfirmasi.
   Tautan <a data-dialog> mengambil halaman konfirmasi dari server dan menampilkannya
   di <dialog>. Tanpa JavaScript, tautan tetap membuka halaman penuh. */
(function () {
  var dlg = document.createElement("dialog");
  dlg.className = "dialog";
  dlg.setAttribute("aria-labelledby", "dialog-judul");
  document.body.appendChild(dlg);

  async function buka(tautan) {
    try {
      var res = await fetch(tautan.href, { credentials: "same-origin" });
      var doc = new DOMParser().parseFromString(await res.text(), "text/html");
      var isi = doc.querySelector("[data-dialog-isi]");
      if (!res.ok || res.redirected || !isi) { throw new Error("tanpa dialog"); }
      dlg.innerHTML = isi.outerHTML;
      dlg.showModal();
    } catch (e) {
      window.location.href = tautan.href;   // cadangan: halaman penuh
    }
  }

  document.addEventListener("click", function (e) {
    var tautan = e.target.closest("a[data-dialog]");
    if (tautan && e.button === 0 && !(e.metaKey || e.ctrlKey || e.shiftKey)) {
      e.preventDefault();
      buka(tautan);
      return;
    }
    if (dlg.open && dlg.contains(e.target) && e.target.closest("[data-dialog-tutup]")) {
      e.preventDefault();
      dlg.close();
    }
  });

  dlg.addEventListener("click", function (e) {   // klik di area gelap menutup dialog
    if (e.target === dlg) { dlg.close(); }
  });
})();
