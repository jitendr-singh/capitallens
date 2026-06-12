import React from 'react';
import { useAuth } from '../context/AuthContext';

export default function Sidebar({ isOpen, onClose, activeTab, setActiveTab }) {
  const { logout, user } = useAuth();

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
    { id: 'analytics', label: 'Analytics', icon: 'monitoring' },
    { id: 'investments', label: 'Investments', icon: 'trending_up' },
    { id: 'transactions', label: 'Transactions', icon: 'receipt_long' },
    { id: 'savings', label: 'Savings Goals', icon: 'savings' },
    { id: 'settings', label: 'Settings', icon: 'settings' },
  ];

  return (
    <>
      {/* Mobile Sidebar Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-[45] lg:hidden backdrop-blur-sm transition-opacity duration-300"
          onClick={onClose}
        />
      )}

      {/* SideNavBar */}
      <aside
        id="side-nav"
        className={`fixed left-0 top-0 h-full w-[280px] bg-slate-surface backdrop-blur-[20px] border-r border-glass-border shadow-2xl flex flex-col py-margin-page px-gutter-desktop z-50 transition-transform duration-300 cubic-bezier(0.4, 0, 0.2, 1) ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="mb-10 flex justify-between items-start">
          <div>
            <h1 className="font-display-lg text-display-lg text-primary tracking-tighter leading-none mb-1">
              Capitallens
            </h1>
            <p className="font-body-base text-on-surface-variant opacity-70 text-[12px]">
              Premium Wealth Console
            </p>
          </div>
          <button
            className="lg:hidden p-2 text-on-surface-variant hover:text-primary transition-colors"
            onClick={onClose}
            aria-label="Close Sidebar"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        {/* Navigation links */}
        <nav className="flex-1 space-y-2">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id);
                  onClose();
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg group transition-all relative ${
                  isActive
                    ? 'text-primary font-body-bold bg-primary-container/10'
                    : 'text-on-surface-variant font-body-base hover:bg-surface-variant/50'
                }`}
              >
                {isActive && <div className="active-link-indicator"></div>}
                <span className="material-symbols-outlined">{item.icon}</span>
                <span className="text-[14px]">{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Footer Area */}
        <div className="mt-auto pt-6 border-t border-glass-border space-y-2">
          <button className="w-full py-3 mb-4 bg-gradient-to-r from-primary to-secondary text-on-primary font-bold rounded-lg shadow-[0_0_20px_rgba(90,240,179,0.3)] hover:brightness-110 active:scale-[0.98] transition-all text-sm">
            Upgrade to Pro
          </button>
          
          <button className="w-full flex items-center gap-3 px-4 py-2 text-on-surface-variant font-body-base hover:text-primary transition-colors text-left text-sm">
            <span className="material-symbols-outlined">help</span>
            <span>Support</span>
          </button>

          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-4 py-2 text-on-surface-variant font-body-base hover:text-rose-expense transition-colors text-left text-sm"
          >
            <span className="material-symbols-outlined">logout</span>
            <span>Log Out</span>
          </button>
        </div>
      </aside>
    </>
  );
}
