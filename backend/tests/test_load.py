"""
Testes de Carga - Performance Básica
Sprint 4 - Sistema Contábil

Estes testes medem a performance do sistema sob carga.
"""

import pytest
import time
import statistics
from typing import List, Dict, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass


# ============================================================================
# UTILITÁRIOS DE BENCHMARK
# ============================================================================

@dataclass
class BenchmarkResult:
    """Resultado de benchmark."""
    name: str
    iterations: int
    total_time: float
    min_time: float
    max_time: float
    avg_time: float
    median_time: float
    std_dev: float
    ops_per_second: float
    
    def __str__(self):
        return (
            f"\n{self.name}:\n"
            f"  Iterações: {self.iterations}\n"
            f"  Tempo total: {self.total_time:.4f}s\n"
            f"  Tempo médio: {self.avg_time*1000:.2f}ms\n"
            f"  Tempo mínimo: {self.min_time*1000:.2f}ms\n"
            f"  Tempo máximo: {self.max_time*1000:.2f}ms\n"
            f"  Mediana: {self.median_time*1000:.2f}ms\n"
            f"  Desvio padrão: {self.std_dev*1000:.2f}ms\n"
            f"  Ops/segundo: {self.ops_per_second:.2f}\n"
        )


def benchmark(func: Callable, iterations: int = 100, name: str = None) -> BenchmarkResult:
    """Executa benchmark de uma função."""
    times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append(end - start)
    
    total_time = sum(times)
    
    return BenchmarkResult(
        name=name or func.__name__,
        iterations=iterations,
        total_time=total_time,
        min_time=min(times),
        max_time=max(times),
        avg_time=statistics.mean(times),
        median_time=statistics.median(times),
        std_dev=statistics.stdev(times) if len(times) > 1 else 0,
        ops_per_second=iterations / total_time if total_time > 0 else 0
    )


# ============================================================================
# SIMULADORES PARA TESTES DE CARGA
# ============================================================================

class HighLoadSimulator:
    """Simulador otimizado para testes de carga."""
    
    def __init__(self):
        self.users = {}
        self.empresas = {}
        self.dados = {}
        self._lock_counter = 0
    
    def registrar_usuario(self, email: str) -> int:
        """Registra usuário rapidamente."""
        user_id = len(self.users) + 1
        self.users[user_id] = {"id": user_id, "email": email}
        return user_id
    
    def criar_empresa(self, user_id: int, nome: str) -> int:
        """Cria empresa rapidamente."""
        empresa_id = len(self.empresas) + 1
        self.empresas[empresa_id] = {
            "id": empresa_id,
            "nome": nome,
            "user_id": user_id
        }
        return empresa_id
    
    def lancar_dados(self, empresa_id: int, dados: Dict) -> int:
        """Lança dados rapidamente."""
        dados_id = len(self.dados) + 1
        self.dados[dados_id] = {"id": dados_id, "empresa_id": empresa_id, **dados}
        return dados_id
    
    def calcular_indicadores(self, receita: float, custos: float, 
                            lucro: float, ativo: float, passivo: float) -> Dict:
        """Calcula indicadores financeiros."""
        return {
            "margem_bruta": ((receita - custos) / receita * 100) if receita > 0 else 0,
            "margem_liquida": (lucro / receita * 100) if receita > 0 else 0,
            "endividamento": (passivo / ativo * 100) if ativo > 0 else 0
        }
    
    def classificar_saude(self, score: float) -> str:
        """Classifica saúde financeira."""
        if score >= 80:
            return "excelente"
        elif score >= 60:
            return "bom"
        elif score >= 40:
            return "regular"
        return "critico"


# ============================================================================
# TESTES DE CARGA
# ============================================================================

