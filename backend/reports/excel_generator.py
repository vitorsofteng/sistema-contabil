#!/usr/bin/env python3
"""Gerador Excel Profissional — Kontabil. Usa dados REAIS da análise."""

import io, statistics
from datetime import datetime
from typing import Dict, List, Optional

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
    from openpyxl.chart import LineChart, BarChart, PieChart, Reference
    from openpyxl.utils import get_column_letter
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


class ExcelGenerator:
    def __init__(self, config=None):
        if not EXCEL_AVAILABLE: raise ImportError("openpyxl não instalado")
        self.config = config or {}
        self.wb = Workbook()
        self._styles()

    def _styles(self):
        cor = self.config.get('cor_primaria', '#1A3C6E').replace('#', '')
        self.cor = cor
        self.tf = Font(name='Calibri', size=16, bold=True, color=cor)
        self.sf = Font(name='Calibri', size=12, bold=True, color='374151')
        self.hf = Font(name='Calibri', size=10, bold=True, color='FFFFFF')
        self.hfl = PatternFill(start_color=cor, end_color=cor, fill_type='solid')
        self.hfl2 = PatternFill(start_color='374151', end_color='374151', fill_type='solid')
        self.nf = Font(name='Calibri', size=10)
        self.bf = Font(name='Calibri', size=10, bold=True)
        self.smf = Font(name='Calibri', size=9, color='6B7280')
        self.alt = PatternFill(start_color='F3F4F6', end_color='F3F4F6', fill_type='solid')
        self.gf = PatternFill(start_color='D1FAE5', end_color='D1FAE5', fill_type='solid')
        self.yf = PatternFill(start_color='FEF3C7', end_color='FEF3C7', fill_type='solid')
        self.rf = PatternFill(start_color='FEE2E2', end_color='FEE2E2', fill_type='solid')
        self.bf2 = PatternFill(start_color='DBEAFE', end_color='DBEAFE', fill_type='solid')
        thin = Side(style='thin', color='D1D5DB')
        self.brd = Border(left=thin, right=thin, top=thin, bottom=thin)
        self.ca = Alignment(horizontal='center', vertical='center', wrap_text=True)
        self.ra = Alignment(horizontal='right', vertical='center')
        self.la = Alignment(horizontal='left', vertical='center', wrap_text=True)
        self.C = 'R$ #,##0.00'; self.P = '0.0%'; self.N = '#,##0.00'

    def _sfill(self, s):
        s = (s or '').lower()
        if any(w in s for w in ['excelente','saudavel','saudável','baixo','positiv','mínimo','minimo']): return self.gf
        if any(w in s for w in ['bom','adequado','moderado','estável','estavel']): return self.bf2
        if any(w in s for w in ['regular','atenção','atencao','elevado','alto']): return self.yf
        if any(w in s for w in ['crítico','critico','prejuízo','negativ','queda']): return self.rf
        return self.alt

    def _hrow(self, ws, r, hdrs, sc=2):
        for i, h in enumerate(hdrs):
            c = ws.cell(row=r, column=sc+i, value=h)
            c.font = self.hf; c.fill = self.hfl; c.border = self.brd; c.alignment = self.ca
        return r + 1

    def _drow(self, ws, r, vals, fmts=None, bold=False, fill=None, sc=2):
        fmts = fmts or []
        for i, v in enumerate(vals):
            c = ws.cell(row=r, column=sc+i, value=v)
            c.font = self.bf if bold else self.nf; c.border = self.brd
            if fill: c.fill = fill
            if i < len(fmts) and fmts[i]: c.number_format = fmts[i]
            c.alignment = self.la if i == 0 else self.ra
        return r + 1

    def _kv(self, ws, r, label, val, fmt=None, fill=None, sc=2):
        ws.cell(row=r, column=sc, value=label).font = self.nf
        ws.cell(row=r, column=sc).border = self.brd
        c = ws.cell(row=r, column=sc+1, value=val)
        c.border = self.brd; c.alignment = self.ra
        if fmt: c.number_format = fmt
        if fill: c.fill = fill
        return r + 1

    # === EXTRAÇÃO DE DADOS ===
    def _resultado(self, analise):
        if not analise: return {}
        r = analise.get('resultado_completo', analise.get('resultado', {}))
        return r if isinstance(r, dict) else {}

    def _calc_indicadores(self, dados):
        """Calcula indicadores dos dados brutos do banco."""
        if not dados: return {}
        dados = sorted(dados, key=lambda x: (x.get('ano', 0), x.get('mes', 0)))
        u = dados[-1]; n = len(dados)
        def s(c, a=None): return sum(float(d.get(c, 0) or 0) + (float(d.get(a, 0) or 0) if a and not d.get(c) else 0) for d in dados)
        rec = s('receita', 'receita_bruta'); cus = s('custos', 'custos_total')
        des = s('despesas', 'despesas_operacionais'); imp = s('impostos', 'deducoes_receita')
        fol = s('folha'); lb = rec - cus
        ll = s('lucro_liquido') or (rec - cus - des - imp - fol)
        ac = float(u.get('ativo_circulante', 0) or 0); pc = float(u.get('passivo_circulante', 0) or 0)
        pnc = float(u.get('passivo_nao_circulante', 0) or 0)
        at = float(u.get('ativo_total', 0) or 0) or ac
        pl = float(u.get('patrimonio_liquido', 0) or 0)
        disp = float(u.get('disponivel', 0) or u.get('caixa', 0) or 0)
        cli = float(u.get('clientes', 0) or 0); est = float(u.get('estoques', 0) or 0)
        rm = rec / n if n else 0
        ind = {
            'receita_total': rec, 'receita_mensal_media': rm, 'custos_total': cus,
            'lucro_bruto': lb, 'despesas_total': des, 'impostos_total': imp,
            'folha_total': fol, 'lucro_liquido': ll,
            'margem_bruta': (lb / rec * 100) if rec else 0,
            'margem_liquida': (ll / rec * 100) if rec else 0,
            'margem_operacional': ((rec - cus - des) / rec * 100) if rec else 0,
            'liquidez_corrente': ac / pc if pc else 0,
            'liquidez_seca': (ac - est) / pc if pc else 0,
            'liquidez_imediata': disp / pc if pc else 0,
            'roe': (ll / pl * 100) if pl else 0, 'roa': (ll / at * 100) if at else 0,
            'giro_ativo': rec / at if at else 0,
            'endividamento_geral': ((pc + pnc) / at * 100) if at else 0,
            'composicao_endividamento': (pc / (pc + pnc) * 100) if (pc + pnc) else 0,
            'pmr': (cli / rm * 30) if rm else 0,
            'carga_tributaria': (imp / rec * 100) if rec else 0,
            'capital_giro': ac - pc,
            'ativo_total': at, 'ativo_circulante': ac, 'passivo_circulante': pc,
            'passivo_nao_circulante': pnc, 'patrimonio_liquido': pl,
            'disponivel': disp, 'estoques': est, 'clientes': cli,
            'meses_analisados': n,
        }
        if n >= 3:
            recs = [float(d.get('receita', 0) or d.get('receita_bruta', 0) or 0) for d in dados]
            p1 = statistics.mean(recs[:n // 2]) if recs[:n // 2] else 0
            p2 = statistics.mean(recs[n // 2:]) if recs[n // 2:] else 0
            ind['variacao_receita'] = ((p2 - p1) / p1 * 100) if p1 else 0
        else:
            ind['variacao_receita'] = 0
        return ind

    # === MAIN ===
    def gerar_relatorio(self, empresa, dados_mensais, analise=None, alertas=None, config=None):
        self.config = config or self.config; self.wb = Workbook(); self._styles()
        self.wb.remove(self.wb.active)
        res = self._resultado(analise)
        ind = self._calc_indicadores(dados_mensais)
        # Merge com dados do resultado se disponíveis
        if res.get('faturamento_total'):
            ind['receita_total'] = res['faturamento_total']
            ind['receita_mensal_media'] = res.get('faturamento_medio', ind.get('receita_mensal_media', 0))
        if res.get('lucro_total'): ind['lucro_liquido'] = res['lucro_total']
        if res.get('margem_media'): ind['margem_liquida'] = res['margem_media']

        score = res.get('score', 0) if isinstance(res.get('score'), (int, float)) else (analise or {}).get('score', 0)
        status = res.get('status', '') or (analise or {}).get('status', '')
        sd = res.get('score_detalhado', {})
        tend = res.get('tendencia', {})
        caixa = res.get('risco_caixa', {})
        prob = res.get('probabilidades', {})
        prev = res.get('previsoes', [])
        insights = res.get('insights', [])
        rec_princ = res.get('recomendacao_principal', '')
        meses = res.get('meses_analisados', ind.get('meses_analisados', 0))

        slides = [
            (self._aba_resumo, (empresa, ind, score, status, sd, tend, caixa, meses, alertas, rec_princ)),
            (self._aba_score, (score, status, sd, tend, caixa, prob)) if score else None,
            (self._aba_dre, (empresa, dados_mensais, ind)),
            (self._aba_indicadores, (ind,)),
            (self._aba_balanco, (ind,)),
            (self._aba_evolucao, (dados_mensais,)),
            (self._aba_tendencia, (tend, prev)),
            (self._aba_riscos, (prob, caixa)),
            (self._aba_alertas, (alertas, rec_princ, tend, caixa)),
        ]
        for fn, args in [s for s in slides if s]:
            try: fn(*args)
            except Exception as e:
                import logging; logging.getLogger(__name__).error(f"Erro {fn.__name__}: {e}")
                try:
                    ws = self.wb.create_sheet(fn.__name__.replace('_aba_','').title())
                    ws['B2'] = f"Erro: {str(e)[:100]}"
                except: pass
        buf = io.BytesIO(); self.wb.save(buf); buf.seek(0); return buf.getvalue()

    # === ABA 1: RESUMO ===
    def _aba_resumo(self, empresa, ind, score, status, sd, tend, caixa, meses, alertas, rec_princ):
        ws = self.wb.create_sheet("Resumo Executivo", 0)
        ws.sheet_properties.tabColor = self.cor
        for c, w in {'A':3,'B':32,'C':22,'D':22,'E':22,'F':22}.items(): ws.column_dimensions[c].width = w
        r = 2; nome = self.config.get('nome_escritorio', 'Kontabil')
        ws.merge_cells(f'B{r}:F{r}'); ws[f'B{r}'] = nome; ws[f'B{r}'].font = self.tf; r += 1
        ws.merge_cells(f'B{r}:F{r}'); ws[f'B{r}'] = "DIAGNÓSTICO FINANCEIRO"
        ws[f'B{r}'].font = Font(name='Calibri', size=12, color='6B7280'); r += 2
        ws[f'B{r}'] = empresa.get('razao_social', ''); ws[f'B{r}'].font = Font(name='Calibri', size=13, bold=True); r += 1
        info = [f"CNPJ: {empresa.get('cnpj', '-')}"]
        if empresa.get('setor'): info.append(f"Setor: {empresa['setor']}")
        if empresa.get('regime_tributario'): info.append(f"Regime: {empresa['regime_tributario']}")
        ws[f'B{r}'] = " | ".join(info); ws[f'B{r}'].font = self.smf; r += 1
        ws[f'B{r}'] = f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')} | {meses} meses analisados"; ws[f'B{r}'].font = self.smf; r += 2

        # Score + dimensões
        if score:
            ws[f'B{r}'] = "SCORE DE SAÚDE FINANCEIRA"; ws[f'B{r}'].font = self.bf; r += 1
            ws[f'B{r}'] = score; ws[f'B{r}'].font = Font(name='Calibri', size=36, bold=True, color=self.cor)
            lbl = 'Saudável' if status == 'saudavel' else 'Atenção' if status == 'atencao' else 'Crítico' if status == 'critico' else status
            ws[f'C{r}'] = f"/100 — {lbl}"; ws[f'C{r}'].font = Font(name='Calibri', size=14, bold=True)
            ws[f'C{r}'].fill = self._sfill(status)
            if sd:
                for j, (lbl2, key) in enumerate([('Tendência','tendencia'),('Margem','margem'),('Caixa','caixa'),('Estabilidade','estabilidade')]):
                    ws.cell(row=r, column=4+j, value=lbl2).font = self.smf
                    ws.cell(row=r+1, column=4+j, value=sd.get(key, '-')).font = self.bf
            r += 3
        else:
            ws[f'B{r}'] = "Análise completa disponível a partir de 6 meses de dados importados."
            ws[f'B{r}'].font = Font(name='Calibri', size=10, italic=True, color='6B7280'); r += 2

        # KPIs
        ws[f'B{r}'] = "RESUMO FINANCEIRO"; ws[f'B{r}'].font = self.bf; r += 1
        for lbl, val, fmt in [
            ('Faturamento Total', ind.get('receita_total', 0), self.C),
            ('Receita Mensal Média', ind.get('receita_mensal_media', 0), self.C),
            ('Lucro Bruto', ind.get('lucro_bruto', 0), self.C),
            ('Lucro Líquido', ind.get('lucro_liquido', 0), self.C),
            ('Margem Bruta', (ind.get('margem_bruta', 0) or 0) / 100, self.P),
            ('Margem Líquida', (ind.get('margem_liquida', 0) or 0) / 100, self.P),
            ('Liquidez Corrente', ind.get('liquidez_corrente', 0), '0.00'),
            ('Endividamento Geral', (ind.get('endividamento_geral', 0) or 0) / 100, self.P),
            ('Capital de Giro', ind.get('capital_giro', 0), self.C),
            ('Variação Receita', (ind.get('variacao_receita', 0) or 0) / 100, self.P),
        ]:
            r = self._kv(ws, r, lbl, val, fmt)
        r += 1

        # Tendência rápida
        if tend:
            ws[f'B{r}'] = "TENDÊNCIA"; ws[f'B{r}'].font = self.bf; r += 1
            r = self._kv(ws, r, 'Direção', tend.get('tendencia', tend.get('direcao', '-')))
            r = self._kv(ws, r, 'Taxa Mensal', f"{tend.get('taxa_mensal', 0):+.2f}%")
            r = self._kv(ws, r, 'Taxa Anual Projetada', f"{tend.get('taxa_anual_projetada', 0):+.2f}%")
            r += 1

        # Caixa rápida
        if caixa:
            ws[f'B{r}'] = "RISCO DE CAIXA"; ws[f'B{r}'].font = self.bf; r += 1
            nivel = caixa.get('nivel', '-')
            r = self._kv(ws, r, 'Nível de Risco', nivel, fill=self._sfill(nivel))
            r = self._kv(ws, r, 'Saldo Atual', caixa.get('saldo_atual', 0), self.C)
            r = self._kv(ws, r, 'Runway (cenário base)', f"{caixa.get('runway_p50', '-')} meses")
            r += 1

        # (insights removidos - dados apenas)

    # === ABA 2: SCORE DETALHADO ===
    def _aba_score(self, score, status, sd, tend, caixa, prob):
        ws = self.wb.create_sheet("Score Detalhado")
        ws.sheet_properties.tabColor = '0EA5E9'
        for c, w in {'A':3,'B':30,'C':18,'D':18,'E':38}.items(): ws.column_dimensions[c].width = w
        r = 2; ws[f'B{r}'] = "SCORE DE SAÚDE FINANCEIRA"; ws[f'B{r}'].font = self.tf; r += 2

        # Score principal
        r = self._hrow(ws, r, ['Componente', 'Pontuação', 'Peso', 'Descrição'])
        lbl = 'Saudável' if status == 'saudavel' else 'Atenção' if status == 'atencao' else 'Crítico' if status == 'critico' else status
        r = self._drow(ws, r, ['SCORE FINAL', score, '100%', lbl], bold=True, fill=self.alt)
        if sd:
            formula = sd.get('formula', '')
            for nm, key in [('Tendência','tendencia'),('Margem','margem'),('Caixa','caixa'),('Estabilidade','estabilidade'),('Anomalias','anomalias')]:
                val = sd.get(key, 0)
                r = self._drow(ws, r, [nm, val, '', ''], [None, '0.0', None, None])
            if formula:
                r += 1; ws[f'B{r}'] = f"Fórmula: {formula}"; ws[f'B{r}'].font = self.smf; r += 1
        r += 1

        # Tendência detalhada
        if tend:
            ws[f'B{r}'] = "ANÁLISE DE TENDÊNCIA"; ws[f'B{r}'].font = self.sf; r += 1
            for lbl, val in [
                ('Classificação', tend.get('tendencia', '-')),
                ('Direção', tend.get('direcao', '-')),
                ('Taxa Mensal', f"{tend.get('taxa_mensal', 0):+.2f}%"),
                ('Taxa Anual Projetada', f"{tend.get('taxa_anual_projetada', 0):+.2f}%"),
                ('R² (qualidade modelo)', f"{tend.get('r_squared', 0):.3f}"),
                ('Sazonalidade Detectada', 'Sim' if tend.get('tem_sazonalidade') else 'Não'),
                ('Erro Médio (MAPE)', f"{tend.get('mape', 0):.1f}%"),
            ]:
                r = self._kv(ws, r, lbl, val)
            desc = tend.get('descricao', '')
            if desc: ws.merge_cells(f'B{r}:E{r}'); ws[f'B{r}'] = desc; ws[f'B{r}'].font = self.smf; r += 1
            rec2 = tend.get('recomendacao', '')
            if rec2: ws.merge_cells(f'B{r}:E{r}'); ws[f'B{r}'] = f"→ {rec2}"; ws[f'B{r}'].font = Font(name='Calibri', size=9, bold=True, color='059669'); r += 1
            r += 1

        # Risco de caixa
        if caixa:
            ws[f'B{r}'] = "RISCO DE CAIXA"; ws[f'B{r}'].font = self.sf; r += 1
            nivel = caixa.get('nivel', '-')
            for lbl, val, fl in [
                ('Nível de Risco', nivel, self._sfill(nivel)),
                ('Saldo Atual', caixa.get('saldo_atual', 0), None),
                ('Burn Rate Médio', caixa.get('burn_rate_medio', 0), None),
                ('Runway Pessimista', f"{caixa.get('runway_p10', '-')} meses", None),
                ('Runway Base', f"{caixa.get('runway_p50', '-')} meses", None),
                ('Runway Otimista', f"{caixa.get('runway_p90', '-')} meses", None),
                ('Prob. Caixa Negativo 3m', f"{(caixa.get('prob_caixa_negativo_3m', 0) or 0)*100:.1f}%", None),
                ('Prob. Caixa Negativo 6m', f"{(caixa.get('prob_caixa_negativo_6m', 0) or 0)*100:.1f}%", None),
            ]:
                fmt = self.C if isinstance(val, (int, float)) and 'Saldo' in lbl or 'Burn' in lbl else None
                r = self._kv(ws, r, lbl, val, fmt, fl)
            desc = caixa.get('descricao', '')
            if desc: ws.merge_cells(f'B{r}:E{r}'); ws[f'B{r}'] = desc; ws[f'B{r}'].font = self.smf; r += 1

        # Probabilidades
        if prob:
            r += 1; ws[f'B{r}'] = "ANÁLISE DE PROBABILIDADES"; ws[f'B{r}'].font = self.sf; r += 1
            for lbl, pkey, rkey in [
                ('Risco de Prejuízo', 'prob_prejuizo', 'risco_prejuizo'),
                ('Risco de Quebra', 'prob_quebra', 'risco_quebra'),
                ('Risco Imposto Inesperado', 'prob_imposto_inesperado', 'risco_imposto'),
            ]:
                pv = prob.get(pkey, 0); rv = prob.get(rkey, '-')
                r = self._drow(ws, r, [lbl, f"{pv}%", rv, ''], fill=self._sfill(rv))
            r += 1
            fp = prob.get('fatores_positivos', [])
            fr = prob.get('fatores_risco', [])
            if fp:
                ws[f'B{r}'] = "Fatores Positivos:"; ws[f'B{r}'].font = self.bf; r += 1
                for f in fp[:5]:
                    ws[f'B{r}'] = f"  ✓ {f}"; ws[f'B{r}'].font = Font(name='Calibri', size=9, color='059669'); r += 1
            if fr:
                ws[f'B{r}'] = "Fatores de Risco:"; ws[f'B{r}'].font = self.bf; r += 1
                for f in fr[:5]:
                    ws[f'B{r}'] = f"  ⚠ {f}"; ws[f'B{r}'].font = Font(name='Calibri', size=9, color='DC2626'); r += 1

    # === ABA 3: DRE ===
    def _aba_dre(self, empresa, dados, ind):
        ws = self.wb.create_sheet("DRE")
        ws.sheet_properties.tabColor = '059669'
        for c, w in {'A':3,'B':30,'C':20,'D':14}.items(): ws.column_dimensions[c].width = w
        r = 2; ws[f'B{r}'] = "DEMONSTRAÇÃO DO RESULTADO"; ws[f'B{r}'].font = self.tf; r += 2
        rt = ind.get('receita_total', 1) or 1
        r = self._hrow(ws, r, ['Conta', 'Valor Acumulado', '% Receita'])
        for desc, v, p, d in [
            ('RECEITA BRUTA', ind.get('receita_total', 0), 1, True),
            ('  (-) Impostos s/ Vendas', -ind.get('impostos_total', 0), -(ind.get('carga_tributaria', 0) or 0)/100, False),
            ('(=) RECEITA LÍQUIDA', rt - ind.get('impostos_total', 0), (rt - ind.get('impostos_total', 0))/rt, True),
            ('  (-) Custos (CMV/CSP)', -ind.get('custos_total', 0), -ind.get('custos_total', 0)/rt, False),
            ('(=) LUCRO BRUTO', ind.get('lucro_bruto', 0), (ind.get('margem_bruta', 0) or 0)/100, True),
            ('  (-) Despesas Operacionais', -ind.get('despesas_total', 0), -ind.get('despesas_total', 0)/rt, False),
            ('  (-) Folha de Pagamento', -ind.get('folha_total', 0), -ind.get('folha_total', 0)/rt, False),
            ('(=) LUCRO LÍQUIDO', ind.get('lucro_liquido', 0), (ind.get('margem_liquida', 0) or 0)/100, True),
        ]:
            r = self._drow(ws, r, [desc, v, p], [None, self.C, self.P], bold=d, fill=self.alt if d else None)

        # Mensal detalhado
        if dados and len(dados) >= 2:
            r += 2; ws[f'B{r}'] = "EVOLUÇÃO MENSAL"; ws[f'B{r}'].font = self.sf; r += 1
            ds = sorted(dados, key=lambda x: (x.get('ano', 0), x.get('mes', 0)))[-12:]
            hdrs = ['Conta'] + [f"{d.get('mes',0):02d}/{d.get('ano',0)}" for d in ds]
            for i, h in enumerate(hdrs):
                ws.column_dimensions[get_column_letter(2+i)].width = 14 if i > 0 else 30
                c = ws.cell(row=r, column=2+i, value=h); c.font = self.hf; c.fill = self.hfl; c.border = self.brd
            r += 1
            for nm, fn in [('Receita', lambda d: float(d.get('receita',0) or d.get('receita_bruta',0) or 0)),
                           ('Custos', lambda d: float(d.get('custos',0) or d.get('custos_total',0) or 0)),
                           ('Despesas', lambda d: float(d.get('despesas',0) or d.get('despesas_operacionais',0) or 0)),
                           ('Impostos', lambda d: float(d.get('impostos',0) or d.get('deducoes_receita',0) or 0)),
                           ('Folha', lambda d: float(d.get('folha',0) or 0)),
                           ('Caixa', lambda d: float(d.get('caixa',0) or 0)),
                           ('Lucro Líq.', lambda d: float(d.get('lucro_liquido',0) or 0) or (float(d.get('receita',0) or 0)-float(d.get('custos',0) or 0)-float(d.get('despesas',0) or 0)-float(d.get('impostos',0) or 0)-float(d.get('folha',0) or 0)))]:
                ws.cell(row=r, column=2, value=nm).font = self.bf if 'Lucro' in nm else self.nf
                ws.cell(row=r, column=2).border = self.brd
                for j, d in enumerate(ds):
                    c = ws.cell(row=r, column=3+j, value=fn(d)); c.border = self.brd; c.number_format = self.C; c.alignment = self.ra
                r += 1

    # === ABA 4: INDICADORES ===
    def _aba_indicadores(self, ind):
        ws = self.wb.create_sheet("Indicadores")
        ws.sheet_properties.tabColor = '2D6BB4'
        for c, w in {'A':3,'B':28,'C':14,'D':14,'E':38}.items(): ws.column_dimensions[c].width = w
        r = 2; ws[f'B{r}'] = "INDICADORES FINANCEIROS"; ws[f'B{r}'].font = self.tf; r += 2

        def sec(title, items):
            nonlocal r
            r = self._hrow(ws, r, [title, 'Valor', 'Status', 'Referência'])
            for nm, v, fmt, st, ref in items:
                ws.cell(row=r, column=2, value=nm).font = self.nf; ws.cell(row=r, column=2).border = self.brd
                c = ws.cell(row=r, column=3, value=v); c.number_format = fmt; c.border = self.brd; c.alignment = self.ca
                cs = ws.cell(row=r, column=4, value=st); cs.border = self.brd; cs.alignment = self.ca; cs.fill = self._sfill(st); cs.font = Font(name='Calibri', size=9, bold=True)
                cr = ws.cell(row=r, column=5, value=ref); cr.border = self.brd; cr.font = self.smf
                r += 1
            r += 1

        mb=ind.get('margem_bruta',0);ml=ind.get('margem_liquida',0);mo=ind.get('margem_operacional',0)
        roe=ind.get('roe',0);roa=ind.get('roa',0);ga=ind.get('giro_ativo',0)
        sec("RENTABILIDADE",[
            ('Margem Bruta',mb/100,self.P,'Excelente' if mb>=50 else 'Bom' if mb>=35 else 'Adequado' if mb>=20 else 'Baixa','Lucro bruto / Receita'),
            ('Margem Operacional',mo/100,self.P,'Excelente' if mo>=25 else 'Bom' if mo>=15 else 'Adequado' if mo>=5 else 'Baixa','Eficiência operacional'),
            ('Margem Líquida',ml/100,self.P,'Excelente' if ml>=20 else 'Bom' if ml>=10 else 'Adequado' if ml>=0 else 'Prejuízo','Benchmark: 10-15% saudável'),
            ('ROE',roe/100,self.P,'Excelente' if roe>=25 else 'Bom' if roe>=15 else 'Moderado','Retorno sobre PL'),
            ('ROA',roa/100,self.P,'Excelente' if roa>=15 else 'Bom' if roa>=8 else 'Moderado','Retorno sobre ativos'),
            ('Giro do Ativo',ga,'0.00','Alto' if ga>=2 else 'Adequado' if ga>=1 else 'Baixo','Receita / Ativo'),])
        lc=ind.get('liquidez_corrente',0);ls=ind.get('liquidez_seca',0);li=ind.get('liquidez_imediata',0)
        sec("LIQUIDEZ",[
            ('Liquidez Corrente',lc,'0.00','Excelente' if lc>=2 else 'Bom' if lc>=1.5 else 'Adequado' if lc>=1 else 'Crítico','AC / PC — ideal > 1.5'),
            ('Liquidez Seca',ls,'0.00','Bom' if ls>=1 else 'Adequado' if ls>=0.7 else 'Baixa','(AC - Estoques) / PC'),
            ('Liquidez Imediata',li,'0.00','Alto' if li>=0.5 else 'Adequado' if li>=0.2 else 'Baixo','Caixa / PC'),
            ('Capital de Giro',ind.get('capital_giro',0),self.C,'Positivo' if ind.get('capital_giro',0)>0 else 'Negativo','AC - PC'),])
        eg=ind.get('endividamento_geral',0);ce=ind.get('composicao_endividamento',0);pmr=ind.get('pmr',0);ct=ind.get('carga_tributaria',0)
        sec("ENDIVIDAMENTO E EFICIÊNCIA",[
            ('Endividamento Geral',eg/100,self.P,'Baixo' if eg<=30 else 'Moderado' if eg<=50 else 'Elevado' if eg<=70 else 'Crítico','% ativo com terceiros'),
            ('Composição CP',ce/100,self.P,'Equilibrado' if ce<=50 else 'Concentrado CP','% dívida de curto prazo'),
            ('Prazo Médio Receb.',pmr,'0','Bom' if pmr<=30 else 'Adequado' if pmr<=45 else 'Elevado','Dias para receber'),
            ('Carga Tributária',ct/100,self.P,'Baixa' if ct<=10 else 'Moderada' if ct<=18 else 'Alta','Impostos / Receita'),])

    # === ABA 5: BALANÇO ===
    def _aba_balanco(self, ind):
        ws = self.wb.create_sheet("Balanço")
        ws.sheet_properties.tabColor = 'D97706'
        for c, w in {'A':3,'B':32,'C':20,'D':14}.items(): ws.column_dimensions[c].width = w
        r = 2; ws[f'B{r}'] = "ESTRUTURA PATRIMONIAL"; ws[f'B{r}'].font = self.tf; r += 2
        at = ind.get('ativo_total', 0) or 1
        if at <= 1:
            ws[f'B{r}'] = "Dados de balanço patrimonial não disponíveis para esta empresa."
            ws[f'B{r}'].font = self.smf; ws[f'B{r+1}'] = "Importe balancetes com dados de ativo/passivo para visualizar esta aba."
            ws[f'B{r+1}'].font = self.smf; return
        r = self._hrow(ws, r, ['Conta', 'Valor', '% Ativo'])
        for desc, v, d in [('ATIVO TOTAL', at, True),('  Ativo Circulante', ind.get('ativo_circulante',0), False),
            ('    Disponibilidades', ind.get('disponivel',0), False),('    Clientes', ind.get('clientes',0), False),
            ('    Estoques', ind.get('estoques',0), False),('  Ativo Não Circulante', max(0,at-ind.get('ativo_circulante',0)), False)]:
            r = self._drow(ws, r, [desc, v, v/at], [None, self.C, self.P], bold=d, fill=self.alt if d else None)
        r += 1; r = self._hrow(ws, r, ['Conta', 'Valor', '% Ativo'])
        for desc, v, d in [('PASSIVO + PL', at, True),('  Passivo Circulante', ind.get('passivo_circulante',0), False),
            ('  Passivo Não Circulante', ind.get('passivo_nao_circulante',0), False),
            ('  Patrimônio Líquido', ind.get('patrimonio_liquido',0), False)]:
            r = self._drow(ws, r, [desc, v, v/at], [None, self.C, self.P], bold=d, fill=self.alt if d else None)

    # === ABA 6: EVOLUÇÃO ===
    def _aba_evolucao(self, dados):
        if not dados or len(dados) < 2: return  # Skip - need 2+ months
        ws = self.wb.create_sheet("Evolução")
        ws.sheet_properties.tabColor = self.cor
        ws.column_dimensions['A'].width = 3
        r = 2; ws[f'B{r}'] = "ANÁLISE DE EVOLUÇÃO"; ws[f'B{r}'].font = self.tf; r += 2
        ds = sorted(dados, key=lambda x: (x.get('ano',0), x.get('mes',0)))[-12:]
        for i, h in enumerate(['Mês','Receita','Custos','Desp.+Folha','Lucro Líq.','Margem','Caixa']):
            ws.column_dimensions[get_column_letter(2+i)].width = 16
            c = ws.cell(row=r, column=2+i, value=h); c.font = self.hf; c.fill = self.hfl; c.border = self.brd
        r += 1; sr = r
        for d in ds:
            rec = float(d.get('receita',0) or d.get('receita_bruta',0) or 0)
            cus = float(d.get('custos',0) or 0); des = float(d.get('despesas',0) or 0) + float(d.get('folha',0) or 0)
            luc = float(d.get('lucro_liquido',0) or 0) or (rec - cus - des - float(d.get('impostos',0) or 0))
            mar = luc/rec if rec > 0 else 0; cxa = float(d.get('caixa',0) or 0)
            for i, (v, f) in enumerate(zip(
                [f"{d.get('mes',0):02d}/{d.get('ano',0)}", rec, cus, des, luc, mar, cxa],
                [None, self.C, self.C, self.C, self.C, self.P, self.C])):
                c = ws.cell(row=r, column=2+i, value=v); c.border = self.brd
                if f: c.number_format = f; c.alignment = self.ca if i == 0 else self.ra
            r += 1
        er = r - 1
        if er > sr:
            try:
                ch = LineChart(); ch.title = "Receita e Lucro"; ch.style = 10; ch.y_axis.numFmt = '#,##0'
                ch.add_data(Reference(ws, min_col=3, min_row=sr-1, max_col=6, max_row=er), titles_from_data=True)
                ch.set_categories(Reference(ws, min_col=2, min_row=sr, max_row=er)); ch.width = 22; ch.height = 12
                for i, clr in enumerate(['2D6BB4','DC2626','6B7280','059669']):
                    if i < len(ch.series): ch.series[i].graphicalProperties.line.solidFill = clr
                ws.add_chart(ch, f"I{sr-1}")
            except: pass

    # === ABA 7: TENDÊNCIA E PREVISÕES ===
    def _aba_tendencia(self, tend, prev):
        if not tend and not prev: return  # Skip tab entirely
        ws = self.wb.create_sheet("Tendência e Previsões")
        ws.sheet_properties.tabColor = '7C3AED'
        for c, w in {'A':3,'B':28,'C':22,'D':22,'E':22}.items(): ws.column_dimensions[c].width = w
        r = 2; ws[f'B{r}'] = "TENDÊNCIA E PREVISÕES"; ws[f'B{r}'].font = self.tf; r += 2

        ws[f'B{r}'] = "TENDÊNCIA ATUAL"; ws[f'B{r}'].font = self.sf; r += 1
        for lbl, val in [('Classificação', tend.get('tendencia','-')),('Taxa Mensal', f"{tend.get('taxa_mensal',0):+.2f}%"),
            ('Taxa Anual Projetada', f"{tend.get('taxa_anual_projetada',0):+.2f}%"),('R²', f"{tend.get('r_squared',0):.3f}"),
            ('MAPE', f"{tend.get('mape',0):.1f}%"),('Sazonalidade', 'Sim' if tend.get('tem_sazonalidade') else 'Não')]:
            r = self._kv(ws, r, lbl, val)
        desc = tend.get('descricao','')
        if desc: r += 1; ws.merge_cells(f'B{r}:E{r}'); ws[f'B{r}'] = desc; ws[f'B{r}'].font = self.smf; ws[f'B{r}'].alignment = Alignment(wrap_text=True); r += 1
        r += 1

        # Previsões
        if prev:
            ws[f'B{r}'] = "PREVISÕES DE FATURAMENTO"; ws[f'B{r}'].font = self.sf; r += 1
            r = self._hrow(ws, r, ['Horizonte', 'Previsto', 'Mínimo (IC 95%)', 'Máximo (IC 95%)'])
            for p in prev:
                r = self._drow(ws, r, [p.get('periodo',''), p.get('receita_prevista',0), p.get('receita_inferior',0), p.get('receita_superior',0)],
                    [None, self.C, self.C, self.C])
        else:
            # Previsões embutidas no tendencia
            for lbl, key in [('3 Meses','previsao_3m'),('6 Meses','previsao_6m'),('12 Meses','previsao_12m')]:
                pv = tend.get(key, {})
                if pv:
                    if not (r > 10): ws[f'B{r}'] = "PREVISÕES"; ws[f'B{r}'].font = self.sf; r += 1; r = self._hrow(ws, r, ['Horizonte','Previsto','Mínimo','Máximo'])
                    r = self._drow(ws, r, [lbl, pv.get('valor_previsto',0), pv.get('intervalo_inferior',0), pv.get('intervalo_superior',0)], [None,self.C,self.C,self.C])

    # === ABA 8: RISCOS ===
    def _aba_riscos(self, prob, caixa):
        if not prob and not caixa: return  # Skip tab entirely
        ws = self.wb.create_sheet("Análise de Riscos")
        ws.sheet_properties.tabColor = 'DC2626'
        for c, w in {'A':3,'B':30,'C':18,'D':18,'E':30}.items(): ws.column_dimensions[c].width = w
        r = 2; ws[f'B{r}'] = "ANÁLISE DE RISCOS"; ws[f'B{r}'].font = self.tf; r += 2

        if prob:
            r = self._hrow(ws, r, ['Tipo de Risco', 'Probabilidade', 'Nível', 'Observação'])
            for lbl, pk, rk in [('Risco de Prejuízo','prob_prejuizo','risco_prejuizo'),('Risco de Quebra','prob_quebra','risco_quebra'),
                ('Risco Imposto Inesperado','prob_imposto_inesperado','risco_imposto')]:
                pv = prob.get(pk,0); rv = prob.get(rk,'-')
                r = self._drow(ws, r, [lbl, f"{pv}%", rv, ''], fill=self._sfill(rv))
            r += 1
            sc = prob.get('score_confianca', 0)
            if sc: r = self._kv(ws, r, 'Confiança da Análise', f"{sc}%")
            r += 1
            for titulo, items, cor in [("FATORES POSITIVOS", prob.get('fatores_positivos',[]), '059669'),
                                        ("FATORES DE RISCO", prob.get('fatores_risco',[]), 'DC2626')]:
                if items:
                    ws[f'B{r}'] = titulo; ws[f'B{r}'].font = self.sf; r += 1
                    for f in items[:8]:
                        ws.merge_cells(f'B{r}:E{r}')
                        ws[f'B{r}'] = f"  {'✓' if 'POSITIV' in titulo else '⚠'} {f}"
                        ws[f'B{r}'].font = Font(name='Calibri', size=9, color=cor); r += 1
                    r += 1

        if caixa:
            ws[f'B{r}'] = "RISCO DE CAIXA DETALHADO"; ws[f'B{r}'].font = self.sf; r += 1
            for lbl, val in [('Nível', caixa.get('nivel','-')),('Saldo Atual', caixa.get('saldo_atual',0)),
                ('Burn Rate Médio', caixa.get('burn_rate_medio',0)),('Volatilidade Caixa', caixa.get('volatilidade_caixa',0)),
                ('Runway Pessimista', f"{caixa.get('runway_p10','-')} meses"),
                ('Runway Base', f"{caixa.get('runway_p50','-')} meses"),
                ('Runway Otimista', f"{caixa.get('runway_p90','-')} meses")]:
                fmt = self.C if isinstance(val, (int,float)) else None
                r = self._kv(ws, r, lbl, val, fmt)

    # === ABA 9: ALERTAS E RECOMENDAÇÕES ===
    def _aba_alertas(self, alertas, rec_princ, tend, caixa):
        ws = self.wb.create_sheet("Alertas e Recomendações")
        ws.sheet_properties.tabColor = 'DC2626'
        for c, w in {'A':3,'B':14,'C':60,'D':18}.items(): ws.column_dimensions[c].width = w
        r = 2; ws[f'B{r}'] = "ALERTAS E RECOMENDAÇÕES"; ws[f'B{r}'].font = self.tf; r += 2

        if alertas:
            r = self._hrow(ws, r, ['Severidade', 'Descrição', 'Período'])
            for a in (alertas or [])[:25]:
                sev = a.get('severidade','info')
                fl = self.rf if sev=='critico' else self.yf if sev=='atencao' else self.gf
                ws.cell(row=r,column=2,value=sev.upper()).font=Font(name='Calibri',size=9,bold=True)
                ws.cell(row=r,column=2).border=self.brd; ws.cell(row=r,column=2).fill=fl; ws.cell(row=r,column=2).alignment=self.ca
                ws.cell(row=r,column=3,value=a.get('titulo','')).border=self.brd; ws.cell(row=r,column=3).alignment=self.la
                ws.cell(row=r,column=4,value=a.get('periodo_referencia','')).border=self.brd; ws.cell(row=r,column=4).alignment=self.ca
                r += 1
        else: ws[f'B{r}'] = "Nenhum alerta registrado."; r += 1
        r += 2

        # Recomendações
        ws[f'B{r}'] = "RECOMENDAÇÕES"; ws[f'B{r}'].font = self.sf; r += 1
        recs = []
        if rec_princ: recs.append(f"⭐ {rec_princ}")
        if tend and tend.get('recomendacao'): recs.append(f"📈 Tendência: {tend['recomendacao']}")
        if caixa and caixa.get('recomendacao'): recs.append(f"💰 Caixa: {caixa['recomendacao']}")
        if not recs: recs = ["Manter monitoramento mensal dos indicadores", "Executar análise completa para recomendações detalhadas"]
        for rc in recs:
            ws.merge_cells(f'B{r}:D{r}'); ws[f'B{r}'] = rc; ws[f'B{r}'].font = self.nf
            ws[f'B{r}'].alignment = Alignment(wrap_text=True); r += 1

        # (insights removidos)


def gerar_excel(empresa, dados_mensais, analise=None, config=None, alertas=None):
    return ExcelGenerator(config).gerar_relatorio(empresa, dados_mensais, analise, alertas, config)
