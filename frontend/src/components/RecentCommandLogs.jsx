import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { transactionService } from '../services/api';
import { useCurrency } from '../context/CurrencyContext';

export default function RecentCommandLogs({ transactions, onRefresh }) {
  const { formatCurrency, currencySymbol } = useCurrency();
  const [showAddModal, setShowAddModal] = useState(false);
  const [amount, setAmount] = useState('');
  const [type, setType] = useState('income');
  const [category, setCategory] = useState('Tech Equity Index');
  const [description, setDescription] = useState('');

  const handleCreateTransaction = async (e) => {
    e.preventDefault();
    if (!amount || !category) return;

    try {
      await transactionService.createTransaction({
        amount: parseFloat(amount),
        type,
        category,
        description,
        date: new Date().toISOString()
      });
      setShowAddModal(false);
      setAmount('');
      setType('income');
      setCategory('Tech Equity Index');
      setDescription('');
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error('Failed to create transaction', err);
    }
  };

  // Helper HSL bullets for asset classes
  const getAssetBullet = (category) => {
    const name = category.toLowerCase();
    if (name.includes('tech') || name.includes('equity') || name.includes('income')) {
      return 'bg-primary';
    } else if (name.includes('collectible') || name.includes('digital') || name.includes('art') || name.includes('violet')) {
      return 'bg-violet-accent';
    } else {
      return 'bg-secondary';
    }
  };

  return (
    <div className="midnight-glass rounded-xl overflow-hidden cursor-default">
      <div className="p-6 md:p-card-padding border-b border-glass-border flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h3 className="font-headline-md text-lg md:text-[18px] text-text-primary">Recent Command Logs</h3>
        
        <div className="flex gap-4">
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1 text-primary text-sm font-semibold hover:text-emerald-glow transition-colors"
          >
            <span className="material-symbols-outlined text-[18px]">add_circle</span>
            Add Log
          </button>
          
          <button className="flex items-center gap-1 text-on-surface-variant text-sm md:text-body-base cursor-pointer hover:text-primary transition-colors">
            <span className="material-symbols-outlined text-[18px]">filter_list</span>
            Filter
          </button>
          
          <button className="flex items-center gap-1 text-on-surface-variant text-sm md:text-body-base cursor-pointer hover:text-primary transition-colors">
            <span className="material-symbols-outlined text-[18px]">download</span>
            Export
          </button>
        </div>
      </div>

      <div className="overflow-x-auto scrollbar-thin scrollbar-thumb-glass-border">
        <table className="w-full text-left min-w-[600px]">
          <thead className="bg-surface-variant/10 text-label-caps text-on-surface-variant border-b border-glass-border text-xs tracking-wider">
            <tr>
              <th className="px-6 py-4 font-bold">TRANSACTION ID</th>
              <th className="px-6 py-4 font-bold">ASSET CLASS</th>
              <th className="px-6 py-4 font-bold">STATUS</th>
              <th className="px-6 py-4 font-bold">TIMESTAMP</th>
              <th className="px-6 py-4 font-bold text-right">QUANTITY</th>
            </tr>
          </thead>
          
          <tbody className="divide-y divide-glass-border">
            {transactions.map((txn, index) => {
              const isIncome = txn.type === 'income';
              const isPending = txn.id.toString().includes('8812') || index === 1;

              return (
                <tr key={txn.id || index} className="hover:bg-slate-surface/50 transition-colors group">
                  <td className="px-6 py-4 font-body-bold text-primary text-sm font-bold">
                    {txn.id.toString().startsWith('#') ? txn.id : `#TXN-${txn.id}-CS`}
                  </td>
                  
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2 text-sm text-text-primary">
                      <div className={`w-2 h-2 rounded-full ${getAssetBullet(txn.category)}`}></div>
                      {txn.category}
                    </div>
                  </td>
                  
                  <td className="px-6 py-4">
                    {isPending ? (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-secondary/10 text-secondary border border-secondary/20 shadow-[0_0_8px_rgba(0,203,230,0.1)]">
                        PENDING
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-primary/10 text-primary border border-primary/20 shadow-[0_0_8px_rgba(90,240,179,0.1)]">
                        EXECUTED
                      </span>
                    )}
                  </td>
                  
                  <td className="px-6 py-4 text-on-surface-variant text-sm">
                    {txn.date}
                  </td>
                  
                  <td className={`px-6 py-4 text-right font-bold text-sm ${isIncome ? 'text-emerald-glow' : 'text-rose-expense'}`}>
                    {isIncome ? '+' : '-'}{formatCurrency(Math.abs(parseFloat(txn.amount)))}
                  </td>
                </tr>
              );
            })}

            {transactions.length === 0 && (
              <tr>
                <td colSpan="5" className="text-center py-8 text-on-surface-variant opacity-60 text-sm">
                  No logs available. Use 'Add Log' to seeding items!
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* --- ADD TRANSACTION MODAL --- */}
      {showAddModal && createPortal(
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-[200] backdrop-blur-md">
          <div className="bg-surface-container border border-primary/30 rounded-xl p-6 w-full max-w-md shadow-2xl midnight-glass transform scale-100 transition-all duration-300">
            <h4 className="font-headline-md text-[18px] text-text-primary mb-4 flex items-center justify-between">
              Add New Transaction
              <button
                onClick={() => setShowAddModal(false)}
                className="material-symbols-outlined text-on-surface-variant hover:text-rose-expense cursor-pointer"
              >
                close
              </button>
            </h4>
            <form onSubmit={handleCreateTransaction} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-1">TYPE</label>
                  <select
                    value={type}
                    onChange={(e) => setType(e.target.value)}
                    className="w-full bg-[#080e1a] border border-glass-border rounded-lg py-2 px-3 text-sm text-text-primary focus:outline-none focus:border-primary/50"
                  >
                    <option value="income">Income (+)</option>
                    <option value="expense">Expense (-)</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-1">AMOUNT ({currencySymbol})</label>
                  <input
                    type="number"
                    required
                    placeholder="e.g. 2500"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-full bg-[#080e1a] border border-glass-border rounded-lg py-2 px-3 text-sm text-text-primary focus:outline-none focus:border-primary/50"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-on-surface-variant mb-1">ASSET CLASS / CATEGORY</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-[#080e1a] border border-glass-border rounded-lg py-2 px-3 text-sm text-text-primary focus:outline-none focus:border-primary/50"
                >
                  <option value="Tech Equity Index">💻 Tech Equity Index</option>
                  <option value="Digital Collectible A">🎨 Digital Collectible A</option>
                  <option value="Liquid Cash Reserve">💵 Liquid Cash Reserve</option>
                  <option value="Housing">🏠 Housing</option>
                  <option value="Food">🍔 Food</option>
                  <option value="Transport">🚗 Transport</option>
                  <option value="Other">📦 Other</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-on-surface-variant mb-1">DESCRIPTION</label>
                <input
                  type="text"
                  placeholder="e.g. Buy monthly index stocks"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full bg-[#080e1a] border border-glass-border rounded-lg py-2 px-3 text-sm text-text-primary focus:outline-none focus:border-primary/50"
                />
              </div>

              <button
                type="submit"
                className="w-full py-2.5 bg-gradient-to-r from-primary to-secondary text-on-primary font-bold rounded-lg hover:brightness-110 transition-all text-sm shadow-[0_0_15px_rgba(90,240,179,0.3)]"
              >
                Execute Log Command
              </button>
            </form>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}
