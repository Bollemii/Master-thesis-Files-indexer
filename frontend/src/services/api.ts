import { API_BASE_URL } from "../config/api";

export class AuthError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AuthError";
  }
}

export async function fetchWithAuth(
  endpoint: string,
  token: string | null,
  options: RequestInit = {}
) {
  if (!token) {
    throw new AuthError("No authentication token");
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.status === 401) {
    throw new AuthError("Token expired or invalid");
  }

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}
