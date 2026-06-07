import React, { useState } from 'react';

export default function WealthGrowthChart({ trendData }) {
  const [activeTimeframe, setActiveTimeframe] = useState('7D');

  // Exact mockup trajectory datasets
  const data7D = [
    { label: 'MON', heightClass: 'h-1/2', value: '$600k' },
    { label: 'TUE', heightClass: 'h-3/5', value: '$720k' },
    { label: 'WED', heightClass: 'h-2/3', value: '$800k' },
    { label: 'THU', heightClass: 'h-1/2', value: '$600k' },
    { label: 'FRI', heightClass: 'h-4/5', value: '$960k' },
    { label: 'SAT', heightClass: 'h-full', value: '$1.2M', highlight: true }
  ];

  const data1M = [
    { label: 'WK 1', heightClass: 'h-1/3', value: '$400k' },
    { label: 'WK 2', heightClass: 'h-1/2', value: '$600k' },
    { label: 'WK 3', heightClass: 'h-2/3', value: '$800k' },
    { label: 'WK 4', heightClass: 'h-full', value: '$1.2M', highlight: true }
  ];

  const data1Y = [
    { label: 'Q1', heightClass: 'h-1/2', value: '$600k' },
    { label: 'Q2', heightClass: 'h-3/5', value: '$720k' },
    { label: 'Q3', heightClass: 'h-4/5', value: '$960k' },
    { label: 'Q4', heightClass: 'h-full', value: '$1.25M', highlight: true }
  ];

  const activeData = activeTimeframe === '1M' ? data1M : activeTimeframe === '1Y' ? data1Y : data7D;

  return (
    <div className="mb-8">
      <div className="midnight-glass p-6 md:p-card-padding rounded-xl overflow-hidden cursor-default">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <h3 className="font-headline-md text-lg md:text-[18px] text-text-primary">Wealth Growth Trajectory</h3>
          
          <div className="flex bg-surface-variant/50 p-1 rounded-lg border border-glass-border">
            {['7D', '1M', '1Y', 'MAX'].map((timeframe) => {
              const isActive = activeTimeframe === timeframe;
              return (
                <button
                  key={timeframe}
                  onClick={() => setActiveTimeframe(timeframe)}
                  className={`px-3 py-1 text-[11px] font-bold tracking-wider rounded transition-all ${
                    isActive
                      ? 'text-primary bg-primary-container/10'
                      : 'text-on-surface-variant hover:text-primary'
                  }`}
                >
                  {timeframe}
                </button>
              );
            })}
          </div>
        </div>

        {/* Bar charts grid wrapper */}
        <div className="h-64 md:h-80 flex items-end justify-between gap-1.5 md:gap-6 px-2 mb-4">
          {activeData.map((item, index) => (
            <div
              key={index}
              className={`flex-1 bg-gradient-to-t from-primary/20 to-transparent ${item.heightClass} rounded-t-sm relative group cursor-pointer transition-all duration-500 hover:from-primary/30`}
            >
              {/* Glowing Top Indicator Border */}
              <div className="absolute inset-x-0 top-0 h-1 bg-primary"></div>
              
              {/* Dynamic Popup Tooltip */}
              <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-primary text-on-primary px-2.5 py-1 rounded text-[10px] font-bold opacity-0 group-hover:opacity-100 transition-opacity duration-300 shadow-[0_0_10px_rgba(90,240,179,0.4)] whitespace-nowrap pointer-events-none z-10">
                {item.value}
              </div>
            </div>
          ))}
        </div>

        {/* X-Axis scale */}
        <div className="flex justify-between text-on-surface-variant text-[10px] md:text-label-caps border-t border-glass-border pt-4 px-2">
          {activeData.map((item, index) => (
            <span
              key={index}
              className={item.highlight ? 'text-primary font-bold' : ''}
            >
              {item.label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
