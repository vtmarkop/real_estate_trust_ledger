import { createContext, useContext, useState, useEffect } from 'react';
import api from '../api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    // Βάζουμε ένα ασφαλές default
    const [viewMode, setViewMode] = useState(localStorage.getItem('viewMode') || 'tenant');

    const checkAuth = async () => {
        try {
            const response = await api.get('/auth/me');
            const userData = response.data;
            setUser(userData);
            
            // --- ΑΥΣΤΗΡΟΣ ΕΛΕΓΧΟΣ ΡΟΛΟΥ ---
            if (userData.role === 'tenant') {
                // Αν είναι ενοικιαστής στη βάση, το καρφώνουμε σε tenant mode.
                setViewMode('tenant');
                localStorage.setItem('viewMode', 'tenant');
            } else {
                // Αν είναι ιδιοκτήτης, διαβάζουμε τι είχε διαλέξει (ή βάζουμε default landlord)
                const savedMode = localStorage.getItem('viewMode');
                if (!savedMode || savedMode === 'undefined') {
                    setViewMode('landlord');
                    localStorage.setItem('viewMode', 'landlord');
                } else {
                    setViewMode(savedMode);
                }
            }
        } catch (error) {
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    // Η αλλαγή ρόλου επιτρέπεται ΜΟΝΟ στους ιδιοκτήτες
    const switchViewMode = (mode) => {
        if (user?.role === 'landlord') {
            setViewMode(mode);
            localStorage.setItem('viewMode', mode);
        }
    };

    useEffect(() => {
        checkAuth();
    }, []);

    const login = async (email, password) => {
        const params = new URLSearchParams();
        params.append('username', email);
        params.append('password', password);

        try {
            await api.post('/auth/login', params, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            });
            await new Promise(resolve => setTimeout(resolve, 100));
            await checkAuth(); 
        } catch (error) {
            throw error;
        }
    };

    const logout = async () => {
        await api.post('/auth/logout');
        setUser(null);
        localStorage.removeItem('viewMode');
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, logout, viewMode, switchViewMode }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);