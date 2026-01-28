#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Relatório PDF Profissional - Padrão ABNT
Sistema ContaGestor - Diagnóstico Financeiro Empresarial
Versão 3.1 - Correções de formatação e sobreposição
"""

import io
from datetime import datetime
from typing import Dict, List, Optional, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Flowable
)
from reportlab.graphics.shapes import Drawing, String, Line, Circle
from reportlab.graphics.charts.piecharts import Pie


# CONFIGURAÇÕES
MARGEM_SUPERIOR = 2.5 * cm
MARGEM_INFERIOR = 2 * cm
MARGEM_ESQUERDA = 2.5 * cm
MARGEM_DIREITA = 2 * cm


class Cores:
    """Paleta de cores."""
    AZUL_ESCURO = colors.HexColor('#1E3A5F')
    AZUL_MEDIO = colors.HexColor('#2563EB')
    AZUL_BG = colors.HexColor('#EFF6FF')
    VERDE = colors.HexColor('#059669')
    VERDE_CLARO = colors.HexColor('#D1FAE5')
    AMARELO = colors.HexColor('#D97706')
    AMARELO_CLARO = colors.HexColor('#FEF3C7')
    VERMELHO = colors.HexColor('#DC2626')
    VERMELHO_CLARO = colors.HexColor('#FEE2E2')
    CINZA_700 = colors.HexColor('#374151')
    CINZA_600 = colors.HexColor('#4B5563')
    CINZA_500 = colors.HexColor('#6B7280')
    CINZA_300 = colors.HexColor('#D1D5DB')
    CINZA_200 = colors.HexColor('#E5E7EB')
    CINZA_100 = colors.HexColor('#F3F4F6')
    CINZA_50 = colors.HexColor('#F9FAFB')
    BRANCO = colors.white
    PRETO = colors.HexColor('#111827')


class GaugeChart(Flowable):
    """Gráfico de velocímetro para score."""
    
    def __init__(self, valor, maximo=100, largura=220, altura=140):
        Flowable.__init__(self)
        self.valor = min(max(valor or 0, 0), maximo)
        self.maximo = maximo
        self.largura = largura
        self.altura = altura
    
    def draw(self):
        cx = self.largura / 2
        
        # Layout de baixo para cima (Y=0 é a base):
        # - Status na base (Y ~ 5)
        # - Gauge no meio (cy ~ 55)
        # - Título no topo (Y ~ altura - 12)
        
        # Determinar cor e status
        if self.valor >= 70:
            cor, status = Cores.VERDE, "SAUDÁVEL"
        elif self.valor >= 40:
            cor, status = Cores.AMARELO, "ATENÇÃO"
        else:
            cor, status = Cores.VERMELHO, "CRÍTICO"
        
        # 1. TÍTULO NO TOPO
        self.canv.setFillColor(Cores.CINZA_600)
        self.canv.setFont('Helvetica-Bold', 9)
        self.canv.drawCentredString(cx, self.altura - 12, "SCORE DE SAÚDE FINANCEIRA")
        
        # 2. GAUGE NO MEIO
        cy = 55  # Centro do arco
        raio = 40
        
        # Arco de fundo (semicírculo completo)
        self.canv.setStrokeColor(Cores.CINZA_200)
        self.canv.setLineWidth(10)
        self.canv.arc(cx - raio, cy - raio, cx + raio, cy + raio, 0, 180)
        
        # Arco preenchido (colorido) - só desenha se ângulo > 0
        angulo = 180 * (self.valor / self.maximo) if self.maximo > 0 else 0
        if angulo > 0.5:  # Evita divisão por zero no bezierArc
            self.canv.setStrokeColor(cor)
            self.canv.arc(cx - raio, cy - raio, cx + raio, cy + raio, 180 - angulo, angulo)
        
        # 3. VALOR NUMÉRICO (dentro do arco)
        self.canv.setFillColor(Cores.PRETO)
        self.canv.setFont('Helvetica-Bold', 28)
        self.canv.drawCentredString(cx, cy - 8, str(int(self.valor)))
        
        # 4. STATUS ABAIXO DO GAUGE
        self.canv.setFillColor(cor)
        self.canv.setFont('Helvetica-Bold', 10)
        self.canv.drawCentredString(cx, 5, status)
    
    def wrap(self, availWidth, availHeight):
        return (self.largura, self.altura)


def criar_grafico_linha(dados, largura=400, altura=160):
    """Cria gráfico de linha."""
    drawing = Drawing(largura, altura)
    if not dados or len(dados) < 2:
        return drawing
    
    valores = [d[1] for d in dados]
    labels = [d[0] for d in dados]
    n = len(valores)
    
    x_start, x_end = 55, largura - 20
    y_start, y_end = 25, altura - 25
    graph_width = x_end - x_start
    graph_height = y_end - y_start
    
    v_min = min(valores) * 0.9 if min(valores) > 0 else min(valores) * 1.1
    v_max = max(valores) * 1.1 if max(valores) > 0 else 1
    v_range = v_max - v_min if v_max != v_min else 1
    
    # Grid
    for i in range(5):
        y = y_start + (graph_height * i / 4)
        drawing.add(Line(x_start, y, x_end, y, strokeColor=Cores.CINZA_200, strokeWidth=0.5))
        val = v_min + (v_range * i / 4)
        drawing.add(String(x_start - 5, y - 3, f"{val/1000:.0f}k",
                          fontName='Helvetica', fontSize=7,
                          fillColor=Cores.CINZA_500, textAnchor='end'))
    
    # Pontos e linhas
    pontos = []
    for i, v in enumerate(valores):
        x = x_start + (graph_width * i / max(n - 1, 1))
        y = y_start + (graph_height * (v - v_min) / v_range) if v_range else y_start
        pontos.append((x, y))
    
    for i in range(len(pontos) - 1):
        drawing.add(Line(pontos[i][0], pontos[i][1],
                        pontos[i+1][0], pontos[i+1][1],
                        strokeColor=Cores.AZUL_MEDIO, strokeWidth=2))
    
    for x, y in pontos:
        drawing.add(Circle(x, y, 3, fillColor=Cores.AZUL_MEDIO,
                          strokeColor=Cores.BRANCO, strokeWidth=1.5))
    
    # Labels X (apenas alguns)
    step = max(1, n // 6)
    for i in range(0, n, step):
        x = x_start + (graph_width * i / max(n - 1, 1))
        drawing.add(String(x, y_start - 12, str(labels[i])[-5:],
                          fontName='Helvetica', fontSize=6,
                          fillColor=Cores.CINZA_500, textAnchor='middle'))
    
    return drawing


def criar_grafico_pizza(dados, largura=220, altura=160):
    """Cria gráfico de pizza."""
    drawing = Drawing(largura, altura)
    dados = [(l, abs(v)) for l, v in dados if v and abs(v) > 0]
    if not dados:
        return drawing
    
    pie = Pie()
    pie.x, pie.y = largura / 2 - 50, 20
    pie.width = pie.height = 100
    pie.data = [d[1] for d in dados]
    pie.labels = [d[0] for d in dados]
    
    cores_lista = [Cores.AZUL_MEDIO, Cores.VERDE, Cores.AMARELO,
                   Cores.VERMELHO, colors.HexColor('#7C3AED'), colors.HexColor('#0891B2')]
    for i in range(len(dados)):
        pie.slices[i].fillColor = cores_lista[i % len(cores_lista)]
        pie.slices[i].strokeColor = Cores.BRANCO
        pie.slices[i].strokeWidth = 1
    pie.slices.fontName = 'Helvetica'
    pie.slices.fontSize = 7
    
    drawing.add(pie)
    return drawing


class PDFGeneratorPro:
    """Gerador de relatório financeiro profissional."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.styles = getSampleStyleSheet()
        self.width, self.height = A4
        self.content_width = self.width - MARGEM_ESQUERDA - MARGEM_DIREITA
        self._setup_styles()
    
    def _setup_styles(self):
        """Configura estilos com leading adequado."""
        # Título da capa
        self.styles.add(ParagraphStyle(
            'TituloCapa', fontSize=22, textColor=Cores.AZUL_ESCURO,
            alignment=TA_CENTER, fontName='Helvetica-Bold',
            leading=28, spaceAfter=10
        ))
        
        # Subtítulo
        self.styles.add(ParagraphStyle(
            'SubtituloCapa', fontSize=12, textColor=Cores.CINZA_600,
            alignment=TA_CENTER, leading=16, spaceAfter=15
        ))
        
        # Nome da empresa (capa)
        self.styles.add(ParagraphStyle(
            'NomeEmpresa', fontSize=16, textColor=Cores.CINZA_700,
            alignment=TA_CENTER, fontName='Helvetica-Bold',
            leading=22, spaceAfter=8
        ))
        
        # Título de seção
        self.styles.add(ParagraphStyle(
            'TituloSecao', fontSize=13, textColor=Cores.AZUL_ESCURO,
            fontName='Helvetica-Bold', leading=18,
            spaceBefore=15, spaceAfter=10
        ))
        
        # Subtítulo de seção
        self.styles.add(ParagraphStyle(
            'SubtituloSecao', fontSize=11, textColor=Cores.CINZA_700,
            fontName='Helvetica-Bold', leading=15,
            spaceBefore=12, spaceAfter=8
        ))
        
        # Corpo do texto
        self.styles.add(ParagraphStyle(
            'Corpo', fontSize=10, textColor=Cores.CINZA_700,
            alignment=TA_JUSTIFY, leading=14, spaceAfter=8
        ))
        
        # Texto pequeno
        self.styles.add(ParagraphStyle(
            'TextoPequeno', fontSize=8, textColor=Cores.CINZA_500,
            leading=11, spaceAfter=4
        ))
        
        # Célula de tabela
        self.styles.add(ParagraphStyle(
            'CelulaTabela', fontSize=9, textColor=Cores.CINZA_700,
            leading=12, alignment=TA_LEFT
        ))
        
        # Célula de tabela centralizada
        self.styles.add(ParagraphStyle(
            'CelulaTabelaCenter', fontSize=9, textColor=Cores.CINZA_700,
            leading=12, alignment=TA_CENTER
        ))
        
        # Célula de tabela header
        self.styles.add(ParagraphStyle(
            'CelulaHeader', fontSize=9, textColor=Cores.BRANCO,
            fontName='Helvetica-Bold', leading=12, alignment=TA_CENTER
        ))
        
        # Alerta crítico
        self.styles.add(ParagraphStyle(
            'AlertaTitulo', fontSize=10, textColor=Cores.VERMELHO,
            fontName='Helvetica-Bold', leading=14
        ))
        
        self.styles.add(ParagraphStyle(
            'AlertaTexto', fontSize=9, textColor=Cores.CINZA_700,
            leading=12
        ))
        
        # Rodapé
        self.styles.add(ParagraphStyle(
            'Rodape', fontSize=8, textColor=Cores.CINZA_500,
            alignment=TA_CENTER, leading=11
        ))
    
    def _p(self, texto, estilo='CelulaTabela'):
        """Cria Paragraph para célula de tabela."""
        return Paragraph(str(texto) if texto else "—", self.styles[estilo])
    
    def _fmt_moeda(self, valor):
        """Formata valor monetário."""
        if valor is None:
            return "—"
        try:
            v = float(valor)
            return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            return "—"
    
    def _fmt_pct(self, valor, sinal=False):
        """Formata percentual."""
        if valor is None:
            return "—"
        try:
            v = float(valor)
            return f"+{v:.1f}%" if sinal and v > 0 else f"{v:.1f}%"
        except:
            return "—"
    
    def _fmt_indice(self, valor):
        """Formata índice."""
        if valor is None:
            return "—"
        try:
            return f"{float(valor):.2f}"
        except:
            return "—"
    
    def _calcular_indicadores(self, dados_mensais):
        """Calcula indicadores financeiros."""
        if not dados_mensais:
            return self._indicadores_vazios()
        
        dados = sorted(dados_mensais, key=lambda x: (x.get('ano', 0), x.get('mes', 0)))
        n = len(dados)
        ultimo = dados[-1] if dados else {}
        
        # DRE
        receita_total = sum(d.get('receita', 0) or d.get('receita_bruta', 0) or 0 for d in dados)
        custos_total = sum(d.get('custos', 0) or d.get('custos_total', 0) or 0 for d in dados)
        despesas_total = sum(d.get('despesas', 0) or d.get('despesas_operacionais', 0) or 0 for d in dados)
        folha_total = sum(d.get('folha', 0) or d.get('despesas_pessoal', 0) or 0 for d in dados)
        impostos_total = sum(d.get('impostos', 0) or d.get('deducoes_receita', 0) or 0 for d in dados)
        
        lucro_bruto = receita_total - custos_total
        lucro_operacional = lucro_bruto - despesas_total - folha_total
        lucro_liquido = lucro_operacional - impostos_total
        receita_media = receita_total / n if n > 0 else 0
        
        # Balanço
        ac = ultimo.get('ativo_circulante') or 0
        disponivel = (ultimo.get('disponibilidades') or ultimo.get('disponivel') or 
                      ultimo.get('caixa', 0) + ultimo.get('bancos', 0))
        clientes = ultimo.get('clientes') or 0
        estoques = ultimo.get('estoques') or 0
        anc = ultimo.get('ativo_nao_circulante') or ultimo.get('imobilizado') or 0
        at = ultimo.get('ativo_total') or (ac + anc) or 0
        
        if ac == 0 and (disponivel > 0 or clientes > 0 or estoques > 0):
            ac = disponivel + clientes + estoques
        
        pc = ultimo.get('passivo_circulante') or 0
        fornecedores = ultimo.get('fornecedores') or 0
        pnc = ultimo.get('passivo_nao_circulante') or 0
        pt = pc + pnc
        pl = ultimo.get('patrimonio_liquido') or (at - pt) or 0
        
        # Liquidez
        liq_corrente = ac / pc if pc > 0 else 0
        liq_seca = (ac - estoques) / pc if pc > 0 else 0
        liq_imediata = disponivel / pc if pc > 0 else 0
        liq_geral = (ac + anc) / (pc + pnc) if (pc + pnc) > 0 else 0
        capital_giro = ac - pc
        ncg = (clientes + estoques) - fornecedores
        
        # Endividamento e rentabilidade
        endiv_geral = (pt / at * 100) if at > 0 else 0
        margem_bruta = (lucro_bruto / receita_total * 100) if receita_total > 0 else 0
        margem_operacional = (lucro_operacional / receita_total * 100) if receita_total > 0 else 0
        margem_liquida = (lucro_liquido / receita_total * 100) if receita_total > 0 else 0
        roe = (lucro_liquido / pl * 100) if pl > 0 else 0
        roa = (lucro_liquido / at * 100) if at > 0 else 0
        giro_ativo = receita_total / at if at > 0 else 0
        
        # Tendência
        receitas = [d.get('receita', 0) or d.get('receita_bruta', 0) or 0 for d in dados]
        variacao_receita = ((receitas[-1] / receitas[0]) - 1) * 100 if len(receitas) >= 2 and receitas[0] > 0 else 0
        
        # Score
        score = self._calcular_score(liq_corrente, endiv_geral, margem_liquida, variacao_receita)
        
        # Dados gráfico
        dados_grafico = []
        for d in dados[-12:]:
            receita = d.get('receita', 0) or d.get('receita_bruta', 0) or 0
            dados_grafico.append({
                'periodo': f"{d.get('mes', 0):02d}/{d.get('ano', 0)}",
                'receita': receita
            })
        
        return {
            'meses_analisados': n,
            'periodo_inicio': f"{dados[0].get('mes', 0):02d}/{dados[0].get('ano', 0)}" if dados else "",
            'periodo_fim': f"{ultimo.get('mes', 0):02d}/{ultimo.get('ano', 0)}" if ultimo else "",
            'receita_total': receita_total, 'receita_media': receita_media,
            'custos_total': custos_total, 'despesas_total': despesas_total,
            'folha_total': folha_total, 'impostos_total': impostos_total,
            'lucro_bruto': lucro_bruto, 'lucro_operacional': lucro_operacional,
            'lucro_liquido': lucro_liquido,
            'ativo_total': at, 'ativo_circulante': ac, 'disponibilidades': disponivel,
            'clientes': clientes, 'estoques': estoques, 'ativo_nao_circulante': anc,
            'passivo_total': pt, 'passivo_circulante': pc, 'fornecedores': fornecedores,
            'passivo_nao_circulante': pnc, 'patrimonio_liquido': pl,
            'liquidez_corrente': liq_corrente, 'liquidez_seca': liq_seca,
            'liquidez_imediata': liq_imediata, 'liquidez_geral': liq_geral,
            'ncg': ncg, 'capital_giro': capital_giro,
            'endividamento_geral': endiv_geral,
            'margem_bruta': margem_bruta, 'margem_operacional': margem_operacional,
            'margem_liquida': margem_liquida,
            'roe': roe, 'roa': roa, 'giro_ativo': giro_ativo,
            'variacao_receita': variacao_receita,
            'score': score,
            'dados_grafico': dados_grafico,
        }
    
    def _indicadores_vazios(self):
        """Retorna indicadores zerados."""
        return {k: 0 for k in [
            'meses_analisados', 'receita_total', 'receita_media', 'custos_total',
            'despesas_total', 'folha_total', 'impostos_total', 'lucro_bruto',
            'lucro_operacional', 'lucro_liquido', 'ativo_total', 'ativo_circulante',
            'disponibilidades', 'clientes', 'estoques', 'ativo_nao_circulante',
            'passivo_total', 'passivo_circulante', 'fornecedores', 'passivo_nao_circulante',
            'patrimonio_liquido', 'liquidez_corrente', 'liquidez_seca', 'liquidez_imediata',
            'liquidez_geral', 'ncg', 'capital_giro', 'endividamento_geral',
            'margem_bruta', 'margem_operacional', 'margem_liquida', 'roe', 'roa',
            'giro_ativo', 'variacao_receita', 'score'
        ]}
    
    def _calcular_score(self, liq, endiv, margem, var):
        """Calcula score de saúde."""
        score = 0
        if liq >= 2: score += 25
        elif liq >= 1.5: score += 20
        elif liq >= 1: score += 15
        elif liq >= 0.8: score += 8
        
        if endiv <= 30: score += 25
        elif endiv <= 50: score += 20
        elif endiv <= 70: score += 12
        elif endiv <= 90: score += 5
        
        if margem >= 15: score += 25
        elif margem >= 10: score += 20
        elif margem >= 5: score += 15
        elif margem >= 0: score += 8
        
        if var >= 10: score += 25
        elif var >= 5: score += 20
        elif var >= 0: score += 15
        elif var >= -10: score += 8
        
        return score
    
    def _gerar_insights(self, ind):
        """Gera insights automáticos."""
        insights = []
        
        if ind.get('liquidez_corrente', 0) < 1:
            insights.append({
                'tipo': 'critico', 'titulo': 'Risco de Insolvência',
                'texto': f"Liquidez corrente de {ind['liquidez_corrente']:.2f} indica dificuldade para pagar dívidas de curto prazo."
            })
        
        if ind.get('patrimonio_liquido', 0) < 0:
            insights.append({
                'tipo': 'critico', 'titulo': 'Passivo a Descoberto',
                'texto': f"Patrimônio Líquido negativo de {self._fmt_moeda(ind['patrimonio_liquido'])}."
            })
        
        if ind.get('endividamento_geral', 0) > 80:
            insights.append({
                'tipo': 'critico', 'titulo': 'Endividamento Crítico',
                'texto': f"Endividamento de {ind['endividamento_geral']:.1f}% está muito elevado."
            })
        
        if ind.get('margem_liquida', 0) < 0:
            insights.append({
                'tipo': 'critico', 'titulo': 'Operação com Prejuízo',
                'texto': f"Margem líquida de {ind['margem_liquida']:.1f}% indica prejuízo."
            })
        elif ind.get('margem_liquida', 0) >= 15:
            insights.append({
                'tipo': 'positivo', 'titulo': 'Boa Rentabilidade',
                'texto': f"Margem líquida de {ind['margem_liquida']:.1f}% está acima da média."
            })
        
        if ind.get('capital_giro', 0) < 0:
            insights.append({
                'tipo': 'critico', 'titulo': 'Capital de Giro Negativo',
                'texto': f"Faltam {self._fmt_moeda(abs(ind['capital_giro']))} para operações de curto prazo."
            })
        
        if ind.get('variacao_receita', 0) > 10:
            insights.append({
                'tipo': 'positivo', 'titulo': 'Crescimento de Receita',
                'texto': f"Receita cresceu {ind['variacao_receita']:.1f}% no período."
            })
        
        return insights
    
    def generate(self, result):
        """Método principal - compatível com versão anterior."""
        empresa = {
            'razao_social': result.get('empresa', 'Empresa'),
            'cnpj': result.get('cnpj', '')
        }
        dados_mensais = result.get('dados_mensais', [])
        
        # Usar score da análise se disponível
        score_analise = result.get('score')
        
        if not dados_mensais and result:
            # Usar dados do result diretamente
            ind = {
                'meses_analisados': result.get('meses_analisados', 0),
                'periodo_inicio': result.get('periodo_inicio', ''),
                'periodo_fim': result.get('periodo_fim', ''),
                'receita_total': result.get('faturamento_total', 0),
                'receita_media': result.get('faturamento_medio', 0),
                'lucro_liquido': result.get('lucro_total', 0),
                'margem_liquida': result.get('margem_media', 0),
                'score': score_analise if score_analise is not None else 50,
                'liquidez_corrente': 1.0,
                'endividamento_geral': 50,
                'variacao_receita': 0,
                'dados_grafico': [],
            }
            ind.update(self._indicadores_vazios())
        else:
            ind = self._calcular_indicadores(dados_mensais)
            # Sobrescrever score calculado com o da análise se disponível
            if score_analise is not None:
                ind['score'] = score_analise
        
        insights = self._gerar_insights(ind)
        return self._gerar_pdf(empresa, ind, insights)
    
    def gerar_relatorio(self, empresa, dados_mensais, analise=None, alertas=None, config=None):
        """Gera relatório completo."""
        ind = self._calcular_indicadores(dados_mensais)
        
        # Usar score da análise se disponível
        if analise and analise.get('score') is not None:
            ind['score'] = analise.get('score')
        
        insights = self._gerar_insights(ind)
        return self._gerar_pdf(empresa, ind, insights)
    
    def _gerar_pdf(self, empresa, ind, insights):
        """Gera o PDF."""
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=MARGEM_DIREITA, leftMargin=MARGEM_ESQUERDA,
            topMargin=MARGEM_SUPERIOR, bottomMargin=MARGEM_INFERIOR
        )
        
        story = []
        
        # 1. CAPA
        story.extend(self._criar_capa(empresa, ind))
        story.append(PageBreak())
        
        # 2. RESUMO EXECUTIVO
        story.extend(self._criar_resumo(empresa, ind, insights))
        story.append(PageBreak())
        
        # 3. ANÁLISE FINANCEIRA
        story.extend(self._criar_analise(ind))
        story.append(PageBreak())
        
        # 4. ÍNDICES DE LIQUIDEZ
        story.extend(self._criar_liquidez(ind))
        story.append(PageBreak())
        
        # 5. RENTABILIDADE E CONCLUSÕES
        story.extend(self._criar_rentabilidade(ind))
        story.extend(self._criar_conclusoes(ind, insights))
        
        doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        buffer.seek(0)
        return buffer.read()
    
    def _header_footer(self, canvas, doc):
        """Cabeçalho e rodapé."""
        canvas.saveState()
        
        # Linha superior
        canvas.setStrokeColor(Cores.AZUL_ESCURO)
        canvas.setLineWidth(0.5)
        canvas.line(MARGEM_ESQUERDA, self.height - MARGEM_SUPERIOR + 0.3*cm,
                   self.width - MARGEM_DIREITA, self.height - MARGEM_SUPERIOR + 0.3*cm)
        
        # Rodapé
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(Cores.CINZA_500)
        canvas.drawString(MARGEM_ESQUERDA, MARGEM_INFERIOR - 0.4*cm,
                         f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        canvas.drawRightString(self.width - MARGEM_DIREITA, MARGEM_INFERIOR - 0.4*cm,
                              f"Página {doc.page}")
        
        canvas.line(MARGEM_ESQUERDA, MARGEM_INFERIOR - 0.1*cm,
                   self.width - MARGEM_DIREITA, MARGEM_INFERIOR - 0.1*cm)
        
        canvas.restoreState()
    
    def _criar_capa(self, empresa, ind):
        """Cria capa do relatório."""
        elements = [Spacer(1, 1.5*cm)]
        
        elements.append(Paragraph("RELATÓRIO DE", self.styles['SubtituloCapa']))
        elements.append(Paragraph("DIAGNÓSTICO FINANCEIRO", self.styles['TituloCapa']))
        
        # Linha separadora
        sep = Table([['']], colWidths=[5*cm], rowHeights=[3])
        sep.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), Cores.AZUL_ESCURO),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ]))
        elements.append(sep)
        elements.append(Spacer(1, 1.2*cm))
        
        # Nome da empresa
        nome = empresa.get('razao_social', empresa.get('nome', 'Empresa'))
        elements.append(Paragraph(nome, self.styles['NomeEmpresa']))
        
        cnpj = empresa.get('cnpj', '')
        if cnpj:
            elements.append(Paragraph(f"CNPJ: {cnpj}", self.styles['SubtituloCapa']))
        
        elements.append(Spacer(1, 0.8*cm))
        elements.append(Paragraph(
            f"Período: {ind.get('periodo_inicio', '')} a {ind.get('periodo_fim', '')}",
            self.styles['SubtituloCapa']
        ))
        elements.append(Spacer(1, 1.5*cm))
        
        # Gauge
        gauge = GaugeChart(ind.get('score', 0), maximo=100, largura=220, altura=130)
        gauge_table = Table([[gauge]], colWidths=[self.content_width])
        gauge_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'CENTER')]))
        elements.append(gauge_table)
        elements.append(Spacer(1, 1*cm))
        
        # Indicadores principais - usando Paragraph nas células
        box_data = [
            [self._p('INDICADOR', 'CelulaHeader'),
             self._p('VALOR', 'CelulaHeader'),
             self._p('STATUS', 'CelulaHeader')],
            [self._p('Liquidez Corrente'),
             self._p(self._fmt_indice(ind.get('liquidez_corrente')), 'CelulaTabelaCenter'),
             self._p(self._status_liq(ind.get('liquidez_corrente', 0)), 'CelulaTabelaCenter')],
            [self._p('Margem Líquida'),
             self._p(self._fmt_pct(ind.get('margem_liquida')), 'CelulaTabelaCenter'),
             self._p(self._status_marg(ind.get('margem_liquida', 0)), 'CelulaTabelaCenter')],
            [self._p('Endividamento'),
             self._p(self._fmt_pct(ind.get('endividamento_geral')), 'CelulaTabelaCenter'),
             self._p(self._status_end(ind.get('endividamento_geral', 0)), 'CelulaTabelaCenter')],
            [self._p('Variação Receita'),
             self._p(self._fmt_pct(ind.get('variacao_receita'), sinal=True), 'CelulaTabelaCenter'),
             self._p(self._status_tend(ind.get('variacao_receita', 0)), 'CelulaTabelaCenter')],
        ]
        
        box_table = Table(box_data, colWidths=[6*cm, 4*cm, 4*cm], rowHeights=[25, 22, 22, 22, 22])
        box_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), Cores.AZUL_ESCURO),
            ('BACKGROUND', (0, 1), (-1, -1), Cores.CINZA_50),
            ('GRID', (0, 0), (-1, -1), 0.5, Cores.CINZA_300),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(box_table)
        
        return elements
    
    def _status_liq(self, v):
        return "Excelente" if v >= 2 else "Bom" if v >= 1.5 else "Adequado" if v >= 1 else "Crítico"
    
    def _status_marg(self, v):
        return "Excelente" if v >= 15 else "Bom" if v >= 10 else "Adequado" if v >= 5 else "Prejuízo" if v < 0 else "Baixo"
    
    def _status_end(self, v):
        return "Baixo" if v <= 30 else "Moderado" if v <= 50 else "Elevado" if v <= 70 else "Crítico"
    
    def _status_tend(self, v):
        return "Crescimento" if v > 5 else "Estável" if v >= -5 else "Queda"
    
    def _criar_resumo(self, empresa, ind, insights):
        """Cria resumo executivo."""
        elements = []
        
        elements.append(Paragraph("1. RESUMO EXECUTIVO", self.styles['TituloSecao']))
        
        # Linha separadora
        sep = Table([['']], colWidths=[self.content_width], rowHeights=[2])
        sep.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), Cores.AZUL_ESCURO)]))
        elements.append(sep)
        elements.append(Spacer(1, 0.4*cm))
        
        nome = empresa.get('razao_social', 'A empresa')
        intro = f"""Este relatório apresenta o diagnóstico financeiro de <b>{nome}</b>, 
        baseado na análise de <b>{ind.get('meses_analisados', 0)} meses</b> de dados contábeis, 
        compreendendo o período de <b>{ind.get('periodo_inicio', '')}</b> a <b>{ind.get('periodo_fim', '')}</b>."""
        elements.append(Paragraph(intro, self.styles['Corpo']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Alertas críticos
        alertas_criticos = [i for i in insights if i['tipo'] == 'critico']
        if alertas_criticos:
            elements.append(Paragraph("1.1 Alertas Críticos", self.styles['SubtituloSecao']))
            
            for alerta in alertas_criticos:
                # Tabela para alerta com células usando Paragraph
                alert_data = [[
                    self._p(f"⚠️ {alerta['titulo']}", 'AlertaTitulo'),
                    self._p(alerta['texto'], 'AlertaTexto')
                ]]
                alert_table = Table(alert_data, colWidths=[4.5*cm, self.content_width - 4.5*cm], rowHeights=[None])
                alert_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), Cores.VERMELHO_CLARO),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ]))
                elements.append(alert_table)
                elements.append(Spacer(1, 0.3*cm))
        
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph("1.2 Principais Indicadores", self.styles['SubtituloSecao']))
        
        # Tabela de indicadores
        numeros_data = [
            [self._p('Receita Total', 'CelulaTabela'), self._p(self._fmt_moeda(ind.get('receita_total')), 'CelulaTabelaCenter'),
             self._p('Lucro Líquido', 'CelulaTabela'), self._p(self._fmt_moeda(ind.get('lucro_liquido')), 'CelulaTabelaCenter')],
            [self._p('Receita Média/Mês', 'CelulaTabela'), self._p(self._fmt_moeda(ind.get('receita_media')), 'CelulaTabelaCenter'),
             self._p('Margem Líquida', 'CelulaTabela'), self._p(self._fmt_pct(ind.get('margem_liquida')), 'CelulaTabelaCenter')],
            [self._p('Ativo Total', 'CelulaTabela'), self._p(self._fmt_moeda(ind.get('ativo_total')), 'CelulaTabelaCenter'),
             self._p('ROE', 'CelulaTabela'), self._p(self._fmt_pct(ind.get('roe')), 'CelulaTabelaCenter')],
            [self._p('Patrimônio Líquido', 'CelulaTabela'), self._p(self._fmt_moeda(ind.get('patrimonio_liquido')), 'CelulaTabelaCenter'),
             self._p('ROA', 'CelulaTabela'), self._p(self._fmt_pct(ind.get('roa')), 'CelulaTabelaCenter')],
        ]
        
        numeros_table = Table(numeros_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm], rowHeights=[22, 22, 22, 22])
        numeros_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, Cores.CINZA_200),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(numeros_table)
        
        return elements
    
    def _criar_analise(self, ind):
        """Cria análise financeira."""
        elements = []
        
        elements.append(Paragraph("2. ANÁLISE DA SITUAÇÃO FINANCEIRA", self.styles['TituloSecao']))
        
        sep = Table([['']], colWidths=[self.content_width], rowHeights=[2])
        sep.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), Cores.AZUL_ESCURO)]))
        elements.append(sep)
        elements.append(Spacer(1, 0.4*cm))
        
        # DRE
        elements.append(Paragraph("2.1 Demonstração do Resultado", self.styles['SubtituloSecao']))
        
        receita = ind.get('receita_total', 0) or 1
        dre_data = [
            [self._p('CONTA', 'CelulaHeader'), self._p('VALOR', 'CelulaHeader'), self._p('AV%', 'CelulaHeader')],
            [self._p('Receita Total'), self._p(self._fmt_moeda(ind.get('receita_total')), 'CelulaTabelaCenter'), self._p('100,0%', 'CelulaTabelaCenter')],
            [self._p('(-) Custos'), self._p(self._fmt_moeda(-ind.get('custos_total', 0)), 'CelulaTabelaCenter'), 
             self._p(self._fmt_pct(-ind.get('custos_total', 0) / receita * 100), 'CelulaTabelaCenter')],
            [self._p('= Lucro Bruto'), self._p(self._fmt_moeda(ind.get('lucro_bruto')), 'CelulaTabelaCenter'), 
             self._p(self._fmt_pct(ind.get('margem_bruta')), 'CelulaTabelaCenter')],
            [self._p('(-) Despesas Operacionais'), self._p(self._fmt_moeda(-ind.get('despesas_total', 0) - ind.get('folha_total', 0)), 'CelulaTabelaCenter'), self._p('', 'CelulaTabelaCenter')],
            [self._p('= Lucro Operacional'), self._p(self._fmt_moeda(ind.get('lucro_operacional')), 'CelulaTabelaCenter'),
             self._p(self._fmt_pct(ind.get('margem_operacional')), 'CelulaTabelaCenter')],
            [self._p('(-) Impostos'), self._p(self._fmt_moeda(-ind.get('impostos_total', 0)), 'CelulaTabelaCenter'), self._p('', 'CelulaTabelaCenter')],
            [self._p('= LUCRO LÍQUIDO', 'CelulaHeader'), self._p(self._fmt_moeda(ind.get('lucro_liquido')), 'CelulaHeader'),
             self._p(self._fmt_pct(ind.get('margem_liquida')), 'CelulaHeader')],
        ]
        
        dre_table = Table(dre_data, colWidths=[8*cm, 4.5*cm, 3.5*cm], rowHeights=[22] * 8)
        dre_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), Cores.AZUL_ESCURO),
            ('BACKGROUND', (0, -1), (-1, -1), Cores.AZUL_MEDIO),
            ('GRID', (0, 0), (-1, -1), 0.5, Cores.CINZA_300),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(dre_table)
        elements.append(Spacer(1, 0.5*cm))
        
        # Gráfico de evolução
        if ind.get('dados_grafico'):
            elements.append(Paragraph("Evolução da Receita Mensal", self.styles['SubtituloSecao']))
            dados_graf = [(d['periodo'], d['receita']) for d in ind['dados_grafico']]
            grafico = criar_grafico_linha(dados_graf, self.content_width, 140)
            elements.append(grafico)
        
        elements.append(Spacer(1, 0.5*cm))
        
        # Balanço
        elements.append(Paragraph("2.2 Balanço Patrimonial Resumido", self.styles['SubtituloSecao']))
        
        balanco_data = [
            [self._p('ATIVO', 'CelulaHeader'), self._p('VALOR', 'CelulaHeader'), 
             self._p('PASSIVO + PL', 'CelulaHeader'), self._p('VALOR', 'CelulaHeader')],
            [self._p('Ativo Circulante'), self._p(self._fmt_moeda(ind.get('ativo_circulante')), 'CelulaTabelaCenter'),
             self._p('Passivo Circulante'), self._p(self._fmt_moeda(ind.get('passivo_circulante')), 'CelulaTabelaCenter')],
            [self._p('  Disponibilidades'), self._p(self._fmt_moeda(ind.get('disponibilidades')), 'CelulaTabelaCenter'),
             self._p('  Fornecedores'), self._p(self._fmt_moeda(ind.get('fornecedores')), 'CelulaTabelaCenter')],
            [self._p('  Clientes'), self._p(self._fmt_moeda(ind.get('clientes')), 'CelulaTabelaCenter'),
             self._p('Passivo Não Circulante'), self._p(self._fmt_moeda(ind.get('passivo_nao_circulante')), 'CelulaTabelaCenter')],
            [self._p('  Estoques'), self._p(self._fmt_moeda(ind.get('estoques')), 'CelulaTabelaCenter'),
             self._p('PATRIMÔNIO LÍQUIDO'), self._p(self._fmt_moeda(ind.get('patrimonio_liquido')), 'CelulaTabelaCenter')],
            [self._p('Ativo Não Circulante'), self._p(self._fmt_moeda(ind.get('ativo_nao_circulante')), 'CelulaTabelaCenter'), 
             self._p(''), self._p('')],
            [self._p('TOTAL ATIVO', 'CelulaHeader'), self._p(self._fmt_moeda(ind.get('ativo_total')), 'CelulaHeader'),
             self._p('TOTAL PASSIVO+PL', 'CelulaHeader'), self._p(self._fmt_moeda(ind.get('ativo_total')), 'CelulaHeader')],
        ]
        
        balanco_table = Table(balanco_data, colWidths=[4.5*cm, 3.5*cm, 4.5*cm, 3.5*cm], rowHeights=[22] * 7)
        balanco_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), Cores.AZUL_ESCURO),
            ('BACKGROUND', (0, -1), (-1, -1), Cores.AZUL_MEDIO),
            ('GRID', (0, 0), (-1, -1), 0.5, Cores.CINZA_300),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(balanco_table)
        
        return elements
    
    def _criar_liquidez(self, ind):
        """Cria seção de liquidez."""
        elements = []
        
        elements.append(Paragraph("3. ÍNDICES DE LIQUIDEZ", self.styles['TituloSecao']))
        
        sep = Table([['']], colWidths=[self.content_width], rowHeights=[2])
        sep.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), Cores.AZUL_ESCURO)]))
        elements.append(sep)
        elements.append(Spacer(1, 0.4*cm))
        
        intro = """Os índices de liquidez medem a capacidade da empresa de honrar seus 
        compromissos financeiros. Quanto maior o índice, maior a folga financeira."""
        elements.append(Paragraph(intro, self.styles['Corpo']))
        elements.append(Spacer(1, 0.4*cm))
        
        def status_l(v): return "Excelente" if v >= 2 else "Bom" if v >= 1.5 else "Adequado" if v >= 1 else "Crítico"
        def status_s(v): return "Excelente" if v >= 1.2 else "Bom" if v >= 1 else "Adequado" if v >= 0.7 else "Baixo"
        def status_i(v): return "Alto" if v >= 0.5 else "Bom" if v >= 0.2 else "Adequado" if v >= 0.1 else "Baixo"
        
        liq_data = [
            [self._p('ÍNDICE', 'CelulaHeader'), self._p('VALOR', 'CelulaHeader'), 
             self._p('PARÂM.', 'CelulaHeader'), self._p('STATUS', 'CelulaHeader'), self._p('FÓRMULA', 'CelulaHeader')],
            [self._p('Liquidez Corrente'), self._p(self._fmt_indice(ind.get('liquidez_corrente')), 'CelulaTabelaCenter'),
             self._p('≥ 1,50', 'CelulaTabelaCenter'), self._p(status_l(ind.get('liquidez_corrente', 0)), 'CelulaTabelaCenter'), self._p('AC / PC', 'CelulaTabelaCenter')],
            [self._p('Liquidez Seca'), self._p(self._fmt_indice(ind.get('liquidez_seca')), 'CelulaTabelaCenter'),
             self._p('≥ 1,00', 'CelulaTabelaCenter'), self._p(status_s(ind.get('liquidez_seca', 0)), 'CelulaTabelaCenter'), self._p('(AC-Est) / PC', 'CelulaTabelaCenter')],
            [self._p('Liquidez Imediata'), self._p(self._fmt_indice(ind.get('liquidez_imediata')), 'CelulaTabelaCenter'),
             self._p('≥ 0,20', 'CelulaTabelaCenter'), self._p(status_i(ind.get('liquidez_imediata', 0)), 'CelulaTabelaCenter'), self._p('Disp / PC', 'CelulaTabelaCenter')],
            [self._p('Liquidez Geral'), self._p(self._fmt_indice(ind.get('liquidez_geral')), 'CelulaTabelaCenter'),
             self._p('≥ 1,00', 'CelulaTabelaCenter'), self._p(status_l(ind.get('liquidez_geral', 0)), 'CelulaTabelaCenter'), self._p('(AC+RLP)/(PC+PNC)', 'CelulaTabelaCenter')],
        ]
        
        liq_table = Table(liq_data, colWidths=[3.8*cm, 2*cm, 2*cm, 2.2*cm, 3.5*cm], rowHeights=[22] * 5)
        liq_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), Cores.AZUL_ESCURO),
            ('GRID', (0, 0), (-1, -1), 0.5, Cores.CINZA_300),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(liq_table)
        elements.append(Spacer(1, 0.5*cm))
        
        # Indicadores complementares
        elements.append(Paragraph("3.1 Capital de Giro", self.styles['SubtituloSecao']))
        
        comp_data = [
            [self._p('Indicador', 'CelulaHeader'), self._p('Valor', 'CelulaHeader'), self._p('Situação', 'CelulaHeader')],
            [self._p('Necessidade de Capital de Giro'), self._p(self._fmt_moeda(ind.get('ncg')), 'CelulaTabelaCenter'),
             self._p('Normal' if ind.get('ncg', 0) >= 0 else 'Negativa', 'CelulaTabelaCenter')],
            [self._p('Capital de Giro Líquido'), self._p(self._fmt_moeda(ind.get('capital_giro')), 'CelulaTabelaCenter'),
             self._p('Positivo' if ind.get('capital_giro', 0) >= 0 else 'NEGATIVO', 'CelulaTabelaCenter')],
        ]
        
        comp_table = Table(comp_data, colWidths=[6*cm, 4.5*cm, 5*cm], rowHeights=[22, 22, 22])
        comp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), Cores.CINZA_700),
            ('GRID', (0, 0), (-1, -1), 0.5, Cores.CINZA_300),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(comp_table)
        
        return elements
    
    def _criar_rentabilidade(self, ind):
        """Cria seção de rentabilidade."""
        elements = []
        
        elements.append(Paragraph("4. ANÁLISE DE RENTABILIDADE", self.styles['TituloSecao']))
        
        sep = Table([['']], colWidths=[self.content_width], rowHeights=[2])
        sep.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), Cores.AZUL_ESCURO)]))
        elements.append(sep)
        elements.append(Spacer(1, 0.4*cm))
        
        # Margens
        elements.append(Paragraph("4.1 Análise de Margens", self.styles['SubtituloSecao']))
        
        def status_mb(v): return "Excelente" if v >= 50 else "Bom" if v >= 40 else "Adequado" if v >= 30 else "Baixo"
        def status_mo(v): return "Excelente" if v >= 20 else "Bom" if v >= 15 else "Adequado" if v >= 10 else "Baixo"
        def status_ml(v): return "Excelente" if v >= 15 else "Bom" if v >= 10 else "Adequado" if v >= 5 else "Prejuízo" if v < 0 else "Baixo"
        
        margens_data = [
            [self._p('MARGEM', 'CelulaHeader'), self._p('VALOR', 'CelulaHeader'), 
             self._p('PARÂM.', 'CelulaHeader'), self._p('STATUS', 'CelulaHeader')],
            [self._p('Margem Bruta'), self._p(self._fmt_pct(ind.get('margem_bruta')), 'CelulaTabelaCenter'),
             self._p('≥ 30%', 'CelulaTabelaCenter'), self._p(status_mb(ind.get('margem_bruta', 0)), 'CelulaTabelaCenter')],
            [self._p('Margem Operacional'), self._p(self._fmt_pct(ind.get('margem_operacional')), 'CelulaTabelaCenter'),
             self._p('≥ 10%', 'CelulaTabelaCenter'), self._p(status_mo(ind.get('margem_operacional', 0)), 'CelulaTabelaCenter')],
            [self._p('Margem Líquida'), self._p(self._fmt_pct(ind.get('margem_liquida')), 'CelulaTabelaCenter'),
             self._p('≥ 5%', 'CelulaTabelaCenter'), self._p(status_ml(ind.get('margem_liquida', 0)), 'CelulaTabelaCenter')],
        ]
        
        margens_table = Table(margens_data, colWidths=[4.5*cm, 3.5*cm, 3*cm, 3.5*cm], rowHeights=[22] * 4)
        margens_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), Cores.AZUL_ESCURO),
            ('GRID', (0, 0), (-1, -1), 0.5, Cores.CINZA_300),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(margens_table)
        elements.append(Spacer(1, 0.5*cm))
        
        # Retorno
        elements.append(Paragraph("4.2 Retorno sobre Investimento", self.styles['SubtituloSecao']))
        
        retorno_data = [
            [self._p('INDICADOR', 'CelulaHeader'), self._p('VALOR', 'CelulaHeader'), 
             self._p('FÓRMULA', 'CelulaHeader'), self._p('INTERPRETAÇÃO', 'CelulaHeader')],
            [self._p('ROE'), self._p(self._fmt_pct(ind.get('roe')), 'CelulaTabelaCenter'),
             self._p('Lucro / PL', 'CelulaTabelaCenter'), self._p('Retorno capital próprio')],
            [self._p('ROA'), self._p(self._fmt_pct(ind.get('roa')), 'CelulaTabelaCenter'),
             self._p('Lucro / Ativo', 'CelulaTabelaCenter'), self._p('Eficiência dos ativos')],
            [self._p('Giro do Ativo'), self._p(f"{ind.get('giro_ativo', 0):.2f}x", 'CelulaTabelaCenter'),
             self._p('Receita / Ativo', 'CelulaTabelaCenter'), self._p('Uso dos ativos')],
        ]
        
        retorno_table = Table(retorno_data, colWidths=[3.5*cm, 2.5*cm, 3.5*cm, 4.5*cm], rowHeights=[22] * 4)
        retorno_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), Cores.CINZA_700),
            ('GRID', (0, 0), (-1, -1), 0.5, Cores.CINZA_300),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(retorno_table)
        elements.append(Spacer(1, 0.5*cm))
        
        # Gráfico pizza
        if ind.get('receita_total', 0) > 0:
            elements.append(Paragraph("Composição dos Custos", self.styles['SubtituloSecao']))
            dados_pizza = [
                ('Custos', ind.get('custos_total', 0)),
                ('Despesas', ind.get('despesas_total', 0) + ind.get('folha_total', 0)),
                ('Impostos', ind.get('impostos_total', 0)),
                ('Lucro', max(ind.get('lucro_liquido', 0), 0)),
            ]
            grafico_pizza = criar_grafico_pizza(dados_pizza, 250, 150)
            elements.append(grafico_pizza)
        
        return elements
    
    def _criar_conclusoes(self, ind, insights):
        """Cria seção de conclusões."""
        elements = []
        
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph("5. CONCLUSÕES E RECOMENDAÇÕES", self.styles['TituloSecao']))
        
        sep = Table([['']], colWidths=[self.content_width], rowHeights=[2])
        sep.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), Cores.AZUL_ESCURO)]))
        elements.append(sep)
        elements.append(Spacer(1, 0.4*cm))
        
        # Diagnóstico
        score = ind.get('score', 0)
        if score >= 70:
            diag = "A empresa apresenta <b>boa saúde financeira</b>, com indicadores equilibrados."
        elif score >= 40:
            diag = "A empresa requer <b>atenção em alguns pontos</b>, mas apresenta condições de recuperação."
        else:
            diag = "A empresa está em <b>situação crítica</b> e necessita de ações urgentes."
        
        elements.append(Paragraph("5.1 Diagnóstico Geral", self.styles['SubtituloSecao']))
        elements.append(Paragraph(diag, self.styles['Corpo']))
        elements.append(Spacer(1, 0.3*cm))
        
        # Pontos positivos
        positivos = [i for i in insights if i['tipo'] == 'positivo']
        if positivos:
            elements.append(Paragraph("5.2 Pontos Positivos", self.styles['SubtituloSecao']))
            for p in positivos:
                elements.append(Paragraph(f"✅ <b>{p['titulo']}</b>: {p['texto']}", self.styles['Corpo']))
        
        elements.append(Spacer(1, 0.3*cm))
        
        # Recomendações
        elements.append(Paragraph("5.3 Recomendações", self.styles['SubtituloSecao']))
        
        recomendacoes = self._gerar_recomendacoes(ind)
        for i, rec in enumerate(recomendacoes, 1):
            elements.append(Paragraph(f"<b>{i}.</b> {rec}", self.styles['Corpo']))
        
        elements.append(Spacer(1, 0.8*cm))
        
        # Disclaimer
        sep2 = Table([['']], colWidths=[self.content_width], rowHeights=[1])
        sep2.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), Cores.CINZA_300)]))
        elements.append(sep2)
        elements.append(Spacer(1, 0.3*cm))
        
        elements.append(Paragraph(
            "Este documento é de caráter informativo e não substitui a análise de profissional habilitado.",
            self.styles['Rodape']
        ))
        
        return elements
    
    def _gerar_recomendacoes(self, ind):
        """Gera recomendações."""
        recs = []
        
        if ind.get('liquidez_corrente', 0) < 1:
            recs.append("Buscar aumento de capital de giro através de renegociação de dívidas ou aporte de capital.")
        
        if ind.get('patrimonio_liquido', 0) < 0:
            recs.append("Avaliar aporte de capital dos sócios para recompor o patrimônio líquido.")
        
        if ind.get('endividamento_geral', 0) > 70:
            recs.append("Priorizar redução do endividamento, evitando novos empréstimos.")
        
        if ind.get('margem_liquida', 0) < 5:
            recs.append("Revisar estrutura de custos e política de precificação.")
        
        if ind.get('variacao_receita', 0) < -5:
            recs.append("Investigar causas da queda de receita e desenvolver estratégias de recuperação.")
        
        if not recs:
            recs = [
                "Manter as boas práticas de gestão financeira atuais.",
                "Continuar monitorando indicadores mensalmente.",
                "Avaliar oportunidades de crescimento sustentável.",
            ]
        
        return recs


def gerar_pdf(empresa, dados_mensais, analise=None, config=None, alertas=None):
    """Função principal para gerar PDF."""
    generator = PDFGeneratorPro(config)
    return generator.gerar_relatorio(empresa, dados_mensais, analise, alertas, config)
