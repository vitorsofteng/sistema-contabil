import React from 'react';
import { X } from 'lucide-react';

function Modal({ isOpen, onClose, title, children, size = 'md' }) {
  if (!isOpen) return null;
  
  const sizes = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  };
  
  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative min-h-full flex items-end sm:items-center justify-center sm:p-4">
        <div className={`relative bg-white sm:rounded-xl shadow-xl w-full ${sizes[size]} rounded-t-xl sm:rounded-xl max-h-[90vh] sm:max-h-[85vh] flex flex-col`}>
          <div className="flex items-center justify-between p-4 border-b flex-shrink-0">
            <h3 className="text-lg font-semibold text-slate-900 truncate pr-4">{title}</h3>
            <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded-lg flex-shrink-0">
              <X className="w-5 h-5 text-slate-500" />
            </button>
          </div>
          <div className="p-4 overflow-y-auto flex-1">{children}</div>
        </div>
      </div>
    </div>
  );
}

export default Modal;
