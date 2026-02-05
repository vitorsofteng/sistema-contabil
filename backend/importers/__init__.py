#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Importação Avançada - Sistema Contábil
=================================================

Suporta: CSV, OFX/QIF, XML NFe, PDF (balancetes)
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any, Type

from .base import (
    ImportadorBase, RegistroImportado, ResultadoImportacao,
    HistoricoImportacao, MapeamentoImportacao, RegistroImportadoDB
)
from .csv_importer import ImportadorCSV
from .ofx_importer import ImportadorOFX
from .nfe_importer import ImportadorNFe

# Importador de Balancetes (standalone, sem dependências pesadas)
try:
    from .balancete_standalone import (
        importar_balancete as _importar_balancete_interno,
        importar_balancete_bytes,
        ImportadorBalancete,
        DadosBalancete,
        ResultadoImportacao as ResultadoBalancete
    )
    BALANCETE_IMPORTER_AVAILABLE = True
except ImportError:
    BALANCETE_IMPORTER_AVAILABLE = False

# Importador Final de Balancetes (versão completa)
try:
    from .importador_balancete_final import (
        importar_balancete as importar_balancete_completo,
        importar_arquivo as importar_arquivo_balancete,
        ImportadorBalancete as ImportadorBalanceteFinal,
        BalanceteImportado,
        ResultadoImportacao as ResultadoImportacaoBalancete,
        ContaContabil,
        DadosEmpresa as DadosEmpresaBalancete
    )
    BALANCETE_FINAL_AVAILABLE = True
except ImportError:
    BALANCETE_FINAL_AVAILABLE = False

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import get_db, salvar_dados_mensais


# Registro de importadores disponíveis
IMPORTADORES: Dict[str, Type[ImportadorBase]] = {
    'csv': ImportadorCSV,
    'ofx': ImportadorOFX,
    'xml_nfe': ImportadorNFe
}

# Mapeamento de extensões
EXTENSAO_PARA_TIPO = {
    '.csv': 'csv',
    '.txt': 'csv',
    '.ofx': 'ofx',
    '.qif': 'ofx',
    '.qfx': 'ofx',
    '.xml': 'xml_nfe'
}


def detectar_tipo_arquivo(nome_arquivo: str, conteudo: bytes = None) -> str:
    """Detecta tipo do arquivo pela extensão ou conteúdo."""
    ext = os.path.splitext(nome_arquivo.lower())[1]
    
    if ext in EXTENSAO_PARA_TIPO:
        tipo = EXTENSAO_PARA_TIPO[ext]
        
        # Para XML, verifica se é realmente NFe
        if tipo == 'xml_nfe' and conteudo:
            texto = conteudo[:1000].decode('utf-8', errors='ignore').lower()
            if 'nfe' not in texto and 'nfse' not in texto and 'cte' not in texto:
                # XML genérico, trata como CSV (pode ser exportação de algum sistema)
                return 'csv'
        
        return tipo
    
    return 'csv'  # Fallback


def obter_importador(tipo: str, empresa_id: int = None) -> ImportadorBase:
    """Retorna instância do importador para o tipo."""
    if tipo not in IMPORTADORES:
        raise ValueError(f"Tipo de arquivo não suportado: {tipo}")
    
    return IMPORTADORES[tipo](empresa_id=empresa_id)


def preview_importacao(
    conteudo: bytes,
    nome_arquivo: str,
    empresa_id: int = None,
    mapeamento: Dict = None
) -> Dict:
    """
    Faz preview da importação sem salvar dados.
    Retorna colunas detectadas, mapeamento sugerido e preview dos registros.
    """
    tipo = detectar_tipo_arquivo(nome_arquivo, conteudo)
    importador = obter_importador(tipo, empresa_id)
    
    resultado = importador.processar(conteudo, nome_arquivo, mapeamento)
    
    # Limita preview a 20 registros
    preview_registros = []
    for reg in resultado.registros[:20]:
        preview_registros.append({
            'linha': reg.linha,
            'ano': reg.ano,
            'mes': reg.mes,
            'receita': reg.receita,
            'custos': reg.custos,
            'despesas': reg.despesas,
            'impostos': reg.impostos,
            'folha': reg.folha,
            'caixa': reg.caixa,
            'descricao': reg.descricao[:50] if reg.descricao else '',
            'erro': reg.erro,
            'is_duplicado': reg.is_duplicado
        })
    
    return {
        'tipo_arquivo': tipo,
        'colunas_detectadas': resultado.colunas_detectadas,
        'mapeamento_sugerido': resultado.mapeamento_sugerido,
        'total_registros': resultado.total_registros,
        'registros_validos': resultado.registros_importados,
        'registros_duplicados': resultado.registros_duplicados,
        'registros_erro': resultado.registros_erro,
        'preview': preview_registros,
        'erros': resultado.erros[:10],  # Primeiros 10 erros
        'periodo_inicio': resultado.periodo_inicio,
        'periodo_fim': resultado.periodo_fim
    }


