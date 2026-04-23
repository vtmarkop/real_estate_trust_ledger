import { useEffect, useState } from 'react';
import api from '../../api';
import DashboardLayout from '../../components/layout/DashboardLayout';
import { useAuth } from '../../context/AuthContext';

const Dashboard = () => {
    // 1. Παίρνουμε το viewMode
    const { viewMode } = useAuth(); 
    const [stats, setStats] = useState({ total_properties: 0, active_tickets: 0, wallet_balance: 0, recent_tickets: [] });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                setLoading(true);
                // 2. Περνάμε το viewMode στο URL!
                const res = await api.get(`/dashboard/summary?mode=${viewMode}`);
                setStats(res.data);
            } catch (err) { 
                console.error(err); 
            } finally { 
                setLoading(false); 
            }
        };
        fetchStats();
    }, [viewMode]); // 3. Το useEffect "ακούει" το viewMode. Αν αλλάξει, ξανατρέχει!

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <h1 className="text-3xl font-black text-slate-800 tracking-tight">Επισκόπηση</h1>
                
                {loading ? (
                    <div className="animate-pulse flex space-x-4">Φόρτωση δεδομένων...</div>
                ) : (
                    <>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                                <p className="text-slate-500 text-xs font-bold uppercase tracking-wider">
                                    {viewMode === 'landlord' ? 'Ενεργά Ακίνητα' : 'Σπίτια που νοικιάζω'}
                                </p>
                                <p className="text-4xl font-black mt-2">{stats.total_properties}</p>
                            </div>
                            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                                <p className="text-slate-500 text-xs font-bold uppercase tracking-wider">Εκκρεμή Αιτήματα</p>
                                <p className="text-4xl font-black text-orange-500 mt-2">{stats.active_tickets}</p>
                            </div>
                            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                                <p className="text-slate-500 text-xs font-bold uppercase tracking-wider">Υπόλοιπο Πορτοφολιού</p>
                                <p className="text-4xl font-black text-green-600 mt-2">€{stats.wallet_balance.toFixed(2)}</p>
                            </div>
                        </div>

                        {/* Πρόσφατη Δραστηριότητα */}
                        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm mt-8">
                            <div className="p-4 border-b border-slate-100 font-bold text-slate-800 uppercase text-xs tracking-widest">
                                Πρόσφατα Αιτήματα
                            </div>
                            <div className="divide-y divide-slate-100">
                                {stats.recent_tickets.length > 0 ? stats.recent_tickets.map(t => (
                                    <div key={t.id} className="p-4 text-sm flex justify-between items-center hover:bg-slate-50 transition-colors">
                                        <span className="font-bold text-slate-700">{t.title}</span>
                                        <span className="text-[10px] font-black uppercase px-2 py-1 bg-blue-50 text-blue-600 rounded">{t.status}</span>
                                    </div>
                                )) : <div className="p-8 text-center text-slate-400 italic">Δεν υπάρχουν πρόσφατα αιτήματα.</div>}
                            </div>
                        </div>
                    </>
                )}
            </div>
        </DashboardLayout>
    );
};

export default Dashboard;