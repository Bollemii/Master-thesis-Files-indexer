import { Link } from "react-router-dom";
import { Home as HomeIcon, Search, User } from "lucide-react";

export function Navbar() {
  return (
    <nav className="bg-white shadow">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <Link to="/" className="text-gray-800 hover:text-gray-600">
            <HomeIcon className="h-6 w-6" />
          </Link>

          <div className="flex-1 max-w-lg mx-8">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <input
                name="search"
                type="text"
                placeholder="Search documents..."
                className="w-full rounded-md border border-gray-300 py-2 pl-10 pr-4 focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>

          <div className="text-gray-800">
            <User className="h-6 w-6" />
          </div>
        </div>
      </div>
    </nav>
  );
}
