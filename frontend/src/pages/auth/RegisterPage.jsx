import AuthBranding from './AuthBranding';
import React, { useState } from 'react';
import { Activity, AlertCircle, ArrowLeft, Award, BarChart3, Building2, Check, CheckCircle, ChevronRight, Eye, FileText, Info, Loader2, Lock, User, XCircle } from 'lucide-react';
import { BarChart } from 'recharts';
import { useAuth } from '../../contexts/AuthContext';

function RegisterPage({ onToggle }) {
  const { register } = useAuth();
  const [form, setForm] = useState({ 
    nome: '', 
    email: '', 
    senha: '', 
    telefone: '',
    escritorio: '',
    cnpj: '',
    crc: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [step, setStep] = useState(1);
  
  const passwordChecks = {
    length: form.senha.length >= 8,
    uppercase: /[A-Z]/.test(form.senha),
    lowercase: /[a-z]/.test(form.senha),
    number: /\d/.test(form.senha),
    special: /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(form.senha),
  };
  const passwordStrength = Object.values(passwordChecks).filter(Boolean).length;
  const isPasswordValid = passwordStrength >= 4;

  const getStrengthColor = () => {
    if (passwordStrength <= 1) return 'bg-red-500';
    if (passwordStrength <= 2) return 'bg-orange-500';
    if (passwordStrength <= 3) return 'bg-yellow-500';
    if (passwordStrength <= 4) return 'bg-lime-500';
    return 'bg-emerald-500';
  };

  const getStrengthText = () => {
    if (passwordStrength <= 1) return 'Muito fraca';
    if (passwordStrength <= 2) return 'Fraca';
    if (passwordStrength <= 3) return 'Média';
    if (passwordStrength <= 4) return 'Forte';
    return 'Muito forte';
  };

  // Formatar CNPJ
  const formatCNPJ = (value) => {
    const numbers = value.replace(/\D/g, '').slice(0, 14);
    return numbers.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5')
                  .replace(/(\d{2})(\d{3})(\d{3})(\d{4})/, '$1.$2.$3/$4')
                  .replace(/(\d{2})(\d{3})(\d{3})/, '$1.$2.$3')
                  .replace(/(\d{2})(\d{3})/, '$1.$2');
  };

  // Formatar telefone
  const formatPhone = (value) => {
    const numbers = value.replace(/\D/g, '').slice(0, 11);
    if (numbers.length <= 10) {
      return numbers.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3')
                    .replace(/(\d{2})(\d{4})/, '($1) $2');
    }
    return numbers.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3')
                  .replace(/(\d{2})(\d{5})/, '($1) $2');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!isPasswordValid) {
      setError('A senha precisa ter pelo menos 4 requisitos atendidos');
      return;
    }
    
    setLoading(true);
    
    try {
      // Enviar dados completos
      await register({
        nome: form.nome,
        email: form.email,
        senha: form.senha,
        telefone: form.telefone,
        escritorio: form.escritorio,
        cnpj: form.cnpj.replace(/\D/g, ''),
        crc: form.crc
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const canProceedStep1 = form.nome.trim().length >= 3 && form.email.includes('@');
  const canProceedStep2 = form.escritorio.trim().length >= 2;

  const stepTitles = {
    1: { title: 'Dados Pessoais', subtitle: 'Informações do responsável pela conta' },
    2: { title: 'Dados do Escritório', subtitle: 'Informações do seu escritório contábil' },
    3: { title: 'Criar Senha', subtitle: 'Defina uma senha segura para sua conta' }
  };

  return (
    <div className="min-h-screen flex bg-slate-50">
      <AuthBranding />
      
      {/* Form Side */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
            <div className="w-12 h-12 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-xl flex items-center justify-center">
              <BarChart3 className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">Kontabil</h1>
              <p className="text-emerald-600 text-xs font-medium">Análise Financeira</p>
            </div>
          </div>

          <div className="text-center lg:text-left mb-6">
            <div className="flex items-center gap-2 text-emerald-600 text-sm font-medium mb-2">
              <span className="w-6 h-6 rounded-full bg-emerald-100 flex items-center justify-center text-xs">
                {step}
              </span>
              <span>Etapa {step} de 3</span>
            </div>
            <h2 className="text-3xl font-bold text-slate-900">{stepTitles[step].title}</h2>
            <p className="text-slate-500 mt-2">{stepTitles[step].subtitle}</p>
          </div>

          {/* Progress Steps */}
          <div className="flex items-center gap-2 mb-8">
            <div className={`flex-1 h-1.5 rounded-full transition-colors ${step >= 1 ? 'bg-emerald-500' : 'bg-slate-200'}`}></div>
            <div className={`flex-1 h-1.5 rounded-full transition-colors ${step >= 2 ? 'bg-emerald-500' : 'bg-slate-200'}`}></div>
            <div className={`flex-1 h-1.5 rounded-full transition-colors ${step >= 3 ? 'bg-emerald-500' : 'bg-slate-200'}`}></div>
          </div>
          
          {error && (
            <div className="mb-6 p-4 rounded-xl text-sm flex items-start gap-3 bg-red-50 border border-red-200 text-red-700">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium">Erro ao criar conta</p>
                <p className="text-sm opacity-80 mt-1">{error}</p>
              </div>
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* ETAPA 1: Dados Pessoais */}
            {step === 1 && (
              <>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Nome completo <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={form.nome}
                      onChange={e => setForm({...form, nome: e.target.value})}
                      placeholder="Seu nome completo"
                      required
                      className="w-full px-4 py-3 pl-11 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                    />
                    <User className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
                  </div>
                  <p className="text-xs text-slate-500 mt-1.5">Nome do contador ou responsável pela conta</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Email profissional <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type="email"
                      value={form.email}
                      onChange={e => setForm({...form, email: e.target.value})}
                      placeholder="contador@escritorio.com.br"
                      required
                      className="w-full px-4 py-3 pl-11 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                    />
                    <FileText className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
                  </div>
                  <p className="text-xs text-slate-500 mt-1.5">Será usado para login e comunicações importantes</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Telefone / WhatsApp
                  </label>
                  <div className="relative">
                    <input
                      type="tel"
                      value={form.telefone}
                      onChange={e => setForm({...form, telefone: formatPhone(e.target.value)})}
                      placeholder="(11) 99999-9999"
                      className="w-full px-4 py-3 pl-11 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                    />
                    <Activity className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => canProceedStep1 && setStep(2)}
                  disabled={!canProceedStep1}
                  className="w-full py-3 px-4 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  Continuar
                  <ChevronRight className="w-5 h-5" />
                </button>
              </>
            )}

            {/* ETAPA 2: Dados do Escritório */}
            {step === 2 && (
              <>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Nome do Escritório <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={form.escritorio}
                      onChange={e => setForm({...form, escritorio: e.target.value})}
                      placeholder="Nome do seu escritório contábil"
                      required
                      className="w-full px-4 py-3 pl-11 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                    />
                    <Building2 className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
                  </div>
                  <p className="text-xs text-slate-500 mt-1.5">Razão social ou nome fantasia do escritório</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    CNPJ do Escritório
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={form.cnpj}
                      onChange={e => setForm({...form, cnpj: formatCNPJ(e.target.value)})}
                      placeholder="00.000.000/0000-00"
                      className="w-full px-4 py-3 pl-11 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                    />
                    <FileText className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Registro CRC
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={form.crc}
                      onChange={e => setForm({...form, crc: e.target.value.toUpperCase()})}
                      placeholder="CRC-SP 123456/O-7"
                      className="w-full px-4 py-3 pl-11 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                    />
                    <Award className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
                  </div>
                  <p className="text-xs text-slate-500 mt-1.5">Registro no Conselho Regional de Contabilidade (opcional)</p>
                </div>

                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => setStep(1)}
                    className="flex-1 py-3 px-4 border border-slate-200 text-slate-700 font-semibold rounded-xl hover:bg-slate-100 transition-all flex items-center justify-center gap-2"
                  >
                    <ArrowLeft className="w-5 h-5" />
                    Voltar
                  </button>
                  <button
                    type="button"
                    onClick={() => canProceedStep2 && setStep(3)}
                    disabled={!canProceedStep2}
                    className="flex-1 py-3 px-4 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    Continuar
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              </>
            )}

            {/* ETAPA 3: Senha */}
            {step === 3 && (
              <>
                {/* Resumo dos dados */}
                <div className="bg-slate-100 rounded-xl p-4 mb-2">
                  <p className="text-xs text-slate-500 uppercase tracking-wide font-medium mb-2">Resumo do cadastro</p>
                  <div className="space-y-1.5 text-sm">
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4 text-slate-400" />
                      <span className="text-slate-700">{form.nome}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Building2 className="w-4 h-4 text-slate-400" />
                      <span className="text-slate-700">{form.escritorio}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-slate-400" />
                      <span className="text-slate-700">{form.email}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Criar senha <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={form.senha}
                      onChange={e => setForm({...form, senha: e.target.value})}
                      placeholder="••••••••"
                      required
                      className="w-full px-4 py-3 pl-11 pr-11 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                    />
                    <Lock className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                    >
                      {showPassword ? <XCircle className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                  
                  {/* Password Strength Indicator */}
                  {form.senha && (
                    <div className="mt-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs text-slate-500">Força da senha</span>
                        <span className={`text-xs font-medium ${
                          passwordStrength >= 4 ? 'text-emerald-600' : 
                          passwordStrength >= 3 ? 'text-lime-600' : 
                          passwordStrength >= 2 ? 'text-yellow-600' : 'text-red-600'
                        }`}>{getStrengthText()}</span>
                      </div>
                      <div className="flex gap-1">
                        {[1, 2, 3, 4, 5].map(i => (
                          <div key={i} className={`flex-1 h-1.5 rounded-full ${i <= passwordStrength ? getStrengthColor() : 'bg-slate-200'}`}></div>
                        ))}
                      </div>
                      
                      <div className="mt-4 grid grid-cols-2 gap-2">
                        {[
                          { check: passwordChecks.length, label: '8+ caracteres' },
                          { check: passwordChecks.uppercase, label: 'Maiúscula' },
                          { check: passwordChecks.lowercase, label: 'Minúscula' },
                          { check: passwordChecks.number, label: 'Número' },
                          { check: passwordChecks.special, label: 'Especial (!@#)' },
                        ].map((item, idx) => (
                          <div key={idx} className="flex items-center gap-2">
                            <div className={`w-4 h-4 rounded-full flex items-center justify-center ${item.check ? 'bg-emerald-500' : 'bg-slate-200'}`}>
                              {item.check && <Check className="w-3 h-3 text-white" />}
                            </div>
                            <span className={`text-xs ${item.check ? 'text-emerald-600' : 'text-slate-500'}`}>{item.label}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => setStep(2)}
                    className="flex-1 py-3 px-4 border border-slate-200 text-slate-700 font-semibold rounded-xl hover:bg-slate-100 transition-all flex items-center justify-center gap-2"
                  >
                    <ArrowLeft className="w-5 h-5" />
                    Voltar
                  </button>
                  <button
                    type="submit"
                    disabled={loading || !isPasswordValid}
                    className="flex-1 py-3 px-4 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Criando...
                      </>
                    ) : (
                      <>
                        Criar conta
                        <Check className="w-5 h-5" />
                      </>
                    )}
                  </button>
                </div>
              </>
            )}
          </form>
          
          {/* Info box */}
          <div className="mt-6 p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="font-medium text-emerald-800">Plano gratuito inclui:</p>
                <ul className="text-emerald-700 mt-1 space-y-0.5 text-xs">
                  <li>• Até 5 empresas cadastradas</li>
                  <li>• Importação de balancetes ilimitada</li>
                  <li>• Relatórios em PDF e Excel</li>
                  <li>• Suporte por email</li>
                </ul>
              </div>
            </div>
          </div>
          
          <p className="mt-6 text-center text-sm text-slate-500">
            Já tem uma conta?{' '}
            <button onClick={onToggle} className="text-emerald-600 font-semibold hover:text-emerald-700">
              Fazer login
            </button>
          </p>

          <p className="mt-4 text-center text-xs text-slate-400">
            Ao criar uma conta, você concorda com nossos{' '}
            <a href="#termos" className="text-emerald-600 hover:underline">Termos de Uso</a>
            {' '}e{' '}
            <a href="#privacidade" className="text-emerald-600 hover:underline">Política de Privacidade</a>
          </p>
        </div>
      </div>
    </div>
  );
}

// Tela de verificação de email pendente (após cadastro)

export default RegisterPage;
