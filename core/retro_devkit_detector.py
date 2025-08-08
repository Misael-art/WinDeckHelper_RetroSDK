"""Sistema de detecção automática de retro devkits
Detecta automaticamente quais devkits retro estão instalados no sistema"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Type
import logging
from dataclasses import dataclass

from .retro_devkit_base import RetroDevkitManager, DevkitInfo
from .gbdk_improvements import GBDKManager
from .snes_improvements import SNESManager
from .psx_improvements import PSXManager
from .n64_improvements import N64Manager
from .gba_improvements import GBAManager
from .neogeo_improvements import NeoGeoManager
from .nes_improvements import NESManager
from .saturn_improvements import SaturnManager

@dataclass
class DetectionResult:
    """Resultado da detecção de um devkit"""
    devkit_name: str
    is_installed: bool
    installation_path: Optional[Path]
    version: Optional[str]
    missing_components: List[str]
    manager_class: Type[RetroDevkitManager]
    confidence: float  # 0.0 a 1.0

class RetroDevkitDetector:
    """Detector automático de retro devkits"""
    
    def __init__(self, base_path: Path, logger: logging.Logger):
        self.base_path = base_path
        self.logger = logger
        
        # Mapeamento de managers disponíveis
        self.available_managers = {
            "GBDK": GBDKManager,
            "SNES": SNESManager,
            "PSX": PSXManager,
            "N64": N64Manager,
            "GBA": GBAManager,
            "NeoGeo": NeoGeoManager,
            "NES": NESManager,
            "Saturn": SaturnManager
        }
        
    def detect_all_devkits(self) -> Dict[str, DetectionResult]:
        """Detecta todos os devkits disponíveis"""
        results = {}
        
        self.logger.info("Iniciando detecção automática de retro devkits...")
        
        for devkit_name, manager_class in self.available_managers.items():
            try:
                result = self._detect_devkit(devkit_name, manager_class)
                results[devkit_name] = result
                
                if result.is_installed:
                    self.logger.info(f"{devkit_name} detectado: {result.installation_path}")
                else:
                    self.logger.debug(f"{devkit_name} não detectado")
                    
            except Exception as e:
                self.logger.error(f"Erro na detecção do {devkit_name}: {e}")
                results[devkit_name] = DetectionResult(
                    devkit_name=devkit_name,
                    is_installed=False,
                    installation_path=None,
                    version=None,
                    missing_components=["Erro na detecção"],
                    manager_class=manager_class,
                    confidence=0.0
                )
                
        self.logger.info(f"Detecção concluída. {len([r for r in results.values() if r.is_installed])} devkits encontrados.")
        return results
        
    def _detect_devkit(self, devkit_name: str, manager_class: Type[RetroDevkitManager]) -> DetectionResult:
        """Detecta um devkit específico"""
        try:
            # Criar instância temporária do manager
            manager = manager_class(self.base_path, self.logger)
            devkit_info = manager.get_devkit_info()
            
            # Verificar se o devkit está instalado
            devkit_path = self.base_path / "retro_devkits" / manager.get_devkit_folder_name()
            
            if not devkit_path.exists():
                return DetectionResult(
                    devkit_name=devkit_name,
                    is_installed=False,
                    installation_path=None,
                    version=None,
                    missing_components=["Pasta do devkit não encontrada"],
                    manager_class=manager_class,
                    confidence=0.0
                )
                
            # Verificar arquivos de verificação
            missing_components = []
            found_components = 0
            total_components = len(devkit_info.verification_files)
            
            for file_path in devkit_info.verification_files:
                full_path = devkit_path / file_path
                if full_path.exists():
                    found_components += 1
                else:
                    missing_components.append(str(file_path))
                    
            # Calcular confiança baseada nos componentes encontrados
            confidence = found_components / total_components if total_components > 0 else 0.0
            
            # Detectar versão se possível
            version = self._detect_version(manager, devkit_path)
            
            # Considerar instalado se pelo menos 70% dos componentes estão presentes
            is_installed = confidence >= 0.7
            
            return DetectionResult(
                devkit_name=devkit_name,
                is_installed=is_installed,
                installation_path=devkit_path if is_installed else None,
                version=version,
                missing_components=missing_components,
                manager_class=manager_class,
                confidence=confidence
            )
            
        except Exception as e:
            self.logger.error(f"Erro na detecção do {devkit_name}: {e}")
            return DetectionResult(
                devkit_name=devkit_name,
                is_installed=False,
                installation_path=None,
                version=None,
                missing_components=[f"Erro: {str(e)}"],
                manager_class=manager_class,
                confidence=0.0
            )
            
    def _detect_version(self, manager: RetroDevkitManager, devkit_path: Path) -> Optional[str]:
        """Tenta detectar a versão do devkit"""
        try:
            devkit_info = manager.get_devkit_info()
            
            # Estratégias específicas por devkit
            if isinstance(manager, GBDKManager):
                return self._detect_gbdk_version(devkit_path)
            elif isinstance(manager, SNESManager):
                return self._detect_cc65_version(devkit_path)
            elif isinstance(manager, PSXManager):
                return self._detect_psn00bsdk_version(devkit_path)
            elif isinstance(manager, N64Manager):
                return self._detect_libdragon_version(devkit_path)
            elif isinstance(manager, GBAManager):
                return self._detect_devkitarm_version(devkit_path)
            elif isinstance(manager, NeoGeoManager):
                return self._detect_ngdevkit_version(devkit_path)
            elif isinstance(manager, NESManager):
                return self._detect_cc65_version(devkit_path)
            elif isinstance(manager, SaturnManager):
                return self._detect_joengine_version(devkit_path)
                
            return devkit_info.version
            
        except Exception as e:
            self.logger.debug(f"Erro na detecção de versão: {e}")
            return None
            
    def _detect_gbdk_version(self, devkit_path: Path) -> Optional[str]:
        """Detecta versão do GBDK"""
        try:
            gcc_path = devkit_path / "bin" / "lcc.exe"
            if gcc_path.exists():
                result = subprocess.run([str(gcc_path), "-v"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    # Extrair versão do output
                    for line in result.stderr.split('\n'):
                        if 'GBDK' in line:
                            return line.strip()
            return "GBDK-2020"
        except:
            return None
            
    def _detect_cc65_version(self, devkit_path: Path) -> Optional[str]:
        """Detecta versão do CC65"""
        try:
            cc65_path = devkit_path / "cc65" / "bin" / "cc65.exe"
            if cc65_path.exists():
                result = subprocess.run([str(cc65_path), "--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return result.stdout.strip().split('\n')[0]
            return "CC65"
        except:
            return None
            
    def _detect_psn00bsdk_version(self, devkit_path: Path) -> Optional[str]:
        """Detecta versão do PSn00bSDK"""
        try:
            # Verificar arquivo de versão
            version_file = devkit_path / "psn00bsdk" / "VERSION"
            if version_file.exists():
                return version_file.read_text().strip()
            return "PSn00bSDK"
        except:
            return None
            
    def _detect_libdragon_version(self, devkit_path: Path) -> Optional[str]:
        """Detecta versão do libdragon"""
        try:
            # Verificar arquivo de versão
            version_file = devkit_path / "libdragon" / "VERSION"
            if version_file.exists():
                return version_file.read_text().strip()
            return "libdragon"
        except:
            return None
            
    def _detect_devkitarm_version(self, devkit_path: Path) -> Optional[str]:
        """Detecta versão do devkitARM"""
        try:
            gcc_path = devkit_path / "devkitARM" / "bin" / "arm-none-eabi-gcc.exe"
            if gcc_path.exists():
                result = subprocess.run([str(gcc_path), "--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return result.stdout.strip().split('\n')[0]
            return "devkitARM"
        except:
            return None
            
    def _detect_ngdevkit_version(self, devkit_path: Path) -> Optional[str]:
        """Detecta versão do NGDevKit"""
        try:
            gcc_path = devkit_path / "toolchain" / "bin" / "m68k-neogeo-elf-gcc.exe"
            if gcc_path.exists():
                result = subprocess.run([str(gcc_path), "--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return result.stdout.strip().split('\n')[0]
            return "NGDevKit"
        except:
            return None
            
    def _detect_joengine_version(self, devkit_path: Path) -> Optional[str]:
        """Detecta versão do Jo-Engine"""
        try:
            # Verificar arquivo de versão
            version_file = devkit_path / "joengine" / "VERSION"
            if version_file.exists():
                return version_file.read_text().strip()
            return "Jo-Engine + Yaul"
        except:
            return None
            
    def get_installation_summary(self, results: Dict[str, DetectionResult]) -> Dict[str, Any]:
        """Gera resumo da instalação"""
        installed = [r for r in results.values() if r.is_installed]
        not_installed = [r for r in results.values() if not r.is_installed]
        partial = [r for r in results.values() if 0.3 <= r.confidence < 0.7]
        
        return {
            "total_devkits": len(results),
            "installed_count": len(installed),
            "not_installed_count": len(not_installed),
            "partial_count": len(partial),
            "installed_devkits": [r.devkit_name for r in installed],
            "not_installed_devkits": [r.devkit_name for r in not_installed],
            "partial_devkits": [r.devkit_name for r in partial],
            "average_confidence": sum(r.confidence for r in results.values()) / len(results)
        }
        
    def generate_report(self, results: Dict[str, DetectionResult]) -> str:
        """Gera relatório detalhado da detecção"""
        summary = self.get_installation_summary(results)
        
        report = []
        report.append("=" * 60)
        report.append("RELATÓRIO DE DETECÇÃO DE RETRO DEVKITS")
        report.append("=" * 60)
        report.append("")
        
        # Resumo geral
        report.append("📊 RESUMO GERAL:")
        report.append(f"  Total de devkits: {summary['total_devkits']}")
        report.append(f"  Instalados: {summary['installed_count']}")
        report.append(f"  Não instalados: {summary['not_installed_count']}")
        report.append(f"  Instalação parcial: {summary['partial_count']}")
        report.append(f"  Confiança média: {summary['average_confidence']:.1%}")
        report.append("")
        
        # Devkits instalados
        if summary['installed_count'] > 0:
            report.append("✅ DEVKITS INSTALADOS:")
            for devkit_name in summary['installed_devkits']:
                result = results[devkit_name]
                report.append(f"  • {devkit_name}")
                report.append(f"    Caminho: {result.installation_path}")
                report.append(f"    Versão: {result.version or 'Desconhecida'}")
                report.append(f"    Confiança: {result.confidence:.1%}")
                if result.missing_components:
                    report.append(f"    Componentes faltando: {len(result.missing_components)}")
                report.append("")
                
        # Devkits não instalados
        if summary['not_installed_count'] > 0:
            report.append("❌ DEVKITS NÃO INSTALADOS:")
            for devkit_name in summary['not_installed_devkits']:
                result = results[devkit_name]
                report.append(f"  • {devkit_name}")
                if result.missing_components:
                    report.append(f"    Problemas: {', '.join(result.missing_components[:3])}")
                    if len(result.missing_components) > 3:
                        report.append(f"    ... e mais {len(result.missing_components) - 3} problemas")
                report.append("")
                
        # Devkits com instalação parcial
        if summary['partial_count'] > 0:
            report.append("⚠️ DEVKITS COM INSTALAÇÃO PARCIAL:")
            for devkit_name in summary['partial_devkits']:
                result = results[devkit_name]
                report.append(f"  • {devkit_name}")
                report.append(f"    Caminho: {result.installation_path}")
                report.append(f"    Confiança: {result.confidence:.1%}")
                report.append(f"    Componentes faltando: {len(result.missing_components)}")
                report.append("")
                
        report.append("=" * 60)
        
        return "\n".join(report)
        
    def save_detection_cache(self, results: Dict[str, DetectionResult], cache_file: Path) -> bool:
        """Salva cache da detecção"""
        try:
            cache_data = {
                "timestamp": str(Path().cwd()),  # Placeholder para timestamp
                "results": {}
            }
            
            for devkit_name, result in results.items():
                cache_data["results"][devkit_name] = {
                    "is_installed": result.is_installed,
                    "installation_path": str(result.installation_path) if result.installation_path else None,
                    "version": result.version,
                    "confidence": result.confidence,
                    "missing_components_count": len(result.missing_components)
                }
                
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar cache de detecção: {e}")
            return False
            
    def load_detection_cache(self, cache_file: Path) -> Optional[Dict[str, Any]]:
        """Carrega cache da detecção"""
        try:
            if not cache_file.exists():
                return None
                
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Erro ao carregar cache de detecção: {e}")
            return None