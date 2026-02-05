"""
Serviço de Importação de Balancetes
Sistema Contábil - Sprint 5

Gerencia o fluxo completo de importação:
1. Recebe arquivo (PDF)
2. Extrai dados automaticamente
3. Identifica empresa pelo CNPJ
4. Cria empresa se necessário
5. Salva dados mensais
6. Retorna resultado completo
"""

import os
import shutil
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# Importar o parser de balancetes
from importers.balancete_importer import (
    GerenciadorImportacao,
    ResultadoImportacao,
    DadosBalancete,
    importar_balancete
)


# ============================================================================
# ESTRUTURAS
# ============================================================================

@dataclass
class EmpresaDTO:
    """Data Transfer Object para empresa."""
    id: int
    nome: str
    cnpj: str
    cnpj_formatado: str = ""
    segmento: Optional[str] = None
    porte: Optional[str] = None
    contador_nome: Optional[str] = None
    contador_crc: Optional[str] = None
    criada_em: Optional[datetime] = None


@dataclass
class DadosMensaisDTO:
    """Data Transfer Object para dados mensais."""
    id: int
    empresa_id: int
    mes: int
    ano: int
    
    # Balanço
    ativo_total: float = 0.0
    ativo_circulante: float = 0.0
    passivo_circulante: float = 0.0
    patrimonio_liquido: float = 0.0
    disponivel: float = 0.0
    
    # DRE
    receita_bruta: float = 0.0
    custos: float = 0.0
    despesas_operacionais: float = 0.0
    despesas_financeiras: float = 0.0
    lucro_liquido: float = 0.0
    
    # Impostos
    impostos_total: float = 0.0


@dataclass
class ResultadoServico:
    """Resultado do serviço de importação."""
    sucesso: bool
    mensagem: str
    empresa: Optional[EmpresaDTO] = None
    empresa_criada: bool = False
    dados_mensais: Optional[DadosMensaisDTO] = None
    dados_completos: Optional[Dict] = None
    avisos: List[str] = field(default_factory=list)
    erros: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "sucesso": self.sucesso,
            "mensagem": self.mensagem,
            "empresa": {
                "id": self.empresa.id,
                "nome": self.empresa.nome,
                "cnpj": self.empresa.cnpj,
                "cnpj_formatado": self.empresa.cnpj_formatado,
                "nova": self.empresa_criada
            } if self.empresa else None,
            "dados_mensais": {
                "id": self.dados_mensais.id,
                "mes": self.dados_mensais.mes,
                "ano": self.dados_mensais.ano,
                "receita_bruta": self.dados_mensais.receita_bruta,
                "lucro_liquido": self.dados_mensais.lucro_liquido,
            } if self.dados_mensais else None,
            "avisos": self.avisos,
            "erros": self.erros
        }


# ============================================================================
# REPOSITÓRIO SIMULADO (para testes sem banco)
# ============================================================================

