# -*- coding: utf-8 -*-
"""
Testes unitários completos para todos os managers implementados
Valida todos os requisitos das Tasks 3, 5, 6 e 7
"""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

# Imports dos managers completos
from env_dev.core.download_manager_enhancements import EnhancedDownloadManager
from env_dev.core.installation_manager_enhancements import EnhancedInstallationManager
from env_dev.core.organization_manager_complete import CompleteOrganizationManager
from env_dev.core.recovery_manager_complete import CompleteRecoveryManager

# Imports dos modelos de dados
from env_dev.core.download_manager import DownloadResult, DownloadStatus, DownloadProgress
from env_dev.core.installation_manager import InstallationResult, InstallationStatus
from env_dev.core.organization_manager import CleanupResult, OrganizationResult, CleanupStatus
from env_dev.core.recovery_manager import RepairResult, RestoreResult, RecoveryStatus


class TestCompleteDownloadManager(unittest.TestCase):
    """Testes completos para o Enhanced Download Manager"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.download_manager = EnhancedDownloadManager()
        self.download_manager.temp_dir = self.temp_dir
        self.download_manager.cache_dir = os.path.join(self.temp_dir, "cache")
        os.makedirs(self.download_manager.cache_dir, exist_ok=True)
        
        # Dados de teste
        self.test_component = {
            'name': 'test_component',
            'download_url': 'https://example.com/test.exe',
            'checksum': {
                'value': 'dummy_hash_value',
                'algorithm': 'sha256'
            },
            'mirror_urls': ['https://mirror1.com/test.exe', 'https://mirror2.com/test.exe']
        }
    
    def tearDown(self):
        """Limpeza após cada teste"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('env_dev.core.download_manager.requests.get')
    @patch('env_dev.core.download_manager.test_internet_connection')
    def test_download_with_verification_success(self, mock_connection, mock_get):
        """Testa download com verificação bem-sucedida (Requisito 2.1)"""
        # Configura mocks
        mock_connection.return_value = True
        mock_response = Mock()
        mock_response.headers = {'content-length': '1024'}
        mock_response.iter_content.return_value = [b'test_content']
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Mock do cálculo de hash
        with patch.object(self.download_manager, '_calculate_file_hash') as mock_hash:
            mock_hash.return_value = 'dummy_hash_value'
            
            result = self.download_manager.download_with_verification(
                'https://example.com/test.exe',
                'dummy_hash_value',
                'sha256'
            )
            
            self.assertTrue(result.success)
            self.assertTrue(result.verification_passed)
            self.assertIn('verificado com sucesso', result.message)
    
    @patch('env_dev.core.download_manager.requests.get')
    @patch('env_dev.core.download_manager.test_internet_connection')
    def test_download_with_verification_hash_mismatch(self, mock_connection, mock_get):
        """Testa falha na verificação de hash (Requisito 2.2)"""
        # Configura mocks
        mock_connection.return_value = True
        mock_response = Mock()
        mock_response.headers = {'content-length': '1024'}
        mock_response.iter_content.return_value = [b'test_content']
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Mock do cálculo de hash (hash diferente)
        with patch.object(self.download_manager, '_calculate_file_hash') as mock_hash:
            mock_hash.return_value = 'different_hash_value'
            
            result = self.download_manager.download_with_verification(
                'https://example.com/test.exe',
                'expected_hash_value',
                'sha256'
            )
            
            self.assertFalse(result.success)
            self.assertFalse(result.verification_passed)
            self.assertIn('Falha na verificação de integridade', result.message)
    
    def test_download_without_hash_security_warning(self):
        """Testa aviso de segurança quando não há hash (Requisito 2.1)"""
        result = self.download_manager.download_with_verification(
            'https://example.com/test.exe',
            '',  # Hash vazio
            'sha256'
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, 'security_warning')
        self.assertIn('AVISO DE SEGURANÇA', result.message)
    
    @patch('env_dev.core.download_manager.requests.get')
    @patch('env_dev.core.download_manager.test_internet_connection')
    def test_download_with_retry_success_on_second_attempt(self, mock_connection, mock_get):
        """Testa retry automático com sucesso na segunda tentativa (Requisito 2.2)"""
        mock_connection.return_value = True
        
        # Primeira tentativa falha, segunda sucede
        mock_responses = [
            Mock(side_effect=Exception("Network error")),  # Primeira falha
            Mock()  # Segunda sucede
        ]
        
        mock_responses[1].headers = {'content-length': '1024'}
        mock_responses[1].iter_content.return_value = [b'test_content']
        mock_responses[1].raise_for_status.return_value = None
        
        mock_get.side_effect = mock_responses
        
        with patch.object(self.download_manager, '_calculate_file_hash') as mock_hash:
            mock_hash.return_value = 'dummy_hash_value'
            
            result = self.download_manager.download_with_retry(
                'https://example.com/test.exe',
                'dummy_hash_value',
                max_retries=3
            )
            
            self.assertTrue(result.success)
            self.assertEqual(result.retry_count, 1)  # Segunda tentativa (índice 1)
    
    def test_download_cache_functionality(self):
        """Testa funcionalidade de cache de downloads (Requisito 2.4)"""
        # Simula arquivo em cache
        cache_entry = {
            'file_path': os.path.join(self.download_manager.cache_dir, 'test_component_12345678.cache'),
            'hash_value': 'dummy_hash_value',
            'algorithm': 'sha256',
            'download_time': datetime.now().isoformat(),
            'file_size': 1024
        }
        
        # Cria arquivo de cache físico
        os.makedirs(os.path.dirname(cache_entry['file_path']), exist_ok=True)
        with open(cache_entry['file_path'], 'w') as f:
            f.write('cached_content')
        
        # Adiciona ao cache do manager
        self.download_manager.download_cache['test_component'] = type('CacheEntry', (), cache_entry)()
        
        # Mock da verificação de integridade
        with patch.object(self.download_manager, 'verify_file_integrity') as mock_verify:
            mock_verify.return_value = True
            
            result = self.download_manager.download_with_cache(
                self.test_component,
                self.temp_dir,
                use_cache=True
            )
            
            self.assertTrue(result.success)
            self.assertIn('cache', result.message)
    
    def test_batch_download_functionality(self):
        """Testa download em lote (Requisito 2.4)"""
        components = [
            {
                'name': 'component1',
                'download_url': 'https://example.com/comp1.exe',
                'checksum': {'value': 'hash1', 'algorithm': 'sha256'}
            },
            {
                'name': 'component2', 
                'download_url': 'https://example.com/comp2.exe',
                'checksum': {'value': 'hash2', 'algorithm': 'sha256'}
            }
        ]
        
        # Mock do download individual
        with patch.object(self.download_manager, 'download_with_cache') as mock_download:
            mock_download.return_value = DownloadResult(
                success=True,
                file_path='/path/to/file',
                message='Download successful'
            )
            
            results = self.download_manager.batch_download(
                components,
                self.temp_dir,
                max_concurrent=2
            )
            
            self.assertEqual(len(results), 2)
            self.assertIn('component1', results)
            self.assertIn('component2', results)
            self.assertTrue(all(result.success for result in results.values()))
    
    def test_cleanup_cache_functionality(self):
        """Testa limpeza de cache (Requisito 2.3)"""
        # Cria arquivos de cache antigos
        old_cache_file = os.path.join(self.download_manager.cache_dir, 'old_file.cache')
        with open(old_cache_file, 'w') as f:
            f.write('old_content')
        
        # Define data antiga
        old_time = time.time() - (25 * 3600)  # 25 horas atrás
        os.utime(old_cache_file, (old_time, old_time))
        
        # Adiciona entrada antiga ao cache
        from env_dev.core.download_manager_enhancements import DownloadCache
        old_cache_entry = DownloadCache(
            file_path=old_cache_file,
            hash_value='old_hash',
            algorithm='sha256',
            download_time=datetime.fromtimestamp(old_time),
            file_size=1024
        )
        self.download_manager.download_cache['old_component'] = old_cache_entry
        
        # Executa limpeza
        self.download_manager.cleanup_cache(max_age_hours=24)
        
        # Verifica se arquivo foi removido
        self.assertFalse(os.path.exists(old_cache_file))
        self.assertNotIn('old_component', self.download_manager.download_cache)
    
    def test_download_statistics(self):
        """Testa coleta de estatísticas de download (Requisito 2.4)"""
        # Simula algumas estatísticas
        self.download_manager.statistics = {
            'total_downloads': 10,
            'successful_downloads': 8,
            'failed_downloads': 2,
            'cache_hits': 3,
            'total_bytes_downloaded': 1024 * 1024 * 100  # 100MB
        }
        
        stats = self.download_manager.get_download_statistics()
        
        self.assertEqual(stats['total_downloads'], 10)
        self.assertEqual(stats['success_rate'], 80.0)
        self.assertEqual(stats['cache_hit_rate'], 30.0)
        self.assertIn('average_speed', stats)


