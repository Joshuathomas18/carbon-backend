import React from 'react';
import { motion } from 'framer-motion';
import { Phone, CheckCircle2, TrendingUp, Leaf, ArrowRight, Share2, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const ResultsView = ({ results }) => {
  const navigate = useNavigate();
  // Use backend data structure or fallback
  const data = {
    value: results?.value_inr ? `₹${results.value_inr.toLocaleString()}` : "₹18,500",
    tonnes: results?.total_tonnes_co2 || 2.4,
    confidence: results?.confidence_score || 0.82,
    practices: results?.practices || [
      { name: "Zero Tillage", if_implemented_value_inr: 800, current: false },
      { name: "Residue Retention", if_implemented_value_inr: 1200, current: true }
    ]
  };

  if (!results) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center bg-[#f8f9fa]">
        <div className="w-20 h-20 bg-green-50 rounded-full flex items-center justify-center text-green-700 mb-6 font-black text-2xl">?</div>
        <h2 className="text-2xl font-black text-gray-900 mb-2">No Report Found</h2>
        <p className="text-gray-500 font-medium mb-8">Please complete a land survey or speak to the assistant first.</p>
        <button onClick={() => navigate('/discover')} className="px-8 py-4 bg-green-700 text-white rounded-2xl font-black uppercase text-xs tracking-widest shadow-lg shadow-green-900/10">Start Survey</button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-[#f8f9fa] overflow-y-auto pb-40">
      {/* Super-Premium Result Card */}
      <div className="p-10 pt-16 pb-20 bg-gradient-to-br from-green-800 to-green-600 text-white rounded-b-[64px] shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-white/10 rounded-full -mr-20 -mt-20 blur-3xl animate-pulse" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-amber-500/10 rounded-full -ml-16 -mb-16 blur-2xl" />

        <div className="relative z-10 space-y-12">
          <div className="flex justify-between items-center">
            <div className="bg-white/10 backdrop-blur-md px-4 py-2 rounded-2xl border border-white/20 flex items-center space-x-2">
              <Sparkles size={16} className="text-amber-300" />
              <span className="text-[10px] font-black uppercase tracking-widest">Satellite Verified</span>
            </div>
            <button className="p-3 bg-white/10 rounded-2xl border border-white/20 active:scale-90 transition-transform">
              <Share2 size={20} />
            </button>
          </div>

          <div className="text-center space-y-4">
            <h2 className="text-xs font-black opacity-80 uppercase tracking-[0.5em]">Estimated Annual Value</h2>
            <motion.h1 
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: "spring", stiffness: 100 }}
              className="text-8xl font-black tracking-tighter drop-shadow-2xl"
            >
              {data.value}
            </motion.h1>
            <div className="flex items-center justify-center space-x-2 text-green-100/80">
              <CheckCircle2 size={16} />
              <span className="text-sm font-bold tracking-tight">Confidence: {(data.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="bg-white/10 backdrop-blur-xl p-6 rounded-[32px] border border-white/20 shadow-inner">
              <div className="flex items-center space-x-2 text-green-200 mb-2">
                <Leaf size={18} />
                <span className="text-[10px] font-black uppercase tracking-wider">Storage</span>
              </div>
              <p className="text-3xl font-black leading-none">{data.tonnes} <span className="text-sm font-bold opacity-60">Tonnes</span></p>
            </div>
            <div className="bg-white/10 backdrop-blur-xl p-6 rounded-[32px] border border-white/20 shadow-inner">
              <div className="flex items-center space-x-2 text-green-200 mb-2">
                <TrendingUp size={18} />
                <span className="text-[10px] font-black uppercase tracking-wider">Potential</span>
              </div>
              <p className="text-3xl font-black leading-none">+15% <span className="text-sm font-bold opacity-60">Growth</span></p>
            </div>
          </div>
        </div>
      </div>

      {/* Recommended Practices - Rooted Elegance Layout */}
      <div className="px-10 py-12 space-y-10">
        <div>
          <div className="flex items-end justify-between mb-8">
            <div className="space-y-1">
              <span className="text-[10px] font-black uppercase tracking-widest text-green-700">Earnings Roadmap</span>
              <h3 className="text-3xl font-black text-gray-900 tracking-tight">Boost your income</h3>
            </div>
          </div>
          
          <div className="space-y-6">
            {data.practices.map((rec, index) => (
              <motion.div
                key={index}
                initial={{ x: 20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ delay: 0.2 + index * 0.1 }}
                className="relative bg-white p-8 rounded-[40px] shadow-lg shadow-green-900/5 group border border-transparent hover:border-green-100 transition-all active:scale-[0.98]"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className={`w-14 h-14 rounded-2xl flex items-center justify-center shadow-inner ${rec.current ? 'bg-green-100 text-green-700' : 'bg-gray-50 text-gray-300'}`}>
                    <CheckCircle2 size={28} />
                  </div>
                  <div className="flex flex-col items-end">
                    <span className="text-[10px] font-black uppercase tracking-widest text-green-600 mb-1">Impact</span>
                    <span className="text-xl font-black text-green-700">+₹{(rec.if_implemented_value_inr || 0).toLocaleString()}</span>
                  </div>
                </div>
                <h4 className="text-2xl font-black text-gray-900 mb-2">{rec.name}</h4>
                <p className="text-sm text-gray-500 font-medium leading-relaxed">
                  Implementing this sustainable management practice will increase your certified soil carbon sequestration.
                </p>
              </motion.div>
            ))}
          </div>
        </div>

        <button 
          onClick={() => navigate('/')}
          className="text-gray-400 font-black hover:text-green-700 transition-colors w-full py-8 uppercase tracking-[0.4em] text-[10px]"
        >
          Check New Survey
        </button>
      </div>

      {/* Floating CTA Hub */}
      <div className="fixed bottom-0 left-0 right-0 p-10 z-50 pointer-events-none">
        <div className="max-w-[480px] mx-auto pointer-events-auto">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="w-full py-7 px-10 rounded-[32px] bg-gray-900 text-white font-black text-xl shadow-2xl flex items-center justify-between group overflow-hidden relative"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-green-500/20 to-transparent -translate-x-full group-hover:translate-x-0 transition-transform duration-700" />
            <div className="flex items-center space-x-6 relative z-10">
              <div className="w-14 h-14 bg-white/10 backdrop-blur-md rounded-2xl flex items-center justify-center border border-white/20">
                <Phone size={24} />
              </div>
              <div className="flex flex-col items-start leading-none">
                <span className="text-[10px] font-black uppercase tracking-widest opacity-60 mb-1.5">Verified Payouts</span>
                <span>Contact Agent</span>
              </div>
            </div>
            <ArrowRight size={28} className="group-hover:translate-x-2 transition-transform relative z-10" />
          </motion.button>
        </div>
      </div>
    </div>
  );
};

export default ResultsView;
