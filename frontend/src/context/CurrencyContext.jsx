import React, { createContext, useContext, useState, useEffect } from 'react';

const CurrencyContext = createContext();

export function CurrencyProvider({ children }) {
  // Default to INR, load from localStorage if exists
  const [currency, setCurrencyState] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('capitallens_currency');
      return saved || 'INR';
    }
    return 'INR';
  });

  const setCurrency = (curr) => {
    setCurrencyState(curr);
    if (typeof window !== 'undefined') {
      localStorage.setItem('capitallens_currency', curr);
    }
  };

  const formatCurrency = (amount, decimals = 2) => {
    const numericAmount = parseFloat(amount);
    if (isNaN(numericAmount)) return '';

    if (currency === 'INR') {
      return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      }).format(numericAmount);
    } else {
      // 1-to-1 visual presentation format for USD
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      }).format(numericAmount);
    }
  };

  const currencySymbol = currency === 'INR' ? '₹' : '$';

  return (
    <CurrencyContext.Provider value={{ currency, setCurrency, formatCurrency, currencySymbol }}>
      {children}
    </CurrencyContext.Provider>
  );
}

export function useCurrency() {
  return useContext(CurrencyContext);
}
