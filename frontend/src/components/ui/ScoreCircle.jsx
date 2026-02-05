import React from 'react';

function ScoreCircle({ score, size = 'md' }) {
  const color = score >= 70 ? 'text-emerald-600' : score >= 40 ? 'text-amber-600' : 'text-red-600';
  const bgColor = score >= 70 ? 'bg-emerald-50' : score >= 40 ? 'bg-amber-50' : 'bg-red-50';
  
  const sizes = {
    sm: 'w-10 h-10 text-sm',
    md: 'w-14 h-14 text-lg',
    lg: 'w-20 h-20 text-2xl',
  };
  
  return (
    <div className={`${sizes[size]} ${bgColor} rounded-full flex items-center justify-center font-bold ${color}`}>
      {score ?? '—'}
    </div>
  );
}

export default ScoreCircle;
