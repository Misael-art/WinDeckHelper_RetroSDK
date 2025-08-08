#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deploy Complete - Script Master de Deployment
Executa todo o processo de criação do pacote de deployment do Environment Dev Deep Evaluation.
"""

import os
import sys
import subprocess
import logging
import time
from pathlib import Path
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MasterDeployer:
    """Deployer master que executa todo o processo"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.start_time = time.time()
        self.deployment_log = []
        
    def log_step(self, step_name, status, details=None):
        """Registra um passo do deployment"""
        entry = {
            "step": step_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.deployment_log.append(entry)
        
        status_icon = "✅" if status == "success" else "❌" if status == "error" else "⚠️"
        logger.info(f"{status_icon} {step_name}: {status}")
        if details:
            logger.info(f"   {details}")
    
    def run_script(self, script_name, description):
        """Executa um script Python"""
        logger.info(f"🚀 Executando: {description}")
        
        script_path = self.project_root / script_name
        if not script_path.exists():
            self.log_step(description, "error", f"Script não encontrado: {script_name}")
            return False
        
        try:
            result = subprocess.run([
                sys.executable, str(script_path)
            ], check=True, capture_output=True, text=True, cwd=self.project_root)
            
            self.log_step(description, "success", "Executado com sucesso")
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Código de saída: {e.returncode}"
            if e.stderr:
                error_msg += f"\nErro: {e.stderr[:200]}..."
            
            self.log_step(description, "error", error_msg)
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")
            return False
    
    def check_prerequisites(self):
        """Verifica pré-requisitos"""
        logger.info("🔍 Verificando pré-requisitos...")
        
        # Verificar Python
        python_version = sys.version_info
        if python_version < (3, 8):
            self.log_step("Python Version Check", "error", 
                         f"Python 3.8+ necessário, encontrado: {python_version}")
            return False
        
        self.log_step("Python Version Check", "success", 
                     f"Python {python_version.major}.{python_version.minor}")
        
        # Verificar arquivos essenciais
        essential_files = [
            "main.py",
            "core/__init__.py",
            "gui/__init__.py",
            "config/components",
            "requirements.txt"
        ]
        
        missing_files = []
        for file_path in essential_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.log_step("Essential Files Check", "error", 
                         f"Arquivos ausentes: {missing_files}")
            return False
        
        self.log_step("Essential Files Check", "success", 
                     f"{len(essential_files)} arquivos verificados")
        
        return True
    
    def install_dependencies(self):
        """Instala dependências necessárias"""
        logger.info("📦 Instalando dependências...")
        return self.run_script("install_build_dependencies.py", 
                              "Instalação de Dependências")
    
    def create_deployment_package(self):
        """Cria o pacote de deployment"""
        logger.info("🔨 Criando pacote de deployment...")
        return self.run_script("build_deployment.py", 
                              "Criação do Pacote")
    
    def test_deployment_package(self):
        """Testa o pacote criado"""
        logger.info("🧪 Testando pacote...")
        return self.run_script("test_deployment_package.py", 
                              "Teste do Pacote")
    
    def generate_final_report(self):
        """Gera relatório final do deployment"""
        logger.info("📊 Gerando relatório final...")
        
        total_time = time.time() - self.start_time
        
        # Contar sucessos e falhas
        successes = sum(1 for entry in self.deployment_log if entry["status"] == "success")
        errors = sum(1 for entry in self.deployment_log if entry["status"] == "error")
        warnings = sum(1 for entry in self.deployment_log if entry["status"] == "warning")
        
        # Status geral
        overall_status = "success" if errors == 0 else "partial" if successes > errors else "failed"
        
        report = {
            "deployment_info": {
                "project": "Environment Dev Deep Evaluation",
                "version": "2.0.0",
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": round(total_time, 2),
                "duration_formatted": f"{int(total_time // 60)}m {int(total_time % 60)}s"
            },
            "overall_status": overall_status,
            "statistics": {
                "total_steps": len(self.deployment_log),
                "successes": successes,
                "errors": errors,
                "warnings": warnings
            },
            "steps": self.deployment_log,
            "output_locations": {
                "deployment_dir": str(self.project_root / "deployment"),
                "package_dir": str(self.project_root / "deployment" / "EnvironmentDevDeepEvaluation_Portable"),
                "executable": "EnvironmentDevDeepEvaluation/EnvironmentDevDeepEvaluation.exe"
            }
        }
        
        # Salvar relatório
        report_file = self.project_root / f"deployment_master_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Mostrar resumo
        print(f"\n{'='*60}")
        print("📊 RELATÓRIO FINAL DO DEPLOYMENT")
        print(f"{'='*60}")
        print(f"🎯 Projeto: Environment Dev Deep Evaluation v2.0")
        print(f"⏱️ Duração: {report['deployment_info']['duration_formatted']}")
        print(f"📈 Status: {overall_status.upper()}")
        print(f"📊 Estatísticas:")
        print(f"   • Total de passos: {len(self.deployment_log)}")
        print(f"   • ✅ Sucessos: {successes}")
        print(f"   • ❌ Erros: {errors}")
        print(f"   • ⚠️ Avisos: {warnings}")
        
        if overall_status == "success":
            print(f"\n🎉 DEPLOYMENT CONCLUÍDO COM SUCESSO!")
            print(f"📁 Pacote disponível em: deployment/EnvironmentDevDeepEvaluation_Portable/")
            print(f"🚀 Execute: deployment/EnvironmentDevDeepEvaluation_Portable/Iniciar_Environment_Dev.bat")
        elif overall_status == "partial":
            print(f"\n⚠️ DEPLOYMENT CONCLUÍDO COM AVISOS")
            print(f"Verifique os avisos acima, mas o pacote deve funcionar.")
        else:
            print(f"\n❌ DEPLOYMENT FALHOU")
            print(f"Verifique os erros acima e tente novamente.")
        
        print(f"\n📄 Relatório detalhado: {report_file}")
        
        return overall_status == "success"
    
    def run_complete_deployment(self):
        """Executa o deployment completo"""
        print("🚀 Environment Dev Deep Evaluation - Deployment Completo")
        print("=" * 70)
        print(f"📅 Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 70)
        
        try:
            # 1. Verificar pré-requisitos
            if not self.check_prerequisites():
                logger.error("❌ Pré-requisitos não atendidos")
                return False
            
            # 2. Instalar dependências
            if not self.install_dependencies():
                logger.error("❌ Falha na instalação de dependências")
                return False
            
            # 3. Criar pacote
            if not self.create_deployment_package():
                logger.error("❌ Falha na criação do pacote")
                return False
            
            # 4. Testar pacote
            if not self.test_deployment_package():
                logger.warning("⚠️ Alguns testes falharam, mas continuando...")
            
            # 5. Gerar relatório final
            return self.generate_final_report()
            
        except KeyboardInterrupt:
            logger.info("⏹️ Deployment interrompido pelo usuário")
            self.log_step("Deployment", "error", "Interrompido pelo usuário")
            return False
        except Exception as e:
            logger.error(f"❌ Erro crítico no deployment: {e}")
            self.log_step("Deployment", "error", f"Erro crítico: {e}")
            return False

def main():
    """Função principal"""
    deployer = MasterDeployer()
    success = deployer.run_complete_deployment()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)