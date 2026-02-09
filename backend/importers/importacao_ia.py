#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serviço de Importação com IA
============================

Usa Claude API para extrair dados de qualquer arquivo contábil,
independente do sistema de origem.

Funciona com:
- PDF de balancetes

- Imagens de relatórios
- Qualquer layout/sistema

Custo aproximado: R$ 0,05 - 0,20 por importação

Autor: Kontabil
Versão: 1.0
"""

import os
import json
import base64
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field, asdict
import httpx

# Configuração da API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"  # Bom custo-benefício


@dataclass
class ResultadoImportacaoIA:
    """Resultado da importação via IA."""
    sucesso: bool
    dados: Dict = field(default_factory=dict)
    empresa: str = ""
    cnpj: str = ""
    periodo: str = ""
    ano: int = 0
    mes: int = 0
    sistema_detectado: str = ""
    campos_extraidos: List[str] = field(default_factory=list)
    confianca: str = ""  # alta, média, baixa
    observacoes: List[str] = field(default_factory=list)
    erro: str = ""
    custo_estimado: float = 0.0
    tokens_usados: int = 0
    
    def to_dict(self):
        return asdict(self)


# =============================================================================
# EXTRAÇÃO DE CONTEÚDO
# =============================================================================

def extrair_texto_pdf(arquivo_bytes: bytes) -> Tuple[str, List[str]]:
    """
    Extrai texto de PDF.
    Retorna (texto, lista_de_imagens_base64)
    """
    texto = ""
    imagens = []
    
    # Tenta pdfplumber primeiro (melhor para tabelas)
    try:
        import pdfplumber
        import io
        
        with pdfplumber.open(io.BytesIO(arquivo_bytes)) as pdf:
            for pagina in pdf.pages:
                texto += pagina.extract_text() or ""
                texto += "\n\n"
        
        if texto.strip():
            return texto.strip(), []
    except ImportError:
        pass
    except Exception as e:
        pass
    
    # Tenta PyPDF2 como fallback
    try:
        from PyPDF2 import PdfReader
        import io
        
        reader = PdfReader(io.BytesIO(arquivo_bytes))
        for pagina in reader.pages:
            texto += pagina.extract_text() or ""
            texto += "\n\n"
        
        if texto.strip():
            return texto.strip(), []
    except ImportError:
        pass
    except Exception:
        pass
    
    # Se não conseguiu extrair texto, converte para imagem
    # (para PDFs escaneados)
    try:
        import fitz  # PyMuPDF
        import io
        
        doc = fitz.open(stream=arquivo_bytes, filetype="pdf")
        for pagina in doc:
            pix = pagina.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom
            img_bytes = pix.tobytes("png")
            img_base64 = base64.standard_b64encode(img_bytes).decode('utf-8')
            imagens.append(img_base64)
        
        return "", imagens
    except ImportError:
        pass
    except Exception:
        pass
    
    # Último recurso: envia o PDF como está para a IA tentar
    return "", []


def extrair_texto_csv(arquivo_bytes: bytes) -> str:
    """Extrai texto de arquivo CSV."""
    # Tenta diferentes encodings
    for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
        try:
            texto = arquivo_bytes.decode(encoding)
            # Verifica se parece válido
            if ',' in texto or ';' in texto or '\t' in texto:
                return texto
        except:
            continue
    return ""


def preparar_conteudo_para_ia(arquivo_bytes: bytes, nome_arquivo: str) -> Tuple[str, List[Dict]]:
    """
    Prepara o conteúdo do arquivo para enviar à IA.
    Retorna (texto, lista_de_imagens)
    """
    extensao = nome_arquivo.lower().split('.')[-1]
    
    if extensao == 'pdf':
        texto, imagens_base64 = extrair_texto_pdf(arquivo_bytes)
        imagens = [{"type": "base64", "media_type": "image/png", "data": img} for img in imagens_base64]
        return texto, imagens
    
    elif extensao == 'csv':
        texto = extrair_texto_csv(arquivo_bytes)
        return texto, []
    
    elif extensao == 'txt':
        # Arquivo de texto simples
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                return arquivo_bytes.decode(encoding), []
            except:
                continue
        return "", []
    
    elif extensao in ['png', 'jpg', 'jpeg', 'webp']:
        # Imagem direta
        media_type = f"image/{'jpeg' if extensao in ['jpg', 'jpeg'] else extensao}"
        img_base64 = base64.standard_b64encode(arquivo_bytes).decode('utf-8')
        return "", [{"type": "base64", "media_type": media_type, "data": img_base64}]
    
    else:
        # Tenta como texto genérico
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                return arquivo_bytes.decode(encoding), []
            except:
                continue
    
    return "", []


# =============================================================================
# PROMPT PARA A IA
# =============================================================================

PROMPT_EXTRACAO = """Você é um especialista em contabilidade brasileira. Sua tarefa é extrair TODOS os valores financeiros deste documento contábil.

