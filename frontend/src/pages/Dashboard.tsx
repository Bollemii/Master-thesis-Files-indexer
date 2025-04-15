import { useState, useEffect, useCallback, useRef } from "react";
import { Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { DocumentsPagination, ProcessStatus } from "../types/api";
import { CorpusList } from "../components/CorpusList";
import { CorpusDetail } from "../components/CorpusDetail";
import { TopicDetail } from "../components/TopicDetail";
import { fetchWithAuth, AuthError } from "../services/api";
import { TopBar } from "@/components/TopBar";
import { Upload } from "lucide-react";

export function Dashboard() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [documents, setDocuments] = useState<DocumentsPagination>();
  const [processStatus, setProcessStatus] = useState<ProcessStatus>({
    status: "idle",
    last_run_time: null,
  });
  const previousStatusRef = useRef<string>(processStatus.status);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const { token, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const itemsPerPage = 21;

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const query = params.get("q");
    if (query) {
      setSearchQuery(query);
    }
  }, [location.search]);

  const isDetailPage = () => {
    return (
      location.pathname.includes("/corpus/") ||
      location.pathname.includes("/topic/")
    );
  };

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

      if (
        previousStatusRef.current === "running" &&
        status.status === "completed"
      ) {
        fetchDocuments();
      }

      previousStatusRef.current = status.status;
      setProcessStatus(status);
    } catch (err) {
      console.error("Failed to fetch process status:", err);
      handleAuthError(err as Error);
    }
  }, [token, handleAuthError, fetchDocuments]);

  const startProcess = async () => {
    try {
      await fetchWithAuth("/documents/process", token, { method: "POST" });
      await fetchProcessStatus();
    } catch (err) {
      console.error("Failed to start process:", err);
      handleAuthError(err as Error);
    }
  };

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      await fetchWithAuth("/documents/", token, {
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
    const isSearchChange = searchQuery !== (new URLSearchParams(location.search).get("q") ?? "");
    if (isSearchChange && currentPage !== 1) {
      setCurrentPage(1);
      return;
    }

    const timeoutId = setTimeout(() => {
      fetchDocuments();
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, fetchDocuments, currentPage, location.search]);

  const totalPages = Math.ceil((documents?.total || 0) / itemsPerPage);

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      <TopBar
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        processStatus={processStatus}
        startProcess={startProcess}
      />
      <main className="flex-1 max-w-7xl w-full mx-auto py-6 sm:px-6 lg:px-8 mt-16">
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
      {!isDetailPage() && (
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className={`fixed bottom-8 right-8 p-4 bg-blue-500 text-white dark:bg-blue-600 dark:hover:bg-blue-500 rounded-full cursor-pointer shadow-lg transition-colors duration-200 flex items-center justify-center group ${
            isUploading ? "opacity-50 cursor-not-allowed" : ""
          }`}
          aria-label="Upload document"
        >
          <Upload className={`w-6 h-6 ${isUploading ? "animate-pulse" : ""}`} />
          <span className="max-w-0 overflow-hidden whitespace-nowrap group-hover:max-w-xs group-hover:ml-2 transition-all duration-200 ease-in-out">
            {isUploading ? "Uploading..." : "Upload"}
          </span>
        </button>
      )}
    </div>
  );
}