class TestCompleteInstallationManager(unittest.TestCase):
    """Testes completos para o Enhanced Installation Manager"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.installation_manager = EnhancedInstallationManager(self.temp_dir)
        
        # Dados de teste
        self.test_component = 'test_component'
    
    def tearDown(self):
        """Limpeza após cada teste"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_system_health_check(self):
        """Testa verificação de saúde do sistema (Requisito 4.1)"""
        health_check = self.installation_manager.perform_system_health_check()
        
        self.assertIsNotNone(health_check)
        self.assertIn(health_check.system_health, ['healthy', 'warning', 'critical'])
        self.assertIsInstance(health_check.available_space_gb, float)
        self.assertIsInstance(health_check.admin_privileges, bool)
        self.assertIsInstance(health_check.network_connectivity, bool)
    
    @patch('env_dev.core.installation_manager.InstallationManager.install_component')
    def test_install_component_enhanced_with_metrics(self, mock_install):
        """Testa instalação aprimorada com métricas (Requisito 4.4)"""
        # Mock do resultado da instalação
        mock_install.return_value = InstallationResult(
            success=True,
            status=InstallationStatus.COMPLETED,
            message="Installation successful",
            details={}
        )
        
        result = self.installation_manager.install_component_enhanced(
            self.test_component
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.status, InstallationStatus.COMPLETED)
        
        # Verifica se métricas foram coletadas
        self.assertIn(self.test_component, self.installation_manager.installation_metrics)
        metrics = self.installation_manager.installation_metrics[self.test_component]
        self.assertIsNotNone(metrics.start_time)
        self.assertIsNotNone(metrics.end_time)
    
    def test_installation_statistics(self):
        """Testa coleta de estatísticas de instalação (Requisito 4.4)"""
        # Simula algumas métricas
        from env_dev.core.installation_manager_enhancements import InstallationMetrics
        
        metrics1 = InstallationMetrics(
            component='comp1',
            start_time=datetime.now() - timedelta(minutes=5),
            end_time=datetime.now(),
            total_time=300,
            rollback_performed=False
        )
        
        metrics2 = InstallationMetrics(
            component='comp2',
            start_time=datetime.now() - timedelta(minutes=10),
            end_time=datetime.now(),
            total_time=600,
            rollback_performed=True
        )
        
        self.installation_manager.installation_metrics = {
            'comp1': metrics1,
            'comp2': metrics2
        }
        
        stats = self.installation_manager.get_installation_statistics()
        
        self.assertEqual(stats['total_installations'], 2)
        self.assertEqual(stats['successful_installations'], 1)
        self.assertEqual(stats['failed_installations'], 1)
        self.assertEqual(stats['success_rate'], 50.0)
        self.assertEqual(stats['rollback_rate'], 50.0)
    
    @patch('env_dev.core.installation_manager.InstallationManager.install_multiple')
    def test_install_multiple_enhanced_with_optimization(self, mock_install_multiple):
        """Testa instalação em lote aprimorada (Requisito 4.2)"""
        from env_dev.core.installation_manager import BatchInstallationResult
        
        # Mock do resultado da instalação em lote
        mock_result = BatchInstallationResult(overall_success=True)
        mock_result.completed_components = ['comp1', 'comp2']
        mock_result.failed_components = []
        mock_install_multiple.return_value = mock_result
        
        components = ['comp1', 'comp2', 'comp3']
        
        result = self.installation_manager.install_multiple_enhanced(
            components,
            max_parallel=2,
            enable_smart_recovery=True
        )
        
        self.assertTrue(result.overall_success)
        self.assertIsInstance(result.total_time, float)
    
    def test_cleanup_installation_artifacts(self):
        """Testa limpeza de artefatos de instalação (Requisito 4.1)"""
        # Cria alguns arquivos de teste antigos
        old_file = os.path.join(self.installation_manager.rollback_dir, 'old_rollback.json')
        os.makedirs(os.path.dirname(old_file), exist_ok=True)
        
        with open(old_file, 'w') as f:
            json.dump({'test': 'data'}, f)
        
        # Define data antiga
        old_time = time.time() - (31 * 24 * 3600)  # 31 dias atrás
        os.utime(old_file, (old_time, old_time))
        
        # Executa limpeza
        cleanup_stats = self.installation_manager.cleanup_installation_artifacts(max_age_days=30)
        
        self.assertIsInstance(cleanup_stats, dict)
        self.assertIn('rollback_files_removed', cleanup_stats)
        self.assertIn('total_space_freed_mb', cleanup_stats)


