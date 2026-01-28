#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Relatório PDF - Diagnóstico Financeiro
"""

import io
from datetime import datetime
from typing import Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)


class PDFGenerator:
    """Gerador de relatório PDF."""
    
    PRIMARY = colors.HexColor('#1e3a5f')
    SECONDARY = colors.HexColor('#2563eb')
    SUCCESS = colors.HexColor('#059669')
    WARNING = colors.HexColor('#d97706')
    DANGER = colors.HexColor('#dc2626')
    GRAY = colors.HexColor('#374151')
    GRAY_LIGHT = colors.HexColor('#f3f4f6')
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        self.styles.add(ParagraphStyle('MainTitle', fontSize=24, textColor=self.PRIMARY, alignment=TA_CENTER, fontName='Helvetica-Bold', spaceAfter=10))
        self.styles.add(ParagraphStyle('Subtitle', fontSize=12, textColor=self.GRAY, alignment=TA_CENTER, spaceAfter=20))
        self.styles.add(ParagraphStyle('SectionTitle', fontSize=14, textColor=self.PRIMARY, fontName='Helvetica-Bold', spaceBefore=15, spaceAfter=8))
        self.styles.add(ParagraphStyle('SubsectionTitle', fontSize=11, textColor=self.SECONDARY, fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=6))
        self.styles.add(ParagraphStyle('BodyTextCustom', fontSize=10, textColor=self.GRAY, alignment=TA_JUSTIFY, leading=14, spaceAfter=6))
        self.styles.add(ParagraphStyle('BulletText', fontSize=10, textColor=self.GRAY, leftIndent=15, spaceAfter=4))
    
    def generate(self, result: Dict) -> bytes:
        """Gera PDF e retorna bytes."""
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm
        )
        
        story = []
        
        # Capa
        story.extend(self._build_cover(result))
        story.append(PageBreak())
        
        # Resumo
        story.extend(self._build_summary(result))
        story.append(PageBreak())
        
        # 4 Pilares
        story.extend(self._build_pilares(result))
        story.append(PageBreak())
        
        # Recomendações
        story.extend(self._build_recomendacoes(result))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.read()
    
    def _build_cover(self, result: Dict) -> List:
        elements = []
        elements.append(Spacer(1, 3*cm))
        elements.append(Paragraph("DIAGNÓSTICO FINANCEIRO", self.styles['MainTitle']))
        elements.append(Paragraph("Análise de Saúde Empresarial", self.styles['Subtitle']))
        elements.append(HRFlowable(width="40%", thickness=2, color=self.PRIMARY, spaceBefore=20, spaceAfter=30))
        
        elements.append(Paragraph(result.get('empresa', 'Empresa'), 
            ParagraphStyle('', fontSize=18, textColor=self.GRAY, alignment=TA_CENTER, fontName='Helvetica-Bold', spaceAfter=10)))
        
        periodo = f"Período: {result.get('periodo_inicio', '')} a {result.get('periodo_fim', '')}"
        elements.append(Paragraph(periodo, self.styles['Subtitle']))
        
        elements.append(Spacer(1, 2*cm))
        
        # Score
        score = result.get('score', 0)
        if score >= 70:
            status_color = self.SUCCESS
            status_text = "SAUDÁVEL"
        elif score >= 40:
            status_color = self.WARNING
            status_text = "ATENÇÃO"
        else:
            status_color = self.DANGER
            status_text = "CRÍTICO"
        
        score_data = [
            [Paragraph("SCORE DE SAÚDE FINANCEIRA", ParagraphStyle('', fontSize=10, textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica-Bold'))],
            [Paragraph(str(score), ParagraphStyle('', fontSize=48, textColor=status_color, alignment=TA_CENTER, fontName='Helvetica-Bold'))],
            [Paragraph(status_text, ParagraphStyle('', fontSize=12, textColor=status_color, alignment=TA_CENTER, fontName='Helvetica-Bold'))],
        ]
        
        score_table = Table(score_data, colWidths=[8*cm])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY),
            ('BACKGROUND', (0, 1), (-1, -1), self.GRAY_LIGHT),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(score_table)
        
        return elements
    
    def _build_summary(self, result: Dict) -> List:
        elements = []
        elements.append(Paragraph("RESUMO EXECUTIVO", self.styles['SectionTitle']))
        
        intro = f"Análise de {result.get('meses_analisados', 0)} meses de dados financeiros."
        elements.append(Paragraph(intro, self.styles['BodyTextCustom']))
        
        # Números
        numeros = [
            ['Faturamento Total', f"R$ {result.get('faturamento_total', 0):,.2f}"],
            ['Faturamento Médio', f"R$ {result.get('faturamento_medio', 0):,.2f}"],
            ['Resultado Total', f"R$ {result.get('lucro_total', 0):,.2f}"],
            ['Margem Média', f"{result.get('margem_media', 0):.1f}%"],
        ]
        
        table = Table(numeros, colWidths=[8*cm, 6*cm])
        table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, self.GRAY_LIGHT),
        ]))
        elements.append(table)
        
        return elements
    
    def _build_pilares(self, result: Dict) -> List:
        elements = []
        
        # Tendência
        elements.append(Paragraph("1. TENDÊNCIA DE FATURAMENTO", self.styles['SectionTitle']))
        tend = result.get('tendencia', {})
        elements.append(Paragraph(f"<b>Status:</b> {tend.get('tendencia', 'N/A')}", self.styles['BodyTextCustom']))
        elements.append(Paragraph(f"<b>Taxa mensal:</b> {tend.get('taxa_mensal', 0):+.2f}%", self.styles['BodyTextCustom']))
        elements.append(Paragraph(tend.get('descricao', ''), self.styles['BodyTextCustom']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Caixa
        elements.append(Paragraph("2. RISCO DE CAIXA", self.styles['SectionTitle']))
        caixa = result.get('risco_caixa', {})
        elements.append(Paragraph(f"<b>Nível:</b> {caixa.get('nivel', 'N/A')}", self.styles['BodyTextCustom']))
        elements.append(Paragraph(f"<b>Runway:</b> {caixa.get('runway_meses', 0)} meses", self.styles['BodyTextCustom']))
        elements.append(Paragraph(caixa.get('descricao', ''), self.styles['BodyTextCustom']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Anomalias
        elements.append(Paragraph("3. ANOMALIAS FINANCEIRAS", self.styles['SectionTitle']))
        anom = result.get('anomalias', {})
        elements.append(Paragraph(f"<b>Total:</b> {anom.get('total', 0)} detectadas", self.styles['BodyTextCustom']))
        elements.append(Paragraph(anom.get('descricao', ''), self.styles['BodyTextCustom']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Probabilidades
        elements.append(Paragraph("4. PROBABILIDADE DE PROBLEMAS", self.styles['SectionTitle']))
        prob = result.get('probabilidades', {})
        elements.append(Paragraph(f"• Prejuízo próx. trimestre: {prob.get('prob_prejuizo', 0)}%", self.styles['BulletText']))
        elements.append(Paragraph(f"• Quebra em 12 meses: {prob.get('prob_quebra', 0)}%", self.styles['BulletText']))
        elements.append(Paragraph(f"• Imposto inesperado: {prob.get('prob_imposto', 0)}%", self.styles['BulletText']))
        
        return elements
    
    def _build_recomendacoes(self, result: Dict) -> List:
        elements = []
        elements.append(Paragraph("RECOMENDAÇÕES", self.styles['SectionTitle']))
        elements.append(Paragraph(result.get('recomendacao_principal', ''), self.styles['BodyTextCustom']))
        
        # Fatores
        prob = result.get('probabilidades', {})
        
        if prob.get('fatores_risco'):
            elements.append(Paragraph("Fatores de Risco:", self.styles['SubsectionTitle']))
            for f in prob['fatores_risco']:
                elements.append(Paragraph(f"• {f}", self.styles['BulletText']))
        
        if prob.get('fatores_positivos'):
            elements.append(Paragraph("Fatores Positivos:", self.styles['SubsectionTitle']))
            for f in prob['fatores_positivos']:
                elements.append(Paragraph(f"• {f}", self.styles['BulletText']))
        
        # Disclaimer
        elements.append(Spacer(1, 1*cm))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=self.GRAY_LIGHT))
        elements.append(Paragraph(
            "Este relatório foi gerado automaticamente e não substitui análise profissional.",
            ParagraphStyle('', fontSize=8, textColor=colors.gray, alignment=TA_CENTER)
        ))
        
        return elements
