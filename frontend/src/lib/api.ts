export interface Documents {
  id: string;
  filename: string;
  upload_date: string;
  processed: boolean;
}

export interface Document {
  id: string;
  filename: string;
  upload_date: string;
  processed: boolean;
  topics: Topic[];
}

export interface Topic {
  id: string;
  name: string;
  description: string | null;
  weight: number;
  words: Record<string, number>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}

const API_BASE_URL = "http://127.0.0.1:8000";

export async function getDocuments(
  query?: string,
  page: number = 0,
  limit: number = 50
): Promise<PaginatedResponse<Documents>> {
  const params = new URLSearchParams();
  if (query) params.append("q", query);
  params.append("page", page.toString());
  params.append("limit", limit.toString());

  const response = await fetch(`${API_BASE_URL}/documents/?${params}`);
  if (!response.ok) {
    throw new Error("Failed to fetch documents");
  }
  return response.json();
}

export async function getDocument(id: string): Promise<Document> {
  const response = await fetch(`${API_BASE_URL}/documents/${id}`);
  if (!response.ok) {
    throw new Error("Failed to fetch document");
  }
  return response.json();
}

export async function uploadDocument(file: File): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE_URL}/documents/`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw new Error("Failed to upload document");
  }
  return response.json();
}

export async function processDocument(): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/documents/process/`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Failed to process document");
  }
}
