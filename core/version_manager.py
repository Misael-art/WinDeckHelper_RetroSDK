"""Sistema de Versões Unificado para o Environment Dev.

Este módulo fornece uma classe centralizada para gerenciamento de versões,
suportando diferentes formatos e operações de comparação.
"""

import re
import logging
from typing import Optional, Tuple, Union, List
from dataclasses import dataclass
from enum import Enum


class VersionFormat(Enum):
    """Formatos de versão suportados."""
    SEMANTIC = "semantic"  # 1.2.3
    SEMANTIC_PRERELEASE = "semantic_prerelease"  # 1.2.3-alpha.1
    SEMANTIC_BUILD = "semantic_build"  # 1.2.3+20130313144700
    SEMANTIC_FULL = "semantic_full"  # 1.2.3-alpha.1+20130313144700
    WINDOWS_STYLE = "windows_style"  # 2.47.1.windows.1
    SIMPLE = "simple"  # 1.2
    SINGLE = "single"  # 5


@dataclass
class ParsedVersion:
    """Representa uma versão parseada."""
    major: int
    minor: int = 0
    patch: int = 0
    prerelease: Optional[str] = None
    build: Optional[str] = None
    original: str = ""
    format_type: VersionFormat = VersionFormat.SEMANTIC
    
    def __str__(self) -> str:
        """Retorna representação string da versão."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version
    
    def to_tuple(self) -> Tuple[int, int, int, str, str]:
        """Converte para tupla para comparação."""
        return (
            self.major,
            self.minor, 
            self.patch,
            self.prerelease or "",
            self.build or ""
        )


class VersionManager:
    """Gerenciador centralizado de versões."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Padrões regex para diferentes formatos
        self.patterns = {
            VersionFormat.SEMANTIC_FULL: re.compile(
                r'^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)'
                r'(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?'
                r'(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$'
            ),
            VersionFormat.WINDOWS_STYLE: re.compile(
                r'^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)'
                r'(?:\.(?P<extra>\w+))?(?:\.(?P<build>\d+))?$'
            ),
            VersionFormat.SIMPLE: re.compile(
                r'^(?P<major>\d+)\.(?P<minor>\d+)$'
            ),
            VersionFormat.SINGLE: re.compile(
                r'^(?P<major>\d+)$'
            )
        }
    
    def parse_version(self, version_str: str) -> Optional[ParsedVersion]:
        """Parse uma string de versão em um objeto ParsedVersion.
        
        Args:
            version_str: String da versão a ser parseada
            
        Returns:
            ParsedVersion ou None se não conseguir parsear
        """
        if not version_str or not isinstance(version_str, str):
            self.logger.warning(f"Versão inválida: {version_str}")
            return None
            
        # Remove espaços e caracteres especiais
        clean_version = version_str.strip()
        
        # Tenta cada padrão em ordem de complexidade
        for format_type, pattern in self.patterns.items():
            match = pattern.match(clean_version)
            if match:
                try:
                    groups = match.groupdict()
                    
                    # Extrai componentes básicos
                    major = int(groups.get('major', 0))
                    minor = int(groups.get('minor', 0))
                    patch = int(groups.get('patch', 0))
                    
                    # Trata prerelease e build
                    prerelease = groups.get('prerelease')
                    build = groups.get('build')
                    
                    # Para formato Windows, trata campos especiais
                    if format_type == VersionFormat.WINDOWS_STYLE:
                        extra = groups.get('extra')
                        if extra and extra != 'windows':
                            prerelease = extra
                        build_num = groups.get('build')
                        if build_num:
                            build = build_num
                    
                    parsed = ParsedVersion(
                        major=major,
                        minor=minor,
                        patch=patch,
                        prerelease=prerelease,
                        build=build,
                        original=version_str,
                        format_type=format_type
                    )
                    
                    self.logger.debug(f"Versão parseada: {version_str} -> {parsed}")
                    return parsed
                    
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Erro ao parsear versão {version_str}: {e}")
                    continue
        
        self.logger.warning(f"Não foi possível parsear a versão: {version_str}")
        return None
    
    def compare_versions(self, version1: Union[str, ParsedVersion], 
                        version2: Union[str, ParsedVersion]) -> int:
        """Compara duas versões.
        
        Args:
            version1: Primeira versão
            version2: Segunda versão
            
        Returns:
            -1 se version1 < version2
             0 se version1 == version2
             1 se version1 > version2
        """
        # Parse das versões se necessário
        if isinstance(version1, str):
            v1 = self.parse_version(version1)
            if not v1:
                raise ValueError(f"Não foi possível parsear versão: {version1}")
        else:
            v1 = version1
            
        if isinstance(version2, str):
            v2 = self.parse_version(version2)
            if not v2:
                raise ValueError(f"Não foi possível parsear versão: {version2}")
        else:
            v2 = version2
        
        # Compara componentes principais
        if v1.major != v2.major:
            return 1 if v1.major > v2.major else -1
        if v1.minor != v2.minor:
            return 1 if v1.minor > v2.minor else -1
        if v1.patch != v2.patch:
            return 1 if v1.patch > v2.patch else -1
        
        # Trata prerelease (versões prerelease são menores que release)
        if v1.prerelease and not v2.prerelease:
            return -1
        if not v1.prerelease and v2.prerelease:
            return 1
        if v1.prerelease and v2.prerelease:
            if v1.prerelease != v2.prerelease:
                return 1 if v1.prerelease > v2.prerelease else -1
        
        # Build metadata não afeta precedência
        return 0
    
    def is_compatible(self, current_version: Union[str, ParsedVersion],
                     required_version: str) -> bool:
        """Verifica se uma versão é compatível com um requisito.
        
        Args:
            current_version: Versão atual
            required_version: Requisito de versão (ex: ">=1.2.0", "==2.0.0")
            
        Returns:
            True se compatível, False caso contrário
        """
        # Parse do operador e versão requerida
        operator_pattern = re.compile(r'^(>=|<=|==|!=|>|<)\s*(.+)$')
        match = operator_pattern.match(required_version.strip())
        
        if not match:
            # Se não há operador, assume igualdade
            operator = "=="
            required_ver = required_version.strip()
        else:
            operator = match.group(1)
            required_ver = match.group(2)
        
        try:
            comparison = self.compare_versions(current_version, required_ver)
            
            if operator == ">=":
                return comparison >= 0
            elif operator == "<=":
                return comparison <= 0
            elif operator == "==":
                return comparison == 0
            elif operator == "!=":
                return comparison != 0
            elif operator == ">":
                return comparison > 0
            elif operator == "<":
                return comparison < 0
            else:
                self.logger.warning(f"Operador desconhecido: {operator}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao verificar compatibilidade: {e}")
            return False
    
    def get_latest_version(self, versions: List[Union[str, ParsedVersion]]) -> Optional[ParsedVersion]:
        """Retorna a versão mais recente de uma lista.
        
        Args:
            versions: Lista de versões
            
        Returns:
            Versão mais recente ou None se lista vazia
        """
        if not versions:
            return None
        
        parsed_versions = []
        for v in versions:
            if isinstance(v, str):
                parsed = self.parse_version(v)
                if parsed:
                    parsed_versions.append(parsed)
            else:
                parsed_versions.append(v)
        
        if not parsed_versions:
            return None
        
        latest = parsed_versions[0]
        for version in parsed_versions[1:]:
            if self.compare_versions(version, latest) > 0:
                latest = version
        
        return latest
    
    def normalize_version(self, version_str: str) -> Optional[str]:
        """Normaliza uma string de versão para formato padrão.
        
        Args:
            version_str: String da versão
            
        Returns:
            Versão normalizada ou None se inválida
        """
        parsed = self.parse_version(version_str)
        if parsed:
            return str(parsed)
        return None


# Instância global para uso em todo o projeto
version_manager = VersionManager()

def get_version_manager() -> VersionManager:
    """Retorna a instância global do VersionManager."""
    return version_manager