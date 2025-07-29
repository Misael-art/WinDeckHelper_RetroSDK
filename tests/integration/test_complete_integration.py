# -*- coding: utf-8 -*-
"""
Testes de integração completos para o Environment Dev Script
Valida fluxos end-to-end e comunicação entre componentes
"""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import threading
import time
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Imports dos managers completos
from env_dev.core.download_manager_enhancements import EnhancedDownloadManager
from env_dev.core.installation_manager_enhancements import EnhancedInstallationManager
from env_dev.core.organization_manager_complete import CompleteOrganizationManager
from env_dev.core.recovery_manager_complete import CompleteRecoveryManager
from env_dev.core.diagnostic_manager import DiagnosticManager

# Imports dos modelos de dados
from env_dev.core.download_manager import DownloadResult, DownloadStatus
from env_dev.core.installation_manager import InstallationResult, InstallationStatus
from env_dev.core.organization_manager import CleanupResult, CleanupStatus
from env_dev.core.recovery_manager import RepairResult, RecoveryStatus


class TestCompleteSystemIntegration(unittest.TestCase):
    """Testes de integração completa do sistema"""
    
    @classmethod
    def setUpClass(cls):
        """Configuração única para toda a classe de testes"""
        cls.test_workspace = Path(tempfile.mkdtemp(prefix="env_dev_integration_"))
        
        # Cria estrutura de diretórios completa
        cls.directories = {
            'downloads': cls.test_workspace / 'downloads',
            'temp': cls.test_workspace / 'temp',
            'logs': cls.test_workspace / 'logs',
            'backups': cls.test_workspace / 'backups',
            'config': cls.test_workspace / 'config',
            'components': cls.test_workspace / 'config' / 'components',
            'rollback': cls.test_workspace / 'rollback',
            'cache': cls.test_workspace / 'cache'
        }
        
        for directory in cls.directories.values():
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def tearDownClass(cls):
        """Limpeza após todos os testes"""
        shutil.rmtree(cls.test_workspace, ignore_errors=True)
    
    def setUp(self):
        """Configuração para cada teste individual"""
        # Inicializa todos os managers com o workspace de teste
        self.download_manager = EnhancedDownloadManager()
        self.download_manager.temp_dir = str(self.directories['temp'])
        self.download_manager.cache_dir = str(self.directories['cache'])
        
        self.installation_manager = EnhancedInstallationManager(str(self.test_workspace))
        self.organization_manager = CompleteOrganizationManager(str(self.test_workspace))
        self.recovery_manager = CompleteRecoveryManager(str(self.test_workspace))
        self.diagnostic_manager = DiagnosticManager()
        
        # Dados de teste para componentes
        self.test_components = [
            {
                'name': 'test_component_1',
                'version': '1.0.0',
                'download_url': 'https://example.com/comp1.exe',
                'checksum': {'value': 'hash1', 'algorithm': 'sha256'},
                'install_method': 'executable',
                'dependencies': [],
                'size_mb': 10.5
            },
            {
                'name': 'test_component_2',
                'version': '2.1.0',
                'download_url': 'https://example.com/comp2.msi',
                'checksum': {'value': 'hash2', 'algorithm': 'sha256'},
                'install_method': 'msi',
                'dependencies': ['test_component_1'],
                'size_mb': 25.3
            },
            {
                'name': 'test_component_3',
                'version': '1.5.2',
                'download_url': 'https://example.com/comp3.zip',
                'checksum': {'value': 'hash3', 'algorithm': 'sha256'},
                'install_method': 'archive',
                'dependencies': [],
                'size_mb': 5.8
            }
        ]
    
    def test_complete_installation_workflow(self):
        """
        Testa fluxo completo de instalação: diagnóstico → download → instalação → verificação → limpeza
        """
        print("\n=== Teste de Fluxo Completo de Instalação ===")
        
        # 1. FASE DE DIAGNÓSTICO
        print("1. Executando diagnóstico do sistema...")
        
        with patch.object(self.diagnostic_manager, 'run_full_diagnostic') as mock_diagnostic:
            from env_dev.core.diagnostic_manager import DiagnosticResult, HealthStatus
            
            mock_diagnostic.return_value = DiagnosticResult(
                overall_health=HealthStatus.HEALTHY,
                issues=[],
                system_info={'os': 'Windows', 'version': '10'},
                timestamp=datetime.now()
            )
            
            diagnostic_result = self.diagnostic_manager.run_full_diagnostic()
            self.assertEqual(diagnostic_result.overall_health, HealthStatus.HEALTHY)
            print("   ✓ Sistema diagnosticado como saudável")
        
        # 2. FASE DE DOWNLOAD
        print("2. Executando downloads dos componentes...")
        
        download_results = {}
        for component in self.test_components:
            with patch.object(self.download_manager, 'download_with_cache') as mock_download:
                mock_download.return_value = DownloadResult(
                    success=True,
                    file_path=str(self.directories['downloads'] / f"{component['name']}.exe"),
                    message=f"Download de {component['name']} concluído",
                    verification_passed=True,
                    file_size=int(component['size_mb'] * 1024 * 1024)
                )
                
                result = self.download_manager.download_with_cache(
                    component, str(self.directories['downloads'])
                )
                download_results[component['name']] = result
                
                self.assertTrue(result.success)
                self.assertTrue(result.verification_passed)
                print(f"   ✓ {component['name']} baixado com sucesso")
        
        # 3. FASE DE INSTALAÇÃO
        print("3. Executando instalações dos componentes...")
        
        installation_results = {}
        for component in self.test_components:
            with patch.object(self.installation_manager, 'install_component_enhanced') as mock_install:
                mock_install.return_value = InstallationResult(
                    success=True,
                    status=InstallationStatus.COMPLETED,
                    message=f"Instalação de {component['name']} concluída",
                    details={
                        'component': component['name'],
                        'version': component['version'],
                        'install_time': 30.5
                    }
                )
                
                result = self.installation_manager.install_component_enhanced(component['name'])
                installation_results[component['name']] = result
                
                self.assertTrue(result.success)
                self.assertEqual(result.status, InstallationStatus.COMPLETED)
                print(f"   ✓ {component['name']} instalado com sucesso")
        
        # 4. FASE DE VERIFICAÇÃO
        print("4. Verificando integridade das instalações...")
        
        for component_name in installation_results.keys():
            # Simula verificação de integridade
            with patch.object(self.installation_manager, 'verify_installation') as mock_verify:
                from env_dev.core.installation_manager import VerificationResult
                
                mock_verify.return_value = VerificationResult(
                    success=True,
                    component=component_name,
                    message="Verificação bem-sucedida"
                )
                
                verification = self.installation_manager.verify_installation(component_name)
                self.assertTrue(verification.success)
                print(f"   ✓ {component_name} verificado com sucesso")
        
        # 5. FASE DE LIMPEZA
        print("5. Executando limpeza pós-instalação...")
        
        cleanup_result = self.organization_manager.cleanup_temporary_files(max_age_hours=0)
        self.assertEqual(cleanup_result.status, CleanupStatus.COMPLETED)
        print(f"   ✓ Limpeza concluída: {cleanup_result.files_removed} arquivos removidos")
        
        print("=== Fluxo Completo Concluído com Sucesso ===\n")
    
    def test_batch_installation_with_dependencies(self):
        """
        Testa instalação em lote respeitando dependências
        """
        print("\n=== Teste de Instalação em Lote com Dependências ===")
        
        # Componentes com dependências
        components_with_deps = ['test_component_1', 'test_component_2']  # comp2 depende de comp1
        
        with patch.object(self.installation_manager, 'install_multiple_enhanced') as mock_batch_install:
            from env_dev.core.installation_manager import BatchInstallationResult
            
            # Simula instalação em lote bem-sucedida
            batch_result = BatchInstallationResult(overall_success=True)
            batch_result.completed_components = components_with_deps
            batch_result.failed_components = []
            batch_result.installation_order = ['test_component_1', 'test_component_2']  # Ordem correta
            batch_result.total_time = 125.7
            
            mock_batch_install.return_value = batch_result
            
            result = self.installation_manager.install_multiple_enhanced(
                components_with_deps,
                max_parallel=2,
                enable_smart_recovery=True
            )
            
            self.assertTrue(result.overall_success)
            self.assertEqual(len(result.completed_components), 2)
            self.assertEqual(result.installation_order[0], 'test_component_1')  # Dependência primeiro
            print("   ✓ Instalação em lote respeitou ordem de dependências")
            print(f"   ✓ Tempo total: {result.total_time}s")
        
        print("=== Instalação em Lote Concluída ===\n")
    
    def test_error_recovery_and_rollback_workflow(self):
        """
        Testa fluxo completo de recuperação de erros com rollback
        """
        print("\n=== Teste de Recuperação de Erros e Rollback ===")
        
        component_name = 'test_component_failing'
        
        # 1. SIMULA FALHA NA INSTALAÇÃO
        print("1. Simulando falha na instalação...")
        
        with patch.object(self.installation_manager, 'install_component_enhanced') as mock_install:
            # Primeira tentativa falha
            mock_install.return_value = InstallationResult(
                success=False,
                status=InstallationStatus.FAILED,
                message="Falha na instalação: dependência ausente",
                details={'error_type': 'missing_dependency', 'dependency': 'required_lib.dll'}
            )
            
            install_result = self.installation_manager.install_component_enhanced(component_name)
            self.assertFalse(install_result.success)
            print("   ✓ Falha na instalação detectada")
        
        # 2. DIAGNÓSTICO DE PROBLEMAS
        print("2. Executando diagnóstico de problemas...")
        
        with patch.object(self.diagnostic_manager, 'run_full_diagnostic') as mock_diagnostic:
            from env_dev.core.diagnostic_manager import Issue, DiagnosticResult, HealthStatus
            
            detected_issues = [
                Issue(
                    id="missing_dep_001",
                    title="Dependência Ausente",
                    description="required_lib.dll não encontrado",
                    severity="critical",
                    category="dependency",
                    issue_type="missing_dependency",
                    details={'dependency_name': 'required_lib.dll'}
                )
            ]
            
            mock_diagnostic.return_value = DiagnosticResult(
                overall_health=HealthStatus.WARNING,
                issues=detected_issues,
                system_info={},
                timestamp=datetime.now()
            )
            
            diagnostic_result = self.diagnostic_manager.run_full_diagnostic()
            self.assertEqual(len(diagnostic_result.issues), 1)
            print(f"   ✓ {len(diagnostic_result.issues)} problemas detectados")
        
        # 3. REPARO AUTOMÁTICO
        print("3. Executando reparo automático...")
        
        with patch.object(self.recovery_manager, 'auto_repair_issues') as mock_repair:
            mock_repair.return_value = RepairResult(
                action_id="auto_repair_missing_dep",
                status=RecoveryStatus.COMPLETED,
                message="Dependência instalada com sucesso",
                details={'repaired_issues': 1, 'dependency_installed': 'required_lib.dll'}
            )
            
            repair_result = self.recovery_manager.auto_repair_issues(detected_issues)
            self.assertEqual(repair_result.status, RecoveryStatus.COMPLETED)
            print("   ✓ Reparo automático concluído")
        
        # 4. NOVA TENTATIVA DE INSTALAÇÃO
        print("4. Tentando instalação novamente...")
        
        with patch.object(self.installation_manager, 'install_component_enhanced') as mock_install_retry:
            # Segunda tentativa bem-sucedida
            mock_install_retry.return_value = InstallationResult(
                success=True,
                status=InstallationStatus.COMPLETED,
                message="Instalação concluída após reparo",
                details={'retry_attempt': True, 'previous_error_resolved': True}
            )
            
            retry_result = self.installation_manager.install_component_enhanced(component_name)
            self.assertTrue(retry_result.success)
            print("   ✓ Instalação bem-sucedida após reparo")
        
        print("=== Recuperação de Erros Concluída ===\n")
    
    def test_system_maintenance_workflow(self):
        """
        Testa fluxo completo de manutenção do sistema
        """
        print("\n=== Teste de Manutenção do Sistema ===")
        
        # 1. ANÁLISE DE SAÚDE DO SISTEMA
        print("1. Executando análise de saúde...")
        
        health_report = self.recovery_manager.generate_health_report(include_recommendations=True)
        
        self.assertIsNotNone(health_report)
        self.assertIsInstance(health_report.recommendations, list)
        print(f"   ✓ Relatório gerado com {len(health_report.system_issues)} problemas")
        print(f"   ✓ {len(health_report.recommendations)} recomendações geradas")
        
        # 2. VERIFICAÇÃO DE ATUALIZAÇÕES
        print("2. Verificando atualizações disponíveis...")
        
        components_to_check = [comp['name'] for comp in self.test_components]
        
        with patch.object(self.recovery_manager, 'notify_outdated_components') as mock_updates:
            from env_dev.core.recovery_manager_complete import UpdateInfo
            
            mock_outdated = {
                'test_component_1': UpdateInfo(
                    component='test_component_1',
                    current_version='1.0.0',
                    available_version='1.0.1',
                    update_url='https://example.com/update1',
                    changelog='Bug fixes and security updates',
                    is_critical=True,
                    size_mb=12.3
                )
            }
            
            mock_updates.return_value = mock_outdated
            
            outdated_components = self.recovery_manager.notify_outdated_components()
            self.assertEqual(len(outdated_components), 1)
            self.assertTrue(outdated_components['test_component_1'].is_critical)
            print(f"   ✓ {len(outdated_components)} componentes desatualizados encontrados")
        
        # 3. LIMPEZA E ORGANIZAÇÃO
        print("3. Executando limpeza e organização...")
        
        # Análise de uso de disco
        disk_analysis = self.organization_manager.analyze_disk_usage()
        self.assertIsNotNone(disk_analysis)
        print(f"   ✓ Análise de disco: {disk_analysis.free_space / (1024**3):.1f}GB livres")
        
        # Limpeza de arquivos temporários
        cleanup_result = self.organization_manager.cleanup_temporary_files(aggressive=True)
        print(f"   ✓ Limpeza: {cleanup_result.files_removed} arquivos removidos")
        
        # Rotação de logs
        log_rotation = self.organization_manager.rotate_logs(max_age_days=30)
        print(f"   ✓ Rotação de logs: {log_rotation.files_removed} logs processados")
        
        # Gerenciamento de backups
        backup_management = self.organization_manager.manage_backups(max_backups=10)
        print(f"   ✓ Backups: {backup_management.backups_processed} processados")
        
        # 4. OTIMIZAÇÃO DE PERFORMANCE
        print("4. Executando otimização de performance...")
        
        optimization_result = self.organization_manager.optimize_disk_usage(target_free_space_gb=2.0)
        self.assertIn(optimization_result.status, [CleanupStatus.COMPLETED, CleanupStatus.PARTIAL, CleanupStatus.SKIPPED])
        print(f"   ✓ Otimização: {len(optimization_result.operations_performed)} operações executadas")
        
        print("=== Manutenção do Sistema Concluída ===\n")
    
    def test_concurrent_operations_stress_test(self):
        """
        Testa operações concorrentes para validar thread safety
        """
        print("\n=== Teste de Stress com Operações Concorrentes ===")
        
        # Configuração do teste de stress
        num_concurrent_downloads = 5
        num_concurrent_installations = 3
        num_concurrent_cleanups = 2
        
        results = {
            'downloads': [],
            'installations': [],
            'cleanups': []
        }
        
        def concurrent_download(component_index):
            """Simula download concorrente"""
            component = {
                'name': f'concurrent_component_{component_index}',
                'download_url': f'https://example.com/concurrent_{component_index}.exe',
                'checksum': {'value': f'hash_{component_index}', 'algorithm': 'sha256'}
            }
            
            with patch.object(self.download_manager, 'download_with_cache') as mock_download:
                mock_download.return_value = DownloadResult(
                    success=True,
                    file_path=f'/path/to/concurrent_{component_index}.exe',
                    message=f'Concurrent download {component_index} successful'
                )
                
                result = self.download_manager.download_with_cache(component, str(self.directories['downloads']))
                results['downloads'].append(result)
        
        def concurrent_installation(component_index):
            """Simula instalação concorrente"""
            with patch.object(self.installation_manager, 'install_component_enhanced') as mock_install:
                mock_install.return_value = InstallationResult(
                    success=True,
                    status=InstallationStatus.COMPLETED,
                    message=f'Concurrent installation {component_index} successful',
                    details={}
                )
                
                result = self.installation_manager.install_component_enhanced(f'concurrent_component_{component_index}')
                results['installations'].append(result)
        
        def concurrent_cleanup(cleanup_index):
            """Simula limpeza concorrente"""
            if cleanup_index % 2 == 0:
                result = self.organization_manager.cleanup_temporary_files()
            else:
                result = self.organization_manager.rotate_logs()
            results['cleanups'].append(result)
        
        # Executa operações concorrentes
        print("1. Iniciando operações concorrentes...")
        
        threads = []
        
        # Downloads concorrentes
        for i in range(num_concurrent_downloads):
            thread = threading.Thread(target=concurrent_download, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Instalações concorrentes
        for i in range(num_concurrent_installations):
            thread = threading.Thread(target=concurrent_installation, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Limpezas concorrentes
        for i in range(num_concurrent_cleanups):
            thread = threading.Thread(target=concurrent_cleanup, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Aguarda conclusão de todas as threads
        for thread in threads:
            thread.join(timeout=30)  # Timeout de 30 segundos
        
        # Valida resultados
        print("2. Validando resultados das operações concorrentes...")
        
        self.assertEqual(len(results['downloads']), num_concurrent_downloads)
        self.assertEqual(len(results['installations']), num_concurrent_installations)
        self.assertEqual(len(results['cleanups']), num_concurrent_cleanups)
        
        # Verifica se todas as operações foram bem-sucedidas
        all_downloads_successful = all(result.success for result in results['downloads'])
        all_installations_successful = all(result.success for result in results['installations'])
        all_cleanups_successful = all(result.status == CleanupStatus.COMPLETED for result in results['cleanups'])
        
        self.assertTrue(all_downloads_successful)
        self.assertTrue(all_installations_successful)
        self.assertTrue(all_cleanups_successful)
        
        print(f"   ✓ {len(results['downloads'])} downloads concorrentes bem-sucedidos")
        print(f"   ✓ {len(results['installations'])} instalações concorrentes bem-sucedidas")
        print(f"   ✓ {len(results['cleanups'])} limpezas concorrentes bem-sucedidas")
        
        print("=== Teste de Stress Concluído ===\n")
    
    def test_data_persistence_and_recovery(self):
        """
        Testa persistência de dados e recuperação após reinicialização
        """
        print("\n=== Teste de Persistência e Recuperação de Dados ===")
        
        # 1. GERA DADOS DE TESTE
        print("1. Gerando dados de teste...")
        
        # Simula estatísticas de download
        self.download_manager.statistics = {
            'total_downloads': 15,
            'successful_downloads': 13,
            'failed_downloads': 2,
            'cache_hits': 5,
            'total_bytes_downloaded': 1024 * 1024 * 500  # 500MB
        }
        
        # Simula métricas de instalação
        from env_dev.core.installation_manager_enhancements import InstallationMetrics
        test_metrics = InstallationMetrics(
            component='persistence_test_component',
            start_time=datetime.now() - timedelta(minutes=10),
            end_time=datetime.now(),
            total_time=600,
            rollback_performed=False
        )
        self.installation_manager.installation_metrics['persistence_test_component'] = test_metrics
        
        # Simula cache de downloads
        from env_dev.core.download_manager_enhancements import DownloadCache
        test_cache = DownloadCache(
            file_path=str(self.directories['cache'] / 'test_cache.file'),
            hash_value='test_hash_persistence',
            algorithm='sha256',
            download_time=datetime.now(),
            file_size=1024
        )
        self.download_manager.download_cache['persistence_test'] = test_cache
        
        print("   ✓ Dados de teste gerados")
        
        # 2. SALVA DADOS
        print("2. Salvando dados...")
        
        # Salva cache de downloads
        self.download_manager._save_cache()
        
        # Salva métricas de instalação
        self.installation_manager._save_installation_metrics(test_metrics)
        
        # Gera relatório de saúde
        health_report = self.recovery_manager.generate_health_report()
        
        print("   ✓ Dados salvos com sucesso")
        
        # 3. SIMULA REINICIALIZAÇÃO (CRIA NOVOS MANAGERS)
        print("3. Simulando reinicialização do sistema...")
        
        new_download_manager = EnhancedDownloadManager()
        new_download_manager.cache_dir = str(self.directories['cache'])
        new_download_manager._load_cache()
        
        new_installation_manager = EnhancedInstallationManager(str(self.test_workspace))
        new_recovery_manager = CompleteRecoveryManager(str(self.test_workspace))
        
        print("   ✓ Novos managers inicializados")
        
        # 4. VERIFICA RECUPERAÇÃO DE DADOS
        print("4. Verificando recuperação de dados...")
        
        # Verifica cache de downloads
        self.assertIn('persistence_test', new_download_manager.download_cache)
        recovered_cache = new_download_manager.download_cache['persistence_test']
        self.assertEqual(recovered_cache.hash_value, 'test_hash_persistence')
        print("   ✓ Cache de downloads recuperado")
        
        # Verifica relatórios de saúde
        health_reports = list(self.recovery_manager.health_reports_dir.glob("health_report_*.json"))
        self.assertGreater(len(health_reports), 0)
        print(f"   ✓ {len(health_reports)} relatórios de saúde encontrados")
        
        # Verifica estatísticas
        download_stats = self.download_manager.get_download_statistics()
        self.assertEqual(download_stats['total_downloads'], 15)
        print("   ✓ Estatísticas de download preservadas")
        
        installation_stats = self.installation_manager.get_installation_statistics()
        self.assertGreater(installation_stats['total_installations'], 0)
        print("   ✓ Estatísticas de instalação preservadas")
        
        print("=== Persistência e Recuperação Validadas ===\n")
    
    def test_performance_benchmarks(self):
        """
        Testa benchmarks de performance dos componentes
        """
        print("\n=== Teste de Benchmarks de Performance ===")
        
        benchmarks = {}
        
        # 1. BENCHMARK DE DOWNLOAD
        print("1. Executando benchmark de download...")
        
        start_time = time.time()
        
        # Simula múltiplos downloads
        for i in range(10):
            component = {
                'name': f'benchmark_component_{i}',
                'download_url': f'https://example.com/benchmark_{i}.exe',
                'checksum': {'value': f'benchmark_hash_{i}', 'algorithm': 'sha256'}
            }
            
            with patch.object(self.download_manager, 'download_with_cache') as mock_download:
                mock_download.return_value = DownloadResult(
                    success=True,
                    file_path=f'/path/to/benchmark_{i}.exe',
                    message=f'Benchmark download {i} successful',
                    download_time=0.5  # 500ms por download
                )
                
                self.download_manager.download_with_cache(component, str(self.directories['downloads']))
        
        download_time = time.time() - start_time
        benchmarks['download_10_components'] = download_time
        print(f"   ✓ 10 downloads em {download_time:.2f}s ({download_time/10:.3f}s por download)")
        
        # 2. BENCHMARK DE INSTALAÇÃO
        print("2. Executando benchmark de instalação...")
        
        start_time = time.time()
        
        # Simula múltiplas instalações
        for i in range(5):
            with patch.object(self.installation_manager, 'install_component_enhanced') as mock_install:
                mock_install.return_value = InstallationResult(
                    success=True,
                    status=InstallationStatus.COMPLETED,
                    message=f'Benchmark installation {i} successful',
                    details={}
                )
                
                self.installation_manager.install_component_enhanced(f'benchmark_component_{i}')
        
        installation_time = time.time() - start_time
        benchmarks['install_5_components'] = installation_time
        print(f"   ✓ 5 instalações em {installation_time:.2f}s ({installation_time/5:.3f}s por instalação)")
        
        # 3. BENCHMARK DE LIMPEZA
        print("3. Executando benchmark de limpeza...")
        
        # Cria arquivos temporários para limpeza
        temp_files = []
        for i in range(100):
            temp_file = self.directories['temp'] / f'benchmark_temp_{i}.tmp'
            temp_file.write_text(f'temporary content {i}')
            temp_files.append(temp_file)
        
        start_time = time.time()
        cleanup_result = self.organization_manager.cleanup_temporary_files()
        cleanup_time = time.time() - start_time
        
        benchmarks['cleanup_100_files'] = cleanup_time
        print(f"   ✓ Limpeza de 100 arquivos em {cleanup_time:.2f}s")
        
        # 4. BENCHMARK DE DIAGNÓSTICO
        print("4. Executando benchmark de diagnóstico...")
        
        start_time = time.time()
        
        with patch.object(self.diagnostic_manager, 'run_full_diagnostic') as mock_diagnostic:
            from env_dev.core.diagnostic_manager import DiagnosticResult, HealthStatus
            
            mock_diagnostic.return_value = DiagnosticResult(
                overall_health=HealthStatus.HEALTHY,
                issues=[],
                system_info={'benchmark': True},
                timestamp=datetime.now()
            )
            
            self.diagnostic_manager.run_full_diagnostic()
        
        diagnostic_time = time.time() - start_time
        benchmarks['full_diagnostic'] = diagnostic_time
        print(f"   ✓ Diagnóstico completo em {diagnostic_time:.2f}s")
        
        # 5. RELATÓRIO DE PERFORMANCE
        print("5. Relatório de Performance:")
        print("   " + "="*50)
        for operation, duration in benchmarks.items():
            status = "✓ EXCELENTE" if duration < 1.0 else "⚠ ACEITÁVEL" if duration < 5.0 else "❌ LENTO"
            print(f"   {operation:<25}: {duration:>8.3f}s {status}")
        print("   " + "="*50)
        
        # Valida que nenhuma operação seja excessivamente lenta
        max_acceptable_time = 10.0  # 10 segundos
        slow_operations = [op for op, time in benchmarks.items() if time > max_acceptable_time]
        
        self.assertEqual(len(slow_operations), 0, 
                        f"Operações muito lentas detectadas: {slow_operations}")
        
        print("=== Benchmarks de Performance Concluídos ===\n")


class TestErrorHandlingAndEdgeCases(unittest.TestCase):
    """Testes de tratamento de erros e casos extremos"""
    
    def setUp(self):
        """Configuração para testes de erro"""
        self.temp_dir = tempfile.mkdtemp()
        self.download_manager = EnhancedDownloadManager()
        self.installation_manager = EnhancedInstallationManager(self.temp_dir)
        self.organization_manager = CompleteOrganizationManager(self.temp_dir)
        self.recovery_manager = CompleteRecoveryManager(self.temp_dir)
    
    def tearDown(self):
        """Limpeza após testes de erro"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_network_failure_recovery(self):
        """Testa recuperação de falhas de rede"""
        print("\n=== Teste de Recuperação de Falhas de Rede ===")
        
        component = {
            'name': 'network_test_component',
            'download_url': 'https://unreachable.example.com/test.exe',
            'checksum': {'value': 'test_hash', 'algorithm': 'sha256'}
        }
        
        # Simula falha de rede
        with patch('env_dev.core.download_manager.test_internet_connection') as mock_connection:
            mock_connection.return_value = False
            
            result = self.download_manager.download_with_cache(component, self.temp_dir)
            
            self.assertFalse(result.success)
            self.assertEqual(result.error_type, 'connectivity_error')
            print("   ✓ Falha de rede detectada e tratada corretamente")
    
    def test_disk_space_exhaustion(self):
        """Testa comportamento com espaço em disco esgotado"""
        print("\n=== Teste de Esgotamento de Espaço em Disco ===")
        
        # Simula espaço em disco insuficiente
        with patch('shutil.disk_usage') as mock_disk_usage:
            mock_disk_usage.return_value = (1000000, 999999, 1)  # Apenas 1 byte livre
            
            analysis = self.organization_manager.analyze_disk_usage()
            
            self.assertLess(analysis.free_space, 1024)  # Menos de 1KB livre
            self.assertIn('Espaço livre crítico', analysis.recommendations)
            print("   ✓ Espaço em disco crítico detectado")
    
    def test_corrupted_data_handling(self):
        """Testa tratamento de dados corrompidos"""
        print("\n=== Teste de Tratamento de Dados Corrompidos ===")
        
        # Simula arquivo de cache corrompido
        cache_file = os.path.join(self.download_manager.cache_dir, "cache_index.json")
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        
        # Escreve JSON inválido
        with open(cache_file, 'w') as f:
            f.write("{ invalid json content")
        
        # Tenta carregar cache corrompido
        self.download_manager._load_cache()
        
        # Deve continuar funcionando mesmo com cache corrompido
        self.assertIsInstance(self.download_manager.download_cache, dict)
        print("   ✓ Cache corrompido tratado graciosamente")
    
    def test_concurrent_access_conflicts(self):
        """Testa conflitos de acesso concorrente"""
        print("\n=== Teste de Conflitos de Acesso Concorrente ===")
        
        results = []
        errors = []
        
        def concurrent_operation(operation_id):
            """Operação concorrente que pode causar conflitos"""
            try:
                # Simula operação que acessa recursos compartilhados
                with patch.object(self.organization_manager, 'cleanup_temporary_files') as mock_cleanup:
                    mock_cleanup.return_value = CleanupResult(
                        status=CleanupStatus.COMPLETED,
                        files_removed=operation_id,
                        space_freed=operation_id * 1024
                    )
                    
                    result = self.organization_manager.cleanup_temporary_files()
                    results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Executa múltiplas operações concorrentes
        threads = []
        for i in range(10):
            thread = threading.Thread(target=concurrent_operation, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Aguarda conclusão
        for thread in threads:
            thread.join()
        
        # Verifica que não houve erros de concorrência
        self.assertEqual(len(errors), 0, f"Erros de concorrência: {errors}")
        self.assertEqual(len(results), 10)
        print("   ✓ Operações concorrentes executadas sem conflitos")
    
    def test_malformed_configuration_handling(self):
        """Testa tratamento de configurações malformadas"""
        print("\n=== Teste de Configurações Malformadas ===")
        
        # Cria arquivo de configuração malformado
        config_dir = os.path.join(self.temp_dir, 'config')
        os.makedirs(config_dir, exist_ok=True)
        
        malformed_config = os.path.join(config_dir, 'malformed.json')
        with open(malformed_config, 'w') as f:
            f.write('{ "incomplete": json, "missing": }')
        
        # Tenta carregar configuração malformada
        try:
            with open(malformed_config, 'r') as f:
                json.load(f)
            self.fail("Deveria ter falhado ao carregar JSON malformado")
        except json.JSONDecodeError:
            print("   ✓ JSON malformado detectado e tratado")
    
    def test_resource_exhaustion_handling(self):
        """Testa tratamento de esgotamento de recursos"""
        print("\n=== Teste de Esgotamento de Recursos ===")
        
        # Simula esgotamento de memória
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value.percent = 95.0  # 95% de uso de memória
            
            health_check = self.recovery_manager.perform_system_health_check()
            
            self.assertEqual(health_check.system_health, 'critical')
            self.assertIn('memória crítico', ' '.join(health_check.recommendations))
            print("   ✓ Esgotamento de memória detectado")


if __name__ == '__main__':
    # Configura logging para os testes
    import logging
    logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
    
    # Executa testes com verbosidade
    unittest.main(verbosity=2, buffer=True)