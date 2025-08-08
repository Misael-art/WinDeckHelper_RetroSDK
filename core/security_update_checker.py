"""Verificador de Atualizações de Segurança.

Este módulo implementa verificação específica de atualizações de segurança,
consultando bases de vulnerabilidades e classificando criticidade.

Author: AI Assistant
Date: 2024
"""

import logging
import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum


class VulnerabilitySeverity(Enum):
    """Severidade de vulnerabilidade."""
    CRITICAL = "critical"  # 9.0-10.0
    HIGH = "high"         # 7.0-8.9
    MEDIUM = "medium"     # 4.0-6.9
    LOW = "low"           # 0.1-3.9
    NONE = "none"         # 0.0


@dataclass
class VulnerabilityInfo:
    """Informações sobre uma vulnerabilidade."""
    cve_id: str
    severity: VulnerabilitySeverity
    score: float  # CVSS score
    description: str
    affected_versions: List[str]
    fixed_version: str
    published_date: datetime
    references: List[str] = field(default_factory=list)
    exploit_available: bool = False
    patch_available: bool = True


@dataclass
class SecurityAssessment:
    """Avaliação de segurança de uma aplicação."""
    application_name: str
    current_version: str
    vulnerabilities: List[VulnerabilityInfo] = field(default_factory=list)
    is_security_update: bool = False
    is_eol: bool = False  # End of Life
    eol_date: Optional[datetime] = None
    security_score: float = 0.0
    risk_level: str = "low"
    recommendations: List[str] = field(default_factory=list)


