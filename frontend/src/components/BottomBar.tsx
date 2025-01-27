interface BottomBarProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (newPage: number) => void;
  limit: number;
  page: number;
  total: number;
}

export function BottomBar({
  currentPage,
  totalPages,
  onPageChange,
  page,
}: BottomBarProps) {
  return (
    <div
      className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 
                    dark:border-gray-700 shadow-lg transition-colors duration-200"
    >
      <div className="container mx-auto px-4 h-10 flex items-center justify-between">
        <div className="flex-1 flex justify-center items-center space-x-4">
          {totalPages > 1 && (
            <>
              <button
                onClick={() => onPageChange(Math.max(0, page - 1))}
                disabled={page === 0}
                className="px-4 py-1 bg-blue-500 dark:bg-blue-600 text-white rounded 
                         hover:bg-blue-600 dark:hover:bg-blue-700 disabled:opacity-50 
                         transition-colors duration-200"
              >
                Previous
              </button>
              <span className="text-gray-700 dark:text-gray-300">
                Page {currentPage} of {totalPages}
              </span>
              <button
                onClick={() => onPageChange(page + 1)}
                disabled={page === totalPages - 1}
                className="px-4 py-1 bg-blue-500 dark:bg-blue-600 text-white rounded 
                         hover:bg-blue-600 dark:hover:bg-blue-700 disabled:opacity-50
                         transition-colors duration-200"
              >
                Next
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
