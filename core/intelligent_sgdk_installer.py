#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Intelligent SGDK Installer - Instalador Inteligente do SGDK
Instala SGDK com detecção automática de editores compatíveis e configuração otimizada.
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

# Importar módulos do sistema
from .editor_detection_manager import EditorDetectionManager, EditorInfo, EditorCompatibility
from .retro_devkit_manager import RetroDevKitManager
from .component_manager import ComponentManager
from .installation_manager import InstallationManager
from .download_manager import DownloadManager

@dataclass
class SGDKInstallationPlan:
    """Plano de instalação do SGDK"""
    install_vscode: bool
    target_editor: Optional[EditorInfo]
    required_dependencies: List[str]
    extensions_to_install: List[str]
    configuration_steps: List[str]
    reason: str

class IntelligentSGDKInstaller:
    """Instalador inteligente do SGDK com detecção automática de editores"""
    
    def __init__(self, base_path: Path, logger: Optional[logging.Logger] = None):
        self.base_path = base_path
        self.logger = logger or logging.getLogger(__name__)
        
        # Inicializar managers
        self.editor_manager = EditorDetectionManager(base_path, logger)
        self.retro_manager = RetroDevKitManager(base_path)
        self.component_manager = ComponentManager(base_path)
        self.installation_manager = InstallationManager(base_path)
        self.download_manager = DownloadManager(base_path)
        
        # Configurações do SGDK
        self.sgdk_config = {
            "name": "SGDK (Sega Genesis Development Kit)",
            "version": "1.80",
            "download_url": "https://github.com/Stephane-D/SGDK/releases/latest/download/sgdk180.7z",
            "install_path": base_path / "retro_devkits" / "sgdk",
            "required_dependencies": [
                "Microsoft Visual C++ Redistributable",
                "Java Runtime Environment",
                "Make"
            ],
            "optional_dependencies": [
                "Visual Studio Code"  # Agora opcional, baseado na detecção
            ],
            "emulators": [
                "Gens",
                "Fusion",
                "BlastEm"
            ]
        }
        
        # Extensões por tipo de editor
        self.extensions_config = {
            "vscode_compatible": [
                "zerasul.genesis-code",
                "ms-vscode.cpptools",
                "13xforever.language-x86-64-assembly",
                "ms-vscode.hexeditor"
            ],
            "minimal_extensions": [
                "ms-vscode.cpptools",
                "zerasul.genesis-code"
            ]
        }
    
    def create_installation_plan(self) -> SGDKInstallationPlan:
        """Cria um plano de instalação inteligente baseado nos editores detectados"""
        self.logger.info("🎯 Criando plano de instalação inteligente para SGDK...")
        
        # Detectar editores instalados
        detected_editors = self.editor_manager.detect_installed_editors()
        
        # Determinar se deve instalar VSCode
        should_install_vscode, reason = self.editor_manager.should_install_vscode(detected_editors)
        
        # Encontrar o melhor editor compatível
        best_editor = self.editor_manager.get_best_compatible_editor(detected_editors)
        
        # Determinar dependências necessárias
        required_deps = self.sgdk_config["required_dependencies"].copy()
        if should_install_vscode:
            required_deps.append("Visual Studio Code")
        
        # Determinar extensões a instalar
        extensions = []
        if best_editor and best_editor.supports_vscode_extensions:
            extensions = self.extensions_config["vscode_compatible"]
        elif should_install_vscode:
            extensions = self.extensions_config["vscode_compatible"]
        else:
            extensions = self.extensions_config["minimal_extensions"]
        
        # Criar passos de configuração
        config_steps = self._create_configuration_steps(best_editor, should_install_vscode)
        
        plan = SGDKInstallationPlan(
            install_vscode=should_install_vscode,
            target_editor=best_editor,
            required_dependencies=required_deps,
            extensions_to_install=extensions,
            configuration_steps=config_steps,
            reason=reason
        )
        
        self._log_installation_plan(plan)
        return plan
    
    def _create_configuration_steps(self, target_editor: Optional[EditorInfo], install_vscode: bool) -> List[str]:
        """Cria passos de configuração baseados no editor alvo"""
        steps = []
        
        if target_editor:
            if target_editor.supports_vscode_extensions:
                steps.append(f"Configurar extensões para {target_editor.name}")
                steps.append("Instalar extensão Genesis Code")
                steps.append("Configurar IntelliSense para C/C++")
                steps.append("Configurar syntax highlighting para Assembly")
                steps.append("Configurar Hex Editor para ROMs")
            else:
                steps.append(f"Configuração manual necessária para {target_editor.name}")
                steps.append("Criar configuração de build personalizada")
                steps.append("Configurar syntax highlighting básico")
        
        if install_vscode:
            steps.append("Instalar Visual Studio Code")
            steps.append("Configurar VSCode como editor padrão para SGDK")
        
        steps.extend([
            "Configurar variáveis de ambiente SGDK",
            "Configurar PATH para ferramentas SGDK",
            "Testar compilação de projeto exemplo",
            "Configurar emulador padrão"
        ])
        
        return steps
    
    def _log_installation_plan(self, plan: SGDKInstallationPlan):
        """Registra o plano de instalação no log"""
        self.logger.info("📋 PLANO DE INSTALAÇÃO SGDK")
        self.logger.info("=" * 40)
        self.logger.info(f"💭 Motivo: {plan.reason}")
        self.logger.info(f"📦 Instalar VSCode: {'Sim' if plan.install_vscode else 'Não'}")
        
        if plan.target_editor:
            self.logger.info(f"🎯 Editor alvo: {plan.target_editor.name}")
            self.logger.info(f"🔧 Compatibilidade: {plan.target_editor.compatibility.value}")
        
        self.logger.info(f"📚 Dependências: {', '.join(plan.required_dependencies)}")
        self.logger.info(f"🧩 Extensões: {', '.join(plan.extensions_to_install)}")
        self.logger.info(f"⚙️ Passos de configuração: {len(plan.configuration_steps)}")
    
    def install_sgdk(self, force_reinstall: bool = False) -> bool:
        """Instala SGDK usando o plano inteligente"""
        try:
            self.logger.info("🚀 Iniciando instalação inteligente do SGDK...")
            
            # Criar plano de instalação
            plan = self.create_installation_plan()
            
            # Verificar se já está instalado
            if not force_reinstall and self._is_sgdk_installed():
                self.logger.info("✅ SGDK já está instalado. Use force_reinstall=True para reinstalar.")
                return True
            
            # Instalar dependências
            if not self._install_dependencies(plan):
                self.logger.error("❌ Falha ao instalar dependências")
                return False
            
            # Baixar e instalar SGDK
            if not self._download_and_install_sgdk():
                self.logger.error("❌ Falha ao baixar/instalar SGDK")
                return False
            
            # Configurar editor
            if not self._configure_editor(plan):
                self.logger.warning("⚠️ Falha na configuração do editor (continuando...)")
            
            # Configurar ambiente
            if not self._configure_environment():
                self.logger.error("❌ Falha ao configurar ambiente")
                return False
            
            # Verificar instalação
            if not self._verify_installation():
                self.logger.error("❌ Verificação da instalação falhou")
                return False
            
            self.logger.info("🎉 SGDK instalado com sucesso!")
            self._show_post_install_info(plan)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro durante instalação do SGDK: {e}")
            return False
    
    def _is_sgdk_installed(self) -> bool:
        """Verifica se SGDK já está instalado"""
        sgdk_path = self.sgdk_config["install_path"]
        required_files = [
            sgdk_path / "bin" / "rescomp.jar",
            sgdk_path / "inc" / "genesis.h",
            sgdk_path / "bin" / "gcc" / "bin" / "m68k-elf-gcc.exe"
        ]
        
        return all(file.exists() for file in required_files)
    
    def _install_dependencies(self, plan: SGDKInstallationPlan) -> bool:
        """Instala dependências necessárias"""
        self.logger.info("📦 Instalando dependências...")
        
        for dependency in plan.required_dependencies:
            self.logger.info(f"🔄 Instalando {dependency}...")
            
            try:
                if not self.component_manager.install_component(dependency):
                    self.logger.error(f"❌ Falha ao instalar {dependency}")
                    return False
                self.logger.info(f"✅ {dependency} instalado com sucesso")
            except Exception as e:
                self.logger.error(f"❌ Erro ao instalar {dependency}: {e}")
                return False
        
        return True
    
    def _download_and_install_sgdk(self) -> bool:
        """Baixa e instala o SGDK"""
        self.logger.info("📥 Baixando SGDK...")
        
        try:
            # Usar o retro devkit manager para instalação
            return self.retro_manager.install_sgdk()
        except Exception as e:
            self.logger.error(f"❌ Erro ao baixar/instalar SGDK: {e}")
            return False
    
    def _configure_editor(self, plan: SGDKInstallationPlan) -> bool:
        """Configura o editor baseado no plano"""
        self.logger.info("🔧 Configurando editor...")
        
        try:
            if plan.target_editor:
                # Configurar editor existente
                sgdk_path = self.sgdk_config["install_path"]
                return self.editor_manager.configure_sgdk_for_editor(plan.target_editor, sgdk_path)
            elif plan.install_vscode:
                # Configurar VSCode recém-instalado
                return self._configure_vscode_extensions(plan.extensions_to_install)
            else:
                self.logger.info("ℹ️ Nenhuma configuração de editor necessária")
                return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao configurar editor: {e}")
            return False
    
    def _configure_vscode_extensions(self, extensions: List[str]) -> bool:
        """Configura extensões do VSCode"""
        self.logger.info("🧩 Instalando extensões do VSCode...")
        
        for extension in extensions:
            try:
                result = subprocess.run(
                    ["code", "--install-extension", extension],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    self.logger.info(f"✅ Extensão instalada: {extension}")
                else:
                    self.logger.warning(f"⚠️ Falha ao instalar extensão {extension}: {result.stderr}")
            except subprocess.TimeoutExpired:
                self.logger.warning(f"⏰ Timeout ao instalar extensão {extension}")
            except Exception as e:
                self.logger.error(f"❌ Erro ao instalar extensão {extension}: {e}")
        
        return True
    
    def _configure_environment(self) -> bool:
        """Configura variáveis de ambiente"""
        self.logger.info("🌍 Configurando variáveis de ambiente...")
        
        try:
            sgdk_path = self.sgdk_config["install_path"]
            
            # Configurar SGDK_HOME
            os.environ["SGDK_HOME"] = str(sgdk_path)
            
            # Adicionar ao PATH
            sgdk_bin = sgdk_path / "bin"
            gcc_bin = sgdk_path / "bin" / "gcc" / "bin"
            
            current_path = os.environ.get("PATH", "")
            new_paths = [str(sgdk_bin), str(gcc_bin)]
            
            for new_path in new_paths:
                if new_path not in current_path:
                    os.environ["PATH"] = f"{new_path};{current_path}"
            
            self.logger.info("✅ Variáveis de ambiente configuradas")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao configurar ambiente: {e}")
            return False
    
    def _verify_installation(self) -> bool:
        """Verifica se a instalação foi bem-sucedida"""
        self.logger.info("🔍 Verificando instalação...")
        
        try:
            # Verificar arquivos essenciais
            if not self._is_sgdk_installed():
                self.logger.error("❌ Arquivos essenciais do SGDK não encontrados")
                return False
            
            # Testar compilador
            gcc_path = self.sgdk_config["install_path"] / "bin" / "gcc" / "bin" / "m68k-elf-gcc.exe"
            if gcc_path.exists():
                try:
                    result = subprocess.run(
                        [str(gcc_path), "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        self.logger.info("✅ Compilador GCC funcionando")
                    else:
                        self.logger.warning("⚠️ Compilador GCC pode ter problemas")
                except Exception as e:
                    self.logger.warning(f"⚠️ Não foi possível testar GCC: {e}")
            
            # Verificar Java (necessário para rescomp)
            try:
                result = subprocess.run(
                    ["java", "-version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    self.logger.info("✅ Java Runtime disponível")
                else:
                    self.logger.warning("⚠️ Java Runtime pode ter problemas")
            except Exception as e:
                self.logger.warning(f"⚠️ Não foi possível verificar Java: {e}")
            
            self.logger.info("✅ Verificação da instalação concluída")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro durante verificação: {e}")
            return False
    
    def _show_post_install_info(self, plan: SGDKInstallationPlan):
        """Mostra informações pós-instalação"""
        self.logger.info("\n" + "=" * 50)
        self.logger.info("🎉 SGDK INSTALADO COM SUCESSO!")
        self.logger.info("=" * 50)
        
        if plan.target_editor:
            self.logger.info(f"🎯 Editor configurado: {plan.target_editor.name}")
        elif plan.install_vscode:
            self.logger.info("🎯 Editor configurado: Visual Studio Code")
        
        self.logger.info(f"📁 Caminho de instalação: {self.sgdk_config['install_path']}")
        self.logger.info(f"🧩 Extensões instaladas: {len(plan.extensions_to_install)}")
        
        self.logger.info("\n📝 PRÓXIMOS PASSOS:")
        self.logger.info("1. Reinicie o terminal para carregar as variáveis de ambiente")
        self.logger.info("2. Abra seu editor e crie um novo projeto SGDK")
        self.logger.info("3. Use a extensão Genesis Code para facilitar o desenvolvimento")
        self.logger.info("4. Teste a compilação com um projeto exemplo")
        
        if plan.target_editor and plan.target_editor.compatibility != EditorCompatibility.FULL:
            self.logger.info("\n⚠️ ATENÇÃO:")
            self.logger.info(f"Seu editor ({plan.target_editor.name}) tem compatibilidade {plan.target_editor.compatibility.value}")
            self.logger.info("Considere usar VSCode para melhor experiência de desenvolvimento")
    
    def get_installation_status(self) -> Dict[str, Any]:
        """Retorna status detalhado da instalação"""
        detected_editors = self.editor_manager.detect_installed_editors()
        plan = self.create_installation_plan()
        
        return {
            "sgdk_installed": self._is_sgdk_installed(),
            "sgdk_path": str(self.sgdk_config["install_path"]),
            "detected_editors": [
                {
                    "name": editor.name,
                    "path": editor.path,
                    "version": editor.version,
                    "compatibility": editor.compatibility.value,
                    "supports_vscode_extensions": editor.supports_vscode_extensions
                }
                for editor in detected_editors
            ],
            "installation_plan": {
                "install_vscode": plan.install_vscode,
                "target_editor": plan.target_editor.name if plan.target_editor else None,
                "required_dependencies": plan.required_dependencies,
                "extensions_to_install": plan.extensions_to_install,
                "reason": plan.reason
            }
        }


def get_intelligent_sgdk_installer(base_path: Optional[Path] = None, logger: Optional[logging.Logger] = None) -> IntelligentSGDKInstaller:
    """Factory function para criar IntelligentSGDKInstaller"""
    if base_path is None:
        base_path = Path.cwd()
    return IntelligentSGDKInstaller(base_path, logger)