class SecurityUpdateChecker:
    """Verificador de atualizações de segurança."""
    
    def __init__(self):
        """Inicializa o verificador de segurança."""
        self.logger = logging.getLogger(__name__)
        
        # Cache de vulnerabilidades
        self._vulnerability_cache: Dict[str, List[VulnerabilityInfo]] = {}
        self._cache_timestamp: Dict[str, datetime] = {}
        self._cache_duration = timedelta(hours=6)  # Cache por 6 horas
        
        # Base de dados de vulnerabilidades conhecidas (simulada)
        self._known_vulnerabilities = {
            "git": [
                {
                    "cve_id": "CVE-2023-29007",
                    "severity": "high",
                    "score": 7.8,
                    "description": "Git is vulnerable to path traversal via a crafted .gitmodules file",
                    "affected_versions": ["<2.40.1"],
                    "fixed_version": "2.40.1",
                    "published_date": "2023-04-25"
                },
                {
                    "cve_id": "CVE-2023-25652",
                    "severity": "critical",
                    "score": 9.8,
                    "description": "Git is vulnerable to arbitrary code execution via crafted .gitattributes",
                    "affected_versions": ["<2.40.0"],
                    "fixed_version": "2.40.0",
                    "published_date": "2023-04-20"
                }
            ],
            "nodejs": [
                {
                    "cve_id": "CVE-2023-44487",
                    "severity": "high",
                    "score": 7.5,
                    "description": "HTTP/2 Rapid Reset Attack vulnerability",
                    "affected_versions": ["<18.18.2", "<20.8.1"],
                    "fixed_version": "20.8.1",
                    "published_date": "2023-10-10"
                }
            ],
            "python": [
                {
                    "cve_id": "CVE-2023-40217",
                    "severity": "medium",
                    "score": 5.3,
                    "description": "TLS handshake bypass vulnerability",
                    "affected_versions": ["<3.8.18", "<3.9.18", "<3.10.13", "<3.11.5", "<3.12.0"],
                    "fixed_version": "3.11.5",
                    "published_date": "2023-08-25"
                }
            ],
            "java": [
                {
                    "cve_id": "CVE-2023-22081",
                    "severity": "medium",
                    "score": 5.3,
                    "description": "Vulnerability in Oracle Java SE HTTPS client",
                    "affected_versions": ["<8u381", "<11.0.20", "<17.0.8", "<21.0.0"],
                    "fixed_version": "21.0.0",
                    "published_date": "2023-07-18"
                }
            ],
            "dotnet": [
                {
                    "cve_id": "CVE-2023-36049",
                    "severity": "high",
                    "score": 7.6,
                    "description": ".NET Elevation of Privilege Vulnerability",
                    "affected_versions": ["<6.0.21", "<7.0.10"],
                    "fixed_version": "7.0.10",
                    "published_date": "2023-08-08"
                }
            ],
            "visual_studio_code": [
                {
                    "cve_id": "CVE-2023-36742",
                    "severity": "medium",
                    "score": 6.5,
                    "description": "Visual Studio Code Remote Code Execution Vulnerability",
                    "affected_versions": ["<1.81.0"],
                    "fixed_version": "1.81.0",
                    "published_date": "2023-08-08"
                }
            ]
        }
        
        # Informações de End of Life
        self._eol_info = {
            "python": {
                "3.7": datetime(2023, 6, 27),
                "3.8": datetime(2024, 10, 14),
                "2.7": datetime(2020, 1, 1)  # Já EOL
            },
            "nodejs": {
                "14": datetime(2023, 4, 30),
                "16": datetime(2024, 4, 30),
                "12": datetime(2022, 4, 30)  # Já EOL
            },
            "java": {
                "8": datetime(2030, 12, 31),  # LTS
                "11": datetime(2026, 9, 30),  # LTS
                "17": datetime(2029, 9, 30),  # LTS
                "21": datetime(2031, 9, 30)   # LTS
            },
            "dotnet": {
                "3.1": datetime(2022, 12, 13),  # Já EOL
                "5.0": datetime(2022, 5, 10),   # Já EOL
                "6.0": datetime(2024, 11, 12),  # LTS
                "7.0": datetime(2024, 5, 14),
                "8.0": datetime(2026, 11, 10)   # LTS
            }
        }
        
        self.logger.info("SecurityUpdateChecker inicializado")
    
    async def check_security_updates(self, app_name: str, current_version: str, latest_version: str) -> Dict[str, Any]:
        """Verifica atualizações de segurança para uma aplicação."""
        try:
            # Normalizar nome da aplicação
            normalized_name = self._normalize_app_name(app_name)
            
            # Obter vulnerabilidades
            vulnerabilities = await self._get_vulnerabilities(normalized_name)
            
            # Filtrar vulnerabilidades que afetam a versão atual
            affecting_vulns = self._filter_affecting_vulnerabilities(vulnerabilities, current_version)
            
            # Verificar se é EOL
            is_eol, eol_date = self._check_eol_status(normalized_name, current_version)
            
            # Verificar se a atualização é de segurança
            is_security_update = self._is_security_update(affecting_vulns, current_version, latest_version)
            
            # Calcular score de segurança
            security_score = self._calculate_security_score(affecting_vulns, is_eol)
            
            # Determinar nível de risco
            risk_level = self._determine_risk_level(affecting_vulns, is_eol)
            
            # Gerar recomendações
            recommendations = self._generate_security_recommendations(affecting_vulns, is_eol, current_version, latest_version)
            
            return {
                "vulnerabilities": len(affecting_vulns),
                "critical_vulnerabilities": len([v for v in affecting_vulns if v.severity == VulnerabilitySeverity.CRITICAL]),
                "high_vulnerabilities": len([v for v in affecting_vulns if v.severity == VulnerabilitySeverity.HIGH]),
                "medium_vulnerabilities": len([v for v in affecting_vulns if v.severity == VulnerabilitySeverity.MEDIUM]),
                "low_vulnerabilities": len([v for v in affecting_vulns if v.severity == VulnerabilitySeverity.LOW]),
                "is_security_update": is_security_update,
                "is_eol": is_eol,
                "eol_date": eol_date.isoformat() if eol_date else None,
                "score": security_score,
                "risk_level": risk_level,
                "recommendations": recommendations,
                "vulnerability_details": [self._vulnerability_to_dict(v) for v in affecting_vulns]
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar segurança para {app_name}: {e}")
            return {
                "vulnerabilities": 0,
                "critical_vulnerabilities": 0,
                "high_vulnerabilities": 0,
                "medium_vulnerabilities": 0,
                "low_vulnerabilities": 0,
                "is_security_update": False,
                "is_eol": False,
                "eol_date": None,
                "score": 0.0,
                "risk_level": "unknown",
                "recommendations": [],
                "vulnerability_details": [],
                "error": str(e)
            }
    
    def _normalize_app_name(self, app_name: str) -> str:
        """Normaliza nome da aplicação."""
        name_lower = app_name.lower()
        
        mappings = {
            "visual studio code": "visual_studio_code",
            "vscode": "visual_studio_code",
            "code": "visual_studio_code",
            "node.js": "nodejs",
            "node": "nodejs",
            "npm": "nodejs",
            "java jdk": "java",
            "openjdk": "java",
            "oracle jdk": "java",
            ".net": "dotnet",
            ".net core": "dotnet",
            ".net framework": "dotnet",
            "python": "python",
            "git": "git"
        }
        
        for pattern, key in mappings.items():
            if pattern in name_lower:
                return key
        
        return name_lower.replace(" ", "_")
    
    async def _get_vulnerabilities(self, app_name: str) -> List[VulnerabilityInfo]:
        """Obtém vulnerabilidades para uma aplicação."""
        # Verificar cache
        if self._is_cache_valid(app_name):
            return self._vulnerability_cache.get(app_name, [])
        
        # Obter vulnerabilidades da base de dados
        vulnerabilities = []
        
        if app_name in self._known_vulnerabilities:
            for vuln_data in self._known_vulnerabilities[app_name]:
                vulnerability = VulnerabilityInfo(
                    cve_id=vuln_data["cve_id"],
                    severity=VulnerabilitySeverity(vuln_data["severity"]),
                    score=vuln_data["score"],
                    description=vuln_data["description"],
                    affected_versions=vuln_data["affected_versions"],
                    fixed_version=vuln_data["fixed_version"],
                    published_date=datetime.fromisoformat(vuln_data["published_date"])
                )
                vulnerabilities.append(vulnerability)
        
        # Armazenar no cache
        self._vulnerability_cache[app_name] = vulnerabilities
        self._cache_timestamp[app_name] = datetime.now()
        
        return vulnerabilities
    
    def _filter_affecting_vulnerabilities(self, vulnerabilities: List[VulnerabilityInfo], current_version: str) -> List[VulnerabilityInfo]:
        """Filtra vulnerabilidades que afetam a versão atual."""
        affecting = []
        
        for vuln in vulnerabilities:
            if self._version_is_affected(current_version, vuln.affected_versions):
                affecting.append(vuln)
        
        return affecting
    
    def _version_is_affected(self, version: str, affected_patterns: List[str]) -> bool:
        """Verifica se uma versão é afetada por vulnerabilidade."""
        try:
            for pattern in affected_patterns:
                if self._matches_version_pattern(version, pattern):
                    return True
            return False
        except Exception:
            return False
    
    def _matches_version_pattern(self, version: str, pattern: str) -> bool:
        """Verifica se versão corresponde ao padrão."""
        # Remover prefixos comuns
        clean_version = re.sub(r'^v?', '', version)
        clean_pattern = re.sub(r'^v?', '', pattern)
        
        # Padrões como "<2.40.1"
        if clean_pattern.startswith('<'):
            target_version = clean_pattern[1:]
            return self._compare_versions(clean_version, target_version) < 0
        
        # Padrões como ">=2.40.0"
        if clean_pattern.startswith('>='):
            target_version = clean_pattern[2:]
            return self._compare_versions(clean_version, target_version) >= 0
        
        # Padrões como ">2.40.0"
        if clean_pattern.startswith('>'):
            target_version = clean_pattern[1:]
            return self._compare_versions(clean_version, target_version) > 0
        
        # Padrões como "<=2.40.0"
        if clean_pattern.startswith('<='):
            target_version = clean_pattern[2:]
            return self._compare_versions(clean_version, target_version) <= 0
        
        # Padrões como "=2.40.0" ou "2.40.0"
        if clean_pattern.startswith('='):
            target_version = clean_pattern[1:]
        else:
            target_version = clean_pattern
        
        return self._compare_versions(clean_version, target_version) == 0
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compara duas versões. Retorna -1, 0, ou 1."""
        try:
            # Normalizar versões
            v1_parts = [int(x) for x in version1.split('.')[:3]]
            v2_parts = [int(x) for x in version2.split('.')[:3]]
            
            # Preencher com zeros se necessário
            while len(v1_parts) < 3:
                v1_parts.append(0)
            while len(v2_parts) < 3:
                v2_parts.append(0)
            
            for i in range(3):
                if v1_parts[i] < v2_parts[i]:
                    return -1
                elif v1_parts[i] > v2_parts[i]:
                    return 1
            
            return 0
            
        except (ValueError, IndexError):
            # Fallback para comparação de string
            if version1 < version2:
                return -1
            elif version1 > version2:
                return 1
            else:
                return 0
    
    def _check_eol_status(self, app_name: str, version: str) -> Tuple[bool, Optional[datetime]]:
        """Verifica se a versão está em End of Life."""
        if app_name not in self._eol_info:
            return False, None
        
        eol_versions = self._eol_info[app_name]
        
        # Extrair versão major.minor
        try:
            version_parts = version.split('.')
            if len(version_parts) >= 2:
                major_minor = f"{version_parts[0]}.{version_parts[1]}"
            else:
                major_minor = version_parts[0]
            
            if major_minor in eol_versions:
                eol_date = eol_versions[major_minor]
                is_eol = datetime.now() > eol_date
                return is_eol, eol_date
            
        except (ValueError, IndexError):
            pass
        
        return False, None
    
    def _is_security_update(self, vulnerabilities: List[VulnerabilityInfo], current_version: str, latest_version: str) -> bool:
        """Verifica se a atualização é de segurança."""
        if not vulnerabilities:
            return False
        
        # Verificar se alguma vulnerabilidade é corrigida na versão mais recente
        for vuln in vulnerabilities:
            if self._compare_versions(latest_version, vuln.fixed_version) >= 0:
                return True
        
        return False
    
    def _calculate_security_score(self, vulnerabilities: List[VulnerabilityInfo], is_eol: bool) -> float:
        """Calcula score de segurança (0.0 a 10.0)."""
        if not vulnerabilities and not is_eol:
            return 0.0
        
        # Score base para EOL
        base_score = 5.0 if is_eol else 0.0
        
        # Adicionar scores das vulnerabilidades
        vuln_score = 0.0
        if vulnerabilities:
            max_score = max(v.score for v in vulnerabilities)
            vuln_score = max_score
        
        # Combinar scores
        total_score = max(base_score, vuln_score)
        
        return min(total_score, 10.0)
    
    def _determine_risk_level(self, vulnerabilities: List[VulnerabilityInfo], is_eol: bool) -> str:
        """Determina nível de risco."""
        if any(v.severity == VulnerabilitySeverity.CRITICAL for v in vulnerabilities):
            return "critical"
        
        if any(v.severity == VulnerabilitySeverity.HIGH for v in vulnerabilities) or is_eol:
            return "high"
        
        if any(v.severity == VulnerabilitySeverity.MEDIUM for v in vulnerabilities):
            return "medium"
        
        if vulnerabilities:
            return "low"
        
        return "minimal"
    
    def _generate_security_recommendations(self, vulnerabilities: List[VulnerabilityInfo], is_eol: bool, current_version: str, latest_version: str) -> List[str]:
        """Gera recomendações de segurança."""
        recommendations = []
        
        if is_eol:
            recommendations.append(f"Versão {current_version} está em End of Life. Atualize para uma versão suportada.")
        
        critical_vulns = [v for v in vulnerabilities if v.severity == VulnerabilitySeverity.CRITICAL]
        if critical_vulns:
            recommendations.append(f"CRÍTICO: {len(critical_vulns)} vulnerabilidade(s) crítica(s) encontrada(s). Atualize imediatamente.")
        
        high_vulns = [v for v in vulnerabilities if v.severity == VulnerabilitySeverity.HIGH]
        if high_vulns:
            recommendations.append(f"ALTO: {len(high_vulns)} vulnerabilidade(s) de alta severidade encontrada(s). Atualize em breve.")
        
        if vulnerabilities:
            fixed_in_latest = [v for v in vulnerabilities if self._compare_versions(latest_version, v.fixed_version) >= 0]
            if fixed_in_latest:
                recommendations.append(f"Atualização para {latest_version} corrige {len(fixed_in_latest)} vulnerabilidade(s).")
        
        if not recommendations:
            recommendations.append("Nenhum problema de segurança crítico identificado.")
        
        return recommendations
    
    def _vulnerability_to_dict(self, vuln: VulnerabilityInfo) -> Dict[str, Any]:
        """Converte vulnerabilidade para dicionário."""
        return {
            "cve_id": vuln.cve_id,
            "severity": vuln.severity.value,
            "score": vuln.score,
            "description": vuln.description,
            "affected_versions": vuln.affected_versions,
            "fixed_version": vuln.fixed_version,
            "published_date": vuln.published_date.isoformat(),
            "exploit_available": vuln.exploit_available,
            "patch_available": vuln.patch_available
        }
    
    def _is_cache_valid(self, app_name: str) -> bool:
        """Verifica se o cache é válido."""
        if app_name not in self._cache_timestamp:
            return False
        
        return datetime.now() - self._cache_timestamp[app_name] < self._cache_duration
    
    def clear_cache(self) -> None:
        """Limpa o cache de vulnerabilidades."""
        self._vulnerability_cache.clear()
        self._cache_timestamp.clear()
        self.logger.info("Cache de vulnerabilidades limpo")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do cache."""
        return {
            "cached_apps": len(self._vulnerability_cache),
            "total_vulnerabilities": sum(len(vulns) for vulns in self._vulnerability_cache.values()),
            "cache_timestamps": len(self._cache_timestamp)
        }
    
    async def get_security_assessment(self, app_name: str, current_version: str) -> SecurityAssessment:
        """Obtém avaliação completa de segurança."""
        normalized_name = self._normalize_app_name(app_name)
        vulnerabilities = await self._get_vulnerabilities(normalized_name)
        affecting_vulns = self._filter_affecting_vulnerabilities(vulnerabilities, current_version)
        is_eol, eol_date = self._check_eol_status(normalized_name, current_version)
        security_score = self._calculate_security_score(affecting_vulns, is_eol)
        risk_level = self._determine_risk_level(affecting_vulns, is_eol)
        recommendations = self._generate_security_recommendations(affecting_vulns, is_eol, current_version, "latest")
        
        return SecurityAssessment(
            application_name=app_name,
            current_version=current_version,
            vulnerabilities=affecting_vulns,
            is_security_update=len(affecting_vulns) > 0,
            is_eol=is_eol,
            eol_date=eol_date,
            security_score=security_score,
            risk_level=risk_level,
            recommendations=recommendations
        )