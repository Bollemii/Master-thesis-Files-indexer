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

export default function App() {
  return (
    <ThemeProvider>
      <div className="min-h-screen transition-colors duration-200">
        <BrowserRouter>
          <AuthProvider>
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route
                  path="/dashboard/*"
                  element={
                    <ProtectedRoute>
                      <DashboardFiltersProvider>
                        <Dashboard />
                      </DashboardFiltersProvider>
                    </ProtectedRoute>
                  }
                />
                <Route path="/chatbot" element={<ChatbotPage />} />
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
              </Routes>
          </AuthProvider>
        </BrowserRouter>
      </div>
    </ThemeProvider>
  );
}
