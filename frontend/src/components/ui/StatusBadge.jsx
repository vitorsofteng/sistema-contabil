import React from 'react';
import Badge from './Badge';

function StatusBadge({ status }) {
  const config = {
    // Formato antigo
    saudavel: { label: 'Saudável', variant: 'success' },
    atencao: { label: 'Atenção', variant: 'warning' },
    critico: { label: 'Crítico', variant: 'danger' },
    // Formato novo (analyzer profissional)
    'Excelente': { label: 'Excelente', variant: 'success' },
    'Bom': { label: 'Bom', variant: 'success' },
    'Regular': { label: 'Regular', variant: 'warning' },
    'Atenção': { label: 'Atenção', variant: 'warning' },
    'Crítico': { label: 'Crítico', variant: 'danger' },
  };
  
  const { label, variant } = config[status] || { label: status || 'N/A', variant: 'default' };
  return <Badge variant={variant}>{label}</Badge>;
}

export default StatusBadge;
