import React, { useState, useEffect } from "react";
import { X, Edit, Upload } from "lucide-react";
import { Document } from "../types/api";
import { fetchWithAuth } from "../services/api";

interface UpdateDocumentModalProps {
  document: Document;
  token: string;
  isOpen: boolean;
  onClose: () => void;
  onDocumentUpdated: (updatedDocument: Document) => void;
}

export function UpdateDocumentModal({
  document,
  token,
  isOpen,
  onClose,
  onDocumentUpdated,
}: UpdateDocumentModalProps) {
  const [newFilename, setNewFilename] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState("");

  useEffect(() => {
    if (document) {
      setNewFilename(document.filename);
    }
  }, [document]);

  useEffect(() => {
    if (!isOpen) {
      setSelectedFile(null);
      setUpdateError("");
    }
  }, [isOpen]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleSubmitUpdate = async () => {
    setIsUpdating(true);
    setUpdateError("");

    try {
      let wasUpdated = false;

      if (newFilename !== document.filename) {
        await fetchWithAuth(`/documents/${document.id}/name`, token, {
          method: "PUT",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: new URLSearchParams({ name: newFilename }).toString(),
        });
        wasUpdated = true;
      }

      if (selectedFile) {
        const formData = new FormData();
        formData.append("file", selectedFile);

        await fetchWithAuth(`/documents/${document.id}`, token, {
          method: "PUT",
          body: formData,
        });
        wasUpdated = true;
      }

      if (wasUpdated) {
        const updatedDocument = await fetchWithAuth(
          `/documents/${document.id}`,
          token
        );
        onDocumentUpdated(updatedDocument);
      }

      onClose();
    } catch (error) {
      console.error("Failed to update document:", error);
      setUpdateError("Failed to update document. Please try again.");
    } finally {
      setIsUpdating(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium dark:text-white">
            Update Document
          </h3>
          <button
            onClick={onClose}
            className="cursor-pointer text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            aria-label="Close dialog"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {updateError && (
          <div className="mb-4 p-2 bg-red-100 text-red-700 rounded-md text-sm">
            {updateError}
          </div>
        )}

        <div className="space-y-4">
          {/* Filename input */}
          <div>
            <label
              htmlFor="filename"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Document Name
            </label>
            <div className="flex">
              <span className="inline-flex items-center px-3 rounded-l-md border border-r-0 border-gray-300 bg-gray-50 dark:bg-gray-700 dark:border-gray-600 text-gray-500 dark:text-gray-400">
                <Edit className="h-4 w-4" />
              </span>
              <input
                type="text"
                id="filename"
                value={newFilename}
                onChange={(e) => setNewFilename(e.target.value)}
                className="flex-1 min-w-0 block w-full px-3 py-2 rounded-none rounded-r-md border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          </div>

          {/* File upload */}
          <div>
            <label
              htmlFor="file"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Replace Document Content (Optional)
            </label>
            <div className="flex items-center justify-center w-full">
              <label
                htmlFor="file"
                className="flex flex-col items-center justify-center w-full h-24 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 dark:bg-gray-700 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600"
              >
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <Upload className="w-8 h-8 mb-1 text-gray-500 dark:text-gray-400" />
                  <p className="mb-1 text-sm text-gray-500 dark:text-gray-400">
                    {selectedFile
                      ? selectedFile.name
                      : "Click to upload or drag and drop"}
                  </p>
                </div>
                <input
                  id="file"
                  type="file"
                  className="hidden"
                  onChange={handleFileChange}
                />
              </label>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-3">
            <button
              type="button"
              onClick={onClose}
              className="cursor-pointer px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600 rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSubmitUpdate}
              disabled={isUpdating}
              className="cursor-pointer px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isUpdating ? "Updating..." : "Update Document"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
