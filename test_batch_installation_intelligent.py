#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes para instalação em lote inteligente do Installation Manager
Testa as funcionalidades implementadas na task 5.2
"""

import os
import sys
import unittest
import tempfile
import shutil
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from env_dev.core.installation_manager import (
    InstallationManager, InstallationResult, InstallationStatus,
    BatchInstallationResult, ConflictInfo, ParallelInstallationGroup
)


class TestBatchInstallationIntelligent(unittest.TestCase):
    """Testes para instalação em lote inteligente"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = InstallationManager(self.temp_dir)
        
        # Mock dos componentes auxiliares
        self.manager.download_manager = Mock()
        self.manager.preparation_manager = Mock()
        
        # Configuração padrão de sucesso para preparation_manager
        prep_result = Mock()
        prep_result.status.value = "completed"
        prep_result.errors = []
        self.manager.preparation_manager.prepare_environment.return_value = prep_result
        
        # Cria estrutura de diretórios de teste
        os.makedirs(os.path.join(self.temp_dir, "config", "components"), exist_ok=True)
        
    def tearDown(self):
        """Limpeza após os testes"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _create_test_component_config(self, name: str, dependencies: list = None, 
                                    conflicts: list = None, supports_parallel: bool = True):
        """Cria configuração de teste para um componente"""
        config = {
            'name': name,
            'version': '1.0.0',
            'install_method': 'executable',
            'download_url': f'https://example.com/{name}.exe',
            'hash_value': 'test_hash',
            'dependencies': dependencies or [],
            'conflicts': conflicts or [],
            'supports_parallel_install': supports_parallel,
            'install_paths': [f'/test/{name}']
        }
        
        config_path = os.path.join(self.temp_dir, "config", "components", f"{name}.yaml")
        with open(config_path, 'w') as f:
            import yaml
            yaml.dump(config, f)
        
        return config
    
    def test_detect_component_conflicts_explicit(self):
        """Testa detecção de conflitos explícitos entre componentes"""
        # Cria componentes com conflitos explícitos
        self._create_test_component_config('comp1', conflicts=['comp2'])
        self._create_test_component_config('comp2')
        
        conflicts = self.manager._detect_component_conflicts(['comp1', 'comp2'])
        
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].conflict_type, 'explicit')
        self.assertEqual(conflicts[0].severity, 'critical')
        self.assertIn('comp1', [conflicts[0].component1, conflicts[0].component2])
        self.assertIn('comp2', [conflicts[0].component1, conflicts[0].component2])
    
    def test_detect_component_conflicts_path(self):
        """Testa detecção de conflitos de caminho entre componentes"""
        # Cria componentes com caminhos conflitantes
        config1 = self._create_test_component_config('comp1')
        config1['install_paths'] = ['/shared/path']
        
        config2 = self._create_test_component_config('comp2')
        config2['install_paths'] = ['/shared/path']
        
        # Salva configurações atualizadas
        import yaml
        for name, config in [('comp1', config1), ('comp2', config2)]:
            config_path = os.path.join(self.temp_dir, "config", "components", f"{name}.yaml")
            with open(config_path, 'w') as f:
                yaml.dump(config, f)
        
        conflicts = self.manager._detect_component_conflicts(['comp1', 'comp2'])
        
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].conflict_type, 'path')
        self.assertEqual(conflicts[0].severity, 'warning')
    
    def test_create_parallel_installation_groups_simple(self):
        """Testa criação de grupos de instalação paralela simples"""
        # Cria componentes independentes
        self._create_test_component_config('comp1')
        self._create_test_component_config('comp2')
        self._create_test_component_config('comp3')
        
        groups = self.manager._create_parallel_installation_groups(['comp1', 'comp2', 'comp3'])
        
        # Todos devem estar no mesmo grupo (nível 0) e podem ser paralelos
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].level, 0)
        self.assertEqual(len(groups[0].components), 3)
        self.assertTrue(groups[0].can_install_parallel)
    
    def test_create_parallel_installation_groups_with_dependencies(self):
        """Testa criação de grupos com dependências"""
        # Cria cadeia de dependências: comp1 -> comp2 -> comp3
        self._create_test_component_config('comp1', dependencies=['comp2'])
        self._create_test_component_config('comp2', dependencies=['comp3'])
        self._create_test_component_config('comp3')
        
        groups = self.manager._create_parallel_installation_groups(['comp1', 'comp2', 'comp3'])
        
        # Deve criar 3 grupos (um para cada nível)
        self.assertEqual(len(groups), 3)
        
        # Verifica ordem correta
        levels = {group.level: group.components for group in groups}
        self.assertIn('comp3', levels[0])  # Sem dependências
        self.assertIn('comp2', levels[1])  # Depende de comp3
        self.assertIn('comp1', levels[2])  # Depende de comp2
    
    def test_create_parallel_installation_groups_mixed(self):
        """Testa criação de grupos com dependências mistas"""
        # comp1 e comp2 dependem de comp3, comp4 é independente
        self._create_test_component_config('comp1', dependencies=['comp3'])
        self._create_test_component_config('comp2', dependencies=['comp3'])
        self._create_test_component_config('comp3')
        self._create_test_component_config('comp4')
        
        groups = self.manager._create_parallel_installation_groups(['comp1', 'comp2', 'comp3', 'comp4'])
        
        # Deve criar 2 grupos
        self.assertEqual(len(groups), 2)
        
        # Grupo 0: comp3 e comp4 (independentes)
        # Grupo 1: comp1 e comp2 (dependem de comp3)
        levels = {group.level: group.components for group in groups}
        self.assertEqual(len(levels[0]), 2)  # comp3 e comp4
        self.assertEqual(len(levels[1]), 2)  # comp1 e comp2
    
    @patch('env_dev.core.installation_manager.InstallationManager.install_component')
    def test_install_group_parallel_success(self, mock_install):
        """Testa instalação paralela bem-sucedida de um grupo"""
        # Mock de instalação bem-sucedida
        mock_install.return_value = InstallationResult(
            success=True,
            status=InstallationStatus.COMPLETED,
            message="Sucesso",
            details={}
        )
        
        # Cria grupo de teste
        group = ParallelInstallationGroup(
            components=['comp1', 'comp2', 'comp3'],
            level=0,
            can_install_parallel=True
        )
        
        result = BatchInstallationResult(overall_success=False)
        
        # Testa instalação paralela
        success = self.manager._install_group_parallel(group, 3, True, result)
        
        self.assertTrue(success)
        self.assertEqual(len(result.completed_components), 3)
        self.assertEqual(len(result.failed_components), 0)
        self.assertEqual(mock_install.call_count, 3)
    
    @patch('env_dev.core.installation_manager.InstallationManager.install_component')
    def test_install_group_parallel_partial_failure(self, mock_install):
        """Testa instalação paralela com falha parcial"""
        # Mock com uma falha
        def mock_install_side_effect(component):
            if component == 'comp2':
                return InstallationResult(
                    success=False,
                    status=InstallationStatus.FAILED,
                    message="Falha",
                    details={'error': 'test_error'}
                )
            return InstallationResult(
                success=True,
                status=InstallationStatus.COMPLETED,
                message="Sucesso",
                details={}
            )
        
        mock_install.side_effect = mock_install_side_effect
        
        group = ParallelInstallationGroup(
            components=['comp1', 'comp2', 'comp3'],
            level=0,
            can_install_parallel=True
        )
        
        result = BatchInstallationResult(overall_success=False)
        
        success = self.manager._install_group_parallel(group, 3, True, result)
        
        self.assertFalse(success)
        self.assertEqual(len(result.completed_components), 2)
        self.assertEqual(len(result.failed_components), 1)
        self.assertIn('comp2', result.failed_components)
    
    @patch('env_dev.core.installation_manager.InstallationManager._install_component_with_recovery')
    def test_install_group_sequential_success(self, mock_install):
        """Testa instalação sequencial bem-sucedida"""
        mock_install.return_value = InstallationResult(
            success=True,
            status=InstallationStatus.COMPLETED,
            message="Sucesso",
            details={}
        )
        
        group = ParallelInstallationGroup(
            components=['comp1', 'comp2'],
            level=0,
            can_install_parallel=False
        )
        
        result = BatchInstallationResult(overall_success=False)
        
        success = self.manager._install_group_sequential(group, True, result)
        
        self.assertTrue(success)
        self.assertEqual(len(result.completed_components), 2)
        self.assertEqual(mock_install.call_count, 2)
    
    @patch('env_dev.core.installation_manager.InstallationManager.install_component')
    def test_install_component_with_recovery_success_first_try(self, mock_install):
        """Testa recovery com sucesso na primeira tentativa"""
        mock_install.return_value = InstallationResult(
            success=True,
            status=InstallationStatus.COMPLETED,
            message="Sucesso",
            details={}
        )
        
        result = BatchInstallationResult(overall_success=False)
        
        install_result = self.manager._install_component_with_recovery('comp1', True, result)
        
        self.assertTrue(install_result.success)
        self.assertEqual(mock_install.call_count, 1)
        self.assertNotIn('comp1', result.recovery_attempts)
    
    @patch('env_dev.core.installation_manager.InstallationManager.install_component')
    def test_install_component_with_recovery_success_after_retry(self, mock_install):
        """Testa recovery com sucesso após retry"""
        # Primeira tentativa falha, segunda sucede
        mock_install.side_effect = [
            InstallationResult(
                success=False,
                status=InstallationStatus.FAILED,
                message="Falha temporária",
                details={'error': 'network_timeout'}
            ),
            InstallationResult(
                success=True,
                status=InstallationStatus.COMPLETED,
                message="Sucesso",
                details={}
            )
        ]
        
        result = BatchInstallationResult(overall_success=False)
        
        install_result = self.manager._install_component_with_recovery('comp1', True, result)
        
        self.assertTrue(install_result.success)
        self.assertEqual(mock_install.call_count, 2)
        self.assertEqual(result.recovery_attempts['comp1'], 2)
    
    @patch('env_dev.core.installation_manager.InstallationManager.install_component')
    def test_install_component_with_recovery_no_retry_critical_error(self, mock_install):
        """Testa que não tenta recovery para erros críticos"""
        mock_install.return_value = InstallationResult(
            success=False,
            status=InstallationStatus.FAILED,
            message="Erro crítico",
            details={'error': 'insufficient_privileges'}
        )
        
        result = BatchInstallationResult(overall_success=False)
        
        install_result = self.manager._install_component_with_recovery('comp1', True, result)
        
        self.assertFalse(install_result.success)
        self.assertEqual(mock_install.call_count, 1)  # Não tenta novamente
        self.assertNotIn('comp1', result.recovery_attempts)
    
    def test_should_retry_installation_recoverable_errors(self):
        """Testa identificação de erros recuperáveis"""
        recoverable_cases = [
            {'error': 'network_timeout'},
            {'error': 'download_failed'},
            {'error': 'temporary_failure'}
        ]
        
        for case in recoverable_cases:
            result = InstallationResult(
                success=False,
                status=InstallationStatus.FAILED,
                message="Erro",
                details=case
            )
            
            self.assertTrue(
                self.manager._should_retry_installation(result),
                f"Deveria tentar recovery para: {case}"
            )
    
    def test_should_retry_installation_non_recoverable_errors(self):
        """Testa identificação de erros não-recuperáveis"""
        non_recoverable_cases = [
            {'error': 'insufficient_privileges'},
            {'error': 'disk_space'},
            {'error': 'circular_dependency'}
        ]
        
        for case in non_recoverable_cases:
            result = InstallationResult(
                success=False,
                status=InstallationStatus.FAILED,
                message="Erro",
                details=case
            )
            
            self.assertFalse(
                self.manager._should_retry_installation(result),
                f"Não deveria tentar recovery para: {case}"
            )
    
    def test_has_critical_failures(self):
        """Testa detecção de falhas críticas"""
        result = BatchInstallationResult(overall_success=False)
        
        # Adiciona falha não-crítica
        result.installation_results['comp1'] = InstallationResult(
            success=False,
            status=InstallationStatus.FAILED,
            message="Erro",
            details={'error': 'network_timeout'}
        )
        
        self.assertFalse(self.manager._has_critical_failures(result))
        
        # Adiciona falha crítica
        result.installation_results['comp2'] = InstallationResult(
            success=False,
            status=InstallationStatus.FAILED,
            message="Erro crítico",
            details={'error': 'insufficient_privileges'}
        )
        
        self.assertTrue(self.manager._has_critical_failures(result))
    
    @patch('env_dev.core.installation_manager.InstallationManager._create_parallel_installation_groups')
    @patch('env_dev.core.installation_manager.InstallationManager._detect_component_conflicts')
    @patch('env_dev.core.installation_manager.InstallationManager.detect_circular_dependencies')
    def test_install_multiple_with_conflicts_critical(self, mock_circular, mock_conflicts, mock_groups):
        """Testa instalação múltipla com conflitos críticos"""
        # Mock de conflito crítico
        mock_circular.return_value = False
        mock_conflicts.return_value = [
            ConflictInfo(
                component1='comp1',
                component2='comp2',
                conflict_type='explicit',
                description='Conflito crítico',
                severity='critical'
            )
        ]
        
        result = self.manager.install_multiple(['comp1', 'comp2'])
        
        self.assertFalse(result.overall_success)
        self.assertEqual(len(result.detected_conflicts), 1)
        self.assertEqual(result.detected_conflicts[0].severity, 'critical')
        # Não deve tentar criar grupos se há conflitos críticos
        mock_groups.assert_not_called()
    
    @patch('env_dev.core.installation_manager.InstallationManager._install_group_parallel')
    @patch('env_dev.core.installation_manager.InstallationManager._create_parallel_installation_groups')
    @patch('env_dev.core.installation_manager.InstallationManager._detect_component_conflicts')
    @patch('env_dev.core.installation_manager.InstallationManager.detect_circular_dependencies')
    def test_install_multiple_parallel_execution(self, mock_circular, mock_conflicts, mock_groups, mock_parallel):
        """Testa execução paralela na instalação múltipla"""
        # Setup mocks
        mock_circular.return_value = False
        mock_conflicts.return_value = []
        
        # Cria grupo que pode ser instalado em paralelo
        parallel_group = ParallelInstallationGroup(
            components=['comp1', 'comp2'],
            level=0,
            can_install_parallel=True
        )
        mock_groups.return_value = [parallel_group]
        mock_parallel.return_value = True
        
        result = self.manager.install_multiple(['comp1', 'comp2'], max_parallel=2)
        
        # Verifica que instalação paralela foi chamada
        mock_parallel.assert_called_once()
        args = mock_parallel.call_args[0]
        self.assertEqual(args[0], parallel_group)  # Grupo correto
        self.assertEqual(args[1], 2)  # max_parallel correto
    
    def test_integration_full_batch_installation(self):
        """Teste de integração completo da instalação em lote"""
        # Cria componentes de teste com dependências
        self._create_test_component_config('base')
        self._create_test_component_config('middleware', dependencies=['base'])
        self._create_test_component_config('app1', dependencies=['middleware'])
        self._create_test_component_config('app2', dependencies=['middleware'])
        
        # Mock dos downloads e instalações
        self.manager.download_manager.download_with_verification.return_value = Mock(
            success=True,
            file_path='/tmp/test.exe'
        )
        
        with patch('env_dev.core.installation_manager.InstallationManager.install_component') as mock_install:
            mock_install.return_value = InstallationResult(
                success=True,
                status=InstallationStatus.COMPLETED,
                message="Sucesso",
                details={}
            )
            
            result = self.manager.install_multiple(['app1', 'app2', 'middleware', 'base'])
            
            # Verifica resultado
            self.assertTrue(result.overall_success)
            self.assertEqual(len(result.completed_components), 4)
            self.assertEqual(len(result.failed_components), 0)
            
            # Verifica ordem de instalação (base -> middleware -> apps)
            expected_order = ['base', 'middleware', 'app1', 'app2']
            # Os apps podem estar em qualquer ordem, mas base e middleware devem vir primeiro
            self.assertEqual(result.dependency_order[0], 'base')
            self.assertEqual(result.dependency_order[1], 'middleware')
            self.assertIn('app1', result.dependency_order[2:])
            self.assertIn('app2', result.dependency_order[2:])


if __name__ == '__main__':
    # Configura logging para os testes
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    unittest.main(verbosity=2)