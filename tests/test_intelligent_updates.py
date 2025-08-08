"""Testes para o sistema de atualizações inteligentes.

Testa a funcionalidade de verificação inteligente de atualizações
e verificação de segurança.

Author: AI Assistant
Date: 2024
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from pathlib import Path

# Adicionar o diretório pai ao path para importações
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.intelligent_update_checker import (
    IntelligentUpdateChecker,
    UpdateInfo,
    UpdatePriority,
    UpdateStrategy,
    UpdateReason,
    UpdateRecommendation,
    get_intelligent_update_checker
)
from core.security_update_checker import (
    SecurityUpdateChecker,
    VulnerabilityInfo,
    VulnerabilitySeverity,
    SecurityAssessment
)
from core.detection_engine import DetectedApplication, DetectionMethod, ApplicationStatus


class TestUpdateInfo(unittest.TestCase):
    """Testes para a classe UpdateInfo."""
    
    def test_update_info_creation(self):
        """Testa criação de UpdateInfo."""
        update = UpdateInfo(
            application_name="Git",
            current_version="2.40.0",
            available_version="2.43.0",
            priority=UpdatePriority.MEDIUM,
            strategy=UpdateStrategy.SCHEDULED,
            reasons=[UpdateReason.BUG_FIX, UpdateReason.FEATURE_UPDATE]
        )
        
        self.assertEqual(update.application_name, "Git")
        self.assertEqual(update.current_version, "2.40.0")
        self.assertEqual(update.available_version, "2.43.0")
        self.assertEqual(update.priority, UpdatePriority.MEDIUM)
        self.assertEqual(update.strategy, UpdateStrategy.SCHEDULED)
        self.assertIn(UpdateReason.BUG_FIX, update.reasons)
        self.assertIn(UpdateReason.FEATURE_UPDATE, update.reasons)
    
    def test_update_info_defaults(self):
        """Testa valores padrão de UpdateInfo."""
        update = UpdateInfo(
            application_name="Test",
            current_version="1.0.0",
            available_version="1.1.0",
            priority=UpdatePriority.LOW,
            strategy=UpdateStrategy.MANUAL,
            reasons=[UpdateReason.BUG_FIX]
        )
        
        self.assertEqual(update.description, "")
        self.assertIsNone(update.release_date)
        self.assertEqual(update.security_score, 0.0)
        self.assertEqual(update.download_url, "")
        self.assertEqual(update.estimated_download_size, 0)
        self.assertFalse(update.requires_restart)
        self.assertFalse(update.backup_recommended)


class TestVulnerabilityInfo(unittest.TestCase):
    """Testes para a classe VulnerabilityInfo."""
    
    def test_vulnerability_info_creation(self):
        """Testa criação de VulnerabilityInfo."""
        vuln = VulnerabilityInfo(
            cve_id="CVE-2023-12345",
            severity=VulnerabilitySeverity.HIGH,
            score=7.5,
            description="Test vulnerability",
            affected_versions=["<2.40.0"],
            fixed_version="2.40.0",
            published_date=datetime(2023, 1, 1)
        )
        
        self.assertEqual(vuln.cve_id, "CVE-2023-12345")
        self.assertEqual(vuln.severity, VulnerabilitySeverity.HIGH)
        self.assertEqual(vuln.score, 7.5)
        self.assertEqual(vuln.description, "Test vulnerability")
        self.assertEqual(vuln.affected_versions, ["<2.40.0"])
        self.assertEqual(vuln.fixed_version, "2.40.0")
        self.assertFalse(vuln.exploit_available)
        self.assertTrue(vuln.patch_available)


class TestSecurityUpdateChecker(unittest.TestCase):
    """Testes para SecurityUpdateChecker."""
    
    def setUp(self):
        """Configuração para cada teste."""
        self.checker = SecurityUpdateChecker()
    
    def test_initialization(self):
        """Testa inicialização do SecurityUpdateChecker."""
        self.assertIsInstance(self.checker._known_vulnerabilities, dict)
        self.assertIn("git", self.checker._known_vulnerabilities)
        self.assertIn("nodejs", self.checker._known_vulnerabilities)
        self.assertIn("python", self.checker._eol_info)
    
    def test_normalize_app_name(self):
        """Testa normalização de nomes de aplicação."""
        self.assertEqual(self.checker._normalize_app_name("Visual Studio Code"), "visual_studio_code")
        self.assertEqual(self.checker._normalize_app_name("Node.js"), "nodejs")
        self.assertEqual(self.checker._normalize_app_name("Java JDK"), "java")
        self.assertEqual(self.checker._normalize_app_name(".NET Core"), "dotnet")
        self.assertEqual(self.checker._normalize_app_name("Git"), "git")
    
    def test_compare_versions(self):
        """Testa comparação de versões."""
        self.assertEqual(self.checker._compare_versions("1.0.0", "1.0.0"), 0)
        self.assertEqual(self.checker._compare_versions("1.0.0", "1.0.1"), -1)
        self.assertEqual(self.checker._compare_versions("1.0.1", "1.0.0"), 1)
        self.assertEqual(self.checker._compare_versions("2.0.0", "1.9.9"), 1)
        self.assertEqual(self.checker._compare_versions("1.9.9", "2.0.0"), -1)
    
    def test_matches_version_pattern(self):
        """Testa correspondência de padrões de versão."""
        self.assertTrue(self.checker._matches_version_pattern("2.39.0", "<2.40.0"))
        self.assertFalse(self.checker._matches_version_pattern("2.40.0", "<2.40.0"))
        self.assertTrue(self.checker._matches_version_pattern("2.40.0", ">=2.40.0"))
        self.assertFalse(self.checker._matches_version_pattern("2.39.0", ">=2.40.0"))
        self.assertTrue(self.checker._matches_version_pattern("2.40.0", "2.40.0"))
    
    def test_version_is_affected(self):
        """Testa se versão é afetada por vulnerabilidade."""
        self.assertTrue(self.checker._version_is_affected("2.39.0", ["<2.40.0"]))
        self.assertFalse(self.checker._version_is_affected("2.40.0", ["<2.40.0"]))
        self.assertTrue(self.checker._version_is_affected("2.39.0", ["<2.40.0", ">=3.0.0"]))
    
    def test_check_eol_status(self):
        """Testa verificação de status EOL."""
        # Python 2.7 já está EOL
        is_eol, eol_date = self.checker._check_eol_status("python", "2.7.18")
        self.assertTrue(is_eol)
        self.assertIsNotNone(eol_date)
        
        # Python 3.11 ainda não está EOL
        is_eol, eol_date = self.checker._check_eol_status("python", "3.11.5")
        self.assertFalse(is_eol)
        
        # Aplicação desconhecida
        is_eol, eol_date = self.checker._check_eol_status("unknown_app", "1.0.0")
        self.assertFalse(is_eol)
        self.assertIsNone(eol_date)
    
    def test_calculate_security_score(self):
        """Testa cálculo de score de segurança."""
        # Sem vulnerabilidades
        score = self.checker._calculate_security_score([], False)
        self.assertEqual(score, 0.0)
        
        # Com EOL
        score = self.checker._calculate_security_score([], True)
        self.assertEqual(score, 5.0)
        
        # Com vulnerabilidade crítica
        vuln = VulnerabilityInfo(
            cve_id="CVE-2023-12345",
            severity=VulnerabilitySeverity.CRITICAL,
            score=9.5,
            description="Critical vuln",
            affected_versions=["<2.40.0"],
            fixed_version="2.40.0",
            published_date=datetime.now()
        )
        score = self.checker._calculate_security_score([vuln], False)
        self.assertEqual(score, 9.5)
    
    def test_determine_risk_level(self):
        """Testa determinação de nível de risco."""
        # Sem vulnerabilidades
        risk = self.checker._determine_risk_level([], False)
        self.assertEqual(risk, "minimal")
        
        # Com EOL
        risk = self.checker._determine_risk_level([], True)
        self.assertEqual(risk, "high")
        
        # Com vulnerabilidade crítica
        critical_vuln = VulnerabilityInfo(
            cve_id="CVE-2023-12345",
            severity=VulnerabilitySeverity.CRITICAL,
            score=9.5,
            description="Critical vuln",
            affected_versions=["<2.40.0"],
            fixed_version="2.40.0",
            published_date=datetime.now()
        )
        risk = self.checker._determine_risk_level([critical_vuln], False)
        self.assertEqual(risk, "critical")
        
        # Com vulnerabilidade alta
        high_vuln = VulnerabilityInfo(
            cve_id="CVE-2023-12346",
            severity=VulnerabilitySeverity.HIGH,
            score=7.5,
            description="High vuln",
            affected_versions=["<2.40.0"],
            fixed_version="2.40.0",
            published_date=datetime.now()
        )
        risk = self.checker._determine_risk_level([high_vuln], False)
        self.assertEqual(risk, "high")
    
    @patch('asyncio.sleep', new_callable=AsyncMock)
    async def test_check_security_updates(self, mock_sleep):
        """Testa verificação de atualizações de segurança."""
        result = await self.checker.check_security_updates("git", "2.39.0", "2.43.0")
        
        self.assertIsInstance(result, dict)
        self.assertIn("vulnerabilities", result)
        self.assertIn("is_security_update", result)
        self.assertIn("score", result)
        self.assertIn("risk_level", result)
        self.assertIn("recommendations", result)
    
    @patch('asyncio.sleep', new_callable=AsyncMock)
    async def test_get_security_assessment(self, mock_sleep):
        """Testa obtenção de avaliação de segurança."""
        assessment = await self.checker.get_security_assessment("git", "2.39.0")
        
        self.assertIsInstance(assessment, SecurityAssessment)
        self.assertEqual(assessment.application_name, "git")
        self.assertEqual(assessment.current_version, "2.39.0")
        self.assertIsInstance(assessment.vulnerabilities, list)
        self.assertIsInstance(assessment.recommendations, list)
    
    def test_cache_functionality(self):
        """Testa funcionalidade de cache."""
        # Verificar cache vazio inicialmente
        self.assertFalse(self.checker._is_cache_valid("test_app"))
        
        # Limpar cache
        self.checker.clear_cache()
        
        # Obter estatísticas
        stats = self.checker.get_cache_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("cached_apps", stats)
        self.assertIn("total_vulnerabilities", stats)


class TestIntelligentUpdateChecker(unittest.TestCase):
    """Testes para IntelligentUpdateChecker."""
    
    def setUp(self):
        """Configuração para cada teste."""
        self.checker = IntelligentUpdateChecker()
    
    def test_initialization(self):
        """Testa inicialização do IntelligentUpdateChecker."""
        self.assertIsInstance(self.checker.config, dict)
        self.assertIn("check_interval_hours", self.checker.config)
        self.assertIsInstance(self.checker.update_sources, dict)
        self.assertIn("git", self.checker.update_sources)
        self.assertIn("nodejs", self.checker.update_sources)
    
    def test_normalize_app_name(self):
        """Testa normalização de nomes de aplicação."""
        self.assertEqual(self.checker._normalize_app_name("Visual Studio Code"), "visual_studio_code")
        self.assertEqual(self.checker._normalize_app_name("Node.js"), "nodejs")
        self.assertEqual(self.checker._normalize_app_name("Java JDK"), "java")
        self.assertEqual(self.checker._normalize_app_name(".NET Core"), "dotnet")
    
    def test_determine_update_priority(self):
        """Testa determinação de prioridade de atualização."""
        app = DetectedApplication(
            name="Git",
            version="2.39.0",
            detection_method=DetectionMethod.REGISTRY,
            status=ApplicationStatus.INSTALLED
        )
        
        # Vulnerabilidade crítica
        security_info = {"critical_vulnerabilities": 1, "is_security_update": True}
        priority = self.checker._determine_update_priority(app, "2.43.0", security_info)
        self.assertEqual(priority, UpdatePriority.CRITICAL)
        
        # Vulnerabilidade alta
        security_info = {"critical_vulnerabilities": 0, "high_vulnerabilities": 1, "is_security_update": True}
        priority = self.checker._determine_update_priority(app, "2.43.0", security_info)
        self.assertEqual(priority, UpdatePriority.HIGH)
        
        # Atualização normal
        security_info = {"critical_vulnerabilities": 0, "high_vulnerabilities": 0, "is_security_update": False}
        priority = self.checker._determine_update_priority(app, "2.40.0", security_info)
        self.assertEqual(priority, UpdatePriority.LOW)  # Patch version
    
    def test_determine_update_strategy(self):
        """Testa determinação de estratégia de atualização."""
        # Crítica
        strategy = self.checker._determine_update_strategy(UpdatePriority.CRITICAL, {"is_security_update": True})
        self.assertEqual(strategy, UpdateStrategy.IMMEDIATE)
        
        # Alta com auto-update desabilitado
        strategy = self.checker._determine_update_strategy(UpdatePriority.HIGH, {"is_security_update": True})
        self.assertEqual(strategy, UpdateStrategy.SCHEDULED)
        
        # Média
        strategy = self.checker._determine_update_strategy(UpdatePriority.MEDIUM, {"is_security_update": False})
        self.assertEqual(strategy, UpdateStrategy.SCHEDULED)
        
        # Baixa
        strategy = self.checker._determine_update_strategy(UpdatePriority.LOW, {"is_security_update": False})
        self.assertEqual(strategy, UpdateStrategy.MANUAL)
    
    def test_determine_update_reasons(self):
        """Testa determinação de razões de atualização."""
        # Vulnerabilidade de segurança
        security_info = {"critical_vulnerabilities": 1, "is_security_update": True}
        reasons = self.checker._determine_update_reasons(security_info, "2.39.0", "2.40.0")
        self.assertIn(UpdateReason.SECURITY_VULNERABILITY, reasons)
        
        # EOL
        security_info = {"is_eol": True}
        reasons = self.checker._determine_update_reasons(security_info, "2.39.0", "2.40.0")
        self.assertIn(UpdateReason.EOL_VERSION, reasons)
        
        # Major version update
        security_info = {}
        reasons = self.checker._determine_update_reasons(security_info, "2.39.0", "3.0.0")
        self.assertIn(UpdateReason.FEATURE_UPDATE, reasons)
    
    def test_requires_restart(self):
        """Testa verificação de necessidade de reinicialização."""
        self.assertTrue(self.checker._requires_restart("Visual Studio Code"))
        self.assertTrue(self.checker._requires_restart("Git"))
        self.assertTrue(self.checker._requires_restart("Java JDK"))
        self.assertFalse(self.checker._requires_restart("Unknown App"))
    
    def test_create_update_info(self):
        """Testa criação de informações de atualização."""
        app = DetectedApplication(
            name="Git",
            version="2.39.0",
            detection_method=DetectionMethod.REGISTRY,
            status=ApplicationStatus.INSTALLED
        )
        
        security_info = {
            "critical_vulnerabilities": 0,
            "high_vulnerabilities": 1,
            "is_security_update": True,
            "score": 7.5
        }
        
        update_info = self.checker._create_update_info(app, "2.43.0", security_info)
        
        self.assertEqual(update_info.application_name, "Git")
        self.assertEqual(update_info.current_version, "2.39.0")
        self.assertEqual(update_info.available_version, "2.43.0")
        self.assertEqual(update_info.priority, UpdatePriority.HIGH)
        self.assertEqual(update_info.security_score, 7.5)
        self.assertTrue(update_info.requires_restart)
        self.assertTrue(update_info.backup_recommended)
    
    def test_create_batch_groups(self):
        """Testa criação de grupos de lote."""
        updates = [
            UpdateInfo(
                application_name="App1",
                current_version="1.0.0",
                available_version="1.1.0",
                priority=UpdatePriority.CRITICAL,
                strategy=UpdateStrategy.IMMEDIATE,
                reasons=[UpdateReason.SECURITY_VULNERABILITY]
            ),
            UpdateInfo(
                application_name="App2",
                current_version="2.0.0",
                available_version="2.1.0",
                priority=UpdatePriority.HIGH,
                strategy=UpdateStrategy.SCHEDULED,
                reasons=[UpdateReason.BUG_FIX]
            ),
            UpdateInfo(
                application_name="App3",
                current_version="3.0.0",
                available_version="3.1.0",
                priority=UpdatePriority.LOW,
                strategy=UpdateStrategy.MANUAL,
                reasons=[UpdateReason.FEATURE_UPDATE]
            )
        ]
        
        batches = self.checker._create_batch_groups(updates)
        
        self.assertEqual(len(batches), 3)  # Critical, High, Low
        self.assertIn("App1", batches[0])  # Critical
        self.assertIn("App2", batches[1])  # High
        self.assertIn("App3", batches[2])  # Low
    
    def test_generate_warnings(self):
        """Testa geração de avisos."""
        updates = [
            UpdateInfo(
                application_name="App1",
                current_version="1.0.0",
                available_version="1.1.0",
                priority=UpdatePriority.HIGH,
                strategy=UpdateStrategy.IMMEDIATE,
                reasons=[UpdateReason.SECURITY_VULNERABILITY],
                requires_restart=True,
                backup_recommended=True
            ),
            UpdateInfo(
                application_name="App2",
                current_version="2.0.0",
                available_version="2.1.0",
                priority=UpdatePriority.MEDIUM,
                strategy=UpdateStrategy.SCHEDULED,
                reasons=[UpdateReason.BUG_FIX],
                conflicts=["App3"]
            )
        ]
        
        warnings = self.checker._generate_warnings(updates)
        
        self.assertTrue(any("reinicialização" in warning for warning in warnings))
        self.assertTrue(any("Backup" in warning for warning in warnings))
        self.assertTrue(any("conflitos" in warning for warning in warnings))
    
    @patch('asyncio.sleep', new_callable=AsyncMock)
    async def test_get_latest_version(self, mock_sleep):
        """Testa obtenção de versão mais recente."""
        # Aplicação conhecida
        version = await self.checker._get_latest_version("git")
        self.assertIsNotNone(version)
        
        # Aplicação desconhecida
        version = await self.checker._get_latest_version("unknown_app")
        self.assertIsNone(version)
    
    def test_cache_functionality(self):
        """Testa funcionalidade de cache."""
        # Verificar cache vazio inicialmente
        self.assertFalse(self.checker._is_cache_valid("test_app"))
        
        # Limpar cache
        self.checker.clear_cache()
        
        # Obter estatísticas
        stats = self.checker.get_cache_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("cached_updates", stats)
        self.assertIn("last_checks", stats)
    
    def test_generate_update_recommendation_empty(self):
        """Testa geração de recomendação com lista vazia."""
        recommendation = self.checker._generate_update_recommendation([])
        
        self.assertEqual(recommendation.total_updates, 0)
        self.assertEqual(recommendation.critical_updates, 0)
        self.assertEqual(recommendation.security_updates, 0)
        self.assertEqual(recommendation.recommended_action, "Nenhuma atualização necessária")
        self.assertEqual(recommendation.risk_assessment, "Baixo")
    
    def test_generate_update_recommendation_with_updates(self):
        """Testa geração de recomendação com atualizações."""
        updates = [
            UpdateInfo(
                application_name="App1",
                current_version="1.0.0",
                available_version="1.1.0",
                priority=UpdatePriority.CRITICAL,
                strategy=UpdateStrategy.IMMEDIATE,
                reasons=[UpdateReason.SECURITY_VULNERABILITY]
            ),
            UpdateInfo(
                application_name="App2",
                current_version="2.0.0",
                available_version="2.1.0",
                priority=UpdatePriority.HIGH,
                strategy=UpdateStrategy.SCHEDULED,
                reasons=[UpdateReason.SECURITY_VULNERABILITY]
            )
        ]
        
        recommendation = self.checker._generate_update_recommendation(updates)
        
        self.assertEqual(recommendation.total_updates, 2)
        self.assertEqual(recommendation.critical_updates, 1)
        self.assertEqual(recommendation.security_updates, 2)
        self.assertIn("crítica", recommendation.recommended_action)
        self.assertEqual(recommendation.risk_assessment, "Alto")


class TestGlobalFunctions(unittest.TestCase):
    """Testes para funções globais."""
    
    def test_get_intelligent_update_checker(self):
        """Testa obtenção da instância global."""
        checker1 = get_intelligent_update_checker()
        checker2 = get_intelligent_update_checker()
        
        # Deve retornar a mesma instância
        self.assertIs(checker1, checker2)
        self.assertIsInstance(checker1, IntelligentUpdateChecker)


class TestAsyncMethods(unittest.TestCase):
    """Testes para métodos assíncronos."""
    
    def setUp(self):
        """Configuração para cada teste."""
        self.checker = IntelligentUpdateChecker()
        self.security_checker = SecurityUpdateChecker()
    
    @patch('asyncio.sleep', new_callable=AsyncMock)
    async def test_check_updates_for_applications(self, mock_sleep):
        """Testa verificação de atualizações para aplicações."""
        applications = [
            DetectedApplication(
                name="Git",
                version="2.39.0",
                detection_method=DetectionMethod.REGISTRY,
                status=ApplicationStatus.INSTALLED
            ),
            DetectedApplication(
                name="Node.js",
                version="18.0.0",
                detection_method=DetectionMethod.PATH_BASED,
                status=ApplicationStatus.INSTALLED
            )
        ]
        
        with patch.object(self.checker, '_get_latest_version', new_callable=AsyncMock) as mock_get_version:
            mock_get_version.side_effect = ["2.43.0", "20.10.0"]
            
            with patch.object(self.checker.security_checker, 'check_security_updates', new_callable=AsyncMock) as mock_security:
                mock_security.return_value = {
                    "critical_vulnerabilities": 0,
                    "high_vulnerabilities": 1,
                    "is_security_update": True,
                    "score": 7.5
                }
                
                recommendation = await self.checker.check_updates_for_applications(applications)
        
        self.assertIsInstance(recommendation, UpdateRecommendation)
        self.assertGreaterEqual(recommendation.total_updates, 0)


if __name__ == '__main__':
    # Executar testes assíncronos
    async def run_async_tests():
        suite = unittest.TestSuite()
        
        # Adicionar testes assíncronos
        async_test_cases = [
            TestSecurityUpdateChecker('test_check_security_updates'),
            TestSecurityUpdateChecker('test_get_security_assessment'),
            TestAsyncMethods('test_check_updates_for_applications'),
            TestIntelligentUpdateChecker('test_get_latest_version')
        ]
        
        for test_case in async_test_cases:
            try:
                await test_case.debug()
            except Exception as e:
                print(f"Erro no teste {test_case}: {e}")
    
    # Executar testes síncronos
    unittest.main(verbosity=2, exit=False)
    
    # Executar testes assíncronos
    print("\nExecutando testes assíncronos...")
    asyncio.run(run_async_tests())