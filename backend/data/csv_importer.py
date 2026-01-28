#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Importador de Dados Contábeis - Aceita qualquer formato de CSV/Excel
"""

import csv
import io
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field


@dataclass
class MonthlyRecord:
    """Registro mensal normalizado."""
    periodo: str
    data: datetime
    receita: float
    custos: float
    despesas: float
    impostos: float
    folha: float = 0
    caixa: float = 0
    
    @property
    def lucro_bruto(self) -> float:
        return self.receita - self.custos
    
    @property
    def margem_bruta(self) -> float:
        return (self.lucro_bruto / self.receita * 100) if self.receita > 0 else 0
    
    @property
    def despesas_totais(self) -> float:
        return self.despesas + self.folha
    
    @property
    def lucro_operacional(self) -> float:
        return self.lucro_bruto - self.despesas_totais
    
    @property
    def lucro_liquido(self) -> float:
        return self.lucro_operacional - self.impostos
    
    @property
    def margem_liquida(self) -> float:
        return (self.lucro_liquido / self.receita * 100) if self.receita > 0 else 0
    
    @property
    def carga_tributaria(self) -> float:
        return (self.impostos / self.receita * 100) if self.receita > 0 else 0
    
    def to_dict(self) -> Dict:
        return {
            'periodo': self.periodo,
            'receita': self.receita,
            'custos': self.custos,
            'despesas': self.despesas,
            'impostos': self.impostos,
            'folha': self.folha,
            'caixa': self.caixa,
            'lucro_bruto': self.lucro_bruto,
            'lucro_liquido': self.lucro_liquido,
            'margem_bruta': self.margem_bruta,
            'margem_liquida': self.margem_liquida,
        }


@dataclass
class CompanyData:
    """Dados consolidados da empresa."""
    records: List[MonthlyRecord] = field(default_factory=list)
    empresa: str = ""
    cnpj: str = ""
    contador: str = ""
    periodo_inicio: Optional[datetime] = None
    periodo_fim: Optional[datetime] = None
    total_meses: int = 0
    errors: List[str] = field(default_factory=list)
    
    @property
    def faturamento_total(self) -> float:
        return sum(r.receita for r in self.records)
    
    @property
    def faturamento_medio(self) -> float:
        return self.faturamento_total / len(self.records) if self.records else 0
    
    @property
    def lucro_total(self) -> float:
        return sum(r.lucro_liquido for r in self.records)
    
    @property
    def ultimo_caixa(self) -> float:
        return self.records[-1].caixa if self.records else 0


class SmartCSVImporter:
    """Importador inteligente que aceita qualquer formato."""
    
    # Keywords para detecção automática de colunas
    FIELD_KEYWORDS = {
        'data': ['data', 'periodo', 'mes', 'ano', 'competencia', 'ref', 'date', 'month', 'year', 'dt'],
        'receita': ['receita', 'faturamento', 'vendas', 'entradas', 'revenue', 'sales', 'fat', 'income', 'bruto', 'entrada'],
        'custos': ['custo', 'cmv', 'cpv', 'cost', 'mercadoria', 'produto', 'servico'],
        'despesas': ['despesa', 'expense', 'gasto', 'operacional', 'administrativa', 'fixa', 'variavel', 'desp'],
        'impostos': ['imposto', 'tributo', 'tax', 'icms', 'pis', 'cofins', 'iss', 'irpj', 'csll', 'simples', 'tribut'],
        'folha': ['folha', 'salario', 'payroll', 'pessoal', 'funcionario', 'encargo', 'inss', 'fgts', 'rh'],
        'caixa': ['caixa', 'cash', 'disponivel', 'banco', 'saldo', 'disponibilidade', 'disp'],
    }
    
    def __init__(self):
        self.detected_mapping = {}
    
    def detect_delimiter(self, content: str) -> str:
        """Detecta delimitador do CSV."""
        first_lines = content[:2000]
        semicolons = first_lines.count(';')
        commas = first_lines.count(',')
        tabs = first_lines.count('\t')
        
        if semicolons > commas and semicolons > tabs:
            return ';'
        elif tabs > commas:
            return '\t'
        return ','
    
    def detect_columns(self, columns: List[str]) -> Dict[str, str]:
        """Detecta automaticamente o significado das colunas."""
        mapping = {}
        
        for col in columns:
            col_lower = col.lower().strip()
            col_normalized = self._normalize_text(col_lower)
            
            for field_id, keywords in self.FIELD_KEYWORDS.items():
                if field_id in mapping:
                    continue
                for keyword in keywords:
                    if keyword in col_normalized:
                        mapping[field_id] = col
                        break
        
        self.detected_mapping = mapping
        return mapping
    
    def _normalize_text(self, text: str) -> str:
        """Remove acentos e normaliza texto."""
        import unicodedata
        nfkd = unicodedata.normalize('NFKD', text)
        return ''.join(c for c in nfkd if not unicodedata.combining(c))
    
    def parse_number(self, value: Any) -> float:
        """Parseia número de qualquer formato."""
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        
        text = str(value).strip()
        if not text or text.lower() in ['', 'nan', 'null', 'none', '-']:
            return 0.0
        
        # Remove R$, espaços
        text = re.sub(r'[R$\s]', '', text)
        
        # Detecta formato brasileiro (1.234,56) vs americano (1,234.56)
        if ',' in text and '.' in text:
            if text.rfind(',') > text.rfind('.'):
                # Brasileiro: 1.234,56
                text = text.replace('.', '').replace(',', '.')
            else:
                # Americano: 1,234.56
                text = text.replace(',', '')
        elif ',' in text:
            # Pode ser decimal brasileiro ou milhar americano
            parts = text.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                # Provavelmente decimal brasileiro
                text = text.replace(',', '.')
            else:
                # Provavelmente milhar americano
                text = text.replace(',', '')
        
        try:
            return float(text)
        except:
            return 0.0
    
    def parse_date(self, value: Any) -> Optional[datetime]:
        """Parseia data de qualquer formato."""
        if value is None:
            return None
        
        text = str(value).strip()
        
        formats = [
            '%Y-%m', '%Y/%m', '%m/%Y', '%m-%Y',
            '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y',
            '%Y%m', '%m%Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(text, fmt)
            except:
                continue
        
        # Tenta extrair ano e mês de texto livre
        match = re.search(r'(\d{4})[/-]?(\d{1,2})', text)
        if match:
            try:
                return datetime(int(match.group(1)), int(match.group(2)), 1)
            except:
                pass
        
        match = re.search(r'(\d{1,2})[/-](\d{4})', text)
        if match:
            try:
                return datetime(int(match.group(2)), int(match.group(1)), 1)
            except:
                pass
        
        return None
    
    def import_csv(
        self, 
        content: str, 
        mapping: Dict[str, str],
        empresa: str = "",
        cnpj: str = "",
        contador: str = ""
    ) -> CompanyData:
        """Importa CSV com mapeamento fornecido."""
        
        company = CompanyData(empresa=empresa, cnpj=cnpj, contador=contador)
        
        try:
            delimiter = self.detect_delimiter(content)
            reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
            
            for i, row in enumerate(reader, start=2):
                try:
                    # Extrai valores usando mapeamento
                    periodo_raw = row.get(mapping.get('data', ''), '')
                    data = self.parse_date(periodo_raw)
                    
                    if not data:
                        company.errors.append(f"Linha {i}: Data inválida '{periodo_raw}'")
                        continue
                    
                    record = MonthlyRecord(
                        periodo=periodo_raw,
                        data=data,
                        receita=self.parse_number(row.get(mapping.get('receita', ''), 0)),
                        custos=self.parse_number(row.get(mapping.get('custos', ''), 0)),
                        despesas=self.parse_number(row.get(mapping.get('despesas', ''), 0)),
                        impostos=self.parse_number(row.get(mapping.get('impostos', ''), 0)),
                        folha=self.parse_number(row.get(mapping.get('folha', ''), 0)),
                        caixa=self.parse_number(row.get(mapping.get('caixa', ''), 0)),
                    )
                    
                    company.records.append(record)
                    
                except Exception as e:
                    company.errors.append(f"Linha {i}: {str(e)}")
            
            # Ordena por data
            company.records.sort(key=lambda x: x.data)
            
            if company.records:
                company.periodo_inicio = company.records[0].data
                company.periodo_fim = company.records[-1].data
                company.total_meses = len(company.records)
            
        except Exception as e:
            company.errors.append(f"Erro geral: {str(e)}")
        
        return company
    
    def get_preview(self, content: str, max_rows: int = 5) -> Dict:
        """Retorna preview dos dados para mapeamento."""
        try:
            delimiter = self.detect_delimiter(content)
            reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
            
            rows = []
            columns = reader.fieldnames or []
            
            for i, row in enumerate(reader):
                if i >= max_rows:
                    break
                rows.append(dict(row))
            
            # Detecta mapeamento automático
            auto_mapping = self.detect_columns(columns)
            
            return {
                'columns': columns,
                'rows': rows,
                'total_rows': sum(1 for _ in csv.DictReader(io.StringIO(content), delimiter=delimiter)),
                'auto_mapping': auto_mapping,
                'delimiter': delimiter,
            }
        except Exception as e:
            return {
                'error': str(e),
                'columns': [],
                'rows': [],
                'total_rows': 0,
                'auto_mapping': {},
            }


def generate_sample_data(n_months: int = 24, scenario: str = "mixed") -> str:
    """Gera dados de exemplo em CSV."""
    import random
    from datetime import timedelta
    from dateutil.relativedelta import relativedelta
    
    random.seed(42)
    start_date = datetime(2023, 1, 1)
    
    rows = []
    base_fat = 500000
    base_custo_pct = 0.45
    base_desp_pct = 0.20
    base_imp_pct = 0.15
    base_folha_pct = 0.18
    caixa = 300000
    
    for month in range(n_months):
        dt = start_date + relativedelta(months=month)
        
        if scenario == "growth":
            growth = 1 + (month * 0.02)
            fat = base_fat * growth * random.uniform(0.95, 1.05)
        elif scenario == "decline":
            decline = max(0.3, 1 - (month * 0.03))
            fat = base_fat * decline * random.uniform(0.92, 1.02)
        elif scenario == "crisis":
            if month < 12:
                fat = base_fat * random.uniform(0.95, 1.05)
            else:
                decline = max(0.2, 1 - ((month - 12) * 0.08))
                fat = base_fat * decline * random.uniform(0.85, 0.98)
        else:  # mixed
            if month < 8:
                growth = 1 + (month * 0.015)
                fat = base_fat * growth * random.uniform(0.97, 1.03)
            elif month < 14:
                fat = base_fat * 1.12 * random.uniform(0.94, 1.02)
            else:
                decline = max(0.7, 1 - ((month - 14) * 0.025))
                fat = base_fat * 1.12 * decline * random.uniform(0.93, 1.01)
        
        custo_pct = base_custo_pct
        imp_pct = base_imp_pct
        
        if scenario == "mixed":
            if month >= 10:
                custo_pct = base_custo_pct + (month - 10) * 0.01
            if month in [15, 16, 17]:
                imp_pct = base_imp_pct * 1.4
        
        custos = fat * custo_pct * random.uniform(0.98, 1.02)
        despesas = fat * base_desp_pct * random.uniform(0.95, 1.05)
        impostos = fat * imp_pct * random.uniform(0.97, 1.03)
        folha = base_fat * base_folha_pct * (1 + month * 0.005) * random.uniform(0.99, 1.01)
        
        lucro = fat - custos - despesas - impostos - folha
        caixa = caixa + lucro * random.uniform(0.6, 0.9)
        
        rows.append({
            'Competência': dt.strftime('%Y-%m'),
            'Faturamento Bruto': f"{fat:.2f}",
            'Custo Mercadorias': f"{custos:.2f}",
            'Despesas Operacionais': f"{despesas:.2f}",
            'Tributos': f"{impostos:.2f}",
            'Folha Pagamento': f"{folha:.2f}",
            'Saldo Banco': f"{max(0, caixa):.2f}",
        })
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
