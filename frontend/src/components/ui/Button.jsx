import React from 'react';
import { Loader2 } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

function Button({ children, variant = 'primary', size = 'md', disabled, loading, className = '', style = {}, ...props }) {
  const themeCtx = useTheme();
  const theme = themeCtx?.theme || {};
  
  const baseClasses = 'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-all disabled:cursor-not-allowed';
  
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3 text-lg',
  };
  
  // Estilos dinâmicos para variante primary
  const getVariantStyles = () => {
    if (variant === 'primary') {
      return {
        backgroundColor: theme.cor_primaria || '#1e40af',
        color: 'white',
        ...style
      };
    }
    return style;
  };
  
  const variants = {
    primary: 'text-white hover:brightness-110 disabled:opacity-50',
    secondary: 'bg-slate-100 text-slate-700 hover:bg-slate-200',
    danger: 'bg-red-600 text-white hover:bg-red-700',
    ghost: 'text-slate-600 hover:bg-slate-100',
    success: 'bg-emerald-600 text-white hover:bg-emerald-700',
  };
  
  return (
    <button
      className={`${baseClasses} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled || loading}
      style={getVariantStyles()}
      {...props}
    >
      {loading && <Loader2 className="w-4 h-4 animate-spin" />}
      {children}
    </button>
  );
}

export default Button;
