#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Teste de Sucesso de Instalações - Environment Dev

Este script testa o sucesso das instalações realizadas pelo projeto,
com foco especial no SGDK e suas dependências (Java e Make).
"""

import os
import sys
import subprocess
import logging
import platform
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
import time

# Adicionar o diretório raiz ao path para importar módulos do projeto
sys.path.insert(0, str(Path(__file__).parent))

from core.component_manager import ComponentManager
from core.retro_devkit_manager import RetroDevKitManager
from utils.env_checker import check_path_for_executable, check_env_var_exists
from utils.permission_checker import is_admin, check_write_permission
from utils.disk_space import get_disk_space, format_size

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_installation_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class InstallationTester:
    """Classe para testar o sucesso das instalações do Environment Dev"""
    
    def __init__(self):
        self.results = {
            'system_info': {},
            'dependencies': {},
            'components': {},
            'sgdk': {},
            'overall_status': 'UNKNOWN'
        }
        self.component_manager = None
        self.retro_manager = None
        
    def run_full_test(self) -> Dict:
        """Executa todos os testes de instalação"""
        logger.info("🚀 Iniciando teste completo de instalações...")
        
        try:
            # 1. Informações do sistema
            self._collect_system_info()
            
            # 2. Testar dependências básicas
            self._test_basic_dependencies()
            
            # 3. Testar dependências do SGDK
            self._test_sgdk_dependencies()
            
            # 4. Testar componentes principais
            self._test_main_components()
            
            # 5. Testar SGDK especificamente
            self._test_sgdk_installation()
            
            # 6. Determinar status geral
            self._determine_overall_status()
            
            # 7. Gerar relatório
            self._generate_report()
            
        except Exception as e:
            logger.error(f"Erro durante os testes: {e}")
            self.results['overall_status'] = 'ERROR'
            self.results['error'] = str(e)
            
        return self.results
    
    def _collect_system_info(self):
        """Coleta informações básicas do sistema"""
        logger.info("📊 Coletando informações do sistema...")
        
        self.results['system_info'] = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'python_version': platform.python_version(),
            'is_admin': is_admin(),
            'working_directory': str(Path.cwd()),
            'disk_space': self._get_disk_info()
        }
        
        logger.info(f"Sistema: {self.results['system_info']['platform']} {self.results['system_info']['architecture']}")
        logger.info(f"Python: {self.results['system_info']['python_version']}")
        logger.info(f"Admin: {self.results['system_info']['is_admin']}")
    
    def _get_disk_info(self) -> Dict:
        """Obtém informações de espaço em disco"""
        try:
            disk_info = get_disk_space(str(Path.cwd()))
            return {
                'total': format_size(disk_info['total']),
                'used': format_size(disk_info['used']),
                'free': format_size(disk_info['free']),
                'free_bytes': disk_info['free']
            }
        except Exception as e:
            logger.warning(f"Erro ao obter informações de disco: {e}")
            return {'error': str(e)}
    
    def _test_basic_dependencies(self):
        """Testa dependências básicas do sistema"""
        logger.info("🔍 Testando dependências básicas...")
        
        basic_deps = {
            'python3': ['python', '--version'],
            'pip': ['pip', '--version'],
            'git': ['git', '--version'],
            '7zip': ['7z'] if platform.system() == 'Windows' else ['7z', '--help']
        }
        
        for dep_name, test_cmd in basic_deps.items():
            self.results['dependencies'][dep_name] = self._test_command(dep_name, test_cmd)
    
    def _test_sgdk_dependencies(self):
        """Testa especificamente as dependências do SGDK"""
        logger.info("☕ Testando dependências do SGDK (Java e Make)...")
        
        # Testar Java
        java_result = self._test_java_installation()
        self.results['dependencies']['java'] = java_result
        
        # Testar Make
        make_result = self._test_make_installation()
        self.results['dependencies']['make'] = make_result
        
        # Testar Microsoft Visual C++ Redistributable
        vcredist_result = self._test_vcredist()
        self.results['dependencies']['vcredist'] = vcredist_result
    
    def _test_java_installation(self) -> Dict:
        """Testa a instalação do Java de forma robusta"""
        logger.info("☕ Testando instalação do Java...")
        
        result = {
            'installed': False,
            'version': None,
            'java_home': None,
            'path_accessible': False,
            'javac_available': False,
            'details': []
        }
        
        try:
            # Testar comando java
            java_test = subprocess.run(['java', '-version'], 
                                     capture_output=True, text=True, timeout=10)
            if java_test.returncode == 0:
                result['installed'] = True
                result['path_accessible'] = True
                # Extrair versão do stderr (Java imprime versão no stderr)
                version_output = java_test.stderr
                if 'version' in version_output:
                    result['version'] = version_output.split('\n')[0]
                result['details'].append("✅ Comando 'java' funciona")
            else:
                result['details'].append("❌ Comando 'java' falhou")
                
            # Testar javac
            javac_test = subprocess.run(['javac', '-version'], 
                                      capture_output=True, text=True, timeout=10)
            if javac_test.returncode == 0:
                result['javac_available'] = True
                result['details'].append("✅ Comando 'javac' funciona")
            else:
                result['details'].append("❌ Comando 'javac' não disponível")
                
            # Verificar JAVA_HOME
            java_home = os.environ.get('JAVA_HOME')
            if java_home and Path(java_home).exists():
                result['java_home'] = java_home
                result['details'].append(f"✅ JAVA_HOME configurado: {java_home}")
            else:
                result['details'].append("⚠️ JAVA_HOME não configurado ou inválido")
                
        except subprocess.TimeoutExpired:
            result['details'].append("⏰ Timeout ao testar Java")
        except FileNotFoundError:
            result['details'].append("❌ Java não encontrado no PATH")
        except Exception as e:
            result['details'].append(f"❌ Erro ao testar Java: {e}")
            
        return result
    
    def _test_make_installation(self) -> Dict:
        """Testa a instalação do Make"""
        logger.info("🔨 Testando instalação do Make...")
        
        result = {
            'installed': False,
            'version': None,
            'path_accessible': False,
            'details': []
        }
        
        try:
            # Testar comando make
            make_test = subprocess.run(['make', '--version'], 
                                     capture_output=True, text=True, timeout=10)
            if make_test.returncode == 0:
                result['installed'] = True
                result['path_accessible'] = True
                # Extrair versão
                version_output = make_test.stdout
                if version_output:
                    result['version'] = version_output.split('\n')[0]
                result['details'].append("✅ Comando 'make' funciona")
            else:
                result['details'].append("❌ Comando 'make' falhou")
                
            # Verificar se make está no PATH
            make_path = shutil.which('make')
            if make_path:
                result['details'].append(f"✅ Make encontrado em: {make_path}")
            else:
                result['details'].append("❌ Make não encontrado no PATH")
                
        except subprocess.TimeoutExpired:
            result['details'].append("⏰ Timeout ao testar Make")
        except FileNotFoundError:
            result['details'].append("❌ Make não encontrado")
        except Exception as e:
            result['details'].append(f"❌ Erro ao testar Make: {e}")
            
        return result
    
    def _test_vcredist(self) -> Dict:
        """Testa a presença do Visual C++ Redistributable"""
        result = {
            'installed': False,
            'details': []
        }
        
        if platform.system() == 'Windows':
            try:
                # Verificar no registro do Windows
                import winreg
                key_path = r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64"
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                        result['installed'] = True
                        result['details'].append("✅ Visual C++ Redistributable encontrado no registro")
                except FileNotFoundError:
                    result['details'].append("❌ Visual C++ Redistributable não encontrado no registro")
            except ImportError:
                result['details'].append("⚠️ Não foi possível verificar registro (winreg não disponível)")
        else:
            result['details'].append("ℹ️ Verificação de VCRedist não aplicável (não é Windows)")
            result['installed'] = True  # Não é necessário em sistemas não-Windows
            
        return result
    
    def _test_main_components(self):
        """Testa componentes principais do projeto"""
        logger.info("🧩 Testando componentes principais...")
        
        try:
            self.component_manager = ComponentManager()
            components_status = self.component_manager.get_installation_status()
            
            # Focar nos componentes mais importantes
            important_components = [
                'Java Runtime Environment',
                'Make',
                'Microsoft Visual C++ Redistributable',
                'Git',
                '7-Zip'
            ]
            
            for comp_name in important_components:
                if comp_name in components_status:
                    self.results['components'][comp_name] = {
                        'installed': components_status[comp_name],
                        'details': [f"Status: {'✅ Instalado' if components_status[comp_name] else '❌ Não instalado'}"]
                    }
                else:
                    self.results['components'][comp_name] = {
                        'installed': False,
                        'details': ["⚠️ Componente não encontrado na configuração"]
                    }
                    
        except Exception as e:
            logger.error(f"Erro ao testar componentes principais: {e}")
            self.results['components']['error'] = str(e)
    
    def _test_sgdk_installation(self):
        """Testa especificamente a instalação do SGDK"""
        logger.info("🎮 Testando instalação do SGDK...")
        
        result = {
            'installed': False,
            'sgdk_home': None,
            'bin_accessible': False,
            'sample_compile': False,
            'dependencies_ok': False,
            'details': []
        }
        
        try:
            # Verificar SGDK_HOME
            sgdk_home = os.environ.get('SGDK_HOME')
            if sgdk_home and Path(sgdk_home).exists():
                result['sgdk_home'] = sgdk_home
                result['details'].append(f"✅ SGDK_HOME configurado: {sgdk_home}")
                
                # Verificar estrutura de diretórios
                sgdk_path = Path(sgdk_home)
                expected_dirs = ['bin', 'inc', 'lib', 'src']
                missing_dirs = []
                
                for dir_name in expected_dirs:
                    if not (sgdk_path / dir_name).exists():
                        missing_dirs.append(dir_name)
                        
                if not missing_dirs:
                    result['installed'] = True
                    result['details'].append("✅ Estrutura de diretórios do SGDK completa")
                else:
                    result['details'].append(f"❌ Diretórios ausentes: {', '.join(missing_dirs)}")
                    
                # Verificar executáveis
                bin_path = sgdk_path / 'bin'
                if bin_path.exists():
                    executables = ['sgdk-gcc.exe', 'sgdk-objcopy.exe'] if platform.system() == 'Windows' else ['sgdk-gcc', 'sgdk-objcopy']
                    found_exes = []
                    for exe in executables:
                        if (bin_path / exe).exists():
                            found_exes.append(exe)
                            
                    if found_exes:
                        result['bin_accessible'] = True
                        result['details'].append(f"✅ Executáveis encontrados: {', '.join(found_exes)}")
                    else:
                        result['details'].append("❌ Executáveis do SGDK não encontrados")
            else:
                result['details'].append("❌ SGDK_HOME não configurado ou diretório não existe")
                
            # Verificar dependências
            java_ok = self.results['dependencies'].get('java', {}).get('installed', False)
            make_ok = self.results['dependencies'].get('make', {}).get('installed', False)
            vcredist_ok = self.results['dependencies'].get('vcredist', {}).get('installed', False)
            
            if java_ok and make_ok and vcredist_ok:
                result['dependencies_ok'] = True
                result['details'].append("✅ Todas as dependências do SGDK estão instaladas")
            else:
                missing_deps = []
                if not java_ok: missing_deps.append('Java')
                if not make_ok: missing_deps.append('Make')
                if not vcredist_ok: missing_deps.append('VCRedist')
                result['details'].append(f"❌ Dependências ausentes: {', '.join(missing_deps)}")
                
            # Teste de compilação simples (se tudo estiver OK)
            if result['installed'] and result['dependencies_ok']:
                compile_result = self._test_sgdk_compilation(sgdk_home)
                result['sample_compile'] = compile_result['success']
                result['details'].extend(compile_result['details'])
                
        except Exception as e:
            result['details'].append(f"❌ Erro ao testar SGDK: {e}")
            
        self.results['sgdk'] = result
    
    def _test_sgdk_compilation(self, sgdk_home: str) -> Dict:
        """Testa compilação de um projeto simples com SGDK"""
        logger.info("🔨 Testando compilação com SGDK...")
        
        result = {
            'success': False,
            'details': []
        }
        
        try:
            # Criar diretório temporário para teste
            test_dir = Path.cwd() / 'temp_sgdk_test'
            test_dir.mkdir(exist_ok=True)
            
            # Criar arquivo C simples
            test_c_file = test_dir / 'test.c'
            test_c_content = '''
#include <genesis.h>

int main() {
    VDP_drawText("Hello SGDK!", 1, 1);
    while(1) {
        SYS_doVBlankProcess();
    }
    return 0;
}
'''
            
            with open(test_c_file, 'w') as f:
                f.write(test_c_content)
                
            # Tentar compilar
            compile_cmd = [
                'make',
                '-f', str(Path(sgdk_home) / 'makefile.gen'),
                f'PROJECT_DIR={test_dir}',
                'compile'
            ]
            
            compile_result = subprocess.run(
                compile_cmd,
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if compile_result.returncode == 0:
                result['success'] = True
                result['details'].append("✅ Compilação de teste bem-sucedida")
            else:
                result['details'].append(f"❌ Falha na compilação: {compile_result.stderr[:200]}...")
                
            # Limpar arquivos de teste
            shutil.rmtree(test_dir, ignore_errors=True)
            
        except subprocess.TimeoutExpired:
            result['details'].append("⏰ Timeout na compilação de teste")
        except Exception as e:
            result['details'].append(f"❌ Erro no teste de compilação: {e}")
            
        return result
    
    def _test_command(self, name: str, cmd: List[str]) -> Dict:
        """Testa um comando genérico"""
        result = {
            'installed': False,
            'details': []
        }
        
        try:
            test_result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if test_result.returncode == 0:
                result['installed'] = True
                result['details'].append(f"✅ {name} funciona")
            else:
                result['details'].append(f"❌ {name} falhou")
        except subprocess.TimeoutExpired:
            result['details'].append(f"⏰ Timeout ao testar {name}")
        except FileNotFoundError:
            result['details'].append(f"❌ {name} não encontrado")
        except Exception as e:
            result['details'].append(f"❌ Erro ao testar {name}: {e}")
            
        return result
    
    def _determine_overall_status(self):
        """Determina o status geral baseado nos resultados"""
        # Verificar dependências críticas
        critical_deps = ['java', 'make']
        deps_ok = all(
            self.results['dependencies'].get(dep, {}).get('installed', False)
            for dep in critical_deps
        )
        
        # Verificar SGDK
        sgdk_ok = self.results['sgdk'].get('installed', False)
        
        if deps_ok and sgdk_ok:
            self.results['overall_status'] = 'SUCCESS'
        elif deps_ok:
            self.results['overall_status'] = 'PARTIAL'
        else:
            self.results['overall_status'] = 'FAILED'
    
    def _generate_report(self):
        """Gera relatório detalhado dos testes"""
        logger.info("📋 Gerando relatório de testes...")
        
        # Salvar resultados em JSON
        with open('installation_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
            
        # Gerar relatório em texto
        self._generate_text_report()
        
        logger.info("✅ Relatório gerado: installation_test_results.json")
        logger.info("✅ Relatório em texto: installation_test_report.txt")
    
    def _generate_text_report(self):
        """Gera relatório em formato texto legível"""
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("RELATÓRIO DE TESTE DE INSTALAÇÕES - ENVIRONMENT DEV")
        report_lines.append("=" * 60)
        report_lines.append(f"Data/Hora: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Status Geral: {self.results['overall_status']}")
        report_lines.append("")
        
        # Informações do sistema
        report_lines.append("📊 INFORMAÇÕES DO SISTEMA:")
        report_lines.append("-" * 30)
        sys_info = self.results['system_info']
        report_lines.append(f"Sistema: {sys_info.get('platform', 'N/A')} {sys_info.get('architecture', 'N/A')}")
        report_lines.append(f"Python: {sys_info.get('python_version', 'N/A')}")
        report_lines.append(f"Administrador: {sys_info.get('is_admin', 'N/A')}")
        disk_info = sys_info.get('disk_space', {})
        if 'free' in disk_info:
            report_lines.append(f"Espaço livre: {disk_info['free']}")
        report_lines.append("")
        
        # Dependências
        report_lines.append("🔍 DEPENDÊNCIAS:")
        report_lines.append("-" * 30)
        for dep_name, dep_info in self.results['dependencies'].items():
            status = "✅" if dep_info.get('installed', False) else "❌"
            report_lines.append(f"{status} {dep_name.upper()}")
            for detail in dep_info.get('details', []):
                report_lines.append(f"   {detail}")
            report_lines.append("")
        
        # SGDK
        report_lines.append("🎮 SGDK:")
        report_lines.append("-" * 30)
        sgdk_info = self.results['sgdk']
        status = "✅" if sgdk_info.get('installed', False) else "❌"
        report_lines.append(f"{status} SGDK INSTALADO")
        for detail in sgdk_info.get('details', []):
            report_lines.append(f"   {detail}")
        report_lines.append("")
        
        # Resumo
        report_lines.append("📋 RESUMO:")
        report_lines.append("-" * 30)
        if self.results['overall_status'] == 'SUCCESS':
            report_lines.append("✅ Todas as instalações estão funcionando corretamente!")
            report_lines.append("   O SGDK e suas dependências estão prontos para uso.")
        elif self.results['overall_status'] == 'PARTIAL':
            report_lines.append("⚠️ Instalações parcialmente funcionais.")
            report_lines.append("   Dependências básicas OK, mas SGDK pode ter problemas.")
        else:
            report_lines.append("❌ Problemas detectados nas instalações.")
            report_lines.append("   Verifique os detalhes acima e reinstale os componentes necessários.")
        
        # Salvar relatório
        with open('installation_test_report.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

def main():
    """Função principal"""
    print("🚀 Iniciando teste de instalações do Environment Dev...")
    print("📋 Foco especial: SGDK e dependências (Java, Make)")
    print("=" * 60)
    
    tester = InstallationTester()
    results = tester.run_full_test()
    
    print("\n" + "=" * 60)
    print(f"🏁 RESULTADO FINAL: {results['overall_status']}")
    
    if results['overall_status'] == 'SUCCESS':
        print("✅ Todas as instalações estão funcionando!")
        print("🎮 SGDK pronto para desenvolvimento de jogos Sega Genesis!")
    elif results['overall_status'] == 'PARTIAL':
        print("⚠️ Algumas instalações precisam de atenção.")
        print("📋 Verifique o relatório detalhado.")
    else:
        print("❌ Problemas detectados nas instalações.")
        print("🔧 Execute o Environment Dev para corrigir os problemas.")
    
    print("\n📄 Relatórios gerados:")
    print("   - installation_test_results.json (dados completos)")
    print("   - installation_test_report.txt (relatório legível)")
    print("   - test_installation_results.log (log detalhado)")
    
    return results['overall_status'] == 'SUCCESS'

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)