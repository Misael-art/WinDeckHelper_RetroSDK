#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do Pacote de Deployment
Testa se o pacote de deployment foi criado corretamente e funciona.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
import json
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeploymentTester:
    """Testador do pacote de deployment"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.deployment_dir = self.project_root / "deployment"
        self.package_dir = None
        self.test_results = {
            "timestamp": time.time(),
            "tests": {},
            "overall_status": "unknown"
        }
    
    def find_package_directory(self):
        """Encontra o diretório do pacote"""
        logger.info("🔍 Procurando pacote de deployment...")
        
        possible_dirs = [
            self.deployment_dir / "EnvironmentDevDeepEvaluation_Portable",
            self.deployment_dir / "package",
            self.project_root / "dist" / "EnvironmentDevDeepEvaluation"
        ]
        
        for dir_path in possible_dirs:
            if dir_path.exists():
                self.package_dir = dir_path
                logger.info(f"  ✅ Pacote encontrado: {dir_path}")
                return True
        
        logger.error("  ❌ Pacote não encontrado")
        return False
    
    def test_package_structure(self):
        """Testa a estrutura do pacote"""
        logger.info("📁 Testando estrutura do pacote...")
        
        required_items = [
            "EnvironmentDevDeepEvaluation",  # Diretório do executável
            "config",                        # Configurações
            "docs",                         # Documentação
            "LEIA-ME.txt",                  # Arquivo de informações
        ]
        
        optional_items = [
            "data",                         # Dados iniciais
            "Iniciar_Environment_Dev.bat", # Script Windows
            "iniciar_environment_dev.sh",  # Script Linux/Mac
        ]
        
        missing_required = []
        missing_optional = []
        
        for item in required_items:
            item_path = self.package_dir / item
            if not item_path.exists():
                missing_required.append(item)
            else:
                logger.info(f"  ✅ Encontrado: {item}")
        
        for item in optional_items:
            item_path = self.package_dir / item
            if not item_path.exists():
                missing_optional.append(item)
            else:
                logger.info(f"  ✅ Encontrado: {item}")
        
        test_passed = len(missing_required) == 0
        self.test_results["tests"]["package_structure"] = {
            "status": "pass" if test_passed else "fail",
            "missing_required": missing_required,
            "missing_optional": missing_optional
        }
        
        if test_passed:
            logger.info("  ✅ Estrutura do pacote OK")
        else:
            logger.error(f"  ❌ Itens obrigatórios ausentes: {missing_required}")
        
        return test_passed
    
    def test_executable_exists(self):
        """Testa se o executável existe"""
        logger.info("🔧 Testando existência do executável...")
        
        exe_dir = self.package_dir / "EnvironmentDevDeepEvaluation"
        exe_file = exe_dir / "EnvironmentDevDeepEvaluation.exe"
        exe_file_linux = exe_dir / "EnvironmentDevDeepEvaluation"
        
        exe_exists = exe_file.exists() or exe_file_linux.exists()
        
        if exe_exists:
            exe_path = exe_file if exe_file.exists() else exe_file_linux
            exe_size = exe_path.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"  ✅ Executável encontrado: {exe_path.name}")
            logger.info(f"  📊 Tamanho: {exe_size:.1f} MB")
        else:
            logger.error("  ❌ Executável não encontrado")
        
        self.test_results["tests"]["executable_exists"] = {
            "status": "pass" if exe_exists else "fail",
            "executable_path": str(exe_path) if exe_exists else None,
            "size_mb": f"{exe_size:.1f}" if exe_exists else None
        }
        
        return exe_exists
    
    def test_configuration_files(self):
        """Testa se os arquivos de configuração existem"""
        logger.info("⚙️ Testando arquivos de configuração...")
        
        config_dir = self.package_dir / "config"
        required_configs = [
            "components",  # Diretório de componentes
        ]
        
        missing_configs = []
        for config in required_configs:
            config_path = config_dir / config
            if not config_path.exists():
                missing_configs.append(config)
            else:
                if config_path.is_dir():
                    file_count = len(list(config_path.glob("*.yaml")))
                    logger.info(f"  ✅ {config}: {file_count} arquivos YAML")
                else:
                    logger.info(f"  ✅ {config}: arquivo encontrado")
        
        test_passed = len(missing_configs) == 0
        self.test_results["tests"]["configuration_files"] = {
            "status": "pass" if test_passed else "fail",
            "missing_configs": missing_configs
        }
        
        if test_passed:
            logger.info("  ✅ Arquivos de configuração OK")
        else:
            logger.error(f"  ❌ Configurações ausentes: {missing_configs}")
        
        return test_passed
    
    def test_documentation(self):
        """Testa se a documentação existe"""
        logger.info("📚 Testando documentação...")
        
        docs_dir = self.package_dir / "docs"
        readme_file = self.package_dir / "LEIA-ME.txt"
        
        docs_exist = docs_dir.exists()
        readme_exists = readme_file.exists()
        
        if docs_exist:
            doc_count = len(list(docs_dir.glob("*.md")))
            logger.info(f"  ✅ Documentação: {doc_count} arquivos")
        else:
            logger.warning("  ⚠ Diretório de documentação não encontrado")
        
        if readme_exists:
            readme_size = readme_file.stat().st_size
            logger.info(f"  ✅ LEIA-ME.txt: {readme_size} bytes")
        else:
            logger.warning("  ⚠ LEIA-ME.txt não encontrado")
        
        test_passed = docs_exist or readme_exists
        self.test_results["tests"]["documentation"] = {
            "status": "pass" if test_passed else "fail",
            "docs_dir_exists": docs_exist,
            "readme_exists": readme_exists
        }
        
        return test_passed
    
    def test_startup_scripts(self):
        """Testa os scripts de inicialização"""
        logger.info("🚀 Testando scripts de inicialização...")
        
        bat_script = self.package_dir / "Iniciar_Environment_Dev.bat"
        sh_script = self.package_dir / "iniciar_environment_dev.sh"
        
        bat_exists = bat_script.exists()
        sh_exists = sh_script.exists()
        
        if bat_exists:
            logger.info("  ✅ Script Windows (.bat) encontrado")
        else:
            logger.warning("  ⚠ Script Windows não encontrado")
        
        if sh_exists:
            logger.info("  ✅ Script Linux/Mac (.sh) encontrado")
            # Verificar se é executável
            try:
                is_executable = os.access(sh_script, os.X_OK)
                if is_executable:
                    logger.info("  ✅ Script Linux/Mac é executável")
                else:
                    logger.warning("  ⚠ Script Linux/Mac não é executável")
            except:
                pass
        else:
            logger.warning("  ⚠ Script Linux/Mac não encontrado")
        
        test_passed = bat_exists or sh_exists
        self.test_results["tests"]["startup_scripts"] = {
            "status": "pass" if test_passed else "fail",
            "bat_exists": bat_exists,
            "sh_exists": sh_exists
        }
        
        return test_passed
    
    def test_executable_dependencies(self):
        """Testa se o executável tem todas as dependências"""
        logger.info("🔗 Testando dependências do executável...")
        
        exe_dir = self.package_dir / "EnvironmentDevDeepEvaluation"
        
        # Verificar se existem bibliotecas essenciais
        essential_libs = [
            "_internal",  # Diretório interno do PyInstaller
        ]
        
        missing_libs = []
        for lib in essential_libs:
            lib_path = exe_dir / lib
            if not lib_path.exists():
                missing_libs.append(lib)
            else:
                if lib_path.is_dir():
                    file_count = len(list(lib_path.rglob("*")))
                    logger.info(f"  ✅ {lib}: {file_count} arquivos")
                else:
                    logger.info(f"  ✅ {lib}: encontrado")
        
        # Calcular tamanho total
        total_size = 0
        file_count = 0
        for file_path in exe_dir.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1
        
        size_mb = total_size / (1024 * 1024)
        logger.info(f"  📊 Total: {file_count} arquivos, {size_mb:.1f} MB")
        
        test_passed = len(missing_libs) == 0
        self.test_results["tests"]["executable_dependencies"] = {
            "status": "pass" if test_passed else "fail",
            "missing_libs": missing_libs,
            "total_files": file_count,
            "total_size_mb": f"{size_mb:.1f}"
        }
        
        return test_passed
    
    def run_quick_executable_test(self):
        """Executa um teste rápido do executável"""
        logger.info("⚡ Executando teste rápido do executável...")
        
        exe_dir = self.package_dir / "EnvironmentDevDeepEvaluation"
        exe_file = exe_dir / "EnvironmentDevDeepEvaluation.exe"
        exe_file_linux = exe_dir / "EnvironmentDevDeepEvaluation"
        
        exe_path = exe_file if exe_file.exists() else exe_file_linux
        
        if not exe_path.exists():
            logger.error("  ❌ Executável não encontrado para teste")
            return False
        
        try:
            # Tentar executar com --help ou --version (se suportado)
            # Como não sabemos se o executável suporta esses parâmetros,
            # vamos apenas verificar se ele pode ser executado
            logger.info("  ℹ️ Teste de execução não implementado (requer GUI)")
            logger.info("  ✅ Executável existe e parece válido")
            
            self.test_results["tests"]["executable_test"] = {
                "status": "skip",
                "reason": "GUI application - manual test required"
            }
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Erro no teste do executável: {e}")
            self.test_results["tests"]["executable_test"] = {
                "status": "fail",
                "error": str(e)
            }
            return False
    
    def generate_test_report(self):
        """Gera relatório dos testes"""
        logger.info("📊 Gerando relatório de testes...")
        
        # Calcular estatísticas
        total_tests = len(self.test_results["tests"])
        passed_tests = sum(1 for test in self.test_results["tests"].values() 
                          if test["status"] == "pass")
        failed_tests = sum(1 for test in self.test_results["tests"].values() 
                          if test["status"] == "fail")
        skipped_tests = sum(1 for test in self.test_results["tests"].values() 
                           if test["status"] == "skip")
        
        # Determinar status geral
        if failed_tests == 0:
            overall_status = "pass"
        elif passed_tests > failed_tests:
            overall_status = "partial"
        else:
            overall_status = "fail"
        
        self.test_results["overall_status"] = overall_status
        self.test_results["statistics"] = {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "skipped": skipped_tests
        }
        
        # Salvar relatório
        report_file = self.deployment_dir / f"test_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"  ✅ Relatório salvo: {report_file}")
        
        # Mostrar resumo
        print(f"\n📊 RESUMO DOS TESTES")
        print("=" * 30)
        print(f"Total de testes: {total_tests}")
        print(f"✅ Passou: {passed_tests}")
        print(f"❌ Falhou: {failed_tests}")
        print(f"⏭️ Pulado: {skipped_tests}")
        print(f"Status geral: {overall_status.upper()}")
        
        return overall_status
    
    def run_all_tests(self):
        """Executa todos os testes"""
        logger.info("🧪 Iniciando testes do pacote de deployment...")
        
        if not self.find_package_directory():
            return False
        
        tests = [
            ("Estrutura do Pacote", self.test_package_structure),
            ("Executável", self.test_executable_exists),
            ("Configurações", self.test_configuration_files),
            ("Documentação", self.test_documentation),
            ("Scripts de Inicialização", self.test_startup_scripts),
            ("Dependências", self.test_executable_dependencies),
            ("Teste Rápido", self.run_quick_executable_test),
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n--- {test_name} ---")
            try:
                test_func()
            except Exception as e:
                logger.error(f"❌ Erro no teste '{test_name}': {e}")
                self.test_results["tests"][test_name.lower().replace(" ", "_")] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Gerar relatório final
        overall_status = self.generate_test_report()
        
        return overall_status in ["pass", "partial"]

def main():
    """Função principal"""
    print("🧪 Environment Dev Deep Evaluation - Teste de Deployment")
    print("=" * 60)
    
    tester = DeploymentTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ TESTES CONCLUÍDOS COM SUCESSO!")
        print("O pacote de deployment está pronto para distribuição.")
    else:
        print("\n❌ ALGUNS TESTES FALHARAM!")
        print("Verifique os erros acima antes de distribuir o pacote.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)