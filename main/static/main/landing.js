(() => {
  const STORAGE_KEY = "quizora.theme";
  const root = document.documentElement;
  const toggle = document.getElementById("themeToggle");
  const label = document.getElementById("themeLabel");

  const getPreferredTheme = () => {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === "light" || stored === "dark") return stored;
    return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  };

  const applyTheme = (theme) => {
    root.setAttribute("data-theme", theme);
    if (label) label.textContent = theme === "dark" ? "Тёмная" : "Светлая";
    if (toggle) toggle.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
  };

  const setTheme = (theme) => {
    window.localStorage.setItem(STORAGE_KEY, theme);
    applyTheme(theme);
  };

  applyTheme(getPreferredTheme());

  toggle?.addEventListener("click", () => {
    const current = root.getAttribute("data-theme") === "dark" ? "dark" : "light";
    setTheme(current === "dark" ? "light" : "dark");
  });

  // randomized blink timings for background icons
  const icons = document.querySelectorAll(".bg-icon");
  icons.forEach((icon, index) => {
    const duration = 5 + Math.random() * 5; // 5–10s
    const delay = Math.random() * 8 + index * 0.2; // slightly разбросать и по индексу
    icon.style.animationDuration = `${duration}s`;
    icon.style.animationDelay = `${delay}s`;
  });
})();

