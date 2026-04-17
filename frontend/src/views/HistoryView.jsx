import React from 'react';
import { motion } from 'framer-motion';
import { History, ArrowRight, TrendingUp, Calendar, MapPin } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const HistoryView = () => {
  const navigate = useNavigate();
  
  const scanHistory = [
    { id: 1, date: "Apr 12, 2026", district: "Mandya", area: "1.9 Ac", value: "₹18,500", status: "Verified" },
    { id: 2, date: "Mar 28, 2026", district: "Mysuru", area: "0.8 Ac", value: "₹7,200", status: "Paid" },
    { id: 3, date: "Feb 15, 2026", district: "Mandya", area: "1.9 Ac", value: "₹15,100", status: "Archived" }
  ];

  return (
    <div className="flex flex-col h-full bg-[#f8f9fa]">
      <header className="p-8 pb-12 bg-white rounded-b-[48px] shadow-sm">
        <h1 className="text-4xl font-black text-gray-900 mb-2">My History</h1>
        <p className="text-gray-400 font-bold uppercase tracking-widest text-xs">Past Reports & Scans</p>
      </header>

      <div className="flex-1 p-8 space-y-6">
        {scanHistory.map((scan, index) => (
          <motion.div
            key={scan.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            onClick={() => navigate('/impact')}
            className="bg-white p-6 rounded-[32px] shadow-lg shadow-green-900/5 group border border-transparent hover:border-green-100 transition-all cursor-pointer active:scale-[0.98]"
          >
            <div className="flex justify-between items-start mb-4">
              <div className="space-y-1">
                <div className="flex items-center space-x-2 text-green-700">
                  <Calendar size={14} />
                  <span className="text-xs font-black uppercase tracking-widest">{scan.date}</span>
                </div>
                <h3 className="text-xl font-black text-gray-900">{scan.district} Plot</h3>
              </div>
              <div className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-tighter ${
                scan.status === 'Paid' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
              }`}>
                {scan.status}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 border-t border-gray-50 pt-4">
              <div className="flex items-center space-x-2">
                <MapPin size={16} className="text-gray-300" />
                <span className="text-sm font-bold text-gray-500">{scan.area}</span>
              </div>
              <div className="flex items-center space-x-2">
                <TrendingUp size={16} className="text-green-600" />
                <span className="text-sm font-black text-green-700">{scan.value}</span>
              </div>
            </div>
            
            <div className="mt-4 flex justify-end">
              <ArrowRight size={20} className="text-gray-200 group-hover:text-green-600 group-hover:translate-x-1 transition-all" />
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default HistoryView;
