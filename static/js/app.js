// Inline JavaScript'siz (Content-Security-Policy: script-src 'self') umumiy xatti-harakatlar.
(function () {
  "use strict";
  // Modal oynani yopish: <button data-close-modal>
  document.addEventListener("click", function (event) {
    var btn = event.target.closest("[data-close-modal]");
    if (btn) {
      var modal = document.getElementById("modal");
      if (modal) modal.innerHTML = "";
    }
  });
  // Tasdiqlash so'rovi: <form data-confirm="Matn">
  document.addEventListener("submit", function (event) {
    var form = event.target.closest("form[data-confirm]");
    if (form && !window.confirm(form.getAttribute("data-confirm"))) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  }, true);
})();
