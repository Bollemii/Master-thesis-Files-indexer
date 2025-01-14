import React, { useState, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Home as HomeIcon, Search, User, Sun, Moon, Play } from "lucide-react";
import { useTheme } from "../contexts/ThemeContext";
import debounce from "lodash.debounce";
import { processDocument } from "../lib/api";

export function Navbar() {
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState(searchParams.get("q") || "");
  const [isProcessing, setIsProcessing] = useState(false);

  const debouncedSearch = useCallback(
    debounce((query: string) => {
      if (query) {
        navigate(`/?q=${encodeURIComponent(query)}`);
      } else {
        navigate("/");
      }
    }, 300),
    [navigate]
  );

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
  }

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
            <button
              onClick={handleProcess}
              disabled={isProcessing}
              className="text-gray-800 dark:text-gray-200 hover:text-gray-600 dark:hover:text-gray-400
                       disabled:opacity-50 disabled:cursor-not-allowed"
              title="Process documents"
            >
              <Play
                className={`h-6 w-6 ${isProcessing ? "animate-pulse" : ""}`}
              />
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
