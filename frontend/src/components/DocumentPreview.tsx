import { useState, useEffect } from "react";
import { API_BASE_URL } from "../config/api";
import { useAuth } from "@/hooks/useAuth";

interface DocumentPreviewProps {
  previewUrl: string;
  filename: string;
  size?: "thumbnail" | "detail";
  className?: string;
}

const CACHE_NAME = "document-previews-v1";

async function getCachedImage(
  url: string,
  token: string,
  size: string
): Promise<Blob | null> {
  try {
    const cache = await caches.open(CACHE_NAME);
    const requestUrl = new URL(url);
    requestUrl.searchParams.set("size", size);
    const request = new Request(requestUrl.toString(), {
      headers: { Authorization: `Bearer ${token}` },
    });

    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      // Check if the image has been modified
      const response = await fetch(request, { method: "HEAD" });
      const cachedDate = new Date(cachedResponse.headers.get("date") || "");
      const lastModified = new Date(
        response.headers.get("last-modified") || ""
      );

      if (lastModified <= cachedDate) {
        return cachedResponse.blob();
      }
    }

    // Fetch and cache new image
    const response = await fetch(request);
    if (!response.ok) throw new Error("Failed to load image");

    const blob = await response.clone().blob();
    await cache.put(request, response);
    return blob;
  } catch (err) {
    console.error("Cache error:", err);
    return null;
  }
}

export function DocumentPreview({
  previewUrl,
  filename,
  size = "thumbnail",
  className = "",
}: DocumentPreviewProps) {
  const [error, setError] = useState(false);
  const [imageUrl, setImageUrl] = useState<string>("");
  const { token } = useAuth();

  useEffect(() => {
    if (!previewUrl) return;

    let isMounted = true;
    const abortController = new AbortController();

    const fetchImage = async () => {
      try {
        if (!token) return;
        const fullUrl = `${API_BASE_URL}${previewUrl}`;
        const cachedBlob = await getCachedImage(fullUrl, token, size);

        if (!isMounted) return;

        if (cachedBlob) {
          const url = URL.createObjectURL(cachedBlob);
          setImageUrl(url);
        } else {
          // Fallback to direct fetch if cache fails
          const response = await fetch(fullUrl, {
            headers: { Authorization: `Bearer ${token}` },
            signal: abortController.signal,
          });

          if (!response.ok) throw new Error("Failed to load image");

          const blob = await response.blob();
          if (!isMounted) return;

          const url = URL.createObjectURL(blob);
          setImageUrl(url);
        }
      } catch (err) {
        if (!isMounted) return;
        console.error("Error loading preview:", err);
        setError(true);
      }
    };

    fetchImage();

    return () => {
      isMounted = false;
      abortController.abort();
      if (imageUrl) {
        URL.revokeObjectURL(imageUrl);
      }
    };
  }, [previewUrl, token, size]);

  return (
    <div
      className={`bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden ${className}`}
    >
      {error || !previewUrl ? (
        <div className="w-full h-full flex items-center justify-center">
          <div className="text-center">
            <div className="text-4xl mb-2">📄</div>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Preview not available
            </span>
          </div>
        </div>
      ) : imageUrl ? (
        <img
          src={imageUrl}
          alt={`Preview of ${filename}`}
          onError={() => setError(true)}
          className={`w-full h-full ${
            size === "thumbnail"
              ? "object-cover"
              : "object-contain max-h-[calc(90vh-220px)]"
          }`}
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center">
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Loading preview...
          </div>
        </div>
      )}
    </div>
  );
}