def executar_importacao(
    conteudo: bytes,
    nome_arquivo: str,
    empresa_id: int,
    contador_id: int,
    organizacao_id: int = None,
    mapeamento: Dict = None,
    ignorar_duplicados: bool = True,
    modo_agregacao: str = 'substituir'  # substituir, somar, ignorar
) -> Dict:
    """
    Executa importação completa salvando dados no sistema.
    
    Args:
        conteudo: Bytes do arquivo
        nome_arquivo: Nome original do arquivo
        empresa_id: ID da empresa destino
        contador_id: ID do contador que está importando
        organizacao_id: ID da organização (opcional)
        mapeamento: Mapeamento de colunas personalizado
        ignorar_duplicados: Se True, ignora registros duplicados
        modo_agregacao: Como tratar dados existentes no mesmo período
    
    Returns:
        Dicionário com resultado da importação
    """
    tipo = detectar_tipo_arquivo(nome_arquivo, conteudo)
    importador = obter_importador(tipo, empresa_id)
    
    # Calcula hash do arquivo
    hash_arquivo = hashlib.sha256(conteudo).hexdigest()
    
    with get_db() as db:
        # Verifica se arquivo já foi importado
        importacao_existente = db.query(HistoricoImportacao).filter(
            HistoricoImportacao.empresa_id == empresa_id,
            HistoricoImportacao.hash_arquivo == hash_arquivo
        ).first()
        
        if importacao_existente:
            return {
                'sucesso': False,
                'erro': 'Este arquivo já foi importado anteriormente',
                'importacao_id': importacao_existente.id
            }
        
        # Cria registro de histórico
        historico = HistoricoImportacao(
            organizacao_id=organizacao_id,
            empresa_id=empresa_id,
            contador_id=contador_id,
            nome_arquivo=nome_arquivo,
            tipo_arquivo=tipo,
            tamanho_bytes=len(conteudo),
            hash_arquivo=hash_arquivo,
            status='processando',
            mapeamento_usado=json.dumps(mapeamento) if mapeamento else None
        )
        db.add(historico)
        db.flush()
        
        try:
            # Processa arquivo
            resultado = importador.processar(conteudo, nome_arquivo, mapeamento)
            
            # Agrupa registros por período (ano-mês)
            por_periodo = {}
            registros_salvos = 0
            registros_duplicados = 0
            erros = []
            
            for reg in resultado.registros:
                if reg.erro:
                    erros.append({'linha': reg.linha, 'erro': reg.erro})
                    continue
                
                if reg.is_duplicado and ignorar_duplicados:
                    registros_duplicados += 1
                    continue
                
                periodo = f"{reg.ano}-{reg.mes:02d}"
                
                if periodo not in por_periodo:
                    por_periodo[periodo] = {
                        'ano': reg.ano,
                        'mes': reg.mes,
                        'receita': 0,
                        'custos': 0,
                        'despesas': 0,
                        'impostos': 0,
                        'folha': 0,
                        'caixa': 0
                    }
                
                # Agrega valores
                por_periodo[periodo]['receita'] += reg.receita
                por_periodo[periodo]['custos'] += reg.custos
                por_periodo[periodo]['despesas'] += reg.despesas
                por_periodo[periodo]['impostos'] += reg.impostos
                por_periodo[periodo]['folha'] += reg.folha
                por_periodo[periodo]['caixa'] = reg.caixa  # Caixa não agrega, usa último
                
                # Registra para detecção de duplicatas
                reg_db = RegistroImportadoDB(
                    importacao_id=historico.id,
                    empresa_id=empresa_id,
                    hash_registro=reg.hash,
                    competencia=periodo,
                    tipo=reg.tipo or tipo,
                    dados_originais=json.dumps(reg.dados_originais)
                )
                db.add(reg_db)
            
            # Salva dados mensais agregados
            for periodo, dados in por_periodo.items():
                try:
                    salvar_dados_mensais(empresa_id, dados)
                    registros_salvos += 1
                except Exception as e:
                    erros.append({'periodo': periodo, 'erro': str(e)})
            
            # Atualiza histórico
            periodos_ordenados = sorted(por_periodo.keys())
            
            historico.status = 'sucesso' if not erros else ('parcial' if registros_salvos > 0 else 'erro')
            historico.total_registros = resultado.total_registros
            historico.registros_importados = registros_salvos
            historico.registros_duplicados = registros_duplicados
            historico.registros_erro = len(erros)
            historico.erros = json.dumps(erros[:50]) if erros else None
            historico.periodo_inicio = periodos_ordenados[0] if periodos_ordenados else None
            historico.periodo_fim = periodos_ordenados[-1] if periodos_ordenados else None
            historico.completed_at = datetime.now()
            
            return {
                'sucesso': historico.status in ('sucesso', 'parcial'),
                'importacao_id': historico.id,
                'total_registros': resultado.total_registros,
                'registros_importados': registros_salvos,
                'registros_duplicados': registros_duplicados,
                'registros_erro': len(erros),
                'periodos_afetados': list(por_periodo.keys()),
                'periodo_inicio': historico.periodo_inicio,
                'periodo_fim': historico.periodo_fim,
                'erros': erros[:10]
            }
            
        except Exception as e:
            historico.status = 'erro'
            historico.erros = json.dumps([{'erro': str(e)}])
            historico.completed_at = datetime.now()
            
            return {
                'sucesso': False,
                'importacao_id': historico.id,
                'erro': str(e)
            }


