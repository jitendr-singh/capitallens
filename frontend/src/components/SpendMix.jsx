import React from 'react';
import { useCurrency } from '../context/CurrencyContext';

export default function SpendMix({ categoryData }) {
  const { formatCurrency, currencySymbol } = useCurrency();
  // Mockup high-fidelity fallback values
  const defaultExpenses = [
    { category: 'Housing', amount: 4980, colorClass: 'bg-violet-accent', hex: '#a78bfa', shadow: 'rgba(167, 139, 250, 0.4)' },
    { category: 'Food', amount: 3112.50, colorClass: 'bg-rose-expense', hex: '#fb7185', shadow: 'rgba(251, 113, 133, 0.4)' },
    { category: 'Transport', amount: 1245, colorClass: 'bg-secondary-fixed-dim', hex: '#2fd9f4', shadow: 'rgba(47, 217, 244, 0.4)' },
    { category: 'Other', amount: 3112.50, colorClass: 'bg-emerald-glow', hex: '#6ee7b7', shadow: 'rgba(110, 231, 183, 0.4)' }
  ];

  // Map category data if supplied, otherwise fallback
  let expenses = defaultExpenses;
  if (categoryData && categoryData.expense_by_category && categoryData.expense_by_category.length > 0) {
    const apiExpenses = categoryData.expense_by_category;
    
    // Merge colors to incoming categories
    const colors = [
      { bg: 'bg-violet-accent', hex: '#a78bfa', shadow: 'rgba(167, 139, 250, 0.4)' },
      { bg: 'bg-rose-expense', hex: '#fb7185', shadow: 'rgba(251, 113, 133, 0.4)' },
      { bg: 'bg-secondary-fixed-dim', hex: '#2fd9f4', shadow: 'rgba(47, 217, 244, 0.4)' },
      { bg: 'bg-emerald-glow', hex: '#6ee7b7', shadow: 'rgba(110, 231, 183, 0.4)' }
    ];

    expenses = apiExpenses.map((item, index) => {
      const colorStyle = colors[index % colors.length];
      return {
        category: item.category,
        amount: item.amount,
        colorClass: colorStyle.bg,
        hex: colorStyle.hex,
        shadow: colorStyle.shadow
      };
    });
  }

  const total = expenses.reduce((sum, item) => sum + item.amount, 0);

  const formatTotalK = (val) => {
    if (val >= 1000) {
      return `${currencySymbol}${(val / 1000).toFixed(1)}k`;
    }
    return `${currencySymbol}${val}`;
  };

  // Calculate segment ratios for SVG strokeDasharray
  let accumulatedPercent = 0;
  const svgSegments = expenses.map((item, index) => {
    const percentage = total > 0 ? (item.amount / total) * 100 : 0;
    
    // We want to map percentage out of 251.2 circumference (2 * pi * r where r=40)
    const circumference = 251.2;
    const strokeDash = (percentage / 100) * circumference;
    const strokeOffset = -((accumulatedPercent / 100) * circumference);
    
    accumulatedPercent += percentage;

    return {
      ...item,
      percentage: Math.round(percentage),
      strokeDashArray: `${strokeDash} ${circumference - strokeDash}`,
      strokeDashOffset: strokeOffset
    };
  });

  return (
    <div className="lg:col-span-7 flex flex-col gap-6">
      {/* Spend Mix Card */}
      <div className="midnight-glass p-6 md:p-card-padding rounded-xl flex flex-col cursor-default">
        <h3 className="font-headline-md text-lg md:text-[18px] text-text-primary mb-6 flex items-center justify-between">
          Spend Mix
          <span className="text-label-caps text-on-surface-variant text-[11px] font-bold">OCTOBER</span>
        </h3>
        
        <div className="flex flex-col sm:flex-row items-center gap-8">
          {/* Radial SVG Donut */}
          <div className="relative w-40 h-40">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
              {/* Background circle */}
              <circle
                className="text-surface-variant/20"
                cx="50"
                cy="50"
                fill="transparent"
                r="40"
                stroke="currentColor"
                strokeWidth="12"
              ></circle>
              
              {/* Custom segmented circles with mockup-exact drop shadows */}
              {svgSegments.map((seg, index) => (
                <circle
                  key={index}
                  cx="50"
                  cy="50"
                  fill="transparent"
                  r="40"
                  stroke={seg.hex}
                  strokeWidth="12"
                  strokeDasharray={seg.strokeDashArray}
                  strokeDashoffset={seg.strokeDashOffset}
                  style={{
                    filter: `drop-shadow(0 0 5px ${seg.shadow})`
                  }}
                ></circle>
              ))}
            </svg>

            {/* Inner Absolute Label */}
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-on-surface-variant text-[10px] font-label-caps tracking-wider opacity-60">TOTAL</span>
              <span className="text-xl font-stat-lg text-text-primary font-bold">
                {formatTotalK(total)}
              </span>
            </div>
          </div>

          {/* Color Indicators Grid */}
          <div className="grid grid-cols-2 gap-x-6 gap-y-3 flex-1 w-full">
            {svgSegments.map((item, index) => (
              <div key={index} className="flex items-center gap-2">
                <div className={`w-2.5 h-2.5 rounded-sm ${item.colorClass}`}></div>
                <span className="text-xs font-body-base text-on-surface-variant">
                  {item.category} ({item.percentage}%)
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Categories Progress Layout */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {svgSegments.slice(0, 2).map((item, index) => (
          <div
            key={index}
            className={`midnight-glass p-4 rounded-xl border-l-2 cursor-default ${
              index === 0 ? 'border-l-violet-accent' : 'border-l-rose-expense'
            }`}
          >
            <div className="flex justify-between items-center mb-2">
              <span className="font-body-bold text-sm text-text-primary font-semibold">
                {item.category === 'Housing' ? 'Housing & Utilities' : item.category === 'Food' ? 'Dining & Food' : item.category}
              </span>
              <span className={`text-label-caps text-xs font-bold ${
                index === 0 ? 'text-violet-accent' : 'text-rose-expense'
              }`}>
                {item.percentage}%
              </span>
            </div>

            <div className="h-1.5 w-full bg-surface-variant/30 rounded-full overflow-hidden mb-1">
              <div
                className={`h-full transition-all duration-1000 ${
                  index === 0 ? 'bg-violet-accent' : 'bg-rose-expense'
                }`}
                style={{ width: `${item.percentage}%` }}
              ></div>
            </div>

            <p className="text-[10px] text-on-surface-variant">
              {formatCurrency(item.amount)} of budget
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
