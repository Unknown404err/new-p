(function () {
  "use strict";

  var sidebar = document.getElementById("sidebar");
  var menuBtn = document.getElementById("menuBtn");
  var nav = document.getElementById("nav");
  var search = document.getElementById("search");
  var idx = document.getElementById("idx");
  var pbarFill = document.getElementById("pbarFill");
  var pbarText = document.getElementById("pbarText");

  var LESSONS = Array.prototype.slice.call(document.querySelectorAll(".lesson"));
  var TOTAL = LESSONS.length;
  var KEY = "darslik1000:done";

  /* ---------- menyu ---------- */

  if (menuBtn) {
    menuBtn.addEventListener("click", function () {
      sidebar.classList.toggle("open");
    });
  }

  document.addEventListener("click", function (e) {
    if (window.innerWidth <= 1000 && sidebar.classList.contains("open")) {
      if (!sidebar.contains(e.target) && e.target !== menuBtn) {
        sidebar.classList.remove("open");
      }
    }
  });

  nav.addEventListener("click", function (e) {
    if (e.target.closest("a") && window.innerWidth <= 1000) {
      sidebar.classList.remove("open");
    }
  });

  /* ---------- progress ---------- */

  function readDone() {
    try {
      return JSON.parse(localStorage.getItem(KEY) || "[]");
    } catch (err) {
      return [];
    }
  }

  function writeDone(list) {
    try {
      localStorage.setItem(KEY, JSON.stringify(list));
    } catch (err) {
      /* localStorage o'chirilgan bo'lsa jim o'tamiz */
    }
  }

  function paintProgress() {
    var done = readDone();
    var pct = TOTAL ? Math.round((done.length / TOTAL) * 100) : 0;
    if (pbarFill) pbarFill.style.width = pct + "%";
    if (pbarText) pbarText.textContent = done.length + " / " + TOTAL + " dars";
    document.querySelectorAll("[data-done]").forEach(function (box) {
      var n = box.getAttribute("data-done");
      var isDone = done.indexOf(n) !== -1;
      box.checked = isDone;
      var sec = box.closest(".lesson");
      if (sec) sec.classList.toggle("is-done", isDone);
    });
  }

  document.querySelectorAll("[data-done]").forEach(function (box) {
    box.addEventListener("change", function () {
      var n = box.getAttribute("data-done");
      var done = readDone();
      var i = done.indexOf(n);
      if (box.checked && i === -1) done.push(n);
      if (!box.checked && i !== -1) done.splice(i, 1);
      writeDone(done);
      paintProgress();
    });
  });

  paintProgress();

  /* ---------- scroll spy ---------- */

  var links = Array.prototype.slice.call(nav.querySelectorAll("a"));
  var byTarget = {};
  links.forEach(function (a) {
    byTarget[a.getAttribute("href").slice(1)] = a;
  });

  var visible = new Map();
  var spy = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) visible.set(entry.target.id, entry.boundingClientRect.top);
        else visible.delete(entry.target.id);
      });
      if (!visible.size) return;
      var best = null;
      visible.forEach(function (top, id) {
        if (best === null || top < visible.get(best)) best = id;
      });
      links.forEach(function (a) {
        a.classList.remove("on");
      });
      if (best && byTarget[best]) byTarget[best].classList.add("on");
    },
    { rootMargin: "-10% 0px -70% 0px", threshold: 0 }
  );

  document.querySelectorAll("section.doc, header.cover").forEach(function (sec) {
    if (sec.id) spy.observe(sec);
  });

  /* ---------- qidiruv ---------- */

  if (search) {
    search.addEventListener("input", function () {
      var q = search.value.trim().toLowerCase();
      links.forEach(function (a) {
        var hit = !q || a.textContent.toLowerCase().indexOf(q) !== -1;
        a.classList.toggle("hidden", !hit);
      });
      if (idx) {
        var rows = idx.querySelectorAll(".row[data-w]");
        for (var i = 0; i < rows.length; i++) {
          var row = rows[i];
          var hit = !q || row.getAttribute("data-w").indexOf(q) !== -1;
          row.classList.toggle("hide", !hit);
        }
      }
    });
  }

  /* ---------- klaviatura ---------- */

  document.addEventListener("keydown", function (e) {
    if (e.target.matches("input, textarea")) return;
    if (e.key !== "j" && e.key !== "k") return;
    var ids = LESSONS.map(function (s) {
      return s.id;
    });
    var y = window.scrollY + 120;
    var current = 0;
    LESSONS.forEach(function (s, i) {
      if (s.getBoundingClientRect().top + window.scrollY <= y) current = i;
    });
    var next = e.key === "j" ? Math.min(current + 1, ids.length - 1) : Math.max(current - 1, 0);
    var el = document.getElementById(ids[next]);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  /* ---------- chop etish: javoblarni ochish ---------- */

  window.addEventListener("beforeprint", function () {
    document.querySelectorAll("details").forEach(function (d) {
      d.open = true;
    });
  });
})();
