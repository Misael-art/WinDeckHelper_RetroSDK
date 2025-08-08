#!/usr/bin/env python3
import sys
from pathlib import Path

# Adicionar o diretório raiz do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'config'))
sys.path.insert(0, str(project_root / 'utils'))

from loader import load_all_components

def check_emulators():
    print("Carregando componentes...")
    components_data = load_all_components()
    
    print(f"Tipo de dados retornados: {type(components_data)}")
    
    # O loader retorna um dicionário com categorias como chaves
    if isinstance(components_data, dict):
        print(f"Categorias disponíveis: {list(components_data.keys())}")
        
        # Procurar pela categoria de emuladores
        emulators_category = 'Emuladores (Windows)'
        if emulators_category in components_data:
            emulators = components_data[emulators_category]
            print(f"\nTotal de emuladores na categoria '{emulators_category}': {len(emulators)}")
            
            for emulator in sorted(emulators, key=lambda x: x['name']):
                print(f"- {emulator['name']}")
            
            # Verificar se Mednafen está presente
            mednafen_found = False
            for emulator in emulators:
                if 'Mednafen' in emulator['name']:
                    print(f"\n✅ Mednafen encontrado: {emulator['name']}")
                    mednafen_found = True
                    break
            
            if not mednafen_found:
                print("\n❌ Mednafen não encontrado na categoria de emuladores")
        else:
            print(f"\n❌ Categoria '{emulators_category}' não encontrada")
            print("Categorias disponíveis:")
            for cat in components_data.keys():
                print(f"  - {cat} ({len(components_data[cat])} componentes)")
    else:
        print("Estrutura de dados inesperada")

if __name__ == "__main__":
    check_emulators()