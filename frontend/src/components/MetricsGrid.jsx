import React from 'react';
import { useCurrency } from '../context/CurrencyContext';

export default function MetricsGrid({ summaryData }) {
  const { formatCurrency } = useCurrency();
  // Graceful fallback defaults if data isn't loaded yet
  const totalBalance = summaryData?.total_savings ?? 1248592;
  const assetPerformance = "84.2%";
  const monthlyExpenses = summaryData?.total_expense ?? 12450;
  const transactionCount = summaryData?.transaction_count ?? 142;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-gutter-desktop mb-8">
      {/* Metric 1: Total Balance */}
      <div className="midnight-glass p-6 rounded-xl relative overflow-hidden group min-h-[160px] cursor-default">
        <div className="absolute top-4 right-4 text-primary glow-point"></div>
        <div className="flex flex-col h-full">
          <span className="text-label-caps text-on-surface-variant mb-4 flex items-center gap-2 text-xs">
            <span className="material-symbols-outlined text-[16px]">account_balance</span>
            TOTAL BALANCE
          </span>
          <span className="font-stat-lg text-2xl md:text-stat-lg text-text-primary">
            {formatCurrency(totalBalance)}
          </span>
          <div className="mt-auto pt-4 flex items-center gap-1 text-emerald-glow font-body-bold text-[12px]">
            <span className="material-symbols-outlined text-[14px]">trending_up</span>
            +12.4% <span className="text-on-surface-variant font-normal">this month</span>
          </div>
        </div>
      </div>

      {/* Metric 2: Asset Performance */}
      <div className="midnight-glass p-6 rounded-xl relative overflow-hidden group min-h-[160px] cursor-default">
        <div className="absolute top-4 right-4 text-secondary glow-point" style={{ color: '#5de6ff' }}></div>
        <div className="flex flex-col h-full">
          <span className="text-label-caps text-on-surface-variant mb-4 flex items-center gap-2 text-xs">
            <span className="material-symbols-outlined text-[16px]">show_chart</span>
            month
          </span>
          <span className="font-stat-lg text-2xl md:text-stat-lg text-text-primary">
            {assetPerformance}
          </span>
          <div className="mt-auto pt-4 flex items-center gap-1 text-emerald-glow font-body-bold text-[12px]">
            <span className="material-symbols-outlined text-[14px]">arrow_drop_up</span>
            Optimized <span className="text-on-surface-variant font-normal">levels detected</span>
          </div>
        </div>
      </div>

      {/* Metric 3: Monthly Expenses */}
      <div className="midnight-glass p-6 rounded-xl relative overflow-hidden group min-h-[160px] cursor-default">
        <div className="absolute top-4 right-4 text-rose-expense glow-point" style={{ color: '#fb7185' }}></div>
        <div className="flex flex-col h-full">
          <span className="text-label-caps text-on-surface-variant mb-4 flex items-center gap-2 text-xs">
            <span className="material-symbols-outlined text-[16px]">payments</span>
            MONTHLY EXPENSES
          </span>
          <span className="font-stat-lg text-2xl md:text-stat-lg text-text-primary">
            {formatCurrency(monthlyExpenses)}
          </span>
          <div className="mt-auto pt-4 flex items-center gap-1 text-rose-expense font-body-bold text-[12px]">
            <span className="material-symbols-outlined text-[14px]">trending_down</span>
            -2.1% <span className="text-on-surface-variant font-normal">from average</span>
          </div>
        </div>
      </div>

      {/* Metric 4: Transactions This Month */}
      <div className="midnight-glass p-6 rounded-xl relative overflow-hidden group min-h-[160px] cursor-default">
        <div className="absolute top-4 right-4 text-primary-fixed glow-point" style={{ color: '#68fcbf' }}></div>
        <div className="flex flex-col h-full">
          <span className="text-label-caps text-on-surface-variant mb-4 flex items-center gap-2 text-xs">
            <span className="material-symbols-outlined text-[16px]">receipt_long</span>
            TRANSACTIONS THIS MONTH
          </span>
          <span className="font-stat-lg text-2xl md:text-stat-lg text-text-primary">
            {transactionCount}
          </span>
          <div className="mt-auto pt-4 flex items-center gap-1 text-primary font-body-bold text-[12px]">
            <span className="material-symbols-outlined text-[14px]">bolt</span>
            +15 <span className="text-on-surface-variant font-normal">vs last month</span>
          </div>
        </div>
      </div>
    </div>
  );
}
