import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useCurrency } from '../context/CurrencyContext';

export default function Header({ onOpenSidebar, onSync }) {
  const { user } = useAuth();
  const { currency, setCurrency } = useCurrency();
  const [isSyncing, setIsSyncing] = useState(false);
  const [searchFocused, setSearchFocused] = useState(false);

  const handleSyncClick = async () => {
    setIsSyncing(true);
    if (onSync) {
      await onSync();
    }
    // Simulate minor sync duration for cool micro-animation
    setTimeout(() => {
      setIsSyncing(false);
    }, 1000);
  };

  return (
    <header className="fixed top-0 right-0 left-0 lg:left-[280px] h-16 bg-background/80 backdrop-blur-md border-b border-glass-border flex justify-between items-center px-4 md:px-gutter-desktop z-40">
      <div className="flex items-center gap-3 md:gap-8">
        <button
          className="lg:hidden p-2 -ml-2 text-on-surface-variant hover:text-primary transition-colors"
          onClick={onOpenSidebar}
          aria-label="Open Sidebar"
        >
          <span className="material-symbols-outlined">menu</span>
        </button>

        {/* Search Bar with Focus Expand */}
        <div className={`relative hidden sm:block transition-all duration-300 ${searchFocused ? 'scale-105' : ''}`}>
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[18px]">
            search
          </span>
          <input
            type="text"
            placeholder="Search assets..."
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
            className="bg-surface-variant/30 border border-glass-border rounded-full py-1.5 pl-10 pr-4 w-48 xl:w-64 text-[14px] text-body-base focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all placeholder:opacity-50"
          />
        </div>

        <nav className="hidden xl:flex items-center gap-6">
          <button className="text-primary border-b-2 border-primary pb-1 font-bold text-sm">
            Market Overview
          </button>
          <button className="text-on-surface-variant hover:text-emerald-glow transition-all text-sm">
            Asset Insights
          </button>
        </nav>
      </div>

      <div className="flex items-center gap-2 md:gap-4">
        {/* Currency Switcher */}
        <div className="flex bg-[#0a101d]/60 border border-glass-border/40 rounded-full p-0.5 items-center">
          <button
            onClick={() => setCurrency('INR')}
            className={`px-3 py-1 rounded-full text-xs font-bold transition-all duration-300 ${
              currency === 'INR'
                ? 'bg-primary text-slate-surface shadow-[0_0_10px_rgba(90,240,179,0.35)]'
                : 'text-on-surface-variant hover:text-text-primary'
            }`}
          >
            ₹ INR
          </button>
          <button
            onClick={() => setCurrency('USD')}
            className={`px-3 py-1 rounded-full text-xs font-bold transition-all duration-300 ${
              currency === 'USD'
                ? 'bg-primary text-slate-surface shadow-[0_0_10px_rgba(90,240,179,0.35)]'
                : 'text-on-surface-variant hover:text-text-primary'
            }`}
          >
            $ USD
          </button>
        </div>

        {/* Interactive Live Sync Button */}
        <button
          onClick={handleSyncClick}
          className="flex items-center gap-2 px-3 md:px-4 py-1.5 border border-primary/50 text-primary rounded-full font-bold hover:bg-primary/10 transition-all active:scale-95 text-xs md:text-sm"
        >
          <span className={`material-symbols-outlined text-[16px] ${isSyncing ? 'animate-spin' : ''}`}>
            sync
          </span>
          <span className="hidden xs:inline">{isSyncing ? 'Syncing...' : 'Live Sync'}</span>
        </button>

        {/* Notifications Icon */}
        <button className="p-2 text-on-surface-variant hover:text-primary transition-colors relative" aria-label="Notifications">
          <span className="material-symbols-outlined text-[22px]">notifications</span>
          <span className="absolute top-2 right-2 w-2 h-2 bg-rose-expense rounded-full"></span>
        </button>

        {/* User Profile Avatar */}
        <div className="h-8 w-8 rounded-full overflow-hidden border border-glass-border cursor-pointer flex items-center justify-center bg-surface-variant">
          <img
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuBG3V64tnaRcPBkMyocXGgjMs_O-TiTLUAejEDfjKt4ECqklvV1-om-fmp8xS0lsyz9UNU1BkIGrPpJBscZ4d7sd1LjDaob975aB2YP51umqGarNqP-QT8SXB6bsSmutJl1wmMPMz4ftr3VETK9l1x8nZ8plw5AkTu4lOui3egb0VKCbjaRTjRvKi6LyZ4W24UjLG123MzYqLQrzvmTAPwZW7XmFJRjzpvo50Fu4PENtpkOX8AErpI1knDcBwBOPDxFqAQvv0QJHlg"
            alt="User Avatar"
            className="h-full w-full object-cover"
            onError={(e) => {
              // Graceful fallback for profile image if network fails
              e.target.style.display = 'none';
            }}
          />
          <span className="text-[10px] font-bold text-primary uppercase">CS</span>
        </div>
      </div>
    </header>
  );
}
