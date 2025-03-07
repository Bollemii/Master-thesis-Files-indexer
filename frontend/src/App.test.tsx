import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/dom";
import App from "./App";

// Mock the router components to avoid actual navigation
vi.mock("react-router-dom", () => {
  return {
    BrowserRouter: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="browser-router">{children}</div>
    ),
    Routes: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="routes">{children}</div>
    ),
    Route: ({ path, element }: { path: string; element: React.ReactNode }) => (
      <div data-testid={`route-${path}`} data-path={path}>
        {element}
      </div>
    ),
    Navigate: ({ to }: { to: string; replace?: boolean }) => (
      <div data-testid={`navigate-${to}`} data-to={to}>
        Navigate to {to}
      </div>
    ),
  };
});

// Mock providers to check their presence
vi.mock("./contexts/AuthProvider", () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="auth-provider">{children}</div>
  ),
}));

vi.mock("./components/ThemeProvider", () => ({
  ThemeProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="theme-provider">{children}</div>
  ),
}));

// Mock the pages
vi.mock("./pages/Login", () => ({
  Login: () => <div data-testid="login-page">Login Page</div>,
}));

vi.mock("./pages/Register", () => ({
  Register: () => <div data-testid="register-page">Register Page</div>,
}));

vi.mock("./pages/Dashboard", () => ({
  Dashboard: () => <div data-testid="dashboard-page">Dashboard Page</div>,
}));

// Mock ProtectedRoute
vi.mock("./components/ProtectedRoute", () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="protected-route">{children}</div>
  ),
}));

describe("App Component", () => {
  it("renders without crashing", () => {
    render(<App />);
    expect(document.body).toBeTruthy();
  });

  it("includes the necessary providers", () => {
    render(<App />);
    expect(screen.getByTestId("theme-provider")).toBeTruthy();
    expect(screen.getByTestId("browser-router")).toBeTruthy();
    expect(screen.getByTestId("auth-provider")).toBeTruthy();
  });

  it("renders routes correctly", () => {
    // We can't easily test actual routing with BrowserRouter
    // so we test that Routes and Route components are used with the right structure
    const { container } = render(<App />);
    // Check that routes structure exists
    expect(container.innerHTML).toContain('path="/login"');
    expect(container.innerHTML).toContain('path="/register"');
    expect(container.innerHTML).toContain('path="/dashboard/*"');
    expect(container.innerHTML).toContain('path="/"');
  });

  it("wraps Dashboard route with ProtectedRoute", () => {
    render(<App />);
    // Check that the dashboard is wrapped by a protected route
    const protectedRoute = screen.getByTestId("protected-route");
    expect(protectedRoute).toBeTruthy();
    // The dashboard should be inside the protected route
    expect(protectedRoute.innerHTML).toContain("dashboard-page");
  });

  it("redirects root path to dashboard", () => {
    render(<App />);
    // This tests that a Navigate component pointing to "/dashboard" is used for the "/" route
    const navigateElement = screen.getByTestId("navigate-/dashboard");
    expect(navigateElement).toBeTruthy();
    expect(navigateElement.getAttribute("data-to")).toBe("/dashboard");
  });
});
