import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Books from './pages/Books';
import BorrowedBooks from './pages/BorrowedBooks';
import Recommendations from './pages/Recommendations';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <>
      <Navbar />
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        {/* Protected routes */}
        <Route path="/books" element={<ProtectedRoute><Books /></ProtectedRoute>}/>
        <Route path="/my-borrows" element={<ProtectedRoute><BorrowedBooks /></ProtectedRoute> }/>
        <Route path="/recommendations" element={<ProtectedRoute><Recommendations /></ProtectedRoute> } />
        <Route  path="*"  element={localStorage.getItem('access_token') ? <Navigate to="/books" /> : <Navigate to="/login" />  }/>
      </Routes>
    </>
  );
}

export default App;
