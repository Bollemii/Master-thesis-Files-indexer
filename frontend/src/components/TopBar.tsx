import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Logo } from "./Logo";
import { ThemeToggle } from "./ThemeToggle";

export function TopBar() {
  const navigate = useNavigate();
  const { logout } = useAuth();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white dark:bg-gray-800 shadow-md">
      <div className="px-4 w-full flex items-center justify-between h-16">
        <div className="flex-1">
          <button
            onClick={() => {
              navigate("/dashboard");
            }}
            className="text-xl cursor-pointer font-bold hover:text-gray-700 dark:text-white dark:hover:text-gray-300"
          >
            <div className="flex items-center space-x-2">
              <Logo />
              Codex
            </div>
          </button>
        </div>
        <div className="flex-1 flex items-center justify-end space-x-4">
          <ThemeToggle />
          <button
            onClick={logout}
            className="px-4 py-2 cursor-pointer rounded-md text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}
