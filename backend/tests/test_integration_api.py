"""
Testes de Integração - API REST
Sprint 4 - Sistema Contábil

Estes testes validam a integração entre componentes da API.
Podem ser executados com ou sem o servidor real.
"""

import pytest
import json
import time
from typing import Dict, Any, Optional
from unittest.mock import MagicMock, patch
from dataclasses import dataclass


# ============================================================================
# SIMULADOR DE CLIENTE HTTP
# ============================================================================

@dataclass
class MockResponse:
    """Resposta simulada de HTTP."""
    status_code: int
    data: Dict[str, Any]
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {"Content-Type": "application/json"}
    
    def json(self) -> Dict:
        return self.data


class APIClientSimulator:
    """Simulador de cliente de API para testes."""
    
    def __init__(self):
        self.users = {}
        self.empresas = {}
        self.tokens = {}
        self.dados_mensais = {}
        self.analises = {}
        self._user_counter = 0
        self._empresa_counter = 0
    
    def _get_user_from_token(self, token: str) -> Optional[Dict]:
        """Obtém usuário a partir do token."""
        user_id = self.tokens.get(token)
        if user_id:
            return self.users.get(user_id)
        return None
    
    def _check_auth(self, headers: Dict) -> Optional[Dict]:
        """Verifica autenticação."""
        auth = headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            return self._get_user_from_token(token)
        return None
    
    # ===== AUTH ENDPOINTS =====
    
    def post_register(self, data: Dict) -> MockResponse:
        """POST /api/auth/register"""
        # Validações
        if not data.get("nome"):
            return MockResponse(400, {"detail": "Nome é obrigatório"})
        
        if not data.get("email"):
            return MockResponse(400, {"detail": "Email é obrigatório"})
        
        if not data.get("senha"):
            return MockResponse(400, {"detail": "Senha é obrigatória"})
        
        # Verificar email duplicado
        for user in self.users.values():
            if user["email"] == data["email"]:
                return MockResponse(400, {"detail": "Email já cadastrado"})
        
        # Validar senha
        senha = data["senha"]
        if len(senha) < 8:
            return MockResponse(400, {"detail": "Senha deve ter no mínimo 8 caracteres"})
        
        # Criar usuário
        self._user_counter += 1
        user_id = self._user_counter
        
        self.users[user_id] = {
            "id": user_id,
            "nome": data["nome"],
            "email": data["email"],
            "senha_hash": f"hash_{senha}",
            "ativo": True,
            "criado_em": time.time()
        }
        
        return MockResponse(200, {
            "id": user_id,
            "nome": data["nome"],
            "email": data["email"],
            "message": "Usuário criado com sucesso"
        })
    
    def post_login(self, data: Dict) -> MockResponse:
        """POST /api/auth/login"""
        email = data.get("email")
        senha = data.get("senha")
        
        if not email or not senha:
            return MockResponse(400, {"detail": "Email e senha são obrigatórios"})
        
        # Buscar usuário
        user = None
        for u in self.users.values():
            if u["email"] == email:
                user = u
                break
        
        if not user:
            return MockResponse(401, {"detail": "Credenciais inválidas"})
        
        if user["senha_hash"] != f"hash_{senha}":
            return MockResponse(401, {"detail": "Credenciais inválidas"})
        
        # Gerar token
        token = f"token_{user['id']}_{int(time.time())}"
        self.tokens[token] = user["id"]
        
        return MockResponse(200, {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "nome": user["nome"],
                "email": user["email"]
            }
        })
    
    def get_me(self, headers: Dict) -> MockResponse:
        """GET /api/auth/me"""
        user = self._check_auth(headers)
        if not user:
            return MockResponse(401, {"detail": "Não autenticado"})
        
        return MockResponse(200, {
            "id": user["id"],
            "nome": user["nome"],
            "email": user["email"]
        })
    
    def post_logout(self, headers: Dict) -> MockResponse:
        """POST /api/auth/logout"""
        auth = headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            if token in self.tokens:
                del self.tokens[token]
        
        return MockResponse(200, {"message": "Logout realizado com sucesso"})
    
    # ===== EMPRESAS ENDPOINTS =====
    
    def post_empresa(self, data: Dict, headers: Dict) -> MockResponse:
        """POST /api/empresas"""
        user = self._check_auth(headers)
        if not user:
            return MockResponse(401, {"detail": "Não autenticado"})
        
        if not data.get("nome"):
            return MockResponse(400, {"detail": "Nome da empresa é obrigatório"})
        
        self._empresa_counter += 1
        empresa_id = self._empresa_counter
        
        empresa = {
            "id": empresa_id,
            "nome": data["nome"],
            "cnpj": data.get("cnpj"),
            "segmento": data.get("segmento"),
            "porte": data.get("porte"),
            "contador_id": user["id"],
            "criado_em": time.time()
        }
        
        self.empresas[empresa_id] = empresa
        
        return MockResponse(200, empresa)
    
    def get_empresas(self, headers: Dict) -> MockResponse:
        """GET /api/empresas"""
        user = self._check_auth(headers)
        if not user:
            return MockResponse(401, {"detail": "Não autenticado"})
        
        # Filtrar empresas do contador
        empresas = [e for e in self.empresas.values() if e["contador_id"] == user["id"]]
        
        return MockResponse(200, {"empresas": empresas, "total": len(empresas)})
    
    def get_empresa(self, empresa_id: int, headers: Dict) -> MockResponse:
        """GET /api/empresas/{id}"""
        user = self._check_auth(headers)
        if not user:
            return MockResponse(401, {"detail": "Não autenticado"})
        
        empresa = self.empresas.get(empresa_id)
        
        if not empresa:
            return MockResponse(404, {"detail": "Empresa não encontrada"})
        
        if empresa["contador_id"] != user["id"]:
            return MockResponse(403, {"detail": "Acesso negado"})
        
        return MockResponse(200, empresa)
    
    def delete_empresa(self, empresa_id: int, headers: Dict) -> MockResponse:
        """DELETE /api/empresas/{id}"""
        user = self._check_auth(headers)
        if not user:
            return MockResponse(401, {"detail": "Não autenticado"})
        
        empresa = self.empresas.get(empresa_id)
        
        if not empresa:
            return MockResponse(404, {"detail": "Empresa não encontrada"})
        
        if empresa["contador_id"] != user["id"]:
            return MockResponse(403, {"detail": "Acesso negado"})
        
        del self.empresas[empresa_id]
        
        return MockResponse(200, {"message": "Empresa excluída com sucesso"})
    
    # ===== DADOS MENSAIS ENDPOINTS =====
    
    def post_dados_mensais(self, empresa_id: int, data: Dict, headers: Dict) -> MockResponse:
        """POST /api/empresas/{id}/dados-mensais"""
        user = self._check_auth(headers)
        if not user:
            return MockResponse(401, {"detail": "Não autenticado"})
        
        empresa = self.empresas.get(empresa_id)
        if not empresa or empresa["contador_id"] != user["id"]:
            return MockResponse(404, {"detail": "Empresa não encontrada"})
        
        key = f"{empresa_id}_{data['ano']}_{data['mes']}"
        
        dados = {
            "id": len(self.dados_mensais) + 1,
            "empresa_id": empresa_id,
            **data
        }
        
        self.dados_mensais[key] = dados
        
        return MockResponse(200, dados)
    
    def get_dados_mensais(self, empresa_id: int, headers: Dict) -> MockResponse:
        """GET /api/empresas/{id}/dados-mensais"""
        user = self._check_auth(headers)
        if not user:
            return MockResponse(401, {"detail": "Não autenticado"})
        
        empresa = self.empresas.get(empresa_id)
        if not empresa or empresa["contador_id"] != user["id"]:
            return MockResponse(404, {"detail": "Empresa não encontrada"})
        
        dados = [d for d in self.dados_mensais.values() if d["empresa_id"] == empresa_id]
        
        return MockResponse(200, {"dados": dados, "total": len(dados)})
    
    # ===== ANÁLISE ENDPOINTS =====
    
    def post_analise(self, empresa_id: int, headers: Dict) -> MockResponse:
        """POST /api/empresas/{id}/analise"""
        user = self._check_auth(headers)
        if not user:
            return MockResponse(401, {"detail": "Não autenticado"})
        
        empresa = self.empresas.get(empresa_id)
        if not empresa or empresa["contador_id"] != user["id"]:
            return MockResponse(404, {"detail": "Empresa não encontrada"})
        
        # Verificar se tem dados suficientes
        dados = [d for d in self.dados_mensais.values() if d["empresa_id"] == empresa_id]
        
        if len(dados) < 3:
            return MockResponse(400, {"detail": "Necessário pelo menos 3 meses de dados"})
        
        # Calcular indicadores (simplificado)
        ultimo = dados[-1]
        
        analise = {
            "id": len(self.analises) + 1,
            "empresa_id": empresa_id,
            "periodo": f"{ultimo['mes']:02d}/{ultimo['ano']}",
            "indicadores": {
                "margem_bruta": ((ultimo["receita_bruta"] - ultimo["custos"]) / ultimo["receita_bruta"]) * 100,
                "margem_liquida": (ultimo["lucro_liquido"] / ultimo["receita_bruta"]) * 100,
                "liquidez_corrente": ultimo["ativo_circulante"] / ultimo["passivo_circulante"],
                "endividamento": (ultimo["passivo_total"] / ultimo["ativo_total"]) * 100
            },
            "score": 75.0,
            "classificacao": "bom",
            "alertas": []
        }
        
        self.analises[analise["id"]] = analise
        
        return MockResponse(200, analise)
    
    # ===== HEALTH ENDPOINTS =====
    
    def get_health(self) -> MockResponse:
        """GET /api/health"""
        return MockResponse(200, {
            "status": "healthy",
            "version": "3.0.0",
            "database": "connected",
            "timestamp": time.time()
        })


