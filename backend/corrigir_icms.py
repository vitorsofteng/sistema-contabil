#!/usr/bin/env python3
"""
CORREÇÃO DE ICMS NO BANCO DE DADOS
Este script calcula o ICMS faltante a partir dos dados existentes
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def corrigir_icms():
    print("="*60)
    print("CORREÇÃO: ICMS NO BANCO DE DADOS")
    print("="*60)
    
    try:
        from data.database import get_db, DadosMensal, Empresa
        
        with get_db() as db:
            # Buscar empresa E. TOCANTINS
            empresa = db.query(Empresa).filter(
                Empresa.razao_social.ilike('%tocantins%')
            ).first()
            
            if not empresa:
                print("\n❌ Empresa E. TOCANTINS não encontrada!")
                return
            
            print(f"\n✓ Empresa: {empresa.razao_social} (ID: {empresa.id})")
            
            # Buscar dados mensais
            dados = db.query(DadosMensal).filter(
                DadosMensal.empresa_id == empresa.id,
                DadosMensal.deleted_at.is_(None)
            ).order_by(DadosMensal.ano, DadosMensal.mes).all()
            
            if not dados:
                print("\n❌ Nenhum dado mensal encontrado!")
                return
            
            print(f"\n{len(dados)} meses encontrados. Corrigindo...\n")
            
            corrigidos = 0
            
            for d in dados:
                # Valores atuais
                impostos_total = d.impostos or 0
                soma_outros = (d.pis or 0) + (d.cofins or 0) + (d.irpj or 0) + (d.csll or 0) + (d.iss or 0)
                icms_atual = d.icms or 0
                
                print(f"📅 {d.mes:02d}/{d.ano}:")
                print(f"   Impostos (total): R$ {impostos_total:,.2f}")
                print(f"   Soma (PIS+COFINS+IRPJ+CSLL+ISS): R$ {soma_outros:,.2f}")
                print(f"   ICMS atual: R$ {icms_atual:,.2f}")
                
                # Se ICMS está zerado mas temos impostos total maior que a soma
                if icms_atual == 0 and impostos_total > soma_outros:
                    icms_calculado = impostos_total - soma_outros
                    print(f"   🔧 ICMS calculado: R$ {icms_calculado:,.2f}")
                    
                    # Atualizar no banco
                    d.icms = icms_calculado
                    corrigidos += 1
                    print(f"   ✓ ICMS atualizado!")
                elif icms_atual > 0:
                    print(f"   ✓ ICMS já está preenchido")
                else:
                    # Se impostos_total também está zerado, tentar usar deducoes_receita
                    deducoes = d.deducoes_receita or 0
                    if deducoes > soma_outros:
                        icms_calculado = deducoes - soma_outros
                        # Descontar devoluções (aproximadamente 2% da receita)
                        if icms_calculado > 0:
                            print(f"   🔧 ICMS estimado de deduções: R$ {icms_calculado:,.2f}")
                            d.icms = icms_calculado
                            d.impostos = deducoes
                            corrigidos += 1
                            print(f"   ✓ ICMS e impostos atualizados!")
                    else:
                        print(f"   ⚠️ Não foi possível calcular ICMS")
            
            if corrigidos > 0:
                db.commit()
                print(f"\n✅ {corrigidos} registros corrigidos!")
                print("\n👉 Agora gere uma nova análise para ver a carga correta.")
            else:
                print("\n✓ Nenhuma correção necessária.")
                
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    corrigir_icms()