def listar_historico_importacoes(
    empresa_id: int = None,
    organizacao_id: int = None,
    limite: int = 20
) -> List[Dict]:
    """Lista histórico de importações."""
    with get_db() as db:
        query = db.query(HistoricoImportacao)
        
        if empresa_id:
            query = query.filter(HistoricoImportacao.empresa_id == empresa_id)
        elif organizacao_id:
            query = query.filter(HistoricoImportacao.organizacao_id == organizacao_id)
        
        historicos = query.order_by(
            HistoricoImportacao.created_at.desc()
        ).limit(limite).all()
        
        return [h.to_dict() for h in historicos]


def obter_importacao(importacao_id: int) -> Optional[Dict]:
    """Obtém detalhes de uma importação."""
    with get_db() as db:
        historico = db.query(HistoricoImportacao).filter(
            HistoricoImportacao.id == importacao_id
        ).first()
        
        return historico.to_dict() if historico else None


def salvar_mapeamento(
    nome: str,
    tipo_arquivo: str,
    mapeamento: Dict,
    contador_id: int,
    empresa_id: int = None,
    organizacao_id: int = None,
    is_default: bool = False
) -> Dict:
    """Salva um mapeamento para reutilização."""
    with get_db() as db:
        # Se marcado como default, desmarca outros
        if is_default:
            db.query(MapeamentoImportacao).filter(
                MapeamentoImportacao.empresa_id == empresa_id,
                MapeamentoImportacao.tipo_arquivo == tipo_arquivo
            ).update({'is_default': False})
        
        mapa = MapeamentoImportacao(
            organizacao_id=organizacao_id,
            empresa_id=empresa_id,
            contador_id=contador_id,
            nome=nome,
            tipo_arquivo=tipo_arquivo,
            mapeamento=json.dumps(mapeamento),
            is_default=is_default
        )
        db.add(mapa)
        db.flush()
        
        return mapa.to_dict()


def listar_mapeamentos(
    tipo_arquivo: str = None,
    empresa_id: int = None,
    organizacao_id: int = None
) -> List[Dict]:
    """Lista mapeamentos salvos."""
    with get_db() as db:
        query = db.query(MapeamentoImportacao)
        
        if tipo_arquivo:
            query = query.filter(MapeamentoImportacao.tipo_arquivo == tipo_arquivo)
        
        if empresa_id:
            query = query.filter(
                (MapeamentoImportacao.empresa_id == empresa_id) |
                (MapeamentoImportacao.empresa_id.is_(None))
            )
        
        if organizacao_id:
            query = query.filter(
                (MapeamentoImportacao.organizacao_id == organizacao_id) |
                (MapeamentoImportacao.organizacao_id.is_(None))
            )
        
        mapeamentos = query.order_by(
            MapeamentoImportacao.is_default.desc(),
            MapeamentoImportacao.nome
        ).all()
        
        return [m.to_dict() for m in mapeamentos]


def obter_mapeamento_padrao(
    tipo_arquivo: str,
    empresa_id: int = None
) -> Optional[Dict]:
    """Obtém mapeamento padrão para tipo de arquivo."""
    with get_db() as db:
        mapa = db.query(MapeamentoImportacao).filter(
            MapeamentoImportacao.tipo_arquivo == tipo_arquivo,
            MapeamentoImportacao.is_default == True
        )
        
        if empresa_id:
            mapa = mapa.filter(
                (MapeamentoImportacao.empresa_id == empresa_id) |
                (MapeamentoImportacao.empresa_id.is_(None))
            )
        
        mapa = mapa.first()
        return mapa.to_dict() if mapa else None


