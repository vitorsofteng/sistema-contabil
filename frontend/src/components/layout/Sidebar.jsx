import React from 'react';
import { BarChart3, Building2, Bell, Upload, FileText, Home, Menu, LogOut } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { adjustBrightness } from '../../utils/formatters';

function Sidebar({ currentPage, onNavigate, collapsed, onToggle }) {
  const { user, logout } = useAuth();
  const themeCtx = useTheme();
  const theme = themeCtx?.theme || {};
  
  const menuItems = [
    { id: 'dashboard', icon: Home, label: 'Dashboard' },
    { id: 'empresas', icon: Building2, label: 'Empresas' },
    { id: 'alertas', icon: Bell, label: 'Alertas' },
    { id: 'importacao', icon: Upload, label: 'Importação' },
    { id: 'relatorios', icon: FileText, label: 'Relatórios' },
  ];

  // Estilo dinâmico baseado no tema
  const sidebarStyle = {
    background: theme.cor_primaria 
      ? `linear-gradient(180deg, ${theme.cor_primaria} 0%, ${adjustBrightness(theme.cor_primaria, -30)} 100%)`
      : 'linear-gradient(180deg, #1e40af 0%, #1e3a8a 100%)'
  };
  
  const activeItemStyle = {
    backgroundColor: theme.cor_secundaria || '#3b82f6'
  };

  return (
    <aside 
      className={`fixed left-0 top-0 h-full text-white transition-all z-40 ${collapsed ? 'w-16' : 'w-64'}`}
      style={sidebarStyle}
    >
      <div className="flex items-center justify-between p-4 border-b border-white/20">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <BarChart3 className="w-8 h-8 text-white/90" />
            <span className="font-bold text-lg">{theme.nome_escritorio || 'Kontabil'}</span>
          </div>
        )}
        <button onClick={onToggle} className="p-1.5 hover:bg-white/10 rounded-lg">
          <Menu className="w-5 h-5" />
        </button>
      </div>
      
      <nav className="p-2 space-y-1">
        {menuItems.map(item => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
              currentPage === item.id 
                ? 'text-white' 
                : 'text-white/70 hover:bg-white/10'
            }`}
            style={currentPage === item.id ? activeItemStyle : {}}
          >
            <item.icon className="w-5 h-5" />
            {!collapsed && <span>{item.label}</span>}
          </button>
        ))}
      </nav>
      
      <div className="absolute bottom-0 left-0 right-0 p-2 border-t border-white/20">
        {!collapsed && (
          <div className="px-3 py-2 mb-2">
            <p className="text-sm font-medium truncate">{user?.nome}</p>
            <p className="text-xs text-white/60 truncate">{user?.email}</p>
          </div>
        )}
        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-white/70 hover:bg-white/10"
        >
          <LogOut className="w-5 h-5" />
          {!collapsed && <span>Sair</span>}
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;
