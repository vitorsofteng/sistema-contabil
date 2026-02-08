import React from 'react';

function Header({ title, subtitle, actions }) {
  return (
    <header className="mb-6">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 truncate">{title}</h1>
          {subtitle && <p className="text-slate-500 mt-1 text-sm sm:text-base truncate">{subtitle}</p>}
        </div>
        {actions && (
          <div className="flex items-center gap-2 flex-wrap flex-shrink-0">
            {actions}
          </div>
        )}
      </div>
    </header>
  );
}

export default Header;
