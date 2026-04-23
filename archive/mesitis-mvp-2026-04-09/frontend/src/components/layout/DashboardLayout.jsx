import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import api from '../../api';

const DashboardLayout = ({ children }) => {
    const { user, logout, viewMode, switchViewMode } = useAuth();
    const navigate = useNavigate();

    // States για το Score History Modal
    const [isScoreModalOpen, setIsScoreModalOpen] = useState(false);
    const [scoreHistory, setScoreHistory] = useState([]);
    const [loadingHistory, setLoadingHistory] = useState(false);

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    // Συνάρτηση που φέρνει το ιστορικό πόντων
    const openScoreHistory = async () => {
        if (user?.role === 'judge') return; // Ο δικαστής δεν έχει score ιστορικό
        setIsScoreModalOpen(true);
        setLoadingHistory(true);
        try {
            const res = await api.get('/auth/me/score-history');
            setScoreHistory(res.data);
        } catch (error) {
            console.error("Αποτυχία φόρτωσης ιστορικού σκορ:", error);
        } finally {
            setLoadingHistory(false);
        }
    };

    // --- ΛΟΓΙΚΗ ΕΠΙΛΟΓΗΣ ΣΚΟΡ ΒΑΣΕΙ VIEW MODE ---
    // Αν είμαστε σε landlord mode δείχνουμε το landlord_score, αλλιώς το tenant_score
    const displayScore = viewMode === 'landlord' ? user?.landlord_score : user?.tenant_score;

    return (
        <div className="flex h-screen bg-slate-50 overflow-hidden">
            {/* Sidebar */}
            <aside className="w-64 bg-slate-900 text-white flex flex-col shadow-xl z-20">
                <div className="p-6 text-2xl font-bold border-b border-slate-800 text-blue-400 tracking-tight">
                    Mesitis App
                </div>
                
                <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
                    <Link to="/" className="flex items-center space-x-3 p-3 rounded-lg hover:bg-slate-800 transition-colors group">
                        <span className="text-slate-400 group-hover:text-white">🏠</span>
                        <span className="font-medium">Ταμπλό</span>
                    </Link>
                    <Link to="/properties" className="flex items-center space-x-3 p-3 rounded-lg hover:bg-slate-800 transition-colors group">
                        <span className="text-slate-400 group-hover:text-white">🏢</span>
                        <span className="font-medium">Ακίνητα</span>
                    </Link>
                    <Link to="/tickets" className="flex items-center space-x-3 p-3 rounded-lg hover:bg-slate-800 transition-colors group">
                        <span className="text-slate-400 group-hover:text-white">🎫</span>
                        <span className="font-medium">Αιτήματα</span>
                    </Link>
                    <Link to="/payments" className="flex items-center space-x-3 p-3 rounded-lg hover:bg-slate-800 transition-colors group">
                        <span className="text-slate-400 group-hover:text-white">💳</span>
                        <span className="font-medium">Οικονομικά</span>
                    </Link>
                </nav>

                {/* --- ΔΙΑΚΟΠΤΗΣ ΡΟΛΟΥ: ΟΡΑΤΟΣ ΜΟΝΟ ΣΤΟΥΣ ΙΔΙΟΚΤΗΤΕΣ --- */}
                {user?.role === 'landlord' && (
                    <div className="px-4 py-4 border-t border-slate-800 bg-slate-900/50">
                        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3 px-2">
                            Προβολή ως
                        </p>
                        <div className="flex bg-slate-950 rounded-xl p-1 border border-slate-800">
                            <button
                                onClick={() => switchViewMode('landlord')}
                                className={`flex-1 py-2 text-[11px] font-black rounded-lg transition-all ${
                                    viewMode === 'landlord' 
                                    ? 'bg-blue-600 text-white shadow-lg' 
                                    : 'text-slate-500 hover:text-slate-300'
                                }`}
                            >
                                ΙΔΙΟΚΤΗΤΗΣ
                            </button>
                            <button
                                onClick={() => switchViewMode('tenant')}
                                className={`flex-1 py-2 text-[11px] font-black rounded-lg transition-all ${
                                    viewMode === 'tenant' 
                                    ? 'bg-orange-600 text-white shadow-lg' 
                                    : 'text-slate-500 hover:text-slate-300'
                                }`}
                            >
                                ΕΝΟΙΚΙΑΣΤΗΣ
                            </button>
                        </div>
                    </div>
                )}

                <div className="p-4 border-t border-slate-800">
                    <button 
                        onClick={handleLogout}
                        className="w-full flex items-center space-x-3 p-3 text-red-400 hover:bg-red-900/20 rounded-lg transition-all"
                    >
                        <span>🚪</span>
                        <span className="font-semibold">Αποσύνδεση</span>
                    </button>
                </div>
            </aside>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col relative">
                <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 shadow-sm z-10">
                    <div className="text-slate-400 font-medium italic text-sm">
                        Real Estate Dispute Resolution System
                    </div>
                    
                    <div className="flex items-center space-x-4">
                        {/* --- ΒΑΘΜΟΛΟΓΙΑ (TRUST SCORE) - Clickable & Dynamic --- */}
                        {user?.role !== 'judge' && (
                            <button 
                                onClick={openScoreHistory}
                                className="hidden sm:flex items-center space-x-2 mr-2 bg-slate-100 hover:bg-slate-200 transition-colors px-3 py-1.5 rounded-xl border border-slate-200 shadow-inner group" 
                                title={`Ιστορικό εμπιστοσύνης ως ${viewMode === 'landlord' ? 'Ιδιοκτήτης' : 'Ενοικιαστής'}`}
                            >
                                <span className="text-yellow-500 text-lg leading-none group-hover:scale-110 transition-transform">⭐</span>
                                <span className="font-black text-slate-700">
                                    {displayScore?.toFixed(1) ?? "100.0"}/100
                                </span>
                            </button>
                        )}

                        <div className="text-right mr-2">
                            <p className="text-sm font-bold text-slate-800 leading-none">
                                {user?.full_name || 'Χρήστης'}
                            </p>
                            
                            {/* Ταμπελάκια Ρόλων */}
                            {user?.role === 'judge' ? (
                                <p className="text-[10px] font-black uppercase tracking-widest mt-1.5 px-2 py-0.5 rounded-md inline-block text-purple-600 bg-purple-50">
                                    ⚖️ Δικαστής
                                </p>
                            ) : user?.role === 'landlord' ? (
                                <p className={`text-[10px] font-black uppercase tracking-widest mt-1.5 px-2 py-0.5 rounded-md inline-block ${
                                    viewMode === 'landlord' ? 'text-blue-600 bg-blue-50' : 'text-orange-600 bg-orange-50'
                                }`}>
                                    {viewMode === 'landlord' ? 'Landlord Mode' : 'Tenant Mode'}
                                </p>
                            ) : (
                                <p className="text-[10px] font-black uppercase tracking-widest mt-1.5 px-2 py-0.5 rounded-md inline-block text-orange-600 bg-orange-50">
                                    Ενοικιαστής
                                </p>
                            )}
                        </div>

                        <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold shadow-md transition-colors ${
                             user?.role === 'judge' ? 'bg-gradient-to-br from-purple-500 to-indigo-700' :
                             viewMode === 'landlord' ? 'bg-gradient-to-br from-blue-500 to-indigo-600' : 
                             'bg-gradient-to-br from-orange-500 to-red-600'
                        }`}>
                            {user?.full_name?.[0]?.toUpperCase() || 'U'}
                        </div>
                    </div>
                </header>

                <main className="flex-1 overflow-y-auto p-8 bg-slate-50/50">
                    <div className="max-w-7xl mx-auto">
                        {children}
                    </div>
                </main>
            </div>

            {/* --- MODAL ΙΣΤΟΡΙΚΟΥ ΒΑΘΜΟΛΟΓΙΑΣ --- */}
            {isScoreModalOpen && (
                <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-[100] p-4">
                    <div className="bg-white rounded-3xl w-full max-w-lg shadow-2xl flex flex-col max-h-[85vh] animate-in fade-in zoom-in duration-200">
                        <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50/50 rounded-t-3xl">
                            <div>
                                <h2 className="text-xl font-black text-slate-800 flex items-center gap-2">
                                    <span className="text-2xl">⭐</span> Ιστορικό Εμπιστοσύνης
                                </h2>
                                <p className="text-xs text-slate-500 mt-1 uppercase tracking-wider font-bold">
                                    Σκορ ως {viewMode === 'landlord' ? 'Ιδιοκτήτης' : 'Ενοικιαστής'}: <span className="text-slate-900">{displayScore?.toFixed(1)}/100.0</span>
                                </p>
                            </div>
                            <button 
                                onClick={() => setIsScoreModalOpen(false)} 
                                className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-slate-200 text-slate-400 transition-colors text-2xl"
                            >
                                &times;
                            </button>
                        </div>
                        
                        <div className="p-6 overflow-y-auto flex-1">
                            {loadingHistory ? (
                                <div className="space-y-4 py-10">
                                    <div className="h-12 bg-slate-100 rounded-xl animate-pulse"></div>
                                    <div className="h-12 bg-slate-100 rounded-xl animate-pulse w-3/4"></div>
                                </div>
                            ) : scoreHistory.length > 0 ? (
                                <div className="space-y-4">
                                    {scoreHistory.map((item, index) => (
                                        <div key={index} className="flex items-start gap-4 p-4 border border-slate-100 rounded-2xl bg-white hover:border-blue-100 transition-colors">
                                            <div className={`shrink-0 flex items-center justify-center w-12 h-12 rounded-2xl font-black text-sm shadow-sm ${
                                                item.amount_changed > 0 ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'
                                            }`}>
                                                {item.amount_changed > 0 ? '+' : ''}{item.amount_changed.toFixed(1)}
                                            </div>
                                            <div className="flex-1">
                                                <p className="text-sm font-bold text-slate-800 leading-tight">{item.reason}</p>
                                                <div className="flex items-center gap-3 mt-2">
                                                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">
                                                        📅 {new Date(item.created_at).toLocaleDateString('el-GR', { day: '2-digit', month: 'short', year: 'numeric' })}
                                                    </span>
                                                    {item.reference_id && (
                                                        <span className="text-[9px] bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full font-mono font-bold">
                                                            Ticket ID: {item.reference_id.substring(0,8)}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-16">
                                    <div className="text-5xl mb-4 grayscale">🏆</div>
                                    <h3 className="font-black text-slate-800 text-lg">Πεντακάθαρο Μητρώο!</h3>
                                    <p className="text-sm text-slate-500 mt-2 max-w-[250px] mx-auto">
                                        Δεν υπάρχουν καταγεγραμμένες ποινές για αυτόν τον ρόλο. Συνεχίστε έτσι!
                                    </p>
                                </div>
                            )}
                        </div>
                        
                        <div className="p-4 bg-slate-50 border-t border-slate-100 rounded-b-3xl text-center">
                            <button 
                                onClick={() => setIsScoreModalOpen(false)} 
                                className="px-8 py-2.5 bg-slate-900 text-white text-sm font-bold rounded-xl hover:bg-slate-800 transition-all shadow-lg"
                            >
                                Κατάλαβα
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DashboardLayout;