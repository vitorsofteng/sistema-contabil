import LoginPage from './LoginPage';
import RegisterPage from './RegisterPage';
import ForgotPasswordPage from './ForgotPasswordPage';
import ResetPasswordPage from './ResetPasswordPage';
import React, { useState, useEffect } from 'react';

function AuthPages() {
  const [page, setPage] = useState('login'); // login, register, forgot, reset
  const [resetToken, setResetToken] = useState('');
  
  // Detectar reset_token na URL (para usuários deslogados clicando link de reset)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const resetTokenUrl = params.get('reset_token');
    if (resetTokenUrl) {
      setResetToken(resetTokenUrl);
      setPage('reset');
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);
  
  if (page === 'forgot') {
    return <ForgotPasswordPage onBack={() => setPage('login')} onTokenReceived={(token) => { setResetToken(token); setPage('reset'); }} />;
  }
  
  if (page === 'reset') {
    return <ResetPasswordPage token={resetToken} onBack={() => setPage('login')} onSuccess={() => setPage('login')} />;
  }
  
  if (page === 'register') {
    return <RegisterPage onToggle={() => setPage('login')} />;
  }
  
  return <LoginPage onToggle={() => setPage('register')} onForgot={() => setPage('forgot')} />;
}

// Página de Esqueci Minha Senha

export default AuthPages;
