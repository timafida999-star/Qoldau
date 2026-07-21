import { Moon, Sun } from "lucide-react";

import { useTheme } from "@/hooks/useTheme";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label="Toggle theme"
      title={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className={`relative inline-flex h-8 w-14 shrink-0 items-center rounded-full border border-input transition-colors duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${
        isDark ? "bg-primary/90" : "bg-secondary"
      }`}
    >
      <span
        className={`absolute left-1 flex h-6 w-6 items-center justify-center rounded-full bg-background shadow-soft transition-transform duration-300 ease-in-out ${
          isDark ? "translate-x-6" : "translate-x-0"
        }`}
      >
        <Sun
          className={`absolute h-3.5 w-3.5 text-yellow-500 transition-all duration-300 ease-in-out ${
            isDark ? "rotate-90 scale-0 opacity-0" : "rotate-0 scale-100 opacity-100"
          }`}
        />
        <Moon
          className={`absolute h-3.5 w-3.5 text-primary transition-all duration-300 ease-in-out ${
            isDark ? "rotate-0 scale-100 opacity-100" : "-rotate-90 scale-0 opacity-0"
          }`}
        />
      </span>
    </button>
  );
}