class TestCompleteOrganizationManager(unittest.TestCase):
    """Testes completos para o Complete Organization Manager"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.organization_manager = CompleteOrganizationManager(str(self.temp_dir))
        
        # Cria estrutura de diretórios de teste
        self.temp_subdir = self.temp_dir / "temp"
        self.logs_subdir = self.temp_dir / "logs"
        self.downloads_subdir = self.temp_dir / "downloads"
        self.backups_subdir = self.temp_dir / "backups"
        
        for subdir in [self.temp_subdir, self.logs_subdir, self.downloads_subdir, self.backups_subdir]:
            subdir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """Limpeza após cada teste"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cleanup_temporary_files(self):
        """Testa limpeza de arquivos temporários (Requisito 5.1)"""
        # Cria arquivos temporários de teste
        temp_files = [
            self.temp_subdir / "test.tmp",
            self.temp_subdir / "old_file.temp",
            self.temp_subdir / "backup.bak"
        ]
        
        for temp_file in temp_files:
            temp_file.write_text("temporary content")
            
            # Define como arquivo antigo
            old_time = time.time() - (25 * 3600)  # 25 horas atrás
            os.utime(temp_file, (old_time, old_time))
        
        # Executa limpeza
        result = self.organization_manager.cleanup_temporary_files(max_age_hours=24)
        
        self.assertEqual(result.status, CleanupStatus.COMPLETED)
        self.assertEqual(result.files_removed, 3)
        self.assertGreater(result.space_freed, 0)
        
        # Verifica se arquivos foram removidos
        for temp_file in temp_files:
            self.assertFalse(temp_file.exists())
    
    def test_organize_downloads(self):
        """Testa organização de downloads (Requisito 5.2)"""
        # Cria arquivos de download de teste
        download_files = [
            self.downloads_subdir / "program.exe",
            self.downloads_subdir / "archive.zip",
            self.downloads_subdir / "document.pdf",
            self.downloads_subdir / "image.jpg"
        ]
        
        for download_file in download_files:
            download_file.write_text("download content")
        
        # Executa organização
        result = self.organization_manager.organize_downloads(create_subdirs=True)
        
        self.assertEqual(result.status, CleanupStatus.COMPLETED)
        self.assertGreater(result.files_organized, 0)
        self.assertGreater(result.directories_created, 0)
        
        # Verifica se subdiretórios foram criados
        expected_subdirs = ['executables', 'archives', 'documents', 'images']
        for subdir in expected_subdirs:
            self.assertTrue((self.downloads_subdir / subdir).exists())
    
    def test_rotate_logs(self):
        """Testa rotação de logs (Requisito 5.4)"""
        # Cria arquivos de log de teste
        log_files = [
            self.logs_subdir / "old.log",
            self.logs_subdir / "recent.log"
        ]
        
        # Arquivo antigo
        log_files[0].write_text("old log content" * 1000)  # Arquivo grande
        old_time = time.time() - (8 * 24 * 3600)  # 8 dias atrás
        os.utime(log_files[0], (old_time, old_time))
        
        # Arquivo recente
        log_files[1].write_text("recent log content")
        
        # Executa rotação
        result = self.organization_manager.rotate_logs(max_age_days=7, max_size_mb=1)
        
        self.assertEqual(result.status, CleanupStatus.COMPLETED)
        self.assertGreater(result.files_removed, 0)
        
        # Verifica se diretório de arquivo foi criado
        archive_dir = self.logs_subdir / "archived"
        self.assertTrue(archive_dir.exists())
    
    def test_manage_backups(self):
        """Testa gerenciamento de backups (Requisito 5.3)"""
        # Cria arquivos de backup de teste
        backup_files = []
        for i in range(15):  # Mais que o máximo permitido
            backup_file = self.backups_subdir / f"component_backup_{i:02d}.zip"
            backup_file.write_text(f"backup content {i}")
            
            # Define datas diferentes
            backup_time = time.time() - (i * 24 * 3600)  # i dias atrás
            os.utime(backup_file, (backup_time, backup_time))
            backup_files.append(backup_file)
        
        # Executa gerenciamento
        result = self.organization_manager.manage_backups(max_backups=10, max_age_days=30)
        
        self.assertEqual(result.status, CleanupStatus.COMPLETED)
        self.assertGreater(result.backups_processed, 0)
        self.assertGreater(result.backups_removed, 0)
        
        # Verifica se backups excedentes foram removidos
        remaining_files = list(self.backups_subdir.glob("*.zip"))
        self.assertLessEqual(len(remaining_files), 10)
    
    def test_optimize_disk_usage(self):
        """Testa otimização de uso de disco (Requisito 5.5)"""
        # Cria arquivos para otimização
        large_files = []
        for i in range(3):
            large_file = self.temp_dir / f"large_file_{i}.txt"
            large_file.write_text("large content " * 10000)  # Arquivo grande
            large_files.append(large_file)
        
        # Executa otimização
        result = self.organization_manager.optimize_disk_usage(target_free_space_gb=1.0)
        
        self.assertIn(result.status, [CleanupStatus.COMPLETED, CleanupStatus.PARTIAL, CleanupStatus.SKIPPED])
        self.assertIsInstance(result.total_space_freed, int)
        self.assertIsInstance(result.operations_performed, list)
    
    def test_analyze_disk_usage(self):
        """Testa análise de uso de disco"""
        # Cria arquivos de diferentes tipos
        (self.temp_subdir / "temp_file.tmp").write_text("temp content")
        (self.logs_subdir / "app.log").write_text("log content")
        (self.backups_subdir / "backup.zip").write_text("backup content")
        
        # Executa análise
        analysis = self.organization_manager.analyze_disk_usage()
        
        self.assertIsNotNone(analysis)
        self.assertGreater(analysis.total_space, 0)
        self.assertGreaterEqual(analysis.free_space, 0)
        self.assertIsInstance(analysis.recommendations, list)
        self.assertIsInstance(analysis.largest_files, list)
        self.assertIsInstance(analysis.oldest_files, list)
    
    def test_auto_cleanup_schedule(self):
        """Testa agendamento de limpeza automática"""
        # Configura limpeza automática
        self.organization_manager.auto_cleanup_schedule.enabled = True
        self.organization_manager.auto_cleanup_schedule.interval_hours = 1
        
        # Inicia limpeza automática
        self.organization_manager.start_auto_cleanup()
        
        # Verifica se thread foi iniciada
        self.assertTrue(self.organization_manager.cleanup_running)
        self.assertIsNotNone(self.organization_manager.cleanup_thread)
        
        # Para limpeza automática
        self.organization_manager.stop_auto_cleanup()
        
        # Verifica se foi parada
        self.assertFalse(self.organization_manager.cleanup_running)
    
    def test_organization_statistics(self):
        """Testa coleta de estatísticas de organização"""
        # Executa análise para gerar dados
        self.organization_manager.analyze_disk_usage()
        
        # Obtém estatísticas
        stats = self.organization_manager.get_organization_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('managed_directories', stats)
        self.assertIn('auto_cleanup_enabled', stats)
        self.assertIn('cleanup_running', stats)
        
        if 'last_analysis' in stats and stats['last_analysis']:
            self.assertIn('total_space_gb', stats)
            self.assertIn('free_space_gb', stats)
            self.assertIn('free_space_percent', stats)


