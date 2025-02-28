import { useState, useEffect } from "react";
import { API_BASE_URL } from "../config/api";
import { useAuth } from "@/hooks/useAuth";

interface DocumentPreviewProps {
  previewUrl: string;
  filename: string;
}

const CACHE_NAME = "document-previews-v1";

async function getCachedImage(
  url: string,
  token: string
): Promise<Blob | null> {
  try {
    const cache = await caches.open(CACHE_NAME);
    const request = new Request(url, {
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
        const cachedBlob = await getCachedImage(fullUrl, token);

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
  }, [previewUrl, token]);

  return (
    <div className="aspect-square w-full bg-gray-100 rounded-t-lg overflow-hidden">
      {error || !previewUrl ? (
        <div className="w-full h-full flex items-center justify-center">
          <div className="text-center">
            <div className="text-4xl mb-2">📄</div>
            <span className="text-sm text-gray-500">Preview not available</span>
          </div>
        </div>
      ) : imageUrl ? (
        <img
          src={imageUrl}
          alt={`Preview of ${filename}`}
          onError={() => setError(true)}
          className="w-full h-full object-cover"
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center">
          <div className="text-sm text-gray-500">Loading preview...</div>
        </div>
      )}
    </div>
  );
}
