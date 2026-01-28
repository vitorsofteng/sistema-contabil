"""
Testes End-to-End (E2E) - Fluxos Completos
Sprint 4 - Sistema Contábil

Estes testes validam fluxos completos de uso do sistema,
simulando cenários reais de um contador utilizando a aplicação.
"""

import pytest
import time
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta


# ============================================================================
# SIMULADOR DE SISTEMA COMPLETO
# ============================================================================

class ContabilSystemSimulator:
    """Simulador completo do sistema contábil para testes E2E."""
    
    def __init__(self):
        # Dados
        self.users = {}
        self.empresas = {}
        self.dados_mensais = {}
        self.analises = {}
        self.alertas = {}
        self.relatorios = {}
        self.sessoes = {}
        
        # Contadores
        self._counters = {
            "user": 0,
            "empresa": 0,
            "dados": 0,
            "analise": 0,
            "alerta": 0,
            "relatorio": 0
        }
        
        # Sessão atual
        self.current_user = None
        self.current_token = None
    
    def _next_id(self, entity: str) -> int:
        self._counters[entity] += 1
        return self._counters[entity]
    
    # ===== AUTENTICAÇÃO =====
    
    def registrar(self, nome: str, email: str, senha: str) -> Dict:
        """Registra novo usuário."""
        # Verificar email duplicado
        for user in self.users.values():
            if user["email"] == email:
                raise ValueError("Email já cadastrado")
        
        # Validar senha
        if len(senha) < 8:
            raise ValueError("Senha deve ter no mínimo 8 caracteres")
        
        user_id = self._next_id("user")
        self.users[user_id] = {
            "id": user_id,
            "nome": nome,
            "email": email,
            "senha": senha,
            "criado_em": datetime.now(),
            "ativo": True,
            "plano": "free"
        }
        
        return self.users[user_id]
    
    def login(self, email: str, senha: str) -> str:
        """Faz login e retorna token."""
        for user in self.users.values():
            if user["email"] == email and user["senha"] == senha:
                token = f"token_{user['id']}_{int(time.time())}"
                self.sessoes[token] = {
                    "user_id": user["id"],
                    "criado_em": datetime.now(),
                    "ativo": True
                }
                self.current_user = user
                self.current_token = token
                return token
        
        raise ValueError("Credenciais inválidas")
    
    def logout(self):
        """Faz logout."""
        if self.current_token and self.current_token in self.sessoes:
            self.sessoes[self.current_token]["ativo"] = False
        self.current_user = None
        self.current_token = None
    
    def _check_auth(self):
        """Verifica se está autenticado."""
        if not self.current_user:
            raise PermissionError("Não autenticado")
    
    # ===== EMPRESAS =====
    
    def criar_empresa(self, nome: str, cnpj: str = None, 
                      segmento: str = None, porte: str = None) -> Dict:
        """Cria nova empresa."""
        self._check_auth()
        
        empresa_id = self._next_id("empresa")
        self.empresas[empresa_id] = {
            "id": empresa_id,
            "nome": nome,
            "cnpj": cnpj,
            "segmento": segmento,
            "porte": porte,
            "contador_id": self.current_user["id"],
            "criado_em": datetime.now(),
            "ativo": True
        }
        
        return self.empresas[empresa_id]
    
    def listar_empresas(self) -> List[Dict]:
        """Lista empresas do contador logado."""
        self._check_auth()
        return [e for e in self.empresas.values() 
                if e["contador_id"] == self.current_user["id"] and e["ativo"]]
    
    def obter_empresa(self, empresa_id: int) -> Dict:
        """Obtém empresa específica."""
        self._check_auth()
        empresa = self.empresas.get(empresa_id)
        
        if not empresa or not empresa["ativo"]:
            raise ValueError("Empresa não encontrada")
        
        if empresa["contador_id"] != self.current_user["id"]:
            raise PermissionError("Acesso negado")
        
        return empresa
    
    def excluir_empresa(self, empresa_id: int):
        """Exclui empresa (soft delete)."""
        empresa = self.obter_empresa(empresa_id)
        empresa["ativo"] = False
    
    # ===== DADOS MENSAIS =====
    
    def lancar_dados(self, empresa_id: int, mes: int, ano: int, 
                     dados: Dict) -> Dict:
        """Lança dados mensais de uma empresa."""
        self.obter_empresa(empresa_id)  # Verifica acesso
        
        dados_id = self._next_id("dados")
        key = f"{empresa_id}_{ano}_{mes}"
        
        registro = {
            "id": dados_id,
            "empresa_id": empresa_id,
            "mes": mes,
            "ano": ano,
            "criado_em": datetime.now(),
            **dados
        }
        
        self.dados_mensais[key] = registro
        return registro
    
    def obter_dados_empresa(self, empresa_id: int) -> List[Dict]:
        """Obtém todos os dados mensais de uma empresa."""
        self.obter_empresa(empresa_id)  # Verifica acesso
        
        dados = [d for d in self.dados_mensais.values() 
                 if d["empresa_id"] == empresa_id]
        return sorted(dados, key=lambda x: (x["ano"], x["mes"]))
    
    # ===== ANÁLISE =====
    
    def gerar_analise(self, empresa_id: int) -> Dict:
        """Gera análise financeira."""
        empresa = self.obter_empresa(empresa_id)
        dados = self.obter_dados_empresa(empresa_id)
        
        if len(dados) < 3:
            raise ValueError("Necessário pelo menos 3 meses de dados")
        
        # Calcular indicadores (último período)
        ultimo = dados[-1]
        
        margem_bruta = ((ultimo["receita_bruta"] - ultimo["custos"]) / 
                        ultimo["receita_bruta"]) * 100 if ultimo["receita_bruta"] > 0 else 0
        
        margem_liquida = (ultimo["lucro_liquido"] / 
                         ultimo["receita_bruta"]) * 100 if ultimo["receita_bruta"] > 0 else 0
        
        liquidez = (ultimo["ativo_circulante"] / 
                   ultimo["passivo_circulante"]) if ultimo["passivo_circulante"] > 0 else 0
        
        endividamento = (ultimo["passivo_total"] / 
                        ultimo["ativo_total"]) * 100 if ultimo["ativo_total"] > 0 else 0
        
        # Calcular score (simplificado)
        score = 0
        if margem_liquida >= 10: score += 25
        elif margem_liquida >= 5: score += 15
        elif margem_liquida >= 0: score += 5
        
        if liquidez >= 2.0: score += 25
        elif liquidez >= 1.5: score += 20
        elif liquidez >= 1.0: score += 10
        
        if endividamento <= 40: score += 25
        elif endividamento <= 60: score += 15
        elif endividamento <= 80: score += 5
        
        roa = (ultimo["lucro_liquido"] / ultimo["ativo_total"]) * 100 if ultimo["ativo_total"] > 0 else 0
        if roa >= 10: score += 25
        elif roa >= 5: score += 15
        elif roa >= 2: score += 5
        
        # Classificação
        if score >= 80:
            classificacao = "excelente"
        elif score >= 60:
            classificacao = "bom"
        elif score >= 40:
            classificacao = "regular"
        else:
            classificacao = "critico"
        
        # Gerar alertas
        alertas = []
        
        if liquidez < 1.0:
            alertas.append({
                "nivel": "critico",
                "indicador": "liquidez_corrente",
                "mensagem": "Liquidez corrente abaixo de 1,0"
            })
        
        if margem_liquida < 0:
            alertas.append({
                "nivel": "critico",
                "indicador": "margem_liquida",
                "mensagem": "Margem líquida negativa"
            })
        
        if endividamento > 80:
            alertas.append({
                "nivel": "atencao",
                "indicador": "endividamento",
                "mensagem": "Endividamento acima de 80%"
            })
        
        # Calcular tendência
        if len(dados) >= 3:
            receitas = [d["receita_bruta"] for d in dados[-3:]]
            if receitas[-1] > receitas[0]:
                tendencia = "crescimento"
            elif receitas[-1] < receitas[0]:
                tendencia = "queda"
            else:
                tendencia = "estavel"
        else:
            tendencia = "indeterminada"
        
        analise_id = self._next_id("analise")
        analise = {
            "id": analise_id,
            "empresa_id": empresa_id,
            "empresa_nome": empresa["nome"],
            "periodo": f"{ultimo['mes']:02d}/{ultimo['ano']}",
            "indicadores": {
                "margem_bruta": round(margem_bruta, 2),
                "margem_liquida": round(margem_liquida, 2),
                "liquidez_corrente": round(liquidez, 2),
                "endividamento": round(endividamento, 2),
                "roa": round(roa, 2)
            },
            "score": score,
            "classificacao": classificacao,
            "tendencia": tendencia,
            "alertas": alertas,
            "total_meses_analisados": len(dados),
            "gerado_em": datetime.now()
        }
        
        self.analises[analise_id] = analise
        return analise
    
    # ===== RELATÓRIOS =====
    
    def gerar_relatorio(self, empresa_id: int, tipo: str = "completo") -> Dict:
        """Gera relatório para a empresa."""
        analise = self.gerar_analise(empresa_id)
        empresa = self.obter_empresa(empresa_id)
        
        relatorio_id = self._next_id("relatorio")
        relatorio = {
            "id": relatorio_id,
            "empresa_id": empresa_id,
            "empresa_nome": empresa["nome"],
            "tipo": tipo,
            "analise": analise,
            "gerado_em": datetime.now(),
            "gerado_por": self.current_user["nome"]
        }
        
        self.relatorios[relatorio_id] = relatorio
        return relatorio
    
    # ===== DASHBOARD =====
    
    def obter_dashboard(self) -> Dict:
        """Obtém dados do dashboard."""
        self._check_auth()
        
        empresas = self.listar_empresas()
        
        # Estatísticas
        total_empresas = len(empresas)
        
        # Análises recentes
        analises_recentes = [
            a for a in self.analises.values()
            if a["empresa_id"] in [e["id"] for e in empresas]
        ]
        
        # Contagem por classificação
        classificacoes = {"excelente": 0, "bom": 0, "regular": 0, "critico": 0}
        for analise in analises_recentes:
            classificacoes[analise["classificacao"]] += 1
        
        # Alertas pendentes
        alertas_pendentes = []
        for analise in analises_recentes:
            for alerta in analise.get("alertas", []):
                alertas_pendentes.append({
                    **alerta,
                    "empresa": analise["empresa_nome"]
                })
        
        return {
            "total_empresas": total_empresas,
            "classificacoes": classificacoes,
            "alertas_pendentes": alertas_pendentes,
            "total_alertas": len(alertas_pendentes)
        }


