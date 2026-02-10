#!/usr/bin/env python3
"""Gerador PowerPoint Profissional — Kontabil.
Usa dados REAIS do resultado_completo (ResultadoAnalisePro serializado).

resultado_completo keys:
  score: int, status: str, score_confianca: float,
  score_detalhado: {tendencia, margem, caixa, estabilidade, anomalias, formula}
  tendencia: {tendencia, direcao, taxa_mensal, taxa_anual_projetada, r_squared, previsao_3m/6m/12m, descricao, recomendacao}
  risco_caixa: {nivel, saldo_atual, burn_rate_medio, runway_p10/p50/p90, prob_caixa_negativo_3m/6m, descricao, recomendacao}
  probabilidades: {prob_prejuizo, prob_quebra, prob_imposto_inesperado, risco_*, fatores_risco, fatores_positivos, recomendacao}
  anomalias: {total, anomalias: [...]}
  faturamento_total, faturamento_medio, lucro_total, margem_media
  previsoes: [{periodo, receita_prevista, receita_inferior, receita_superior}]
  dados_mensais: [{periodo, receita, lucro, margem, caixa, custos_pct, impostos_pct}]
  insights: [str], recomendacao_principal: str
"""

import io, statistics
from datetime import datetime
from typing import Dict, List, Optional

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt, Emu
    from pptx.enum.text import PP_ALIGN
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.chart import XL_CHART_TYPE
    from pptx.dml.color import RGBColor
    from pptx.chart.data import CategoryChartData
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False


