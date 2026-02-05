#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Relatório PDF Profissional - Versão 5.0
Sistema Kontabil - Diagnóstico Financeiro Empresarial
"""

import io
from datetime import datetime
from typing import Dict, List, Optional, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.widgets.markers import makeMarker

MARGEM_SUPERIOR = 2.5 * cm
MARGEM_INFERIOR = 2 * cm
MARGEM_ESQUERDA = 2.5 * cm
MARGEM_DIREITA = 2 * cm

class Cores:
    AZUL_ESCURO = colors.HexColor('#1E3A5F')
    AZUL_MEDIO = colors.HexColor('#2563EB')
    AZUL_BG = colors.HexColor('#EFF6FF')
    VERDE = colors.HexColor('#059669')
    VERDE_ESCURO = colors.HexColor('#047857')
    AMARELO = colors.HexColor('#D97706')
    VERMELHO = colors.HexColor('#DC2626')
    VERMELHO_ESCURO = colors.HexColor('#B91C1C')
    CINZA_700 = colors.HexColor('#374151')
    CINZA_600 = colors.HexColor('#4B5563')
    CINZA_500 = colors.HexColor('#6B7280')
    CINZA_300 = colors.HexColor('#D1D5DB')
    CINZA_200 = colors.HexColor('#E5E7EB')
    CINZA_100 = colors.HexColor('#F3F4F6')
    CINZA_50 = colors.HexColor('#F9FAFB')
    BRANCO = colors.white
    PRETO = colors.HexColor('#111827')
    CHART_1 = colors.HexColor('#3B82F6')
    CHART_2 = colors.HexColor('#10B981')
    CHART_3 = colors.HexColor('#F59E0B')
    CHART_4 = colors.HexColor('#EF4444')
    CHART_5 = colors.HexColor('#8B5CF6')

class GaugeChart(Flowable):
    def __init__(self, valor, maximo=100, largura=220, altura=140):
        Flowable.__init__(self)
        self.valor = min(max(valor or 0, 0), maximo)
        self.maximo = maximo
        self.largura = largura
        self.altura = altura
    
    def draw(self):
        cx = self.largura / 2
        if self.valor >= 70: cor, status = Cores.VERDE, "SAUDÁVEL"
        elif self.valor >= 40: cor, status = Cores.AMARELO, "ATENÇÃO"
        else: cor, status = Cores.VERMELHO, "CRÍTICO"
        self.canv.setFillColor(Cores.CINZA_600)
        self.canv.setFont('Helvetica-Bold', 9)
        self.canv.drawCentredString(cx, self.altura - 12, "SCORE DE SAÚDE FINANCEIRA")
        cy, raio = 55, 40
        self.canv.setStrokeColor(Cores.CINZA_200)
        self.canv.setLineWidth(12)
        self.canv.arc(cx - raio, cy - raio, cx + raio, cy + raio, 0, 180)
        angulo = 180 * (self.valor / self.maximo) if self.maximo > 0 else 0
        if angulo > 0.5:
            self.canv.setStrokeColor(cor)
            self.canv.arc(cx - raio, cy - raio, cx + raio, cy + raio, 180 - angulo, angulo)
        self.canv.setFillColor(Cores.PRETO)
        self.canv.setFont('Helvetica-Bold', 32)
        self.canv.drawCentredString(cx, cy - 10, str(int(self.valor)))
        self.canv.setFillColor(Cores.CINZA_500)
        self.canv.setFont('Helvetica', 7)
        self.canv.drawString(cx - raio - 5, cy - raio - 8, "0")
        self.canv.drawRightString(cx + raio + 5, cy - raio - 8, "100")
        self.canv.setFillColor(cor)
        self.canv.setFont('Helvetica-Bold', 11)
        self.canv.drawCentredString(cx, 5, status)
    
    def wrap(self, availWidth, availHeight):
        return (self.largura, self.altura)

def criar_grafico_linha(dados, largura=400, altura=150, cor=None):
    drawing = Drawing(largura, altura)
    if not dados or len(dados) < 2: return drawing
    valores, labels = [d[1] for d in dados], [d[0] for d in dados]
    chart = HorizontalLineChart()
    chart.x, chart.y, chart.width, chart.height = 50, 30, largura - 80, altura - 50
    chart.data = [valores]
    cor_linha = cor or Cores.AZUL_MEDIO
    chart.lines[0].strokeColor = cor_linha
    chart.lines[0].strokeWidth = 2
    chart.lines[0].symbol = makeMarker('Circle')
    chart.lines[0].symbol.size = 4
    chart.lines[0].symbol.fillColor = cor_linha
    chart.categoryAxis.categoryNames = labels
    chart.categoryAxis.labels.fontName = 'Helvetica'
    chart.categoryAxis.labels.fontSize = 7
    chart.categoryAxis.labels.angle = 45
    chart.categoryAxis.labels.boxAnchor = 'ne'
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max(valores) * 1.1 if valores else 100
    chart.valueAxis.labels.fontName = 'Helvetica'
    chart.valueAxis.labels.fontSize = 7
    chart.valueAxis.visibleGrid = True
    chart.valueAxis.gridStrokeColor = Cores.CINZA_200
    drawing.add(chart)
    return drawing

def criar_grafico_barras(dados, largura=400, altura=150):
    drawing = Drawing(largura, altura)
    if not dados: return drawing
    valores, labels = [d[1] for d in dados], [d[0] for d in dados]
    chart = VerticalBarChart()
    chart.x, chart.y, chart.width, chart.height = 50, 30, largura - 80, altura - 50
    chart.data = [valores]
    chart.bars[0].fillColor = Cores.AZUL_MEDIO
    chart.categoryAxis.categoryNames = labels
    chart.categoryAxis.labels.fontName = 'Helvetica'
    chart.categoryAxis.labels.fontSize = 7
    chart.categoryAxis.labels.angle = 45
    chart.categoryAxis.labels.boxAnchor = 'ne'
    chart.valueAxis.valueMin = min(0, min(valores) * 1.1) if valores else 0
    chart.valueAxis.valueMax = max(valores) * 1.1 if valores else 100
    chart.valueAxis.labels.fontName = 'Helvetica'
    chart.valueAxis.labels.fontSize = 7
    drawing.add(chart)
    return drawing

def criar_grafico_pizza(dados, largura=280, altura=160):
    drawing = Drawing(largura, altura)
    dados_validos = [(l, v) for l, v in dados if v and v > 0]
    if not dados_validos: return drawing
    valores, labels = [d[1] for d in dados_validos], [d[0] for d in dados_validos]
    pie = Pie()
    pie.x, pie.y, pie.width, pie.height = 70, 20, 100, 100
    pie.data, pie.labels = valores, labels
    cores = [Cores.CHART_1, Cores.CHART_2, Cores.CHART_3, Cores.CHART_4, Cores.CHART_5]
    for i in range(len(valores)):
        pie.slices[i].fillColor = cores[i % len(cores)]
        pie.slices[i].strokeColor = Cores.BRANCO
    pie.sideLabels = True
    pie.slices.fontName = 'Helvetica'
    pie.slices.fontSize = 8
    drawing.add(pie)
    return drawing

class PDFGeneratorPro:
    def __init__(self, config=None):
        self.config = config or {}
        self.styles = getSampleStyleSheet()
        self.width, self.height = A4
        self.content_width = self.width - MARGEM_ESQUERDA - MARGEM_DIREITA
        self._setup_styles()
    
    def _setup_styles(self):
        self.styles.add(ParagraphStyle('TituloCapa', fontSize=26, textColor=Cores.AZUL_ESCURO,
            alignment=TA_CENTER, fontName='Helvetica-Bold', leading=32, spaceAfter=10))
        self.styles.add(ParagraphStyle('SubtituloCapa', fontSize=12, textColor=Cores.CINZA_600,
            alignment=TA_CENTER, leading=16, spaceAfter=15))
        self.styles.add(ParagraphStyle('NomeEmpresa', fontSize=20, textColor=Cores.PRETO,
            alignment=TA_CENTER, fontName='Helvetica-Bold', leading=26, spaceAfter=8))
        self.styles.add(ParagraphStyle('TituloSecao', fontSize=14, textColor=Cores.AZUL_ESCURO,
            fontName='Helvetica-Bold', leading=20, spaceBefore=15, spaceAfter=10))
        self.styles.add(ParagraphStyle('SubtituloSecao', fontSize=11, textColor=Cores.CINZA_700,
            fontName='Helvetica-Bold', leading=15, spaceBefore=12, spaceAfter=8))
        self.styles.add(ParagraphStyle('Corpo', fontSize=10, textColor=Cores.CINZA_700,
            alignment=TA_JUSTIFY, leading=14, spaceAfter=8))
        self.styles.add(ParagraphStyle('TextoPequeno', fontSize=8, textColor=Cores.CINZA_500, leading=11))
        self.styles.add(ParagraphStyle('CelulaTabela', fontSize=9, textColor=Cores.CINZA_700, leading=12))
        self.styles.add(ParagraphStyle('CelulaTabelaCenter', fontSize=9, textColor=Cores.CINZA_700, leading=12, alignment=TA_CENTER))
        self.styles.add(ParagraphStyle('CelulaTabelaRight', fontSize=9, textColor=Cores.CINZA_700, leading=12, alignment=TA_RIGHT))
        self.styles.add(ParagraphStyle('CelulaHeader', fontSize=9, textColor=Cores.BRANCO, fontName='Helvetica-Bold', leading=12, alignment=TA_CENTER))
        self.styles.add(ParagraphStyle('Rodape', fontSize=8, textColor=Cores.CINZA_500, alignment=TA_CENTER))
    
    def _p(self, texto, estilo='CelulaTabela'):
        return Paragraph(str(texto) if texto else "—", self.styles[estilo])
    
    def _fmt_moeda(self, valor):
        if valor is None: return "—"
        try:
            v = float(valor)
            fmt = f"R$ {abs(v):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            return f"-{fmt}" if v < 0 else fmt
        except: return "—"
    
    def _fmt_pct(self, valor, casas=1, sinal=False):
        if valor is None: return "—"
        try:
            v = float(valor)
            if sinal and v > 0: return f"+{v:.{casas}f}%"
            return f"{v:.{casas}f}%"
        except: return "—"
    
    def _fmt_indice(self, valor, casas=2):
        if valor is None: return "—"
        try: return f"{float(valor):.{casas}f}"
        except: return "—"
    
    def _calcular_indicadores(self, dados_mensais):
        if not dados_mensais: return self._indicadores_vazios()
        dados = sorted(dados_mensais, key=lambda x: (x.get('ano', 0), x.get('mes', 0)))
        n = len(dados)
        ultimo = dados[-1] if dados else {}
        
        # DRE
        receita_bruta = sum(d.get('receita_bruta', 0) or d.get('receita', 0) or 0 for d in dados)
        receita_servicos = sum(d.get('receita_servicos', 0) or 0 for d in dados)
        deducoes = sum(d.get('deducoes_receita', 0) or 0 for d in dados)
        receita_liq_imp = sum(d.get('receita_liquida', 0) or 0 for d in dados)
        receita_liquida = receita_liq_imp if receita_liq_imp else receita_bruta - deducoes
        custos = sum(d.get('custos_total', 0) or d.get('custos', 0) or 0 for d in dados)
        lucro_bruto_imp = sum(d.get('lucro_bruto', 0) or 0 for d in dados)
        lucro_bruto = lucro_bruto_imp if lucro_bruto_imp else receita_liquida - custos
        despesas_op = sum(d.get('despesas_operacionais', 0) or d.get('despesas', 0) or 0 for d in dados)
        folha = sum(d.get('folha', 0) or 0 for d in dados)
        desp_fin = sum(d.get('despesas_financeiras', 0) or 0 for d in dados)
        rec_fin = sum(d.get('receitas_financeiras', 0) or 0 for d in dados)
        lucro_op = lucro_bruto - despesas_op - folha - desp_fin + rec_fin
        
        iss = sum(d.get('iss', 0) or 0 for d in dados)
        pis = sum(d.get('pis', 0) or 0 for d in dados)
        cofins = sum(d.get('cofins', 0) or 0 for d in dados)
        irpj = sum(d.get('irpj', 0) or 0 for d in dados)
        csll = sum(d.get('csll', 0) or 0 for d in dados)
        # CORRIGIDO: Priorizar 'impostos' sobre 'impostos_total'
        imp_total = sum(d.get('impostos', 0) or d.get('impostos_total', 0) or 0 for d in dados)
        if imp_total == 0: imp_total = iss + pis + cofins + irpj + csll
        
        lucro_liq_imp = sum(d.get('lucro_liquido', 0) or 0 for d in dados)
        lucro_liquido = lucro_liq_imp if lucro_liq_imp else lucro_op - irpj - csll
        
        # Balanço
        disponivel = ultimo.get('disponivel', 0) or 0
        caixa = ultimo.get('caixa', 0) or 0
        bancos = ultimo.get('bancos', 0) or 0
        if not disponivel: disponivel = caixa + bancos
        clientes = ultimo.get('clientes', 0) or 0
        estoques = ultimo.get('estoques', 0) or 0
        ac = ultimo.get('ativo_circulante', 0) or (disponivel + clientes + estoques)
        anc = ultimo.get('ativo_nao_circulante', 0) or ultimo.get('imobilizado', 0) or 0
        imobilizado = ultimo.get('imobilizado', 0) or 0
        at = ultimo.get('ativo_total', 0) or (ac + anc)
        
        fornecedores = ultimo.get('fornecedores', 0) or 0
        obrig_trab = ultimo.get('obrigacoes_trabalhistas', 0) or 0
        obrig_trib = ultimo.get('obrigacoes_tributarias', 0) or 0
        emp_cp = ultimo.get('emprestimos_cp', 0) or 0
        pc = ultimo.get('passivo_circulante', 0) or (fornecedores + obrig_trab + obrig_trib + emp_cp)
        emp_lp = ultimo.get('emprestimos_lp', 0) or 0
        pnc = ultimo.get('passivo_nao_circulante', 0) or emp_lp
        pt = ultimo.get('passivo_total', 0) or (pc + pnc)
        capital_social = ultimo.get('capital_social', 0) or 0
        lucros_acum = ultimo.get('lucros_acumulados', 0) or 0
        dividendos_pagar = ultimo.get('dividendos_pagar', 0) or 0
        
        # ==================================================================
        # PATRIMÔNIO LÍQUIDO - CÁLCULO CORRETO PARA ANÁLISE
        # ==================================================================
        # O PL Contábil durante o exercício deve incluir o Resultado do Período
        # 
        # Estrutura do PL:
        #   Capital Social
        #   + Reservas de Capital
        #   + Reservas de Lucros  
        #   + Lucros Acumulados (de exercícios anteriores)
        #   + Resultado do Exercício (ainda não encerrado/distribuído)
        #   = PATRIMÔNIO LÍQUIDO TOTAL
        #
        # Nota: Dividendos a Pagar NÃO fazem parte do PL (são passivo),
        # mas indicam lucros anteriores retidos na empresa.
        # ==================================================================
        
        pl_informado = ultimo.get('patrimonio_liquido', 0) or 0
        pl_total_informado = ultimo.get('patrimonio_liquido_total', 0) or 0
        
        # Se o PL informado não inclui o resultado do exercício, calculamos
        if pl_total_informado > 0:
            # Parser já calculou o PL Total (com resultado)
            pl = pl_total_informado
        elif pl_informado > 0:
            # PL informado pode ser apenas Capital Social
            # Se lucro_liquido é significativo e PL é muito baixo, soma o resultado
            if lucro_liquido > 0 and pl_informado > 0 and lucro_liquido > pl_informado:
                # Lucro maior que PL indica que PL não inclui resultado
                pl = pl_informado + lucro_liquido
            else:
                pl = pl_informado
        else:
            # Fallback: calcula pela diferença AT - PT
            pl = at - pt
        
        # Garante que PL inclua pelo menos capital + resultado
        pl_minimo = capital_social + lucro_liquido
        if pl < pl_minimo and capital_social > 0:
            pl = pl_minimo
        
        # PL Inicial (para cálculo alternativo de ROE)
        pl_inicial = capital_social + lucros_acum  # Sem resultado do exercício atual
        
        # ==================================================================
        # INDICADORES
        # ==================================================================
        
        # Liquidez
        liq_corr = ac / pc if pc > 0 else 0
        liq_seca = (ac - estoques) / pc if pc > 0 else 0
        liq_imed = disponivel / pc if pc > 0 else 0
        liq_geral = (ac + anc) / (pc + pnc) if (pc + pnc) > 0 else 0
        cap_giro = ac - pc
        ncg = (clientes + estoques) - fornecedores
        
        # Endividamento
        endiv_geral = (pt / at * 100) if at > 0 else 0
        comp_endiv = (pc / (pc + pnc) * 100) if (pc + pnc) > 0 else 0
        grau_endiv = (pt / pl * 100) if pl > 0 else 0
        imob_pl = (anc / pl * 100) if pl > 0 else 0
        
        # Rentabilidade
        mg_bruta = (lucro_bruto / receita_bruta * 100) if receita_bruta > 0 else 0
        mg_op = (lucro_op / receita_bruta * 100) if receita_bruta > 0 else 0
        mg_liq = (lucro_liquido / receita_bruta * 100) if receita_bruta > 0 else 0
        
        # ==================================================================
        # ROE - RETORNO SOBRE O PATRIMÔNIO LÍQUIDO
        # ==================================================================
        # Fórmula: ROE = Lucro Líquido / Patrimônio Líquido
        #
        # O PL usado deve incluir o resultado do exercício quando este ainda
        # não foi encerrado, pois representa o capital total dos sócios.
        # ==================================================================
        roe = (lucro_liquido / pl * 100) if pl > 0 else 0
        
        # ROE sobre capital inicial (para comparação - DuPont)
        roe_inicial = (lucro_liquido / pl_inicial * 100) if pl_inicial > 0 else 0
        
        roa = (lucro_liquido / at * 100) if at > 0 else 0
        giro = receita_bruta / at if at > 0 else 0
        carga_trib = (imp_total / receita_bruta * 100) if receita_bruta > 0 else 0
        
        receitas = [d.get('receita_bruta', 0) or d.get('receita', 0) or 0 for d in dados]
        lucros = [d.get('lucro_liquido', 0) or 0 for d in dados]
        var_rec = ((receitas[-1] / receitas[0]) - 1) * 100 if len(receitas) >= 2 and receitas[0] > 0 else 0
        var_luc = ((lucros[-1] / lucros[0]) - 1) * 100 if len(lucros) >= 2 and lucros[0] != 0 else 0
        
        dados_rec, dados_luc, dados_evol = [], [], []
        for d in dados[-12:]:
            mes, ano = d.get('mes', 0), d.get('ano', 0)
            per = f"{mes:02d}/{str(ano)[-2:]}"
            rec = d.get('receita_bruta', 0) or d.get('receita', 0) or 0
            luc = d.get('lucro_liquido', 0) or 0
            # CORRIGIDO: Priorizar 'impostos' sobre 'impostos_total'
            imp = d.get('impostos', 0) or d.get('impostos_total', 0) or 0
            dados_rec.append((per, rec))
            dados_luc.append((per, luc))
            dados_evol.append({'periodo': f"{mes:02d}/{ano}", 'receita': rec, 'lucro': luc, 'impostos': imp,
                              'margem': (luc / rec * 100) if rec > 0 else 0})
        
        score = self._calcular_score(liq_corr, endiv_geral, mg_liq, var_rec)
        
        return {
            'meses_analisados': n,
            'periodo_inicio': f"{dados[0].get('mes', 0):02d}/{dados[0].get('ano', 0)}" if dados else "",
            'periodo_fim': f"{ultimo.get('mes', 0):02d}/{ultimo.get('ano', 0)}" if ultimo else "",
            'receita_bruta': receita_bruta, 'receita_total': receita_bruta, 'receita_servicos': receita_servicos,
            'deducoes_receita': deducoes, 'receita_liquida': receita_liquida, 'custos_total': custos,
            'lucro_bruto': lucro_bruto, 'despesas_operacionais': despesas_op, 'folha_total': folha,
            'despesas_financeiras': desp_fin, 'receitas_financeiras': rec_fin, 'lucro_operacional': lucro_op,
            'lucro_liquido': lucro_liquido, 'receita_media': receita_bruta / n if n > 0 else 0,
            'lucro_medio': lucro_liquido / n if n > 0 else 0,
            'iss': iss, 'pis': pis, 'cofins': cofins, 'irpj': irpj, 'csll': csll, 'impostos_total': imp_total,
            'ativo_total': at, 'ativo_circulante': ac, 'disponivel': disponivel, 'caixa': caixa, 'bancos': bancos,
            'clientes': clientes, 'estoques': estoques, 'ativo_nao_circulante': anc, 'imobilizado': imobilizado,
            'passivo_total': pt, 'passivo_circulante': pc, 'fornecedores': fornecedores,
            'obrigacoes_trabalhistas': obrig_trab, 'obrigacoes_tributarias': obrig_trib, 'emprestimos_cp': emp_cp,
            'passivo_nao_circulante': pnc, 'emprestimos_lp': emp_lp, 'patrimonio_liquido': pl,
            'patrimonio_liquido_inicial': pl_inicial, 'dividendos_pagar': dividendos_pagar,
            'capital_social': capital_social, 'lucros_acumulados': lucros_acum,
            'liquidez_corrente': liq_corr, 'liquidez_seca': liq_seca, 'liquidez_imediata': liq_imed,
            'liquidez_geral': liq_geral, 'capital_giro': cap_giro, 'ncg': ncg,
            'endividamento_geral': endiv_geral, 'composicao_endividamento': comp_endiv,
            'grau_endividamento': grau_endiv, 'imobilizacao_pl': imob_pl,
            'margem_bruta': mg_bruta, 'margem_operacional': mg_op, 'margem_liquida': mg_liq,
            'roe': roe, 'roe_sobre_capital_inicial': roe_inicial, 'roa': roa, 'giro_ativo': giro, 'carga_tributaria': carga_trib,
            'variacao_receita': var_rec, 'variacao_lucro': var_luc,
            'dados_receita': dados_rec, 'dados_lucro': dados_luc, 'dados_evolucao': dados_evol, 'score': score,
        }
    
    def _indicadores_vazios(self):
        campos = ['meses_analisados', 'receita_bruta', 'receita_total', 'receita_servicos', 'deducoes_receita',
            'receita_liquida', 'custos_total', 'lucro_bruto', 'despesas_operacionais', 'folha_total',
            'despesas_financeiras', 'receitas_financeiras', 'lucro_operacional', 'lucro_liquido',
            'receita_media', 'lucro_medio', 'iss', 'pis', 'cofins', 'irpj', 'csll', 'impostos_total',
            'ativo_total', 'ativo_circulante', 'disponivel', 'caixa', 'bancos', 'clientes', 'estoques',
            'ativo_nao_circulante', 'imobilizado', 'passivo_total', 'passivo_circulante', 'fornecedores',
            'obrigacoes_trabalhistas', 'obrigacoes_tributarias', 'emprestimos_cp', 'passivo_nao_circulante',
            'emprestimos_lp', 'patrimonio_liquido', 'capital_social', 'lucros_acumulados',
            'liquidez_corrente', 'liquidez_seca', 'liquidez_imediata', 'liquidez_geral', 'capital_giro', 'ncg',
            'endividamento_geral', 'composicao_endividamento', 'grau_endividamento', 'imobilizacao_pl',
            'margem_bruta', 'margem_operacional', 'margem_liquida', 'roe', 'roa', 'giro_ativo',
            'carga_tributaria', 'variacao_receita', 'variacao_lucro', 'score']
        r = {k: 0 for k in campos}
        r.update({'periodo_inicio': '', 'periodo_fim': '', 'dados_receita': [], 'dados_lucro': [], 'dados_evolucao': []})
        return r
    
    def _calcular_score(self, liq, endiv, margem, var):
        s = 0
        if liq >= 2: s += 25
        elif liq >= 1.5: s += 20
        elif liq >= 1: s += 15
        elif liq >= 0.8: s += 10
        elif liq >= 0.5: s += 5
        if endiv <= 30: s += 25
        elif endiv <= 50: s += 20
        elif endiv <= 70: s += 15
        elif endiv <= 85: s += 8
        elif endiv <= 100: s += 3
        if margem >= 15: s += 25
        elif margem >= 10: s += 20
        elif margem >= 5: s += 15
        elif margem >= 0: s += 10
        elif margem >= -5: s += 5
        if var >= 15: s += 25
        elif var >= 10: s += 22
        elif var >= 5: s += 18
        elif var >= 0: s += 15
        elif var >= -5: s += 10
        elif var >= -10: s += 5
        return min(s, 100)
    
    def _gerar_insights(self, ind):
        ins = []
        if ind.get('liquidez_corrente', 0) < 1:
            ins.append({'tipo': 'critico', 'titulo': 'Risco de Insolvência',
                'texto': f"Liquidez corrente de {ind['liquidez_corrente']:.2f} indica dificuldade para honrar compromissos de curto prazo."})
        elif ind.get('liquidez_corrente', 0) >= 2:
            ins.append({'tipo': 'positivo', 'titulo': 'Excelente Liquidez',
                'texto': f"Liquidez corrente de {ind['liquidez_corrente']:.2f} demonstra ampla folga financeira."})
        if ind.get('patrimonio_liquido', 0) < 0:
            ins.append({'tipo': 'critico', 'titulo': 'Passivo a Descoberto',
                'texto': f"Patrimônio Líquido negativo de {self._fmt_moeda(ind['patrimonio_liquido'])}."})
        if ind.get('endividamento_geral', 0) > 80:
            ins.append({'tipo': 'critico', 'titulo': 'Endividamento Crítico',
                'texto': f"Endividamento de {ind['endividamento_geral']:.1f}% indica dependência excessiva de capital de terceiros."})
        elif ind.get('endividamento_geral', 0) <= 50:
            ins.append({'tipo': 'positivo', 'titulo': 'Estrutura de Capital Saudável',
                'texto': f"Endividamento de {ind['endividamento_geral']:.1f}% demonstra equilíbrio."})
        if ind.get('margem_liquida', 0) < 0:
            ins.append({'tipo': 'critico', 'titulo': 'Operação Deficitária',
                'texto': f"Margem líquida de {ind['margem_liquida']:.1f}% indica prejuízo."})
        elif ind.get('margem_liquida', 0) >= 15:
            ins.append({'tipo': 'positivo', 'titulo': 'Alta Rentabilidade',
                'texto': f"Margem líquida de {ind['margem_liquida']:.1f}% está acima da média."})
        if ind.get('capital_giro', 0) < 0:
            ins.append({'tipo': 'critico', 'titulo': 'Capital de Giro Negativo',
                'texto': f"Déficit de {self._fmt_moeda(abs(ind['capital_giro']))} no capital de giro."})
        if ind.get('variacao_receita', 0) > 10:
            ins.append({'tipo': 'positivo', 'titulo': 'Crescimento de Receita',
                'texto': f"Receita cresceu {ind['variacao_receita']:.1f}% no período."})
        elif ind.get('variacao_receita', 0) < -10:
            ins.append({'tipo': 'critico', 'titulo': 'Queda de Faturamento',
                'texto': f"Receita caiu {abs(ind['variacao_receita']):.1f}% no período."})
        if ind.get('roe', 0) > 20:
            ins.append({'tipo': 'positivo', 'titulo': 'Excelente Retorno ao Acionista',
                'texto': f"ROE de {ind['roe']:.1f}% demonstra alta eficiência."})
        if ind.get('carga_tributaria', 0) > 30:
            ins.append({'tipo': 'critico', 'titulo': 'Carga Tributária Elevada',
                'texto': f"Carga de {ind['carga_tributaria']:.1f}% sobre receita."})
        return ins
    
    def generate(self, result):
        empresa = {'razao_social': result.get('empresa', 'Empresa'), 'cnpj': result.get('cnpj', '')}
        dados_mensais = result.get('dados_mensais', [])
        ind = self._calcular_indicadores(dados_mensais) if dados_mensais else self._indicadores_vazios()
        if result.get('score') is not None: ind['score'] = result.get('score')
        return self._gerar_pdf(empresa, ind, self._gerar_insights(ind))
    
    def gerar_relatorio(self, empresa, dados_mensais, analise=None, alertas=None, config=None):
        ind = self._calcular_indicadores(dados_mensais)
        if analise and analise.get('score') is not None: ind['score'] = analise.get('score')
        return self._gerar_pdf(empresa, ind, self._gerar_insights(ind))
    
    def _gerar_pdf(self, empresa, ind, insights):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=MARGEM_DIREITA, leftMargin=MARGEM_ESQUERDA,
                               topMargin=MARGEM_SUPERIOR, bottomMargin=MARGEM_INFERIOR)
        story = []
        story.extend(self._criar_capa(empresa, ind))
        story.append(PageBreak())
        story.extend(self._criar_resumo(empresa, ind, insights))
        story.append(PageBreak())
        story.extend(self._criar_dre(ind))
        story.append(PageBreak())
        story.extend(self._criar_balanco(ind))
        story.append(PageBreak())
        story.extend(self._criar_liquidez(ind))
        story.extend(self._criar_endividamento(ind))
        story.append(PageBreak())
        story.extend(self._criar_rentabilidade(ind))
        story.extend(self._criar_analise_fiscal(ind))
        story.append(PageBreak())
        story.extend(self._criar_evolucao(ind))
        story.append(PageBreak())
        story.extend(self._criar_conclusoes(ind, insights))
        doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        buffer.seek(0)
        return buffer.read()
    
    def _header_footer(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(Cores.AZUL_ESCURO)
        canvas.setLineWidth(0.5)
        canvas.line(MARGEM_ESQUERDA, self.height - MARGEM_SUPERIOR + 0.3*cm,
                   self.width - MARGEM_DIREITA, self.height - MARGEM_SUPERIOR + 0.3*cm)
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(Cores.CINZA_500)
        canvas.drawString(MARGEM_ESQUERDA, MARGEM_INFERIOR - 0.5*cm, f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
        canvas.drawRightString(self.width - MARGEM_DIREITA, MARGEM_INFERIOR - 0.5*cm, f"Página {doc.page}")
        canvas.drawCentredString(self.width / 2, MARGEM_INFERIOR - 0.5*cm, "Kontabil - Análise Financeira Inteligente")
        canvas.line(MARGEM_ESQUERDA, MARGEM_INFERIOR - 0.2*cm, self.width - MARGEM_DIREITA, MARGEM_INFERIOR - 0.2*cm)
        canvas.restoreState()
    
    def _criar_capa(self, empresa, ind):
        el = [Spacer(1, 1.5*cm)]
        el.append(Paragraph("RELATÓRIO DE", self.styles['SubtituloCapa']))
        el.append(Paragraph("DIAGNÓSTICO FINANCEIRO", self.styles['TituloCapa']))
        sep = Table([['']], colWidths=[6*cm], rowHeights=[3])
        sep.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), Cores.AZUL_ESCURO)]))
        el.append(sep)
        el.append(Spacer(1, 1.2*cm))
        el.append(Paragraph(empresa.get('razao_social', 'Empresa').upper(), self.styles['NomeEmpresa']))
        if empresa.get('cnpj'): el.append(Paragraph(f"CNPJ: {empresa['cnpj']}", self.styles['SubtituloCapa']))
        el.append(Spacer(1, 0.6*cm))
        el.append(Paragraph(f"Período: {ind.get('periodo_inicio', '')} a {ind.get('periodo_fim', '')}", self.styles['SubtituloCapa']))
        el.append(Paragraph(f"({ind.get('meses_analisados', 0)} meses analisados)", self.styles['TextoPequeno']))
        el.append(Spacer(1, 1.2*cm))
        gauge = GaugeChart(ind.get('score', 0))
        gt = Table([[gauge]], colWidths=[self.content_width])
        gt.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'CENTER')]))
        el.append(gt)
        el.append(Spacer(1, 0.8*cm))
        kpi = [
            [self._p('RECEITA TOTAL', 'CelulaHeader'), self._p('LUCRO LÍQUIDO', 'CelulaHeader'),
             self._p('MARGEM LÍQUIDA', 'CelulaHeader'), self._p('LIQUIDEZ', 'CelulaHeader')],
            [self._p(self._fmt_moeda(ind.get('receita_total')), 'CelulaTabelaCenter'),
             self._p(self._fmt_moeda(ind.get('lucro_liquido')), 'CelulaTabelaCenter'),
             self._p(self._fmt_pct(ind.get('margem_liquida')), 'CelulaTabelaCenter'),
             self._p(self._fmt_indice(ind.get('liquidez_corrente')), 'CelulaTabelaCenter')]]
        kt = Table(kpi, colWidths=[4*cm]*4, rowHeights=[24, 30])
        kt.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), Cores.AZUL_ESCURO), ('BACKGROUND', (0, 1), (-1, 1), Cores.AZUL_BG),
                                ('GRID', (0, 0), (-1, -1), 0.5, Cores.CINZA_300), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        el.append(kt)
        kpi2 = [
            [self._p('ROE', 'CelulaHeader'), self._p('ENDIVIDAMENTO', 'CelulaHeader'),
             self._p('CAPITAL DE GIRO', 'CelulaHeader'), self._p('PATRIMÔNIO LÍQ.', 'CelulaHeader')],
            [self._p(self._fmt_pct(ind.get('roe')), 'CelulaTabelaCenter'),
             self._p(self._fmt_pct(ind.get('endividamento_geral')), 'CelulaTabelaCenter'),
             self._p(self._fmt_moeda(ind.get('capital_giro')), 'CelulaTabelaCenter'),
             self._p(self._fmt_moeda(ind.get('patrimonio_liquido')), 'CelulaTabelaCenter')]]
        kt2 = Table(kpi2, colWidths=[4*cm]*4, rowHeights=[24, 30])
        kt2.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), Cores.CINZA_700), ('BACKGROUND', (0, 1), (-1, 1), Cores.CINZA_100),
                                 ('GRID', (0, 0), (-1, -1), 0.5, Cores.CINZA_300), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        el.append(kt2)
        return el
    
    def _criar_resumo(self, empresa, ind, insights):
        el = [Paragraph("1. RESUMO EXECUTIVO", self.styles['TituloSecao'])]
        sep = Table([['']], colWidths=[self.content_width], rowHeights=[2])
        sep.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), Cores.AZUL_ESCURO)]))
        el.append(sep)
        el.append(Spacer(1, 0.5*cm))
        score = ind.get('score', 0)
        if score >= 70: status, cor, txt = "BOA SAÚDE FINANCEIRA", Cores.VERDE, "A empresa apresenta indicadores financeiros sólidos."
        elif score >= 40: status, cor, txt = "ATENÇÃO NECESSÁRIA", Cores.AMARELO, "A empresa apresenta alguns pontos de atenção."
        else: status, cor, txt = "SITUAÇÃO CRÍTICA", Cores.VERMELHO, "A empresa necessita de ações urgentes."
        st = [[Paragraph(f"<b>{status}</b> (Score: {score}/100)", ParagraphStyle('S', fontSize=13, textColor=cor, fontName='Helvetica-Bold', alignment=TA_CENTER))]]
        stb = Table(st, colWidths=[self.content_width], rowHeights=[40])
        stb.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), Cores.CINZA_50), ('BOX', (0, 0), (0, 0), 2, cor), ('VALIGN', (0, 0), (0, 0), 'MIDDLE')]))
        el.append(stb)
        el.append(Spacer(1, 0.4*cm))
        el.append(Paragraph(txt, self.styles['Corpo']))
        el.append(Spacer(1, 0.5*cm))
        el.append(Paragraph("1.1 Principais Números do Período", self.styles['SubtituloSecao']))
        num = [
            [self._p('DRE (ACUMULADO)', 'CelulaHeader'), self._p('VALOR', 'CelulaHeader'), self._p('BALANÇO', 'CelulaHeader'), self._p('VALOR', 'CelulaHeader')],
            [self._p('Receita Bruta'), self._p(self._fmt_moeda(ind.get('receita_bruta')), 'CelulaTabelaRight'), self._p('Ativo Total'), self._p(self._fmt_moeda(ind.get('ativo_total')), 'CelulaTabelaRight')],
            [self._p('(-) Deduções'), self._p(self._fmt_moeda(-abs(ind.get('deducoes_receita', 0))), 'CelulaTabelaRight'), self._p('Passivo Total'), self._p(self._fmt_moeda(ind.get('passivo_total')), 'CelulaTabelaRight')],
            [self._p('Receita Líquida'), self._p(self._fmt_moeda(ind.get('receita_liquida')), 'CelulaTabelaRight'), self._p('Patrimônio Líquido'), self._p(self._fmt_moeda(ind.get('patrimonio_liquido')), 'CelulaTabelaRight')],
            [self._p('Lucro Bruto'), self._p(self._fmt_moeda(ind.get('lucro_bruto')), 'CelulaTabelaRight'), self._p('Capital de Giro'), self._p(self._fmt_moeda(ind.get('capital_giro')), 'CelulaTabelaRight')],
            [self._p('<b>Lucro Líquido</b>'), self._p(self._fmt_moeda(ind.get('lucro_liquido')), 'CelulaTabelaRight'), self._p('Disponível'), self._p(self._fmt_moeda(ind.get('disponivel')), 'CelulaTabelaRight')]]
        nt = Table(num, colWidths=[4*cm]*4, rowHeights=[24]+[22]*5)
        nt.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), Cores.AZUL_ESCURO), ('GRID', (0, 0), (-1, -1), 0.5, Cores.CINZA_300),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('BACKGROUND', (0, -1), (-1, -1), Cores.AZUL_BG)]))
        el.append(nt)
        el.append(Spacer(1, 0.5*cm))
        crit = [i for i in insights if i['tipo'] == 'critico']
        pos = [i for i in insights if i['tipo'] == 'positivo']
        if crit:
            el.append(Paragraph("1.2 Pontos de Atenção", self.styles['SubtituloSecao']))
            for i in crit[:4]: el.append(Paragraph(f"⚠️ <b>{i['titulo']}</b>: {i['texto']}", self.styles['Corpo']))
        if pos:
            el.append(Paragraph("1.3 Pontos Positivos", self.styles['SubtituloSecao']))
            for i in pos[:4]: el.append(Paragraph(f"✅ <b>{i['titulo']}</b>: {i['texto']}", self.styles['Corpo']))
        return el
    
    def _criar_dre(self, ind):
        el = [Paragraph("2. DEMONSTRAÇÃO DO RESULTADO (DRE)", self.styles['TituloSecao'])]
        sep = Table([['']], colWidths=[self.content_width], rowHeights=[2])
        sep.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), Cores.AZUL_ESCURO)]))
        el.append(sep)
        el.append(Spacer(1, 0.4*cm))
        el.append(Paragraph(f"Período: <b>{ind.get('periodo_inicio', '')}</b> a <b>{ind.get('periodo_fim', '')}</b> ({ind.get('meses_analisados', 0)} meses)", self.styles['Corpo']))
        el.append(Spacer(1, 0.4*cm))
        rec = ind.get('receita_bruta', 0) or 1
        def av(v): return f"{(v / rec * 100):.1f}%" if v else "—"
        dre = [
            [self._p('CONTA', 'CelulaHeader'), self._p('VALOR (R$)', 'CelulaHeader'), self._p('AV%', 'CelulaHeader')],
            [self._p('<b>RECEITA BRUTA</b>'), self._p(self._fmt_moeda(ind.get('receita_bruta')), 'CelulaTabelaRight'), self._p('100,0%', 'CelulaTabelaCenter')],
            [self._p('   Receita de Serviços'), self._p(self._fmt_moeda(ind.get('receita_servicos')), 'CelulaTabelaRight'), self._p(av(ind.get('receita_servicos')), 'CelulaTabelaCenter')],
            [self._p('(-) Deduções da Receita'), self._p(self._fmt_moeda(-abs(ind.get('deducoes_receita', 0))), 'CelulaTabelaRight'), self._p(av(-abs(ind.get('deducoes_receita', 0))), 'CelulaTabelaCenter')],
            [self._p('<b>= RECEITA LÍQUIDA</b>'), self._p(self._fmt_moeda(ind.get('receita_liquida')), 'CelulaTabelaRight'), self._p(av(ind.get('receita_liquida')), 'CelulaTabelaCenter')],
            [self._p('(-) Custos'), self._p(self._fmt_moeda(-abs(ind.get('custos_total', 0))), 'CelulaTabelaRight'), self._p(av(-abs(ind.get('custos_total', 0))), 'CelulaTabelaCenter')],
            [self._p('<b>= LUCRO BRUTO</b>'), self._p(self._fmt_moeda(ind.get('lucro_bruto')), 'CelulaTabelaRight'), self._p(self._fmt_pct(ind.get('margem_bruta')), 'CelulaTabelaCenter')],
            [self._p('(-) Despesas Operacionais'), self._p(self._fmt_moeda(-abs(ind.get('despesas_operacionais', 0))), 'CelulaTabelaRight'), self._p(av(-abs(ind.get('despesas_operacionais', 0))), 'CelulaTabelaCenter')],
            [self._p('(-) Despesas com Pessoal'), self._p(self._fmt_moeda(-abs(ind.get('folha_total', 0))), 'CelulaTabelaRight'), self._p(av(-abs(ind.get('folha_total', 0))), 'CelulaTabelaCenter')],
            [self._p('(-) Despesas Financeiras'), self._p(self._fmt_moeda(-abs(ind.get('despesas_financeiras', 0))), 'CelulaTabelaRight'), self._p(av(-abs(ind.get('despesas_financeiras', 0))), 'CelulaTabelaCenter')],
            [self._p('(+) Receitas Financeiras'), self._p(self._fmt_moeda(ind.get('receitas_financeiras')), 'CelulaTabelaRight'), self._p(av(ind.get('receitas_financeiras')), 'CelulaTabelaCenter')],
            [self._p('<b>= LUCRO OPERACIONAL</b>'), self._p(self._fmt_moeda(ind.get('lucro_operacional')), 'CelulaTabelaRight'), self._p(self._fmt_pct(ind.get('margem_operacional')), 'CelulaTabelaCenter')],
            [self._p('(-) IRPJ'), self._p(self._fmt_moeda(-abs(ind.get('irpj', 0))), 'CelulaTabelaRight'), self._p(av(-abs(ind.get('irpj', 0))), 'CelulaTabelaCenter')],
            [self._p('(-) CSLL'), self._p(self._fmt_moeda(-abs(ind.get('csll', 0))), 'CelulaTabelaRight'), self._p(av(-abs(ind.get('csll', 0))), 'CelulaTabelaCenter')],
            [self._p('<b>= LUCRO LÍQUIDO</b>'), self._p(self._fmt_moeda(ind.get('lucro_liquido')), 'CelulaTabelaRight'), self._p(self._fmt_pct(ind.get('margem_liquida')), 'CelulaTabelaCenter')]]
        dt = Table(dre, colWidths=[9*cm, 4*cm, 3*cm], rowHeights=[24]+[20]*14)
        dt.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), Cores.AZUL_ESCURO), ('BACKGROUND', (0, 1), (-1, 1), Cores.AZUL_BG),
                                ('BACKGROUND', (0, 4), (-1, 4), Cores.CINZA_100), ('BACKGROUND', (0, 6), (-1, 6), Cores.CINZA_100),
                                ('BACKGROUND', (0, 11), (-1, 11), Cores.CINZA_100), ('BACKGROUND', (0, 14), (-1, 14), Cores.AZUL_MEDIO),
                                ('TEXTCOLOR', (0, 14), (-1, 14), Cores.BRANCO), ('GRID', (0, 0), (-1, -1), 0.5, Cores.CINZA_300),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        el.append(dt)
        el.append(Spacer(1, 0.5*cm))
        if ind.get('dados_receita'):
            el.append(Paragraph("2.1 Evolução da Receita Mensal", self.styles['SubtituloSecao']))
            el.append(criar_grafico_linha(ind['dados_receita'], self.content_width - 20, 140))
        return el
    
    def _criar_balanco(self, ind):
        el = [Paragraph("3. BALANÇO PATRIMONIAL", self.styles['TituloSecao'])]
        sep = Table([['']], colWidths=[self.content_width], rowHeights=[2])
        sep.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), Cores.AZUL_ESCURO)]))
        el.append(sep)
        el.append(Spacer(1, 0.4*cm))
        el.append(Paragraph(f"Posição em <b>{ind.get('periodo_fim', '')}</b>", self.styles['Corpo']))
        el.append(Spacer(1, 0.4*cm))
        bal = [
            [self._p('ATIVO', 'CelulaHeader'), self._p('VALOR', 'CelulaHeader'), self._p('PASSIVO + PL', 'CelulaHeader'), self._p('VALOR', 'CelulaHeader')],
            [self._p('<b>ATIVO CIRCULANTE</b>'), self._p(self._fmt_moeda(ind.get('ativo_circulante')), 'CelulaTabelaRight'), self._p('<b>PASSIVO CIRCULANTE</b>'), self._p(self._fmt_moeda(ind.get('passivo_circulante')), 'CelulaTabelaRight')],
            [self._p('   Caixa'), self._p(self._fmt_moeda(ind.get('caixa')), 'CelulaTabelaRight'), self._p('   Fornecedores'), self._p(self._fmt_moeda(ind.get('fornecedores')), 'CelulaTabelaRight')],
            [self._p('   Bancos'), self._p(self._fmt_moeda(ind.get('bancos')), 'CelulaTabelaRight'), self._p('   Obrig. Trabalhistas'), self._p(self._fmt_moeda(ind.get('obrigacoes_trabalhistas')), 'CelulaTabelaRight')],
            [self._p('   Clientes'), self._p(self._fmt_moeda(ind.get('clientes')), 'CelulaTabelaRight'), self._p('   Obrig. Tributárias'), self._p(self._fmt_moeda(ind.get('obrigacoes_tributarias')), 'CelulaTabelaRight')],
            [self._p('   Estoques'), self._p(self._fmt_moeda(ind.get('estoques')), 'CelulaTabelaRight'), self._p('   Empréstimos CP'), self._p(self._fmt_moeda(ind.get('emprestimos_cp')), 'CelulaTabelaRight')],
            [self._p('<b>ATIVO NÃO CIRCULANTE</b>'), self._p(self._fmt_moeda(ind.get('ativo_nao_circulante')), 'CelulaTabelaRight'), self._p('<b>PASSIVO NÃO CIRCULANTE</b>'), self._p(self._fmt_moeda(ind.get('passivo_nao_circulante')), 'CelulaTabelaRight')],
            [self._p('   Imobilizado'), self._p(self._fmt_moeda(ind.get('imobilizado')), 'CelulaTabelaRight'), self._p('   Empréstimos LP'), self._p(self._fmt_moeda(ind.get('emprestimos_lp')), 'CelulaTabelaRight')],
            [self._p(''), self._p(''), self._p('<b>PATRIMÔNIO LÍQUIDO</b>'), self._p(self._fmt_moeda(ind.get('patrimonio_liquido')), 'CelulaTabelaRight')],
            [self._p(''), self._p(''), self._p('   Capital Social'), self._p(self._fmt_moeda(ind.get('capital_social')), 'CelulaTabelaRight')],
            [self._p(''), self._p(''), self._p('   Lucros Acumulados'), self._p(self._fmt_moeda(ind.get('lucros_acumulados')), 'CelulaTabelaRight')],
            [self._p('<b>TOTAL ATIVO</b>'), self._p(self._fmt_moeda(ind.get('ativo_total')), 'CelulaTabelaRight'), self._p('<b>TOTAL PASSIVO + PL</b>'), self._p(self._fmt_moeda(ind.get('ativo_total')), 'CelulaTabelaRight')]]
        bt = Table(bal, colWidths=[4.5*cm, 3.5*cm, 4.5*cm, 3.5*cm], rowHeights=[24]+[20]*11)
        bt.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), Cores.AZUL_ESCURO),
                                ('BACKGROUND', (0, 1), (1, 1), Cores.AZUL_BG), ('BACKGROUND', (2, 1), (3, 1), Cores.AZUL_BG),
                                ('BACKGROUND', (0, 6), (1, 6), Cores.CINZA_100), ('BACKGROUND', (2, 6), (3, 6), Cores.CINZA_100),
                                ('BACKGROUND', (2, 8), (3, 8), Cores.CINZA_100),
                                ('BACKGROUND', (0, -1), (-1, -1), Cores.AZUL_MEDIO), ('TEXTCOLOR', (0, -1), (-1, -1), Cores.BRANCO),
                                ('GRID', (0, 0), (-1, -1), 0.5, Cores.CINZA_300), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        el.append(bt)
        return el
    
    def _criar_liquidez(self, ind):
        el = [Paragraph("4. ANÁLISE DE LIQUIDEZ", self.styles['TituloSecao'])]
        sep = Table([['']], colWidths=[self.content_width], rowHeights=[2])
        sep.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), Cores.AZUL_ESCURO)]))
        el.append(sep)
        el.append(Spacer(1, 0.4*cm))
        el.append(Paragraph("Capacidade de honrar compromissos financeiros.", self.styles['Corpo']))
        el.append(Spacer(1, 0.4*cm))
        def st(v, t='c'):
            if t == 'c': return 'Excelente' if v >= 2 else 'Bom' if v >= 1.5 else 'Adequado' if v >= 1 else 'Crítico'
            if t == 's': return 'Excelente' if v >= 1.2 else 'Bom' if v >= 1 else 'Adequado' if v >= 0.7 else 'Baixo'
            return 'Alto' if v >= 0.5 else 'Bom' if v >= 0.2 else 'Adequado' if v >= 0.1 else 'Baixo'
        liq = [
            [self._p('ÍNDICE', 'CelulaHeader'), self._p('VALOR', 'CelulaHeader'), self._p('PARÂM.', 'CelulaHeader'), self._p('STATUS', 'CelulaHeader'), self._p('FÓRMULA', 'CelulaHeader')],
            [self._p('Liquidez Corrente'), self._p(self._fmt_indice(ind.get('liquidez_corrente')), 'CelulaTabelaCenter'), self._p('≥ 1,50', 'CelulaTabelaCenter'), self._p(st(ind.get('liquidez_corrente', 0)), 'CelulaTabelaCenter'), self._p('AC / PC', 'CelulaTabelaCenter')],
            [self._p('Liquidez Seca'), self._p(self._fmt_indice(ind.get('liquidez_seca')), 'CelulaTabelaCenter'), self._p('≥ 1,00', 'CelulaTabelaCenter'), self._p(st(ind.get('liquidez_seca', 0), 's'), 'CelulaTabelaCenter'), self._p('(AC-Est)/PC', 'CelulaTabelaCenter')],
            [self._p('Liquidez Imediata'), self._p(self._fmt_indice(ind.get('liquidez_imediata')), 'CelulaTabelaCenter'), self._p('≥ 0,20', 'CelulaTabelaCenter'), self._p(st(ind.get('liquidez_imediata', 0), 'i'), 'CelulaTabelaCenter'), self._p('Disp / PC', 'CelulaTabelaCenter')],
            [self._p('Liquidez Geral'), self._p(self._fmt_indice(ind.get('liquidez_geral')), 'CelulaTabelaCenter'), self._p('≥ 1,00', 'CelulaTabelaCenter'), self._p(st(ind.get('liquidez_geral', 0)), 'CelulaTabelaCenter'), self._p('(AC+RLP)/(PC+PNC)', 'CelulaTabelaCenter')]]
        lt = Table(liq, colWidths=[3.5*cm, 2*cm, 2.2*cm, 2.3*cm, 4*cm], rowHeights=[24]+[22]*4)
        lt.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), Cores.AZUL_ESCURO), ('GRID', (0, 0), (-1, -1), 0.5, Cores.CINZA_300), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        el.append(lt)
        el.append(Spacer(1, 0.5*cm))
        el.append(Paragraph("4.1 Capital de Giro", self.styles['SubtituloSecao']))
        cg = [
            [self._p('INDICADOR', 'CelulaHeader'), self._p('VALOR', 'CelulaHeader'), self._p('SITUAÇÃO', 'CelulaHeader')],
            [self._p('Capital de Giro Líquido'), self._p(self._fmt_moeda(ind.get('capital_giro')), 'CelulaTabelaCenter'), self._p('✅ Positivo' if ind.get('capital_giro', 0) >= 0 else '⚠️ NEGATIVO', 'CelulaTabelaCenter')],
            [self._p('NCG'), self._p(self._fmt_moeda(ind.get('ncg')), 'CelulaTabelaCenter'), self._p('Normal' if ind.get('ncg', 0) >= 0 else 'Negativa', 'CelulaTabelaCenter')]]
        ct = Table(cg, colWidths=[7*cm, 4.5*cm, 4.5*cm], rowHeights=[24, 22, 22])
        ct.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), Cores.CINZA_700), ('GRID', (0, 0), (-1, -1), 0.5, Cores.CINZA_300), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        el.append(ct)
        el.append(Spacer(1, 0.5*cm))
        return el
    
    def _criar_endividamento(self, ind):
        el = [Paragraph("5. ANÁLISE DE ENDIVIDAMENTO", self.styles['TituloSecao'])]
        sep = Table([['']], colWidths=[self.content_width], rowHeights=[2])
        sep.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), Cores.AZUL_ESCURO)]))
        el.append(sep)
        el.append(Spacer(1, 0.4*cm))
        el.append(Paragraph("Estrutura de capital e dependência de terceiros.", self.styles['Corpo']))
        el.append(Spacer(1, 0.4*cm))
        end = [
            [self._p('INDICADOR', 'CelulaHeader'), self._p('VALOR', 'CelulaHeader'), self._p('PARÂM.', 'CelulaHeader'), self._p('INTERPRETAÇÃO', 'CelulaHeader')],
            [self._p('Endividamento Geral'), self._p(self._fmt_pct(ind.get('endividamento_geral')), 'CelulaTabelaCenter'), self._p('≤ 60%', 'CelulaTabelaCenter'), self._p('% do ativo financiado por terceiros')],
            [self._p('Composição (CP/Total)'), self._p(self._fmt_pct(ind.get('composicao_endividamento')), 'CelulaTabelaCenter'), self._p('≤ 50%', 'CelulaTabelaCenter'), self._p('% das dívidas de curto prazo')],
            [self._p('Grau de Endividamento'), self._p(self._fmt_pct(ind.get('grau_endividamento')), 'CelulaTabelaCenter'), self._p('≤ 100%', 'CelulaTabelaCenter'), self._p('Capital de terceiros / PL')],
            [self._p('Imobilização do PL'), self._p(self._fmt_pct(ind.get('imobilizacao_pl')), 'CelulaTabelaCenter'), self._p('≤ 50%', 'CelulaTabelaCenter'), self._p('% do PL aplicado no imobilizado')]]
        et = Table(end, colWidths=[5*cm, 2.5*cm, 2*cm, 5.5*cm], rowHeights=[24]+[22]*4)
        et.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), Cores.AZUL_ESCURO), ('GRID', (0, 0), (-1, -1), 0.5, Cores.CINZA_300), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        el.append(et)
        el.append(Spacer(1, 0.5*cm))
        return el
    
    def _criar_rentabilidade(self, ind):
        el = [Paragraph("6. ANÁLISE DE RENTABILIDADE", self.styles['TituloSecao'])]
        sep = Table([['']], colWidths=[self.content_width], rowHeights=[2])
        sep.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), Cores.AZUL_ESCURO)]))
        el.append(sep)
        el.append(Spacer(1, 0.4*cm))
        el.append(Paragraph("6.1 Análise de Margens", self.styles['SubtituloSecao']))
        def stm(v, t):
            if t == 'b': return 'Excelente' if v >= 50 else 'Bom' if v >= 40 else 'Adequado' if v >= 30 else 'Baixo'
            if t == 'o': return 'Excelente' if v >= 20 else 'Bom' if v >= 15 else 'Adequado' if v >= 10 else 'Baixo'
            return 'Excelente' if v >= 15 else 'Bom' if v >= 10 else 'Adequado' if v >= 5 else 'Prejuízo' if v < 0 else 'Baixo'
        mg = [
            [self._p('MARGEM', 'CelulaHeader'), self._p('VALOR', 'CelulaHeader'), self._p('PARÂM.', 'CelulaHeader'), self._p('STATUS', 'CelulaHeader')],
            [self._p('Margem Bruta'), self._p(self._fmt_pct(ind.get('margem_bruta')), 'CelulaTabelaCenter'), self._p('≥ 30%', 'CelulaTabelaCenter'), self._p(stm(ind.get('margem_bruta', 0), 'b'), 'CelulaTabelaCenter')],
            [self._p('Margem Operacional'), self._p(self._fmt_pct(ind.get('margem_operacional')), 'CelulaTabelaCenter'), self._p('≥ 10%', 'CelulaTabelaCenter'), self._p(stm(ind.get('margem_operacional', 0), 'o'), 'CelulaTabelaCenter')],
            [self._p('Margem Líquida'), self._p(self._fmt_pct(ind.get('margem_liquida')), 'CelulaTabelaCenter'), self._p('≥ 5%', 'CelulaTabelaCenter'), self._p(stm(ind.get('margem_liquida', 0), 'l'), 'CelulaTabelaCenter')]]
        mt = Table(mg, colWidths=[5*cm, 3*cm, 3*cm, 3*cm], rowHeights=[24]+[22]*3)
        mt.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), Cores.AZUL_ESCURO), ('GRID', (0, 0), (-1, -1), 0.5, Cores.CINZA_300), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        el.append(mt)
        el.append(Spacer(1, 0.5*cm))
        el.append(Paragraph("6.2 Retorno sobre Investimento", self.styles['SubtituloSecao']))
        ret = [
            [self._p('INDICADOR', 'CelulaHeader'), self._p('VALOR', 'CelulaHeader'), self._p('FÓRMULA', 'CelulaHeader'), self._p('INTERPRETAÇÃO', 'CelulaHeader')],
            [self._p('ROE'), self._p(self._fmt_pct(ind.get('roe')), 'CelulaTabelaCenter'), self._p('Lucro / PL', 'CelulaTabelaCenter'), self._p('Retorno capital dos sócios')],
            [self._p('ROA'), self._p(self._fmt_pct(ind.get('roa')), 'CelulaTabelaCenter'), self._p('Lucro / Ativo', 'CelulaTabelaCenter'), self._p('Eficiência uso dos ativos')],
            [self._p('Giro do Ativo'), self._p(f"{ind.get('giro_ativo', 0):.2f}x", 'CelulaTabelaCenter'), self._p('Receita / Ativo', 'CelulaTabelaCenter'), self._p('Velocidade uso dos ativos')]]
        rt = Table(ret, colWidths=[3.5*cm, 2.5*cm, 3.5*cm, 5*cm], rowHeights=[24]+[22]*3)
        rt.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), Cores.CINZA_700), ('GRID', (0, 0), (-1, -1), 0.5, Cores.CINZA_300), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        el.append(rt)
        el.append(Spacer(1, 0.5*cm))
        if ind.get('receita_total', 0) > 0:
            el.append(Paragraph("6.3 Composição da Receita", self.styles['SubtituloSecao']))
            dados = [('Lucro', max(ind.get('lucro_liquido', 0), 0)), ('Custos', ind.get('custos_total', 0) or 0),
                     ('Despesas', (ind.get('despesas_operacionais', 0) or 0) + (ind.get('folha_total', 0) or 0)),
                     ('Impostos', ind.get('impostos_total', 0) or 0)]
            el.append(criar_grafico_pizza(dados, 300, 160))
        return el
    
    def _criar_analise_fiscal(self, ind):
        el = [Paragraph("7. ANÁLISE FISCAL / TRIBUTÁRIA", self.styles['TituloSecao'])]
        sep = Table([['']], colWidths=[self.content_width], rowHeights=[2])
        sep.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), Cores.AZUL_ESCURO)]))
        el.append(sep)
        el.append(Spacer(1, 0.4*cm))
        el.append(Paragraph(f"Tributos recolhidos no período ({ind.get('meses_analisados', 0)} meses).", self.styles['Corpo']))
        el.append(Spacer(1, 0.4*cm))
        rec = ind.get('receita_bruta', 0) or 1
        imp = [[self._p('TRIBUTO', 'CelulaHeader'), self._p('VALOR (R$)', 'CelulaHeader'), self._p('% RECEITA', 'CelulaHeader')]]
        for nome, val in [('ISS', ind.get('iss', 0)), ('PIS', ind.get('pis', 0)), ('COFINS', ind.get('cofins', 0)),
                          ('IRPJ', ind.get('irpj', 0)), ('CSLL', ind.get('csll', 0))]:
            if val and val > 0:
                imp.append([self._p(nome), self._p(self._fmt_moeda(val), 'CelulaTabelaRight'), self._p(f"{(val/rec*100):.2f}%", 'CelulaTabelaCenter')])
        imp.append([self._p('<b>TOTAL</b>'), self._p(self._fmt_moeda(ind.get('impostos_total')), 'CelulaTabelaRight'), self._p(self._fmt_pct(ind.get('carga_tributaria')), 'CelulaTabelaCenter')])
        it = Table(imp, colWidths=[5*cm, 4*cm, 3*cm], rowHeights=[24]+[20]*(len(imp)-1))
        it.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), Cores.AZUL_ESCURO), ('BACKGROUND', (0, -1), (-1, -1), Cores.CINZA_100),
                                ('GRID', (0, 0), (-1, -1), 0.5, Cores.CINZA_300), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        el.append(it)
        el.append(Spacer(1, 0.5*cm))
        return el
    
    def _criar_evolucao(self, ind):
        el = [Paragraph("8. EVOLUÇÃO MENSAL", self.styles['TituloSecao'])]
        sep = Table([['']], colWidths=[self.content_width], rowHeights=[2])
        sep.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), Cores.AZUL_ESCURO)]))
        el.append(sep)
        el.append(Spacer(1, 0.4*cm))
        if ind.get('dados_evolucao'):
            d = ind['dados_evolucao'][-6:]
            hdr = [self._p('INDICADOR', 'CelulaHeader')] + [self._p(x['periodo'][:5], 'CelulaHeader') for x in d]
            rec = [self._p('Receita')] + [self._p(self._fmt_moeda(x['receita']), 'CelulaTabelaCenter') for x in d]
            luc = [self._p('Lucro')] + [self._p(self._fmt_moeda(x['lucro']), 'CelulaTabelaCenter') for x in d]
            mg = [self._p('Margem')] + [self._p(self._fmt_pct(x['margem']), 'CelulaTabelaCenter') for x in d]
            cw = (self.content_width - 3*cm) / len(d)
            evol = Table([hdr, rec, luc, mg], colWidths=[3*cm]+[cw]*len(d), rowHeights=[24]+[22]*3)
            evol.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), Cores.AZUL_ESCURO), ('BACKGROUND', (0, 1), (0, -1), Cores.CINZA_100),
                                      ('GRID', (0, 0), (-1, -1), 0.5, Cores.CINZA_300), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
            el.append(evol)
            el.append(Spacer(1, 0.5*cm))
        if ind.get('dados_lucro'):
            el.append(Paragraph("8.1 Evolução do Lucro Líquido", self.styles['SubtituloSecao']))
            el.append(criar_grafico_barras(ind['dados_lucro'], self.content_width - 20, 140))
        el.append(Spacer(1, 0.5*cm))
        el.append(Paragraph("8.2 Variações no Período", self.styles['SubtituloSecao']))
        vr, vl = ind.get('variacao_receita', 0), ind.get('variacao_lucro', 0)
        var = [
            [self._p('INDICADOR', 'CelulaHeader'), self._p('VARIAÇÃO', 'CelulaHeader'), self._p('TENDÊNCIA', 'CelulaHeader')],
            [self._p('Receita'), self._p(self._fmt_pct(vr, sinal=True), 'CelulaTabelaCenter'), self._p('↑ Crescimento' if vr > 0 else '↓ Queda' if vr < 0 else '→ Estável', 'CelulaTabelaCenter')],
            [self._p('Lucro'), self._p(self._fmt_pct(vl, sinal=True), 'CelulaTabelaCenter'), self._p('↑ Melhora' if vl > 0 else '↓ Piora' if vl < 0 else '→ Estável', 'CelulaTabelaCenter')]]
        vt = Table(var, colWidths=[5*cm, 4*cm, 5*cm], rowHeights=[24, 22, 22])
        vt.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), Cores.CINZA_700), ('GRID', (0, 0), (-1, -1), 0.5, Cores.CINZA_300), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        el.append(vt)
        return el
    
    def _criar_conclusoes(self, ind, insights):
        el = [Paragraph("9. CONCLUSÕES E RECOMENDAÇÕES", self.styles['TituloSecao'])]
        sep = Table([['']], colWidths=[self.content_width], rowHeights=[2])
        sep.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), Cores.AZUL_ESCURO)]))
        el.append(sep)
        el.append(Spacer(1, 0.4*cm))
        s = ind.get('score', 0)
        if s >= 70: diag = "A empresa apresenta <b>boa saúde financeira</b>, com indicadores equilibrados."
        elif s >= 40: diag = "A empresa requer <b>atenção em alguns pontos</b> identificados nesta análise."
        else: diag = "A empresa está em <b>situação crítica</b> e necessita de ações urgentes."
        el.append(Paragraph("9.1 Diagnóstico Geral", self.styles['SubtituloSecao']))
        el.append(Paragraph(diag, self.styles['Corpo']))
        el.append(Spacer(1, 0.4*cm))
        pos = [i for i in insights if i['tipo'] == 'positivo']
        crit = [i for i in insights if i['tipo'] == 'critico']
        if pos:
            el.append(Paragraph("9.2 Pontos Fortes", self.styles['SubtituloSecao']))
            for i in pos: el.append(Paragraph(f"✅ <b>{i['titulo']}</b>: {i['texto']}", self.styles['Corpo']))
        if crit:
            el.append(Paragraph("9.3 Pontos de Atenção", self.styles['SubtituloSecao']))
            for i in crit: el.append(Paragraph(f"⚠️ <b>{i['titulo']}</b>: {i['texto']}", self.styles['Corpo']))
        el.append(Paragraph("9.4 Recomendações", self.styles['SubtituloSecao']))
        recs = self._gerar_recomendacoes(ind)
        for i, r in enumerate(recs, 1): el.append(Paragraph(f"<b>{i}.</b> {r}", self.styles['Corpo']))
        el.append(Spacer(1, 1*cm))
        sep2 = Table([['']], colWidths=[self.content_width], rowHeights=[1])
        sep2.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), Cores.CINZA_300)]))
        el.append(sep2)
        el.append(Spacer(1, 0.3*cm))
        el.append(Paragraph("Este relatório tem caráter informativo e não substitui análise de profissional habilitado.", self.styles['Rodape']))
        return el
    
    def _gerar_recomendacoes(self, ind):
        r = []
        if ind.get('liquidez_corrente', 0) < 1: r.append("Buscar aumento do capital de giro através de renegociação de prazos ou aporte de capital.")
        if ind.get('patrimonio_liquido', 0) < 0: r.append("Avaliar aporte de capital dos sócios para recompor o patrimônio líquido.")
        if ind.get('endividamento_geral', 0) > 70: r.append("Priorizar redução do endividamento, evitando novos empréstimos.")
        if ind.get('margem_liquida', 0) < 5: r.append("Revisar estrutura de custos e política de precificação.")
        if ind.get('variacao_receita', 0) < -5: r.append("Investigar causas da queda de receita e desenvolver estratégias de recuperação.")
        if ind.get('capital_giro', 0) < 0: r.append("URGENTE: Recompor capital de giro através de alongamento de dívidas.")
        if ind.get('carga_tributaria', 0) > 25: r.append("Avaliar planejamento tributário e regime de tributação.")
        if not r: r = ["Manter as boas práticas de gestão financeira.", "Continuar monitorando indicadores mensalmente.",
                       "Avaliar oportunidades de crescimento sustentável.", "Manter reserva de caixa para imprevistos."]
        return r

def gerar_pdf(empresa, dados_mensais, analise=None, config=None, alertas=None):
    return PDFGeneratorPro(config).gerar_relatorio(empresa, dados_mensais, analise, alertas, config)