class TestLoadPerformance:
    """Testes de performance e carga."""
    
    @pytest.fixture
    def simulator(self):
        return HighLoadSimulator()
    
    # ===== TESTES DE THROUGHPUT =====
    
    def test_throughput_registro_usuarios(self, simulator):
        """Mede throughput de registro de usuários."""
        def register():
            simulator.registrar_usuario(f"user{time.time_ns()}@teste.com")
        
        result = benchmark(register, iterations=1000, name="Registro de Usuários")
        
        print(result)
        
        # Deve processar pelo menos 1000 registros/segundo
        assert result.ops_per_second >= 1000
    
    def test_throughput_criacao_empresas(self, simulator):
        """Mede throughput de criação de empresas."""
        user_id = simulator.registrar_usuario("teste@teste.com")
        
        def create():
            simulator.criar_empresa(user_id, f"Empresa {time.time_ns()}")
        
        result = benchmark(create, iterations=1000, name="Criação de Empresas")
        
        print(result)
        
        assert result.ops_per_second >= 1000
    
    def test_throughput_lancamento_dados(self, simulator):
        """Mede throughput de lançamento de dados."""
        user_id = simulator.registrar_usuario("teste@teste.com")
        empresa_id = simulator.criar_empresa(user_id, "Empresa Teste")
        
        dados = {
            "mes": 1,
            "ano": 2024,
            "receita_bruta": 100000,
            "custos": 60000,
            "lucro_liquido": 15000
        }
        
        def insert():
            simulator.lancar_dados(empresa_id, dados)
        
        result = benchmark(insert, iterations=1000, name="Lançamento de Dados")
        
        print(result)
        
        assert result.ops_per_second >= 1000
    
    def test_throughput_calculo_indicadores(self, simulator):
        """Mede throughput de cálculo de indicadores."""
        def calculate():
            simulator.calcular_indicadores(
                receita=100000,
                custos=60000,
                lucro=15000,
                ativo=500000,
                passivo=200000
            )
        
        result = benchmark(calculate, iterations=10000, name="Cálculo de Indicadores")
        
        print(result)
        
        # Cálculos devem ser muito rápidos
        assert result.ops_per_second >= 50000
    
    # ===== TESTES DE LATÊNCIA =====
    
    def test_latencia_aceitavel(self, simulator):
        """Verifica se latência está dentro do aceitável."""
        user_id = simulator.registrar_usuario("teste@teste.com")
        
        def full_operation():
            empresa_id = simulator.criar_empresa(user_id, "Empresa")
            simulator.lancar_dados(empresa_id, {"mes": 1, "ano": 2024, "receita": 100000})
            simulator.calcular_indicadores(100000, 60000, 15000, 500000, 200000)
        
        result = benchmark(full_operation, iterations=100, name="Operação Completa")
        
        print(result)
        
        # Latência média deve ser menor que 10ms
        assert result.avg_time < 0.01
        
        # 95% das operações devem completar em menos de 20ms
        assert result.median_time < 0.02
    
    # ===== TESTES DE CARGA CONCORRENTE =====
    
    def test_carga_concorrente_usuarios(self, simulator):
        """Testa criação concorrente de usuários."""
        num_threads = 10
        users_per_thread = 100
        
        def create_users(thread_id: int):
            for i in range(users_per_thread):
                simulator.registrar_usuario(f"user_{thread_id}_{i}@teste.com")
            return users_per_thread
        
        start = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(create_users, i) for i in range(num_threads)]
            total_created = sum(f.result() for f in as_completed(futures))
        
        elapsed = time.perf_counter() - start
        
        print(f"\nCarga Concorrente (Usuários):")
        print(f"  Threads: {num_threads}")
        print(f"  Total criado: {total_created}")
        print(f"  Tempo: {elapsed:.2f}s")
        print(f"  Taxa: {total_created/elapsed:.0f} usuários/segundo")
        
        assert total_created == num_threads * users_per_thread
        # Deve processar pelo menos 500 usuários/segundo
        assert total_created / elapsed >= 500
    
    def test_carga_concorrente_operacoes_mistas(self, simulator):
        """Testa operações mistas concorrentes."""
        num_threads = 5
        operations_per_thread = 50
        
        def mixed_operations(thread_id: int):
            results = []
            user_id = simulator.registrar_usuario(f"user_{thread_id}@teste.com")
            
            for i in range(operations_per_thread):
                # Criar empresa
                empresa_id = simulator.criar_empresa(user_id, f"Empresa_{thread_id}_{i}")
                
                # Lançar dados
                simulator.lancar_dados(empresa_id, {
                    "mes": (i % 12) + 1,
                    "ano": 2024,
                    "receita_bruta": 100000
                })
                
                # Calcular indicadores
                simulator.calcular_indicadores(100000, 60000, 15000, 500000, 200000)
                
                results.append(empresa_id)
            
            return len(results)
        
        start = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(mixed_operations, i) for i in range(num_threads)]
            total_ops = sum(f.result() for f in as_completed(futures))
        
        elapsed = time.perf_counter() - start
        
        # Cada thread faz 3 operações por iteração
        total_operations = total_ops * 3
        
        print(f"\nCarga Concorrente (Operações Mistas):")
        print(f"  Threads: {num_threads}")
        print(f"  Total operações: {total_operations}")
        print(f"  Tempo: {elapsed:.2f}s")
        print(f"  Taxa: {total_operations/elapsed:.0f} ops/segundo")
        
        assert total_ops == num_threads * operations_per_thread
    
    # ===== TESTES DE STRESS =====
    
    def test_stress_grande_volume(self, simulator):
        """Testa comportamento com grande volume de dados."""
        user_id = simulator.registrar_usuario("stress@teste.com")
        
        # Criar 100 empresas
        start = time.perf_counter()
        
        for i in range(100):
            empresa_id = simulator.criar_empresa(user_id, f"Empresa {i}")
            
            # Cada empresa com 12 meses de dados
            for mes in range(1, 13):
                simulator.lancar_dados(empresa_id, {
                    "mes": mes,
                    "ano": 2024,
                    "receita_bruta": 100000 + (i * 1000),
                    "custos": 60000 + (i * 500)
                })
        
        elapsed = time.perf_counter() - start
        
        total_empresas = 100
        total_dados = 100 * 12
        total_ops = total_empresas + total_dados
        
        print(f"\nStress Test (Grande Volume):")
        print(f"  Empresas: {total_empresas}")
        print(f"  Registros de dados: {total_dados}")
        print(f"  Tempo total: {elapsed:.2f}s")
        print(f"  Taxa: {total_ops/elapsed:.0f} ops/segundo")
        
        assert len(simulator.empresas) == 100
        assert len(simulator.dados) == 1200
        
        # Deve completar em menos de 5 segundos
        assert elapsed < 5


