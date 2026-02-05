# Estratégia de Confiabilidade para Importação de Balancetes

## O Problema

Você tem dois métodos de extração:
- **Parser Local**: Controlável, previsível, mas precisa ser adaptado para cada sistema
- **IA (Claude)**: Flexível, mas pode "inventar" dados ou extrair incorretamente

E múltiplos sistemas contábeis diferentes (Domínio, Contmatic, Alterdata, etc).

---

## Solução: Sistema de Validação em 3 Camadas

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARQUIVO DO CLIENTE                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA 1: EXTRAÇÃO                                             │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │ Parser Local    │    │ IA (Fallback)   │                     │
│  │ (PREFERIDO)     │───▶│ (Só se falhar)  │                     │
│  │ - Domínio ✓     │    │ - Custo/chamada │                     │
│  │ - Contmatic     │    │ - Pode errar    │                     │
│  │ - Genérico      │    │                 │                     │
│  └─────────────────┘    └─────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA 2: VALIDAÇÃO AUTOMÁTICA (SEMPRE EXECUTA)                │
│                                                                  │
│  ✓ Ativo = Passivo + PL (±5%)                                   │
│  ✓ Receita ≥ Lucro                                               │
│  ✓ Valores positivos onde esperado                               │
│  ✓ Margens dentro de limites razoáveis                           │
│  ✓ Campos obrigatórios preenchidos                               │
│                                                                  │
│  Resultado: Score de Confiança (0-100)                           │
│  - 90-100: ✅ Confiável                                          │
│  - 70-89:  ⚠️ Revisar recomendado                                │
│  - 40-69:  🔶 Revisão obrigatória                                │
│  - 0-39:   ❌ Dados provavelmente errados                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAMADA 3: REVISÃO DO USUÁRIO (SEMPRE MOSTRA)                   │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ REVISÃO DE IMPORTAÇÃO           Score: 85/100 ⚠️          │  │
│  │                                                           │  │
│  │ Receita Bruta:     R$ 521.818,00  ✅                      │  │
│  │ Lucro Líquido:     R$ 284.743,10  ✅                      │  │
│  │ Ativo Total:       R$ 1.065.383   ✅                      │  │
│  │ Patrimônio Líq.:   R$ 384.743,10  ⚠️ [Editar]            │  │
│  │                                                           │  │
│  │ ⚠️ Alertas:                                               │  │
│  │ - PL difere 26% do calculado                              │  │
│  │                                                           │  │
│  │              [Cancelar]  [Salvar com Revisão]             │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Hierarquia de Confiança

| Prioridade | Fonte | Confiança | Quando Usar |
|------------|-------|-----------|-------------|
| 1️⃣ | Parser Específico (ex: Domínio) | 90-100% | Sistema conhecido |
| 2️⃣ | Parser Genérico | 70-90% | Sistema não identificado |
| 3️⃣ | IA como Fallback | 50-80% | Parser falhou |
| 4️⃣ | IA Forçada | 40-70% | Usuário solicitou |

---

## Regras de Validação Contábil

### Críticas (Bloqueia se falhar)
```
❌ Ativo = Passivo + PL (tolerância 10%)
❌ Lucro > Receita 
❌ Ativo Circulante > Ativo Total
❌ Receita Líquida > Receita Bruta
```

### Alertas (Permite, mas destaca)
```
⚠️ Equação com diferença 5-10%
⚠️ Margem líquida > 60%
⚠️ Carga tributária > 40%
⚠️ PL negativo (passivo a descoberto)
```

### Informativos
```
ℹ️ Campo zerado (pode ser legítimo)
ℹ️ Margem atípica para o setor
```

---

## Estratégia para Múltiplos Sistemas

### Opção A: Expandir Parsers Locais (RECOMENDADO)

Criar parser específico para cada sistema importante:

```python
# Já implementado
✅ parser_dominio.py      # Domínio Sistemas

# A implementar conforme demanda
□ parser_contmatic.py    # Contmatic Phoenix
□ parser_alterdata.py    # Alterdata
□ parser_fortes.py       # Fortes AC
□ parser_questor.py      # Questor
```

**Vantagens:**
- 100% controlável
- Sem custo de API
- Resultados previsíveis

**Desvantagens:**
- Trabalho inicial por sistema
- Manutenção quando sistema atualiza

### Opção B: IA com Validação Rigorosa

Usar IA para sistemas desconhecidos, MAS:
1. Sempre validar com regras contábeis
2. Sempre mostrar tela de revisão
3. Destacar campos com baixa confiança

### Opção C: Híbrido (MELHOR ABORDAGEM)

```
1. Detecta sistema automaticamente
2. Se conhece: usa parser específico
3. Se não conhece: tenta parser genérico
4. Se falha: usa IA com AVISO claro
5. SEMPRE valida
6. SEMPRE mostra revisão
```

---

## Configuração Recomendada

```python
# No arquivo de configuração

class ConfiguracaoImportacao:
    # Parser SEMPRE primeiro
    USAR_IA_COMO_FALLBACK = True  # IA só quando parser falha
    
    # NÃO comparar automaticamente (custo de API)
    COMPARAR_PARSER_IA = False
    
    # Score mínimo para aceitar sem revisão
    SCORE_MINIMO_AUTO_ACEITE = 90  # Bem alto
    
    # SEMPRE mostrar tela de revisão
    SEMPRE_REVISAR = True  # ⚠️ IMPORTANTE: Manter True
```

---

## Fluxo de Uso Recomendado

### Para o Contador (Usuário Final)

1. **Upload do arquivo**
   - Sistema detecta automaticamente o formato

2. **Extração automática**
   - Tenta parser local primeiro
   - Se falha, usa IA (se configurada)

3. **Tela de Revisão (SEMPRE)**
   - Mostra dados extraídos
   - Destaca alertas e inconsistências
   - Permite editar qualquer campo

4. **Confirmação**
   - Usuário revisa e confirma
   - Só salva após confirmação explícita

### Para Você (Desenvolvedor)

1. **Quando aparecer sistema novo frequente**
   - Crie parser específico
   - Adicione à detecção automática

2. **Quando usuário reportar erro**
   - Verifique se é problema de parser
   - Ajuste regras de extração

3. **Manutenção**
   - Acompanhe score médio de confiança
   - Sistemas com score baixo precisam de parser melhor

---

## Métricas de Sucesso

Acompanhe estes indicadores:

| Métrica | Meta | Ação se Fora |
|---------|------|--------------|
| Score médio Parser | > 85 | Melhorar parser |
| Score médio IA | > 70 | OK (IA é fallback) |
| % usando IA | < 20% | Criar mais parsers |
| Taxa de edição manual | < 30% | Melhorar extração |

---

## Conclusão

**A chave é: VALIDAÇÃO + REVISÃO OBRIGATÓRIA**

Não importa de onde vem o dado (parser ou IA), SEMPRE:
1. ✅ Validar com regras contábeis
2. ✅ Mostrar score de confiança
3. ✅ Destacar inconsistências
4. ✅ Permitir edição
5. ✅ Exigir confirmação antes de salvar

Isso garante que erros sejam detectados ANTES de entrar no sistema.
