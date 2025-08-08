#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create Distribution ZIP
Cria arquivo ZIP final para distribuição do Environment Dev Deep Evaluation.
"""

import zipfile
import os
from pathlib import Path
from datetime import datetime

def create_distribution_zip():
    """Cria arquivo ZIP para distribuição"""
    project_root = Path.cwd()
    package_dir = project_root / "deployment" / "EnvironmentDevDeepEvaluation_Portable"
    
    if not package_dir.exists():
        print("Erro: Pacote de deployment não encontrado!")
        print("Execute primeiro: python build_deployment.py")
        return False
    
    # Nome do arquivo ZIP
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"EnvironmentDevDeepEvaluation_v2.0_{timestamp}.zip"
    zip_path = project_root / "deployment" / zip_name
    
    print(f"Criando arquivo ZIP: {zip_name}")
    print(f"Origem: {package_dir}")
    print(f"Destino: {zip_path}")
    
    # Criar ZIP
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        file_count = 0
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = Path(root) / file
                # Caminho relativo dentro do ZIP
                arc_path = file_path.relative_to(package_dir.parent)
                zipf.write(file_path, arc_path)
                file_count += 1
                
                if file_count % 100 == 0:
                    print(f"  Processados: {file_count} arquivos...")
    
    # Verificar resultado
    zip_size = zip_path.stat().st_size / (1024 * 1024)  # MB
    
    print(f"\nArquivo ZIP criado com sucesso!")
    print(f"Nome: {zip_name}")
    print(f"Tamanho: {zip_size:.1f} MB")
    print(f"Arquivos: {file_count}")
    print(f"Localização: {zip_path}")
    
    # Criar arquivo de informações
    info_file = zip_path.with_suffix('.txt')
    info_content = f"""Environment Dev Deep Evaluation v2.0 - Pacote de Distribuição

INFORMAÇÕES DO PACOTE:
- Nome: {zip_name}
- Tamanho: {zip_size:.1f} MB
- Arquivos: {file_count}
- Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

COMO INSTALAR:
1. Extrair o arquivo ZIP
2. Executar 'Iniciar_Environment_Dev.bat' (Windows)
3. Ou executar './iniciar_environment_dev.sh' (Linux/Mac)

CONTEÚDO:
- Executável principal com todas as dependências
- Arquivos de configuração completos
- Documentação detalhada
- Scripts de inicialização
- Dados e exemplos

REQUISITOS:
- Windows 10/11, Linux ou macOS
- 2GB RAM mínimo
- 1GB espaço em disco

FUNCIONALIDADES:
- Detecção automática de componentes
- Sistema de instalação robusto
- Interface gráfica moderna
- Suporte ao Steam Deck
- SGDK 2.11 com instalação real
- Sistema de status persistente

Para suporte, consulte a documentação incluída no pacote.

Environment Dev Team - 2025
"""
    
    info_file.write_text(info_content, encoding='utf-8')
    print(f"Arquivo de informações: {info_file.name}")
    
    return True

if __name__ == "__main__":
    success = create_distribution_zip()
    if success:
        print("\nPacote de distribuição criado com sucesso!")
        print("Pronto para distribuição!")
    else:
        print("\nErro na criação do pacote de distribuição.")