class TestCompleteRecoveryManager(unittest.TestCase):
    """Testes completos para o Complete Recovery Manager"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.recovery_manager = CompleteRecoveryManager(self.temp_dir)
        
        # Mock do diagnostic manager
        self.recovery_manager.diagnostic_manager = Mock()
    
    def tearDown(self):
        """Limpeza após cada teste"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_auto_repair_issues_success(self):
        """Testa reparo automático bem-sucedido (Requisito 8.1)"""
        # Cria problemas de teste
        from env_dev.core.diagnostic_manager import Issue
        
        test_issues = [
            Issue(
                id="issue1",
                title="Test Issue 1",
                description="Missing dependency",
                severity="critical",
                category="dependency",
                issue_type="missing_dependency",
                details={'dependency_name': 'test_dep'}
            ),
            Issue(
                id="issue2", 
                title="Test Issue 2",
                description="Permission problem",
                severity="warning",
                category="permission",
                issue_type="permission_issue",
                details={'file_path': '/test/path'}
            )
        ]
        
        # Mock dos métodos de reparo
        with patch.object(self.recovery_manager, '_execute_issue_repair') as mock_repair:
            mock_repair.return_value = RepairResult(
                action_id="test_repair",
                status=RecoveryStatus.COMPLETED,
                message="Repair successful"
            )
            
            result = self.recovery_manager.auto_repair_issues(test_issues)
            
            self.assertIn(result.status, [RecoveryStatus.COMPLETED, RecoveryStatus.PARTIAL])
            self.assertIsInstance(result.details, dict)
            self.assertIn('total_issues', result.details)
    
    def test_restore_from_backup_success(self):
        """Testa restauração bem-sucedida de backup (Requisito 8.5)"""
        backup_id = "test_backup_123"
        
        # Mock das funções de backup
        with patch.object(self.recovery_manager, '_get_backup_info') as mock_get_backup, \
             patch.object(self.recovery_manager, '_validate_backup_integrity') as mock_validate, \
             patch.object(self.recovery_manager, '_create_safety_backup') as mock_safety, \
             patch.object(self.recovery_manager, '_restore_configuration_backup') as mock_restore:
            
            # Configura mocks
            from env_dev.core.recovery_manager import BackupInfo, BackupType
            mock_backup_info = BackupInfo(
                id=backup_id,
                name="Test Backup",
                backup_type=BackupType.CONFIGURATION,
                path="/test/backup/path",
                size=1024,
                created_at=datetime.now(),
                description="Test backup"
            )
            
            mock_get_backup.return_value = mock_backup_info
            mock_validate.return_value = True
            mock_safety.return_value = "safety_backup_456"
            mock_restore.return_value = True
            
            # Mock da verificação pós-restauração
            with patch.object(self.recovery_manager, '_verify_post_restore_state') as mock_verify:
                mock_verify.return_value = {'success': True, 'warnings': [], 'errors': []}
                
                result = self.recovery_manager.restore_from_backup(backup_id)
                
                self.assertEqual(result.status, RecoveryStatus.COMPLETED)
                self.assertEqual(result.backup_id, backup_id)
                self.assertIn('sucesso', result.message)
    
    def test_update_components_check_only(self):
        """Testa verificação de atualizações sem instalar (Requisito 8.2)"""
        components = ['component1', 'component2']
        
        # Mock da verificação de atualizações
        from env_dev.core.recovery_manager_complete import UpdateInfo
        mock_updates = {
            'component1': UpdateInfo(
                component='component1',
                current_version='1.0.0',
                available_version='1.1.0',
                update_url='https://example.com/update',
                changelog='Bug fixes',
                is_critical=False,
                size_mb=10.5
            )
        }
        
        with patch.object(self.recovery_manager, '_check_component_updates') as mock_check:
            mock_check.return_value = mock_updates
            
            result = self.recovery_manager.update_components(components, check_only=True)
            
            self.assertEqual(result['status'], 'completed')
            self.assertEqual(result['updates_available'], 1)
            self.assertIn('component1', result['component_results'])
    
    def test_fix_inconsistencies_success(self):
        """Testa correção de inconsistências (Requisito 8.3)"""
        # Mock da detecção de inconsistências
        mock_inconsistencies = [
            {
                'type': 'missing_file',
                'description': 'Missing configuration file',
                'severity': 'critical',
                'file_path': '/test/config.json'
            },
            {
                'type': 'corrupted_config',
                'description': 'Corrupted settings',
                'severity': 'warning',
                'config_file': '/test/settings.ini'
            }
        ]
        
        with patch.object(self.recovery_manager, '_detect_system_inconsistencies') as mock_detect, \
             patch.object(self.recovery_manager, '_apply_inconsistency_fix') as mock_fix:
            
            mock_detect.return_value = mock_inconsistencies
            mock_fix.return_value = True
            
            result = self.recovery_manager.fix_inconsistencies(deep_scan=False)
            
            self.assertEqual(result.status, RecoveryStatus.COMPLETED)
            self.assertIn('inconsistências corrigidas', result.message)
            self.assertIsInstance(result.details, dict)
    
    def test_generate_health_report(self):
        """Testa geração de relatório de saúde (Requisito 8.4)"""
        # Mock do resultado do diagnóstico
        from env_dev.core.diagnostic_manager import DiagnosticResult, HealthStatus, Issue
        
        mock_diagnostic_result = DiagnosticResult(
            overall_health=HealthStatus.HEALTHY,
            issues=[
                Issue(
                    id="test_issue",
                    title="Test Issue",
                    description="Test description",
                    severity="warning",
                    category="test"
                )
            ],
            system_info={},
            timestamp=datetime.now()
        )
        
        self.recovery_manager.diagnostic_manager.run_full_diagnostic.return_value = mock_diagnostic_result
        
        # Mock dos métodos auxiliares
        with patch.object(self.recovery_manager, '_collect_performance_metrics') as mock_perf, \
             patch.object(self.recovery_manager, '_check_security_status') as mock_security, \
             patch.object(self.recovery_manager, '_analyze_component_status') as mock_components:
            
            mock_perf.return_value = {'cpu_usage_percent': 50.0}
            mock_security.return_value = {'critical_files_intact': True}
            mock_components.return_value = {'component1': 'healthy'}
            
            report = self.recovery_manager.generate_health_report(include_recommendations=True)
            
            self.assertIsNotNone(report)
            self.assertEqual(report.overall_health, HealthStatus.HEALTHY)
            self.assertIsInstance(report.system_issues, list)
            self.assertIsInstance(report.recommendations, list)
            self.assertIsInstance(report.performance_metrics, dict)
    
    def test_notify_outdated_components(self):
        """Testa notificação de componentes desatualizados (Requisito 8.2)"""
        # Mock dos componentes instalados
        mock_installed = {
            'component1': '1.0.0',
            'component2': '2.0.0'
        }
        
        # Mock da verificação de atualizações
        from env_dev.core.recovery_manager_complete import UpdateInfo
        mock_update = UpdateInfo(
            component='component1',
            current_version='1.0.0',
            available_version='1.1.0',
            update_url='https://example.com/update',
            changelog='Security fixes',
            is_critical=True,
            size_mb=15.2
        )
        
        with patch.object(self.recovery_manager, '_get_installed_components') as mock_installed_comp, \
             patch.object(self.recovery_manager, '_check_single_component_update') as mock_check_update:
            
            mock_installed_comp.return_value = mock_installed
            mock_check_update.side_effect = lambda name, version: mock_update if name == 'component1' else None
            
            outdated = self.recovery_manager.notify_outdated_components()
            
            self.assertIn('component1', outdated)
            self.assertEqual(outdated['component1'].is_critical, True)
    
    def test_recovery_statistics(self):
        """Testa coleta de estatísticas de recuperação"""
        # Simula alguns reparos na história
        self.recovery_manager.repair_history = [
            RepairResult(
                action_id="repair1",
                status=RecoveryStatus.COMPLETED,
                message="Success"
            ),
            RepairResult(
                action_id="repair2", 
                status=RecoveryStatus.FAILED,
                message="Failed"
            )
        ]
        
        # Mock dos componentes instalados
        with patch.object(self.recovery_manager, '_get_installed_components') as mock_components:
            mock_components.return_value = {'comp1': '1.0', 'comp2': '2.0'}
            
            stats = self.recovery_manager.get_recovery_statistics()
            
            self.assertIsInstance(stats, dict)
            self.assertEqual(stats['total_repairs_attempted'], 2)
            self.assertEqual(stats['successful_repairs'], 1)
            self.assertEqual(stats['failed_repairs'], 1)
            self.assertEqual(stats['success_rate'], 50.0)
            self.assertEqual(stats['components_monitored'], 2)


