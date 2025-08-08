#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validador e Configurador do SGDK
Verifica se o SGDK foi instalado corretamente e configura o ambiente
"""

import os
import sys
from pathlib import Path
import subprocess
import json
from typing import Dict, List, Tuple, Optional

class SGDKValidator:
    def __init__(self, sgdk_path: str = "C:/Users/misae/RetroDevKits/retro_devkits/sgdk"):
        self.sgdk_path = Path(sgdk_path)
        self.required_files = {
            'bin': [
                'm68k-elf-gcc.exe',
                'm68k-elf-as.exe', 
                'm68k-elf-ld.exe',
                'm68k-elf-objcopy.exe',
                'm68k-elf-objdump.exe',
                'm68k-elf-strip.exe'
            ],
            'inc': [
                'genesis.h',
                'vdp.h',
                'sys.h',
                'joy.h',
                'sound.h'
            ],
            'lib': [
                'libmd.a'
            ]
        }
        
    def check_installation(self) -> Dict[str, any]:
        """Verifica se o SGDK está instalado corretamente"""
        results = {
            'installed': False,
            'missing_files': [],
            'found_files': [],
            'directories': {},
            'version': None,
            'errors': []
        }
        
        try:
            # Verifica se o diretório principal existe
            if not self.sgdk_path.exists():
                results['errors'].append(f"Diretório SGDK não encontrado: {self.sgdk_path}")
                return results
            
            # Verifica cada diretório e seus arquivos
            for dir_name, files in self.required_files.items():
                dir_path = self.sgdk_path / dir_name
                results['directories'][dir_name] = {
                    'exists': dir_path.exists(),
                    'files_found': [],
                    'files_missing': []
                }
                
                if dir_path.exists():
                    for file_name in files:
                        file_path = dir_path / file_name
                        if file_path.exists():
                            results['directories'][dir_name]['files_found'].append(file_name)
                            results['found_files'].append(str(file_path))
                        else:
                            results['directories'][dir_name]['files_missing'].append(file_name)
                            results['missing_files'].append(str(file_path))
                else:
                    results['directories'][dir_name]['files_missing'].extend(files)
                    results['missing_files'].extend([str(dir_path / f) for f in files])
            
            # Verifica se a instalação está completa
            results['installed'] = len(results['missing_files']) == 0
            
            # Tenta detectar a versão
            results['version'] = self._detect_version()
            
        except Exception as e:
            results['errors'].append(f"Erro durante verificação: {str(e)}")
        
        return results
    
    def _detect_version(self) -> Optional[str]:
        """Tenta detectar a versão do SGDK"""
        try:
            # Procura por arquivos de versão
            version_files = [
                self.sgdk_path / 'VERSION',
                self.sgdk_path / 'version.txt',
                self.sgdk_path / 'CHANGELOG.txt'
            ]
            
            for version_file in version_files:
                if version_file.exists():
                    with open(version_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()[:200]  # Primeiras linhas
                        # Procura por padrões de versão
                        import re
                        version_match = re.search(r'v?(\d+\.\d+(?:\.\d+)?)', content)
                        if version_match:
                            return version_match.group(1)
            
            # Tenta executar gcc para obter versão
            gcc_path = self.sgdk_path / 'bin' / 'm68k-elf-gcc.exe'
            if gcc_path.exists():
                result = subprocess.run(
                    [str(gcc_path), '--version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return "Detectado via GCC"
            
        except Exception:
            pass
        
        return None
    
    def create_project_template(self, project_name: str, project_path: str) -> bool:
        """Cria um template de projeto SGDK"""
        try:
            project_dir = Path(project_path)
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Estrutura do projeto
            (project_dir / 'src').mkdir(exist_ok=True)
            (project_dir / 'res').mkdir(exist_ok=True)
            (project_dir / 'inc').mkdir(exist_ok=True)
            
            # main.c
            main_content = f'''#include "genesis.h"

int main()
{{
    // Inicializa o sistema SGDK
    SYS_init();
    
    // Configura paleta e prioridade do texto
    VDP_setTextPalette(PAL0);
    VDP_setTextPriority(TRUE);
    
    // Limpa a tela
    VDP_clearPlane(BG_A, TRUE);
    
    // Exibe título do projeto
    VDP_drawText("{project_name}", 2, 2);
    VDP_drawText("Desenvolvido com SGDK", 2, 4);
    VDP_drawText("Pressione START para continuar", 2, 6);
    
    // Loop principal do jogo
    while(1)
    {{
        // Lê entrada do controle
        u16 joy = JOY_readJoypad(JOY_1);
        
        // Verifica se START foi pressionado
        if(joy & BUTTON_START)
        {{
            VDP_clearPlane(BG_A, TRUE);
            VDP_drawText("START pressionado!", 2, 10);
            VDP_drawText("Bem-vindo ao desenvolvimento MD!", 2, 12);
        }}
        
        // Aguarda próximo frame (60 FPS)
        SYS_doVBlankProcess();
    }}
    
    return 0;
}}
'''
            
            with open(project_dir / 'src' / 'main.c', 'w', encoding='utf-8') as f:
                f.write(main_content)
            
            # Makefile
            makefile_content = f'''# Makefile para {project_name}
# Gerado automaticamente pelo SGDK Validator

include $(SGDK_PATH)/makefile.gen

PROJECT_NAME = {project_name}

# Configurações específicas do projeto
CFLAGS += -DPROJECT_NAME=\"{project_name}\"

# Regras personalizadas podem ser adicionadas aqui
'''
            
            with open(project_dir / 'Makefile', 'w', encoding='utf-8') as f:
                f.write(makefile_content)
            
            # README do projeto
            readme_content = f'''# {project_name}

Projeto desenvolvido com SGDK para Mega Drive/Genesis.

## Compilação

1. Configure o ambiente SGDK:
   ```
   C:/Users/misae/RetroDevKits/retro_devkits/sgdk/setup_env.bat
   ```

2. Compile o projeto:
   ```
   make
   ```

3. O arquivo ROM será gerado em: `out/{project_name}.bin`

## Estrutura do Projeto

- `src/` - Código fonte C
- `res/` - Recursos (sprites, música, etc.)
- `inc/` - Headers personalizados
- `out/` - Arquivos compilados

## Desenvolvimento

- Edite `src/main.c` para implementar sua lógica
- Adicione recursos em `res/`
- Use headers personalizados em `inc/`

## Teste

Use um emulador como Gens, Fusion ou RetroArch para testar a ROM.
'''
            
            with open(project_dir / 'README.md', 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            print(f"✓ Projeto '{project_name}' criado em: {project_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar projeto: {e}")
            return False
    
    def generate_report(self) -> str:
        """Gera relatório detalhado da instalação"""
        results = self.check_installation()
        
        report = ["=== RELATÓRIO DE VALIDAÇÃO DO SGDK ==="]
        report.append(f"Caminho: {self.sgdk_path}")
        report.append(f"Status: {'✓ INSTALADO' if results['installed'] else '❌ INCOMPLETO'}")
        
        if results['version']:
            report.append(f"Versão: {results['version']}")
        
        report.append("\n=== DIRETÓRIOS E ARQUIVOS ===")
        
        for dir_name, dir_info in results['directories'].items():
            status = "✓" if dir_info['exists'] else "❌"
            report.append(f"{status} {dir_name}/")
            
            if dir_info['files_found']:
                for file in dir_info['files_found']:
                    report.append(f"  ✓ {file}")
            
            if dir_info['files_missing']:
                for file in dir_info['files_missing']:
                    report.append(f"  ❌ {file}")
        
        if results['errors']:
            report.append("\n=== ERROS ===")
            for error in results['errors']:
                report.append(f"❌ {error}")
        
        if not results['installed']:
            report.append("\n=== AÇÕES NECESSÁRIAS ===")
            report.append("1. Baixe o SGDK de: https://github.com/Stephane-D/SGDK/releases")
            report.append("2. Extraia todos os arquivos para o diretório SGDK")
            report.append("3. Execute este validador novamente")
        else:
            report.append("\n=== PRÓXIMOS PASSOS ===")
            report.append("1. Execute setup_env.bat para configurar variáveis")
            report.append("2. Crie um novo projeto com este validador")
            report.append("3. Compile e teste seu primeiro programa")
        
        return "\n".join(report)

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validador e Configurador do SGDK')
    parser.add_argument('--check', action='store_true', help='Verifica instalação do SGDK')
    parser.add_argument('--create-project', metavar='NAME', help='Cria novo projeto')
    parser.add_argument('--project-path', metavar='PATH', help='Caminho para o novo projeto')
    parser.add_argument('--sgdk-path', metavar='PATH', default='C:/Users/misae/RetroDevKits/retro_devkits/sgdk', help='Caminho do SGDK')
    
    args = parser.parse_args()
    
    validator = SGDKValidator(args.sgdk_path)
    
    if args.check or (not args.create_project):
        # Verifica instalação
        print(validator.generate_report())
        
        results = validator.check_installation()
        if not results['installed']:
            print("\n⚠️  SGDK não está completamente instalado")
            return False
    
    if args.create_project:
        project_path = args.project_path or f"./projects/{args.create_project}"
        success = validator.create_project_template(args.create_project, project_path)
        if not success:
            return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
