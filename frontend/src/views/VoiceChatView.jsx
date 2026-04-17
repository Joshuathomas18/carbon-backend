import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Play, ChevronLeft, Activity, Loader2, Sparkles, Send } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { sendVoiceQuery } from '../api/carbonApi';

const VoiceChatView = ({ setResults }) => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([
    { 
      id: 1, 
      type: 'ai', 
      text: "Namaste! I'm your Carbon AI. Before I calculate your final score, tell me: Are you currently burning your crop residue after harvest?",
      audio: true 
    }
  ]);
  const [isListening, setIsListening] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showCalculate, setShowCalculate] = useState(false);
  const [currentEstimate, setCurrentEstimate] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleHoldStart = () => {
    setIsListening(true);
  };

  const handleHoldEnd = async () => {
    setIsListening(false);
    setIsLoading(true);
    
    // Virtual audio data for prototype
    const mockAudioBase64 = "U09VTkRfREFUQV9NT0NfQkFTRTY0";

    try {
      const response = await sendVoiceQuery(mockAudioBase64, 'en');
      
      // Add User Message (Transcription)
      setMessages(prev => [...prev, { 
        id: Date.now(), 
        type: 'user', 
        text: response.transcribed_text || "Checking my residue practices...", 
      }]);

      // Add AI Response after a slight delay
      setTimeout(() => {
        setMessages(prev => [...prev, { 
          id: Date.now() + 1, 
          type: 'ai', 
          text: response.response_text, 
          audio: !!response.response_audio_base64 
        }]);
        
        if (response.carbon_estimate) {
          setCurrentEstimate(response.carbon_estimate);
          setShowCalculate(true);
        }
      }, 700);

    } catch (error) {
      console.error(error);
      // Demo Fallback
      setMessages(prev => [...prev, { id: 2, type: 'user', text: "No, I am using a mulcher now." }]);
      setTimeout(() => {
        setMessages(prev => [...prev, { 
          id: 3, 
          type: 'ai', 
          text: "That's fantastic! Mulching increases your carbon credit value by about 12%. I'm ready with your report.",
          audio: false 
        }]);
        setShowCalculate(true);
      }, 1000);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#f8f9fa] overflow-hidden">
      {/* Header - Editorial */}
      <header className="flex items-center p-8 bg-white shadow-sm border-b border-gray-100 z-20">
        <button onClick={() => navigate('/discover')} className="p-3 bg-gray-50 rounded-2xl mr-4 active:scale-95 transition-transform">
          <ChevronLeft size={24} className="text-gray-900" />
        </button>
        <div className="flex-1">
          <h1 className="text-xl font-black text-gray-900">Carbon Assistant</h1>
          <div className="flex items-center text-[10px] text-green-600 font-black uppercase tracking-widest">
            <span className="w-1.5 h-1.5 bg-green-500 rounded-full mr-1.5 animate-pulse" />
            Analyzing Field Data
          </div>
        </div>
        <div className="w-10 h-10 bg-green-50 rounded-xl flex items-center justify-center text-green-600">
          <Sparkles size={20} />
        </div>
      </header>

      {/* Chat Area with Organic Layering */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-8 space-y-8 pb-48"
      >
        <AnimatePresence>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ scale: 0.95, opacity: 0, y: 10 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div 
                className={`max-w-[85%] p-6 rounded-[32px] shadow-sm relative ${
                  msg.type === 'user' 
                    ? 'bg-green-700 text-white rounded-tr-none' 
                    : 'bg-white text-gray-800 rounded-tl-none border border-green-50'
                }`}
              >
                <p className="text-lg font-bold leading-relaxed">
                  {msg.text}
                </p>
                {msg.audio && (
                  <div className="absolute -bottom-2 -left-2 w-8 h-8 bg-green-50 rounded-full flex items-center justify-center text-green-600 shadow-sm">
                    <Play size={14} fill="currentColor" />
                  </div>
                )}
              </div>
            </motion.div>
          ))}
          
          {isLoading && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
              <div className="bg-white rounded-[24px] p-6 border border-green-50 shadow-sm flex items-center space-x-3">
                <Loader2 className="animate-spin text-green-700" size={20} />
                <span className="text-gray-400 font-bold italic tracking-tight">AI is processing...</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Futuristic Voice Control Hub */}
      <div className="absolute bottom-0 left-0 right-0 p-8 pt-16 bg-gradient-to-t from-white via-white to-transparent pointer-events-none">
        <div className="max-w-[480px] mx-auto space-y-6 pointer-events-auto">
          {showCalculate && (
            <motion.button
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              onClick={() => {
                setResults(currentEstimate);
                navigate('/impact');
              }}
              className="w-full py-6 px-10 rounded-[32px] bg-amber-500 text-white font-black text-xl shadow-2xl shadow-amber-200 flex items-center justify-between group active:scale-[0.98] transition-all"
            >
              <div className="flex items-center space-x-3">
                <Activity size={24} />
                <span>GENERATE REPORT</span>
              </div>
              <ChevronLeft size={24} className="rotate-180 group-hover:translate-x-2 transition-transform" />
            </motion.button>
          )}

          <div className="relative flex flex-col items-center">
            <motion.button
              onMouseDown={handleHoldStart}
              onMouseUp={handleHoldEnd}
              onTouchStart={handleHoldStart}
              onTouchEnd={handleHoldEnd}
              disabled={isLoading}
              className={`w-full py-8 px-12 rounded-full flex items-center justify-center space-x-5 shadow-2xl transition-all duration-300 relative overflow-hidden ${
                isListening 
                  ? 'bg-red-500 text-white scale-[1.02] h-28' 
                  : 'bg-white text-gray-900 h-24 border-2 border-green-700/10'
              } ${isLoading ? 'opacity-50 grayscale' : ''}`}
            >
              {isListening && (
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: "100%" }}
                  transition={{ duration: 0.5, repeat: Infinity }}
                  className="absolute bottom-0 left-0 h-1.5 bg-white/30"
                />
              )}
              
              {isListening ? (
                <div className="flex items-center space-x-4">
                  <div className="flex space-x-1 items-end h-8">
                    {[1,2,3,4,5].map(i => (
                      <motion.div 
                        key={i}
                        animate={{ height: [10, 30, 10] }}
                        transition={{ duration: 0.5, repeat: Infinity, delay: i*0.1 }}
                        className="w-1.5 bg-white rounded-full"
                      />
                    ))}
                  </div>
                  <span className="text-2xl font-black">Hold to Speak</span>
                </div>
              ) : (
                <>
                  <div className="w-14 h-14 bg-green-50 rounded-full flex items-center justify-center text-green-700">
                    <Mic size={32} />
                  </div>
                  <span className="text-2xl font-black text-gray-900">Hold to Speak</span>
                </>
              )}
            </motion.button>
            <p className="mt-4 text-[10px] font-black uppercase tracking-[0.4em] text-gray-400">
              {isListening ? "Assistant Listening" : "Press and hold for AI Voice"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceChatView;
