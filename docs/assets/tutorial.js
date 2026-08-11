const root = document.documentElement;
const saved = localStorage.getItem("tutorial-theme");
if (saved) root.dataset.theme = saved;
document.querySelector("#theme-toggle")?.addEventListener("click", () => {
  const next = root.dataset.theme === "dark" ? "light" : "dark";
  root.dataset.theme = next;
  localStorage.setItem("tutorial-theme", next);
});
