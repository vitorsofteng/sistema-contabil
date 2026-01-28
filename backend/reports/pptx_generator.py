#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Apresentação PowerPoint Profissional
Sistema ContaGestor - Para Contadores com Múltiplas Empresas
"""

import io
import statistics
from datetime import datetime
from typing import Dict, List, Optional

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False


class PowerPointGenerator:
    """Gerador de apresentações PowerPoint profissionais para contadores."""
    
    COLORS = {
        'primary': RGBColor(30, 64, 175),
        'primary_light': RGBColor(59, 130, 246),
        'success': RGBColor(5, 150, 105),
        'warning': RGBColor(217, 119, 6),
        'danger': RGBColor(220, 38, 38),
        'gray_900': RGBColor(17, 24, 39),
        'gray_700': RGBColor(55, 65, 81),
        'gray_500': RGBColor(107, 114, 128),
        'gray_300': RGBColor(209, 213, 219),
        'gray_100': RGBColor(243, 244, 246),
        'white': RGBColor(255, 255, 255),
        'black': RGBColor(0, 0, 0),
    }
    
    def __init__(self, config: Dict = None):
        if not PPTX_AVAILABLE:
            raise ImportError("python-pptx não instalado")
        
        self.config = config or {}
        self.prs = Presentation()
        self.prs.slide_width = Inches(13.333)
        self.prs.slide_height = Inches(7.5)
        
        self._parse_colors()
    
    def _parse_colors(self):
        if 'cor_primaria' in self.config:
            try:
                hex_color = self.config['cor_primaria'].replace('#', '')
                r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
                self.COLORS['primary'] = RGBColor(r, g, b)
            except:
                pass
    
    def _fmt_moeda(self, valor):
        if valor is None: return "—"
        try:
            v = float(valor)
            return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except: return "—"
    
    def _fmt_pct(self, valor, decimals=1):
        if valor is None: return "—"
        try: return f"{float(valor):.{decimals}f}%"
        except: return "—"
    
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
            'ativo_total': at, 'patrimonio_liquido': pl, 'meses_analisados': n,
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
        
        if pontos >= 80: return {'pontos': pontos, 'status': 'Excelente', 'cor': self.COLORS['success']}
        if pontos >= 60: return {'pontos': pontos, 'status': 'Bom', 'cor': self.COLORS['primary_light']}
        if pontos >= 40: return {'pontos': pontos, 'status': 'Regular', 'cor': self.COLORS['warning']}
        return {'pontos': pontos, 'status': 'Crítico', 'cor': self.COLORS['danger']}
    
    def gerar_apresentacao(self, empresa: Dict, dados_mensais: List[Dict], analise: Dict = None, alertas: List[Dict] = None, config: Dict = None) -> bytes:
        self.config = config or self.config
        self.prs = Presentation()
        self.prs.slide_width = Inches(13.333)
        self.prs.slide_height = Inches(7.5)
        self._parse_colors()
        
        ind = self._calcular_indicadores(dados_mensais, analise)
        saude = self._classificar_saude(ind)
        
        self._criar_slide_capa(empresa, ind, saude)
        self._criar_slide_resumo(empresa, ind, saude)
        self._criar_slide_dre(empresa, ind)
        self._criar_slide_indicadores_rentabilidade(empresa, ind)
        self._criar_slide_indicadores_liquidez(empresa, ind)
        self._criar_slide_evolucao(empresa, dados_mensais)
        self._criar_slide_alertas(empresa, alertas, ind)
        self._criar_slide_recomendacoes(empresa, ind)
        self._criar_slide_contato()
        
        buffer = io.BytesIO()
        self.prs.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _add_text_box(self, slide, left, top, width, height, text, font_size=14, bold=False, color=None, align=PP_ALIGN.LEFT):
        """Adiciona caixa de texto."""
        box = slide.shapes.add_textbox(left, top, width, height)
        tf = box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(font_size)
        p.font.bold = bold
        p.font.color.rgb = color or self.COLORS['black']
        p.alignment = align
        return box
    
    def _add_shape_with_text(self, slide, shape_type, left, top, width, height, text, fill_color, text_color=None, font_size=12, bold=False):
        """Adiciona forma com texto."""
        shape = slide.shapes.add_shape(shape_type, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
        shape.line.fill.background()
        
        tf = shape.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(font_size)
        p.font.bold = bold
        p.font.color.rgb = text_color or self.COLORS['white']
        p.alignment = PP_ALIGN.CENTER
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER
        
        return shape
    
    def _criar_slide_capa(self, empresa: Dict, ind: Dict, saude: Dict):
        """Cria slide de capa."""
        layout = self.prs.slide_layouts[6]
        slide = self.prs.slides.add_slide(layout)
        
        # Background
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, self.prs.slide_width, self.prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = self.COLORS['primary']
        bg.line.fill.background()
        
        # Nome do escritório
        nome_escritorio = self.config.get('nome_escritorio', 'ContaGestor')
        self._add_text_box(slide, Inches(0.5), Inches(1), Inches(12), Inches(0.8),
                          nome_escritorio, font_size=36, bold=True, color=self.COLORS['white'], align=PP_ALIGN.CENTER)
        
        # Título
        self._add_text_box(slide, Inches(0.5), Inches(2), Inches(12), Inches(1),
                          "DIAGNÓSTICO FINANCEIRO", font_size=44, bold=True, color=self.COLORS['white'], align=PP_ALIGN.CENTER)
        
        # Empresa
        nome_empresa = empresa.get('razao_social') or empresa.get('nome_fantasia') or 'Empresa'
        self._add_text_box(slide, Inches(0.5), Inches(3.2), Inches(12), Inches(0.6),
                          nome_empresa, font_size=24, color=self.COLORS['gray_300'], align=PP_ALIGN.CENTER)
        
        # Score
        score_shape = self._add_shape_with_text(slide, MSO_SHAPE.OVAL, Inches(5.5), Inches(4.2), Inches(2.3), Inches(2.3),
                                                str(saude['pontos']), self.COLORS['white'], self.COLORS['primary'], font_size=48, bold=True)
        
        # Status
        self._add_text_box(slide, Inches(0.5), Inches(6.5), Inches(12), Inches(0.5),
                          f"Score de Saúde: {saude['status']}", font_size=20, bold=True, color=self.COLORS['white'], align=PP_ALIGN.CENTER)
        
        # Data
        data = datetime.now().strftime("%d/%m/%Y")
        self._add_text_box(slide, Inches(0.5), Inches(7), Inches(12), Inches(0.3),
                          data, font_size=12, color=self.COLORS['gray_300'], align=PP_ALIGN.CENTER)
    
    def _criar_slide_resumo(self, empresa: Dict, ind: Dict, saude: Dict):
        """Cria slide de resumo executivo."""
        layout = self.prs.slide_layouts[6]
        slide = self.prs.slides.add_slide(layout)
        
        # Título
        self._add_text_box(slide, Inches(0.5), Inches(0.3), Inches(12), Inches(0.6),
                          "RESUMO EXECUTIVO", font_size=28, bold=True, color=self.COLORS['primary'])
        
        # Linha
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(0.9), Inches(12.3), Inches(0.03))
        line.fill.solid()
        line.fill.fore_color.rgb = self.COLORS['primary']
        line.line.fill.background()
        
        # Cards de indicadores
        cards = [
            ("Faturamento", self._fmt_moeda(ind.get('receita_total')), f"{ind.get('meses_analisados', 0)} meses"),
            ("Lucro Líquido", self._fmt_moeda(ind.get('lucro_liquido')), self._fmt_pct(ind.get('margem_liquida')) + " margem"),
            ("Liquidez", f"{ind.get('liquidez_corrente', 0):.2f}", "Corrente"),
            ("Endividamento", self._fmt_pct(ind.get('endividamento_geral')), "do ativo"),
        ]
        
        card_width = Inches(3)
        card_height = Inches(1.8)
        start_x = Inches(0.5)
        gap = Inches(0.2)
        
        for i, (titulo, valor, subtitulo) in enumerate(cards):
            x = start_x + i * (card_width + gap)
            
            # Card background
            card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.2), card_width, card_height)
            card.fill.solid()
            card.fill.fore_color.rgb = self.COLORS['gray_100']
            card.line.color.rgb = self.COLORS['gray_300']
            
            # Título do card
            self._add_text_box(slide, x + Inches(0.1), Inches(1.3), card_width - Inches(0.2), Inches(0.4),
                              titulo, font_size=12, color=self.COLORS['gray_500'], align=PP_ALIGN.CENTER)
            
            # Valor
            self._add_text_box(slide, x + Inches(0.1), Inches(1.7), card_width - Inches(0.2), Inches(0.8),
                              valor, font_size=24, bold=True, color=self.COLORS['primary'], align=PP_ALIGN.CENTER)
            
            # Subtítulo
            self._add_text_box(slide, x + Inches(0.1), Inches(2.5), card_width - Inches(0.2), Inches(0.3),
                              subtitulo, font_size=10, color=self.COLORS['gray_500'], align=PP_ALIGN.CENTER)
        
        # Análise textual
        ml = ind.get('margem_liquida', 0)
        lc = ind.get('liquidez_corrente', 0)
        endiv = ind.get('endividamento_geral', 0)
        
        if ml >= 20: a_ml = "excelente rentabilidade"
        elif ml >= 10: a_ml = "boa rentabilidade"
        elif ml >= 5: a_ml = "rentabilidade moderada"
        elif ml >= 0: a_ml = "rentabilidade baixa"
        else: a_ml = "operando com prejuízo"
        
        a_lc = "liquidez saudável" if lc >= 1.5 else "liquidez adequada" if lc >= 1 else "liquidez preocupante"
        a_end = "estrutura equilibrada" if endiv <= 50 else "endividamento moderado" if endiv <= 70 else "alto endividamento"
        
        nome = empresa.get('razao_social', 'A empresa')[:50]
        texto = f"{nome} apresenta {a_ml} com margem de {ml:.1f}%, {a_lc} e {a_end}."
        
        self._add_text_box(slide, Inches(0.5), Inches(3.3), Inches(12.3), Inches(1),
                          texto, font_size=16, color=self.COLORS['gray_700'])
        
        # Tendência
        var = ind.get('variacao_receita', 0)
        if var > 10:
            tend_text = f"📈 Receita em crescimento: +{var:.1f}%"
            tend_color = self.COLORS['success']
        elif var < -10:
            tend_text = f"📉 Receita em queda: {var:.1f}%"
            tend_color = self.COLORS['danger']
        else:
            tend_text = f"➡️ Receita estável: {var:+.1f}%"
            tend_color = self.COLORS['gray_700']
        
        self._add_text_box(slide, Inches(0.5), Inches(4.3), Inches(12.3), Inches(0.5),
                          tend_text, font_size=18, bold=True, color=tend_color)
    
    def _criar_slide_dre(self, empresa: Dict, ind: Dict):
        """Cria slide de DRE."""
        layout = self.prs.slide_layouts[6]
        slide = self.prs.slides.add_slide(layout)
        
        # Título
        self._add_text_box(slide, Inches(0.5), Inches(0.3), Inches(12), Inches(0.6),
                          "DEMONSTRAÇÃO DO RESULTADO", font_size=28, bold=True, color=self.COLORS['primary'])
        
        # Linha
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(0.9), Inches(12.3), Inches(0.03))
        line.fill.solid()
        line.fill.fore_color.rgb = self.COLORS['primary']
        line.line.fill.background()
        
        # Tabela DRE
        rt = ind.get('receita_total', 1) or 1
        
        dre_items = [
            ("RECEITA BRUTA", self._fmt_moeda(rt), "100,0%", True),
            ("(-) Custos", self._fmt_moeda(-ind.get('custos_total', 0)), self._fmt_pct(-ind.get('custos_total', 0)/rt*100), False),
            ("(=) LUCRO BRUTO", self._fmt_moeda(ind.get('lucro_bruto')), self._fmt_pct(ind.get('margem_bruta')), True),
            ("(-) Despesas", self._fmt_moeda(-ind.get('despesas_total', 0)), self._fmt_pct(-ind.get('despesas_total', 0)/rt*100), False),
            ("(-) Impostos", self._fmt_moeda(-ind.get('impostos_total', 0)), self._fmt_pct(-ind.get('carga_tributaria')), False),
            ("(=) LUCRO LÍQUIDO", self._fmt_moeda(ind.get('lucro_liquido')), self._fmt_pct(ind.get('margem_liquida')), True),
        ]
        
        y = Inches(1.3)
        for desc, valor, pct, destaque in dre_items:
            # Background
            if destaque:
                bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), y, Inches(12.3), Inches(0.6))
                bg.fill.solid()
                bg.fill.fore_color.rgb = self.COLORS['primary'] if "LÍQUIDO" in desc else self.COLORS['gray_100']
                bg.line.fill.background()
            
            cor_texto = self.COLORS['white'] if destaque and "LÍQUIDO" in desc else self.COLORS['gray_900']
            
            self._add_text_box(slide, Inches(0.6), y + Inches(0.1), Inches(5), Inches(0.4),
                              desc, font_size=14, bold=destaque, color=cor_texto)
            self._add_text_box(slide, Inches(6), y + Inches(0.1), Inches(3.5), Inches(0.4),
                              valor, font_size=14, bold=destaque, color=cor_texto, align=PP_ALIGN.RIGHT)
            self._add_text_box(slide, Inches(10), y + Inches(0.1), Inches(2.5), Inches(0.4),
                              pct, font_size=14, color=cor_texto, align=PP_ALIGN.RIGHT)
            
            y += Inches(0.7)
    
    def _criar_slide_indicadores_rentabilidade(self, empresa: Dict, ind: Dict):
        """Cria slide de indicadores de rentabilidade."""
        layout = self.prs.slide_layouts[6]
        slide = self.prs.slides.add_slide(layout)
        
        # Título
        self._add_text_box(slide, Inches(0.5), Inches(0.3), Inches(12), Inches(0.6),
                          "INDICADORES DE RENTABILIDADE", font_size=28, bold=True, color=self.COLORS['primary'])
        
        # Linha
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(0.9), Inches(12.3), Inches(0.03))
        line.fill.solid()
        line.fill.fore_color.rgb = self.COLORS['primary']
        line.line.fill.background()
        
        indicadores = [
            ("Margem Bruta", self._fmt_pct(ind.get('margem_bruta')), "Lucro bruto / Receita", 
             "Excelente" if ind.get('margem_bruta', 0) >= 50 else "Bom" if ind.get('margem_bruta', 0) >= 35 else "Adequado"),
            ("Margem Líquida", self._fmt_pct(ind.get('margem_liquida')), "Lucro líquido / Receita",
             "Excelente" if ind.get('margem_liquida', 0) >= 20 else "Bom" if ind.get('margem_liquida', 0) >= 10 else "Adequado" if ind.get('margem_liquida', 0) >= 0 else "Prejuízo"),
            ("ROE", self._fmt_pct(ind.get('roe')), "Retorno sobre patrimônio",
             "Excelente" if ind.get('roe', 0) >= 25 else "Bom" if ind.get('roe', 0) >= 15 else "Moderado"),
            ("Giro do Ativo", f"{ind.get('giro_ativo', 0):.2f}x", "Receita / Ativo total",
             "Alto" if ind.get('giro_ativo', 0) >= 2 else "Adequado" if ind.get('giro_ativo', 0) >= 1 else "Baixo"),
        ]
        
        y = Inches(1.3)
        for nome, valor, desc, status in indicadores:
            # Card
            card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), y, Inches(12.3), Inches(1.3))
            card.fill.solid()
            card.fill.fore_color.rgb = self.COLORS['gray_100']
            card.line.color.rgb = self.COLORS['gray_300']
            
            self._add_text_box(slide, Inches(0.7), y + Inches(0.2), Inches(4), Inches(0.4),
                              nome, font_size=16, bold=True, color=self.COLORS['gray_900'])
            self._add_text_box(slide, Inches(0.7), y + Inches(0.7), Inches(4), Inches(0.4),
                              desc, font_size=11, color=self.COLORS['gray_500'])
            
            self._add_text_box(slide, Inches(6), y + Inches(0.3), Inches(3), Inches(0.6),
                              valor, font_size=28, bold=True, color=self.COLORS['primary'], align=PP_ALIGN.CENTER)
            
            # Status badge
            status_color = self.COLORS['success'] if 'Excelente' in status or 'Alto' in status else self.COLORS['primary_light'] if 'Bom' in status or 'Adequado' in status else self.COLORS['warning'] if 'Moderado' in status else self.COLORS['danger']
            badge = self._add_shape_with_text(slide, MSO_SHAPE.ROUNDED_RECTANGLE, Inches(10), y + Inches(0.4), Inches(2.5), Inches(0.5),
                                              status, status_color, self.COLORS['white'], font_size=12, bold=True)
            
            y += Inches(1.45)
    
    def _criar_slide_indicadores_liquidez(self, empresa: Dict, ind: Dict):
        """Cria slide de indicadores de liquidez e endividamento."""
        layout = self.prs.slide_layouts[6]
        slide = self.prs.slides.add_slide(layout)
        
        # Título
        self._add_text_box(slide, Inches(0.5), Inches(0.3), Inches(12), Inches(0.6),
                          "LIQUIDEZ E ENDIVIDAMENTO", font_size=28, bold=True, color=self.COLORS['primary'])
        
        # Linha
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(0.9), Inches(12.3), Inches(0.03))
        line.fill.solid()
        line.fill.fore_color.rgb = self.COLORS['primary']
        line.line.fill.background()
        
        # Liquidez
        self._add_text_box(slide, Inches(0.5), Inches(1.2), Inches(6), Inches(0.4),
                          "LIQUIDEZ", font_size=16, bold=True, color=self.COLORS['gray_700'])
        
        liq_items = [
            ("Corrente", f"{ind.get('liquidez_corrente', 0):.2f}", 
             "Excelente" if ind.get('liquidez_corrente', 0) >= 2 else "Bom" if ind.get('liquidez_corrente', 0) >= 1.5 else "Adequado" if ind.get('liquidez_corrente', 0) >= 1 else "Crítico"),
            ("Seca", f"{ind.get('liquidez_seca', 0):.2f}",
             "Excelente" if ind.get('liquidez_seca', 0) >= 1.5 else "Bom" if ind.get('liquidez_seca', 0) >= 1 else "Adequado"),
            ("Imediata", f"{ind.get('liquidez_imediata', 0):.2f}",
             "Alto" if ind.get('liquidez_imediata', 0) >= 0.5 else "Adequado" if ind.get('liquidez_imediata', 0) >= 0.2 else "Baixo"),
        ]
        
        y = Inches(1.7)
        for nome, valor, status in liq_items:
            self._add_text_box(slide, Inches(0.7), y, Inches(2), Inches(0.35), nome, font_size=12, color=self.COLORS['gray_700'])
            self._add_text_box(slide, Inches(3), y, Inches(1.5), Inches(0.35), valor, font_size=14, bold=True, color=self.COLORS['primary'], align=PP_ALIGN.CENTER)
            
            status_color = self.COLORS['success'] if 'Excelente' in status or 'Alto' in status else self.COLORS['primary_light'] if 'Bom' in status or 'Adequado' in status else self.COLORS['danger']
            self._add_text_box(slide, Inches(4.8), y, Inches(1.5), Inches(0.35), status, font_size=10, color=status_color, align=PP_ALIGN.CENTER)
            y += Inches(0.5)
        
        # Endividamento
        self._add_text_box(slide, Inches(7), Inches(1.2), Inches(6), Inches(0.4),
                          "ENDIVIDAMENTO", font_size=16, bold=True, color=self.COLORS['gray_700'])
        
        endiv_items = [
            ("Geral", self._fmt_pct(ind.get('endividamento_geral')),
             "Baixo" if ind.get('endividamento_geral', 0) <= 30 else "Moderado" if ind.get('endividamento_geral', 0) <= 50 else "Elevado" if ind.get('endividamento_geral', 0) <= 70 else "Crítico"),
            ("Composição CP", self._fmt_pct(ind.get('composicao_endividamento')),
             "Equilibrado" if ind.get('composicao_endividamento', 0) <= 50 else "Concentrado"),
            ("PMR", f"{ind.get('pmr', 0):.0f} dias",
             "Bom" if ind.get('pmr', 0) <= 45 else "Elevado" if ind.get('pmr', 0) <= 60 else "Alto"),
        ]
        
        y = Inches(1.7)
        for nome, valor, status in endiv_items:
            self._add_text_box(slide, Inches(7.2), y, Inches(2), Inches(0.35), nome, font_size=12, color=self.COLORS['gray_700'])
            self._add_text_box(slide, Inches(9.5), y, Inches(1.5), Inches(0.35), valor, font_size=14, bold=True, color=self.COLORS['primary'], align=PP_ALIGN.CENTER)
            
            status_color = self.COLORS['success'] if 'Baixo' in status or 'Equilibrado' in status or 'Bom' in status else self.COLORS['warning'] if 'Moderado' in status or 'Concentrado' in status or 'Elevado' in status else self.COLORS['danger']
            self._add_text_box(slide, Inches(11.3), y, Inches(1.5), Inches(0.35), status, font_size=10, color=status_color, align=PP_ALIGN.CENTER)
            y += Inches(0.5)
        
        # Capital de Giro
        self._add_text_box(slide, Inches(0.5), Inches(4), Inches(12.3), Inches(0.5),
                          f"Capital de Giro: {self._fmt_moeda(ind.get('capital_giro'))}", 
                          font_size=18, bold=True, color=self.COLORS['primary'])
    
    def _criar_slide_evolucao(self, empresa: Dict, dados: List[Dict]):
        """Cria slide de evolução com gráfico."""
        layout = self.prs.slide_layouts[6]
        slide = self.prs.slides.add_slide(layout)
        
        # Título
        self._add_text_box(slide, Inches(0.5), Inches(0.3), Inches(12), Inches(0.6),
                          "EVOLUÇÃO FINANCEIRA", font_size=28, bold=True, color=self.COLORS['primary'])
        
        if not dados or len(dados) < 3:
            self._add_text_box(slide, Inches(0.5), Inches(3), Inches(12), Inches(1),
                              "Dados insuficientes para gráfico de evolução", font_size=18, color=self.COLORS['gray_500'], align=PP_ALIGN.CENTER)
            return
        
        # Linha
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(0.9), Inches(12.3), Inches(0.03))
        line.fill.solid()
        line.fill.fore_color.rgb = self.COLORS['primary']
        line.line.fill.background()
        
        # Gráfico de barras
        dados_sorted = sorted(dados, key=lambda x: (x.get('ano', 0), x.get('mes', 0)))[-12:]
        
        chart_data = CategoryChartData()
        chart_data.categories = [f"{d.get('mes', 0):02d}/{str(d.get('ano', 0))[-2:]}" for d in dados_sorted]
        
        receitas = [d.get('receita', 0) or d.get('receita_bruta', 0) or 0 for d in dados_sorted]
        lucros = [d.get('lucro_liquido', 0) or 0 for d in dados_sorted]
        
        chart_data.add_series('Receita', receitas)
        chart_data.add_series('Lucro', lucros)
        
        x, y, cx, cy = Inches(0.5), Inches(1.2), Inches(12.3), Inches(5.5)
        chart = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, x, y, cx, cy, chart_data).chart
        
        chart.has_legend = True
        chart.legend.include_in_layout = False
    
    def _criar_slide_alertas(self, empresa: Dict, alertas: List[Dict], ind: Dict):
        """Cria slide de alertas."""
        layout = self.prs.slide_layouts[6]
        slide = self.prs.slides.add_slide(layout)
        
        # Título
        self._add_text_box(slide, Inches(0.5), Inches(0.3), Inches(12), Inches(0.6),
                          "ALERTAS", font_size=28, bold=True, color=self.COLORS['primary'])
        
        # Linha
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(0.9), Inches(12.3), Inches(0.03))
        line.fill.solid()
        line.fill.fore_color.rgb = self.COLORS['primary']
        line.line.fill.background()
        
        if not alertas:
            self._add_text_box(slide, Inches(0.5), Inches(3), Inches(12), Inches(1),
                              "Nenhum alerta crítico identificado", font_size=18, color=self.COLORS['success'], align=PP_ALIGN.CENTER)
            return
        
        criticos = [a for a in alertas if a.get('severidade') == 'critico'][:4]
        atencao = [a for a in alertas if a.get('severidade') == 'atencao'][:4]
        
        y = Inches(1.2)
        
        if criticos:
            self._add_text_box(slide, Inches(0.5), y, Inches(12), Inches(0.4),
                              "🔴 CRÍTICOS", font_size=14, bold=True, color=self.COLORS['danger'])
            y += Inches(0.5)
            
            for a in criticos:
                self._add_text_box(slide, Inches(0.7), y, Inches(12), Inches(0.4),
                                  f"• {a.get('titulo', '')}", font_size=12, color=self.COLORS['gray_700'])
                y += Inches(0.4)
            y += Inches(0.3)
        
        if atencao:
            self._add_text_box(slide, Inches(0.5), y, Inches(12), Inches(0.4),
                              "⚠️ ATENÇÃO", font_size=14, bold=True, color=self.COLORS['warning'])
            y += Inches(0.5)
            
            for a in atencao:
                self._add_text_box(slide, Inches(0.7), y, Inches(12), Inches(0.4),
                                  f"• {a.get('titulo', '')}", font_size=12, color=self.COLORS['gray_700'])
                y += Inches(0.4)
    
    def _criar_slide_recomendacoes(self, empresa: Dict, ind: Dict):
        """Cria slide de recomendações."""
        layout = self.prs.slide_layouts[6]
        slide = self.prs.slides.add_slide(layout)
        
        # Título
        self._add_text_box(slide, Inches(0.5), Inches(0.3), Inches(12), Inches(0.6),
                          "RECOMENDAÇÕES", font_size=28, bold=True, color=self.COLORS['primary'])
        
        # Linha
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(0.9), Inches(12.3), Inches(0.03))
        line.fill.solid()
        line.fill.fore_color.rgb = self.COLORS['primary']
        line.line.fill.background()
        
        recs = []
        if ind.get('liquidez_corrente', 0) < 1:
            recs.append("📌 Priorizar aumento de capital de giro para melhorar liquidez")
        if ind.get('endividamento_geral', 0) > 70:
            recs.append("📌 Avaliar renegociação de dívidas e evitar novos empréstimos")
        if ind.get('margem_liquida', 0) < 5:
            recs.append("📌 Revisar estrutura de custos e política de precificação")
        if ind.get('pmr', 0) > 60:
            recs.append("📌 Implementar política de cobrança mais eficiente")
        if ind.get('carga_tributaria', 0) > 20:
            recs.append("📌 Avaliar planejamento tributário com especialista")
        if not recs:
            recs = ["📌 Manter as boas práticas de gestão financeira", "📌 Continuar monitorando indicadores mensalmente", "📌 Investir em crescimento sustentável"]
        
        y = Inches(1.3)
        for rec in recs:
            card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), y, Inches(12.3), Inches(0.8))
            card.fill.solid()
            card.fill.fore_color.rgb = self.COLORS['gray_100']
            card.line.color.rgb = self.COLORS['gray_300']
            
            self._add_text_box(slide, Inches(0.7), y + Inches(0.2), Inches(12), Inches(0.5),
                              rec, font_size=14, color=self.COLORS['gray_700'])
            y += Inches(1)
    
    def _criar_slide_contato(self):
        """Cria slide de contato/encerramento."""
        layout = self.prs.slide_layouts[6]
        slide = self.prs.slides.add_slide(layout)
        
        # Background
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, self.prs.slide_width, self.prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = self.COLORS['primary']
        bg.line.fill.background()
        
        nome_escritorio = self.config.get('nome_escritorio', 'ContaGestor')
        
        self._add_text_box(slide, Inches(0.5), Inches(2.5), Inches(12), Inches(1),
                          nome_escritorio, font_size=36, bold=True, color=self.COLORS['white'], align=PP_ALIGN.CENTER)
        
        self._add_text_box(slide, Inches(0.5), Inches(3.8), Inches(12), Inches(0.6),
                          "Obrigado!", font_size=28, color=self.COLORS['gray_300'], align=PP_ALIGN.CENTER)
        
        telefone = self.config.get('telefone', '')
        email = self.config.get('email', '')
        
        contato = []
        if telefone: contato.append(f"📞 {telefone}")
        if email: contato.append(f"✉️ {email}")
        
        if contato:
            self._add_text_box(slide, Inches(0.5), Inches(5), Inches(12), Inches(1),
                              " | ".join(contato), font_size=14, color=self.COLORS['gray_300'], align=PP_ALIGN.CENTER)


def gerar_pptx(empresa: Dict, dados_mensais: List[Dict], analise: Dict = None, config: Dict = None, alertas: List[Dict] = None) -> bytes:
    return PowerPointGenerator(config).gerar_apresentacao(empresa, dados_mensais, analise, alertas, config)