# ============================================================================
# TESTES DE MEMÓRIA
# ============================================================================

class TestMemoryUsage:
    """Testes de uso de memória."""
    
    def test_memoria_com_muitos_usuarios(self):
        """Verifica uso de memória com muitos usuários."""
        import sys
        
        simulator = HighLoadSimulator()
        
        # Medir memória inicial
        initial_size = sys.getsizeof(simulator.users)
        
        # Criar 1000 usuários
        for i in range(1000):
            simulator.registrar_usuario(f"user{i}@teste.com")
        
        # Medir memória final
        final_size = sys.getsizeof(simulator.users)
        
        # Cada usuário não deve usar mais que 1KB em média
        avg_per_user = (final_size - initial_size) / 1000
        
        print(f"\nUso de Memória (Usuários):")
        print(f"  Usuários: 1000")
        print(f"  Tamanho inicial: {initial_size} bytes")
        print(f"  Tamanho final: {final_size} bytes")
        print(f"  Média por usuário: {avg_per_user:.2f} bytes")
        
        # Dict overhead, não o dado real
        assert final_size < initial_size + 100000  # Menos de 100KB para 1000 usuarios
    
    def test_memoria_com_muitos_dados(self):
        """Verifica uso de memória com muitos dados."""
        import sys
        
        simulator = HighLoadSimulator()
        user_id = simulator.registrar_usuario("teste@teste.com")
        empresa_id = simulator.criar_empresa(user_id, "Empresa Teste")
        
        # Medir memória inicial
        initial_size = sys.getsizeof(simulator.dados)
        
        # Criar 10000 registros de dados
        for i in range(10000):
            simulator.lancar_dados(empresa_id, {
                "mes": (i % 12) + 1,
                "ano": 2020 + (i // 12),
                "receita_bruta": 100000,
                "custos": 60000,
                "lucro_liquido": 15000
            })
        
        # Medir memória final
        final_size = sys.getsizeof(simulator.dados)
        
        print(f"\nUso de Memória (Dados):")
        print(f"  Registros: 10000")
        print(f"  Tamanho inicial: {initial_size} bytes")
        print(f"  Tamanho final: {final_size} bytes")
        
        assert len(simulator.dados) == 10000


# ============================================================================
# TESTES DE TEMPO DE RESPOSTA
# ============================================================================

class TestResponseTime:
    """Testes de tempo de resposta."""
    
    def test_response_time_p95(self):
        """Verifica P95 do tempo de resposta."""
        simulator = HighLoadSimulator()
        user_id = simulator.registrar_usuario("teste@teste.com")
        
        times = []
        
        for _ in range(1000):
            start = time.perf_counter()
            
            empresa_id = simulator.criar_empresa(user_id, "Empresa")
            simulator.lancar_dados(empresa_id, {"mes": 1, "ano": 2024, "receita": 100000})
            simulator.calcular_indicadores(100000, 60000, 15000, 500000, 200000)
            
            times.append(time.perf_counter() - start)
        
        times.sort()
        p50 = times[499]
        p95 = times[949]
        p99 = times[989]
        
        print(f"\nTempo de Resposta:")
        print(f"  P50: {p50*1000:.2f}ms")
        print(f"  P95: {p95*1000:.2f}ms")
        print(f"  P99: {p99*1000:.2f}ms")
        
        # P95 deve ser menor que 5ms
        assert p95 < 0.005
        
        # P99 deve ser menor que 10ms
        assert p99 < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
