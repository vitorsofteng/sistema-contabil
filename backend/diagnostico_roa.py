#!/usr/bin/env python3
"""
DIAGNÓSTICO: DIFERENÇA NO ROA ENTRE IA E PARSER

Este script analisa os dados salvos no banco e identifica
por que o ROA está diferente entre importação IA e Parser.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def diagnostico():
    print("="*70)
    print("DIAGNÓSTICO: ROA ENTRE IMPORTAÇÃO IA E PARSER")
    print("="*70)
    
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
            
            print(f"\n{len(dados)} meses encontrados")
            
            print("\n" + "-"*70)
            print("DADOS RELEVANTES PARA ROA (Lucro/Ativo):")
            print("-"*70)
            
            for d in dados:
                print(f"\n📅 {d.mes:02d}/{d.ano}:")
                print(f"   lucro_liquido: R$ {d.lucro_liquido or 0:,.2f}")
                print(f"   ativo_total: R$ {d.ativo_total or 0:,.2f}")
                print(f"   ativo_circulante: R$ {d.ativo_circulante or 0:,.2f}")
                print(f"   patrimonio_liquido: R$ {d.patrimonio_liquido or 0:,.2f}")
                print(f"   capital_social: R$ {d.capital_social or 0:,.2f}")
                
                ll = d.lucro_liquido or 0
                at = d.ativo_total or 0
                ac = d.ativo_circulante or 0
                pl = d.patrimonio_liquido or 0
                
                # Calcular ROA com diferentes denominadores
                if at > 0:
                    roa_at = (ll / at) * 100
                    print(f"   ROA (Lucro/Ativo Total): {roa_at:.2f}%")
                else:
                    print(f"   ROA (Lucro/Ativo Total): N/A (ativo=0)")
                
                if ac > 0:
                    roa_ac = (ll / ac) * 100
                    print(f"   ROA (Lucro/Ativo Circ): {roa_ac:.2f}%")
                
                if pl > 0:
                    roe = (ll / pl) * 100
                    print(f"   ROE (Lucro/Patrimônio): {roe:.2f}%")
                
                # Verificar problemas
                if at == 0 and ac > 0:
                    print(f"   ⚠️  PROBLEMA: ativo_total está zerado mas ativo_circulante não!")
                
                if at > 0 and at == pl:
                    print(f"   ⚠️  PROBLEMA: ativo_total = patrimonio_liquido!")
                
                if at > 0 and ll > 0:
                    if (ll / at) * 100 > 50:
                        print(f"   ⚠️  ALERTA: ROA > 50% - verificar valores!")
            
            # Valores esperados do PDF março/2024
            print("\n" + "="*70)
            print("VALORES ESPERADOS (PDF Março/2024):")
            print("="*70)
            print(f"  lucro_liquido: R$ 118.670,69")
            print(f"  ativo_total: R$ 712.908,34")
            print(f"  ativo_circulante: R$ 708.931,10")
            print(f"  patrimonio_liquido: R$ 100.000,00 (capital) ou R$ 218.670,69 (com lucro)")
            print(f"  ROA correto: 16,65%")
                
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    diagnostico()