class PowerPointGenerator:
    def __init__(self, config=None):
        if not PPTX_AVAILABLE: raise ImportError("python-pptx não instalado")
        self.config = config or {}
        self.C = {
            'dark': RGBColor(0x0A, 0x24, 0x40), 'primary': RGBColor(0x15, 0x44, 0x7E),
            'accent': RGBColor(0x0E, 0xA5, 0xE9), 'success': RGBColor(0x05, 0x96, 0x69),
            'warning': RGBColor(0xD9, 0x77, 0x06), 'danger': RGBColor(0xDC, 0x26, 0x26),
            'light': RGBColor(0xF9, 0xFA, 0xFB), 'gray': RGBColor(0x6B, 0x72, 0x80),
            'white': RGBColor(0xFF, 0xFF, 0xFF), 'text': RGBColor(0x1F, 0x29, 0x37),
        }

    def _fm(self, v):
        try: v=float(v); return f"R$ {v:,.2f}".replace(',','X').replace('.',',').replace('X','.')
        except: return "R$ 0,00"

    def _fp(self, v, d=1):
        try: return f"{float(v):.{d}f}%"
        except: return "0.0%"

    def _tb(self, sl, l, t, w, h, txt, sz=12, bold=False, color=None, align=PP_ALIGN.LEFT):
        txBox = sl.shapes.add_textbox(l, t, w, h)
        tf = txBox.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]; p.text = str(txt); p.alignment = align
        p.font.size = Pt(sz); p.font.name = 'Calibri'
        if bold: p.font.bold = True
        if color: p.font.color.rgb = color
        return txBox

    def _shape(self, sl, l, t, w, h, fill=None, txt=None, sz=10, color=None, bold=False, align=PP_ALIGN.CENTER):
        sh = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
        sh.line.fill.background()
        if fill: sh.fill.solid(); sh.fill.fore_color.rgb = fill
        if txt:
            tf = sh.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]; p.text = str(txt); p.alignment = align
            p.font.size = Pt(sz); p.font.name = 'Calibri'
            if color: p.font.color.rgb = color
            if bold: p.font.bold = True
        return sh

    def _oval(self, sl, l, t, w, h, fill, txt=None, sz=14, color=None, bold=True):
        sh = sl.shapes.add_shape(MSO_SHAPE.OVAL, l, t, w, h)
        sh.line.fill.background(); sh.fill.solid(); sh.fill.fore_color.rgb = fill
        if txt:
            tf = sh.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]; p.text = str(txt); p.alignment = PP_ALIGN.CENTER
            p.font.size = Pt(sz); p.font.name = 'Calibri'; p.font.bold = bold
            if color: p.font.color.rgb = color
        return sh

    def _scor(self, s):
        s = (s or '').lower()
        if any(w in s for w in ['saudavel','saudável','excelente','baixo','positiv','mínimo','minimo']): return self.C['success']
        if any(w in s for w in ['bom','adequado','moderado','estável']): return self.C['accent']
        if any(w in s for w in ['atencao','atenção','regular','elevado','alto']): return self.C['warning']
        if any(w in s for w in ['critico','crítico','queda','prejuízo','negativ']): return self.C['danger']
        return self.C['gray']

    def _bar(self, sl, l, t, w, h, pct, fill):
        self._shape(sl, l, t, w, h, fill=RGBColor(0xE5,0xE7,0xEB))
        fw = max(Emu(int(w * min(1, max(0, pct/100)))), Emu(1))
        self._shape(sl, l, t, fw, h, fill=fill)

    def _insight_text(self, it):
        if isinstance(it, str): return it.lstrip('• ').strip()
        if isinstance(it, dict): return it.get('texto', it.get('descricao', str(it))).lstrip('• ').strip()
        return str(it)

    def _status_label(self, status):
        m = {'saudavel':'Saudável','atencao':'Atenção','critico':'Crítico'}
        return m.get(status, (status or '').title())

    def _res(self, analise):
        if not analise: return {}
        r = analise.get('resultado_completo', analise.get('resultado', {}))
        return r if isinstance(r, dict) else {}

    def _calc(self, dados):
        if not dados: return {}
        dados = sorted(dados, key=lambda x: (x.get('ano',0), x.get('mes',0)))
        u = dados[-1]; n = len(dados)
        def s(c, a=None): return sum(float(d.get(c,0) or 0) + (float(d.get(a,0) or 0) if a and not d.get(c) else 0) for d in dados)
        rec=s('receita','receita_bruta'); cus=s('custos','custos_total')
        des=s('despesas','despesas_operacionais'); imp=s('impostos','deducoes_receita')
        fol=s('folha'); lb=rec-cus
        ll=s('lucro_liquido') or (rec-cus-des-imp-fol)
        ac=float(u.get('ativo_circulante',0) or 0); pc=float(u.get('passivo_circulante',0) or 0)
        pnc=float(u.get('passivo_nao_circulante',0) or 0)
        at=float(u.get('ativo_total',0) or 0) or ac
        pl=float(u.get('patrimonio_liquido',0) or 0)
        disp=float(u.get('disponivel',0) or u.get('caixa',0) or 0)
        est=float(u.get('estoques',0) or 0); rm=rec/n if n else 0
        return {'receita_total':rec,'receita_mensal':rm,'custos_total':cus,'lucro_bruto':lb,
            'despesas_total':des,'impostos_total':imp,'folha_total':fol,'lucro_liquido':ll,
            'margem_bruta':(lb/rec*100) if rec else 0,'margem_liquida':(ll/rec*100) if rec else 0,
            'liquidez_corrente':ac/pc if pc else 0,'liquidez_seca':(ac-est)/pc if pc else 0,
            'liquidez_imediata':disp/pc if pc else 0,
            'endividamento_geral':((pc+pnc)/at*100) if at else 0,
            'capital_giro':ac-pc,'ativo_total':at,'patrimonio_liquido':pl,'meses':n}

    def gerar_apresentacao(self, empresa, dados_mensais, analise=None, alertas=None, config=None):
        self.config = config or self.config
        self.prs = Presentation()
        self.prs.slide_width = Inches(13.333); self.prs.slide_height = Inches(7.5)
        res = self._res(analise)
        calc = self._calc(dados_mensais)
        # Extract all data from resultado_completo
        score = res.get('score',0) if isinstance(res.get('score'),(int,float)) else (analise or {}).get('score',0)
        status = res.get('status','') or (analise or {}).get('status','')
        confianca = res.get('score_confianca',0) or (analise or {}).get('score_confianca',0)
        sd = res.get('score_detalhado',{})
        tend = res.get('tendencia',{})
        caixa = res.get('risco_caixa',{})
        prob = res.get('probabilidades',{})
        prev = res.get('previsoes',[])
        insights = res.get('insights',[]) or (analise or {}).get('insights',[])
        rec_princ = res.get('recomendacao_principal','') or (analise or {}).get('recomendacao_principal','')
        meses = res.get('meses_analisados',0) or (analise or {}).get('meses_analisados',calc.get('meses',0))
        fat_total = res.get('faturamento_total',0) or calc.get('receita_total',0)
        fat_medio = res.get('faturamento_medio',0) or calc.get('receita_mensal',0)
        lucro_total = res.get('lucro_total',0) or calc.get('lucro_liquido',0)
        margem_media = res.get('margem_media',0) or calc.get('margem_liquida',0)
        dados_chart = res.get('dados_mensais',[])

        for fn, args in [
            (self._slide_capa, (empresa, score, status, meses)),
            (self._slide_resumo, (empresa, fat_total, fat_medio, lucro_total, margem_media, calc, score, status, confianca, meses, sd)),
            (self._slide_tendencia, (tend,)),
            (self._slide_riscos, (prob, caixa)),
            (self._slide_dre, (calc,)),
            (self._slide_indicadores, (calc,)),
            (self._slide_evolucao, (dados_mensais, dados_chart)),
            (self._slide_previsoes, (tend, prev)),
            (self._slide_alertas, (alertas, insights, rec_princ, tend, caixa, prob)),
            (self._slide_final, (empresa,)),
        ]:
            try: fn(*args)
            except Exception as e:
                import logging; logging.getLogger(__name__).error(f"Erro slide {fn.__name__}: {e}")
                import traceback; logging.getLogger(__name__).error(traceback.format_exc())
                try:
                    slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])
                    self._tb(slide, Inches(1), Inches(3), Inches(8), Inches(1), f"Erro: {str(e)[:100]}", sz=14, color=self.C['danger'])
                except: pass
        buf = io.BytesIO(); self.prs.save(buf); buf.seek(0); return buf.getvalue()

    def _slide_capa(self, empresa, score, status, meses):
        sl = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self._shape(sl, Inches(0), Inches(0), Inches(13.333), Inches(7.5), fill=self.C['dark'])
        self._shape(sl, Inches(0), Inches(0), Inches(0.15), Inches(7.5), fill=self.C['accent'])
        nome = self.config.get('nome_escritorio','Kontabil')
        self._tb(sl, Inches(1), Inches(0.8), Inches(6), Inches(0.5), nome, sz=16, color=self.C['accent'], bold=True)
        self._tb(sl, Inches(1), Inches(2.2), Inches(7), Inches(1.2), "DIAGNÓSTICO\nFINANCEIRO", sz=44, bold=True, color=self.C['white'])
        self._tb(sl, Inches(1), Inches(4.0), Inches(7), Inches(0.6), empresa.get('razao_social',''), sz=22, color=self.C['light'])
        info = [f"CNPJ: {empresa.get('cnpj','-')}"]
        if empresa.get('setor'): info.append(f"Setor: {empresa['setor']}")
        if meses: info.append(f"{meses} meses analisados")
        self._tb(sl, Inches(1), Inches(4.7), Inches(7), Inches(0.4), " • ".join(info), sz=12, color=self.C['gray'])
        if score:
            scl = self._scor(status)
            self._oval(sl, Inches(9.5), Inches(2.2), Inches(2.5), Inches(2.5), fill=scl, txt=str(score), sz=48, color=self.C['white'])
            self._tb(sl, Inches(9.2), Inches(4.8), Inches(3), Inches(0.4), f"de 100 — {self._status_label(status)}", sz=14, color=self.C['white'], align=PP_ALIGN.CENTER)
        self._tb(sl, Inches(1), Inches(6.5), Inches(10), Inches(0.4), f"Gerado em {datetime.now().strftime('%d/%m/%Y')}", sz=10, color=self.C['gray'])

    def _slide_resumo(self, empresa, fat_total, fat_medio, lucro_total, margem_media, calc, score, status, confianca, meses, sd):
        sl = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self._tb(sl, Inches(0.6), Inches(0.4), Inches(8), Inches(0.5), "RESUMO EXECUTIVO", sz=28, bold=True, color=self.C['dark'])
        self._shape(sl, Inches(0.6), Inches(0.95), Inches(2), Inches(0.04), fill=self.C['accent'])
        # Left side: KPI cards (2x3 grid)
        kpis = [
            ("Faturamento Total", self._fm(fat_total), f"{meses} meses"),
            ("Faturamento Mensal", self._fm(fat_medio), "Média"),
            ("Lucro Líquido", self._fm(lucro_total), "Acumulado"),
            ("Margem Média", self._fp(margem_media), "Líquida"),
            ("Liquidez Corrente", f"{calc.get('liquidez_corrente',0):.2f}", "AC/PC"),
            ("Endividamento", self._fp(calc.get('endividamento_geral',0)), "(PC+PNC)/AT"),
        ]
        for i, (titulo, valor, sub) in enumerate(kpis):
            col=i%3; row=i//3; x=Inches(0.6+col*2.75); y=Inches(1.3+row*1.7)
            self._shape(sl, x, y, Inches(2.55), Inches(1.45), fill=self.C['light'])
            self._shape(sl, x, y, Inches(0.06), Inches(1.45), fill=self.C['accent'])
            self._tb(sl, x+Inches(0.2), y+Inches(0.1), Inches(2.2), Inches(0.25), titulo, sz=9, color=self.C['gray'])
            self._tb(sl, x+Inches(0.2), y+Inches(0.4), Inches(2.2), Inches(0.5), valor, sz=18, bold=True, color=self.C['dark'])
            self._tb(sl, x+Inches(0.2), y+Inches(1.0), Inches(2.2), Inches(0.25), sub, sz=9, color=self.C['gray'])
        # Right side: Score + components
        sx = Inches(9.0)
        scl = self._scor(status)
        self._shape(sl, sx, Inches(1.3), Inches(3.8), Inches(5.3), fill=self.C['light'])
        self._shape(sl, sx, Inches(1.3), Inches(3.8), Inches(0.06), fill=scl)
        # Score number
        self._oval(sl, sx+Inches(0.9), Inches(1.55), Inches(2), Inches(2), fill=scl, txt=str(score), sz=40, color=self.C['white'])
        self._tb(sl, sx, Inches(3.6), Inches(3.8), Inches(0.3), f"de 100 — {self._status_label(status)}", sz=12, bold=True, color=scl, align=PP_ALIGN.CENTER)
        if confianca:
            self._tb(sl, sx, Inches(3.9), Inches(3.8), Inches(0.25), f"Confiança: {self._fp(confianca,0)}", sz=9, color=self.C['gray'], align=PP_ALIGN.CENTER)
        # Score components as mini bars
        if sd:
            cy = Inches(4.35)
            for label, key in [('Tendência','tendencia'),('Margem','margem'),('Caixa','caixa'),('Estabilidade','estabilidade'),('Anomalias','anomalias')]:
                val = sd.get(key, 0)
                self._tb(sl, sx+Inches(0.2), cy, Inches(1.5), Inches(0.25), label, sz=8, color=self.C['gray'])
                self._tb(sl, sx+Inches(1.6), cy, Inches(0.6), Inches(0.25), f"{val:.1f}", sz=8, bold=True, color=self.C['dark'], align=PP_ALIGN.RIGHT)
                max_val = max(30, max(sd.get(k,0) for _,k in [('','tendencia'),('','margem'),('','caixa'),('','estabilidade'),('','anomalias')]) * 1.2)
                self._bar(sl, sx+Inches(2.3), cy+Inches(0.05), Inches(1.3), Inches(0.15), min(100,val/max_val*100) if max_val else 0, self.C['accent'])
                cy += Inches(0.38)

    def _slide_tendencia(self, tend):
        if not tend: return  # Skip entire slide
        sl = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self._tb(sl, Inches(0.6), Inches(0.4), Inches(8), Inches(0.5), "ANÁLISE DE TENDÊNCIA", sz=28, bold=True, color=self.C['dark'])
        self._shape(sl, Inches(0.6), Inches(0.95), Inches(2), Inches(0.04), fill=self.C['accent'])
        direcao=tend.get('direcao','stable'); taxa=tend.get('taxa_mensal',0); taxa_anual=tend.get('taxa_anual_projetada',0); r2=tend.get('r_squared',0)
        dcor = self.C['success'] if direcao=='up' else self.C['danger'] if direcao=='down' else self.C['warning']
        dsim = '↑' if direcao=='up' else '↓' if direcao=='down' else '→'
        # Direction card
        self._shape(sl, Inches(0.6), Inches(1.4), Inches(4), Inches(2.5), fill=self.C['light'])
        self._shape(sl, Inches(0.6), Inches(1.4), Inches(0.1), Inches(2.5), fill=dcor)
        self._tb(sl, Inches(1), Inches(1.6), Inches(3), Inches(0.3), "Direção", sz=11, color=self.C['gray'])
        self._tb(sl, Inches(1), Inches(2.0), Inches(3.3), Inches(0.6), f"{dsim} {tend.get('tendencia','-').replace('_',' ').title()}", sz=22, bold=True, color=dcor)
        self._tb(sl, Inches(1), Inches(2.8), Inches(3), Inches(0.3), f"Taxa: {taxa:+.2f}%/mês", sz=14, color=self.C['text'])
        self._tb(sl, Inches(1), Inches(3.2), Inches(3), Inches(0.3), f"Projeção anual: {taxa_anual:+.1f}%", sz=12, color=self.C['gray'])
        # Stats
        for i, (lbl, val, sub) in enumerate([("R²", f"{r2:.3f}", "Qualidade"),("MAPE", f"{tend.get('mape',0):.1f}%", "Erro médio"),("Sazonalidade", "Sim" if tend.get('tem_sazonalidade') else "Não", "Detecção")]):
            x = Inches(5.0+i*2.8)
            self._shape(sl, x, Inches(1.4), Inches(2.5), Inches(2.5), fill=self.C['light'])
            self._tb(sl, x+Inches(0.2), Inches(1.6), Inches(2.2), Inches(0.3), lbl, sz=10, color=self.C['gray'])
            self._tb(sl, x+Inches(0.2), Inches(2.1), Inches(2.2), Inches(0.5), val, sz=20, bold=True, color=self.C['dark'])
            self._tb(sl, x+Inches(0.2), Inches(2.8), Inches(2.2), Inches(0.3), sub, sz=9, color=self.C['gray'])
        y = Inches(4.3)
        desc=tend.get('descricao',''); rec=tend.get('recomendacao','')
        if desc: self._shape(sl,Inches(0.6),y,Inches(12),Inches(0.9),fill=self.C['light']); self._tb(sl,Inches(0.9),y+Inches(0.1),Inches(11.5),Inches(0.7),desc,sz=12,color=self.C['text']); y+=Inches(1.1)
        if rec: self._shape(sl,Inches(0.6),y,Inches(12),Inches(0.9),fill=RGBColor(0xD1,0xFA,0xE5)); self._tb(sl,Inches(0.9),y+Inches(0.1),Inches(11.5),Inches(0.7),f"→ {rec}",sz=12,bold=True,color=self.C['success']); y+=Inches(1.2)
        for key,lbl in [('previsao_3m','3 meses'),('previsao_6m','6 meses'),('previsao_12m','12 meses')]:
            pv = tend.get(key,{})
            if pv:
                self._tb(sl,Inches(0.6),y,Inches(2.5),Inches(0.3),f"Previsão {lbl}:",sz=10,bold=True,color=self.C['dark'])
                self._tb(sl,Inches(3.2),y,Inches(8),Inches(0.3),f"{self._fm(pv.get('valor_previsto',0))}  (IC: {self._fm(pv.get('intervalo_inferior',0))} ~ {self._fm(pv.get('intervalo_superior',0))})",sz=10,color=self.C['text']); y+=Inches(0.35)

    def _slide_riscos(self, prob, caixa):
        if not prob and not caixa: return  # Skip entire slide
        sl = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self._tb(sl, Inches(0.6), Inches(0.4), Inches(8), Inches(0.5), "ANÁLISE DE RISCOS", sz=28, bold=True, color=self.C['dark'])
        self._shape(sl, Inches(0.6), Inches(0.95), Inches(2), Inches(0.04), fill=self.C['accent'])
        if prob:
            for i, (lbl, pk, rk) in enumerate([("Risco de Prejuízo",'prob_prejuizo','risco_prejuizo'),("Risco de Quebra",'prob_quebra','risco_quebra'),("Imposto Inesperado",'prob_imposto_inesperado','risco_imposto')]):
                pct=prob.get(pk,0); nivel=prob.get(rk,'-'); x=Inches(0.6+i*4.1); ncor=self._scor(nivel)
                self._shape(sl, x, Inches(1.4), Inches(3.8), Inches(2.0), fill=self.C['light'])
                self._shape(sl, x, Inches(1.4), Inches(3.8), Inches(0.08), fill=ncor)
                self._tb(sl, x+Inches(0.3), Inches(1.6), Inches(3.2), Inches(0.3), lbl, sz=11, color=self.C['gray'])
                self._tb(sl, x+Inches(0.3), Inches(2.0), Inches(3.2), Inches(0.5), f"{pct:.1f}%", sz=26, bold=True, color=ncor)
                self._tb(sl, x+Inches(0.3), Inches(2.7), Inches(3.2), Inches(0.3), f"Nível: {nivel.title()}", sz=11, color=self.C['text'])
        if caixa:
            y=Inches(3.8); self._tb(sl,Inches(0.6),y,Inches(8),Inches(0.4),"RISCO DE CAIXA",sz=16,bold=True,color=self.C['dark']); y+=Inches(0.5)
            items=[("Nível",caixa.get('nivel','-').title()),("Saldo Atual",self._fm(caixa.get('saldo_atual',0))),("Burn Rate",self._fm(caixa.get('burn_rate_medio',0))),
                   ("Runway Pessim.",f"{caixa.get('runway_p10','-')} meses"),("Runway Base",f"{caixa.get('runway_p50','-')} meses"),("Runway Otim.",f"{caixa.get('runway_p90','-')} meses")]
            for i,(lbl,val) in enumerate(items):
                col=i%3;row=i//3;x=Inches(0.6+col*4.1);yy=y+Inches(row*0.9)
                self._shape(sl,x,yy,Inches(3.8),Inches(0.75),fill=self.C['light'])
                self._tb(sl,x+Inches(0.2),yy+Inches(0.05),Inches(1.5),Inches(0.3),lbl,sz=9,color=self.C['gray'])
                self._tb(sl,x+Inches(1.8),yy+Inches(0.05),Inches(1.8),Inches(0.3),val,sz=12,bold=True,color=self.C['dark'],align=PP_ALIGN.RIGHT)
        if prob:
            y=Inches(6.0); fp=prob.get('fatores_positivos',[]); fr=prob.get('fatores_risco',[])
            if fp: self._tb(sl,Inches(0.6),y,Inches(6),Inches(0.3),"✓ Positivos:",sz=10,bold=True,color=self.C['success']); self._tb(sl,Inches(0.6),y+Inches(0.3),Inches(6),Inches(0.8)," • ".join(fp[:4]),sz=9,color=self.C['text'])
            if fr: self._tb(sl,Inches(6.8),y,Inches(6),Inches(0.3),"⚠ Riscos:",sz=10,bold=True,color=self.C['danger']); self._tb(sl,Inches(6.8),y+Inches(0.3),Inches(6),Inches(0.8)," • ".join(fr[:4]),sz=9,color=self.C['text'])

    def _slide_dre(self, calc):
        sl = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self._tb(sl, Inches(0.6), Inches(0.4), Inches(8), Inches(0.5), "DEMONSTRAÇÃO DO RESULTADO", sz=28, bold=True, color=self.C['dark'])
        self._shape(sl, Inches(0.6), Inches(0.95), Inches(2), Inches(0.04), fill=self.C['accent'])
        rt = calc.get('receita_total',0) or 1
        linhas = [
            ("RECEITA BRUTA", calc.get('receita_total',0), 100, True),
            ("  (-) Impostos", -calc.get('impostos_total',0), -(calc.get('impostos_total',0)/rt*100), False),
            ("(=) Receita Líquida", rt-calc.get('impostos_total',0), (rt-calc.get('impostos_total',0))/rt*100, False),
            ("  (-) Custos (CMV/CSP)", -calc.get('custos_total',0), -(calc.get('custos_total',0)/rt*100), False),
            ("(=) LUCRO BRUTO", calc.get('lucro_bruto',0), calc.get('margem_bruta',0), True),
            ("  (-) Despesas Operacionais", -calc.get('despesas_total',0), -(calc.get('despesas_total',0)/rt*100), False),
            ("  (-) Folha de Pagamento", -calc.get('folha_total',0), -(calc.get('folha_total',0)/rt*100), False),
            ("(=) LUCRO LÍQUIDO", calc.get('lucro_liquido',0), calc.get('margem_liquida',0), True),
        ]
        y = Inches(1.3)
        for tag, w, pos in [("Conta",5.5,0.6),("Valor",3.2,6.1),("% Receita",2.5,9.3)]:
            self._shape(sl,Inches(pos),y,Inches(w),Inches(0.45),fill=self.C['dark'])
            self._tb(sl,Inches(pos+0.2),y+Inches(0.05),Inches(w-0.4),Inches(0.35),tag,sz=11,bold=True,color=self.C['white'],align=PP_ALIGN.RIGHT if pos>1 else PP_ALIGN.LEFT)
        y += Inches(0.5)
        for conta, valor, pct, destaque in linhas:
            if destaque: self._shape(sl,Inches(0.6),y,Inches(11.2),Inches(0.5),fill=self.C['light'])
            vcor = self.C['danger'] if valor<0 and destaque else (self.C['success'] if valor>0 and 'LUCRO' in conta else self.C['text'])
            self._tb(sl,Inches(0.8),y+Inches(0.08),Inches(5),Inches(0.35),conta,sz=12,bold=destaque,color=self.C['dark'])
            self._tb(sl,Inches(6.3),y+Inches(0.08),Inches(2.8),Inches(0.35),self._fm(abs(valor) if valor<0 else valor),sz=12,bold=destaque,color=vcor,align=PP_ALIGN.RIGHT)
            self._tb(sl,Inches(9.5),y+Inches(0.08),Inches(2.1),Inches(0.35),self._fp(abs(pct)),sz=11,color=self.C['gray'],align=PP_ALIGN.RIGHT)
            y += Inches(0.55)

    def _slide_indicadores(self, calc):
        sl = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self._tb(sl, Inches(0.6), Inches(0.4), Inches(8), Inches(0.5), "INDICADORES FINANCEIROS", sz=28, bold=True, color=self.C['dark'])
        self._shape(sl, Inches(0.6), Inches(0.95), Inches(2), Inches(0.04), fill=self.C['accent'])
        mb=calc.get('margem_bruta',0);ml=calc.get('margem_liquida',0);lc=calc.get('liquidez_corrente',0);ls=calc.get('liquidez_seca',0);eg=calc.get('endividamento_geral',0);cg=calc.get('capital_giro',0)
        cards = [
            ("Margem Bruta",self._fp(mb),'Excelente' if mb>=50 else 'Bom' if mb>=35 else 'Adequado' if mb>=20 else 'Baixa',"LB / Receita"),
            ("Margem Líquida",self._fp(ml),'Excelente' if ml>=20 else 'Bom' if ml>=10 else 'Adequado' if ml>=0 else 'Prejuízo',"LL / Receita"),
            ("Liquidez Corrente",f"{lc:.2f}",'Excelente' if lc>=2 else 'Bom' if lc>=1.5 else 'Adequado' if lc>=1 else 'Crítico',"AC / PC"),
            ("Liquidez Seca",f"{ls:.2f}",'Bom' if ls>=1 else 'Adequado' if ls>=0.7 else 'Baixa',"(AC-Est) / PC"),
            ("Endividamento",self._fp(eg),'Baixo' if eg<=30 else 'Moderado' if eg<=50 else 'Elevado',"(PC+PNC) / AT"),
            ("Capital de Giro",self._fm(cg),'Positivo' if cg>0 else 'Negativo',"AC - PC"),
        ]
        for i, (titulo, valor, status, ref) in enumerate(cards):
            col=i%3;row=i//3;x=Inches(0.6+col*4.1);y=Inches(1.4+row*2.8);scor=self._scor(status)
            self._shape(sl,x,y,Inches(3.8),Inches(2.4),fill=self.C['light'])
            self._shape(sl,x,y,Inches(3.8),Inches(0.06),fill=scor)
            self._tb(sl,x+Inches(0.3),y+Inches(0.2),Inches(3.2),Inches(0.3),titulo,sz=11,color=self.C['gray'])
            self._tb(sl,x+Inches(0.3),y+Inches(0.65),Inches(3.2),Inches(0.6),valor,sz=24,bold=True,color=self.C['dark'])
            self._shape(sl,x+Inches(0.3),y+Inches(1.5),Inches(1.5),Inches(0.35),fill=scor,txt=status,sz=9,bold=True,color=self.C['white'])
            self._tb(sl,x+Inches(0.3),y+Inches(1.95),Inches(3.2),Inches(0.25),ref,sz=9,color=self.C['gray'])

    def _slide_evolucao(self, dados_raw, dados_chart):
        sl = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self._tb(sl, Inches(0.6), Inches(0.4), Inches(8), Inches(0.5), "EVOLUÇÃO FINANCEIRA", sz=28, bold=True, color=self.C['dark'])
        self._shape(sl, Inches(0.6), Inches(0.95), Inches(2), Inches(0.04), fill=self.C['accent'])
        if dados_chart and len(dados_chart)>=2:
            labels=[d.get('periodo','') for d in dados_chart]; receitas=[d.get('receita',0) for d in dados_chart]; lucros=[d.get('lucro',0) for d in dados_chart]
        elif dados_raw and len(dados_raw)>=2:
            ds=sorted(dados_raw, key=lambda x:(x.get('ano',0),x.get('mes',0)))[-12:]
            labels=[f"{d.get('mes',0):02d}/{d.get('ano',0)}" for d in ds]
            receitas=[float(d.get('receita',0) or 0) for d in ds]
            lucros=[float(d.get('lucro_liquido',0) or 0) or (float(d.get('receita',0) or 0)-float(d.get('custos',0) or 0)-float(d.get('despesas',0) or 0)-float(d.get('impostos',0) or 0)-float(d.get('folha',0) or 0)) for d in ds]
        else: return
        try:
            cd = CategoryChartData(); cd.categories = labels
            cd.add_series('Receita', receitas); cd.add_series('Lucro Líquido', lucros)
            chart = sl.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.6), Inches(1.3), Inches(12), Inches(5.5), cd).chart
            chart.has_legend = True; chart.legend.include_in_layout = False
            chart.series[0].format.fill.solid(); chart.series[0].format.fill.fore_color.rgb = RGBColor(0x15,0x44,0x7E)
            chart.series[1].format.fill.solid(); chart.series[1].format.fill.fore_color.rgb = RGBColor(0x05,0x96,0x69)
        except: self._tb(sl,Inches(1),Inches(2.5),Inches(10),Inches(1),"Erro no gráfico.",sz=14,color=self.C['danger'])

    def _slide_previsoes(self, tend, prev):
        if not prev and not (tend and any(tend.get(k) for k in ('previsao_3m','previsao_6m','previsao_12m'))): return
        sl = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self._tb(sl, Inches(0.6), Inches(0.4), Inches(8), Inches(0.5), "PREVISÕES DE FATURAMENTO", sz=28, bold=True, color=self.C['dark'])
        self._shape(sl, Inches(0.6), Inches(0.95), Inches(2), Inches(0.04), fill=self.C['accent'])
        has = False
        if prev:
            has = True
            for i, p in enumerate(prev[:3]):
                y=Inches(1.5+i*1.8)
                self._shape(sl,Inches(0.6),y,Inches(12),Inches(1.5),fill=self.C['light'])
                self._tb(sl,Inches(1),y+Inches(0.15),Inches(2),Inches(0.3),p.get('periodo',''),sz=14,bold=True,color=self.C['accent'])
                self._tb(sl,Inches(1),y+Inches(0.5),Inches(3),Inches(0.5),self._fm(p.get('receita_prevista',0)),sz=28,bold=True,color=self.C['dark'])
                self._tb(sl,Inches(5),y+Inches(0.3),Inches(3),Inches(0.3),"Intervalo de Confiança:",sz=10,color=self.C['gray'])
                self._tb(sl,Inches(5),y+Inches(0.65),Inches(5),Inches(0.3),f"{self._fm(p.get('receita_inferior',0))}  —  {self._fm(p.get('receita_superior',0))}",sz=14,color=self.C['text'])
        if not has and tend:
            for i,(key,lbl) in enumerate([('previsao_3m','Próximos 3 meses'),('previsao_6m','Próximos 6 meses'),('previsao_12m','Próximos 12 meses')]):
                pv=tend.get(key,{})
                if pv:
                    has=True; y=Inches(1.5+i*1.8)
                    self._shape(sl,Inches(0.6),y,Inches(12),Inches(1.5),fill=self.C['light'])
                    self._tb(sl,Inches(1),y+Inches(0.15),Inches(3),Inches(0.3),lbl,sz=14,bold=True,color=self.C['accent'])
                    self._tb(sl,Inches(1),y+Inches(0.5),Inches(3),Inches(0.5),self._fm(pv.get('valor_previsto',0)),sz=28,bold=True,color=self.C['dark'])
                    self._tb(sl,Inches(5),y+Inches(0.3),Inches(3),Inches(0.3),f"IC {pv.get('confianca',95)}%:",sz=10,color=self.C['gray'])
                    self._tb(sl,Inches(5),y+Inches(0.65),Inches(5),Inches(0.3),f"{self._fm(pv.get('intervalo_inferior',0))}  —  {self._fm(pv.get('intervalo_superior',0))}",sz=14,color=self.C['text'])
        if not has: return  # Skip slide

    def _slide_alertas(self, alertas, insights, rec_princ, tend, caixa, prob):
        sl = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self._tb(sl, Inches(0.6), Inches(0.4), Inches(8), Inches(0.5), "ALERTAS E RECOMENDAÇÕES", sz=28, bold=True, color=self.C['dark'])
        self._shape(sl, Inches(0.6), Inches(0.95), Inches(2), Inches(0.04), fill=self.C['accent'])
        y = Inches(1.3)
        if alertas:
            crit=[a for a in alertas if a.get('severidade')=='critico']; aten=[a for a in alertas if a.get('severidade')=='atencao']
            if crit:
                self._shape(sl,Inches(0.6),y,Inches(12),Inches(0.4),fill=RGBColor(0xFE,0xE2,0xE2))
                self._tb(sl,Inches(0.8),y+Inches(0.05),Inches(4),Inches(0.3),f"🔴 CRÍTICOS ({len(crit)})",sz=11,bold=True,color=self.C['danger']); y+=Inches(0.45)
                for a in crit[:4]: self._tb(sl,Inches(1),y,Inches(11),Inches(0.3),f"• {a.get('titulo','')}",sz=11,color=self.C['danger']); y+=Inches(0.35)
            if aten:
                self._shape(sl,Inches(0.6),y,Inches(12),Inches(0.4),fill=RGBColor(0xFE,0xF3,0xC7))
                self._tb(sl,Inches(0.8),y+Inches(0.05),Inches(4),Inches(0.3),f"🟡 ATENÇÃO ({len(aten)})",sz=11,bold=True,color=self.C['warning']); y+=Inches(0.45)
                for a in aten[:4]: self._tb(sl,Inches(1),y,Inches(11),Inches(0.3),f"• {a.get('titulo','')}",sz=11,color=self.C['warning']); y+=Inches(0.35)
        else:
            self._shape(sl,Inches(0.6),y,Inches(12),Inches(0.4),fill=RGBColor(0xD1,0xFA,0xE5))
            self._tb(sl,Inches(0.8),y+Inches(0.05),Inches(4),Inches(0.3),"✅ Nenhum alerta",sz=11,bold=True,color=self.C['success']); y+=Inches(0.5)
        y+=Inches(0.3); self._tb(sl,Inches(0.6),y,Inches(8),Inches(0.4),"RECOMENDAÇÕES",sz=16,bold=True,color=self.C['dark']); y+=Inches(0.5)
        recs=[]
        if rec_princ: recs.append(f"⭐ {rec_princ}")
        if tend and tend.get('recomendacao'): recs.append(f"📈 {tend['recomendacao']}")
        if caixa and caixa.get('recomendacao'): recs.append(f"💰 {caixa['recomendacao']}")
        if prob and prob.get('recomendacao'): recs.append(f"⚠️ {prob['recomendacao']}")
        if not recs: recs=["Manter monitoramento mensal","Executar análise completa"]
        for i, rc in enumerate(recs[:6]):
            if i%2==0: self._shape(sl,Inches(0.6),y,Inches(12),Inches(0.5),fill=self.C['light'])
            self._tb(sl,Inches(0.9),y+Inches(0.08),Inches(11.3),Inches(0.35),rc,sz=12,color=self.C['text']); y+=Inches(0.55)
        if insights and y<Inches(6.0):
            y+=Inches(0.2); self._tb(sl,Inches(0.6),y,Inches(8),Inches(0.3),"INSIGHTS",sz=13,bold=True,color=self.C['dark']); y+=Inches(0.4)
            for it in (insights[:5] if isinstance(insights,list) else []):
                txt = self._insight_text(it)
                if txt: self._tb(sl,Inches(0.9),y,Inches(11),Inches(0.3),f"• {txt}",sz=10,color=self.C['gray']); y+=Inches(0.3)

    def _slide_final(self, empresa):
        sl = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self._shape(sl,Inches(0),Inches(0),Inches(13.333),Inches(7.5),fill=self.C['dark'])
        self._shape(sl,Inches(0),Inches(0),Inches(0.15),Inches(7.5),fill=self.C['accent'])
        nome=self.config.get('nome_escritorio','Kontabil')
        self._tb(sl,Inches(1),Inches(1.5),Inches(10),Inches(0.5),nome,sz=16,color=self.C['accent'],bold=True)
        self._tb(sl,Inches(1),Inches(2.8),Inches(10),Inches(0.8),"Obrigado pela confiança!",sz=36,bold=True,color=self.C['white'])
        info=[]
        if self.config.get('telefone'): info.append(f"Tel: {self.config['telefone']}")
        if self.config.get('email'): info.append(f"Email: {self.config['email']}")
        if info: self._tb(sl,Inches(1),Inches(4.2),Inches(10),Inches(0.4)," • ".join(info),sz=14,color=self.C['light'])
        self._tb(sl,Inches(1),Inches(5.5),Inches(10),Inches(0.4),f"Gerado em {datetime.now().strftime('%d/%m/%Y')} — Dados confidenciais",sz=10,color=self.C['gray'])


def gerar_pptx(empresa, dados_mensais, analise=None, config=None, alertas=None):
    return PowerPointGenerator(config).gerar_apresentacao(empresa, dados_mensais, analise, alertas, config)