class RepositorioEmpresas:
    """Repositório de empresas (simulado para testes standalone)."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.empresas = {}
            cls._instance.dados_mensais = {}
            cls._instance._empresa_counter = 0
            cls._instance._dados_counter = 0
        return cls._instance
    
    def buscar_por_cnpj(self, cnpj: str) -> Optional[EmpresaDTO]:
        """Busca empresa pelo CNPJ."""
        cnpj_limpo = ''.join(filter(str.isdigit, cnpj))
        return self.empresas.get(cnpj_limpo)
    
    def criar_empresa(self, nome: str, cnpj: str, **kwargs) -> EmpresaDTO:
        """Cria nova empresa."""
        self._empresa_counter += 1
        cnpj_limpo = ''.join(filter(str.isdigit, cnpj))
        
        empresa = EmpresaDTO(
            id=self._empresa_counter,
            nome=nome,
            cnpj=cnpj_limpo,
            cnpj_formatado=self._formatar_cnpj(cnpj_limpo),
            segmento=kwargs.get('segmento'),
            porte=kwargs.get('porte'),
            contador_nome=kwargs.get('contador_nome'),
            contador_crc=kwargs.get('contador_crc'),
            criada_em=datetime.now()
        )
        
        self.empresas[cnpj_limpo] = empresa
        return empresa
    
    def atualizar_empresa(self, empresa: EmpresaDTO, **kwargs) -> EmpresaDTO:
        """Atualiza dados da empresa."""
        for key, value in kwargs.items():
            if hasattr(empresa, key) and value is not None:
                setattr(empresa, key, value)
        return empresa
    
    def criar_dados_mensais(self, empresa_id: int, mes: int, ano: int, dados: Dict) -> DadosMensaisDTO:
        """Cria registro de dados mensais."""
        self._dados_counter += 1
        
        dados_dto = DadosMensaisDTO(
            id=self._dados_counter,
            empresa_id=empresa_id,
            mes=mes,
            ano=ano,
            ativo_total=dados.get('ativo_total', 0),
            ativo_circulante=dados.get('ativo_circulante', 0),
            passivo_circulante=dados.get('passivo_circulante', 0),
            patrimonio_liquido=dados.get('patrimonio_liquido', 0),
            disponivel=dados.get('disponivel', 0),
            receita_bruta=dados.get('receita_bruta', 0),
            custos=dados.get('custos_total', dados.get('custos', 0)),
            despesas_operacionais=dados.get('despesas_operacionais', 0),
            despesas_financeiras=dados.get('despesas_financeiras', 0),
            lucro_liquido=dados.get('lucro_liquido', 0),
            impostos_total=dados.get('deducoes_receita', 0)
        )
        
        key = f"{empresa_id}_{ano}_{mes}"
        self.dados_mensais[key] = dados_dto
        return dados_dto
    
    def buscar_dados_mensais(self, empresa_id: int, mes: int, ano: int) -> Optional[DadosMensaisDTO]:
        """Busca dados mensais existentes."""
        key = f"{empresa_id}_{ano}_{mes}"
        return self.dados_mensais.get(key)
    
    def _formatar_cnpj(self, cnpj: str) -> str:
        """Formata CNPJ."""
        if len(cnpj) == 14:
            return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
        return cnpj
    
    def listar_empresas(self) -> List[EmpresaDTO]:
        """Lista todas as empresas."""
        return list(self.empresas.values())
    
    def reset(self):
        """Reseta o repositório (para testes)."""
        self.empresas = {}
        self.dados_mensais = {}
        self._empresa_counter = 0
        self._dados_counter = 0


# ============================================================================
# SERVIÇO DE IMPORTAÇÃO
# ============================================================================

class ServicoImportacao:
    """
    Serviço principal de importação de balancetes.
    
    Fluxo:
    1. Recebe arquivo (caminho ou bytes)
    2. Salva temporariamente se necessário
    3. Usa GerenciadorImportacao para extrair dados
    4. Busca ou cria empresa pelo CNPJ
    5. Salva dados mensais
    6. Retorna resultado completo
    """
    
    def __init__(self, repositorio: RepositorioEmpresas = None):
        self.repositorio = repositorio or RepositorioEmpresas()
        self.gerenciador = GerenciadorImportacao()
    
    def importar_arquivo(self, caminho: str) -> ResultadoServico:
        """
        Importa balancete de arquivo.
        
        Args:
            caminho: Caminho do arquivo (PDF)
        
        Returns:
            ResultadoServico com dados completos
        """
        # Validar arquivo
        if not os.path.exists(caminho):
            return ResultadoServico(
                sucesso=False,
                mensagem=f"Arquivo não encontrado: {caminho}"
            )
        
        # Verificar extensão
        extensao = os.path.splitext(caminho)[1].lower()
        if extensao not in ['.pdf']:
            return ResultadoServico(
                sucesso=False,
                mensagem=f"Formato não suportado: {extensao}. Use PDF."
            )
        
        # Importar dados
        resultado = importar_balancete(caminho)
        
        if not resultado.sucesso:
            return ResultadoServico(
                sucesso=False,
                mensagem=resultado.mensagem,
                erros=resultado.erros
            )
        
        # Processar empresa e dados
        return self._processar_dados(resultado)
    
    def importar_bytes(self, conteudo: bytes, nome_arquivo: str) -> ResultadoServico:
        """
        Importa balancete de bytes (upload).
        
        Args:
            conteudo: Bytes do arquivo
            nome_arquivo: Nome original do arquivo
        
        Returns:
            ResultadoServico com dados completos
        """
        # Salvar temporariamente
        extensao = os.path.splitext(nome_arquivo)[1].lower()
        
        with tempfile.NamedTemporaryFile(suffix=extensao, delete=False) as tmp:
            tmp.write(conteudo)
            caminho_temp = tmp.name
        
        try:
            return self.importar_arquivo(caminho_temp)
        finally:
            # Limpar arquivo temporário
            if os.path.exists(caminho_temp):
                os.remove(caminho_temp)
    
    def _processar_dados(self, resultado: ResultadoImportacao) -> ResultadoServico:
        """Processa dados importados, criando/atualizando empresa."""
        dados = resultado.dados
        avisos = resultado.avisos.copy()
        
        # Buscar ou criar empresa
        empresa = self.repositorio.buscar_por_cnpj(dados.empresa.cnpj)
        empresa_criada = False
        
        if empresa is None:
            # Criar nova empresa
            empresa = self.repositorio.criar_empresa(
                nome=dados.empresa.nome,
                cnpj=dados.empresa.cnpj,
                contador_nome=dados.empresa.contador_nome,
                contador_crc=dados.empresa.contador_crc
            )
            empresa_criada = True
            avisos.append(f"Nova empresa criada: {empresa.nome}")
        else:
            # Atualizar dados do contador se informados
            if dados.empresa.contador_nome:
                self.repositorio.atualizar_empresa(
                    empresa,
                    contador_nome=dados.empresa.contador_nome,
                    contador_crc=dados.empresa.contador_crc
                )
        
        # Verificar se já existem dados para o período
        mes = dados.periodo_fim.month
        ano = dados.periodo_fim.year
        
        dados_existentes = self.repositorio.buscar_dados_mensais(empresa.id, mes, ano)
        
        if dados_existentes:
            avisos.append(f"Dados existentes para {mes:02d}/{ano} serão atualizados")
        
        # Criar/atualizar dados mensais
        dados_dict = dados.to_dict()
        dados_mensais = self.repositorio.criar_dados_mensais(
            empresa_id=empresa.id,
            mes=mes,
            ano=ano,
            dados={
                'ativo_total': dados.ativo_total,
                'ativo_circulante': dados.ativo_circulante,
                'passivo_circulante': dados.passivo_circulante,
                'patrimonio_liquido': dados.patrimonio_liquido,
                'disponivel': dados.disponivel,
                'receita_bruta': dados.receita_bruta,
                'custos_total': dados.custos_total,
                'despesas_operacionais': dados.despesas_operacionais,
                'despesas_financeiras': dados.despesas_financeiras,
                'lucro_liquido': dados.lucro_liquido,
                'deducoes_receita': dados.deducoes_receita,
            }
        )
        
        return ResultadoServico(
            sucesso=True,
            mensagem=f"Balancete importado com sucesso para {empresa.nome}",
            empresa=empresa,
            empresa_criada=empresa_criada,
            dados_mensais=dados_mensais,
            dados_completos=dados_dict,
            avisos=avisos
        )
    
    def listar_empresas(self) -> List[EmpresaDTO]:
        """Lista todas as empresas cadastradas."""
        return self.repositorio.listar_empresas()
    
    def obter_empresa(self, cnpj: str) -> Optional[EmpresaDTO]:
        """Busca empresa pelo CNPJ."""
        return self.repositorio.buscar_por_cnpj(cnpj)


# ============================================================================
# FUNÇÕES DE CONVENIÊNCIA
# ============================================================================

def importar_balancete_completo(caminho: str) -> ResultadoServico:
    """
    Importa balancete e processa automaticamente.
    
    Função de conveniência para uso simplificado.
    
    Args:
        caminho: Caminho do arquivo
    
    Returns:
        ResultadoServico com todos os dados
    """
    servico = ServicoImportacao()
    return servico.importar_arquivo(caminho)


def importar_upload(conteudo: bytes, nome_arquivo: str) -> ResultadoServico:
    """
    Importa balancete de upload.
    
    Args:
        conteudo: Bytes do arquivo
        nome_arquivo: Nome original
    
    Returns:
        ResultadoServico com todos os dados
    """
    servico = ServicoImportacao()
    return servico.importar_bytes(conteudo, nome_arquivo)


# ============================================================================
# API ENDPOINT (simulado para teste)
# ============================================================================

class ImportacaoAPI:
    """
    API de importação (simulada para demonstração).
    
    Em produção, estes métodos seriam endpoints FastAPI.
    """
    
    def __init__(self):
        self.servico = ServicoImportacao()
    
    def post_importar(self, arquivo_bytes: bytes, nome_arquivo: str) -> Dict:
        """
        POST /api/importacao/balancete
        
        Importa balancete e retorna resultado.
        """
        resultado = self.servico.importar_bytes(arquivo_bytes, nome_arquivo)
        return resultado.to_dict()
    
    def get_empresas(self) -> Dict:
        """
        GET /api/empresas
        
        Lista todas as empresas.
        """
        empresas = self.servico.listar_empresas()
        return {
            "sucesso": True,
            "empresas": [
                {
                    "id": e.id,
                    "nome": e.nome,
                    "cnpj": e.cnpj,
                    "cnpj_formatado": e.cnpj_formatado
                }
                for e in empresas
            ],
            "total": len(empresas)
        }
    
    def get_empresa_por_cnpj(self, cnpj: str) -> Dict:
        """
        GET /api/empresas/cnpj/{cnpj}
        
        Busca empresa pelo CNPJ.
        """
        empresa = self.servico.obter_empresa(cnpj)
        
        if not empresa:
            return {
                "sucesso": False,
                "mensagem": "Empresa não encontrada"
            }
        
        return {
            "sucesso": True,
            "empresa": {
                "id": empresa.id,
                "nome": empresa.nome,
                "cnpj": empresa.cnpj,
                "cnpj_formatado": empresa.cnpj_formatado,
                "contador": empresa.contador_nome,
                "crc": empresa.contador_crc
            }
        }


# ============================================================================
# MAIN PARA TESTE
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        caminho = sys.argv[1]
        print(f"Importando: {caminho}")
        print("="*60)
        
        resultado = importar_balancete_completo(caminho)
        
        print(f"Sucesso: {resultado.sucesso}")
        print(f"Mensagem: {resultado.mensagem}")
        
        if resultado.empresa:
            print(f"\nEmpresa:")
            print(f"  ID: {resultado.empresa.id}")
            print(f"  Nome: {resultado.empresa.nome}")
            print(f"  CNPJ: {resultado.empresa.cnpj_formatado}")
            print(f"  Nova: {resultado.empresa_criada}")
        
        if resultado.dados_mensais:
            dm = resultado.dados_mensais
            print(f"\nDados Mensais ({dm.mes:02d}/{dm.ano}):")
            print(f"  Receita Bruta: R$ {dm.receita_bruta:,.2f}")
            print(f"  Lucro Líquido: R$ {dm.lucro_liquido:,.2f}")
            print(f"  Ativo Total: R$ {dm.ativo_total:,.2f}")
        
        if resultado.avisos:
            print(f"\nAvisos: {resultado.avisos}")
        
        if resultado.dados_completos:
            import json
            print("\n" + "="*60)
            print("DADOS COMPLETOS (JSON):")
            print("="*60)
            print(json.dumps(resultado.dados_completos, indent=2, ensure_ascii=False, default=str))
    else:
        print("Uso: python servico_importacao.py <arquivo>")
        print("Formatos suportados: PDF")
