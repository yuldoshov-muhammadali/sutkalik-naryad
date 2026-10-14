// Chop etish sahifasi: PDF yuklangach chop etish oynasini ochadi.
(function () {
  "use strict";
  var frame = document.getElementById("pdf");
  function printPdf() {
    try { frame.contentWindow.focus(); frame.contentWindow.print(); }
    catch (e) { window.open(frame.src, "_blank"); }
  }
  document.getElementById("print-again").addEventListener("click", printPdf);
  frame.addEventListener("load", function () { setTimeout(printPdf, 400); });
})();
