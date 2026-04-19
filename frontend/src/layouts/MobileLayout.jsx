import React from 'react';
import { useLocation } from 'react-router-dom';
import BottomNavBar from '../components/BottomNavBar';

const MobileLayout = ({ children }) => {
  const location = useLocation();
  const hideNavRoutes = ['/map', '/discover'];
  const shouldHideNav = hideNavRoutes.includes(location.pathname);

  return (
    <div className="mobile-container relative flex flex-col min-h-screen">
      {/* Main Content Area */}
      <main className={`flex-1 ${shouldHideNav ? '' : 'pb-32'} overflow-x-hidden`}>
        {children}
      </main>

      {/* Persistent Bottom Navigation */}
      {!shouldHideNav && <BottomNavBar />}
    </div>
  );
};

export default MobileLayout;
