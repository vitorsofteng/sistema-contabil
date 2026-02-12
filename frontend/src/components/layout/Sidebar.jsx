import React from 'react';
import { BarChart3, Building2, Bell, Upload, FileText, Home, Menu, LogOut, Download, X } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { useExport } from '../../contexts/ExportContext';
import { adjustBrightness } from '../../utils/formatters';

function Sidebar({ currentPage, onNavigate, collapsed, onToggle, mobileOpen, onMobileClose }) {
  const { user, logout } = useAuth();
  const themeCtx = useTheme();
  const theme = themeCtx?.theme || {};
  const { setPanelOpen, pendingCount, readyCount } = useExport();
  
  const menuItems = [
    { id: 'dashboard', icon: Home, label: 'Dashboard' },
    { id: 'empresas', icon: Building2, label: 'Empresas' },
    { id: 'alertas', icon: Bell, label: 'Alertas' },
    { id: 'importacao', icon: Upload, label: 'Importação' },
    { id: 'relatorios', icon: FileText, label: 'Relatórios' },
  ];

  const sidebarStyle = {
    background: theme.cor_primaria 
      ? `linear-gradient(180deg, ${theme.cor_primaria} 0%, ${adjustBrightness(theme.cor_primaria, -30)} 100%)`
      : 'linear-gradient(180deg, #1e40af 0%, #1e3a8a 100%)'
  };
  
  const activeItemStyle = {
    backgroundColor: theme.cor_secundaria || '#3b82f6'
  };

  const totalBadge = pendingCount + readyCount;

  const handleNav = (id) => {
    onNavigate(id);
    if (onMobileClose) onMobileClose();
  };

  const handleExport = () => {
    setPanelOpen(true);
    if (onMobileClose) onMobileClose();
  };

  const handleLogout = () => {
    logout();
    if (onMobileClose) onMobileClose();
  };

  const sidebarContent = (isMobile) => (
    <>
      <div className="flex items-center justify-between p-4 border-b border-white/20">
        {(isMobile || !collapsed) && (
          <div className="flex items-center gap-2 min-w-0">
            <BarChart3 className="w-8 h-8 text-white/90 flex-shrink-0" />
            <span className="font-bold text-lg truncate">{theme.nome_escritorio || 'Kontabil'}</span>
          </div>
        )}
        <button 
          onClick={isMobile ? onMobileClose : onToggle} 
          className="p-1.5 hover:bg-white/10 rounded-lg flex-shrink-0"
        >
          {isMobile ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>
      
      <nav className="p-2 space-y-1 flex-1 overflow-y-auto">
        {menuItems.map(item => (
          <button
            key={item.id}
            onClick={() => handleNav(item.id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
              currentPage === item.id 
                ? 'text-white' 
                : 'text-white/70 hover:bg-white/10'
            }`}
            style={currentPage === item.id ? activeItemStyle : {}}
          >
            <item.icon className="w-5 h-5 flex-shrink-0" />
            {(isMobile || !collapsed) && <span>{item.label}</span>}
          </button>
        ))}

        {/* Botão Exportações */}
        <button
          onClick={handleExport}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-white/70 hover:bg-white/10 transition-colors relative"
        >
          <div className="relative flex-shrink-0">
            <Download className="w-5 h-5" />
            {pendingCount > 0 && (
              <div className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-amber-400 rounded-full animate-pulse" />
            )}
          </div>
          {(isMobile || !collapsed) && (
            <div className="flex items-center justify-between flex-1">
              <span>Exportações</span>
              {totalBadge > 0 && (
                <span className={`text-xs font-semibold px-1.5 py-0.5 rounded-full ${
                  readyCount > 0 ? 'bg-emerald-400/20 text-emerald-300' : 'bg-amber-400/20 text-amber-300'
                }`}>
                  {readyCount > 0 ? readyCount : pendingCount}
                </span>
              )}
            </div>
          )}
          {!isMobile && collapsed && totalBadge > 0 && (
            <span className={`absolute -top-0.5 -right-0.5 text-[10px] font-bold w-4 h-4 flex items-center justify-center rounded-full ${
              readyCount > 0 ? 'bg-emerald-400 text-white' : 'bg-amber-400 text-white'
            }`}>
              {readyCount > 0 ? readyCount : pendingCount}
            </span>
          )}
        </button>
      </nav>
      
      <div className="p-2 border-t border-white/20">
        {(isMobile || !collapsed) && (
          <div className="px-3 py-2 mb-2">
            <p className="text-sm font-medium truncate">{user?.nome}</p>
            <p className="text-xs text-white/60 truncate">{user?.email}</p>
          </div>
        )}
        {(isMobile || !collapsed) && (
          <div className="flex items-center gap-2 px-3 mb-2 text-[10px] text-white/40">
            <a href="#termos" className="hover:text-white/70 transition-colors">Termos</a>
            <span>·</span>
            <a href="#privacidade" className="hover:text-white/70 transition-colors">Privacidade</a>
          </div>
        )}
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-white/70 hover:bg-white/10"
        >
          <LogOut className="w-5 h-5 flex-shrink-0" />
          {(isMobile || !collapsed) && <span>Sair</span>}
        </button>
      </div>
    </>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside 
        className={`hidden md:flex fixed left-0 top-0 h-full text-white transition-all z-40 flex-col ${collapsed ? 'w-16' : 'w-64'}`}
        style={sidebarStyle}
      >
        {sidebarContent(false)}
      </aside>

      {/* Mobile backdrop */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 bg-black/50 z-40" onClick={onMobileClose} />
      )}

      {/* Mobile sidebar */}
      <aside 
        className={`md:hidden fixed inset-y-0 left-0 w-72 text-white z-50 flex flex-col transform transition-transform duration-300 ease-in-out ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}
        style={sidebarStyle}
      >
        {sidebarContent(true)}
      </aside>
    </>
  );
}

export default Sidebar;