## REGRA CRÍTICA SOBRE PATRIMÔNIO LÍQUIDO E ROE

⚠️ MUITO IMPORTANTE PARA INDICADORES FINANCEIROS:

No balancete, o grupo "2.3 PATRIMÔNIO LÍQUIDO" geralmente contém APENAS o Capital Social e reservas.
O "RESULTADO DO EXERCÍCIO" (grupo 3) fica em conta separada, mas PERTENCE ECONOMICAMENTE ao PL durante o ano fiscal.

**Para calcular indicadores como ROE corretamente:**
- PL Contábil (grupo 2.3) = Capital Social + Reservas (ex: R$ 100.000)
- Resultado do Exercício (grupo 3) = Lucro acumulado no ano (ex: R$ 95.941)
- **PL TOTAL para indicadores = PL Contábil + Resultado do Exercício** (ex: R$ 195.941)

Exemplo ERRADO de ROE:
- ROE = 95.941 / 100.000 = 95,9% ❌ (usando só Capital Social)

Exemplo CORRETO de ROE:
- ROE = 95.941 / (100.000 + 95.941) = 49,0% ✅ (usando PL Total)

**Você DEVE extrair o campo "patrimonio_liquido_total" calculado como:**
patrimonio_liquido_total = patrimonio_liquido (grupo 2.3) + resultado_exercicio (grupo 3)

## REGRA CRÍTICA SOBRE BALANCETES BRASILEIROS

⚠️ ATENÇÃO: Em balancetes brasileiros (especialmente do Domínio Sistemas e similares), a DRE (Demonstração do Resultado) apresenta valores **ACUMULADOS NO EXERCÍCIO**, NÃO valores mensais!

Isso significa que:
- O balancete de Janeiro mostra receita de R$ 50.000 → receita de janeiro = 50.000
- O balancete de Fevereiro mostra receita de R$ 120.000 → isso JÁ INCLUI janeiro! Receita de fev = 70.000
- O balancete de Março mostra receita de R$ 190.000 → isso JÁ INCLUI jan+fev! Receita de mar = 70.000

**NUNCA SOME** valores de diferentes meses - o último mês já contém o total acumulado!

Se o documento mostrar APENAS UM período (ex: "01/03/2024 - 31/03/2024"), extraia os valores do "Saldo Atual" que JÁ É o valor acumulado do exercício até aquele mês.

## ONDE ENCONTRAR O LUCRO LÍQUIDO

⚠️ MUITO IMPORTANTE: O lucro líquido correto está no "RESUMO DO BALANCETE" no final do documento!

Há DUAS linhas diferentes que você pode encontrar:
- "RESULTADO DO MES" → NÃO usar! É só o movimento do mês atual
- "RESULTADO DO EXERCÍCIO" → USAR ESTE! É o lucro ACUMULADO do exercício

Exemplo de RESUMO DO BALANCETE:
```
RESULTADO DO MES          21.118,55
RESULTADO DO EXERCÍCIO    95.941,82C   ← USE ESTE VALOR (95.941,82)
```

**NÃO USE** a conta 402 "RESULTADO LÍQUIDO DO PERÍODO ANTES DO IRPJ, CSLL E PARTICIP." 
Essa conta mostra o resultado ANTES de descontar impostos, não é o lucro líquido final!

Procure especificamente por (em ordem de prioridade):
1. "RESULTADO DO EXERCÍCIO" no RESUMO DO BALANCETE → É O MAIS CONFIÁVEL!
2. "LUCRO LÍQUIDO DO EXERCÍCIO"
3. Evite usar "RESULTADO LÍQUIDO DO PERÍODO ANTES DO IRPJ" (conta 402)