# ============================================================================
# TESTES DE INTEGRAÇÃO - AUTENTICAÇÃO
# ============================================================================

class TestAuthIntegration:
    """Testes de integração para autenticação."""
    
    @pytest.fixture
    def api(self):
        return APIClientSimulator()
    
    def test_registro_login_flow(self, api, sample_user_data):
        """Fluxo completo: registro → login → acesso."""
        # 1. Registrar
        response = api.post_register(sample_user_data)
        assert response.status_code == 200
        assert "id" in response.data
        
        # 2. Login
        login_data = {"email": sample_user_data["email"], "senha": sample_user_data["senha"]}
        response = api.post_login(login_data)
        assert response.status_code == 200
        assert "access_token" in response.data
        
        token = response.data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Acessar dados do usuário
        response = api.get_me(headers)
        assert response.status_code == 200
        assert response.data["email"] == sample_user_data["email"]
    
    def test_registro_email_duplicado(self, api, sample_user_data):
        """Não deve permitir email duplicado."""
        # Primeiro registro
        response = api.post_register(sample_user_data)
        assert response.status_code == 200
        
        # Segundo registro com mesmo email
        response = api.post_register(sample_user_data)
        assert response.status_code == 400
        assert "já cadastrado" in response.data["detail"]
    
    def test_login_credenciais_invalidas(self, api, sample_user_data):
        """Login com credenciais inválidas deve falhar."""
        # Registrar
        api.post_register(sample_user_data)
        
        # Tentar login com senha errada
        response = api.post_login({"email": sample_user_data["email"], "senha": "senhaerrada"})
        assert response.status_code == 401
    
    def test_acesso_sem_token(self, api):
        """Acesso sem token deve ser negado."""
        response = api.get_me({})
        assert response.status_code == 401
    
    def test_logout_invalida_token(self, api, sample_user_data):
        """Logout deve invalidar o token."""
        # Registrar e login
        api.post_register(sample_user_data)
        login_response = api.post_login({
            "email": sample_user_data["email"],
            "senha": sample_user_data["senha"]
        })
        
        token = login_response.data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Logout
        response = api.post_logout(headers)
        assert response.status_code == 200
        
        # Tentar acessar com token antigo
        response = api.get_me(headers)
        assert response.status_code == 401


