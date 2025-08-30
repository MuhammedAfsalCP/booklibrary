import { Link } from 'react-router-dom';
import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';

export default function Navbar() {
  const { user, logout } = useContext(AuthContext);

  return (
    <nav className="bg-gray-800 text-white p-4 flex justify-between items-center shadow-md">
      <div className="space-x-6">
        {user && (
          <>
            <Link to="/books" className="hover:text-gray-300 transition-colors duration-200">Books</Link>
            <Link to="/my-borrows" className="hover:text-gray-300 transition-colors duration-200">My Borrows</Link>
            <Link to="/recommendations" className="hover:text-gray-300 transition-colors duration-200">Recommendations</Link>
          </>
        )}
      </div>
      <div className="flex items-center space-x-4">
        {user ? (
          <button
            onClick={logout}
            className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors duration-200"
          >
            Logout
          </button>
        ) : (
          <>
            <Link to="/login" className="hover:text-gray-300 transition-colors duration-200">Login</Link>
            <Link to="/register" className="hover:text-gray-300 transition-colors duration-200">Register</Link>
          </>
        )}
      </div>
    </nav>
  );
}