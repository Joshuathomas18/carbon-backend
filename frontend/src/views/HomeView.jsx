import React, { useState } from 'react';
import { Mic, MapPin, Globe, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import farmHero from '../assets/farm_hero.png';

const HomeView = () => {
  const navigate = useNavigate();
  const [isRecording, setIsRecording] = useState(false);
  const [language, setLanguage] = useState('EN');

  const toggleRecording = () => {
    setIsRecording(!isRecording);
    if (!isRecording) {
      // Simulate listening and move to voice chat
      setTimeout(() => {
        setIsRecording(false);
        navigate('/assistant'); 
      }, 2500);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#FCF9F1]"> 
      {/* Header - Editorial Style */}
      <header className="flex justify-between items-center p-8 bg-white/80 backdrop-blur-md sticky top-0 z-30 shadow-sm border-b border-green-50">
        <div className="flex flex-col">
          <span className="text-[10px] font-black uppercase tracking-[0.2em] text-green-600 mb-0.5">The Digital Agronomist</span>
          <h1 className="text-2xl font-black text-gray-900 leading-none">Carbon-Voice</h1>
        </div>
        <div className="flex items-center space-x-2 bg-green-50 px-4 py-2 rounded-xl border border-green-100">
          <Globe size={16} className="text-green-600" />
          <select 
            value={language} 
            onChange={(e) => setLanguage(e.target.value)}
            className="bg-transparent border-none text-xs font-black uppercase tracking-wider text-green-800 focus:ring-0 cursor-pointer"
          >
            <option value="EN">English</option>
            <option value="HI">Hindi</option>
            <option value="KN">Kannada</option>
            <option value="PA">Punjabi</option>
          </select>
        </div>
      </header>

      {/* Main Content - Organic Layering */}
      <div className="flex-1 overflow-y-auto px-8 py-10 space-y-12">
        {/* Illustration Card */}
        <motion.div 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="relative group"
        >
          <div className="absolute inset-0 bg-green-600/5 rounded-[40px] rotate-3 group-hover:rotate-1 transition-transform" />
          <div className="relative bg-white p-6 rounded-[40px] shadow-xl shadow-green-900/5 border border-green-50 overflow-hidden">
            <img 
              src={farmHero} 
              alt="Farm Illustration" 
              className="w-full h-auto rounded-3xl mb-8 transform group-hover:scale-105 transition-transform duration-700" 
            />
            <div className="space-y-3">
              <h2 className="text-3xl font-black text-gray-900 leading-tight">
                Unlock the Gold in Your Soil.
              </h2>
              <p className="text-lg text-gray-500 font-medium leading-relaxed">
                Empowering Indian farmers to turn sustainable soil management into real financial growth.
              </p>
            </div>
          </div>
        </motion.div>

        {/* Action Hub */}
        <div className="flex flex-col items-center space-y-10 pb-16">
          {/* Pulsing Mic FAB */}
          <div className="relative group cursor-pointer" onClick={toggleRecording}>
            <AnimatePresence>
              {isRecording && (
                <>
                  <motion.div
                    initial={{ scale: 1, opacity: 0.6 }}
                    animate={{ scale: 2.2, opacity: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: "easeOut" }}
                    className="absolute inset-0 rounded-full bg-red-400"
                  />
                  <motion.div
                    initial={{ scale: 1, opacity: 0.4 }}
                    animate={{ scale: 1.8, opacity: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: "easeOut", delay: 0.5 }}
                    className="absolute inset-0 rounded-full bg-red-300"
                  />
                </>
              )}
            </AnimatePresence>
            
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className={`relative z-10 w-28 h-28 rounded-full flex items-center justify-center shadow-2xl transition-all duration-500 ${isRecording ? 'bg-red-500' : 'bg-green-700 hover:bg-green-800'}`}
            >
              <Mic size={40} className="text-white" />
            </motion.div>
            
            <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 w-max text-center">
              <span className={`text-xs font-black uppercase tracking-[0.3em] ${isRecording ? 'text-red-500 animate-pulse' : 'text-gray-400'}`}>
                {isRecording ? "Listening..." : "Tap to Speak"}
              </span>
            </div>
          </div>

          <div className="w-full pt-4 space-y-4">
            <button 
              onClick={() => navigate('/discover')}
              className="w-full flex items-center justify-between py-6 px-8 rounded-3xl bg-white border-2 border-green-700/10 text-green-800 font-black text-lg hover:border-green-700/30 hover:bg-green-50 transition-all shadow-sm group"
            >
              <div className="flex items-center space-x-4">
                <div className="bg-green-100 p-2 rounded-xl text-green-700">
                  <MapPin size={24} />
                </div>
                <span>Use Location</span>
              </div>
              <ChevronRight size={20} className="text-gray-300 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomeView;
