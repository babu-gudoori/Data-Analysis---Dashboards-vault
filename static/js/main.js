document.addEventListener("DOMContentLoaded", () => {
  const body = document.body;
  const themeSwitch = document.getElementById("themeSwitch");

  // 🌙 Load Theme from Local Storage
  if (localStorage.getItem("theme") === "dark") {
    body.classList.add("dark");
    themeSwitch.checked = true;
  }

  // 🌞 Toggle Theme
  if (themeSwitch) {
    themeSwitch.addEventListener("change", () => {
      const isDark = themeSwitch.checked;
      body.classList.toggle("dark", isDark);
      localStorage.setItem("theme", isDark ? "dark" : "light");
    });
  }

  // 🎯 Filter by Category
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document
        .querySelectorAll(".tab")
        .forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");

      const selected = tab.dataset.filter;
      document.querySelectorAll(".dashboard-card").forEach((card) => {
        const match = selected === "All" || card.dataset.category === selected;
        card.style.display = match ? "flex" : "none";
      });
    });
  });

  // 📖 Read More Toggle
  document.querySelectorAll(".dashboard-card").forEach((card) => {
    const desc = card.querySelector(".desc");
    const toggle = card.querySelector(".read-toggle");

    if (desc && toggle) {
      if (desc.scrollHeight <= desc.clientHeight + 5)
        toggle.style.display = "none";

      toggle.addEventListener("click", (e) => {
        e.preventDefault();
        desc.classList.toggle("expanded");
        toggle.textContent = desc.classList.contains("expanded")
          ? "Read less"
          : "Read more...";
      });
    }
  });

  // ⌨️ Secret Admin Shortcut: Ctrl + Alt + L
  document.addEventListener("keydown", (e) => {
    if (e.ctrlKey && e.altKey && e.key.toLowerCase() === "l") {
      fetch("/trigger_admin_shortcut")
        .then((res) => res.url) // Get the login URL with token
        .then((url) => {
          // Open in the same tab instead of new tab
          window.location.href = url;
        })
        .catch((err) => {
          alert("❌ Failed to open admin login.");
          console.error(err);
        });
    }
  });

  // 🔗 Auto Scroll to Hash in URL
  setTimeout(() => {
    const hash = window.location.hash.slice(1);
    if (hash) {
      const target = document.getElementById(hash);
      if (target) {
        target.scrollIntoView({ behavior: "smooth", block: "center" });
        target.classList.add("highlight");
        setTimeout(() => target.classList.remove("highlight"), 3000);
      }
    }
  }, 500);
});

// 📋 Copy Dashboard Link with Hash
function copyDashboardAnchorLink(dashboardId, button) {
  const baseUrl = `${window.location.origin}${window.location.pathname}`;
  const fullLink = `${baseUrl}#${dashboardId}`;
  console.log("Copying full link:", fullLink);

  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard
      .writeText(fullLink)
      .then(() => showCopyFeedback(button, "✅ Copied!"))
      .catch(() => {
        fallbackCopyTextToClipboard(fullLink);
        showCopyFeedback(button, "✅ Copied (fallback)!");
      });
  } else {
    fallbackCopyTextToClipboard(fullLink);
    showCopyFeedback(button, "✅ Copied (fallback)!");
  }
}

function showCopyFeedback(button, message) {
  const existing = button.parentElement.querySelector(".copy-feedback");
  if (existing) existing.remove();

  const feedback = document.createElement("span");
  feedback.className = "copy-feedback";
  feedback.textContent = message;
  button.parentElement.appendChild(feedback);

  setTimeout(() => feedback.remove(), 2000);
}

function fallbackCopyTextToClipboard(text) {
  const textArea = document.createElement("textarea");
  textArea.value = text;
  textArea.style.position = "fixed";
  textArea.style.top = 0;
  textArea.style.left = 0;
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();

  try {
    document.execCommand("copy");
    alert("✅ Link copied: " + text);
  } catch (err) {
    alert("❌ Copy failed: " + err);
  }

  document.body.removeChild(textArea);
}

// 🔎 Fullscreen Iframe
function fullscreenIframe(id) {
  const iframe = document.getElementById(id);
  if (iframe.requestFullscreen) {
    iframe.requestFullscreen();
  } else if (iframe.webkitRequestFullscreen) {
    iframe.webkitRequestFullscreen();
  } else if (iframe.msRequestFullscreen) {
    iframe.msRequestFullscreen();
  } else {
    alert("❌ Fullscreen not supported in this browser.");
  }
}