# ============================================================================
# IMPORTADOR DE BALANCETES (PDF)
# ============================================================================

def importar_balancete(conteudo: bytes, nome_arquivo: str) -> Dict:
    """
    Importa balancete de arquivo PDF.
    
    Extrai automaticamente:
    - CNPJ e dados da empresa
    - Período do balancete
    - Dados do contador
    - Balanço Patrimonial completo
    - DRE
    - Impostos
    - Indicadores financeiros
    - Sócios e Clientes
    
    Args:
        conteudo: Bytes do arquivo
        nome_arquivo: Nome original (para detectar tipo)
    
    Returns:
        Dicionário com resultado da importação e dados extraídos
    """
    # Usar novo importador final se disponível
    if BALANCETE_FINAL_AVAILABLE:
        try:
            resultado = importar_balancete_completo(conteudo, nome_arquivo)
            return resultado.to_dict()
        except Exception as e:
            pass
    
    # Fallback para importador antigo
    if not BALANCETE_IMPORTER_AVAILABLE:
        return {
            'sucesso': False,
            'mensagem': 'Importador de balancetes não disponível',
            'erro': 'Módulo não encontrado'
        }
    
    try:
        resultado = importar_balancete_bytes(conteudo, nome_arquivo)
        
        if not resultado.sucesso:
            return {
                'sucesso': False,
                'mensagem': resultado.mensagem,
                'erros': resultado.erros
            }
        
        dados = resultado.dados
        
        return {
            'sucesso': True,
            'mensagem': resultado.mensagem,
            'empresa': {
                'nome': dados.empresa.nome,
                'cnpj': dados.empresa.cnpj,
                'cnpj_formatado': dados.empresa.cnpj_formatado,
                'contador': dados.empresa.contador_nome,
                'crc': dados.empresa.contador_crc
            },
            'periodo': {
                'inicio': dados.periodo_inicio.isoformat() if dados.periodo_inicio else None,
                'fim': dados.periodo_fim.isoformat() if dados.periodo_fim else None,
                'mes': dados.periodo_fim.month if dados.periodo_fim else None,
                'ano': dados.periodo_fim.year if dados.periodo_fim else None
            },
            'dados': dados.to_dict(),
            'campos_mapeados': resultado.campos_mapeados,
            'avisos': resultado.avisos
        }
        
    except Exception as e:
        return {
            'sucesso': False,
            'mensagem': f'Erro ao importar balancete: {str(e)}',
            'erro': str(e)
        }


def importar_balancete_e_salvar(
    conteudo: bytes,
    nome_arquivo: str,
    contador_id: int,
    empresa_id: int = None
) -> Dict:
    """
    Importa balancete e salva no banco de dados.
    
    Se empresa_id não for informado, busca ou cria empresa pelo CNPJ.
    
    Args:
        conteudo: Bytes do arquivo
        nome_arquivo: Nome original
        contador_id: ID do contador que está importando
        empresa_id: ID da empresa (opcional)
    
    Returns:
        Dicionário com resultado e IDs
    """
    # Primeiro, importar e extrair dados
    resultado = importar_balancete(conteudo, nome_arquivo)
    
    if not resultado['sucesso']:
        return resultado
    
    dados = resultado['dados']
    empresa_info = resultado['empresa']
    periodo = resultado['periodo']
    
    # TODO: Integrar com banco de dados real
    # Por enquanto, retorna os dados extraídos
    
    return {
        'sucesso': True,
        'mensagem': f"Balancete importado: {empresa_info['nome']}",
        'empresa': empresa_info,
        'periodo': periodo,
        'dados_extraidos': dados,
        'campos_mapeados': resultado.get('campos_mapeados', []),
        'avisos': resultado.get('avisos', [])
    }


__all__ = [
    # Importadores
    'ImportadorBase', 'ImportadorCSV', 'ImportadorOFX', 'ImportadorNFe',
    
    # Funções principais
    'detectar_tipo_arquivo', 'obter_importador',
    'preview_importacao', 'executar_importacao',
    
    # Histórico
    'listar_historico_importacoes', 'obter_importacao',
    
    # Mapeamentos
    'salvar_mapeamento', 'listar_mapeamentos', 'obter_mapeamento_padrao',
    
    # Balancetes (PDF)
    'importar_balancete', 'importar_balancete_e_salvar',
    'BALANCETE_IMPORTER_AVAILABLE', 'BALANCETE_FINAL_AVAILABLE',
    'importar_balancete_completo', 'importar_arquivo_balancete',
    
    # Classes de dados
    'RegistroImportado', 'ResultadoImportacao',
    'HistoricoImportacao', 'MapeamentoImportacao'
]