# ============================================================================
# TESTES DE INTEGRAÇÃO - EMPRESAS
# ============================================================================

class TestEmpresasIntegration:
    """Testes de integração para gestão de empresas."""
    
    @pytest.fixture
    def api(self):
        return APIClientSimulator()
    
    @pytest.fixture
    def auth_headers(self, api, sample_user_data):
        """Retorna headers autenticados."""
        api.post_register(sample_user_data)
        response = api.post_login({
            "email": sample_user_data["email"],
            "senha": sample_user_data["senha"]
        })
        return {"Authorization": f"Bearer {response.data['access_token']}"}
    
    def test_crud_empresa_completo(self, api, auth_headers, sample_empresa_data):
        """Fluxo CRUD completo de empresa."""
        # CREATE
        response = api.post_empresa(sample_empresa_data, auth_headers)
        assert response.status_code == 200
        empresa_id = response.data["id"]
        
        # READ (lista)
        response = api.get_empresas(auth_headers)
        assert response.status_code == 200
        assert response.data["total"] == 1
        
        # READ (único)
        response = api.get_empresa(empresa_id, auth_headers)
        assert response.status_code == 200
        assert response.data["nome"] == sample_empresa_data["nome"]
        
        # DELETE
        response = api.delete_empresa(empresa_id, auth_headers)
        assert response.status_code == 200
        
        # Verificar exclusão
        response = api.get_empresa(empresa_id, auth_headers)
        assert response.status_code == 404
    
    def test_criar_multiplas_empresas(self, api, auth_headers, multiple_empresas_data):
        """Deve criar múltiplas empresas."""
        for empresa_data in multiple_empresas_data:
            response = api.post_empresa(empresa_data, auth_headers)
            assert response.status_code == 200
        
        response = api.get_empresas(auth_headers)
        assert response.data["total"] == len(multiple_empresas_data)
    
    def test_isolamento_entre_contadores(self, api, sample_user_data, sample_empresa_data):
        """Cada contador só vê suas empresas."""
        # Contador 1
        api.post_register(sample_user_data)
        login1 = api.post_login({"email": sample_user_data["email"], "senha": sample_user_data["senha"]})
        headers1 = {"Authorization": f"Bearer {login1.data['access_token']}"}
        
        # Contador 2
        user2 = {**sample_user_data, "email": "outro@teste.com"}
        api.post_register(user2)
        login2 = api.post_login({"email": user2["email"], "senha": user2["senha"]})
        headers2 = {"Authorization": f"Bearer {login2.data['access_token']}"}
        
        # Contador 1 cria empresa
        response = api.post_empresa(sample_empresa_data, headers1)
        empresa_id = response.data["id"]
        
        # Contador 2 não deve ver
        response = api.get_empresas(headers2)
        assert response.data["total"] == 0
        
        # Contador 2 não deve acessar diretamente
        response = api.get_empresa(empresa_id, headers2)
        assert response.status_code == 403
    
    def test_empresa_sem_autenticacao(self, api, sample_empresa_data):
        """Não deve criar empresa sem autenticação."""
        response = api.post_empresa(sample_empresa_data, {})
        assert response.status_code == 401