# ============================================================================
# TESTES E2E - FLUXO DE ONBOARDING
# ============================================================================

class TestOnboardingFlow:
    """Testes E2E para fluxo de onboarding de novo contador."""
    
    @pytest.fixture
    def sistema(self):
        return ContabilSystemSimulator()
    
    def test_fluxo_completo_novo_contador(self, sistema):
        """
        Cenário: Novo contador se cadastra e começa a usar o sistema.
        
        1. Registro
        2. Login
        3. Criar primeira empresa
        4. Lançar dados de 6 meses
        5. Gerar análise
        6. Verificar dashboard
        """
        # 1. Registro
        user = sistema.registrar(
            nome="Maria Silva",
            email="maria@contabil.com",
            senha="Senha@123"
        )
        assert user["id"] is not None
        assert user["nome"] == "Maria Silva"
        
        # 2. Login
        token = sistema.login("maria@contabil.com", "Senha@123")
        assert token is not None
        assert sistema.current_user is not None
        
        # 3. Criar empresa
        empresa = sistema.criar_empresa(
            nome="Padaria Doce Pão LTDA",
            cnpj="12.345.678/0001-90",
            segmento="Comércio",
            porte="Pequena"
        )
        assert empresa["id"] is not None
        
        # 4. Lançar 6 meses de dados
        dados_base = {
            "despesas_operacionais": 15000,
            "despesas_financeiras": 2000,
            "impostos": 3000,
            "ativo_total": 300000,
            "ativo_circulante": 120000,
            "passivo_total": 150000,
            "passivo_circulante": 80000,
            "patrimonio_liquido": 150000,
            "disponivel": 30000
        }
        
        meses_dados = [
            {"mes": 1, "receita_bruta": 80000, "custos": 50000, "lucro_liquido": 10000},
            {"mes": 2, "receita_bruta": 85000, "custos": 52000, "lucro_liquido": 13000},
            {"mes": 3, "receita_bruta": 82000, "custos": 51000, "lucro_liquido": 11000},
            {"mes": 4, "receita_bruta": 90000, "custos": 54000, "lucro_liquido": 16000},
            {"mes": 5, "receita_bruta": 88000, "custos": 53000, "lucro_liquido": 15000},
            {"mes": 6, "receita_bruta": 95000, "custos": 56000, "lucro_liquido": 19000},
        ]
        
        for dados in meses_dados:
            sistema.lancar_dados(
                empresa_id=empresa["id"],
                mes=dados["mes"],
                ano=2024,
                dados={**dados_base, **dados}
            )
        
        # 5. Gerar análise
        analise = sistema.gerar_analise(empresa["id"])
        
        assert analise["score"] > 0
        assert analise["classificacao"] in ["excelente", "bom", "regular", "critico"]
        assert "indicadores" in analise
        assert analise["tendencia"] == "crescimento"  # Receita crescendo
        
        # 6. Verificar dashboard
        dashboard = sistema.obter_dashboard()
        
        assert dashboard["total_empresas"] == 1
        assert sum(dashboard["classificacoes"].values()) == 1


