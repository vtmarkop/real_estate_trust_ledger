import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import api from '../../api';
import DashboardLayout from '../../components/layout/DashboardLayout';
import { useAuth } from '../../context/AuthContext';

const Tickets = () => {
    const [tickets, setTickets] = useState([]);
    const [properties, setProperties] = useState([]);
    const [loading, setLoading] = useState(true);
    
    const [isTicketModalOpen, setIsTicketModalOpen] = useState(false);
    
    const [detailsModalOpen, setDetailsModalOpen] = useState(false);
    const [selectedTicket, setSelectedTicket] = useState(null);
    const [actionComment, setActionComment] = useState('');
    const [actionPenalty, setActionPenalty] = useState(0);
    const [guiltyPartyId, setGuiltyPartyId] = useState('');
    const [actionFiles, setActionFiles] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');

    const { user, viewMode } = useAuth(); 
    const { register, handleSubmit, reset } = useForm();
    const [selectedFiles, setSelectedFiles] = useState([]);

    const openDetailsModal = (ticket) => {
        setSelectedTicket(ticket);
        setActionComment(ticket.arbitration_notes || '');
        setActionPenalty(ticket.score_impact || 0);
        setGuiltyPartyId(ticket.guilty_party_id || '');
        setActionFiles([]);
        setDetailsModalOpen(true);
    };

    const renderTimelineLog = (logLine) => {
        const parts = logLine.split(" 📎 [ΑΡΧΕΙΑ:");
        let textPart = parts[0]; 
        let links = [];
        
        if (parts.length > 1) {
            const urlsStr = parts[1].split("]")[0]; 
            if (urlsStr) {
                links = urlsStr.split(",");
            }
            const extraText = parts[1].substring(parts[1].indexOf("]") + 1);
            if (extraText) textPart += extraText;
        }

        return (
            <div className="flex flex-col gap-1.5">
                <span className="text-slate-700 font-medium">{textPart}</span>
                {links.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-1 relative z-10">
                        {links.map((url, i) => (
                            <a 
                                key={i} href={url} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()} 
                                className="inline-flex items-center gap-1 text-[10px] font-black text-purple-700 bg-purple-100 px-2.5 py-1 rounded hover:bg-purple-200 transition-colors shadow-sm cursor-pointer"
                            >
                                📎 Αρχείο {i + 1}
                            </a>
                        ))}
                    </div>
                )}
            </div>
        );
    };

    const fetchData = async () => {
        try {
            setLoading(true);
            const [tickRes, propRes] = await Promise.all([
                api.get(`/tickets/my-tickets`),
                api.get(`/properties/my-properties?mode=${viewMode}`)
            ]);
            setTickets(tickRes.data);
            setProperties(propRes.data);
        } catch (error) {
            console.error("Σφάλμα ανάκτησης δεδομένων:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchData(); }, [viewMode]);

    const onTicketSubmit = async (data) => {
        try {
            let uploadedUrls = [];
            if (selectedFiles.length > 0) {
                const formData = new FormData();
                selectedFiles.forEach(file => formData.append("files", file));
                const uploadRes = await api.post('/upload/', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
                uploadedUrls = uploadRes.data.urls; 
            }

            await api.post('/tickets/', {
                property_id: data.property_id,
                title: data.title,
                description: data.description,
                priority: data.priority,
                attachment_urls: uploadedUrls 
            });
            
            setIsTicketModalOpen(false);
            setSelectedFiles([]); 
            reset();
            fetchData();
        } catch (error) {
            alert(error.response?.data?.detail || "Υπήρξε πρόβλημα στην καταχώρηση.");
        }
    };

    const getPropertyTitle = (propertyId) => {
        const prop = properties.find(p => p.id === propertyId);
        return prop ? prop.title : 'Άγνωστο Ακίνητο';
    };

    const executeAction = async (newStatus) => {
        if (!selectedTicket) return;
        
        // Tenant Dispute Check
        if (viewMode === 'tenant' && newStatus === 'disputed' && !actionComment.trim()) {
            alert("Η αιτιολόγηση είναι υποχρεωτική για να κάνετε ένσταση.");
            return;
        }

        // Judge Validation
        if (user?.role === 'judge' && !actionComment.trim()) {
            alert("Το σκεπτικό απόφασης είναι υποχρεωτικό για τον Δικαστή.");
            return;
        }

        try {
            let uploadedUrls = [];
            if (actionFiles.length > 0) {
                const formData = new FormData();
                actionFiles.forEach(file => formData.append("files", file));
                const uploadRes = await api.post('/upload/', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
                uploadedUrls = uploadRes.data.urls;
            }

            await api.patch(`/tickets/${selectedTicket.id}/status`, { 
                status: newStatus,
                comment: actionComment,
                new_attachment_urls: uploadedUrls,
                ...(user?.role === 'judge' && {
                    arbitration_notes: actionComment, // Use comment as judge notes
                    score_impact: actionPenalty > 0 ? Math.abs(actionPenalty) : 0, 
                    guilty_party_id: guiltyPartyId || null
                })
            });
            
            setDetailsModalOpen(false);
            setSelectedTicket(null);
            setActionFiles([]); 
            fetchData();
        } catch (error) {
            alert("Σφάλμα: " + (error.response?.data?.detail || "Αποτυχία ενημέρωσης."));
        }
    };

    const getStatusBadge = (status) => {
        const s = typeof status === 'string' ? status.toUpperCase() : (status?.name || 'UNKNOWN');
        switch(s) {
            case 'OPEN': return <span className="inline-flex text-[10px] font-black bg-blue-100 text-blue-700 px-3 py-1.5 rounded uppercase shadow-sm whitespace-nowrap">🆕 Ανοιχτό</span>;
            case 'IN_PROGRESS': return <span className="inline-flex text-[10px] font-black bg-orange-100 text-orange-700 px-3 py-1.5 rounded uppercase shadow-sm whitespace-nowrap">⚙️ Σε Εξέλιξη</span>;
            case 'RESOLVED': return <span className="inline-flex text-[10px] font-black bg-green-100 text-green-700 px-3 py-1.5 rounded uppercase shadow-sm whitespace-nowrap">✅ Επιλύθηκε</span>;
            case 'REJECTED': return <span className="inline-flex text-[10px] font-black bg-red-100 text-red-700 px-3 py-1.5 rounded uppercase shadow-sm whitespace-nowrap">❌ Απορρίφθηκε</span>;
            case 'DISPUTED': return <span className="inline-flex text-[10px] font-black bg-yellow-100 text-yellow-700 px-3 py-1.5 rounded uppercase shadow-sm whitespace-nowrap">⚖️ Υπό Διαιτησία</span>;
            case 'CLOSED': return <span className="inline-flex text-[10px] font-black bg-slate-200 text-slate-700 px-3 py-1.5 rounded uppercase shadow-sm whitespace-nowrap">🔒 Κλειστό</span>;
            default: return <span>{s}</span>;
        }
    };

    const filteredTickets = user?.role === 'judge' ? tickets : tickets.filter(t => {
        const prop = properties.find(p => p.id === t.property_id);
        if (!prop) return false;
        
        const isRoleMatch = viewMode === 'landlord' ? prop.owner_id === user?.id : prop.tenant_id === user?.id;
        const term = searchTerm.toLowerCase();
        const propTitle = prop.title.toLowerCase();
        const desc = (t.description || '').toLowerCase();
        const title = (t.title || '').toLowerCase();
        
        return isRoleMatch && (propTitle.includes(term) || desc.includes(term) || title.includes(term));
    });

    return (
        <DashboardLayout>
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-2xl font-black text-slate-800 tracking-tight">
                        {user?.role === 'judge' ? 'Κέντρο Διαιτησίας' : 'Αιτήματα & Βλάβες'}
                    </h1>
                </div>
                {user?.role !== 'judge' && viewMode === 'tenant' && (
                    <button onClick={() => setIsTicketModalOpen(true)} className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-5 py-2.5 rounded-xl shadow-lg shadow-blue-200 transition-all flex items-center gap-2">
                        <span>➕</span> Νέο Αίτημα
                    </button>
                )}
            </div>

            {loading ? (
                <div className="text-center py-20 text-slate-400 font-bold animate-pulse">Ανάκτηση αιτημάτων...</div>
            ) : (
                <>
                    <div className="mb-4 flex items-center bg-white p-2 rounded-xl border border-slate-200 shadow-sm w-full max-w-md">
                        <span className="pl-3 pr-2 text-slate-400">🔍</span>
                        <input type="text" placeholder="Αναζήτηση..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="w-full bg-transparent outline-none text-sm p-1 font-medium text-slate-700" />
                    </div>
                    
                    <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-widest border-b border-slate-200">
                                        <th className="p-5 font-black">Ακίνητο & Περιγραφή</th>
                                        <th className="p-5 font-black">Προτεραιότητα</th>
                                        <th className="p-5 font-black">Κατάσταση</th>
                                        <th className="p-5 font-black text-right">Ενέργειες</th>
                                    </tr>
                                </thead>
                                <tbody>
                                {filteredTickets.length > 0 ? filteredTickets.map((ticket) => (
                                    <tr key={ticket.id} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                                        <td className="p-5 align-top">
                                            <div className="font-bold text-slate-800 text-sm mb-1">🏢 {getPropertyTitle(ticket.property_id)}</div>
                                            <div className="text-xs font-bold text-slate-700 mt-1">{ticket.title}</div>
                                            <div className="text-xs text-slate-500 mt-1">{ticket.description}</div>
                                            
                                            {Array.isArray(ticket.attachment_urls) && ticket.attachment_urls.length > 0 && (
                                                <div className="flex flex-wrap gap-2 mb-4 mt-2">
                                                    {ticket.attachment_urls.map((url, idx) => (
                                                        <a key={idx} href={url} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()} className="inline-flex items-center gap-1 text-[10px] font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded-md border border-blue-200 relative z-10 shadow-sm">
                                                            📎 Αρχικό Αρχείο {idx + 1}
                                                        </a>
                                                    ))}
                                                </div>
                                            )}
                                            
                                            {ticket.dispute_comment && (
                                                <div className="border-l-2 border-slate-200 ml-2 mt-4 space-y-3 py-1">
                                                    {ticket.dispute_comment.split('||').map((commentLine, index) => {
                                                        const line = commentLine.trim();
                                                        if (!line) return null;
                                                        return (
                                                            <div key={index} className="relative pl-5">
                                                                <div className="absolute -left-[7px] top-1.5 w-3 h-3 bg-purple-400 rounded-full border-2 border-white shadow-sm"></div>
                                                                <div className="bg-white p-2.5 rounded-lg border border-slate-200 shadow-sm text-[11px]">
                                                                    {renderTimelineLog(line)}
                                                                </div>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            )}
                                        </td>
                                        <td className="p-5 align-top">
                                            <div className="font-black text-red-600 uppercase">{ticket.priority}</div>
                                            <div className="text-[10px] text-slate-400 mt-1">{new Date(ticket.created_at).toLocaleDateString('el-GR')}</div>
                                        </td>
                                        <td className="p-5 align-top">{getStatusBadge(ticket.status)}</td>
                                        <td className="p-5 text-right align-top">
                                            {/* --- THE FIXED BUTTON: Using inline-flex and whitespace-nowrap --- */}
                                            <button 
                                                onClick={() => openDetailsModal(ticket)} 
                                                className="inline-flex items-center justify-center gap-1.5 bg-slate-100 text-slate-700 hover:bg-slate-200 px-4 py-2 rounded-xl text-xs font-bold transition-colors shadow-sm whitespace-nowrap"
                                            >
                                                <span>👁️</span>
                                                <span>Λεπτομέρειες</span>
                                            </button>
                                        </td>
                                    </tr>
                                )) : (
                                    <tr><td colSpan="4" className="p-10 text-center text-slate-500">Δεν βρέθηκαν αιτήματα.</td></tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
                </>
            )}

            {/* MODAL ΠΡΟΒΟΛΗΣ & ΕΝΕΡΓΕΙΩΝ ΑΙΤΗΜΑΤΟΣ */}
            {detailsModalOpen && selectedTicket && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-3xl p-8 w-full max-w-2xl shadow-2xl overflow-y-auto max-h-[90vh]">
                        <div className="flex justify-between items-start mb-6 border-b border-slate-100 pb-4">
                            <div>
                                <h2 className="text-2xl font-black text-slate-800">Στοιχεία Αιτήματος</h2>
                                <p className="text-sm text-slate-500 mt-1">Ακίνητο: <strong className="text-slate-700">{getPropertyTitle(selectedTicket.property_id)}</strong></p>
                            </div>
                            <div>{getStatusBadge(selectedTicket.status)}</div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 mb-6 bg-slate-50 p-5 rounded-xl border border-slate-100">
                            <div className="col-span-2">
                                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Τιτλος & Περιγραφη</div>
                                <div className="font-bold text-slate-800 text-base">{selectedTicket.title}</div>
                                <div className="font-medium text-slate-600 text-sm mt-1">{selectedTicket.description}</div>
                            </div>
                            <div>
                                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Προτεραιοτητα</div>
                                <div className="font-black text-red-600 uppercase text-sm">{selectedTicket.priority}</div>
                            </div>
                        </div>

                        {selectedTicket.dispute_comment && (
                            <div className="mb-6">
                                <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-3">Ιστορικό Ενεργειών</h3>
                                <div className="border-l-2 border-slate-200 ml-2 space-y-3 py-1">
                                    {selectedTicket.dispute_comment.split('||').map((commentLine, index) => {
                                        const line = commentLine.trim();
                                        if (!line) return null;
                                        return (
                                            <div key={index} className="relative pl-5">
                                                <div className="absolute -left-[7px] top-1.5 w-3 h-3 bg-purple-400 rounded-full border-2 border-white shadow-sm"></div>
                                                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 shadow-sm text-xs">
                                                    {renderTimelineLog(line)}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        <div className="bg-white border-t border-slate-200 pt-6 mt-4">
                            {(() => {
                                const statusStr = typeof selectedTicket.status === 'string' ? selectedTicket.status.toUpperCase() : (selectedTicket.status?.name || 'UNKNOWN');
                                
                                if (statusStr === 'CLOSED') {
                                    return (
                                        <div className="text-center p-6 bg-slate-50 rounded-3xl border border-slate-100 shadow-sm">
                                            <div className="text-3xl mb-2">🔒</div>
                                            <div className="text-sm font-bold text-slate-700">Η υπόθεση έχει κλείσει οριστικά.</div>
                                            {selectedTicket.arbitration_notes && (
                                                <div className="mt-4 p-4 bg-purple-50 rounded-2xl text-left border border-purple-100 shadow-sm">
                                                    <h4 className="text-[10px] font-black text-purple-600 uppercase tracking-widest mb-1">Αποφαση Διαιτησιας</h4>
                                                    <p className="text-sm text-slate-800 font-medium">{selectedTicket.arbitration_notes}</p>
                                                    {selectedTicket.score_impact > 0 && <div className="mt-2 text-xs font-bold text-red-600 bg-white inline-block px-2 py-1 rounded-md border border-red-100 shadow-sm">⚠️ Ποινή: -{selectedTicket.score_impact} πόντοι</div>}
                                                </div>
                                            )}
                                        </div>
                                    );
                                }

                                const canLandlordAct = viewMode === 'landlord' && user?.role !== 'judge' && (statusStr === 'OPEN' || statusStr === 'IN_PROGRESS');
                                const canTenantAct = viewMode === 'tenant' && user?.role !== 'judge' && (statusStr === 'RESOLVED' || statusStr === 'REJECTED');
                                const canJudgeAct = user?.role === 'judge';

                                if (!canLandlordAct && !canTenantAct && !canJudgeAct) {
                                    return <div className="text-center text-sm text-slate-400 italic">Δεν απαιτείται κάποια ενέργεια από εσάς αυτή τη στιγμή.</div>;
                                }

                                return (
                                    <div className="space-y-5">
                                        <h3 className="text-sm font-black text-slate-800">Ενέργειες / Απάντηση</h3>
                                        
                                        <div>
                                            <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wider">Σχόλιο / Αιτιολόγηση {user?.role === 'judge' || canTenantAct ? '(Υποχρεωτικό)' : ''}</label>
                                            <textarea value={actionComment} onChange={(e) => setActionComment(e.target.value)} rows="3" className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-2xl outline-none text-sm focus:ring-2 focus:ring-blue-500 transition-shadow" placeholder={user?.role === 'judge' ? "Γράψτε το σκεπτικό της απόφασής σας..." : "Προσθέστε το σχόλιό σας..."} />
                                        </div>
                                        <div>
                                            <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wider">Συνημμένα Αρχεία (Προαιρετικό)</label>
                                            <input type="file" multiple onChange={(e) => setActionFiles(Array.from(e.target.files))} className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-2xl text-sm transition-shadow hover:shadow-sm" />
                                        </div>

                                        {canJudgeAct && (
                                            <div className="p-5 bg-purple-50 border border-purple-200 rounded-2xl mt-4 space-y-4 shadow-sm">
                                                <h4 className="text-xs font-black text-purple-700 uppercase tracking-widest flex items-center gap-2"><span>⚖️</span> Επιβολή Ποινής</h4>
                                                <div className="grid grid-cols-2 gap-4">
                                                    <div>
                                                        <label className="block text-[10px] font-bold text-slate-700 mb-1 uppercase tracking-wider">Υπαίτιος</label>
                                                        <select value={guiltyPartyId} onChange={(e) => setGuiltyPartyId(e.target.value)} className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-purple-500 shadow-sm">
                                                            <option value="">Κανένας</option>
                                                            {properties.find(p => p.id === selectedTicket.property_id)?.owner_id && <option value={properties.find(p => p.id === selectedTicket.property_id).owner_id}>Ιδιοκτήτης</option>}
                                                            {properties.find(p => p.id === selectedTicket.property_id)?.tenant_id && <option value={properties.find(p => p.id === selectedTicket.property_id).tenant_id}>Ενοικιαστής</option>}
                                                        </select>
                                                    </div>
                                                    <div>
                                                        <label className="block text-[10px] font-bold text-red-600 mb-1 uppercase tracking-wider">Αφαίρεση Πόντων</label>
                                                        <input type="number" min="0" value={actionPenalty} onChange={(e) => setActionPenalty(parseInt(e.target.value) || 0)} className="w-full px-4 py-2.5 bg-white border border-red-200 rounded-xl outline-none font-black text-red-700 focus:ring-2 focus:ring-red-500 shadow-sm" />
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        <div className="flex flex-col sm:flex-row gap-3 pt-2">
                                            {canLandlordAct && (
                                                <>
                                                    <button onClick={() => executeAction('rejected')} className="flex-1 bg-red-500 hover:bg-red-600 text-white font-black py-3.5 rounded-2xl shadow-lg shadow-red-200 transition-all">Απόρριψη</button>
                                                    {statusStr === 'OPEN' && (
                                                        <button onClick={() => executeAction('in_progress')} className="flex-1 bg-orange-500 hover:bg-orange-600 text-white font-black py-3.5 rounded-2xl shadow-lg shadow-orange-200 transition-all">Σε Εξέλιξη</button>
                                                    )}
                                                    <button onClick={() => executeAction('resolved')} className="flex-1 bg-green-500 hover:bg-green-600 text-white font-black py-3.5 rounded-2xl shadow-lg shadow-green-200 transition-all">Επίλυση</button>
                                                </>
                                            )}
                                            {canTenantAct && (
                                                <button onClick={() => executeAction('disputed')} className="flex-1 bg-amber-500 hover:bg-amber-600 text-white font-black py-3.5 rounded-2xl shadow-lg shadow-amber-200 transition-all text-sm">Άνοιγμα Ένστασης (Διαιτησία)</button>
                                            )}
                                            {canJudgeAct && (
                                                <>
                                                    {statusStr !== 'RESOLVED' && <button onClick={() => executeAction('resolved')} className="flex-1 bg-green-500 hover:bg-green-600 text-white font-black py-3.5 rounded-2xl shadow-lg shadow-green-200 transition-all">Επίλυση Υπόθεσης</button>}
                                                    <button onClick={() => executeAction('closed')} className="flex-1 bg-purple-600 hover:bg-purple-700 text-white font-black py-3.5 rounded-2xl shadow-lg shadow-purple-200 transition-all">Οριστικό Κλείσιμο</button>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                );
                            })()}
                        </div>

                        <div className="mt-6 pt-4 border-t border-slate-100 text-right">
                            <button onClick={() => { setDetailsModalOpen(false); setSelectedTicket(null); }} className="px-6 py-2.5 bg-slate-100 text-slate-600 font-bold hover:bg-slate-200 rounded-xl transition-colors">Κλείσιμο</button>
                        </div>
                    </div>
                </div>
            )}

            {/* MODAL ΔΗΜΙΟΥΡΓΙΑΣ ΝΕΟΥ ΑΙΤΗΜΑΤΟΣ */}
            {isTicketModalOpen && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-3xl p-8 w-full max-w-md shadow-2xl overflow-y-auto max-h-[90vh]">
                        <h2 className="text-2xl font-black text-slate-800 mb-6">Νέο Αίτημα / Βλάβη</h2>
                        <form onSubmit={handleSubmit(onTicketSubmit)} className="space-y-5">
                            <div>
                                <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wider">Ακίνητο</label>
                                <select {...register("property_id", { required: "Επιλέξτε ακίνητο" })} className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl outline-none font-medium transition-shadow hover:shadow-sm focus:ring-2 focus:ring-blue-100">
                                    <option value="">Επιλέξτε ακίνητο...</option>
                                    {properties.filter(p => viewMode === 'landlord' ? p.owner_id === user?.id : p.tenant_id === user?.id).map(p => (
                                        <option key={p.id} value={p.id}>{p.title}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wider">Τίτλος</label>
                                <input type="text" {...register("title", { required: true })} className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl font-medium outline-none text-sm transition-shadow hover:shadow-sm focus:ring-2 focus:ring-blue-100" placeholder="π.χ. Διαρροή σωλήνα" />
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wider">Περιγραφή</label>
                                <textarea {...register("description", { required: true })} rows="3" className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl font-medium outline-none text-sm transition-shadow hover:shadow-sm focus:ring-2 focus:ring-blue-100" placeholder="Περιγράψτε το ζήτημα..."></textarea>
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wider">Προτεραιότητα</label>
                                <select {...register("priority")} className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl outline-none font-medium text-slate-800 transition-shadow hover:shadow-sm focus:ring-2 focus:ring-blue-100">
                                    <option value="low">Χαμηλή</option>
                                    <option value="medium">Μεσαία</option>
                                    <option value="high">Υψηλή</option>
                                    <option value="critical">Κρίσιμη</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wider">Αποδεικτικά (Πολλαπλά Αρχεία)</label>
                                <input type="file" multiple onChange={(e) => setSelectedFiles(Array.from(e.target.files))} className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm transition-shadow hover:shadow-sm" />
                            </div>
                            <div className="flex gap-3 mt-8 pt-4 border-t border-slate-100">
                                <button type="button" onClick={() => setIsTicketModalOpen(false)} className="flex-1 py-3 text-slate-500 font-bold hover:bg-slate-100 rounded-xl transition-colors">Ακύρωση</button>
                                <button type="submit" className="flex-1 py-3 bg-blue-600 text-white font-black rounded-xl hover:bg-blue-700 shadow-lg shadow-blue-200 transition-all">Υποβολή</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </DashboardLayout>
    );
};

export default Tickets;