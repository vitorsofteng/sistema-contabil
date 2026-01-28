#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Relatório Excel Profissional
Sistema ContaGestor - Para Contadores com Múltiplas Empresas
"""

import io
import statistics
from datetime import datetime
from typing import Dict, List, Optional

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Border, Side, Alignment, NamedStyle
    from openpyxl.chart import LineChart, BarChart, PieChart, Reference
    from openpyxl.chart.label import DataLabelList
    from openpyxl.utils import get_column_letter
    from openpyxl.formatting.rule import ColorScaleRule, FormulaRule
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


class ExcelGenerator:
    """Gerador de relatórios Excel profissionais para contadores."""
    
    COLORS = {
        'primary': '1E40AF',
        'primary_light': '3B82F6',
        'success': '059669',
        'success_light': 'D1FAE5',
        'warning': 'D97706',
        'warning_light': 'FEF3C7',
        'danger': 'DC2626',
        'danger_light': 'FEE2E2',
        'gray_700': '374151',
        'gray_500': '6B7280',
        'gray_300': 'D1D5DB',
        'gray_100': 'F3F4F6',
        'white': 'FFFFFF',
    }
    
    def __init__(self, config: Dict = None):
        if not EXCEL_AVAILABLE:
            raise ImportError("openpyxl não instalado")
        
        self.config = config or {}
        self.wb = Workbook()
        self._setup_styles()
    
    def _setup_styles(self):
        cor = self.config.get('cor_primaria', '#1E40AF').replace('#', '')
        
        self.title_font = Font(name='Calibri', size=18, bold=True, color=cor)
        self.header_font = Font(name='Calibri', size=11, bold=True, color=self.COLORS['white'])
        self.header_fill = PatternFill(start_color=cor, end_color=cor, fill_type='solid')
        self.subheader_fill = PatternFill(start_color=self.COLORS['gray_700'], end_color=self.COLORS['gray_700'], fill_type='solid')
        self.highlight_fill = PatternFill(start_color=self.COLORS['gray_100'], end_color=self.COLORS['gray_100'], fill_type='solid')
        self.success_fill = PatternFill(start_color=self.COLORS['success_light'], end_color=self.COLORS['success_light'], fill_type='solid')
        self.warning_fill = PatternFill(start_color=self.COLORS['warning_light'], end_color=self.COLORS['warning_light'], fill_type='solid')
        self.danger_fill = PatternFill(start_color=self.COLORS['danger_light'], end_color=self.COLORS['danger_light'], fill_type='solid')
        
        self.normal_font = Font(name='Calibri', size=10)
        self.bold_font = Font(name='Calibri', size=10, bold=True)
        self.small_font = Font(name='Calibri', size=9, color=self.COLORS['gray_500'])
        
        self.currency_format = 'R$ #,##0.00'
        self.percent_format = '0.0%'
        self.number_format = '#,##0.00'
        
        self.thin_border = Border(
            left=Side(style='thin', color=self.COLORS['gray_300']),
            right=Side(style='thin', color=self.COLORS['gray_300']),
            top=Side(style='thin', color=self.COLORS['gray_300']),
            bottom=Side(style='thin', color=self.COLORS['gray_300'])
        )
        
        self.center = Alignment(horizontal='center', vertical='center', wrap_text=True)
        self.right = Alignment(horizontal='right', vertical='center')
        self.left = Alignment(horizontal='left', vertical='center', wrap_text=True)
    
    def _calcular_indicadores(self, dados_mensais: List[Dict], analise: Dict = None) -> Dict:
        if not dados_mensais: return {}
        
        if analise:
            resultado = analise.get('resultado_completo', analise.get('resultado', analise))
            if isinstance(resultado, dict):
                ind = resultado.get('indicadores', {})
                if ind: return ind
        
        dados = sorted(dados_mensais, key=lambda x: (x.get('ano', 0), x.get('mes', 0)))
        ultimo = dados[-1] if dados else {}
        n = len(dados)
        
        receita_total = sum(d.get('receita', 0) or d.get('receita_bruta', 0) or 0 for d in dados)
        custos_total = sum(d.get('custos', 0) or d.get('custos_total', 0) or 0 for d in dados)
        despesas_total = sum(d.get('despesas', 0) or d.get('despesas_operacionais', 0) or 0 for d in dados)
        impostos_total = sum(d.get('impostos', 0) or d.get('deducoes_receita', 0) or 0 for d in dados)
        
        lucro_bruto = receita_total - custos_total
        lucro_liquido = sum(d.get('lucro_liquido', 0) or 0 for d in dados)
        if lucro_liquido == 0:
            lucro_liquido = receita_total - custos_total - despesas_total - impostos_total
        
        ac = ultimo.get('ativo_circulante', 0) or 0
        pc = ultimo.get('passivo_circulante', 0) or 0
        pnc = ultimo.get('passivo_nao_circulante', 0) or 0
        at = ultimo.get('ativo_total', 0) or ac
        pl = ultimo.get('patrimonio_liquido', 0) or 0
        disponivel = ultimo.get('disponivel', 0) or ultimo.get('caixa', 0) or 0
        clientes = ultimo.get('clientes', 0) or 0
        estoques = ultimo.get('estoques', 0) or 0
        receita_mensal = receita_total / n if n > 0 else 0
        
        ind = {
            'receita_total': receita_total, 'receita_mensal_media': receita_mensal,
            'custos_total': custos_total, 'lucro_bruto': lucro_bruto,
            'despesas_total': despesas_total, 'impostos_total': impostos_total,
            'lucro_liquido': lucro_liquido,
            'margem_bruta': (lucro_bruto / receita_total * 100) if receita_total > 0 else 0,
            'margem_liquida': (lucro_liquido / receita_total * 100) if receita_total > 0 else 0,
            'liquidez_corrente': ac / pc if pc > 0 else 0,
            'liquidez_seca': (ac - estoques) / pc if pc > 0 else 0,
            'liquidez_imediata': disponivel / pc if pc > 0 else 0,
            'roe': (lucro_liquido / pl * 100) if pl > 0 else 0,
            'roa': (lucro_liquido / at * 100) if at > 0 else 0,
            'giro_ativo': receita_total / at if at > 0 else 0,
            'endividamento_geral': ((pc + pnc) / at * 100) if at > 0 else 0,
            'composicao_endividamento': (pc / (pc + pnc) * 100) if (pc + pnc) > 0 else 0,
            'pmr': (clientes / receita_mensal * 30) if receita_mensal > 0 else 0,
            'carga_tributaria': (impostos_total / receita_total * 100) if receita_total > 0 else 0,
            'capital_giro': ac - pc,
            'ativo_total': at, 'ativo_circulante': ac, 'passivo_circulante': pc,
            'passivo_nao_circulante': pnc, 'patrimonio_liquido': pl,
            'disponivel': disponivel, 'meses_analisados': n,
        }
        
        if n >= 3:
            receitas = [d.get('receita', 0) or d.get('receita_bruta', 0) or 0 for d in dados]
            p1 = statistics.mean(receitas[:n//2]) if receitas[:n//2] else 0
            p2 = statistics.mean(receitas[n//2:]) if receitas[n//2:] else 0
            ind['variacao_receita'] = ((p2 - p1) / p1 * 100) if p1 > 0 else 0
        else:
            ind['variacao_receita'] = 0
        
        return ind
    
    def _classificar_saude(self, ind: Dict) -> Dict:
        pontos = 0
        ml, lc, endiv, var = ind.get('margem_liquida', 0), ind.get('liquidez_corrente', 0), ind.get('endividamento_geral', 0), ind.get('variacao_receita', 0)
        
        pontos += 25 if ml >= 20 else 20 if ml >= 10 else 15 if ml >= 5 else 5 if ml >= 0 else 0
        pontos += 25 if lc >= 2 else 20 if lc >= 1.5 else 15 if lc >= 1 else 5 if lc >= 0.8 else 0
        pontos += 25 if endiv <= 30 else 20 if endiv <= 50 else 15 if endiv <= 70 else 5 if endiv <= 85 else 0
        pontos += 25 if var >= 20 else 20 if var >= 10 else 15 if var >= 0 else 5 if var >= -10 else 0
        
        if pontos >= 80: return {'pontos': pontos, 'status': 'Excelente'}
        if pontos >= 60: return {'pontos': pontos, 'status': 'Bom'}
        if pontos >= 40: return {'pontos': pontos, 'status': 'Regular'}
        return {'pontos': pontos, 'status': 'Crítico'}
    
    def gerar_relatorio(self, empresa: Dict, dados_mensais: List[Dict], analise: Dict = None, alertas: List[Dict] = None, config: Dict = None) -> bytes:
        self.config = config or self.config
        self.wb = Workbook()
        self._setup_styles()
        
        self.wb.remove(self.wb.active)
        
        ind = self._calcular_indicadores(dados_mensais, analise)
        saude = self._classificar_saude(ind)
        
        self._criar_aba_resumo(empresa, dados_mensais, ind, saude, alertas)
        self._criar_aba_dre(empresa, dados_mensais, ind)
        self._criar_aba_indicadores(empresa, ind)
        self._criar_aba_balanco(empresa, ind)
        self._criar_aba_evolucao(empresa, dados_mensais)
        self._criar_aba_alertas(empresa, alertas, ind)
        
        buffer = io.BytesIO()
        self.wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _criar_aba_resumo(self, empresa: Dict, dados: List[Dict], ind: Dict, saude: Dict, alertas: List[Dict]):
        ws = self.wb.create_sheet("Resumo Executivo", 0)
        ws.sheet_properties.tabColor = self.COLORS['primary']
        
        # Larguras
        ws.column_dimensions['A'].width = 3
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 20
        ws.column_dimensions['E'].width = 25
        
        row = 2
        
        # Cabeçalho
        nome_escritorio = self.config.get('nome_escritorio', 'ContaGestor')
        ws.merge_cells(f'B{row}:E{row}')
        ws[f'B{row}'] = nome_escritorio
        ws[f'B{row}'].font = self.title_font
        row += 1
        
        ws.merge_cells(f'B{row}:E{row}')
        ws[f'B{row}'] = "DIAGNÓSTICO FINANCEIRO"
        ws[f'B{row}'].font = Font(name='Calibri', size=14, color=self.COLORS['gray_500'])
        row += 2
        
        # Empresa
        ws[f'B{row}'] = empresa.get('razao_social', 'Empresa')
        ws[f'B{row}'].font = Font(name='Calibri', size=14, bold=True)
        row += 1
        
        ws[f'B{row}'] = f"CNPJ: {empresa.get('cnpj', '-')}"
        ws[f'B{row}'].font = self.small_font
        row += 1
        
        ws[f'B{row}'] = f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ws[f'B{row}'].font = self.small_font
        row += 3
        
        # Score
        ws[f'B{row}'] = "SCORE DE SAÚDE FINANCEIRA"
        ws[f'B{row}'].font = self.bold_font
        row += 1
        
        ws.merge_cells(f'B{row}:B{row+1}')
        ws[f'B{row}'] = saude['pontos']
        ws[f'B{row}'].font = Font(name='Calibri', size=48, bold=True, color=self.COLORS['primary'])
        ws[f'B{row}'].alignment = self.center
        
        ws[f'C{row}'] = saude['status']
        if saude['status'] == 'Excelente':
            ws[f'C{row}'].fill = self.success_fill
        elif saude['status'] == 'Bom':
            ws[f'C{row}'].fill = PatternFill(start_color='DBEAFE', end_color='DBEAFE', fill_type='solid')
        elif saude['status'] == 'Regular':
            ws[f'C{row}'].fill = self.warning_fill
        else:
            ws[f'C{row}'].fill = self.danger_fill
        ws[f'C{row}'].font = self.bold_font
        ws[f'C{row}'].alignment = self.center
        row += 3
        
        # Resumo Financeiro
        ws[f'B{row}'] = "RESUMO DO PERÍODO"
        ws[f'B{row}'].font = self.bold_font
        row += 1
        
        resumo = [
            ('Período Analisado', f"{ind.get('meses_analisados', 0)} meses"),
            ('Faturamento Total', ind.get('receita_total', 0)),
            ('Lucro Líquido', ind.get('lucro_liquido', 0)),
            ('Margem Líquida', ind.get('margem_liquida', 0) / 100),
            ('Liquidez Corrente', ind.get('liquidez_corrente', 0)),
            ('Endividamento', ind.get('endividamento_geral', 0) / 100),
            ('Variação Receita', ind.get('variacao_receita', 0) / 100),
        ]
        
        for label, valor in resumo:
            ws[f'B{row}'] = label
            ws[f'B{row}'].font = self.normal_font
            ws[f'B{row}'].border = self.thin_border
            
            ws[f'C{row}'] = valor
            ws[f'C{row}'].border = self.thin_border
            ws[f'C{row}'].alignment = self.right
            
            if isinstance(valor, (int, float)) and valor != ind.get('meses_analisados', 0):
                if 'Margem' in label or 'Endiv' in label or 'Variação' in label:
                    ws[f'C{row}'].number_format = '0.0%'
                elif 'Liquidez' in label:
                    ws[f'C{row}'].number_format = '0.00'
                else:
                    ws[f'C{row}'].number_format = self.currency_format
            
            row += 1
        
        row += 2
        
        # Alertas
        if alertas:
            ws[f'B{row}'] = "PRINCIPAIS ALERTAS"
            ws[f'B{row}'].font = self.bold_font
            row += 1
            
            criticos = [a for a in alertas if a.get('severidade') == 'critico'][:3]
            atencao = [a for a in alertas if a.get('severidade') == 'atencao'][:3]
            
            for a in criticos:
                ws[f'B{row}'] = f"🔴 {a.get('titulo', '')}"
                ws[f'B{row}'].font = Font(name='Calibri', size=9, color=self.COLORS['danger'])
                row += 1
            
            for a in atencao:
                ws[f'B{row}'] = f"⚠️ {a.get('titulo', '')}"
                ws[f'B{row}'].font = Font(name='Calibri', size=9, color=self.COLORS['warning'])
                row += 1
    
    def _criar_aba_dre(self, empresa: Dict, dados: List[Dict], ind: Dict):
        ws = self.wb.create_sheet("DRE")
        ws.sheet_properties.tabColor = self.COLORS['success']
        
        ws.column_dimensions['A'].width = 3
        ws.column_dimensions['B'].width = 35
        ws.column_dimensions['C'].width = 18
        ws.column_dimensions['D'].width = 12
        
        row = 2
        
        ws[f'B{row}'] = "DEMONSTRAÇÃO DO RESULTADO DO EXERCÍCIO"
        ws[f'B{row}'].font = self.title_font
        row += 1
        
        ws[f'B{row}'] = empresa.get('razao_social', 'Empresa')
        ws[f'B{row}'].font = self.small_font
        row += 2
        
        # Cabeçalho
        headers = ['Descrição', 'Valor', '% Receita']
        for i, h in enumerate(headers):
            cell = ws.cell(row=row, column=i+2, value=h)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.thin_border
            cell.alignment = self.center
        row += 1
        
        rt = ind.get('receita_total', 1) or 1
        
        dre_items = [
            ('RECEITA BRUTA', ind.get('receita_total', 0), 1, True),
            ('(-) Custos dos Serviços/Produtos', -ind.get('custos_total', 0), -ind.get('custos_total', 0)/rt, False),
            ('(=) LUCRO BRUTO', ind.get('lucro_bruto', 0), ind.get('margem_bruta', 0)/100, True),
            ('(-) Despesas Operacionais', -ind.get('despesas_total', 0), -ind.get('despesas_total', 0)/rt, False),
            ('(-) Impostos e Deduções', -ind.get('impostos_total', 0), -ind.get('carga_tributaria', 0)/100, False),
            ('(=) LUCRO LÍQUIDO', ind.get('lucro_liquido', 0), ind.get('margem_liquida', 0)/100, True),
        ]
        
        for desc, valor, pct, destaque in dre_items:
            ws.cell(row=row, column=2, value=desc).border = self.thin_border
            
            cell_valor = ws.cell(row=row, column=3, value=valor)
            cell_valor.number_format = self.currency_format
            cell_valor.border = self.thin_border
            cell_valor.alignment = self.right
            
            cell_pct = ws.cell(row=row, column=4, value=pct)
            cell_pct.number_format = '0.0%'
            cell_pct.border = self.thin_border
            cell_pct.alignment = self.center
            
            if destaque:
                ws.cell(row=row, column=2).font = self.bold_font
                ws.cell(row=row, column=2).fill = self.highlight_fill
                cell_valor.font = self.bold_font
                cell_valor.fill = self.highlight_fill
                cell_pct.fill = self.highlight_fill
            
            row += 1
        
        # Evolução mensal
        if dados and len(dados) >= 3:
            row += 2
            ws[f'B{row}'] = "EVOLUÇÃO MENSAL"
            ws[f'B{row}'].font = self.bold_font
            row += 1
            
            dados_sorted = sorted(dados, key=lambda x: (x.get('ano', 0), x.get('mes', 0)))[-12:]
            
            headers = ['Mês', 'Receita', 'Custos', 'Despesas', 'Lucro', 'Margem']
            for i, h in enumerate(headers):
                cell = ws.cell(row=row, column=i+2, value=h)
                cell.font = self.header_font
                cell.fill = self.subheader_fill
                cell.border = self.thin_border
                cell.alignment = self.center
            row += 1
            
            for d in dados_sorted:
                mes = f"{d.get('mes', 0):02d}/{d.get('ano', 0)}"
                rec = d.get('receita', 0) or d.get('receita_bruta', 0) or 0
                cus = d.get('custos', 0) or d.get('custos_total', 0) or 0
                des = d.get('despesas', 0) or d.get('despesas_operacionais', 0) or 0
                luc = d.get('lucro_liquido', 0) or (rec - cus - des - (d.get('impostos', 0) or 0))
                mar = luc / rec if rec > 0 else 0
                
                valores = [mes, rec, cus, des, luc, mar]
                for i, v in enumerate(valores):
                    cell = ws.cell(row=row, column=i+2, value=v)
                    cell.border = self.thin_border
                    if i == 0:
                        cell.alignment = self.center
                    elif i == 5:
                        cell.number_format = '0.0%'
                        cell.alignment = self.center
                    else:
                        cell.number_format = self.currency_format
                        cell.alignment = self.right
                row += 1
    
    def _criar_aba_indicadores(self, empresa: Dict, ind: Dict):
        ws = self.wb.create_sheet("Indicadores")
        ws.sheet_properties.tabColor = self.COLORS['primary_light']
        
        ws.column_dimensions['A'].width = 3
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 30
        
        row = 2
        
        ws[f'B{row}'] = "INDICADORES FINANCEIROS"
        ws[f'B{row}'].font = self.title_font
        row += 2
        
        def _add_section(title, items):
            nonlocal row
            ws[f'B{row}'] = title
            ws[f'B{row}'].font = self.bold_font
            ws[f'B{row}'].fill = self.header_fill
            ws[f'B{row}'].font = self.header_font
            ws.merge_cells(f'B{row}:E{row}')
            row += 1
            
            for nome, valor, formato, status in items:
                ws.cell(row=row, column=2, value=nome).border = self.thin_border
                
                cell_v = ws.cell(row=row, column=3, value=valor)
                cell_v.border = self.thin_border
                cell_v.alignment = self.center
                if formato == 'pct':
                    cell_v.number_format = '0.0%'
                elif formato == 'num':
                    cell_v.number_format = '0.00'
                elif formato == 'moeda':
                    cell_v.number_format = self.currency_format
                elif formato == 'dias':
                    cell_v.number_format = '0'
                
                cell_s = ws.cell(row=row, column=4, value=status)
                cell_s.border = self.thin_border
                cell_s.alignment = self.center
                
                if 'Excelente' in status or 'Baixo' in status and 'Endiv' in nome:
                    cell_s.fill = self.success_fill
                elif 'Bom' in status or 'Adequado' in status or 'Moderado' in status:
                    cell_s.fill = PatternFill(start_color='DBEAFE', end_color='DBEAFE', fill_type='solid')
                elif 'Crítico' in status or 'Prejuízo' in status or 'Muito' in status:
                    cell_s.fill = self.danger_fill
                elif 'Elevado' in status or 'Alto' in status:
                    cell_s.fill = self.warning_fill
                
                row += 1
            row += 1
        
        # Rentabilidade
        _add_section("INDICADORES DE RENTABILIDADE", [
            ('Margem Bruta', ind.get('margem_bruta', 0)/100, 'pct', 'Excelente' if ind.get('margem_bruta', 0) >= 50 else 'Bom' if ind.get('margem_bruta', 0) >= 35 else 'Adequado'),
            ('Margem Líquida', ind.get('margem_liquida', 0)/100, 'pct', 'Excelente' if ind.get('margem_liquida', 0) >= 20 else 'Bom' if ind.get('margem_liquida', 0) >= 10 else 'Adequado' if ind.get('margem_liquida', 0) >= 0 else 'Prejuízo'),
            ('ROE', ind.get('roe', 0)/100, 'pct', 'Excelente' if ind.get('roe', 0) >= 25 else 'Bom' if ind.get('roe', 0) >= 15 else 'Moderado'),
            ('ROA', ind.get('roa', 0)/100, 'pct', 'Excelente' if ind.get('roa', 0) >= 15 else 'Bom' if ind.get('roa', 0) >= 8 else 'Moderado'),
            ('Giro do Ativo', ind.get('giro_ativo', 0), 'num', 'Alto' if ind.get('giro_ativo', 0) >= 2 else 'Adequado' if ind.get('giro_ativo', 0) >= 1 else 'Baixo'),
        ])
        
        # Liquidez
        _add_section("INDICADORES DE LIQUIDEZ", [
            ('Liquidez Corrente', ind.get('liquidez_corrente', 0), 'num', 'Excelente' if ind.get('liquidez_corrente', 0) >= 2 else 'Bom' if ind.get('liquidez_corrente', 0) >= 1.5 else 'Adequado' if ind.get('liquidez_corrente', 0) >= 1 else 'Crítico'),
            ('Liquidez Seca', ind.get('liquidez_seca', 0), 'num', 'Excelente' if ind.get('liquidez_seca', 0) >= 1.5 else 'Bom' if ind.get('liquidez_seca', 0) >= 1 else 'Adequado'),
            ('Liquidez Imediata', ind.get('liquidez_imediata', 0), 'num', 'Alto' if ind.get('liquidez_imediata', 0) >= 0.5 else 'Adequado' if ind.get('liquidez_imediata', 0) >= 0.2 else 'Baixo'),
            ('Capital de Giro', ind.get('capital_giro', 0), 'moeda', 'Positivo' if ind.get('capital_giro', 0) > 0 else 'Negativo'),
        ])
        
        # Endividamento
        _add_section("INDICADORES DE ENDIVIDAMENTO", [
            ('Endividamento Geral', ind.get('endividamento_geral', 0)/100, 'pct', 'Baixo' if ind.get('endividamento_geral', 0) <= 30 else 'Moderado' if ind.get('endividamento_geral', 0) <= 50 else 'Elevado' if ind.get('endividamento_geral', 0) <= 70 else 'Crítico'),
            ('Composição Endiv.', ind.get('composicao_endividamento', 0)/100, 'pct', 'Equilibrado' if ind.get('composicao_endividamento', 0) <= 50 else 'Concentrado CP'),
            ('Prazo Médio Receb.', ind.get('pmr', 0), 'dias', 'Excelente' if ind.get('pmr', 0) <= 30 else 'Bom' if ind.get('pmr', 0) <= 45 else 'Elevado' if ind.get('pmr', 0) <= 60 else 'Muito Alto'),
            ('Carga Tributária', ind.get('carga_tributaria', 0)/100, 'pct', 'Baixa' if ind.get('carga_tributaria', 0) <= 10 else 'Moderada' if ind.get('carga_tributaria', 0) <= 18 else 'Alta'),
        ])
    
    def _criar_aba_balanco(self, empresa: Dict, ind: Dict):
        ws = self.wb.create_sheet("Balanço")
        ws.sheet_properties.tabColor = self.COLORS['warning']
        
        ws.column_dimensions['A'].width = 3
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 18
        ws.column_dimensions['D'].width = 12
        
        row = 2
        
        ws[f'B{row}'] = "ESTRUTURA PATRIMONIAL"
        ws[f'B{row}'].font = self.title_font
        row += 2
        
        at = ind.get('ativo_total', 0) or 1
        
        # Ativo
        ws[f'B{row}'] = "ATIVO"
        ws[f'B{row}'].font = self.header_font
        ws[f'B{row}'].fill = self.header_fill
        ws.merge_cells(f'B{row}:D{row}')
        row += 1
        
        ativo_items = [
            ('Ativo Total', ind.get('ativo_total', 0), 1),
            ('  Ativo Circulante', ind.get('ativo_circulante', 0), ind.get('ativo_circulante', 0)/at),
            ('    Disponibilidades', ind.get('disponivel', 0), ind.get('disponivel', 0)/at),
        ]
        
        for desc, valor, pct in ativo_items:
            ws.cell(row=row, column=2, value=desc).border = self.thin_border
            cell_v = ws.cell(row=row, column=3, value=valor)
            cell_v.number_format = self.currency_format
            cell_v.border = self.thin_border
            cell_v.alignment = self.right
            cell_p = ws.cell(row=row, column=4, value=pct)
            cell_p.number_format = '0.0%'
            cell_p.border = self.thin_border
            cell_p.alignment = self.center
            if 'Total' in desc:
                ws.cell(row=row, column=2).font = self.bold_font
                ws.cell(row=row, column=2).fill = self.highlight_fill
                cell_v.fill = self.highlight_fill
                cell_p.fill = self.highlight_fill
            row += 1
        
        row += 1
        
        # Passivo + PL
        ws[f'B{row}'] = "PASSIVO + PATRIMÔNIO LÍQUIDO"
        ws[f'B{row}'].font = self.header_font
        ws[f'B{row}'].fill = self.header_fill
        ws.merge_cells(f'B{row}:D{row}')
        row += 1
        
        passivo_items = [
            ('Passivo + PL', at, 1),
            ('  Passivo Circulante', ind.get('passivo_circulante', 0), ind.get('passivo_circulante', 0)/at),
            ('  Passivo Não Circulante', ind.get('passivo_nao_circulante', 0), ind.get('passivo_nao_circulante', 0)/at),
            ('  Patrimônio Líquido', ind.get('patrimonio_liquido', 0), ind.get('patrimonio_liquido', 0)/at),
        ]
        
        for desc, valor, pct in passivo_items:
            ws.cell(row=row, column=2, value=desc).border = self.thin_border
            cell_v = ws.cell(row=row, column=3, value=valor)
            cell_v.number_format = self.currency_format
            cell_v.border = self.thin_border
            cell_v.alignment = self.right
            cell_p = ws.cell(row=row, column=4, value=pct)
            cell_p.number_format = '0.0%'
            cell_p.border = self.thin_border
            cell_p.alignment = self.center
            if 'Passivo + PL' in desc:
                ws.cell(row=row, column=2).font = self.bold_font
                ws.cell(row=row, column=2).fill = self.highlight_fill
                cell_v.fill = self.highlight_fill
                cell_p.fill = self.highlight_fill
            row += 1
    
    def _criar_aba_evolucao(self, empresa: Dict, dados: List[Dict]):
        ws = self.wb.create_sheet("Evolução")
        ws.sheet_properties.tabColor = self.COLORS['primary']
        
        if not dados or len(dados) < 2:
            ws['B2'] = "Dados insuficientes para análise de evolução"
            return
        
        ws.column_dimensions['A'].width = 3
        
        row = 2
        ws[f'B{row}'] = "ANÁLISE DE EVOLUÇÃO"
        ws[f'B{row}'].font = self.title_font
        row += 2
        
        dados_sorted = sorted(dados, key=lambda x: (x.get('ano', 0), x.get('mes', 0)))[-12:]
        
        # Dados para gráficos
        headers = ['Mês', 'Receita', 'Lucro']
        for i, h in enumerate(headers):
            cell = ws.cell(row=row, column=i+2, value=h)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.thin_border
        row += 1
        
        start_row = row
        for d in dados_sorted:
            mes = f"{d.get('mes', 0):02d}/{d.get('ano', 0)}"
            rec = d.get('receita', 0) or d.get('receita_bruta', 0) or 0
            luc = d.get('lucro_liquido', 0) or 0
            
            ws.cell(row=row, column=2, value=mes).border = self.thin_border
            cell_r = ws.cell(row=row, column=3, value=rec)
            cell_r.number_format = self.currency_format
            cell_r.border = self.thin_border
            cell_l = ws.cell(row=row, column=4, value=luc)
            cell_l.number_format = self.currency_format
            cell_l.border = self.thin_border
            row += 1
        
        end_row = row - 1
        
        # Gráfico de linha
        if end_row > start_row:
            chart = LineChart()
            chart.title = "Evolução de Receita e Lucro"
            chart.style = 10
            chart.y_axis.title = "Valor (R$)"
            chart.x_axis.title = "Mês"
            
            data = Reference(ws, min_col=3, min_row=start_row-1, max_col=4, max_row=end_row)
            cats = Reference(ws, min_col=2, min_row=start_row, max_row=end_row)
            chart.add_data(data, titles_from_data=True)
            chart.set_categories(cats)
            chart.shape = 4
            chart.width = 18
            chart.height = 10
            
            ws.add_chart(chart, "F4")
    
    def _criar_aba_alertas(self, empresa: Dict, alertas: List[Dict], ind: Dict):
        ws = self.wb.create_sheet("Alertas")
        ws.sheet_properties.tabColor = self.COLORS['danger']
        
        ws.column_dimensions['A'].width = 3
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 50
        ws.column_dimensions['D'].width = 15
        
        row = 2
        ws[f'B{row}'] = "ALERTAS E RECOMENDAÇÕES"
        ws[f'B{row}'].font = self.title_font
        row += 2
        
        if not alertas:
            alertas = []
        
        # Cabeçalho
        headers = ['Severidade', 'Alerta', 'Período']
        for i, h in enumerate(headers):
            cell = ws.cell(row=row, column=i+2, value=h)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.thin_border
        row += 1
        
        for a in alertas[:20]:
            sev = a.get('severidade', 'info')
            
            cell_s = ws.cell(row=row, column=2, value=sev.upper())
            cell_s.border = self.thin_border
            cell_s.alignment = self.center
            if sev == 'critico':
                cell_s.fill = self.danger_fill
                cell_s.font = Font(bold=True, color=self.COLORS['danger'])
            elif sev == 'atencao':
                cell_s.fill = self.warning_fill
                cell_s.font = Font(color=self.COLORS['warning'])
            else:
                cell_s.fill = self.success_fill
                cell_s.font = Font(color=self.COLORS['success'])
            
            cell_t = ws.cell(row=row, column=3, value=a.get('titulo', ''))
            cell_t.border = self.thin_border
            cell_t.alignment = self.left
            
            cell_p = ws.cell(row=row, column=4, value=a.get('periodo_referencia', ''))
            cell_p.border = self.thin_border
            cell_p.alignment = self.center
            
            row += 1
        
        row += 2
        
        # Recomendações
        ws[f'B{row}'] = "RECOMENDAÇÕES"
        ws[f'B{row}'].font = self.bold_font
        row += 1
        
        recs = []
        if ind.get('liquidez_corrente', 0) < 1:
            recs.append("• Priorizar aumento de capital de giro para melhorar liquidez")
        if ind.get('endividamento_geral', 0) > 70:
            recs.append("• Avaliar renegociação de dívidas e evitar novos empréstimos")
        if ind.get('margem_liquida', 0) < 5:
            recs.append("• Revisar estrutura de custos e política de precificação")
        if ind.get('pmr', 0) > 60:
            recs.append("• Implementar política de cobrança mais eficiente")
        if not recs:
            recs = ["• Manter as boas práticas de gestão financeira", "• Continuar monitorando indicadores mensalmente"]
        
        for r in recs:
            ws[f'B{row}'] = r
            ws[f'B{row}'].font = self.normal_font
            row += 1


def gerar_excel(empresa: Dict, dados_mensais: List[Dict], analise: Dict = None, config: Dict = None, alertas: List[Dict] = None) -> bytes:
    return ExcelGenerator(config).gerar_relatorio(empresa, dados_mensais, analise, alertas, config)
