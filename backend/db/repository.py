#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repositório - Funções de Acesso ao Banco de Dados
=================================================

Usando SQLAlchemy ORM com:
- Soft delete
- Paginação
- Filtros dinâmicos
"""

import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy import select, update, delete, func, and_, or_, desc
from sqlalchemy.orm import Session, joinedload

from db.models import (
    Contador, Sessao, Empresa, DadosMensal, Analise,
    LoginAttempt, TokenBlacklist
)

# Importa segurança
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from auth.security import (
        hash_password, verify_password, validate_password_strength,
        create_access_token, create_refresh_token, decode_access_token,
        decode_refresh_token, AuthConfig
    )
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    import hashlib
    def hash_password(s): return hashlib.sha256(s.encode()).hexdigest()
    def verify_password(p, h): return hashlib.sha256(p.encode()).hexdigest() == h


# =============================================================================
# CONTADORES (USUÁRIOS)
# =============================================================================

def criar_contador(
    db: Session,
    nome: str,
    email: str,
    senha: str,
    telefone: str = None,
    crc: str = None
) -> Dict:
    """Cria um novo contador."""
    
    # Valida senha
    if SECURITY_AVAILABLE:
        validation = validate_password_strength(senha)
        if not validation.valid:
            raise ValueError("; ".join(validation.errors))
    
    # Verifica se email já existe
    existing = db.query(Contador).filter(
        Contador.email == email,
        Contador.deleted_at.is_(None)
    ).first()
    
    if existing:
        raise ValueError("Email já cadastrado")
    
    # Cria contador
    contador = Contador(
        nome=nome,
        email=email,
        senha_hash=hash_password(senha),
        telefone=telefone,
        crc=crc,
        password_changed_at=datetime.utcnow()
    )
    
    db.add(contador)
    db.flush()  # Obtém o ID
    
    # Gera tokens
    if SECURITY_AVAILABLE:
        access_token = create_access_token({"sub": str(contador.id)})
        refresh_token = create_refresh_token({"sub": str(contador.id)})
        access_payload = decode_access_token(access_token)
        refresh_payload = decode_refresh_token(refresh_token)
        
        # Cria sessão
        sessao = Sessao(
            contador_id=contador.id,
            token_jti=access_payload['jti'],
            refresh_token_jti=refresh_payload['jti'],
            expires_at=datetime.utcnow() + timedelta(minutes=15),
            refresh_expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.add(sessao)
    else:
        import secrets
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        
        sessao = Sessao(
            contador_id=contador.id,
            token_jti=access_token,
            refresh_token_jti=refresh_token,
            expires_at=datetime.utcnow() + timedelta(minutes=15),
            refresh_expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.add(sessao)
    
    db.commit()
    
    return {
        'id': contador.id,
        'nome': contador.nome,
        'email': contador.email,
        'telefone': contador.telefone,
        'crc': contador.crc,
        'token': access_token,
        'refresh_token': refresh_token,
        'expires_in': 900
    }


def autenticar_contador(
    db: Session,
    email: str,
    senha: str,
    ip: str = None
) -> Optional[Dict]:
    """Autentica um contador."""
    
    # Verifica rate limiting
    is_locked, remaining, seconds = verificar_bloqueio_login(db, email)
    if is_locked:
        raise ValueError(f"Conta bloqueada. Tente novamente em {seconds // 60 + 1} minutos.")
    
    # Busca contador
    contador = db.query(Contador).filter(
        Contador.email == email,
        Contador.ativo == True,
        Contador.deleted_at.is_(None)
    ).first()
    
    if not contador:
        registrar_tentativa_login(db, email, ip, False)
        return None
    
    # Verifica senha
    if not verify_password(senha, contador.senha_hash):
        registrar_tentativa_login(db, email, ip, False)
        
        _, remaining, _ = verificar_bloqueio_login(db, email)
        if remaining <= 2:
            raise ValueError(f"Senha incorreta. {remaining} tentativa(s) restante(s).")
        return None
    
    # Login OK - limpa tentativas
    limpar_tentativas_login(db, email)
    registrar_tentativa_login(db, email, ip, True)
    
    # Gera tokens
    if SECURITY_AVAILABLE:
        access_token = create_access_token({"sub": str(contador.id)})
        refresh_token = create_refresh_token({"sub": str(contador.id)})
        access_payload = decode_access_token(access_token)
        refresh_payload = decode_refresh_token(refresh_token)
        
        sessao = Sessao(
            contador_id=contador.id,
            token_jti=access_payload['jti'],
            refresh_token_jti=refresh_payload['jti'],
            ip_address=ip,
            expires_at=datetime.utcnow() + timedelta(minutes=15),
            refresh_expires_at=datetime.utcnow() + timedelta(days=7)
        )
    else:
        import secrets
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        
        sessao = Sessao(
            contador_id=contador.id,
            token_jti=access_token,
            refresh_token_jti=refresh_token,
            ip_address=ip,
            expires_at=datetime.utcnow() + timedelta(minutes=15),
            refresh_expires_at=datetime.utcnow() + timedelta(days=7)
        )
    
    db.add(sessao)
    db.commit()
    
    return {
        'id': contador.id,
        'nome': contador.nome,
        'email': contador.email,
        'telefone': contador.telefone,
        'crc': contador.crc,
        'token': access_token,
        'refresh_token': refresh_token,
        'expires_in': 900
    }


def validar_token(db: Session, token: str) -> Optional[Dict]:
    """Valida token e retorna dados do contador."""
    
    if SECURITY_AVAILABLE:
        payload = decode_access_token(token)
        if not payload:
            return None
        
        jti = payload.get('jti')
        
        # Verifica blacklist
        blacklisted = db.query(TokenBlacklist).filter(
            TokenBlacklist.jti == jti,
            TokenBlacklist.expires_at > datetime.utcnow()
        ).first()
        
        if blacklisted:
            return None
    else:
        jti = token
    
    # Busca sessão
    sessao = db.query(Sessao).filter(
        Sessao.token_jti == jti,
        Sessao.is_active == True
    ).first()
    
    if not sessao:
        return None
    
    # Busca contador
    contador = db.query(Contador).filter(
        Contador.id == sessao.contador_id,
        Contador.ativo == True,
        Contador.deleted_at.is_(None)
    ).first()
    
    if not contador:
        return None
    
    # Atualiza last_used_at
    sessao.last_used_at = datetime.utcnow()
    db.commit()
    
    return contador.to_dict()


def logout(db: Session, token: str):
    """Faz logout da sessão atual."""
    
    if SECURITY_AVAILABLE:
        payload = decode_access_token(token)
        if payload:
            jti = payload['jti']
            exp = datetime.utcfromtimestamp(payload.get('exp', 0))
            
            # Adiciona à blacklist
            blacklist = TokenBlacklist(jti=jti, expires_at=exp, reason="logout")
            db.add(blacklist)
            
            # Desativa sessão
            db.query(Sessao).filter(Sessao.token_jti == jti).update({"is_active": False})
    else:
        db.query(Sessao).filter(Sessao.token_jti == token).update({"is_active": False})
    
    db.commit()


def logout_all_devices(db: Session, user_id: int, current_token: str = None):
    """Faz logout de todos os dispositivos."""
    
    current_jti = None
    if current_token and SECURITY_AVAILABLE:
        payload = decode_access_token(current_token)
        current_jti = payload.get('jti') if payload else None
    
    # Busca todas as sessões ativas
    sessoes = db.query(Sessao).filter(
        Sessao.contador_id == user_id,
        Sessao.is_active == True
    ).all()
    
    for sessao in sessoes:
        if current_jti and sessao.token_jti == current_jti:
            continue
        
        # Adiciona à blacklist
        if sessao.token_jti:
            blacklist = TokenBlacklist(
                jti=sessao.token_jti,
                expires_at=sessao.expires_at or datetime.utcnow() + timedelta(hours=1),
                reason="logout_all"
            )
            db.add(blacklist)
        
        sessao.is_active = False
    
    db.commit()


# =============================================================================
# RATE LIMITING
# =============================================================================

def registrar_tentativa_login(db: Session, identifier: str, ip: str, success: bool):
    """Registra tentativa de login."""
    attempt = LoginAttempt(identifier=identifier, ip_address=ip, success=success)
    db.add(attempt)
    db.commit()


def verificar_bloqueio_login(db: Session, identifier: str) -> Tuple[bool, int, int]:
    """Verifica se está bloqueado por muitas tentativas."""
    
    cutoff = datetime.utcnow() - timedelta(minutes=15)
    
    failed_count = db.query(func.count(LoginAttempt.id)).filter(
        LoginAttempt.identifier == identifier,
        LoginAttempt.success == False,
        LoginAttempt.created_at > cutoff
    ).scalar()
    
    max_attempts = 5
    
    if failed_count >= max_attempts:
        # Pega última tentativa
        last = db.query(LoginAttempt).filter(
            LoginAttempt.identifier == identifier,
            LoginAttempt.success == False
        ).order_by(desc(LoginAttempt.created_at)).first()
        
        if last:
            unlock_time = last.created_at + timedelta(minutes=15)
            if unlock_time > datetime.utcnow():
                remaining = int((unlock_time - datetime.utcnow()).total_seconds())
                return True, 0, remaining
    
    return False, max_attempts - failed_count, 0


def limpar_tentativas_login(db: Session, identifier: str):
    """Limpa tentativas após login bem-sucedido."""
    db.query(LoginAttempt).filter(LoginAttempt.identifier == identifier).delete()
    db.commit()


# =============================================================================
# EMPRESAS
# =============================================================================

def criar_empresa(db: Session, contador_id: int, dados: Dict) -> int:
    """Cria uma nova empresa."""
    
    empresa = Empresa(
        contador_id=contador_id,
        razao_social=dados.get('razao_social'),
        nome_fantasia=dados.get('nome_fantasia'),
        cnpj=dados.get('cnpj'),
        inscricao_estadual=dados.get('inscricao_estadual'),
        regime_tributario=dados.get('regime_tributario'),
        setor=dados.get('setor'),
        endereco=dados.get('endereco'),
        cidade=dados.get('cidade'),
        estado=dados.get('estado'),
        telefone=dados.get('telefone'),
        email=dados.get('email'),
        contato_nome=dados.get('contato_nome'),
        observacoes=dados.get('observacoes')
    )
    
    db.add(empresa)
    db.commit()
    
    return empresa.id


def listar_empresas(
    db: Session,
    contador_id: int,
    apenas_ativas: bool = True,
    search: str = None
) -> List[Dict]:
    """Lista empresas do contador com estatísticas."""
    
    query = db.query(Empresa).filter(
        Empresa.contador_id == contador_id,
        Empresa.deleted_at.is_(None)
    )
    
    if apenas_ativas:
        query = query.filter(Empresa.ativo == True)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Empresa.razao_social.ilike(search_term),
                Empresa.nome_fantasia.ilike(search_term),
                Empresa.cnpj.ilike(search_term)
            )
        )
    
    empresas = query.order_by(Empresa.razao_social).all()
    
    result = []
    for emp in empresas:
        emp_dict = emp.to_dict()
        
        # Conta meses de dados
        meses_dados = db.query(func.count(DadosMensal.id)).filter(
            DadosMensal.empresa_id == emp.id,
            DadosMensal.deleted_at.is_(None)
        ).scalar()
        emp_dict['meses_dados'] = meses_dados
        
        # Última análise
        ultima = db.query(Analise).filter(
            Analise.empresa_id == emp.id
        ).order_by(desc(Analise.data_analise)).first()
        
        if ultima:
            emp_dict['ultimo_score'] = ultima.score
            emp_dict['ultimo_status'] = ultima.status
        else:
            emp_dict['ultimo_score'] = None
            emp_dict['ultimo_status'] = None
        
        result.append(emp_dict)
    
    return result


def obter_empresa(db: Session, empresa_id: int, contador_id: int) -> Optional[Dict]:
    """Obtém uma empresa específica."""
    
    empresa = db.query(Empresa).filter(
        Empresa.id == empresa_id,
        Empresa.contador_id == contador_id,
        Empresa.deleted_at.is_(None)
    ).first()
    
    if not empresa:
        return None
    
    return empresa.to_dict()


def atualizar_empresa(db: Session, empresa_id: int, contador_id: int, dados: Dict):
    """Atualiza uma empresa."""
    
    empresa = db.query(Empresa).filter(
        Empresa.id == empresa_id,
        Empresa.contador_id == contador_id,
        Empresa.deleted_at.is_(None)
    ).first()
    
    if not empresa:
        return False
    
    for key, value in dados.items():
        if hasattr(empresa, key) and value is not None:
            setattr(empresa, key, value)
    
    db.commit()
    return True


def excluir_empresa(db: Session, empresa_id: int, contador_id: int, soft: bool = True):
    """Exclui uma empresa (soft delete por padrão)."""
    
    empresa = db.query(Empresa).filter(
        Empresa.id == empresa_id,
        Empresa.contador_id == contador_id
    ).first()
    
    if not empresa:
        return False
    
    if soft:
        empresa.soft_delete()
        empresa.ativo = False
    else:
        db.delete(empresa)
    
    db.commit()
    return True


# =============================================================================
# DADOS MENSAIS
# =============================================================================

def salvar_dados_mensais(db: Session, empresa_id: int, dados: Dict) -> int:
    """Salva ou atualiza dados mensais."""
    
    # Verifica se já existe
    existing = db.query(DadosMensal).filter(
        DadosMensal.empresa_id == empresa_id,
        DadosMensal.ano == dados['ano'],
        DadosMensal.mes == dados['mes'],
        DadosMensal.deleted_at.is_(None)
    ).first()
    
    if existing:
        # Atualiza
        for key, value in dados.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
        db.commit()
        return existing.id
    else:
        # Cria novo
        dado = DadosMensal(
            empresa_id=empresa_id,
            ano=dados['ano'],
            mes=dados['mes'],
            receita=dados.get('receita', 0),
            custos=dados.get('custos', 0),
            despesas=dados.get('despesas', 0),
            impostos=dados.get('impostos', 0),
            folha=dados.get('folha', 0),
            caixa=dados.get('caixa', 0),
            observacoes=dados.get('observacoes')
        )
        db.add(dado)
        db.commit()
        return dado.id


def listar_dados_mensais(
    db: Session,
    empresa_id: int,
    limite: int = 36
) -> List[Dict]:
    """Lista dados mensais de uma empresa."""
    
    dados = db.query(DadosMensal).filter(
        DadosMensal.empresa_id == empresa_id,
        DadosMensal.deleted_at.is_(None)
    ).order_by(
        desc(DadosMensal.ano),
        desc(DadosMensal.mes)
    ).limit(limite).all()
    
    return [d.to_dict() for d in dados]


def obter_dados_para_analise(db: Session, empresa_id: int) -> List[Dict]:
    """Obtém dados para análise (ordenados cronologicamente)."""
    
    dados = db.query(DadosMensal).filter(
        DadosMensal.empresa_id == empresa_id,
        DadosMensal.deleted_at.is_(None)
    ).order_by(
        DadosMensal.ano,
        DadosMensal.mes
    ).all()
    
    return [d.to_dict() for d in dados]


def excluir_dados_mensais(db: Session, empresa_id: int, ano: int, mes: int, soft: bool = True):
    """Exclui dados mensais."""
    
    dado = db.query(DadosMensal).filter(
        DadosMensal.empresa_id == empresa_id,
        DadosMensal.ano == ano,
        DadosMensal.mes == mes
    ).first()
    
    if not dado:
        return False
    
    if soft:
        dado.soft_delete()
    else:
        db.delete(dado)
    
    db.commit()
    return True


# =============================================================================
# ANÁLISES
# =============================================================================

def salvar_analise(db: Session, empresa_id: int, resultado: Dict) -> int:
    """Salva uma análise."""
    
    analise = Analise(
        empresa_id=empresa_id,
        periodo_inicio=resultado.get('periodo_inicio'),
        periodo_fim=resultado.get('periodo_fim'),
        meses_analisados=resultado.get('meses_analisados'),
        score=resultado.get('score'),
        score_confianca=resultado.get('score_confianca'),
        status=resultado.get('status'),
        resultado_json=json.dumps(resultado)
    )
    
    db.add(analise)
    db.commit()
    
    return analise.id


def listar_analises(db: Session, empresa_id: int, limite: int = 10) -> List[Dict]:
    """Lista análises de uma empresa."""
    
    analises = db.query(Analise).filter(
        Analise.empresa_id == empresa_id
    ).order_by(desc(Analise.data_analise)).limit(limite).all()
    
    result = []
    for a in analises:
        a_dict = a.to_dict()
        
        # Extrai scores do resultado
        resultado = a_dict.get('resultado_completo', {})
        score_det = resultado.get('score_detalhado', {})
        
        a_dict['score_tendencia'] = score_det.get('tendencia', 0)
        a_dict['score_margem'] = score_det.get('margem', 0)
        a_dict['score_caixa'] = score_det.get('caixa', 0)
        a_dict['score_estabilidade'] = score_det.get('estabilidade', 0)
        a_dict['score_anomalias'] = score_det.get('anomalias', 0)
        a_dict['insights'] = resultado.get('insights', [])
        a_dict['recomendacao_principal'] = resultado.get('recomendacao_principal', '')
        
        result.append(a_dict)
    
    return result


def obter_analise(db: Session, analise_id: int, empresa_id: int) -> Optional[Dict]:
    """Obtém uma análise específica."""
    
    analise = db.query(Analise).filter(
        Analise.id == analise_id,
        Analise.empresa_id == empresa_id
    ).first()
    
    if not analise:
        return None
    
    a_dict = analise.to_dict()
    resultado = a_dict.get('resultado_completo', {})
    score_det = resultado.get('score_detalhado', {})
    
    a_dict['score_tendencia'] = score_det.get('tendencia', 0)
    a_dict['score_margem'] = score_det.get('margem', 0)
    a_dict['score_caixa'] = score_det.get('caixa', 0)
    a_dict['score_estabilidade'] = score_det.get('estabilidade', 0)
    a_dict['score_anomalias'] = score_det.get('anomalias', 0)
    a_dict['insights'] = resultado.get('insights', [])
    a_dict['recomendacao_principal'] = resultado.get('recomendacao_principal', '')
    a_dict['resultado'] = resultado  # Para compatibilidade
    
    return a_dict


def obter_ultima_analise(db: Session, empresa_id: int) -> Optional[Dict]:
    """Obtém a última análise de uma empresa."""
    
    analise = db.query(Analise).filter(
        Analise.empresa_id == empresa_id
    ).order_by(desc(Analise.data_analise)).first()
    
    if not analise:
        return None
    
    return obter_analise(db, analise.id, empresa_id)


# =============================================================================
# ESTATÍSTICAS
# =============================================================================

def obter_estatisticas_contador(db: Session, contador_id: int) -> Dict:
    """Obtém estatísticas do dashboard."""
    
    # Total de empresas
    total_empresas = db.query(func.count(Empresa.id)).filter(
        Empresa.contador_id == contador_id,
        Empresa.ativo == True,
        Empresa.deleted_at.is_(None)
    ).scalar()
    
    # Empresas por status
    empresas = listar_empresas(db, contador_id)
    
    saudaveis = sum(1 for e in empresas if e.get('ultimo_status') == 'saudavel')
    atencao = sum(1 for e in empresas if e.get('ultimo_status') == 'atencao')
    criticos = sum(1 for e in empresas if e.get('ultimo_status') == 'critico')
    sem_analise = sum(1 for e in empresas if not e.get('ultimo_status'))
    
    return {
        'total_empresas': total_empresas,
        'empresas_saudaveis': saudaveis,
        'empresas_atencao': atencao,
        'empresas_criticas': criticos,
        'empresas_sem_analise': sem_analise
    }
