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

  const setProcessingFilterStatus = (status: ProcessingStatus) => {
    setFilters((prev) => ({ ...prev, processed: status }));
  };

  const setFilterTopicId = (topicId: string) => {
    setFilters((prev) => ({ ...prev, topicId }));
  };

  return (
    <DashboardFiltersContext.Provider value={{ filters, setFilters, setProcessingFilterStatus, setFilterTopicId }}>
      {children}
    </DashboardFiltersContext.Provider>
  );
}