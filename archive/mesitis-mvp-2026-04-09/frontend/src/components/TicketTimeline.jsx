import { useEffect, useState } from 'react';
import api from '../api';

const TicketTimeline = ({ ticketId }) => {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchTimeline = async () => {
            try {
                const res = await api.get(`/tickets/${ticketId}/timeline`);
                setHistory(res.data);
            } catch (err) {
                console.error("Σφάλμα ιστορικού:", err);
            } finally {
                setLoading(false);
            }
        };
        if (ticketId) fetchTimeline();
    }, [ticketId]);

    if (loading) return <div className="text-xs animate-pulse">Φόρτωση ιστορικού...</div>;
    if (history.length === 0) return <div className="text-xs text-slate-400 italic">Δεν υπάρχουν δικαστικές αποφάσεις ακόμα.</div>;

    return (
        <div className="mt-4 space-y-3">
            <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest border-b pb-1">
                Ιστορικό Αποφάσεων Διαιτησίας
            </h4>
            <div className="relative border-l-2 border-purple-100 ml-2 pl-4 space-y-4">
                {history.map((entry) => (
                    <div key={entry.id} className="relative">
                        {/* Κουκκίδα timeline */}
                        <div className="absolute -left-[21px] top-1 w-3 h-3 bg-purple-500 rounded-full border-2 border-white"></div>
                        
                        <div className="text-[11px]">
                            <div className="flex justify-between items-start">
                                <span className="font-bold text-slate-700">
                                    {entry.amount > 0 ? '✅ Αποκατάσταση' : '⚠️ Ποινή'} στο Score
                                </span>
                                <span className="text-slate-400 text-[9px]">
                                    {new Date(entry.created_at).toLocaleString('el-GR')}
                                </span>
                            </div>
                            <p className="text-purple-600 font-black mt-0.5">
                                {entry.amount > 0 ? `+${entry.amount}` : entry.amount} πόντοι στον {entry.user_name}
                            </p>
                            <p className="text-slate-500 mt-1 italic leading-tight">
                                "{entry.reason}"
                            </p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default TicketTimeline;