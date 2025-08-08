#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Completo de Teste de Instalação - env_dev

Este script verifica o sucesso das instalações realizadas pelo projeto env_dev,
com foco especial no SGDK e suas dependências críticas.

Autor: env_dev Project
Versão: 1.0
"""

import os
import sys
import json
import subprocess
import platform
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class InstallationTester:
    """Classe principal para testes de instalação"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {},
            'project_structure': {},
            'dependencies': {},
            'sgdk': {},
            'summary': {},
            'recommendations': []
        }
        self.project_root = Path(__file__).parent
        
    def run_all_tests(self) -> Dict:
        """Executa todos os testes de instalação"""
        print("🚀 INICIANDO TESTES DE INSTALAÇÃO - env_dev")
        print("=" * 60)
        
        # Coleta informações do sistema
        self._collect_system_info()
        
        # Verifica estrutura do projeto
        self._test_project_structure()
        
        # Testa dependências
        self._test_dependencies()
        
        # Testa SGDK
        self._test_sgdk()
        
        # Gera resumo e recomendações
        self._generate_summary()
        
        # Salva resultados
        self._save_results()
        
        return self.results
    
    def _collect_system_info(self):
        """Coleta informações do sistema"""
        print("\n📋 Coletando informações do sistema...")
        
        self.results['system_info'] = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'python_version': platform.python_version(),
            'user': os.getenv('USERNAME', os.getenv('USER', 'unknown')),
            'working_directory': str(Path.cwd()),
            'project_root': str(self.project_root)
        }
        
        print(f"   ✅ Sistema: {self.results['system_info']['platform']}")
        print(f"   ✅ Arquitetura: {self.results['system_info']['architecture']}")
        print(f"   ✅ Python: {self.results['system_info']['python_version']}")
    
    def _test_project_structure(self):
        """Verifica a estrutura do projeto"""
        print("\n🏗️ Verificando estrutura do projeto...")
        
        required_files = [
            'retro_devkit_manager.py',
            'config/retro_devkits.yaml',
            'config/runtimes.yaml',
            'config/dev_tools.yaml'
        ]
        
        required_dirs = [
            'core',
            'utils',
            'config',
            'installers'
        ]
        
        structure_results = {
            'files': {},
            'directories': {},
            'config_files': {}
        }
        
        # Verifica arquivos
        for file_path in required_files:
            full_path = self.project_root / file_path
            exists = full_path.exists()
            structure_results['files'][file_path] = {
                'exists': exists,
                'path': str(full_path),
                'size': full_path.stat().st_size if exists else 0
            }
            
            status = "✅" if exists else "❌"
            print(f"   {status} {file_path}")
        
        # Verifica diretórios
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            exists = full_path.exists() and full_path.is_dir()
            structure_results['directories'][dir_path] = {
                'exists': exists,
                'path': str(full_path)
            }
            
            status = "✅" if exists else "❌"
            print(f"   {status} {dir_path}/")
        
        # Verifica configurações YAML
        self._test_yaml_configs(structure_results)
        
        self.results['project_structure'] = structure_results
    
    def _test_yaml_configs(self, structure_results):
        """Testa a validade dos arquivos YAML"""
        yaml_files = [
            'config/retro_devkits.yaml',
            'config/runtimes.yaml', 
            'config/dev_tools.yaml'
        ]
        
        for yaml_file in yaml_files:
            yaml_path = self.project_root / yaml_file
            config_result = {
                'exists': yaml_path.exists(),
                'valid': False,
                'sgdk_found': False,
                'error': None
            }
            
            if yaml_path.exists():
                try:
                    import yaml
                    with open(yaml_path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    config_result['valid'] = True
                    
                    # Verifica se SGDK está presente
                    if yaml_file == 'config/retro_devkits.yaml' and data:
                        for key, value in data.items():
                            if 'sgdk' in key.lower() or (isinstance(value, dict) and 
                                'sega genesis' in str(value).lower()):
                                config_result['sgdk_found'] = True
                                break
                                
                except Exception as e:
                    config_result['error'] = str(e)
            
            structure_results['config_files'][yaml_file] = config_result
    
    def _test_dependencies(self):
        """Testa as dependências do SGDK"""
        print("\n🔧 Testando dependências...")
        
        dependencies = {
            'java': self._test_java(),
            'make': self._test_make(),
            'vcredist': self._test_vcredist(),
            'seven_zip': self._test_7zip()
        }
        
        self.results['dependencies'] = dependencies
        
        for dep_name, dep_result in dependencies.items():
            status = "✅" if dep_result['installed'] else "❌"
            print(f"   {status} {dep_name.upper()}: {'INSTALADO' if dep_result['installed'] else 'AUSENTE'}")
            if dep_result.get('version'):
                print(f"      Versão: {dep_result['version']}")
    
    def _test_java(self) -> Dict:
        """Testa a instalação do Java"""
        result = {
            'installed': False,
            'version': None,
            'java_home': None,
            'executable_path': None,
            'error': None
        }
        
        try:
            # Verifica JAVA_HOME
            java_home = os.getenv('JAVA_HOME')
            if java_home:
                result['java_home'] = java_home
            
            # Testa comando java
            java_path = shutil.which('java')
            if java_path:
                result['executable_path'] = java_path
                
                # Obtém versão
                proc = subprocess.run(['java', '-version'], 
                                    capture_output=True, text=True, timeout=10)
                if proc.returncode == 0:
                    result['installed'] = True
                    # Extrai versão do stderr (Java imprime versão no stderr)
                    version_output = proc.stderr
                    if 'version' in version_output:
                        result['version'] = version_output.split('\n')[0]
                        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _test_make(self) -> Dict:
        """Testa a instalação do Make"""
        result = {
            'installed': False,
            'version': None,
            'executable_path': None,
            'error': None
        }
        
        try:
            # Testa comando make
            make_path = shutil.which('make')
            if make_path:
                result['executable_path'] = make_path
                
                # Obtém versão
                proc = subprocess.run(['make', '--version'], 
                                    capture_output=True, text=True, timeout=10)
                if proc.returncode == 0:
                    result['installed'] = True
                    result['version'] = proc.stdout.split('\n')[0]
                        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _test_vcredist(self) -> Dict:
        """Testa a instalação do Visual C++ Redistributable"""
        result = {
            'installed': False,
            'versions': [],
            'error': None
        }
        
        if platform.system() != 'Windows':
            result['installed'] = True  # Não necessário em outros sistemas
            return result
        
        try:
            # Verifica no registro do Windows
            import winreg
            
            keys_to_check = [
                r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64",
                r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x86",
                r"SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x64",
                r"SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x86"
            ]
            
            for key_path in keys_to_check:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                        version, _ = winreg.QueryValueEx(key, "Version")
                        result['versions'].append(version)
                        result['installed'] = True
                except (FileNotFoundError, OSError):
                    continue
                    
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _test_7zip(self) -> Dict:
        """Testa a instalação do 7-Zip"""
        result = {
            'installed': False,
            'version': None,
            'executable_path': None,
            'error': None
        }
        
        try:
            # Testa comando 7z
            zip_path = shutil.which('7z')
            if zip_path:
                result['executable_path'] = zip_path
                result['installed'] = True
            else:
                # Verifica localizações comuns no Windows
                if platform.system() == 'Windows':
                    common_paths = [
                        r"C:\Program Files\7-Zip\7z.exe",
                        r"C:\Program Files (x86)\7-Zip\7z.exe"
                    ]
                    
                    for path in common_paths:
                        if os.path.exists(path):
                            result['executable_path'] = path
                            result['installed'] = True
                            break
                        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _test_sgdk(self):
        """Testa a instalação do SGDK"""
        print("\n🎮 Testando SGDK...")
        
        sgdk_result = {
            'installed': False,
            'sgdk_home': None,
            'bin_directory': None,
            'include_directory': None,
            'lib_directory': None,
            'executables': {},
            'headers': {},
            'compilation_test': None,
            'error': None
        }
        
        try:
            # Verifica SGDK_HOME
            sgdk_home = os.getenv('SGDK_HOME')
            if sgdk_home and os.path.exists(sgdk_home):
                sgdk_result['sgdk_home'] = sgdk_home
                
                # Verifica estrutura de diretórios
                bin_dir = os.path.join(sgdk_home, 'bin')
                inc_dir = os.path.join(sgdk_home, 'inc')
                lib_dir = os.path.join(sgdk_home, 'lib')
                
                sgdk_result['bin_directory'] = os.path.exists(bin_dir)
                sgdk_result['include_directory'] = os.path.exists(inc_dir)
                sgdk_result['lib_directory'] = os.path.exists(lib_dir)
                
                # Verifica executáveis importantes
                executables = ['sgdk-gcc.exe', 'rescomp.exe', 'bintos.exe']
                for exe in executables:
                    exe_path = os.path.join(bin_dir, exe)
                    sgdk_result['executables'][exe] = os.path.exists(exe_path)
                
                # Verifica headers importantes
                headers = ['genesis.h', 'types.h']
                for header in headers:
                    header_path = os.path.join(inc_dir, header)
                    sgdk_result['headers'][header] = os.path.exists(header_path)
                
                # Determina se está instalado
                if (sgdk_result['bin_directory'] and 
                    sgdk_result['include_directory'] and
                    any(sgdk_result['executables'].values())):
                    sgdk_result['installed'] = True
                    
                    # Testa compilação simples
                    sgdk_result['compilation_test'] = self._test_sgdk_compilation(sgdk_home)
            
            # Status do teste
            status = "✅" if sgdk_result['installed'] else "❌"
            print(f"   {status} SGDK: {'INSTALADO' if sgdk_result['installed'] else 'AUSENTE'}")
            
            if sgdk_result['sgdk_home']:
                print(f"      SGDK_HOME: {sgdk_result['sgdk_home']}")
            
            if sgdk_result['installed']:
                print(f"      Diretórios: bin={sgdk_result['bin_directory']}, inc={sgdk_result['include_directory']}, lib={sgdk_result['lib_directory']}")
                
        except Exception as e:
            sgdk_result['error'] = str(e)
        
        self.results['sgdk'] = sgdk_result
    
    def _test_sgdk_compilation(self, sgdk_home: str) -> Dict:
        """Testa compilação simples com SGDK"""
        test_result = {
            'success': False,
            'output': None,
            'error': None
        }
        
        try:
            # Cria arquivo de teste temporário
            test_dir = Path(sgdk_home) / 'test_compilation'
            test_dir.mkdir(exist_ok=True)
            
            test_c_file = test_dir / 'test.c'
            test_c_content = '''
#include "genesis.h"

int main() {
    return 0;
}
'''
            
            with open(test_c_file, 'w') as f:
                f.write(test_c_content)
            
            # Tenta compilar
            gcc_path = os.path.join(sgdk_home, 'bin', 'sgdk-gcc.exe')
            if os.path.exists(gcc_path):
                proc = subprocess.run(
                    [gcc_path, '-c', str(test_c_file)],
                    cwd=str(test_dir),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                test_result['success'] = proc.returncode == 0
                test_result['output'] = proc.stdout
                if proc.stderr:
                    test_result['error'] = proc.stderr
            
            # Limpa arquivos de teste
            if test_dir.exists():
                shutil.rmtree(test_dir, ignore_errors=True)
                
        except Exception as e:
            test_result['error'] = str(e)
        
        return test_result
    
    def _generate_summary(self):
        """Gera resumo dos testes"""
        print("\n📊 Gerando resumo...")
        
        # Conta sucessos e falhas
        deps_installed = sum(1 for dep in self.results['dependencies'].values() 
                           if dep['installed'])
        total_deps = len(self.results['dependencies'])
        
        sgdk_installed = self.results['sgdk']['installed']
        
        # Determina status geral
        if sgdk_installed and deps_installed == total_deps:
            overall_status = 'FULLY_READY'
            status_emoji = '🎉'
        elif sgdk_installed:
            overall_status = 'SGDK_READY_DEPS_MISSING'
            status_emoji = '⚠️'
        elif deps_installed > 0:
            overall_status = 'PARTIAL_DEPENDENCIES'
            status_emoji = '🔧'
        else:
            overall_status = 'CLEAN_SYSTEM'
            status_emoji = '🆕'
        
        # Gera recomendações
        recommendations = []
        
        if not self.results['dependencies']['java']['installed']:
            recommendations.append('Instalar Java Runtime Environment')
        
        if not self.results['dependencies']['make']['installed']:
            recommendations.append('Instalar Make (build tools)')
        
        if (platform.system() == 'Windows' and 
            not self.results['dependencies']['vcredist']['installed']):
            recommendations.append('Instalar Visual C++ Redistributable')
        
        if not sgdk_installed:
            recommendations.append('Instalar SGDK (Sega Genesis Development Kit)')
        
        if not recommendations:
            recommendations.append('Sistema pronto para desenvolvimento!')
        
        summary = {
            'overall_status': overall_status,
            'status_emoji': status_emoji,
            'dependencies_installed': deps_installed,
            'total_dependencies': total_deps,
            'sgdk_installed': sgdk_installed,
            'recommendations': recommendations
        }
        
        self.results['summary'] = summary
        self.results['recommendations'] = recommendations
        
        # Exibe resumo
        print(f"\n{status_emoji} STATUS GERAL: {overall_status}")
        print(f"   Dependências: {deps_installed}/{total_deps}")
        print(f"   SGDK: {'✅ INSTALADO' if sgdk_installed else '❌ AUSENTE'}")
        
        if recommendations:
            print("\n📋 RECOMENDAÇÕES:")
            for rec in recommendations:
                print(f"   • {rec}")
    
    def _save_results(self):
        """Salva os resultados em arquivo JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = self.project_root / f'installation_test_results_{timestamp}.json'
        
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Resultados salvos em: {results_file.name}")
            
        except Exception as e:
            print(f"\n❌ Erro ao salvar resultados: {e}")

def main():
    """Função principal"""
    print("🎮 TESTE COMPLETO DE INSTALAÇÃO - env_dev")
    print("Verificando SGDK e dependências...")
    print("=" * 60)
    
    tester = InstallationTester()
    results = tester.run_all_tests()
    
    print("\n" + "=" * 60)
    print("🏁 TESTE CONCLUÍDO!")
    
    # Exibe próximos passos
    if results['summary']['overall_status'] == 'FULLY_READY':
        print("\n🚀 PRÓXIMOS PASSOS:")
        print("   1. Criar um novo projeto SGDK")
        print("   2. Compilar um exemplo simples")
        print("   3. Testar em emulador")
    else:
        print("\n🔧 PRÓXIMOS PASSOS:")
        print("   1. Executar: python retro_devkit_manager.py")
        print("   2. Instalar dependências faltantes")
        print("   3. Executar este teste novamente")
    
    print("\nPressione Enter para sair...")
    input()
    
    return results

if __name__ == '__main__':
    main()