# ============================================================================
# TESTES E2E - FLUXO DE ANÁLISE MENSAL
# ============================================================================

class TestAnalysisFlow:
    """Testes E2E para fluxo de análise mensal."""
    
    @pytest.fixture
    def sistema_com_empresa(self):
        """Sistema com empresa já configurada."""
        sistema = ContabilSystemSimulator()
        sistema.registrar("Contador", "contador@teste.com", "Senha@123")
        sistema.login("contador@teste.com", "Senha@123")
        
        empresa = sistema.criar_empresa(
            nome="Empresa Teste",
            cnpj="11.111.111/0001-11",
            segmento="Serviços",
            porte="Média"
        )
        
        # Lançar 6 meses de dados
        dados_base = {
            "despesas_operacionais": 20000,
            "despesas_financeiras": 5000,
            "impostos": 4000,
            "ativo_total": 500000,
            "ativo_circulante": 200000,
            "passivo_total": 250000,
            "passivo_circulante": 100000,
            "patrimonio_liquido": 250000,
            "disponivel": 50000
        }
        
        for i in range(6):
            sistema.lancar_dados(
                empresa_id=empresa["id"],
                mes=i + 1,
                ano=2024,
                dados={
                    **dados_base,
                    "receita_bruta": 100000 + (i * 5000),
                    "custos": 60000 + (i * 2000),
                    "lucro_liquido": 11000 + (i * 1500)
                }
            )
        
        return sistema, empresa["id"]
    
    def test_analise_empresa_saudavel(self, sistema_com_empresa):
        """Empresa saudável deve ter boa classificação."""
        sistema, empresa_id = sistema_com_empresa
        
        analise = sistema.gerar_analise(empresa_id)
        
        assert analise["classificacao"] in ["excelente", "bom"]
        assert analise["score"] >= 60
        assert len(analise["alertas"]) == 0  # Sem alertas críticos
    
    def test_geracao_relatorio(self, sistema_com_empresa):
        """Deve gerar relatório com análise."""
        sistema, empresa_id = sistema_com_empresa
        
        relatorio = sistema.gerar_relatorio(empresa_id, tipo="completo")
        
        assert relatorio["tipo"] == "completo"
        assert "analise" in relatorio
        assert relatorio["gerado_por"] == "Contador"


