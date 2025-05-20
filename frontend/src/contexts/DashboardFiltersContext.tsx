import { createContext } from "react";

export type ProcessingStatus = "all" | "processed" | "unprocessed";

export type DashboardFilters = {
  processed: ProcessingStatus;
  topicId: string;
};

export const DashboardFiltersContext = createContext<{
  filters: DashboardFilters;
  setFilters: (filters: DashboardFilters) => void;
  setProcessingFilterStatus: (status: ProcessingStatus) => void;
  setFilterTopicId: (topicId: string) => void;
}>({
  filters: { processed: "all", topicId: "" },
  setFilters: () => {},
  setProcessingFilterStatus: () => {},
  setFilterTopicId: () => {},
});
