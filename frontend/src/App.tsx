import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Home } from "./pages/Home";
import { DocumentDetails } from "./pages/DocumentDetails";
import { Navbar } from "./components/NavBar";

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route
              path="/documents/:documentId"
              element={<DocumentDetails />}
            />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
