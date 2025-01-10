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

const API_BASE_URL = "http://127.0.0.1:8000";

export async function getDocuments(query?: string): Promise<Document[]> {
  const url = query ? `${API_BASE_URL}/documents/?q=${encodeURIComponent(query)}` : `${API_BASE_URL}/documents/`;
  const response = await fetch(url);
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