INSTRUÇÕES DE EXTRAÇÃO:
1. Analise o documento COMPLETAMENTE antes de responder
2. Extraia TODOS os valores numéricos que encontrar
3. Valores em formato brasileiro (1.234,56) devem ser convertidos para formato decimal (1234.56)
4. Se um valor aparece como "1.234.567,89", converta para 1234567.89
5. Valores com D (débito) ou C (crédito) no final: extraia apenas o número
6. NUNCA retorne 0.00 se houver um valor no documento - procure com atenção!

MAPEAMENTO DE CONTAS CONTÁBEIS:
- Contas que começam com 1 = ATIVO
- Contas que começam com 2 = PASSIVO  
- Contas que começam com 3 = RESULTADO (DRE) - Receitas e Despesas
- Contas que começam com 4 = Alternativo para Custos/Despesas (depende do plano de contas)

CAMPOS A EXTRAIR (procure por estes termos ou similares):
- receita_bruta: "Receita Bruta de Vendas", "Faturamento Bruto", contas 3.1.1
- receita_servicos: "Receita de Serviços", "Prestação de Serviços"
- receita: "Receita Líquida" = receita_bruta - deduções
- custos: "Custo dos Produtos", "CMV", "CPV", "Custo das Mercadorias"
- despesas_operacionais: "Despesas Operacionais", soma de despesas com vendas + administrativas
- despesas_financeiras: "Despesas Financeiras", "Juros Passivos"
- lucro_liquido: "RESULTADO DO EXERCÍCIO" (no resumo!), "Lucro Líquido"
- ativo_total: "ATIVO" (conta raiz, geralmente código 1)
- ativo_circulante: "Ativo Circulante", contas 1.1
- disponivel: "Disponível", "Disponibilidades"
- caixa: "Caixa", "Caixa e Equivalentes"
- bancos: "Bancos", "Bancos Conta Movimento"
- clientes: "Clientes", "Contas a Receber", "Duplicatas a Receber"
- estoques: "Estoques", "Mercadorias"
- passivo_total: "PASSIVO" (conta raiz, código 2) - INCLUI Patrimônio Líquido
- passivo_circulante: "Passivo Circulante", contas 2.1
- passivo_nao_circulante: "Passivo Não Circulante", "Exigível a Longo Prazo"
- fornecedores: "Fornecedores", "Contas a Pagar"
- patrimonio_liquido: "Patrimônio Líquido", "PL", contas 2.3 ou 2.4
- capital_social: "Capital Social", "Capital Integralizado"
- resultado_exercicio: "RESULTADO DO EXERCÍCIO" (grupo 3) - mesmo valor do lucro_liquido

## IMPOSTOS - MUITO IMPORTANTE! ##
Os impostos devem ser extraídos das DEDUÇÕES DA RECEITA (grupo 3.1.2), NÃO do passivo:
- icms: conta 426 ou "(-)ICMS" no grupo 3.1.2.03 - Imposto sobre circulação
- pis: conta 429 ou "(-)PIS" no grupo 3.1.2.03
- cofins: conta 428 ou "(-)COFINS" no grupo 3.1.2.03
- iss: "(-)ISS" nas deduções (se empresa de serviços)
- irpj: "(-)IRPJ", "(-)Imposto de Renda" nas deduções (se houver)
- csll: "(-)CSLL", "(-)Contribuição Social" nas deduções (se houver)
- impostos: SOMA de ICMS + ISS + PIS + COFINS + IRPJ + CSLL (total das deduções tributárias)
- folha: "Folha de Pagamento", "Salários", "Despesas com Pessoal"

ATENÇÃO: NÃO confunda impostos A RECOLHER (passivo, grupo 2.1.2) com impostos DEDUZIDOS (DRE, grupo 3.1.2.03)!
Use SEMPRE os valores do grupo 3.1.2.03 (deduções), pois refletem a carga tributária real sobre o faturamento.