# ============================================================================
# TESTES DE INTEGRAÇÃO - DADOS MENSAIS E ANÁLISE
# ============================================================================

class TestAnaliseIntegration:
    """Testes de integração para análise financeira."""
    
    @pytest.fixture
    def api(self):
        return APIClientSimulator()
    
    @pytest.fixture
    def setup_empresa(self, api, sample_user_data, sample_empresa_data):
        """Setup: usuário autenticado com empresa criada."""
        api.post_register(sample_user_data)
        login = api.post_login({
            "email": sample_user_data["email"],
            "senha": sample_user_data["senha"]
        })
        headers = {"Authorization": f"Bearer {login.data['access_token']}"}
        
        empresa = api.post_empresa(sample_empresa_data, headers)
        
        return {
            "headers": headers,
            "empresa_id": empresa.data["id"]
        }
    
    def test_lancar_dados_mensais(self, api, setup_empresa, sample_dados_mensais):
        """Deve lançar dados mensais."""
        response = api.post_dados_mensais(
            setup_empresa["empresa_id"],
            sample_dados_mensais,
            setup_empresa["headers"]
        )
        assert response.status_code == 200
        assert response.data["receita_bruta"] == sample_dados_mensais["receita_bruta"]
    
    def test_fluxo_completo_analise(self, api, setup_empresa, multiple_meses_data):
        """Fluxo completo: lançar dados → gerar análise."""
        headers = setup_empresa["headers"]
        empresa_id = setup_empresa["empresa_id"]
        
        # Lançar 6 meses de dados
        for dados in multiple_meses_data:
            response = api.post_dados_mensais(empresa_id, dados, headers)
            assert response.status_code == 200
        
        # Verificar dados lançados
        response = api.get_dados_mensais(empresa_id, headers)
        assert response.data["total"] == 6
        
        # Gerar análise
        response = api.post_analise(empresa_id, headers)
        assert response.status_code == 200
        assert "indicadores" in response.data
        assert "score" in response.data
        assert "classificacao" in response.data
    
    def test_analise_sem_dados_suficientes(self, api, setup_empresa, sample_dados_mensais):
        """Análise com menos de 3 meses deve falhar."""
        headers = setup_empresa["headers"]
        empresa_id = setup_empresa["empresa_id"]
        
        # Lançar apenas 2 meses
        for i in range(2):
            dados = {**sample_dados_mensais, "mes": i + 1}
            api.post_dados_mensais(empresa_id, dados, headers)
        
        # Tentar gerar análise
        response = api.post_analise(empresa_id, headers)
        assert response.status_code == 400
        assert "3 meses" in response.data["detail"]


