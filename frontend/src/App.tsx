import { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthProvider";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { Dashboard } from "./pages/Dashboard";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { ThemeProvider } from "./contexts/ThemeProvider";
import "./App.css";
import { ChatbotPage } from "./pages/ChatbotPage";
import { DashboardFiltersProvider } from "./contexts/DashboardFiltersProvider";
import { useChatbotPolling } from "./hooks/useChatbotPolling";
import { AppContextProvider, Status } from "./contexts/AppContext";

export default function App() {
  return (
    <ThemeProvider>
      <div className="min-h-screen transition-colors duration-200">
        <BrowserRouter>
          <AuthProvider>
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="*" element={<AppRouter />} />
              </Routes>
          </AuthProvider>
        </BrowserRouter>
      </div>
    </ThemeProvider>
  );
}

function AppRouter() {
  const [pollTaskId, setPollTaskId] = useState<string | null>(null);
  const [chatbotStatus, setChatbotStatus] = useState<Status>("idle");

  useChatbotPolling(pollTaskId, setChatbotStatus, (data) => {
    const currentHistory = JSON.parse(localStorage.getItem("chatbotHistory") || "[]");
    const newMessage = {
      id: crypto.randomUUID(),
      position: currentHistory.length,
      role: "assistant",
      content: data.answer,
      sources: data.sources,
    };
    const updatedHistory = [...currentHistory, newMessage];
    localStorage.setItem("chatbotHistory", JSON.stringify(updatedHistory));
  });

  return (
    <AppContextProvider setPollTaskId={setPollTaskId} chatbotStatus={chatbotStatus} setChatbotStatus={setChatbotStatus}>
      <DashboardFiltersProvider>
      <ProtectedRoute>
        <Routes>
          <Route path="/dashboard/*" element={<Dashboard />} />
          <Route path="/chatbot" element={<ChatbotPage />} />

          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </ProtectedRoute>
      </DashboardFiltersProvider>
    </AppContextProvider>
  );
}
