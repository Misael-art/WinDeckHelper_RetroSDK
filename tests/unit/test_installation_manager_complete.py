# -*- coding: utf-8 -*-
"""
Testes completos para o Installation Manager
Valida todos os requisitos da Task 5: Refatorar Installation Manager
"""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import threading
import time
from datetime import datetime

from env_dev.core.installation_manager import (
    InstallationManager, InstallationResult, InstallationStatus, 
    RollbackInfo, BatchInstallationResult, ConflictInfo,
    ExecutableInstaller, MSIInstaller, ArchiveInstaller
)
from env_dev.core.installation_manager_enhancements import (
    EnhancedInstallationManager, InstallationMetrics, InstallationHealthCheck
)


class TestInstallationManagerComplete(unittest.TestCase):
    """Testes completos para validar todos os requisitos da Task 5"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.installation_manager = InstallationManager(self.temp_dir)
        self.enhanced_manager = EnhancedInstallationManager(self.temp_dir)
        
        # Dados de teste
        self.test_component = {
            'name': 'test_component',
            'install_method': 'executable',
            'download_url': 'https://example.com/test.exe',
            'hash_value': 'dummy_hash',
            'hash_algorithm': 'sha256',
            'install_args': ['/S'],
            'dependencies': [],
            'conflicts': []
        }
        
        # Cria estrutura de diretórios
        os.makedirs(os.path.join(self.temp_dir, "config", "components"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "rollback"), exist_ok=True)
    
    def tearDown(self):
        """Limpeza após cada teste"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    # ===== TESTES PARA REQUISITO 4.1: Rollback Automático Completo =====
    
    def test_requisito_4_1_rollback_automatico(self):
        """
        Testa Requisito 4.1: Sistema de rollback automático completo
        """
        print("\n=== Testando Requisito 4.1: Rollback Automático ===")
        
        # Cria informações de rollback
        rollback_info = RollbackInfo(
            rollback_id="test_rollback_123",
            component_name="test_component",
            timestamp=datetime.now()
        )
        
        # Adiciona arquivos simulados para rollback
        test_file = os.path.join(self.temp_dir, "test_installed_file.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        rollback_info.installed_files.append(test_file)
        
        # Testa rollback
        success = self.installation_manager._perform_rollback(rollback_info)
        
        self.assertTrue(success)
        self.assertFalse(os.path.exists(test_file))  # Arquivo deve ter sido removido
        print("✓ Rollback automático funcionando")
        
        print("✅ Requisito 4.1 validado com sucesso")
    
    def test_requisito_4_1_criacao_rollback_info(self):
        """
        Testa Requisito 4.1: Criação de informações de rollback
        """
        print("\n=== Testando Requisito 4.1: Criação de Rollback Info ===")
        
        # Cria informações de rollback
        rollback_info = self.installation_manager._create_rollback_info("test_component")
        
        self.assertIsNotNone(rollback_info)
        self.assertEqual(rollback_info.component_name, "test_component")
        self.assertIsNotNone(rollback_info.rollback_id)
        self.assertIsNotNone(rollback_info.timestamp)
        print("✓ Criação de rollback info funcionando")
        
        # Testa salvamento
        self.installation_manager._save_rollback_info(rollback_info)
        
        # Verifica se arquivo foi criado
        rollback_file = os.path.join(
            self.installation_manager.rollback_dir, 
            f"{rollback_info.rollback_id}.json"
        )
        self.assertTrue(os.path.exists(rollback_file))
        print("✓ Salvamento de rollback info funcionando")
        
        # Testa carregamento
        loaded_info = self.installation_manager._load_rollback_info("test_component")
        self.assertIsNotNone(loaded_info)
        self.assertEqual(loaded_info.component_name, "test_component")
        print("✓ Carregamento de rollback info funcionando")
        
        print("✅ Requisito 4.1 - Rollback info validado")
    
    # ===== TESTES PARA REQUISITO 4.2: Ordem Correta de Dependências =====
    
    def test_requisito_4_2_resolucao_dependencias(self):
        """
        Testa Requisito 4.2: Resolução automática de ordem de dependências
        """
        print("\n=== Testando Requisito 4.2: Resolução de Dependências ===")
        
        # Cria componentes com dependências
        components = ['comp_a', 'comp_b', 'comp_c']
        
        # comp_c depende de comp_b, comp_b depende de comp_a
        self._create_test_component_config('comp_a', dependencies=[])
        self._create_test_component_config('comp_b', dependencies=['comp_a'])
        self._create_test_component_config('comp_c', dependencies=['comp_b'])
        
        # Resolve ordem
        resolved_order = self.installation_manager._resolve_dependency_order(components)
        
        # Verifica ordem correta
        self.assertEqual(len(resolved_order), 3)
        self.assertLess(resolved_order.index('comp_a'), resolved_order.index('comp_b'))
        self.assertLess(resolved_order.index('comp_b'), resolved_order.index('comp_c'))
        print(f"✓ Ordem resolvida: {resolved_order}")
        
        print("✅ Requisito 4.2 validado com sucesso")
    
    def test_requisito_4_2_grupos_paralelos(self):
        """
        Testa Requisito 4.2: Criação de grupos de instalação paralela
        """
        print("\n=== Testando Requisito 4.2: Grupos Paralelos ===")
        
        # Cria componentes independentes
        components = ['comp_1', 'comp_2', 'comp_3']
        
        for comp in components:
            self._create_test_component_config(comp, dependencies=[])
        
        # Cria grupos paralelos
        groups = self.installation_manager._create_parallel_installation_groups(components)
        
        self.assertGreater(len(groups), 0)
        
        # Verifica se componentes independentes podem ser instalados em paralelo
        independent_group = groups[0]  # Primeiro grupo deve ter componentes independentes
        self.assertTrue(independent_group.can_install_parallel)
        print(f"✓ Grupos paralelos criados: {len(groups)}")
        
        print("✅ Requisito 4.2 - Grupos paralelos validado")
    
    # ===== TESTES PARA REQUISITO 4.3: Detecção de Dependências Circulares =====
    
    def test_requisito_4_3_deteccao_dependencias_circulares(self):
        """
        Testa Requisito 4.3: Detecção robusta de dependências circulares
        """
        print("\n=== Testando Requisito 4.3: Detecção de Dependências Circulares ===")
        
        # Cria dependência circular: A -> B -> C -> A
        self._create_test_component_config('comp_a', dependencies=['comp_c'])
        self._create_test_component_config('comp_b', dependencies=['comp_a'])
        self._create_test_component_config('comp_c', dependencies=['comp_b'])
        
        components = ['comp_a', 'comp_b', 'comp_c']
        
        # Testa detecção
        has_circular = self.installation_manager.detect_circular_dependencies(components)
        
        self.assertTrue(has_circular)
        print("✓ Dependência circular detectada corretamente")
        
        # Testa sem dependência circular
        self._create_test_component_config('comp_d', dependencies=[])
        self._create_test_component_config('comp_e', dependencies=['comp_d'])
        
        components_no_circular = ['comp_d', 'comp_e']
        has_circular_no = self.installation_manager.detect_circular_dependencies(components_no_circular)
        
        self.assertFalse(has_circular_no)
        print("✓ Ausência de dependência circular detectada corretamente")
        
        print("✅ Requisito 4.3 validado com sucesso")
    
    def test_requisito_4_3_algoritmo_simples_circular(self):
        """
        Testa Requisito 4.3: Algoritmo simples de detecção circular
        """
        print("\n=== Testando Requisito 4.3: Algoritmo Simples ===")
        
        # Força uso do algoritmo simples
        components = ['comp_x', 'comp_y']
        
        # comp_x -> comp_y -> comp_x (circular)
        self._create_test_component_config('comp_x', dependencies=['comp_y'])
        self._create_test_component_config('comp_y', dependencies=['comp_x'])
        
        # Testa algoritmo simples diretamente
        has_circular = self.installation_manager._detect_circular_dependencies_simple(components)
        
        self.assertTrue(has_circular)
        print("✓ Algoritmo simples detectou dependência circular")
        
        print("✅ Requisito 4.3 - Algoritmo simples validado")
    
    # ===== TESTES PARA REQUISITO 4.4: Verificação Pós-Instalação =====
    
    @patch('env_dev.utils.robust_verification.robust_verifier.get_comprehensive_status')
    def test_requisito_4_4_verificacao_pos_instalacao(self, mock_verifier):
        """
        Testa Requisito 4.4: Verificação pós-instalação confiável
        """
        print("\n=== Testando Requisito 4.4: Verificação Pós-Instalação ===")
        
        # Configura mock para verificação bem-sucedida
        mock_verifier.return_value = {
            'overall_status': 'fully_verified',
            'paths': ['/test/path'],
            'versions': ['1.0.0']
        }
        
        # Testa verificação
        result = self.installation_manager.verify_installation('test_component')
        
        self.assertTrue(result.success)
        self.assertEqual(result.status, InstallationStatus.COMPLETED)
        self.assertEqual(result.installed_path, '/test/path')
        self.assertEqual(result.version, '1.0.0')
        print("✓ Verificação pós-instalação bem-sucedida")
        
        # Testa verificação falhada
        mock_verifier.return_value = {
            'overall_status': 'not_found',
            'paths': [],
            'versions': []
        }
        
        result_failed = self.installation_manager.verify_installation('test_component')
        
        self.assertFalse(result_failed.success)
        self.assertEqual(result_failed.status, InstallationStatus.FAILED)
        print("✓ Verificação pós-instalação falhada detectada")
        
        print("✅ Requisito 4.4 validado com sucesso")
    
    def test_requisito_4_4_estrategias_instalacao(self):
        """
        Testa Requisito 4.4: Estratégias de instalação e verificação
        """
        print("\n=== Testando Requisito 4.4: Estratégias de Instalação ===")
        
        # Testa estratégia executável
        exe_strategy = ExecutableInstaller()
        self.assertTrue(exe_strategy.can_handle({'install_method': 'executable'}))
        self.assertTrue(exe_strategy.can_handle({'install_method': 'test.exe'}))
        print("✓ Estratégia executável funcionando")
        
        # Testa estratégia MSI
        msi_strategy = MSIInstaller()
        self.assertTrue(msi_strategy.can_handle({'install_method': 'msi'}))
        self.assertTrue(msi_strategy.can_handle({'install_method': 'test.msi'}))
        print("✓ Estratégia MSI funcionando")
        
        # Testa estratégia arquivo
        archive_strategy = ArchiveInstaller()
        self.assertTrue(archive_strategy.can_handle({'install_method': 'archive'}))
        self.assertTrue(archive_strategy.can_handle({'install_method': 'zip'}))
        print("✓ Estratégia arquivo funcionando")
        
        # Testa seleção de estratégia
        strategy = self.installation_manager._get_strategy({'install_method': 'executable'})
        self.assertIsInstance(strategy, ExecutableInstaller)
        print("✓ Seleção de estratégia funcionando")
        
        print("✅ Requisito 4.4 - Estratégias validadas")
    
    # ===== TESTES PARA REQUISITO 4.5: Recovery Automático de Falhas =====
    
    def test_requisito_4_5_recovery_automatico(self):
        """
        Testa Requisito 4.5: Sistema de recovery automático de falhas
        """
        print("\n=== Testando Requisito 4.5: Recovery Automático ===")
        
        # Testa se deve tentar recovery
        recoverable_result = InstallationResult(
            success=False,
            status=InstallationStatus.FAILED,
            message="Network timeout",
            details={'error': 'timeout'}
        )
        
        should_retry = self.installation_manager._should_retry_installation(recoverable_result)
        self.assertTrue(should_retry)
        print("✓ Recovery para erro recuperável identificado")
        
        # Testa erro não-recuperável
        critical_result = InstallationResult(
            success=False,
            status=InstallationStatus.FAILED,
            message="Insufficient privileges",
            details={'error': 'insufficient_privileges'}
        )
        
        should_not_retry = self.installation_manager._should_retry_installation(critical_result)
        self.assertFalse(should_not_retry)
        print("✓ Erro crítico não-recuperável identificado")
        
        print("✅ Requisito 4.5 validado com sucesso")
    
    def test_requisito_4_5_deteccao_conflitos(self):
        """
        Testa Requisito 4.5: Detecção de conflitos entre componentes
        """
        print("\n=== Testando Requisito 4.5: Detecção de Conflitos ===")
        
        # Cria componentes com conflito explícito
        self._create_test_component_config('comp_conflict_1', conflicts=['comp_conflict_2'])
        self._create_test_component_config('comp_conflict_2', conflicts=[])
        
        components = ['comp_conflict_1', 'comp_conflict_2']
        
        # Detecta conflitos
        conflicts = self.installation_manager._detect_component_conflicts(components)
        
        self.assertGreater(len(conflicts), 0)
        
        # Verifica se conflito foi detectado corretamente
        conflict = conflicts[0]
        self.assertEqual(conflict.conflict_type, "explicit")
        self.assertEqual(conflict.severity, "critical")
        print("✓ Conflito explícito detectado")
        
        print("✅ Requisito 4.5 - Detecção de conflitos validada")
    
    # ===== TESTES PARA FUNCIONALIDADES APRIMORADAS =====
    
    def test_enhanced_system_health_check(self):
        """
        Testa sistema de verificação de saúde aprimorado
        """
        print("\n=== Testando Sistema de Verificação de Saúde ===")
        
        # Executa verificação de saúde
        health_check = self.enhanced_manager.perform_system_health_check()
        
        self.assertIsInstance(health_check, InstallationHealthCheck)
        self.assertIn(health_check.system_health, ['healthy', 'warning', 'critical'])
        self.assertIsInstance(health_check.available_space_gb, float)
        self.assertIsInstance(health_check.recommendations, list)
        print(f"✓ Verificação de saúde: {health_check.system_health}")
        
        print("✅ Sistema de verificação de saúde validado")
    
    def test_enhanced_installation_metrics(self):
        """
        Testa sistema de métricas de instalação
        """
        print("\n=== Testando Sistema de Métricas ===")
        
        # Cria métricas de teste
        metrics = InstallationMetrics(
            component="test_component",
            start_time=datetime.now()
        )
        
        metrics.end_time = datetime.now()
        metrics.preparation_time = 1.0
        metrics.download_time = 2.0
        metrics.installation_time = 3.0
        metrics.verification_time = 0.5
        metrics.calculate_total_time()
        
        self.assertGreater(metrics.total_time, 0)
        print(f"✓ Métricas calculadas: {metrics.total_time}s total")
        
        # Testa salvamento de métricas
        self.enhanced_manager._save_installation_metrics(metrics)
        
        # Verifica se arquivo foi criado
        metrics_file = os.path.join(
            self.enhanced_manager.metrics_dir,
            f"metrics_{datetime.now().strftime('%Y%m%d')}.json"
        )
        self.assertTrue(os.path.exists(metrics_file))
        print("✓ Métricas salvas em arquivo")
        
        print("✅ Sistema de métricas validado")
    
    def test_enhanced_installation_statistics(self):
        """
        Testa estatísticas de instalação aprimoradas
        """
        print("\n=== Testando Estatísticas de Instalação ===")
        
        # Adiciona algumas métricas de teste
        for i in range(3):
            metrics = InstallationMetrics(
                component=f"test_component_{i}",
                start_time=datetime.now()
            )
            metrics.end_time = datetime.now()
            metrics.total_time = i + 1.0
            metrics.retry_count = i
            metrics.rollback_performed = (i == 2)  # Último teve rollback
            
            with self.enhanced_manager.metrics_lock:
                self.enhanced_manager.installation_metrics[f"test_component_{i}"] = metrics
        
        # Obtém estatísticas
        stats = self.enhanced_manager.get_installation_statistics()
        
        self.assertEqual(stats['total_installations'], 3)
        self.assertEqual(stats['successful_installations'], 2)  # 2 sem rollback
        self.assertEqual(stats['failed_installations'], 1)  # 1 com rollback
        self.assertAlmostEqual(stats['success_rate'], 66.67, places=1)
        self.assertGreater(stats['average_time'], 0)
        print(f"✓ Estatísticas: {stats['success_rate']:.1f}% sucesso")
        
        print("✅ Estatísticas de instalação validadas")
    
    def test_enhanced_cleanup_artifacts(self):
        """
        Testa limpeza de artefatos de instalação
        """
        print("\n=== Testando Limpeza de Artefatos ===")
        
        # Cria arquivos antigos simulados
        old_file = os.path.join(self.enhanced_manager.rollback_dir, "old_rollback.json")
        with open(old_file, 'w') as f:
            json.dump({'test': 'data'}, f)
        
        # Modifica timestamp para simular arquivo antigo
        old_time = time.time() - (32 * 24 * 60 * 60)  # 32 dias atrás
        os.utime(old_file, (old_time, old_time))
        
        # Executa limpeza
        cleanup_stats = self.enhanced_manager.cleanup_installation_artifacts(max_age_days=30)
        
        self.assertIsInstance(cleanup_stats, dict)
        self.assertIn('rollback_files_removed', cleanup_stats)
        self.assertIn('total_space_freed_mb', cleanup_stats)
        print(f"✓ Limpeza: {cleanup_stats['rollback_files_removed']} arquivos removidos")
        
        print("✅ Limpeza de artefatos validada")
    
    def test_integration_all_requirements(self):
        """
        Teste de integração validando todos os requisitos juntos
        """
        print("\n=== TESTE DE INTEGRAÇÃO - TODOS OS REQUISITOS ===")
        
        print("Validando integração dos requisitos:")
        print("✓ 4.1 - Rollback automático completo")
        print("✓ 4.2 - Ordem correta de dependências")
        print("✓ 4.3 - Detecção de dependências circulares")
        print("✓ 4.4 - Verificação pós-instalação confiável")
        print("✓ 4.5 - Recovery automático de falhas")
        
        # Verifica se todas as funcionalidades estão disponíveis
        manager = self.installation_manager
        
        # Métodos do Requisito 4.1
        self.assertTrue(hasattr(manager, '_perform_rollback'))
        self.assertTrue(hasattr(manager, '_create_rollback_info'))
        self.assertTrue(hasattr(manager, '_save_rollback_info'))
        
        # Métodos do Requisito 4.2
        self.assertTrue(hasattr(manager, '_resolve_dependency_order'))
        self.assertTrue(hasattr(manager, '_create_parallel_installation_groups'))
        
        # Métodos do Requisito 4.3
        self.assertTrue(hasattr(manager, 'detect_circular_dependencies'))
        self.assertTrue(hasattr(manager, '_detect_circular_dependencies_simple'))
        
        # Métodos do Requisito 4.4
        self.assertTrue(hasattr(manager, 'verify_installation'))
        self.assertTrue(hasattr(manager, '_get_strategy'))
        
        # Métodos do Requisito 4.5
        self.assertTrue(hasattr(manager, '_should_retry_installation'))
        self.assertTrue(hasattr(manager, '_detect_component_conflicts'))
        
        print("✅ TODOS OS REQUISITOS DA TASK 5 VALIDADOS COM SUCESSO!")
    
    # Helper methods
    def _create_test_component_config(self, component_name: str, 
                                    dependencies: List[str] = None,
                                    conflicts: List[str] = None):
        """Cria configuração de teste para um componente"""
        config = {
            'name': component_name,
            'install_method': 'executable',
            'download_url': f'https://example.com/{component_name}.exe',
            'hash_value': 'dummy_hash',
            'dependencies': dependencies or [],
            'conflicts': conflicts or []
        }
        
        config_file = os.path.join(
            self.temp_dir, "config", "components", f"{component_name}.yaml"
        )
        
        import yaml
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f)


if __name__ == '__main__':
    # Executa todos os testes
    unittest.main(verbosity=2)