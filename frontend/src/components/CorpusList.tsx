import { memo } from "react";
import { Document } from "../types/api";
import { useNavigate } from "react-router-dom";
import { DocumentPreview } from "./DocumentPreview";
import { Pagination } from "./Pagination";

interface CorpusListProps {
  documents: Document[];
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export const CorpusList = memo(function CorpusList({
  documents,
  currentPage,
  totalPages,
  onPageChange,
}: CorpusListProps) {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen pb-16 dark:bg-gray-900">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {documents.map((doc) => (
          <div
            key={doc.id}
            onClick={() => navigate(`/dashboard/corpus/${doc.id}`)}
            className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg cursor-pointer hover:shadow-md transition-shadow"
          >
            <DocumentPreview
              previewUrl={doc.preview_url}
              filename={doc.filename}
            />
            <div className="p-4 h-[120px]">
              <div className="text-lg font-medium text-gray-900 dark:text-gray-100 truncate">
                {doc.filename}
              </div>
              <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                {new Date(doc.upload_date).toLocaleDateString()}
              </div>
              <div className="mt-2">
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    doc.processed
                      ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300"
                      : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300"
                  }`}
                >
                  {doc.processed ? "Processed" : "Not Processed"}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 h-16">
        <div className="max-w-7xl mx-auto h-full">
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={onPageChange}
          />
        </div>
      </div>
    </div>
  );
});
