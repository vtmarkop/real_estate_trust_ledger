import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/auth/Login';
import DashboardLayout from './components/layout/DashboardLayout';
import Properties from './pages/landlord/Properties';
import Tickets from './pages/landlord/Tickets';
import Dashboard from './pages/landlord/Dashboard';
import Payments from './pages/Payments';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  console.log("Auth State:", { user, loading });

  if (loading) {
      return (
          <div className="min-h-screen flex items-center justify-center bg-slate-100">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <span className="ml-3 text-slate-600 font-medium">Επαλήθευση ασφαλείας...</span>
          </div>
      );
  }
  
  if (!user) return <Navigate to="/login" replace />;
  
  return children;
};

function App() {
    return (
        <AuthProvider>
            <Router>
                <Routes>
                    <Route path="/login" element={<Login />} />
                    
                    {/* Η Αρχική Σελίδα (Dashboard) - ΤΩΡΑ ΕΙΝΑΙ ΜΟΝΟ ΜΙΑ ΚΑΙ ΣΩΣΤΗ */}
                    <Route path="/" element={
                        <ProtectedRoute>
                            <Dashboard />
                        </ProtectedRoute>
                    } />

                    {/* Ακίνητα */}
                    <Route path="/properties" element={
                        <ProtectedRoute>
                            <Properties />
                        </ProtectedRoute>
                    } />

                    {/* Αιτήματα */}
                    <Route path="/tickets" element={
                        <ProtectedRoute>
                            <Tickets />
                        </ProtectedRoute>
                    } />

                    <Route path="/payments" element={
                        <ProtectedRoute>
                            <Payments />
                        </ProtectedRoute>
                    } />

                </Routes>
            </Router>
        </AuthProvider>
    );
}

export default App;