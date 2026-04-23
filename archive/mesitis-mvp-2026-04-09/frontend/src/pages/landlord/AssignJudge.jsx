import { useState, useEffect } from 'react';
import api from '../api';

const AssignJudge = ({ propertyId, currentJudgeId, onUpdate }) => {
    const [judges, setJudges] = useState([]);
    const [loading, setLoading] = useState(false);

    // Φέρνουμε τη λίστα με όλους τους δικαστές
    useEffect(() => {
        const fetchJudges = async () => {
            try {
                const res = await api.get('/users/judges');
                setJudges(res.data);
            } catch (err) {
                console.error("Σφάλμα φόρτωσης δικαστών");
            }
        };
        fetchJudges();
    }, []);

    const handleAssign = async (judgeId) => {
        setLoading(true);
        try {
            await api.patch(`/properties/${propertyId}/assign-judge/${judgeId}`);
            alert("Ο Δικαστής διορίστηκε επιτυχώς!");
            if (onUpdate) onUpdate(); // Refresh τη λίστα ακινήτων
        } catch (err) {
            alert("Αποτυχία διορισμού δικαστή");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="mt-4 p-4 bg-slate-50 rounded-xl border border-dashed border-slate-300">
            <label className="block text-xs font-black text-slate-500 uppercase tracking-widest mb-2">
                ⚖️ Διαιτησία Ακινήτου
            </label>
            
            <select 
                disabled={loading}
                value={currentJudgeId || ""}
                onChange={(e) => handleAssign(e.target.value)}
                className="w-full p-2 bg-white border border-slate-200 rounded-lg text-sm font-medium focus:ring-2 focus:ring-purple-500 outline-none transition-all"
            >
                <option value="" disabled>Επιλέξτε Δικαστή για το ακίνητο...</option>
                {judges.map(judge => (
                    <option key={judge.id} value={judge.id}>
                        {judge.full_name} (⭐ {judge.landlord_score}/100)
                    </option>
                ))}
            </select>
            
            {currentJudgeId && (
                <p className="text-[10px] text-purple-600 font-bold mt-2 italic">
                    * Αυτός ο δικαστής έχει πλέον δικαιοδοσία να επιλύει διαφορές για αυτό το ακίνητο.
                </p>
            )}
        </div>
    );
};

export default AssignJudge;