import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Logo } from "./Logo";
import { ThemeToggle } from "./ThemeToggle";
import { ProcessStatus } from "../types/api";

interface TopBarProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  processStatus: ProcessStatus;
  startProcess: () => void;
  n_not_processed: number;
}

export function TopBarDashboard({
  searchQuery,
  setSearchQuery,
  processStatus,
  startProcess,
  n_not_processed,
}: TopBarProps) {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    navigate(`/dashboard?q=${encodeURIComponent(searchQuery)}`);
  };

  const getStatusColor = (status: ProcessStatus["status"]) => {
    switch (status) {
      case "running":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-400 dark:text-yellow-900";
      case "completed":
        return "bg-green-100 text-green-800 dark:bg-green-400 dark:text-green-900";
      case "failed":
        return "bg-red-100 text-red-800 dark:bg-red-400 dark:text-red-900";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-400 dark:text-gray-900";
    }
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white dark:bg-gray-800 shadow-md">
      <div className="px-4 w-full">
        <div className="flex items-center justify-between h-16">
          <Logo />
          <div className="flex-shrink-0 w-32">
            <button
              onClick={() => {
                setSearchQuery("");
                navigate("/dashboard");
              }}
              className="text-xl cursor-pointer font-bold hover:text-gray-700 dark:text-white dark:hover:text-gray-300"
            >
              Codex
            </button>
          </div>
          <div className="flex-1 flex justify-center px-2 max-w-3xl mx-auto">
            <div className="max-w-lg w-full">
              <form onSubmit={handleSearch}>
                <label htmlFor="search" className="sr-only">
                  Search
                </label>
                <div className="relative">
                  <input
                    id="search"
                    type="text"
                    placeholder="Search documents..."
                    className="block w-full pl-4 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md leading-5 bg-white dark:bg-gray-700 placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-gray-100 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Escape") {
                        e.preventDefault();
                        e.currentTarget.value = ""; // Reset the input
                      }
                    }}
                  />
                </div>
              </form>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div
              className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(
                processStatus.status
              )}`}
            >
              {processStatus.status !== "running" && n_not_processed > 0 ? (
                `${n_not_processed} not processed`
              ) : (
                `${processStatus.status.charAt(0).toUpperCase()}${processStatus.status.slice(1)}`
              )}
            </div>
            {processStatus.last_run_time && (
              <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Last run:{" "}
                {new Date(processStatus.last_run_time).toLocaleString()}
              </div>
            )}

            <button
              onClick={startProcess}
              disabled={processStatus.status === "running" || n_not_processed === 0}
              className={`px-4 py-2 cursor-pointer rounded-md text-sm font-medium ${
                processStatus.status === "running"
                  ? "bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed"
                  : "bg-blue-500 text-white hover:bg-blue-600 dark:hover:bg-blue-400"
              }`}
            >
              Start Process
            </button>

            <ThemeToggle />

            <button
              onClick={logout}
              className="px-4 py-2 cursor-pointer rounded-md text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
