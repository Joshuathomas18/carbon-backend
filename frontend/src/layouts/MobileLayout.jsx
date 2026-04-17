import React from 'react';
import BottomNavBar from '../components/BottomNavBar';

const MobileLayout = ({ children }) => {
  return (
    <div className="mobile-container relative flex flex-col min-h-screen">
      {/* Main Content Area */}
      <main className="flex-1 pb-32 overflow-x-hidden">
        {children}
      </main>

      {/* Persistent Bottom Navigation */}
      <BottomNavBar />
    </div>
  );
};

export default MobileLayout;
