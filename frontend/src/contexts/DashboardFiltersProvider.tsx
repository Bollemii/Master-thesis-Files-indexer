import { useState } from "react";
import { DashboardFiltersContext, DashboardFilters, ProcessingStatus } from "./DashboardFiltersContext";

export function DashboardFiltersProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [filters, setFilters] = useState<DashboardFilters>({
    processed: "all",
    topicId: "",
  });

  const setProcessingStatus = (status: ProcessingStatus) => {
    setFilters((prev) => ({ ...prev, processed: status }));
  };

  const setTopicId = (topicId: string) => {
      setFilters((prev) => ({ ...prev, topicId }));
  };

  return (
    <DashboardFiltersContext.Provider value={{ filters, setFilters, setProcessingStatus, setTopicId }}>
      {children}
    </DashboardFiltersContext.Provider>
  );
}