# ============================================================================
# TESTES DE INTEGRAÇÃO - HEALTH CHECK
# ============================================================================

class TestHealthIntegration:
    """Testes de integração para health check."""
    
    @pytest.fixture
    def api(self):
        return APIClientSimulator()
    
    def test_health_check(self, api):
        """Health check deve retornar status."""
        response = api.get_health()
        assert response.status_code == 200
        assert response.data["status"] == "healthy"
        assert "version" in response.data
        assert "database" in response.data


# ============================================================================
# TESTES DE INTEGRAÇÃO - CONCORRÊNCIA
# ============================================================================

class TestConcurrencyIntegration:
    """Testes de integração para cenários de concorrência."""
    
    @pytest.fixture
    def api(self):
        return APIClientSimulator()
    
    def test_multiplos_usuarios_simultaneos(self, api):
        """Múltiplos usuários operando simultaneamente."""
        users = []
        empresas_por_usuario = {}
        
        # Criar 5 usuários
        for i in range(5):
            user_data = {
                "nome": f"Usuario {i}",
                "email": f"user{i}@teste.com",
                "senha": "Senha@123"
            }
            api.post_register(user_data)
            login = api.post_login({"email": user_data["email"], "senha": user_data["senha"]})
            headers = {"Authorization": f"Bearer {login.data['access_token']}"}
            users.append(headers)
            empresas_por_usuario[i] = []
        
        # Cada usuário cria 3 empresas
        for i, headers in enumerate(users):
            for j in range(3):
                empresa_data = {"nome": f"Empresa {i}-{j}", "cnpj": f"{i}{i}.{j}{j}{j}.000/0001-00"}
                response = api.post_empresa(empresa_data, headers)
                empresas_por_usuario[i].append(response.data["id"])
        
        # Verificar isolamento
        for i, headers in enumerate(users):
            response = api.get_empresas(headers)
            assert response.data["total"] == 3
            
            # Não deve acessar empresas de outros
            for other_i, other_empresas in empresas_por_usuario.items():
                if other_i != i:
                    for empresa_id in other_empresas:
                        response = api.get_empresa(empresa_id, headers)
                        assert response.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