Retorne APENAS um JSON válido (sem ```json, sem explicações):

{
  "sucesso": true,
  "tipo_documento": "balancete",
  "sistema_origem": "nome do sistema ou desconhecido",
  "empresa": "NOME DA EMPRESA EXATAMENTE COMO APARECE",
  "cnpj": "XX.XXX.XXX/XXXX-XX",
  "periodo": "MM/AAAA",
  "ano": 2024,
  "mes": 1,
  "confianca": "alta",
  "valores_acumulados": true,
  "dados": {
    "receita_bruta": 150000.00,
    "receita_servicos": 0.00,
    "deducoes_receita": 0.00,
    "receita": 150000.00,
    "custos": 80000.00,
    "despesas_operacionais": 30000.00,
    "despesas_financeiras": 5000.00,
    "lucro_liquido": 35000.00,
    "ativo_total": 500000.00,
    "ativo_circulante": 200000.00,
    "disponivel": 50000.00,
    "caixa": 10000.00,
    "bancos": 40000.00,
    "clientes": 100000.00,
    "estoques": 50000.00,
    "passivo_total": 500000.00,
    "passivo_circulante": 150000.00,
    "passivo_nao_circulante": 100000.00,
    "fornecedores": 80000.00,
    "patrimonio_liquido": 250000.00,
    "patrimonio_liquido_total": 285000.00,
    "capital_social": 100000.00,
    "resultado_exercicio": 35000.00,
    "icms": 12000.00,
    "iss": 0.00,
    "pis": 1500.00,
    "cofins": 7500.00,
    "irpj": 0.00,
    "csll": 0.00,
    "impostos": 21000.00,
    "folha": 25000.00
  },
  "observacoes": []
}

REGRAS FINAIS:
- Todos os valores DEVEM ser números decimais (não strings)
- Use 0.00 APENAS se o campo realmente não existir no documento
- Se encontrar um valor, SEMPRE inclua-o (não deixe como 0)
- Converta valores brasileiros: "1.234,56" → 1234.56
- LUCRO LÍQUIDO: Use APENAS "RESULTADO DO EXERCÍCIO" no RESUMO DO BALANCETE (final do documento)
- NÃO use "RESULTADO LÍQUIDO DO PERÍODO ANTES DO IRPJ" (conta 402) - esse valor NÃO é o lucro final!
- Lembre-se: valores da DRE são ACUMULADOS no exercício!
- PATRIMÔNIO LÍQUIDO TOTAL: SEMPRE calcule como PL (grupo 2.3) + Resultado do Exercício (grupo 3)
- resultado_exercicio deve ter o MESMO VALOR que lucro_liquido (ambos vêm do RESUMO DO BALANCETE)

Analise o documento abaixo com MÁXIMA ATENÇÃO:
"""


# =============================================================================
# CHAMADA À API
# =============================================================================

def chamar_claude_api(texto: str, imagens: List[Dict] = None) -> Tuple[Dict, int]:
    """
    Chama a API do Claude para extrair dados.
    Retorna (resposta_dict, tokens_usados)
    """
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY não configurada. Defina a variável de ambiente.")
    
    # Monta o conteúdo da mensagem
    content = []
    
    # Adiciona imagens primeiro (se houver)
    if imagens:
        for img in imagens[:5]:  # Máximo 5 imagens
            content.append({
                "type": "image",
                "source": img
            })
    
    # Adiciona o texto
    prompt_completo = PROMPT_EXTRACAO
    if texto:
        prompt_completo += f"\n\n--- CONTEÚDO DO DOCUMENTO ---\n\n{texto[:50000]}"  # Limita a 50k chars
    elif not imagens:
        raise ValueError("Nenhum conteúdo para analisar")
    
    content.append({
        "type": "text",
        "text": prompt_completo
    })
    
    # Faz a requisição
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": MODEL,
        "max_tokens": 4096,
        "messages": [
            {"role": "user", "content": content}
        ]
    }
    
    try:
        import time as _time_mod
        
        MAX_RETRIES = 3
        RETRY_DELAYS = [8, 20, 40]
        
        with httpx.Client(timeout=60.0) as client:
            for attempt in range(MAX_RETRIES):
                try:
                    response = client.post(ANTHROPIC_API_URL, headers=headers, json=payload)
                    response.raise_for_status()
                    
                    result = response.json()
                    
                    # Extrai tokens usados
                    tokens = result.get("usage", {})
                    total_tokens = tokens.get("input_tokens", 0) + tokens.get("output_tokens", 0)
                    
                    # Extrai o texto da resposta
                    resposta_texto = ""
                    for block in result.get("content", []):
                        if block.get("type") == "text":
                            resposta_texto += block.get("text", "")
                    
                    # Parse do JSON - remove markdown code blocks
                    resposta_texto = resposta_texto.strip()
                    if resposta_texto.startswith("```"):
                        resposta_texto = re.sub(r'^```json?\s*', '', resposta_texto)
                        resposta_texto = re.sub(r'\s*```$', '', resposta_texto)
                    
                    dados = json.loads(resposta_texto)
                    return dados, total_tokens
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 401:
                        raise ValueError("API key inválida")
                    elif e.response.status_code in (429, 529, 503):
                        if attempt < MAX_RETRIES - 1:
                            delay = RETRY_DELAYS[attempt]
                            logger.warning(f"Rate limit (HTTP {e.response.status_code}), retry {attempt+1}/{MAX_RETRIES} em {delay}s...")
                            _time_mod.sleep(delay)
                            continue
                        else:
                            raise ValueError("Limite de requisições excedido após múltiplas tentativas.")
                    else:
                        raise ValueError(f"Erro na API: {e.response.status_code}")
                
                except httpx.ReadTimeout:
                    if attempt < MAX_RETRIES - 1:
                        delay = RETRY_DELAYS[attempt]
                        logger.warning(f"Timeout na API, retry {attempt+1}/{MAX_RETRIES} em {delay}s...")
                        _time_mod.sleep(delay)
                        continue
                    else:
                        raise ValueError("Timeout na comunicação com a IA.")
            
            raise ValueError("Limite de requisições excedido após múltiplas tentativas.")
    
    except json.JSONDecodeError:
        raise ValueError("Erro ao processar resposta da IA")
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Erro na comunicação com a IA: {str(e)}")


# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================

def importar_com_ia(
    arquivo_bytes: bytes, 
    nome_arquivo: str,
    empresa_id: int = None
) -> ResultadoImportacaoIA:
    """
    Importa um arquivo contábil usando IA.
    
    Args:
        arquivo_bytes: Conteúdo do arquivo
        nome_arquivo: Nome do arquivo com extensão
        empresa_id: ID da empresa (opcional)
    
    Returns:
        ResultadoImportacaoIA com os dados extraídos
    """
    resultado = ResultadoImportacaoIA(sucesso=False)
    
    try:
        # 1. Prepara o conteúdo
        print(f"[IA] Processando arquivo: {nome_arquivo}")
        texto, imagens = preparar_conteudo_para_ia(arquivo_bytes, nome_arquivo)
        
        if not texto and not imagens:
            resultado.erro = "Não foi possível ler o conteúdo do arquivo"
            print(f"[IA] ERRO: {resultado.erro}")
            return resultado
        
        print(f"[IA] Conteúdo extraído: {len(texto)} chars, {len(imagens)} imagens")
        if texto:
            print(f"[IA] Preview do texto: {texto[:500]}...")
        
        # 2. Chama a IA
        print(f"[IA] Chamando Claude API...")
        dados_ia, tokens = chamar_claude_api(texto, imagens)
        
        print(f"[IA] Resposta recebida: {json.dumps(dados_ia, indent=2, ensure_ascii=False)[:1000]}")
        
        # 3. Processa resultado
        if not dados_ia.get("sucesso", False):
            resultado.erro = "IA não conseguiu extrair os dados"
            resultado.observacoes = dados_ia.get("observacoes", [])
            print(f"[IA] ERRO: {resultado.erro}")
            return resultado
        
        # 4. Monta resultado
        resultado.sucesso = True
        resultado.dados = dados_ia.get("dados", {})
        resultado.empresa = dados_ia.get("empresa", "")
        resultado.cnpj = dados_ia.get("cnpj", "")
        resultado.periodo = dados_ia.get("periodo", "")
        resultado.ano = dados_ia.get("ano", 0)
        resultado.mes = dados_ia.get("mes", 0)
        resultado.sistema_detectado = dados_ia.get("sistema_origem", "desconhecido")
        resultado.confianca = dados_ia.get("confianca", "media")
        resultado.observacoes = dados_ia.get("observacoes", [])
        resultado.tokens_usados = tokens
        
        # =================================================================
        # VALIDAÇÃO: Corrigir confusões comuns da IA
        # =================================================================
        dados = resultado.dados
        
        # Extrair valores para validação
        ativo = dados.get('ativo_total', 0) or 0
        patrimonio = dados.get('patrimonio_liquido', 0) or 0
        ativo_circ = dados.get('ativo_circulante', 0) or 0
        lucro = dados.get('lucro_liquido', 0) or 0
        resultado_exerc = dados.get('resultado_exercicio', 0) or 0
        receita = dados.get('receita_bruta', 0) or dados.get('receita', 0) or 0
        
        print(f"[IA] VALIDAÇÃO - Valores antes da correção:")
        print(f"[IA]   ativo_total: {ativo}, ativo_circ: {ativo_circ}, patrimonio: {patrimonio}")
        print(f"[IA]   lucro_liquido: {lucro}, resultado_exercicio: {resultado_exerc}")
        
        # 1. Se ativo_total < patrimonio_liquido, estão invertidos ou ativo está errado
        if ativo > 0 and patrimonio > 0 and ativo < patrimonio:
            print(f"[IA] CORREÇÃO: ativo_total ({ativo}) < patrimonio ({patrimonio}) - corrigindo")
            dados['ativo_total'] = patrimonio
            dados['patrimonio_liquido'] = ativo
            resultado.observacoes.append("Corrigido: ativo_total e patrimonio_liquido estavam invertidos")
            ativo = patrimonio
        
        # 2. Se ativo_total = patrimonio_liquido ou muito próximos, provavelmente IA confundiu
        if ativo > 0 and patrimonio > 0 and abs(ativo - patrimonio) < patrimonio * 0.1:
            if ativo_circ > ativo:
                print(f"[IA] CORREÇÃO: ativo_total ({ativo}) ≈ patrimonio ({patrimonio}), usando ativo_circulante ({ativo_circ})")
                dados['ativo_total'] = ativo_circ
                resultado.observacoes.append("Corrigido: ativo_total estava próximo do patrimonio, usado ativo_circulante")
                ativo = ativo_circ
        
        # 3. Se ativo_total é muito pequeno comparado com ativo_circulante
        if ativo_circ > 0 and (ativo == 0 or ativo < ativo_circ * 0.5):
            print(f"[IA] CORREÇÃO: ativo_total ({ativo}) muito baixo, usando ativo_circulante ({ativo_circ})")
            dados['ativo_total'] = ativo_circ
            resultado.observacoes.append("Corrigido: ativo_total era menor que ativo_circulante")
            ativo = ativo_circ
        
        # 4. Se lucro_liquido != resultado_exercicio, usar o maior (provavelmente acumulado)
        if resultado_exerc > 0 and lucro > 0 and abs(lucro - resultado_exerc) > 100:
            if resultado_exerc > lucro:
                print(f"[IA] CORREÇÃO: lucro_liquido ({lucro}) < resultado_exercicio ({resultado_exerc}) - usando maior")
                dados['lucro_liquido'] = resultado_exerc
                resultado.observacoes.append("Corrigido: usado resultado_exercicio (acumulado) como lucro_liquido")
                lucro = resultado_exerc
            else:
                print(f"[IA] CORREÇÃO: resultado_exercicio ({resultado_exerc}) < lucro_liquido ({lucro}) - mantendo lucro")
        
        # 5. NOVA VALIDAÇÃO: Se ROA > 50%, provavelmente algo está errado
        # ROA normal de empresas é entre 5% e 30%
        if ativo > 0 and lucro > 0:
            roa_calculado = (lucro / ativo) * 100
            print(f"[IA] ROA calculado: {roa_calculado:.2f}%")
            
            if roa_calculado > 50:
                # ROA muito alto, provavelmente ativo está errado
                print(f"[IA] ALERTA: ROA ({roa_calculado:.2f}%) muito alto, verificando dados...")
                
                # Se ativo_circulante > ativo_total atual, usar ativo_circulante
                if ativo_circ > ativo:
                    print(f"[IA] CORREÇÃO: Usando ativo_circulante ({ativo_circ}) como ativo_total")
                    dados['ativo_total'] = ativo_circ
                    resultado.observacoes.append(f"Corrigido: ROA estava {roa_calculado:.1f}%, ajustado ativo_total")
                    ativo = ativo_circ
                
                # Se ainda está alto e patrimônio é muito pequeno comparado ao lucro
                # pode ser que patrimônio esteja sendo usado como ativo
                roa_novo = (lucro / ativo) * 100 if ativo > 0 else 0
                if roa_novo > 50 and lucro > patrimonio:
                    # Estimar ativo baseado em ROA razoável (20%)
                    ativo_estimado = lucro / 0.20  # ROA de 20%
                    if ativo_estimado > ativo:
                        print(f"[IA] CORREÇÃO: ROA ainda alto ({roa_novo:.2f}%), estimando ativo baseado em ROA 20%")
                        # Não sobrescrever automaticamente, mas avisar
                        resultado.observacoes.append(f"ATENÇÃO: ROA de {roa_novo:.1f}% pode indicar ativo_total incorreto")
        
        # 6. NOVA VALIDAÇÃO: Verificar consistência Ativo = Passivo + PL
        passivo_circ = dados.get('passivo_circulante', 0) or 0
        passivo_nao_circ = dados.get('passivo_nao_circulante', 0) or 0
        passivo_total = passivo_circ + passivo_nao_circ + patrimonio
        
        if ativo > 0 and passivo_total > 0:
            diferenca_pct = abs(ativo - passivo_total) / ativo * 100
            if diferenca_pct > 10:
                print(f"[IA] ALERTA: Ativo ({ativo}) ≠ Passivo+PL ({passivo_total}), diferença: {diferenca_pct:.1f}%")
                resultado.observacoes.append(f"Verificar: diferença entre Ativo e Passivo+PL de {diferenca_pct:.1f}%")
        
        resultado.dados = dados
        
        print(f"[IA] VALIDAÇÃO - Valores após correção:")
        print(f"[IA]   ativo_total: {dados.get('ativo_total', 0)}, lucro_liquido: {dados.get('lucro_liquido', 0)}")
        
        # Calcula custo estimado (Claude Sonnet: ~$3/1M input, ~$15/1M output)
        resultado.custo_estimado = round((tokens / 1000) * 0.005 * 5.0, 4)
        
        # Lista campos extraídos (com valor > 0)
        resultado.campos_extraidos = [k for k, v in resultado.dados.items() if v and v > 0]
        
        print(f"[IA] Campos extraídos com valor > 0: {resultado.campos_extraidos}")
        print(f"[IA] Dados completos: {resultado.dados}")
        
        # Adiciona ano/mes aos dados se não estiver
        if resultado.ano and 'ano' not in resultado.dados:
            resultado.dados['ano'] = resultado.ano
        if resultado.mes and 'mes' not in resultado.dados:
            resultado.dados['mes'] = resultado.mes
        
        print(f"[IA] Importação concluída com sucesso!")
        return resultado
        
    except ValueError as e:
        resultado.erro = str(e)
        print(f"[IA] ERRO ValueError: {resultado.erro}")
        return resultado
    except Exception as e:
        resultado.erro = f"Erro inesperado: {str(e)}"
        print(f"[IA] ERRO Exception: {resultado.erro}")
        import traceback
        traceback.print_exc()
        return resultado


def verificar_configuracao() -> Dict:
    """Verifica se a API está configurada corretamente."""
    return {
        "configurado": bool(ANTHROPIC_API_KEY),
        "modelo": MODEL,
        "api_url": ANTHROPIC_API_URL,
        "mensagem": "API configurada" if ANTHROPIC_API_KEY else "Defina ANTHROPIC_API_KEY nas variáveis de ambiente"
    }


# =============================================================================
# TESTE
# =============================================================================

if __name__ == "__main__":
    print("=== Verificação de Configuração ===")
    config = verificar_configuracao()
    print(f"Configurado: {config['configurado']}")
    print(f"Modelo: {config['modelo']}")
    print(f"Mensagem: {config['mensagem']}")
    
    if config['configurado']:
        print("\n=== Teste com texto de exemplo ===")
        texto_teste = """
        BALANCETE
        Empresa: TESTE LTDA
        CNPJ: 12.345.678/0001-90
        Período: 01/2024
        
        1 ATIVO                     100.000,00D
        1.1 ATIVO CIRCULANTE         80.000,00D
        1.1.1 DISPONÍVEL             30.000,00D
        1.1.2 CLIENTES               50.000,00D
        2 PASSIVO                   100.000,00C
        2.1 PASSIVO CIRCULANTE       40.000,00C
        2.3 PATRIMÔNIO LÍQUIDO       60.000,00C
        """
        
        resultado = importar_com_ia(texto_teste.encode('utf-8'), "teste.txt")
        print(f"Sucesso: {resultado.sucesso}")
        print(f"Empresa: {resultado.empresa}")
        print(f"Dados: {resultado.dados}")
        print(f"Tokens: {resultado.tokens_usados}")
        print(f"Custo estimado: R$ {resultado.custo_estimado}")