# ============================================================================
# TESTES E2E - FLUXO DE ALERTAS
# ============================================================================

class TestAlertFlow:
    """Testes E2E para fluxo de alertas."""
    
    @pytest.fixture
    def sistema(self):
        return ContabilSystemSimulator()
    
    def test_alertas_empresa_critica(self, sistema):
        """Empresa em situação crítica deve gerar alertas."""
        # Setup
        sistema.registrar("Contador", "contador@teste.com", "Senha@123")
        sistema.login("contador@teste.com", "Senha@123")
        
        empresa = sistema.criar_empresa(
            nome="Empresa em Crise",
            cnpj="99.999.999/0001-99"
        )
        
        # Dados críticos (prejuízo, baixa liquidez, alto endividamento)
        dados_criticos = {
            "receita_bruta": 50000,
            "custos": 60000,  # Custo maior que receita
            "lucro_liquido": -15000,  # Prejuízo
            "despesas_operacionais": 5000,
            "despesas_financeiras": 2000,
            "impostos": 0,
            "ativo_total": 100000,
            "ativo_circulante": 30000,
            "passivo_total": 90000,  # 90% endividamento
            "passivo_circulante": 50000,  # Liquidez < 1
            "patrimonio_liquido": 10000,
            "disponivel": 5000
        }
        
        for mes in range(1, 7):
            sistema.lancar_dados(empresa["id"], mes, 2024, dados_criticos)
        
        # Gerar análise
        analise = sistema.gerar_analise(empresa["id"])
        
        # Verificar alertas
        assert analise["classificacao"] == "critico"
        assert len(analise["alertas"]) >= 2
        
        # Verificar tipos de alertas
        niveis = [a["nivel"] for a in analise["alertas"]]
        assert "critico" in niveis
        
        # Dashboard deve mostrar alertas
        dashboard = sistema.obter_dashboard()
        assert dashboard["total_alertas"] >= 2


# ============================================================================
# TESTES E2E - FLUXO MULTI-EMPRESA
# ============================================================================

