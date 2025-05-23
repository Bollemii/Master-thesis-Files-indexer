import { memo, useRef } from "react";
import { Document, TopicResponse } from "../types/api";
import { useNavigate } from "react-router-dom";
import { DocumentPreview } from "./DocumentPreview";
import { Pagination } from "./Pagination";
import DashboardFilters from "./DashboardFilters";

interface CorpusListProps {
  documents: Document[];
  topics: TopicResponse[];
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  itemsPerPage: number;
  setItemsPerPage: (itemsPerPage: number) => void;
}

export const CorpusList = memo(function CorpusList({
  documents,
  topics,
  currentPage,
  totalPages,
  onPageChange,
  itemsPerPage,
  setItemsPerPage,
}: CorpusListProps) {
  const navigate = useNavigate();
  const topPage = useRef<HTMLDivElement>(null);

  const handleScrollToTop = () => {
    topPage.current?.scrollIntoView({ behavior: "smooth" });
  };

  const setItemsPerPageAndScroll = (itemsPerPage: number) => {
    setItemsPerPage(itemsPerPage);
    onPageChange(1);
    handleScrollToTop();
  };
  const changePageAndScroll = (page: number) => {
    onPageChange(page);
    handleScrollToTop();
  }

  return (
    <div className="min-h-screen pb-16 dark:bg-gray-900">
      <div ref={topPage} />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {documents.length === 0 && (
          <div className="col-span-1 sm:col-span-2 lg:col-span-3">
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
              <p className="text-gray-500 dark:text-gray-400 text-center">
                No documents found.
              </p>
            </div>
          </div>
        )}
        {documents.map((doc) => (
          <div
            key={doc.id}
            onClick={() => navigate(`/dashboard/corpus/${doc.id}`)}
            className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg cursor-pointer hover:shadow-md transition-shadow"
          >
            <DocumentPreview
              previewUrl={doc.preview_url}
              filename={doc.filename}
              size="thumbnail"
              className="aspect-square"
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
      <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 h-16 flex items-center justify-between">
        <div className="flex items-center px-4 h-full flex-1">
          <span className="text-sm text-gray-500 dark:text-gray-400 mr-4">
            Items per page:
          </span>
          <div className="rounded-md mr-2 border dark:border-gray-300 border-gray-700 dark:bg-gray-300 bg-white cursor-pointer">
            <select
              className="cursor-pointer p-2"
              onChange={(e) => setItemsPerPageAndScroll(Number(e.target.value))}
              value={itemsPerPage}
            >
              <option value={9}>9</option>
              <option value={12}>12</option>
              <option value={15}>15</option>
              <option value={18}>18</option>
              <option value={21}>21</option>
              <option value={24}>24</option>
              <option value={27}>27</option>
              <option value={30}>30</option>
            </select>
          </div>
          <DashboardFilters topics={topics}/>
        </div>
        <div className="h-full flex-1">
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={changePageAndScroll}
          />
        </div>
        <div className="flex-1"/>
      </div>
    </div>
  );
});
