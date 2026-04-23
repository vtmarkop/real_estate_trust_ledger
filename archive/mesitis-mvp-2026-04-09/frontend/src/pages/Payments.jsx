import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import api from '../api';
import DashboardLayout from '../components/layout/DashboardLayout';
import { useAuth } from '../context/AuthContext';

const Payments = () => {
    const [payments, setPayments] = useState([]);
    const [properties, setProperties] = useState([]);
    const [tickets, setTickets] = useState([]); // ΝΕΟ: State για τα tickets
    const [loading, setLoading] = useState(true);
    
    const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false);
    
    const [detailsModalOpen, setDetailsModalOpen] = useState(false);
    const [selectedPayment, setSelectedPayment] = useState(null);
    const [actionComment, setActionComment] = useState('');
    const [actionPenalty, setActionPenalty] = useState(0);
    const [actionFiles, setActionFiles] = useState([]);
    const [searchTerm, setSearchTerm] = useState(''); // ΝΕΟ: Για την αναζήτηση

    const { user, viewMode } = useAuth(); 
    // ΝΕΟ: Χρησιμοποιούμε το watch και βάζουμε default κατηγορία το 'rent'
    const { register, handleSubmit, reset, watch } = useForm({
        defaultValues: { category: 'rent' }
    });
    const [selectedFiles, setSelectedFiles] = useState([]);

    const selectedCategory = watch('category'); // Παρακολουθεί τι επιλέγει ο χρήστης
   
    const openDetailsModal = (payment) => {
        setSelectedPayment(payment);
        setActionComment('');
        setActionPenalty(0);
        setActionFiles([]); // <--- ΝΕΟ
        setDetailsModalOpen(true);
    };

    // ΝΕΑ ΣΥΝΑΡΤΗΣΗ: Μετατρέπει τα κρυμμένα links του ιστορικού σε πραγματικά κουμπιά!
    const renderTimelineLog = (logLine) => {
        const parts = logLine.split(" 📎 [ΑΡΧΕΙΑ:");
        let textPart = parts[0]; // ΠΡΟΣΟΧΗ: let αντί για const για να μην σκάει το React
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
                                key={i} 
                                href={url} 
                                target="_blank" 
                                rel="noreferrer"
                                onClick={(e) => e.stopPropagation()} // Εξασφαλίζει ότι το κλικ θα πιάσει το link!
                                className="inline-flex items-center gap-1 text-[10px] font-black text-purple-700 bg-purple-100 px-2.5 py-1 rounded hover:bg-purple-200 transition-colors shadow-sm cursor-pointer"
                            >
                                📎 Αρχείο Ενέργειας {i + 1}
                            </a>
                        ))}
                    </div>
                )}
            </div>
        );
    };

    // ΝΕΑ ΣΥΝΑΡΤΗΣΗ: Εντοπίζει το Ticket ID στην περιγραφή και το κάνει Clickable
    const renderDescription = (desc) => {
        if (!desc) return null;
        
        // Ψάχνει το μοτίβο: [Ticket #ABCDEF | Τίτλος] Υπόλοιπο κείμενο
        const ticketMatch = desc.match(/^\[Ticket #([A-Z0-9]+) \| (.*?)\](.*)$/);
        
        if (ticketMatch) {
            const shortId = ticketMatch[1];
            const title = ticketMatch[2];
            const rest = ticketMatch[3];
            
            return (
                <div className="flex flex-wrap items-center gap-1 mt-1">
                    <span 
                        // Όταν το πατάει, τον πάει στη σελίδα των Tickets (ψάχνοντας το ID)
                        onClick={(e) => {
                            e.stopPropagation();
                            window.location.href = `/tickets?search=${shortId}`; 
                        }} 
                        className="inline-flex items-center gap-1 bg-amber-100 text-amber-800 px-2 py-0.5 rounded text-[10px] font-black cursor-pointer hover:bg-amber-200 transition-colors shadow-sm border border-amber-200"
                        title="Μετάβαση στο Ticket"
                    >
                        🎫 Ticket #{shortId}
                    </span>
                    <span className="font-semibold text-slate-700 text-xs">{title}</span>
                    <span className="text-xs text-slate-500">{rest}</span>
                </div>
            );
        }
        
        // Αν δεν είναι Ticket, επιστρέφει το απλό κείμενο (π.χ. [Ενοίκιο] ...)
        return <div className="text-xs text-slate-500 mt-1">{desc}</div>;
    };

    const fetchData = async () => {
        try {
            setLoading(true);
            // ΝΕΟ: Φέρνουμε και τα Tickets ταυτόχρονα
            const [payRes, propRes, tickRes] = await Promise.all([
                api.get(`/payments/my-payments?mode=${viewMode}`),
                api.get(`/properties/my-properties?mode=${viewMode}`),
                api.get(`/tickets/my-tickets`)
            ]);
            setPayments(payRes.data);
            setProperties(propRes.data);
            setTickets(tickRes.data);
        } catch (error) {
            console.error("Σφάλμα ανάκτησης δεδομένων:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [viewMode]);

    // Υποβολή Νέας Πληρωμής (Με τις Κατηγορίες)
    const onPaymentSubmit = async (data) => {
        let finalDescription = "";
        
        if (data.category === 'rent') {
            finalDescription = `[Ενοίκιο] ${data.notes || ''}`.trim();
        } else if (data.category === 'ticket') {
            const selectedTicket = tickets.find(t => t.id === data.ticket_id);
            const ticketTitle = selectedTicket ? selectedTicket.title : 'Άγνωστο Ticket';
            const shortId = selectedTicket ? selectedTicket.id.substring(0, 6).toUpperCase() : 'N/A';
            finalDescription = `[Ticket #${shortId} | ${ticketTitle}] ${data.notes || ''}`.trim();
        } else {
            finalDescription = `[Άλλο] ${data.notes || ''}`.trim();
        }

        try {
            let uploadedUrls = [];

            if (selectedFiles.length > 0) {
                const formData = new FormData();
                // Κάνουμε loop και βάζουμε όλα τα αρχεία στο FormData
                selectedFiles.forEach(file => {
                    formData.append("files", file); // ΠΡΟΣΟΧΗ: Το "files" πρέπει να είναι πληθυντικός για να ματσάρει με το FastAPI
                });
                
                const uploadRes = await api.post('/upload/', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
                uploadedUrls = uploadRes.data.urls; // Παίρνουμε τη λίστα με τα URLs
            }

            await api.post('/payments', {
                property_id: data.property_id,
                amount: Number(data.amount),
                description: finalDescription || "Πληρωμή",
                attachment_urls: uploadedUrls // <--- Στέλνουμε τη λίστα!
            });
            
            setIsPaymentModalOpen(false);
            setSelectedFiles([]); // Καθαρισμός
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

    const openActionModal = (paymentId, newStatus, propertyId, tenantId) => {
        setActionModal({ isOpen: true, paymentId, newStatus, propertyId, tenantId });
        setActionComment('');
        setActionPenalty(0);
    };

    const executeAction = async (newStatus) => {
        if (!selectedPayment) return;
        
        if (user?.role === 'judge' && !actionComment.trim()) {
            alert("Η αιτιολόγηση είναι υποχρεωτική για τον Δικαστή.");
            return;
        }

        let guiltyId = null;
        if (user?.role === 'judge') {
            const property = properties.find(p => p.id === selectedPayment.property_id);
            guiltyId = newStatus === 'COMPLETED' ? property?.owner_id : selectedPayment.tenant_id;
        }

        try {
            // --- ΝΕΟ: ΑΝΕΒΑΣΜΑ ΑΡΧΕΙΩΝ ΕΝΕΡΓΕΙΑΣ ---
            let uploadedUrls = [];
            if (actionFiles.length > 0) {
                const formData = new FormData();
                actionFiles.forEach(file => {
                    formData.append("files", file);
                });
                
                const uploadRes = await api.post('/upload/', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
                uploadedUrls = uploadRes.data.urls;
            }

            // Στέλνουμε το PATCH με τα νέα αρχεία
            await api.patch(`/payments/${selectedPayment.id}/status`, { 
                status: newStatus,
                comment: actionComment,
                score_impact: actionPenalty > 0 ? -Math.abs(actionPenalty) : 0, 
                guilty_party_id: guiltyId,
                new_attachment_urls: uploadedUrls // <--- Το νέο πεδίο!
            });
            
            setDetailsModalOpen(false);
            setSelectedPayment(null);
            setActionFiles([]); // Καθαρισμός
            fetchData();
        } catch (error) {
            console.error(error);
            alert("Σφάλμα: " + (error.response?.data?.detail || "Αποτυχία ενημέρωσης."));
        }
    };

    const getStatusBadge = (status) => {
        const s = typeof status === 'string' ? status.toUpperCase() : (status?.name || 'UNKNOWN');
        switch(s) {
            case 'COMPLETED': return <span className="text-[10px] font-black bg-green-100 text-green-700 px-3 py-1.5 rounded uppercase">✅ Εγκρίθηκε</span>;
            case 'PENDING': return <span className="text-[10px] font-black bg-orange-100 text-orange-700 px-3 py-1.5 rounded uppercase">⏳ Εκκρεμεί</span>;
            case 'REJECTED': return <span className="text-[10px] font-black bg-red-100 text-red-700 px-3 py-1.5 rounded uppercase">❌ Απορρίφθηκε</span>;
            case 'DISPUTED': return <span className="text-[10px] font-black bg-purple-100 text-purple-700 px-3 py-1.5 rounded uppercase">⚖️ Υπό Διαιτησία</span>;
            default: return <span>{s}</span>;
        }
    };

    // Φιλτράρισμα βάσει Αναζήτησης
    const filteredPayments = payments.filter(pay => {
        const term = searchTerm.toLowerCase();
        const propTitle = getPropertyTitle(pay.property_id).toLowerCase();
        const desc = (pay.description || '').toLowerCase();
        return propTitle.includes(term) || desc.includes(term);
    });

    return (
        <DashboardLayout>
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-2xl font-black text-slate-800 tracking-tight">
                        {user?.role === 'judge' ? 'Έλεγχος Συναλλαγών' : (viewMode === 'landlord' ? 'Έσοδα Ενοικίων' : 'Πληρωμές Ενοικίου')}
                    </h1>
                </div>
                {user?.role !== 'judge' && viewMode === 'tenant' && (
                    <button 
                        onClick={() => setIsPaymentModalOpen(true)}
                        className="bg-green-600 hover:bg-green-700 text-white font-semibold px-5 py-2.5 rounded-xl shadow-sm transition-all flex items-center gap-2"
                    >
                        <span>💳</span> Νέα Πληρωμή
                    </button>
                )}
            </div>

            {loading ? (
                <div className="text-center py-20 text-slate-400 font-bold animate-pulse">Ανάκτηση συναλλαγών...</div>
            ) : (
                <> {/* <--- ΒΑΛΕ ΑΥΤΟ ΤΟ ΣΥΜΒΟΛΟ ΕΔΩ (Άνοιγμα Fragment) */}
                    {/* ΜΠΑΡΑ ΑΝΑΖΗΤΗΣΗΣ */}
                    <div className="mb-4 flex items-center bg-white p-2 rounded-xl border border-slate-200 shadow-sm w-full max-w-md">
                        <span className="pl-3 pr-2 text-slate-400">🔍</span>
                        <input
                            type="text"
                            placeholder="Αναζήτηση με Ticket ID, Ακίνητο, ή Περιγραφή..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full bg-transparent outline-none text-sm p-1 font-medium text-slate-700"
                        />
                    </div>
                    <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-widest border-b border-slate-200">
                                        <th className="p-5 font-black">Ακίνητο & Περιγραφή</th>
                                        <th className="p-5 font-black">Ποσό</th>
                                        <th className="p-5 font-black">Κατάσταση</th>
                                        <th className="p-5 font-black text-right">Ενέργειες</th>
                                    </tr>
                                </thead>
                                <tbody>
                                {filteredPayments.length > 0 ? filteredPayments.map((pay) => {
                                    const currentStatus = typeof pay.status === 'string' ? pay.status.toUpperCase() : (pay.status?.name || 'UNKNOWN');
                                    
                                    return (
                                    <tr key={pay.id} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                                        <td className="p-5 align-top">
                                            <div className="font-bold text-slate-800 text-sm mb-1">🏢 {getPropertyTitle(pay.property_id)}</div>
                                            {renderDescription(pay.description)}
                                            
                                            {/* ΕΠΑΝΑΦΟΡΑ: Τα συνολικά αρχεία της πληρωμής (για συμβατότητα με τα παλιά) */}
                                            {Array.isArray(pay.attachment_urls) && pay.attachment_urls.length > 0 && (
                                                <div className="flex flex-wrap gap-2 mb-4">
                                                    {pay.attachment_urls.map((url, idx) => (
                                                        <a 
                                                            key={idx} href={url} target="_blank" rel="noreferrer"
                                                            onClick={(e) => e.stopPropagation()}
                                                            className="inline-flex items-center gap-1 text-[10px] font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded-md hover:bg-blue-100 transition-colors border border-blue-200 cursor-pointer relative z-10"
                                                        >
                                                            📎 Αρχικό Αρχείο {idx + 1}
                                                        </a>
                                                    ))}
                                                </div>
                                            )}
                                            
                                            {/* ΙΣΤΟΡΙΚΟ ΕΝΕΡΓΕΙΩΝ */}
                                            {pay.dispute_comment && (
                                                <div className="pl-3 border-l-2 border-slate-200 space-y-2">
                                                    {pay.dispute_comment.split('||').map((commentLine, index) => {
                                                        const line = commentLine.trim();
                                                        if (!line) return null;
                                                        return (
                                                            <div key={index} className="relative text-[11px]">
                                                                <div className="absolute -left-[17px] top-1.5 w-2 h-2 bg-purple-400 rounded-full border-2 border-white"></div>
                                                                <div className="bg-white p-2 rounded-lg border border-slate-200 shadow-sm">
                                                                    {renderTimelineLog(line)}
                                                                </div>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            )}
                                        </td>
                                        <td className="p-5 align-top">
                                            <div className="font-black text-blue-600">€{parseFloat(pay.amount).toFixed(2)}</div>
                                            <div className="text-[10px] text-slate-400 mt-1">{new Date(pay.created_at).toLocaleDateString('el-GR')}</div>
                                        </td>
                                        <td className="p-5 align-top">
                                            {getStatusBadge(pay.status)}
                                        </td>
                                        <td className="p-5 text-right align-top">
                                            <button 
                                                onClick={() => openDetailsModal(pay)} 
                                                className="bg-slate-100 text-slate-700 hover:bg-slate-200 px-4 py-2 rounded-lg text-xs font-bold transition-colors shadow-sm"
                                            >
                                                👁️ Λεπτομέρειες
                                            </button>
                                        </td>
                                    </tr>
                                )}) : (
                                    <tr><td colSpan="4" className="p-10 text-center text-slate-500">Δεν βρέθηκαν συναλλαγές.</td></tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
                </>
            )}

            {/* MODAL ΠΡΟΒΟΛΗΣ & ΕΝΕΡΓΕΙΩΝ ΠΛΗΡΩΜΗΣ */}
            {detailsModalOpen && selectedPayment && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-3xl p-8 w-full max-w-2xl shadow-2xl overflow-y-auto max-h-[90vh]">
                        <div className="flex justify-between items-start mb-6 border-b border-slate-100 pb-4">
                            <div>
                                <h2 className="text-2xl font-black text-slate-800">Στοιχεία Συναλλαγής</h2>
                                <p className="text-sm text-slate-500 mt-1">Ακίνητο: <strong className="text-slate-700">{getPropertyTitle(selectedPayment.property_id)}</strong></p>
                            </div>
                            <div>{getStatusBadge(selectedPayment.status)}</div>
                        </div>

                        {/* Κεντρικές Πληροφορίες */}
                        <div className="grid grid-cols-2 gap-4 mb-6 bg-slate-50 p-5 rounded-xl border border-slate-100">
                            <div>
                                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Περιγραφη</div>
                                <div className="font-medium text-slate-800 text-sm">{selectedPayment.description}</div>
                            </div>
                            <div>
                                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Ποσο</div>
                                <div className="font-black text-blue-600 text-lg">€{parseFloat(selectedPayment.amount).toFixed(2)}</div>
                            </div>
                        </div>

                        {/* Ιστορικό / Σχόλια */}
                        {selectedPayment.dispute_comment && (
                            <div className="mb-6">
                                <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-3">Ιστορικό Ενεργειών</h3>
                                <div className="space-y-2 pl-2 border-l-2 border-slate-200">
                                    {selectedPayment.dispute_comment.split('||').map((commentLine, index) => {
                                        const line = commentLine.trim();
                                        if (!line) return null;
                                        return (
                                            <div key={index} className="relative text-xs">
                                                <div className="absolute -left-[13px] top-1.5 w-2 h-2 bg-purple-400 rounded-full border-2 border-white"></div>
                                                <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                                                    {renderTimelineLog(line)}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        {/* ΖΩΝΗ ΕΝΕΡΓΕΙΩΝ (Δυναμική ανάλογα με ρόλο) */}
                        <div className="bg-white border-t border-slate-200 pt-6 mt-4">
                            {(() => {
                                const statusStr = typeof selectedPayment.status === 'string' ? selectedPayment.status.toUpperCase() : (selectedPayment.status?.name || 'UNKNOWN');
                                const canLandlordAct = viewMode === 'landlord' && user?.role !== 'judge' && statusStr === 'PENDING';
                                const canTenantAct = viewMode === 'tenant' && statusStr === 'REJECTED';
                                const canJudgeAct = user?.role === 'judge' && (statusStr === 'DISPUTED' || statusStr === 'REJECTED') && !selectedPayment.dispute_comment?.includes('[Δικαστής]');

                                if (!canLandlordAct && !canTenantAct && !canJudgeAct) {
                                    return <div className="text-center text-sm text-slate-400 italic">Δεν απαιτείται κάποια ενέργεια από εσάς αυτή τη στιγμή.</div>;
                                }

                                return (
                                    <div className="space-y-4">
                                        <h3 className="text-sm font-black text-slate-800">Διαθέσιμες Ενέργειες</h3>
                                        <div>
                                            <label className="block text-xs font-bold text-slate-700 mb-1 uppercase">Σχόλιο / Αιτιολόγηση {user?.role === 'judge' ? '(Υποχρεωτικό)' : ''}</label>
                                            <textarea 
                                                value={actionComment} onChange={(e) => setActionComment(e.target.value)} rows="2"
                                                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl outline-none text-sm focus:ring-2 focus:ring-purple-500"
                                                placeholder="Γράψτε τον λόγο..."
                                            />
                                        </div>
                                        {/* ΝΕΟ: ΑΝΕΒΑΣΜΑ ΔΙΚΑΙΟΛΟΓΗΤΙΚΩΝ ΕΝΕΡΓΕΙΑΣ */}
                                        <div>
                                            <label className="block text-xs font-bold text-slate-700 mb-1 uppercase">Συνημμένα Αρχεία (Προαιρετικό)</label>
                                            <input 
                                                type="file" 
                                                multiple 
                                                onChange={(e) => setActionFiles(Array.from(e.target.files))}
                                                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm" 
                                            />
                                            {actionFiles.length > 0 && (
                                                <div className="text-[10px] text-blue-600 mt-1 font-bold">Επιλέχθηκαν {actionFiles.length} αρχεία για ανέβασμα.</div>
                                            )}
                                        </div>

                                        {canJudgeAct && (
                                            <div>
                                                <label className="block text-xs font-bold text-red-600 mb-1 uppercase">Επιβολή Ποινής (Πόντοι)</label>
                                                <input 
                                                    type="number" min="0" value={actionPenalty} onChange={(e) => setActionPenalty(parseInt(e.target.value) || 0)}
                                                    className="w-full px-4 py-2 bg-red-50 border border-red-200 rounded-xl outline-none font-black text-red-700 focus:ring-2 focus:ring-red-500"
                                                />
                                            </div>
                                        )}

                                        <div className="flex gap-2 pt-2">
                                            {canLandlordAct && (
                                                <>
                                                    <button onClick={() => executeAction('COMPLETED')} className="flex-1 bg-green-600 hover:bg-green-700 text-white font-bold py-2.5 rounded-xl transition-colors">Έγκριση Πληρωμής</button>
                                                    <button onClick={() => executeAction('REJECTED')} className="flex-1 bg-red-100 hover:bg-red-200 text-red-700 font-bold py-2.5 rounded-xl transition-colors">Απόρριψη</button>
                                                </>
                                            )}
                                            {canTenantAct && (
                                                <button onClick={() => executeAction('DISPUTED')} className="flex-1 bg-amber-500 hover:bg-amber-600 text-white font-bold py-2.5 rounded-xl transition-colors">Άνοιγμα Ένστασης / Διαιτησία</button>
                                            )}
                                            {canJudgeAct && (
                                                <>
                                                    <button onClick={() => executeAction('COMPLETED')} className="flex-1 bg-green-600 hover:bg-green-700 text-white font-bold py-2.5 rounded-xl transition-colors">Δικαίωση Ενοικιαστή</button>
                                                    <button onClick={() => executeAction('REJECTED')} className="flex-1 bg-red-600 hover:bg-red-700 text-white font-bold py-2.5 rounded-xl transition-colors">Δικαίωση Ιδιοκτήτη</button>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                );
                            })()}
                        </div>

                        <div className="mt-6 pt-4 border-t border-slate-100 text-right">
                            <button onClick={() => { setDetailsModalOpen(false); setSelectedPayment(null); }} className="px-5 py-2 text-slate-500 font-bold hover:bg-slate-100 rounded-xl transition-colors">Κλείσιμο</button>
                        </div>
                    </div>
                </div>
            )}

            {/* ΝΕΟ: ΒΕΛΤΙΩΜΕΝΟ MODAL ΔΗΜΙΟΥΡΓΙΑΣ ΝΕΑΣ ΠΛΗΡΩΜΗΣ */}
            {isPaymentModalOpen && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-3xl p-8 w-full max-w-md shadow-2xl overflow-y-auto max-h-[90vh]">
                        <h2 className="text-2xl font-black text-slate-800 mb-6">Νέα Συναλλαγή</h2>
                        <form onSubmit={handleSubmit(onPaymentSubmit)} className="space-y-5">
                            
                            {/* 1. ΑΚΙΝΗΤΟ */}
                            <div>
                                <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wider">Ακίνητο</label>
                                <select {...register("property_id", { required: "Επιλέξτε ακίνητο" })} className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl outline-none font-medium">
                                    <option value="">Επιλέξτε ακίνητο...</option>
                                    {properties.map(p => <option key={p.id} value={p.id}>{p.title}</option>)}
                                </select>
                            </div>

                            {/* 2. ΚΑΤΗΓΟΡΙΑ */}
                            <div>
                                <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wider">Κατηγορία</label>
                                <select {...register("category")} className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl outline-none font-medium text-slate-800">
                                    <option value="rent">Ενοίκιο</option>
                                    <option value="ticket">Αποζημίωση Ticket (Βλάβη/Επισκευή)</option>
                                    <option value="other">Άλλο</option>
                                </select>
                            </div>

                            {/* 3. ΕΠΙΛΟΓΗ TICKET (Εμφανίζεται ΜΟΝΟ αν η κατηγορία είναι ticket) */}
                            {selectedCategory === 'ticket' && (
                                <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl">
                                    <label className="block text-xs font-bold text-amber-800 mb-1 uppercase tracking-wider">Επιλέξτε Ticket</label>
                                    <select 
                                        {...register("ticket_id", { required: selectedCategory === 'ticket' ? "Πρέπει να επιλέξετε ένα ticket" : false })} 
                                        className="w-full px-3 py-2 bg-white border border-amber-300 rounded-lg outline-none text-sm font-medium"
                                    >
                                        <option value="">-- Επιλέξτε από τη λίστα --</option>
                                        {tickets.map(t => (
                                            <option key={t.id} value={t.id}>{t.title} (Status: {t.status})</option>
                                        ))}
                                    </select>
                                </div>
                            )}

                            {/* 4. ΣΧΟΛΙΟ */}
                            <div>
                                <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wider">Σχόλιο / Περιγραφή</label>
                                <input 
                                    type="text" 
                                    {...register("notes")} 
                                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl font-medium outline-none text-sm" 
                                    placeholder={selectedCategory === 'rent' ? "π.χ. Ενοίκιο Απριλίου" : "Γράψτε λεπτομέρειες..."} 
                                />
                            </div>

                            {/* 5. ΠΟΣΟ */}
                            <div>
                                <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wider">Ποσό (€)</label>
                                <input type="number" step="0.01" min="0.01" {...register("amount", { required: true })} className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl font-black text-lg outline-none" placeholder="0.00" />
                            </div>

                            {/* ΑΝΕΒΑΣΜΑ ΑΠΟΔΕΙΚΤΙΚΟΥ */}
                            <div>
                                <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wider">Αποδεικτικά (Πολλαπλά Αρχεία)</label>
                                <input 
                                    type="file" 
                                    multiple // <--- ΑΥΤΟ ΕΠΙΤΡΕΠΕΙ ΤΗΝ ΕΠΙΛΟΓΗ ΠΟΛΛΩΝ ΑΡΧΕΙΩΝ
                                    onChange={(e) => setSelectedFiles(Array.from(e.target.files))}
                                    className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm" 
                                />
                                {selectedFiles.length > 0 && (
                                    <div className="text-xs text-slate-500 mt-2">Επιλέχθηκαν: {selectedFiles.length} αρχεία</div>
                                )}
                            </div>
                            
                            <div className="flex gap-3 mt-8 pt-4 border-t border-slate-100">
                                <button type="button" onClick={() => setIsPaymentModalOpen(false)} className="flex-1 py-3 text-slate-500 font-bold hover:bg-slate-100 rounded-xl transition-colors">Ακύρωση</button>
                                <button type="submit" className="flex-1 py-3 bg-green-600 text-white font-black rounded-xl hover:bg-green-700 shadow-lg shadow-green-200 transition-all">Υποβολή</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </DashboardLayout>
    );
};

export default Payments;