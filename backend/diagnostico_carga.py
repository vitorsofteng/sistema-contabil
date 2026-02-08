#!/usr/bin/env python3
"""
DIAGNÓSTICO COMPLETO - CARGA TRIBUTÁRIA
Execute este script para identificar onde está o problema
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def diagnostico():
    print("="*60)
    print("DIAGNÓSTICO: CARGA TRIBUTÁRIA")
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
                print("   Verifique se a empresa foi cadastrada.")
                return
            
            print(f"\n✓ Empresa encontrada: {empresa.razao_social} (ID: {empresa.id})")
            
            # Buscar dados mensais
            dados = db.query(DadosMensal).filter(
                DadosMensal.empresa_id == empresa.id,
                DadosMensal.deleted_at.is_(None)
            ).order_by(DadosMensal.ano, DadosMensal.mes).all()
            
            if not dados:
                print("\n❌ Nenhum dado mensal encontrado!")
                print("   Reimporte os PDFs.")
                return
            
            print(f"\n✓ {len(dados)} meses de dados encontrados")
            
            print("\n" + "-"*60)
            print("DADOS NO BANCO DE DADOS:")
            print("-"*60)
            
            total_problemas = 0
            
            for d in dados:
                print(f"\n📅 {d.mes:02d}/{d.ano}:")
                print(f"   Receita Bruta: R$ {d.receita_bruta or 0:,.2f}")
                print(f"   Campo 'impostos': R$ {d.impostos or 0:,.2f}")
                print(f"   Campo 'impostos_total': R$ {d.impostos_total or 0:,.2f}")
                print(f"   ICMS: R$ {d.icms or 0:,.2f}")
                print(f"   PIS: R$ {d.pis or 0:,.2f}")
                print(f"   COFINS: R$ {d.cofins or 0:,.2f}")
                print(f"   IRPJ: R$ {d.irpj or 0:,.2f}")
                print(f"   CSLL: R$ {d.csll or 0:,.2f}")
                print(f"   ISS: R$ {d.iss or 0:,.2f}")
                
                # Calcular soma dos impostos individuais
                soma_individuais = (d.icms or 0) + (d.pis or 0) + (d.cofins or 0) + (d.irpj or 0) + (d.csll or 0) + (d.iss or 0)
                print(f"   Soma impostos individuais: R$ {soma_individuais:,.2f}")
                
                # Verificar se há problema
                impostos_usado = d.impostos or 0
                rb = d.receita_bruta or 0
                
                if rb > 0:
                    carga_campo = (impostos_usado / rb) * 100
                    carga_soma = (soma_individuais / rb) * 100
                    print(f"   Carga (campo 'impostos'): {carga_campo:.2f}%")
                    print(f"   Carga (soma individuais): {carga_soma:.2f}%")
                    
                    # Verificar problema
                    if d.icms == 0 or d.icms is None:
                        print(f"   ⚠️  PROBLEMA: ICMS está zerado no banco!")
                        total_problemas += 1
                    
                    if impostos_usado < soma_individuais * 0.9:
                        print(f"   ⚠️  PROBLEMA: Campo 'impostos' menor que soma!")
                        total_problemas += 1
            
            print("\n" + "="*60)
            print("DIAGNÓSTICO:")
            print("="*60)
            
            if total_problemas > 0:
                print(f"\n❌ {total_problemas} problemas encontrados!")
                print("\n🔧 SOLUÇÃO: Os dados no banco estão incorretos.")
                print("   Você precisa:")
                print("   1. Excluir os dados atuais da empresa")
                print("   2. Reimportar os 3 PDFs")
                print("   3. Gerar nova análise")
            else:
                print("\n✓ Dados no banco parecem corretos!")
                print("   Se a carga ainda está errada, o problema está na análise.")
                print("   Tente gerar uma nova análise.")
                
    except Exception as e:
        print(f"\n❌ Erro ao executar diagnóstico: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    diagnostico()
