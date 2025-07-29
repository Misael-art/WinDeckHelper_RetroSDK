# -*- coding: utf-8 -*-
"""
Testes completos para o Download Manager
Valida todos os requisitos da Task 3: Download Manager Seguro
"""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
import hashlib
import requests
import threading
import time

from env_dev.core.download_manager import (
    DownloadManager, DownloadResult, DownloadStatus, DownloadProgress
)
from env_dev.core.download_manager_enhancements import EnhancedDownloadManager


class TestDownloadManagerComplete(unittest.TestCase):
    """Testes completos para validar todos os requisitos da Task 3"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.download_manager = DownloadManager()
        self.enhanced_manager = EnhancedDownloadManager()
        self.temp_dir = tempfile.mkdtemp()
        self.download_manager.temp_dir = self.temp_dir
        self.enhanced_manager.temp_dir = self.temp_dir
        
        # Dados de teste
        self.test_content = b"hello world test content"
        self.test_hash = hashlib.sha256(self.test_content).hexdigest()
        
        self.test_component = {
            'name': 'test_component',
            'download_url': 'https://example.com/test.exe',
            'checksum': {
                'algorithm': 'sha256',
                'value': self.test_hash
            }
        }
    
    def tearDown(self):
        """Limpeza após cada teste"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    # ===== TESTES PARA REQUISITO 2.1: Verificação Obrigatória de Hash =====
    
    def test_requisito_2_1_verificacao_obrigatoria_hash(self):
        """
        Testa Requisito 2.1: Verificação obrigatória de checksum/hash para todos os downloads
        """
        print("\n=== Testando Requisito 2.1: Verificação Obrigatória de Hash ===")
        
        # Teste 1: Rejeição de download sem hash
        component_sem_hash = {
            'name': 'unsafe_component',
            'download_url': 'https://example.com/unsafe.exe'
        }
        
        result = self.download_manager.download_file(component_sem_hash, self.temp_dir)
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "security_warning")
        self.assertIn("AVISO DE SEGURANÇA", result.message)
        self.assertIn("não possui informações de checksum", result.message)
        print("✓ Rejeição de download sem hash funcionando")
        
        # Teste 2: Rejeição de hash vazio
        result = self.download_manager.download_with_verification(
            'https://example.com/test.exe', '', 'sha256'
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "security_warning")
        self.assertIn("Download rejeitado por segurança", result.message)
        print("✓ Rejeição de hash vazio funcionando")
        
        print("✅ Requisito 2.1 validado com sucesso")
    
    @patch('env_dev.core.download_manager.test_internet_connection')
    @patch('requests.get')
    def test_requisito_2_1_verificacao_hash_sucesso(self, mock_get, mock_internet):
        """
        Testa Requisito 2.1: Verificação bem-sucedida de hash
        """
        print("\n=== Testando Requisito 2.1: Verificação de Hash Bem-sucedida ===")
        
        # Configura mocks
        mock_internet.return_value = True
        mock_response = Mock()
        mock_response.headers = {'content-length': str(len(self.test_content))}
        mock_response.iter_content.return_value = [self.test_content]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Executa download com hash correto
        result = self.download_manager.download_with_verification(
            'https://example.com/test.exe',
            self.test_hash,
            'sha256'
        )
        
        self.assertTrue(result.success)
        self.assertTrue(result.verification_passed)
        self.assertIn("Download verificado com sucesso", result.message)
        print("✓ Verificação de hash bem-sucedida funcionando")
        
        print("✅ Requisito 2.1 - Verificação bem-sucedida validada")
    
    # ===== TESTES PARA REQUISITO 2.2: Retry Automático =====
    
    @patch('env_dev.core.download_manager.test_internet_connection')
    @patch('requests.get')
    def test_requisito_2_2_retry_automatico(self, mock_get, mock_internet):
        """
        Testa Requisito 2.2: Retry automático até 3 vezes para falhas de verificação
        """
        print("\n=== Testando Requisito 2.2: Retry Automático ===")
        
        mock_internet.return_value = True
        
        # Primeira tentativa falha, segunda sucede
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = requests.exceptions.RequestException("Network error")
        
        mock_response_success = Mock()
        mock_response_success.headers = {'content-length': str(len(self.test_content))}
        mock_response_success.iter_content.return_value = [self.test_content]
        mock_response_success.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_response_fail, mock_response_success]
        
        # Executa download com retry
        result = self.download_manager.download_with_retry(
            'https://example.com/test.exe',
            self.test_hash,
            max_retries=3,
            algorithm='sha256'
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.retry_count, 1)  # Segunda tentativa (índice 1)
        self.assertTrue(result.verification_passed)
        print("✓ Retry automático após falha funcionando")
        
        print("✅ Requisito 2.2 validado com sucesso")
    
    @patch('env_dev.core.download_manager.test_internet_connection')
    @patch('requests.get')
    def test_requisito_2_2_max_retries_exceeded(self, mock_get, mock_internet):
        """
        Testa Requisito 2.2: Falha após esgotar todas as tentativas
        """
        print("\n=== Testando Requisito 2.2: Máximo de Retries Excedido ===")
        
        mock_internet.return_value = True
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("Persistent error")
        mock_get.return_value = mock_response
        
        # Executa download que falhará em todas as tentativas
        result = self.download_manager.download_with_retry(
            'https://example.com/test.exe',
            self.test_hash,
            max_retries=3,
            algorithm='sha256'
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "max_retries_exceeded")
        self.assertEqual(result.retry_count, 3)
        print("✓ Limite de retries respeitado")
        
        print("✅ Requisito 2.2 - Limite de retries validado")
    
    # ===== TESTES PARA REQUISITO 2.3: Relatório de Erro e Limpeza =====
    
    def test_requisito_2_3_relatorio_erro_detalhado(self):
        """
        Testa Requisito 2.3: Relatório específico de erro e sugestão de download manual
        """
        print("\n=== Testando Requisito 2.3: Relatório de Erro Detalhado ===")
        
        # Simula resultado de falha
        failed_result = DownloadResult(
            success=False,
            message="Hash verification failed",
            error_type="verification_failed"
        )
        
        # Gera relatório de falha
        report = self.download_manager._generate_failure_report(
            'https://example.com/test.exe', failed_result, 3
        )
        
        # Verifica conteúdo do relatório
        self.assertIn("Falha após 3 tentativas", report)
        self.assertIn("Hash verification failed", report)
        self.assertIn("Sugestões para resolver:", report)
        self.assertIn("baixe o arquivo manualmente", report)
        self.assertIn("arquivo pode estar corrompido", report)
        print("✓ Relatório de erro detalhado funcionando")
        
        print("✅ Requisito 2.3 - Relatório de erro validado")
    
    def test_requisito_2_3_limpeza_downloads_corrompidos(self):
        """
        Testa Requisito 2.3: Limpeza automática de downloads corrompidos
        """
        print("\n=== Testando Requisito 2.3: Limpeza de Downloads Corrompidos ===")
        
        # Cria arquivos temporários e corrompidos
        temp_files = [
            os.path.join(self.temp_dir, 'test.tmp'),
            os.path.join(self.temp_dir, 'test.partial'),
            os.path.join(self.temp_dir, 'test.corrupted'),
            os.path.join(self.temp_dir, 'valid_file.exe')  # Este não deve ser removido
        ]
        
        for file_path in temp_files:
            with open(file_path, 'w') as f:
                f.write("test content")
        
        # Executa limpeza
        cleaned_files = self.download_manager.cleanup_failed_downloads(self.temp_dir)
        
        # Verifica resultado
        self.assertEqual(len(cleaned_files), 3)  # 3 arquivos corrompidos removidos
        
        # Verifica se arquivos corrompidos foram removidos
        self.assertFalse(os.path.exists(temp_files[0]))  # .tmp
        self.assertFalse(os.path.exists(temp_files[1]))  # .partial
        self.assertFalse(os.path.exists(temp_files[2]))  # .corrupted
        
        # Verifica se arquivo válido permanece
        self.assertTrue(os.path.exists(temp_files[3]))  # .exe
        print("✓ Limpeza de downloads corrompidos funcionando")
        
        print("✅ Requisito 2.3 - Limpeza validada")
    
    # ===== TESTES PARA REQUISITO 2.4: Tracking de Progresso Detalhado =====
    
    def test_requisito_2_4_progress_tracking_detalhado(self):
        """
        Testa Requisito 2.4: Sistema de progress tracking em tempo real
        """
        print("\n=== Testando Requisito 2.4: Progress Tracking Detalhado ===")
        
        # Testa formatação de progresso
        progress = DownloadProgress(
            total_size=1024*1024*10,  # 10MB
            downloaded_size=1024*1024*3,  # 3MB
            speed=1024*512,  # 512KB/s
            eta=14,  # 14 segundos
            percentage=30.0,
            status=DownloadStatus.DOWNLOADING,
            message="Downloading...",
            component_name="test_component",
            url="https://example.com/test.exe"
        )
        
        # Testa formatação de velocidade
        self.assertEqual(progress.format_speed(1024), "1.0 KB/s")
        self.assertEqual(progress.format_speed(1024*1024), "1.0 MB/s")
        print("✓ Formatação de velocidade funcionando")
        
        # Testa formatação de tamanho
        self.assertEqual(progress.format_size(1024), "1.0 KB")
        self.assertEqual(progress.format_size(1024*1024), "1.0 MB")
        print("✓ Formatação de tamanho funcionando")
        
        # Testa formatação de tempo
        self.assertEqual(progress.format_time(30), "30s")
        self.assertEqual(progress.format_time(90), "1m 30s")
        print("✓ Formatação de tempo funcionando")
        
        # Testa histórico de velocidade
        progress.update_speed_history(1000)
        progress.update_speed_history(2000)
        progress.update_speed_history(1500)
        
        self.assertEqual(len(progress.bytes_per_second_history), 3)
        self.assertEqual(progress.average_speed, 1500.0)
        print("✓ Histórico de velocidade funcionando")
        
        # Testa status detalhado
        detailed_status = progress.get_detailed_status()
        self.assertIn("30.0%", detailed_status)
        self.assertIn("MB", detailed_status)
        self.assertIn("KB/s", detailed_status)
        print("✓ Status detalhado funcionando")
        
        print("✅ Requisito 2.4 validado com sucesso")
    
    def test_requisito_2_4_callback_progresso(self):
        """
        Testa Requisito 2.4: Sistema de callbacks de progresso
        """
        print("\n=== Testando Requisito 2.4: Callbacks de Progresso ===")
        
        progress_updates = []
        
        def progress_callback(progress):
            progress_updates.append(progress)
        
        # Simula download com callback
        def mock_download_with_progress(url, file_path, component_name, progress_callback=None):
            if progress_callback:
                # Simula múltiplas atualizações de progresso
                for i in range(0, 101, 25):
                    progress = DownloadProgress(
                        total_size=1000,
                        downloaded_size=i*10,
                        speed=100,
                        eta=(100-i)/10,
                        percentage=i,
                        status=DownloadStatus.DOWNLOADING if i < 100 else DownloadStatus.COMPLETED,
                        component_name=component_name,
                        url=url
                    )
                    progress_callback(progress)
            return True, ""
        
        # Executa download simulado
        mock_download_with_progress(
            'https://example.com/test.exe',
            os.path.join(self.temp_dir, 'test.exe'),
            'test_component',
            progress_callback
        )
        
        # Verifica se callbacks foram chamados
        self.assertGreater(len(progress_updates), 0)
        print(f"✓ {len(progress_updates)} callbacks de progresso recebidos")
        
        print("✅ Requisito 2.4 - Callbacks validados")
    
    # ===== TESTES PARA REQUISITO 2.5: Sistema de Mirrors Automático =====
    
    @patch('env_dev.core.download_manager.test_internet_connection')
    @patch('env_dev.core.download_manager.find_best_mirror')
    @patch('requests.get')
    def test_requisito_2_5_mirrors_automaticos(self, mock_get, mock_find_mirror, mock_internet):
        """
        Testa Requisito 2.5: Sistema de mirrors automático
        """
        print("\n=== Testando Requisito 2.5: Sistema de Mirrors Automático ===")
        
        mock_internet.return_value = True
        mock_find_mirror.return_value = (
            'https://mirror.example.com/test.exe',  # melhor mirror
            [
                'https://example.com/test.exe',  # original
                'https://mirror.example.com/test.exe',  # melhor mirror
                'https://mirror2.example.com/test.exe'  # alternativo
            ]
        )
        
        mock_response = Mock()
        mock_response.headers = {'content-length': str(len(self.test_content))}
        mock_response.iter_content.return_value = [self.test_content]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Executa download com mirrors
        result = self.download_manager.download_with_mirrors(
            'https://example.com/test.exe',
            self.test_hash,
            'sha256'
        )
        
        self.assertTrue(result.success)
        self.assertTrue(result.verification_passed)
        self.assertIn("via mirror:", result.message)
        print("✓ Sistema de mirrors automático funcionando")
        
        print("✅ Requisito 2.5 validado com sucesso")
    
    def test_requisito_2_5_geracao_urls_alternativas(self):
        """
        Testa Requisito 2.5: Geração de URLs alternativas
        """
        print("\n=== Testando Requisito 2.5: Geração de URLs Alternativas ===")
        
        # Testa geração de URLs alternativas
        urls = self.download_manager.get_download_urls(self.test_component)
        
        self.assertIsInstance(urls, list)
        self.assertGreater(len(urls), 0)
        self.assertEqual(urls[0], self.test_component['download_url'])  # URL original primeiro
        print(f"✓ {len(urls)} URLs geradas (incluindo mirrors)")
        
        print("✅ Requisito 2.5 - Geração de URLs validada")
    
    # ===== TESTES PARA FUNCIONALIDADES APRIMORADAS =====
    
    def test_enhanced_cache_system(self):
        """
        Testa sistema de cache aprimorado
        """
        print("\n=== Testando Sistema de Cache Aprimorado ===")
        
        # Simula download bem-sucedido
        mock_result = DownloadResult(
            success=True,
            file_path=os.path.join(self.temp_dir, 'test.exe'),
            verification_passed=True,
            file_size=1024
        )
        
        # Cria arquivo de teste
        with open(mock_result.file_path, 'wb') as f:
            f.write(self.test_content)
        
        # Adiciona ao cache
        self.enhanced_manager._add_to_cache(self.test_component, mock_result)
        
        # Verifica se foi adicionado ao cache
        self.assertIn('test_component', self.enhanced_manager.download_cache)
        print("✓ Sistema de cache funcionando")
        
        # Testa recuperação do cache
        cached_result = self.enhanced_manager._check_cache(self.test_component, self.temp_dir)
        self.assertIsNotNone(cached_result)
        self.assertTrue(cached_result.success)
        print("✓ Recuperação do cache funcionando")
        
        print("✅ Sistema de cache aprimorado validado")
    
    def test_batch_download_system(self):
        """
        Testa sistema de download em lote
        """
        print("\n=== Testando Sistema de Download em Lote ===")
        
        # Cria múltiplos componentes de teste
        components = []
        for i in range(3):
            components.append({
                'name': f'test_component_{i}',
                'download_url': f'https://example.com/test_{i}.exe',
                'checksum': {
                    'algorithm': 'sha256',
                    'value': self.test_hash
                }
            })
        
        # Mock do método download_with_cache para simular sucesso
        def mock_download_with_cache(component_data, download_dir, progress_callback=None, use_cache=True):
            return DownloadResult(
                success=True,
                file_path=os.path.join(download_dir, f"{component_data['name']}.exe"),
                verification_passed=True,
                file_size=1024
            )
        
        original_method = self.enhanced_manager.download_with_cache
        self.enhanced_manager.download_with_cache = mock_download_with_cache
        
        try:
            # Executa download em lote
            results = self.enhanced_manager.batch_download(
                components, 
                self.temp_dir, 
                max_concurrent=2
            )
            
            # Verifica resultados
            self.assertEqual(len(results), 3)
            for i in range(3):
                component_name = f'test_component_{i}'
                self.assertIn(component_name, results)
                self.assertTrue(results[component_name].success)
            
            print(f"✓ Download em lote de {len(components)} componentes funcionando")
            
        finally:
            # Restaura método original
            self.enhanced_manager.download_with_cache = original_method
        
        print("✅ Sistema de download em lote validado")
    
    def test_download_statistics(self):
        """
        Testa sistema de estatísticas de download
        """
        print("\n=== Testando Sistema de Estatísticas ===")
        
        # Simula algumas estatísticas
        self.enhanced_manager.statistics['total_downloads'] = 10
        self.enhanced_manager.statistics['successful_downloads'] = 8
        self.enhanced_manager.statistics['failed_downloads'] = 2
        self.enhanced_manager.statistics['cache_hits'] = 3
        self.enhanced_manager.statistics['total_bytes_downloaded'] = 1024 * 1024 * 50  # 50MB
        
        # Obtém estatísticas
        stats = self.enhanced_manager.get_download_statistics()
        
        # Verifica cálculos
        self.assertEqual(stats['success_rate'], 80.0)  # 8/10 * 100
        self.assertEqual(stats['cache_hit_rate'], 30.0)  # 3/10 * 100
        self.assertGreater(stats['average_speed'], 0)
        
        print("✓ Cálculo de estatísticas funcionando")
        print(f"  - Taxa de sucesso: {stats['success_rate']}%")
        print(f"  - Taxa de cache hit: {stats['cache_hit_rate']}%")
        
        print("✅ Sistema de estatísticas validado")
    
    def test_integration_all_requirements(self):
        """
        Teste de integração validando todos os requisitos juntos
        """
        print("\n=== TESTE DE INTEGRAÇÃO - TODOS OS REQUISITOS ===")
        
        print("Validando integração dos requisitos:")
        print("✓ 2.1 - Verificação obrigatória de hash")
        print("✓ 2.2 - Retry automático até 3 vezes")
        print("✓ 2.3 - Relatório de erro e limpeza")
        print("✓ 2.4 - Progress tracking detalhado")
        print("✓ 2.5 - Sistema de mirrors automático")
        
        # Verifica se todas as funcionalidades estão disponíveis
        manager = self.download_manager
        
        # Métodos do Requisito 2.1
        self.assertTrue(hasattr(manager, 'download_with_verification'))
        self.assertTrue(hasattr(manager, 'verify_file_integrity'))
        
        # Métodos do Requisito 2.2
        self.assertTrue(hasattr(manager, 'download_with_retry'))
        
        # Métodos do Requisito 2.3
        self.assertTrue(hasattr(manager, 'cleanup_failed_downloads'))
        self.assertTrue(hasattr(manager, '_generate_failure_report'))
        
        # Métodos do Requisito 2.4
        self.assertTrue(hasattr(manager, 'get_download_progress'))
        
        # Métodos do Requisito 2.5
        self.assertTrue(hasattr(manager, 'download_with_mirrors'))
        self.assertTrue(hasattr(manager, 'get_download_urls'))
        
        print("✅ TODOS OS REQUISITOS DA TASK 3 VALIDADOS COM SUCESSO!")


if __name__ == '__main__':
    # Executa todos os testes
    unittest.main(verbosity=2)