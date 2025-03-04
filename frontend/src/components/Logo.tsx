import bookIcon from "../assets/open-book.png";
import bookIconLight from "../assets/open-book-light.png";
import { useTheme } from "../hooks/useTheme";

export function Logo() {
  const { theme } = useTheme();

  return (
    <div className="flex items-center justify-center">
      <img
        src={theme === "dark" ? bookIconLight : bookIcon}
        alt="Codex Logo"
        className="w-full h-full object-contain max-h-16 p-2 px-4"
      />
    </div>
  );
}
