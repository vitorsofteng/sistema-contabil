export const CORES_GRAFICO = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export function formatarMoeda(valor) {
  if (valor == null || isNaN(valor)) return 'R$ 0,00';
  return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

export function formatarMoedaCurta(valor) {
  if (!valor && valor !== 0) return 'R$ 0';
  if (Math.abs(valor) >= 1e6) return `R$ ${(valor / 1e6).toFixed(1)}M`;
  if (Math.abs(valor) >= 1e3) return `R$ ${(valor / 1e3).toFixed(1)}K`;
  return formatarMoeda(valor);
}

// Função auxiliar para ajustar brilho de cor hex
export function adjustBrightness(hex, percent) {
  if (!hex) return '#1e3a8a';
  hex = hex.replace('#', '');
  const num = parseInt(hex, 16);
  const r = Math.min(255, Math.max(0, (num >> 16) + percent));
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0x00FF) + percent));
  const b = Math.min(255, Math.max(0, (num & 0x0000FF) + percent));
  return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
}
