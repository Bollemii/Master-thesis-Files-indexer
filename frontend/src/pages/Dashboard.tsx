import { useState, useEffect, useCallback, useRef } from "react";
import { Routes, Route, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { DocumentsPagination, ProcessStatus } from "../types/api";
import { CorpusList } from "../components/CorpusList";
import { CorpusDetail } from "../components/CorpusDetail";
import { TopicDetail } from "../components/TopicDetail";
import { fetchWithAuth, AuthError } from "../services/api";
import { Upload } from "lucide-react";
import { Logo } from "@/components/Logo";

export function Dashboard() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [documents, setDocuments] = useState<DocumentsPagination>();
  const [processStatus, setProcessStatus] = useState<ProcessStatus>({
    status: "idle",
    last_run_time: null,
  });
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const { token, logout } = useAuth();
  const navigate = useNavigate();
  const itemsPerPage = 21;

  const handleAuthError = useCallback(
    (error: Error) => {
      if (error instanceof AuthError) {
        logout();
        navigate("/login");
      }
    },
    [logout, navigate]
  );

  const fetchDocuments = useCallback(async () => {
    try {
      const documents = await fetchWithAuth(
        `/documents/?q=${encodeURIComponent(
          searchQuery
        )}&page=${currentPage}&limit=${itemsPerPage}`,
        token
      );
      setDocuments(documents);
    } catch (err) {
      console.error("Failed to fetch documents:", err);
      handleAuthError(err as Error);
    }
  }, [token, searchQuery, currentPage, handleAuthError]);

  const fetchProcessStatus = useCallback(async () => {
    try {
      const status = await fetchWithAuth("/documents/process/status", token);
      setProcessStatus(status);
    } catch (err) {
      console.error("Failed to fetch process status:", err);
      handleAuthError(err as Error);
    }
  }, [token, handleAuthError]);

  const startProcess = useCallback(async () => {
    try {
      await fetchWithAuth("/documents/process", token, { method: "POST" });
      fetchProcessStatus();
    } catch (err) {
      console.error("Failed to start process:", err);
      handleAuthError(err as Error);
    }
  }, [token, fetchProcessStatus, handleAuthError]);

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      await fetchWithAuth("/documents", token, {
        method: "POST",
        body: formData,
        headers: {
          Accept: "application/json",
        },
      });

      await fetchDocuments();
    } catch (err) {
      console.error("Failed to upload document:", err);
      handleAuthError(err as Error);
    } finally {
      setIsUploading(false);
    }
  };

  useEffect(() => {
    fetchProcessStatus();
    const interval = setInterval(fetchProcessStatus, 5000);
    return () => clearInterval(interval);
  }, [fetchProcessStatus]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      fetchDocuments();
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, fetchDocuments]);

  const getStatusColor = (status: ProcessStatus["status"]) => {
    switch (status) {
      case "running":
        return "bg-yellow-100 text-yellow-800";
      case "completed":
        return "bg-green-100 text-green-800";
      case "failed":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const totalPages = Math.ceil((documents?.total || 0) / itemsPerPage) - 1;

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <nav className="bg-white shadow-sm flex-none h-16">
        <div className="max-w-7xl mx-auto lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Logo />
            <div className="flex-shrink-0 w-32">
              <button
                onClick={() => navigate("/")}
                className="text-xl font-bold hover:text-gray-700"
              >
                Codex
              </button>
            </div>

            <div className="flex-1 flex justify-center px-2 max-w-3xl mx-auto">
              <div className="max-w-lg w-full">
                <label htmlFor="search" className="sr-only">
                  Search
                </label>
                <div className="relative">
                  <input
                    id="search"
                    type="search"
                    placeholder="Search documents..."
                    className="block w-full pl-4 pr-12 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div
                className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(
                  processStatus.status
                )}`}
              >
                {processStatus.status.charAt(0).toUpperCase() +
                  processStatus.status.slice(1)}
              </div>
              {processStatus.last_run_time && (
                <div className="mt-1 text-xs text-gray-500">
                  Last run:{" "}
                  {new Date(processStatus.last_run_time).toLocaleString()}
                </div>
              )}

              <button
                onClick={startProcess}
                disabled={processStatus.status === "running"}
                className={`px-4 py-2 rounded-md text-sm font-medium ${
                  processStatus.status === "running"
                    ? "bg-gray-200 text-gray-500 cursor-not-allowed"
                    : "bg-blue-500 text-white hover:bg-blue-600"
                }`}
              >
                Start Process
              </button>

              <button
                onClick={logout}
                className="px-4 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-100"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="flex-1 max-w-7xl w-full mx-auto py-6 sm:px-6 lg:px-8">
        <Routes>
          <Route
            path="/"
            element={
              <CorpusList
                documents={documents?.items || []}
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={setCurrentPage}
              />
            }
          />
          <Route path="/corpus/:id" element={<CorpusDetail />} />
          <Route path="/topic/:id" element={<TopicDetail />} />
        </Routes>
      </main>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.doc,.docx,.txt"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) {
            handleUpload(file);
          }
          // Reset the input
          e.target.value = "";
        }}
      />
      <button
        onClick={() => fileInputRef.current?.click()}
        disabled={isUploading}
        className={`fixed bottom-8 right-8 p-4 bg-blue-500 text-white rounded-full shadow-lg hover:bg-blue-600 transition-colors duration-200 flex items-center justify-center group ${
          isUploading ? "opacity-50 cursor-not-allowed" : ""
        }`}
        aria-label="Upload document"
      >
        <Upload className={`w-6 h-6 ${isUploading ? "animate-pulse" : ""}`} />
        <span className="max-w-0 overflow-hidden whitespace-nowrap group-hover:max-w-xs group-hover:ml-2 transition-all duration-200 ease-in-out">
          {isUploading ? "Uploading..." : "Upload"}
        </span>
      </button>
    </div>
  );
}
