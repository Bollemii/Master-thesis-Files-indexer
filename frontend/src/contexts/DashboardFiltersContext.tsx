import { createContext } from "react";

export type ProcessingStatus = "all" | "processed" | "unprocessed";

export type DashboardFilters = {
  processed: ProcessingStatus;
  topicId: string;
};

export const DashboardFiltersContext = createContext<{
  filters: DashboardFilters;
  setFilters: (filters: DashboardFilters) => void;
  setProcessingStatus: (status: ProcessingStatus) => void;
  setTopicId: (topicId: string) => void;
}>({
  filters: { processed: "all", topicId: "" },
  setFilters: () => {},
  setProcessingStatus: () => {},
  setTopicId: () => {},
});
