import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import api from '../../api';
import DashboardLayout from '../../components/layout/DashboardLayout';
import { useAuth } from '../../context/AuthContext';

const Properties = () => {
    const [properties, setProperties] = useState([]);
    const { user, viewMode } = useAuth(); 
    const [tenants, setTenants] = useState([]);
    const [judges, setJudges] = useState([]); // <--- ΝΕΟ: State για δικαστές
    const [loading, setLoading] = useState(true);
    
    // States για τα Modals
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [assignModalData, setAssignModalData] = useState(null);
    const [assignJudgeModalData, setAssignJudgeModalData] = useState(null); // <--- ΝΕΟ: Modal Δικαστή

    // Form Hooks
    const { 
        register: registerCreate, 
        handleSubmit: handleCreateSubmit, 
        reset: resetCreate,
        formState: { errors: errorsCreate } 
    } = useForm();
    
    const { 
        register: registerAssign, 
        handleSubmit: handleAssignSubmit, 
        reset: resetAssign,
        formState: { errors: errorsAssign }
    } = useForm();

    // ΝΕΟ: Form Hook για τον Δικαστή
    const { 
        register: registerJudge, 
        handleSubmit: handleJudgeSubmit, 
        reset: resetJudge,
        formState: { errors: errorsJudge }
    } = useForm();

    // src/pages/Properties.jsx

// Μέσα στο Properties.jsx, ενημέρωσε τη συνάρτηση fetchData:

const fetchData = async () => {
    try {
        setLoading(true);
        const [propsRes, tenantsRes, judgesRes] = await Promise.all([
            api.get(`/properties/my-properties?mode=${viewMode}`), // <--- ΠΕΡΝΑΜΕ ΤΟ MODE
            api.get('/auth/users?role=tenant'),
            api.get('/auth/users?role=judge')
        ]);
        
        setProperties(propsRes.data);
        setTenants(tenantsRes.data);
        setJudges(judgesRes.data);
    } catch (error) {
        console.error("Σφάλμα:", error);
    } finally {
        setLoading(false);
    }
};

    useEffect(() => {
        fetchData();
    }, [viewMode]);

    const onCreateSubmit = async (data) => {
        try {
            const payload = {
                title: data.title,
                address: data.address,
                price: Number(data.price),
                tenant_id: null,
                judge_id: null 
            };
            await api.post('/properties/', payload);
            setIsCreateModalOpen(false);
            resetCreate();
            fetchData();
        } catch (error) {
            console.error("Σφάλμα δημιουργίας:", error);
            alert("Πρόβλημα στην αποθήκευση.");
        }
    };

    const onAssignSubmit = async (data) => {
        try {
            await api.patch(`/properties/${assignModalData.id}/assign-tenant`, {
                tenant_id: data.tenant_id
            });
            setAssignModalData(null);
            resetAssign();
            fetchData();
        } catch (error) {
            alert(error.response?.data?.detail || "Σφάλμα στην ανάθεση.");
        }
    };

    // ΝΕΟ: Submit για τον Δικαστή
    const onAssignJudgeSubmit = async (data) => {
        try {
            await api.patch(`/properties/${assignJudgeModalData.id}/assign-judge/${data.judge_id}`);
            setAssignJudgeModalData(null);
            resetJudge();
            fetchData();
        } catch (error) {
            alert(error.response?.data?.detail || "Σφάλμα στον διορισμό δικαστή.");
        }
    };

    const getTenantName = (tenantId) => {
        if (!tenantId) return "Χωρίς Ενοικιαστή";
        const t = tenants.find(t => t.id === tenantId);
        return t ? t.full_name : "Άγνωστος";
    };

    const getJudgeName = (judgeId) => {
        if (!judgeId) return "Μη ορισμένος";
        const j = judges.find(j => j.id === judgeId);
        return j ? j.full_name : "Εκκρεμεί";
    };

    return (
        <DashboardLayout>
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-2xl font-black text-slate-800 tracking-tight">
                        {user?.role === 'judge' ? 'Δικαιοδοσία Ακινήτων' : (viewMode === 'landlord' ? 'Τα Ακίνητά μου' : 'Το Σπίτι μου')}
                    </h1>
                    <p className="text-slate-500 text-sm mt-1">
                        {user?.role === 'judge' ? 'Διαχείριση ακινήτων που σας έχουν ανατεθεί.' : 'Σύστημα διαχείρισης και διαιτησίας ακινήτων.'}
                    </p>
                </div>
                
                {user?.role === 'landlord' && viewMode === 'landlord' && (
                    <button 
                        onClick={() => setIsCreateModalOpen(true)}
                        className="bg-blue-600 hover:bg-blue-700 text-white font-bold px-6 py-2.5 rounded-xl shadow-lg shadow-blue-100 transition-all"
                    >
                        + Νέο Ακίνητο
                    </button>
                )}
            </div>

            {loading ? (
                <div className="text-center py-20 text-slate-400 font-bold animate-pulse">Συγχρονισμός...</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {properties.length > 0 ? (
                        properties.map((p) => (
                            <div key={p.id} className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100 flex flex-col hover:shadow-xl transition-all">
                                <h3 className="font-black text-xl text-slate-800 leading-tight">{p.title}</h3>
                                <p className="text-slate-400 text-sm mt-1 mb-6 flex items-center gap-1">📍 {p.address}</p>
                                
                                <div className="space-y-3 mb-6">
                                    <div className="bg-slate-50 p-4 rounded-2xl">
                                        <div className="flex justify-between items-center mb-3">
                                            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Μίσθωμα</span>
                                            <span className="text-blue-600 font-black text-lg">€{p.price}</span>
                                        </div>
                                        
                                        <div className="flex justify-between items-center pt-3 border-t border-slate-200/60">
                                            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Ενοικιαστής</span>
                                            <span className={`text-xs font-bold ${p.tenant_id ? 'text-slate-700' : 'text-orange-500 italic'}`}>
                                                {getTenantName(p.tenant_id)}
                                            </span>
                                        </div>

                                        {/* ΝΕΟ: ΕΜΦΑΝΙΣΗ ΔΙΚΑΣΤΗ ΣΤΗΝ ΚΑΡΤΑ */}
                                        <div className="flex justify-between items-center pt-3 mt-3 border-t border-slate-200/60">
                                            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Διαιτητής</span>
                                            <span className={`text-xs font-bold ${p.judge_id ? 'text-purple-600' : 'text-slate-400 italic'}`}>
                                                ⚖️ {getJudgeName(p.judge_id)}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                {/* ACTIONS ΓΙΑ LANDLORDS */}
                                {viewMode === 'landlord' && (
                                    <div className="grid grid-cols-2 gap-2 mt-auto">
                                        <button 
                                            onClick={() => setAssignModalData(p)}
                                            className="py-2.5 rounded-xl font-bold text-[11px] bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors"
                                        >
                                            👤 ΕΝΟΙΚΙΑΣΤΗΣ
                                        </button>
                                        <button 
                                            onClick={() => setAssignJudgeModalData(p)}
                                            className="py-2.5 rounded-xl font-bold text-[11px] bg-purple-50 text-purple-600 hover:bg-purple-100 transition-colors"
                                        >
                                            ⚖️ ΔΙΚΑΣΤΗΣ
                                        </button>
                                    </div>
                                )}
                            </div>
                        ))
                    ) : (
                        <div className="col-span-full text-center py-20 bg-white rounded-3xl border-2 border-dashed border-slate-100">
                            <div className="text-4xl mb-4">🏠</div>
                            <h3 className="text-lg font-bold text-slate-400">Δεν υπάρχουν ακίνητα για προβολή.</h3>
                        </div>
                    )}
                </div>
            )}

            {/* Modal 1: Δημιουργία Νέου Ακινήτου */}
            {isCreateModalOpen && (
                <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-3xl p-8 w-full max-w-md shadow-2xl">
                        <h2 className="text-2xl font-black text-slate-800 mb-6">Νέο Ακίνητο</h2>
                        <form onSubmit={handleCreateSubmit(onCreateSubmit)} className="space-y-4">
                            <div>
                                <label className="text-xs font-black text-slate-500 uppercase ml-1">Όνομα Ακινήτου</label>
                                <input {...registerCreate("title", { required: "Απαιτείται τίτλος" })} className="mt-1 block w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-blue-500 outline-none font-medium" />
                            </div>
                            <div>
                                <label className="text-xs font-black text-slate-500 uppercase ml-1">Διεύθυνση</label>
                                <input {...registerCreate("address", { required: "Απαιτείται διεύθυνση" })} className="mt-1 block w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-blue-500 outline-none font-medium" />
                            </div>
                            <div>
                                <label className="text-xs font-black text-slate-500 uppercase ml-1">Ενοίκιο (€)</label>
                                <input type="number" {...registerCreate("price", { required: "Απαιτείται τιμή" })} className="mt-1 block w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-blue-500 outline-none font-medium" />
                            </div>
                            <div className="flex gap-3 mt-8">
                                <button type="button" onClick={() => setIsCreateModalOpen(false)} className="flex-1 py-3 text-slate-500 font-bold hover:bg-slate-100 rounded-2xl transition-colors">Άκυρο</button>
                                <button type="submit" className="flex-1 py-3 bg-blue-600 text-white font-bold rounded-2xl hover:bg-blue-700 shadow-lg shadow-blue-100">Δημιουργία</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Modal 2: Ανάθεση Ενοικιαστή */}
            {assignModalData && (
                <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-3xl p-8 w-full max-w-md shadow-2xl">
                        <h2 className="text-2xl font-black text-slate-800 mb-2">Σύνδεση Ενοικιαστή</h2>
                        <p className="text-slate-400 text-sm mb-6 font-medium">Ακίνητο: {assignModalData.title}</p>
                        <form onSubmit={handleAssignSubmit(onAssignSubmit)} className="space-y-4">
                            <select {...registerAssign("tenant_id", { required: true })} className="block w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-blue-500 outline-none font-medium">
                                <option value="">Επιλογή Ενοικιαστή...</option>
                                {tenants.map(t => <option key={t.id} value={t.id}>{t.full_name}</option>)}
                            </select>
                            <div className="flex gap-3 mt-8">
                                <button type="button" onClick={() => setAssignModalData(null)} className="flex-1 py-3 text-slate-500 font-bold hover:bg-slate-100 rounded-2xl transition-colors">Άκυρο</button>
                                <button type="submit" className="flex-1 py-3 bg-blue-600 text-white font-bold rounded-2xl hover:bg-blue-700">Ανάθεση</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Modal 3: Ανάθεση Δικαστή (ΝΕΟ) */}
            {assignJudgeModalData && (
                <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-3xl p-8 w-full max-w-md shadow-2xl border border-purple-100">
                        <h2 className="text-2xl font-black text-slate-800 mb-2 flex items-center gap-2">
                           <span className="text-purple-600">⚖️</span> Ορισμός Διαιτητή
                        </h2>
                        <p className="text-slate-400 text-sm mb-6 font-medium">Επιλέξτε τον υπεύθυνο δικαστή για την επίλυση διαφορών.</p>
                        <form onSubmit={handleJudgeSubmit(onAssignJudgeSubmit)} className="space-y-4">
                            <select {...registerJudge("judge_id", { required: "Επιλέξτε έναν δικαστή" })} className="block w-full px-4 py-3 bg-purple-50 border-none rounded-2xl focus:ring-2 focus:ring-purple-500 outline-none font-bold text-purple-900">
                                <option value="">Επιλογή Δικαστή...</option>
                                {judges.map(j => <option key={j.id} value={j.id}>{j.full_name}</option>)}
                            </select>
                            <div className="flex gap-3 mt-8">
                                <button type="button" onClick={() => setAssignJudgeModalData(null)} className="flex-1 py-3 text-slate-500 font-bold hover:bg-slate-100 rounded-2xl transition-colors">Άκυρο</button>
                                <button type="submit" className="flex-1 py-3 bg-purple-600 text-white font-bold rounded-2xl hover:bg-purple-700 shadow-lg shadow-purple-100">Διορισμός</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </DashboardLayout>
    );
};

export default Properties;