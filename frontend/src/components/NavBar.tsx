import React, { useState, useCallback, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Home as HomeIcon, Search, User, Sun, Moon, Play } from "lucide-react";
import { useTheme } from "../contexts/ThemeContext";
import debounce from "lodash.debounce";
import { processDocument, ProcessStatus, getProcessStatus } from "../lib/api";


export function Navbar() {
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState(searchParams.get("q") || "");
  const [isProcessing, setIsProcessing] = useState(false);
  const [processStatus, setProcessStatus] = useState<ProcessStatus>({
    status: "idle",
    last_run_time: null,
  });

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const status = await getProcessStatus();
        setProcessStatus(status);
      } catch (error) {
        console.error("Failed to get process status:", error);
      }
    };
    const interval = setInterval(checkStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const debouncedSearch = useCallback((query: string) => {
    const delayedSearch = debounce(() => {
      if (query) {
        navigate(`/?q=${encodeURIComponent(query)}`);
      } else {
        navigate("/");
      }
    }, 300);
    delayedSearch();
  }, [navigate]);

  const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
    const query = event.target.value;
    setSearchQuery(query);
    debouncedSearch(query);
  };

  const handleProcess = async () => {
    try {
      setIsProcessing(true);
      await processDocument();
    } catch (error) {
      console.error("Failed to process document", error);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <nav className="bg-white dark:bg-gray-800 shadow dark:shadow-gray-700 transition-colors duration-200">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <Link
            to="/"
            className="text-gray-800 dark:text-gray-200 hover:text-gray-600 dark:hover:text-gray-400"
          >
            <HomeIcon className="h-6 w-6" />
          </Link>

          <div className="flex-1 max-w-lg mx-8">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400 dark:text-gray-500" />
              <input
                name="search"
                type="text"
                value={searchQuery}
                onChange={handleSearch}
                placeholder="Search documents..."
                className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 
                         py-2 pl-10 pr-4 text-gray-900 dark:text-gray-100
                         focus:border-blue-500 dark:focus:border-blue-400 focus:outline-none
                         transition-colors duration-200"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex flex-col items-end mr-4 text-sm">
              <span className="text-gray-600 dark:text-gray-400">
                Status: {processStatus.status}
              </span>
              {processStatus.last_run_time && (
                <span className="text-gray-500 dark:text-gray-500">
                  Last run:{" "}
                  {new Date(processStatus.last_run_time).toLocaleString()}
                </span>
              )}
            </div>
            <button
              onClick={handleProcess}
              disabled={isProcessing}
              className="text-gray-800 dark:text-gray-200 hover:text-gray-600 dark:hover:text-gray-400
                       disabled:opacity-50 disabled:cursor-not-allowed"
              title="Process documents"
            >
              {(processStatus.status === "running") ? (
                <svg
                  aria-hidden="true"
                  className="w-8 h-8 text-gray-200 animate-spin dark:text-gray-600 fill-blue-600"
                  viewBox="0 0 100 101"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z"
                    fill="currentColor"
                  />
                  <path
                    d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z"
                    fill="currentFill"
                  />
                </svg>
              ) : (
                <Play className="h-6 w-6" />
              )}
            </button>
            <button
              onClick={toggleTheme}
              className="text-gray-800 dark:text-gray-200 hover:text-gray-600 dark:hover:text-gray-400"
            >
              {theme === "dark" ? (
                <Sun className="h-6 w-6" />
              ) : (
                <Moon className="h-6 w-6" />
              )}
            </button>
            <div className="text-gray-800 dark:text-gray-200">
              <User className="h-6 w-6" />
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
