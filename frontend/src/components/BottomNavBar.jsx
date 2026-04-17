import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, Map, Mic2, History, User, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';

const BottomNavBar = () => {
  const navItems = [
    { path: '/', icon: Home, label: 'Home' },
    { path: '/discover', icon: Map, label: 'Discover' },
    { path: '/assistant', icon: Mic2, label: 'Voice', large: true },
    { path: '/impact', icon: Sparkles, label: 'Impact' },
    { path: '/history', icon: History, label: 'History' },
  ];

  return (
    <nav className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-[480px] bg-white/95 backdrop-blur-xl border-t border-green-50 px-6 pt-3 pb-8 z-50 shadow-[0_-10px_40px_rgba(0,0,0,0.05)]">
      <div className="flex justify-between items-end">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `
              relative flex flex-col items-center group transition-all duration-300
              ${item.large ? 'mb-2' : ''}
              ${isActive ? 'text-green-700' : 'text-gray-300 hover:text-green-600'}
            `}
          >
            {({ isActive }) => (
              <>
                {item.large ? (
                  <div className={`
                    w-16 h-16 rounded-full flex items-center justify-center shadow-lg transform transition-transform group-active:scale-90
                    ${isActive ? 'bg-green-700 text-white' : 'bg-green-50 text-green-700'}
                  `}>
                    <item.icon size={28} />
                    {isActive && (
                      <motion.div
                        layoutId="nav-large-glow"
                        className="absolute inset-0 rounded-full bg-green-400/20"
                        initial={{ scale: 1 }}
                        animate={{ scale: 1.2 }}
                      />
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center space-y-1">
                    <item.icon size={22} className={`transition-transform duration-300 ${isActive ? 'scale-110' : ''}`} />
                    <span className={`text-[10px] font-black uppercase tracking-widest transition-opacity ${isActive ? 'opacity-100' : 'opacity-0 group-hover:opacity-40'}`}>
                      {item.label}
                    </span>
                    {isActive && (
                      <motion.div
                        layoutId="nav-dot"
                        className="w-1 h-1 bg-green-700 rounded-full absolute -bottom-2"
                      />
                    )}
                  </div>
                )}
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  );
};

export default BottomNavBar;