class TestMultiCompanyFlow:
    """Testes E2E para gestão de múltiplas empresas."""
    
    @pytest.fixture
    def sistema(self):
        return ContabilSystemSimulator()
    
    def test_contador_com_multiplas_empresas(self, sistema):
        """Contador gerenciando múltiplas empresas."""
        # Setup
        sistema.registrar("Contador Multi", "multi@contabil.com", "Senha@123")
        sistema.login("multi@contabil.com", "Senha@123")
        
        empresas = []
        
        # Criar 5 empresas com diferentes situações
        configuracoes = [
            {"nome": "Empresa Excelente", "margem": 20, "liquidez": 2.5, "endiv": 30},
            {"nome": "Empresa Boa", "margem": 12, "liquidez": 1.8, "endiv": 45},
            {"nome": "Empresa Regular", "margem": 5, "liquidez": 1.2, "endiv": 60},
            {"nome": "Empresa Atenção", "margem": 2, "liquidez": 0.9, "endiv": 75},
            {"nome": "Empresa Crítica", "margem": -5, "liquidez": 0.5, "endiv": 90},
        ]
        
        for i, config in enumerate(configuracoes):
            empresa = sistema.criar_empresa(
                nome=config["nome"],
                cnpj=f"{i+1}{i+1}.{i+1}{i+1}{i+1}.{i+1}{i+1}{i+1}/0001-{i+1}{i+1}"
            )
            empresas.append(empresa)
            
            # Lançar dados ajustados
            receita = 100000
            custos = receita * (1 - config["margem"]/100) - 20000  # Ajustar para margem desejada
            ativo_total = 500000
            passivo_total = ativo_total * (config["endiv"]/100)
            passivo_circ = passivo_total * 0.4
            ativo_circ = passivo_circ * config["liquidez"]
            
            for mes in range(1, 7):
                sistema.lancar_dados(
                    empresa_id=empresa["id"],
                    mes=mes,
                    ano=2024,
                    dados={
                        "receita_bruta": receita,
                        "custos": custos,
                        "lucro_liquido": receita * (config["margem"]/100),
                        "despesas_operacionais": 15000,
                        "despesas_financeiras": 5000,
                        "impostos": 3000,
                        "ativo_total": ativo_total,
                        "ativo_circulante": ativo_circ,
                        "passivo_total": passivo_total,
                        "passivo_circulante": passivo_circ,
                        "patrimonio_liquido": ativo_total - passivo_total,
                        "disponivel": ativo_circ * 0.3
                    }
                )
        
        # Gerar análises
        for empresa in empresas:
            sistema.gerar_analise(empresa["id"])
        
        # Verificar dashboard
        dashboard = sistema.obter_dashboard()
        
        assert dashboard["total_empresas"] == 5
        assert sum(dashboard["classificacoes"].values()) == 5
        assert dashboard["classificacoes"]["critico"] >= 1
        assert dashboard["classificacoes"]["excelente"] >= 1


# ============================================================================
# TESTES E2E - FLUXO DE SESSÃO
# ============================================================================

class TestSessionFlow:
    """Testes E2E para gerenciamento de sessão."""
    
    @pytest.fixture
    def sistema(self):
        return ContabilSystemSimulator()
    
    def test_sessao_completa(self, sistema):
        """Fluxo completo de sessão: login → operações → logout."""
        # Registro
        sistema.registrar("Usuário Teste", "teste@teste.com", "Senha@123")
        
        # Login
        token = sistema.login("teste@teste.com", "Senha@123")
        assert sistema.current_user is not None
        
        # Criar empresa (operação autenticada)
        empresa = sistema.criar_empresa("Empresa Sessão")
        assert empresa is not None
        
        # Logout
        sistema.logout()
        assert sistema.current_user is None
        
        # Tentar operação após logout deve falhar
        with pytest.raises(PermissionError):
            sistema.criar_empresa("Outra Empresa")
    
    def test_isolamento_entre_sessoes(self, sistema):
        """Cada contador só vê seus dados."""
        # Contador 1
        sistema.registrar("Contador 1", "c1@teste.com", "Senha@123")
        sistema.login("c1@teste.com", "Senha@123")
        empresa1 = sistema.criar_empresa("Empresa do C1")
        sistema.logout()
        
        # Contador 2
        sistema.registrar("Contador 2", "c2@teste.com", "Senha@123")
        sistema.login("c2@teste.com", "Senha@123")
        empresa2 = sistema.criar_empresa("Empresa do C2")
        
        # C2 só vê suas empresas
        empresas = sistema.listar_empresas()
        assert len(empresas) == 1
        assert empresas[0]["nome"] == "Empresa do C2"
        
        # C2 não pode acessar empresa do C1
        with pytest.raises(PermissionError):
            sistema.obter_empresa(empresa1["id"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