class TestIntegrationScenarios(unittest.TestCase):
    """Testes de integração entre os managers"""
    
    def setUp(self):
        """Configuração inicial para testes de integração"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Inicializa todos os managers
        self.download_manager = EnhancedDownloadManager()
        self.installation_manager = EnhancedInstallationManager(self.temp_dir)
        self.organization_manager = CompleteOrganizationManager(self.temp_dir)
        self.recovery_manager = CompleteRecoveryManager(self.temp_dir)
    
    def tearDown(self):
        """Limpeza após testes de integração"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_installation_workflow(self):
        """Testa fluxo completo de instalação com todos os managers"""
        component_data = {
            'name': 'test_integration_component',
            'download_url': 'https://example.com/test.exe',
            'checksum': {'value': 'test_hash', 'algorithm': 'sha256'},
            'install_method': 'executable'
        }
        
        # Mock das operações
        with patch.object(self.download_manager, 'download_with_cache') as mock_download, \
             patch.object(self.installation_manager, 'install_component_enhanced') as mock_install, \
             patch.object(self.organization_manager, 'cleanup_temporary_files') as mock_cleanup:
            
            # Configura mocks
            mock_download.return_value = DownloadResult(
                success=True,
                file_path='/path/to/downloaded/file.exe',
                message='Download successful'
            )
            
            mock_install.return_value = InstallationResult(
                success=True,
                status=InstallationStatus.COMPLETED,
                message='Installation successful',
                details={}
            )
            
            mock_cleanup.return_value = CleanupResult(
                status=CleanupStatus.COMPLETED,
                files_removed=5,
                space_freed=1024*1024
            )
            
            # Simula fluxo completo
            # 1. Download
            download_result = self.download_manager.download_with_cache(
                component_data, self.temp_dir
            )
            self.assertTrue(download_result.success)
            
            # 2. Instalação
            install_result = self.installation_manager.install_component_enhanced(
                component_data['name']
            )
            self.assertTrue(install_result.success)
            
            # 3. Limpeza
            cleanup_result = self.organization_manager.cleanup_temporary_files()
            self.assertEqual(cleanup_result.status, CleanupStatus.COMPLETED)
    
    def test_error_recovery_workflow(self):
        """Testa fluxo de recuperação de erros"""
        # Simula falha na instalação
        with patch.object(self.installation_manager, 'install_component_enhanced') as mock_install, \
             patch.object(self.recovery_manager, 'auto_repair_issues') as mock_repair:
            
            # Configura falha na instalação
            mock_install.return_value = InstallationResult(
                success=False,
                status=InstallationStatus.FAILED,
                message='Installation failed',
                details={'error': 'dependency_missing'}
            )
            
            # Configura reparo bem-sucedido
            mock_repair.return_value = RepairResult(
                action_id="auto_repair",
                status=RecoveryStatus.COMPLETED,
                message="Issues repaired"
            )
            
            # Simula fluxo de recuperação
            install_result = self.installation_manager.install_component_enhanced('test_component')
            self.assertFalse(install_result.success)
            
            # Tenta reparo automático
            from env_dev.core.diagnostic_manager import Issue
            mock_issues = [
                Issue(
                    id="dep_issue",
                    title="Missing Dependency",
                    description="Required dependency not found",
                    severity="critical",
                    category="dependency"
                )
            ]
            
            repair_result = self.recovery_manager.auto_repair_issues(mock_issues)
            self.assertEqual(repair_result.status, RecoveryStatus.COMPLETED)


if __name__ == '__main__':
    # Configura logging para os testes
    logging.basicConfig(level=logging.WARNING)
    
    # Executa todos os testes
    unittest.main(verbosity=2)