#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integração do SGDK com o Sistema de Componentes
Este script integra a instalação manual do SGDK com o sistema existente
"""

import os
import sys
import json
from pathlib import Path
import subprocess
from typing import Dict, List, Optional

# Adiciona o caminho do projeto ao sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "env_dev"))

try:
    from core.component_manager import ComponentManager
    from core.retro_devkit_logger import RetroDevkitLogger
    from utils.env_manager import EnvManager
except ImportError as e:
    print(f"⚠️  Módulos do sistema não encontrados: {e}")
    print("Executando em modo standalone...")
    ComponentManager = None
    RetroDevkitLogger = None
    EnvManager = None

class SGDKIntegration:
    def __init__(self):
        self.sgdk_path = Path("C:/Users/misae/RetroDevKits/retro_devkits/sgdk")
        self.logger = self._setup_logger()
        self.component_manager = self._setup_component_manager()
        
    def _setup_logger(self):
        """Configura o logger"""
        if RetroDevkitLogger:
            return RetroDevkitLogger("SGDK_Integration")
        else:
            import logging
            logging.basicConfig(level=logging.INFO)
            return logging.getLogger("SGDK_Integration")
    
    def _setup_component_manager(self):
        """Configura o gerenciador de componentes"""
        if ComponentManager:
            try:
                return ComponentManager()
            except Exception as e:
                self.logger.warning(f"Falha ao inicializar ComponentManager: {e}")
        return None
    
    def register_sgdk_component(self) -> bool:
        """Registra o SGDK como componente instalado"""
        try:
            component_data = {
                "name": "SGDK",
                "version": "2.11",
                "category": "Desenvolvimento Retro",
                "description": "Sega Genesis Development Kit",
                "install_path": str(self.sgdk_path),
                "status": "manual_setup",
                "installation_type": "manual",
                "installed_at": self._get_current_timestamp(),
                "components": {
                    "compiler": {
                        "name": "m68k-elf-gcc",
                        "path": str(self.sgdk_path / "bin" / "m68k-elf-gcc.exe"),
                        "required": True
                    },
                    "assembler": {
                        "name": "m68k-elf-as",
                        "path": str(self.sgdk_path / "bin" / "m68k-elf-as.exe"),
                        "required": True
                    },
                    "linker": {
                        "name": "m68k-elf-ld",
                        "path": str(self.sgdk_path / "bin" / "m68k-elf-ld.exe"),
                        "required": True
                    },
                    "library": {
                        "name": "libmd",
                        "path": str(self.sgdk_path / "lib" / "libmd.a"),
                        "required": True
                    }
                },
                "environment_variables": {
                    "SGDK_PATH": str(self.sgdk_path),
                    "GDK": str(self.sgdk_path),
                    "SGDK_BIN": str(self.sgdk_path / "bin"),
                    "SGDK_INC": str(self.sgdk_path / "inc"),
                    "SGDK_LIB": str(self.sgdk_path / "lib")
                },
                "verification": {
                    "method": "file_check",
                    "files_to_check": [
                        "bin/m68k-elf-gcc.exe",
                        "inc/genesis.h",
                        "lib/libmd.a"
                    ]
                }
            }
            
            # Salva informações do componente
            component_file = self.sgdk_path / "component_info.json"
            with open(component_file, 'w', encoding='utf-8') as f:
                json.dump(component_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✓ Componente SGDK registrado: {component_file}")
            
            # Registra no sistema de componentes se disponível
            if self.component_manager:
                try:
                    self.component_manager.register_component("sgdk", component_data)
                    self.logger.info("✓ SGDK registrado no sistema de componentes")
                except Exception as e:
                    self.logger.warning(f"Falha ao registrar no ComponentManager: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao registrar componente SGDK: {e}")
            return False
    
    def setup_environment(self) -> bool:
        """Configura variáveis de ambiente"""
        try:
            env_vars = {
                "SGDK_PATH": str(self.sgdk_path),
                "GDK": str(self.sgdk_path),
                "SGDK_BIN": str(self.sgdk_path / "bin"),
                "SGDK_INC": str(self.sgdk_path / "inc"),
                "SGDK_LIB": str(self.sgdk_path / "lib")
            }
            
            # Usa EnvManager se disponível
            if EnvManager:
                env_manager = EnvManager()
                for var, value in env_vars.items():
                    env_manager.set_variable(var, value)
                self.logger.info("✓ Variáveis de ambiente configuradas via EnvManager")
            else:
                # Configuração manual
                for var, value in env_vars.items():
                    os.environ[var] = value
                self.logger.info("✓ Variáveis de ambiente configuradas manualmente")
            
            # Cria script de ativação
            self._create_activation_script(env_vars)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao configurar ambiente: {e}")
            return False
    
    def _create_activation_script(self, env_vars: Dict[str, str]):
        """Cria script de ativação do ambiente SGDK"""
        # Script para Windows
        bat_content = ["@echo off"]
        bat_content.append("echo Ativando ambiente SGDK...")
        
        for var, value in env_vars.items():
            bat_content.append(f"set {var}={value}")
        
        # Adiciona ao PATH
        bat_content.append(f"set PATH=%PATH%;{env_vars['SGDK_BIN']}")
        bat_content.append("echo ✓ Ambiente SGDK ativado")
        bat_content.append("echo Use 'make' para compilar projetos SGDK")
        
        bat_file = self.sgdk_path / "activate_sgdk.bat"
        with open(bat_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(bat_content))
        
        # Script para PowerShell
        ps1_content = ["# Script de ativação do SGDK para PowerShell"]
        ps1_content.append("Write-Host 'Ativando ambiente SGDK...' -ForegroundColor Green")
        
        for var, value in env_vars.items():
            ps1_content.append(f"$env:{var} = '{value}'")
        
        ps1_content.append(f"$env:PATH += ';{env_vars['SGDK_BIN']}'")
        ps1_content.append("Write-Host '✓ Ambiente SGDK ativado' -ForegroundColor Green")
        ps1_content.append("Write-Host 'Use make para compilar projetos SGDK' -ForegroundColor Yellow")
        
        ps1_file = self.sgdk_path / "activate_sgdk.ps1"
        with open(ps1_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(ps1_content))
        
        self.logger.info(f"✓ Scripts de ativação criados: {bat_file}, {ps1_file}")
    
    def verify_installation(self) -> Dict[str, any]:
        """Verifica se a instalação está completa"""
        results = {
            "status": "unknown",
            "missing_files": [],
            "found_files": [],
            "can_compile": False,
            "recommendations": []
        }
        
        try:
            # Arquivos essenciais
            essential_files = [
                "bin/m68k-elf-gcc.exe",
                "bin/m68k-elf-as.exe",
                "bin/m68k-elf-ld.exe",
                "inc/genesis.h",
                "lib/libmd.a"
            ]
            
            for file_path in essential_files:
                full_path = self.sgdk_path / file_path
                if full_path.exists():
                    results["found_files"].append(file_path)
                else:
                    results["missing_files"].append(file_path)
            
            # Determina status
            if not results["missing_files"]:
                results["status"] = "complete"
                results["can_compile"] = True
            elif len(results["found_files"]) > 0:
                results["status"] = "partial"
            else:
                results["status"] = "not_installed"
            
            # Gera recomendações
            if results["status"] == "not_installed":
                results["recommendations"].extend([
                    "Baixe o SGDK de https://github.com/Stephane-D/SGDK/releases",
                    "Extraia todos os arquivos para o diretório SGDK",
                    "Execute este script novamente para verificar"
                ])
            elif results["status"] == "partial":
                results["recommendations"].extend([
                    "Alguns arquivos estão faltando",
                    "Verifique se a extração foi completa",
                    "Baixe novamente se necessário"
                ])
            else:
                results["recommendations"].extend([
                    "Instalação completa!",
                    "Execute activate_sgdk.bat para configurar o ambiente",
                    "Crie um projeto de teste para verificar funcionamento"
                ])
            
        except Exception as e:
            results["status"] = "error"
            results["recommendations"].append(f"Erro durante verificação: {e}")
        
        return results
    
    def _get_current_timestamp(self) -> str:
        """Retorna timestamp atual"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def generate_status_report(self) -> str:
        """Gera relatório de status completo"""
        verification = self.verify_installation()
        
        report = ["=== RELATÓRIO DE INTEGRAÇÃO DO SGDK ==="]
        report.append(f"Caminho: {self.sgdk_path}")
        report.append(f"Status: {verification['status'].upper()}")
        
        if verification['found_files']:
            report.append("\n=== ARQUIVOS ENCONTRADOS ===")
            for file in verification['found_files']:
                report.append(f"✓ {file}")
        
        if verification['missing_files']:
            report.append("\n=== ARQUIVOS FALTANDO ===")
            for file in verification['missing_files']:
                report.append(f"❌ {file}")
        
        if verification['recommendations']:
            report.append("\n=== RECOMENDAÇÕES ===")
            for i, rec in enumerate(verification['recommendations'], 1):
                report.append(f"{i}. {rec}")
        
        return "\n".join(report)

def main():
    """Função principal"""
    print("=== Integração do SGDK com Sistema de Componentes ===")
    
    integration = SGDKIntegration()
    
    # Verifica status atual
    print("\n" + integration.generate_status_report())
    
    # Registra componente
    print("\n=== REGISTRANDO COMPONENTE ===")
    if integration.register_sgdk_component():
        print("✓ Componente SGDK registrado com sucesso")
    else:
        print("❌ Falha ao registrar componente SGDK")
    
    # Configura ambiente
    print("\n=== CONFIGURANDO AMBIENTE ===")
    if integration.setup_environment():
        print("✓ Ambiente configurado com sucesso")
    else:
        print("❌ Falha ao configurar ambiente")
    
    # Verifica instalação final
    verification = integration.verify_installation()
    
    print("\n=== STATUS FINAL ===")
    if verification['status'] == 'complete':
        print("🎉 SGDK está pronto para uso!")
        print("\nPróximos passos:")
        print("1. Execute: activate_sgdk.bat")
        print("2. Crie um projeto de teste")
        print("3. Compile com: make")
        return True
    else:
        print("⚠️  Instalação ainda não está completa")
        print("\nAções necessárias:")
        for rec in verification['recommendations']:
            print(f"- {rec}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
