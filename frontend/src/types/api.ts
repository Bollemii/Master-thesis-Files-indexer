export interface Document {
  id: string;
  filename: string;
  upload_date: string;
  preview_url: string;
  detail_preview_url?: string;
  processed: boolean;
  topics?: TopicResponse[];
}

export interface TopicResponse {
  id: string;
  name: string;
  description: string | null;
  weight: number;
  words: Record<string, number>;
}

export interface DocumentsPagination {
  items: Document[];
  total: number;
  page: number;
  limit: number;
  n_not_processed: number;
}

export interface ProcessStatus {
  status: "idle" | "running" | "completed" | "failed" | "cancelled";
  last_run_time: string | null;
}
