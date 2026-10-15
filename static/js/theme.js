// Kunduzgi / tungi rejim: <head> da sinxron ulanadi, sahifa chizilishidan oldin <html> ga "dark" klassini qo'yadi
// (oq “yaltirash” bo'lmasin). Tanlov localStorage da: "light" | "dark" | "auto" (tizim sozlamasiga qarab).
(function () {
  "use strict";
  var pref = "auto";
  try { pref = window.localStorage.getItem("naryad-theme") || "auto"; } catch (e) { /* xususiy rejim */ }
  if (pref !== "light" && pref !== "dark") pref = "auto";
  var systemDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  var root = document.documentElement;
  root.setAttribute("data-theme", pref);
  if (pref === "dark" || (pref === "auto" && systemDark)) root.classList.add("dark");
})();
