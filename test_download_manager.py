# -*- coding: utf-8 -*-
"""
Testes para o DownloadManager
Verifica implementação dos requisitos 2.1, 2.2 e 2.3
"""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
import hashlib
import requests

from env_dev.core.download_manager import (
    DownloadManager, DownloadResult, DownloadStatus, DownloadProgress
)


class TestDownloadManager(unittest.TestCase):
    """Testes para o DownloadManager"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.download_manager = DownloadManager()
        self.temp_dir = tempfile.mkdtemp()
        self.download_manager.temp_dir = self.temp_dir
        
        # Dados de componente de teste
        self.test_component = {
            'name': 'test_component',
            'download_url': 'https://example.com/test.exe',
            'checksum': {
                'algorithm': 'sha256',
                'value': 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3'  # hash de "hello"
            }
        }
        
        # Conteúdo de teste
        self.test_content = b"hello"
        self.test_hash = hashlib.sha256(self.test_content).hexdigest()
    
    def tearDown(self):
        """Limpeza após cada teste"""
        # Remove arquivos temporários
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('env_dev.core.download_manager.test_internet_connection')
    @patch('requests.get')
    def test_download_with_verification_success(self, mock_get, mock_internet):
        """
        Testa download com verificação bem-sucedida (Requisito 2.1)
        """
        # Configura mocks
        mock_internet.return_value = True
        mock_response = Mock()
        mock_response.headers = {'content-length': str(len(self.test_content))}
        mock_response.iter_content.return_value = [self.test_content]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Executa download
        result = self.download_manager.download_with_verification(
            'https://example.com/test.exe',
            self.test_hash,
            'sha256'
        )
        
        # Verifica resultado
        self.assertTrue(result.success)
        self.assertTrue(result.verification_passed)
        self.assertIn("Download verificado com sucesso", result.message)
        self.assertEqual(result.error_type, None)
        self.assertTrue(os.path.exists(result.file_path))
    
    @patch('env_dev.core.download_manager.test_internet_connection')
    @patch('requests.get')
    def test_download_with_verification_hash_failure(self, mock_get, mock_internet):
        """
        Testa falha na verificação de hash (Requisito 2.1)
        """
        # Configura mocks
        mock_internet.return_value = True
        mock_response = Mock()
        mock_response.headers = {'content-length': str(len(self.test_content))}
        mock_response.iter_content.return_value = [self.test_content]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Hash incorreto
        wrong_hash = "wrong_hash_value"
        
        # Executa download
        result = self.download_manager.download_with_verification(
            'https://example.com/test.exe',
            wrong_hash,
            'sha256'
        )
        
        # Verifica resultado
        self.assertFalse(result.success)
        self.assertFalse(result.verification_passed)
        self.assertEqual(result.error_type, "verification_failed")
        self.assertIn("Falha na verificação de integridade", result.message)
        self.assertIn(wrong_hash, result.message)
        self.assertIn(self.test_hash, result.message)
    
    def test_download_with_verification_no_hash(self):
        """
        Testa rejeição de download sem hash (Requisito 2.1)
        """
        result = self.download_manager.download_with_verification(
            'https://example.com/test.exe',
            '',  # Hash vazio
            'sha256'
        )
        
        # Verifica resultado
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "security_warning")
        self.assertIn("AVISO DE SEGURANÇA", result.message)
        self.assertIn("Download rejeitado por segurança", result.message)
    
    @patch('env_dev.core.download_manager.test_internet_connection')
    @patch('requests.get')
    def test_download_with_retry_success_after_failure(self, mock_get, mock_internet):
        """
        Testa retry automático após falha (Requisito 2.2)
        """
        # Configura mocks
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
        
        # Verifica resultado
        self.assertTrue(result.success)
        self.assertEqual(result.retry_count, 1)  # Segunda tentativa (índice 1)
        self.assertTrue(result.verification_passed)
    
    @patch('env_dev.core.download_manager.test_internet_connection')
    @patch('requests.get')
    def test_download_with_retry_max_retries_exceeded(self, mock_get, mock_internet):
        """
        Testa falha após esgotar todas as tentativas (Requisito 2.3)
        """
        # Configura mocks
        mock_internet.return_value = True
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("Network error")
        mock_get.return_value = mock_response
        
        # Executa download com retry
        result = self.download_manager.download_with_retry(
            'https://example.com/test.exe',
            self.test_hash,
            max_retries=3,
            algorithm='sha256'
        )
        
        # Verifica resultado
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "max_retries_exceeded")
        self.assertEqual(result.retry_count, 3)
        
        # Verifica se o relatório de falha contém sugestões (Requisito 2.3)
        self.assertIn("Falha após 3 tentativas", result.message)
        self.assertIn("Sugestões para resolver:", result.message)
        self.assertIn("baixe o arquivo manualmente", result.message)
    
    @patch('env_dev.core.download_manager.test_internet_connection')
    def test_download_file_no_checksum_security_warning(self, mock_internet):
        """
        Testa aviso de segurança para componente sem checksum (Requisito 2.1)
        """
        mock_internet.return_value = True
        
        # Componente sem checksum
        component_without_checksum = {
            'name': 'unsafe_component',
            'download_url': 'https://example.com/unsafe.exe'
        }
        
        result = self.download_manager.download_file(
            component_without_checksum,
            self.temp_dir
        )
        
        # Verifica resultado
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "security_warning")
        self.assertIn("AVISO DE SEGURANÇA", result.message)
        self.assertIn("não possui informações de checksum", result.message)
    
    def test_cleanup_failed_downloads(self):
        """
        Testa limpeza de downloads corrompidos (Requisito 2.3)
        """
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
    
    def test_verify_file_integrity(self):
        """
        Testa verificação de integridade de arquivo existente
        """
        # Cria arquivo de teste
        test_file = os.path.join(self.temp_dir, 'test.txt')
        with open(test_file, 'wb') as f:
            f.write(self.test_content)
        
        # Testa verificação com hash correto
        result = self.download_manager.verify_file_integrity(
            test_file, self.test_hash, 'sha256'
        )
        self.assertTrue(result)
        
        # Testa verificação com hash incorreto
        result = self.download_manager.verify_file_integrity(
            test_file, 'wrong_hash', 'sha256'
        )
        self.assertFalse(result)
        
        # Testa verificação de arquivo inexistente
        result = self.download_manager.verify_file_integrity(
            'nonexistent.txt', self.test_hash, 'sha256'
        )
        self.assertFalse(result)
    
    def test_calculate_file_hash(self):
        """
        Testa cálculo de hash de arquivo
        """
        # Cria arquivo de teste
        test_file = os.path.join(self.temp_dir, 'test.txt')
        with open(test_file, 'wb') as f:
            f.write(self.test_content)
        
        # Testa diferentes algoritmos
        sha256_hash = self.download_manager._calculate_file_hash(test_file, 'sha256')
        self.assertEqual(sha256_hash, self.test_hash)
        
        md5_hash = self.download_manager._calculate_file_hash(test_file, 'md5')
        expected_md5 = hashlib.md5(self.test_content).hexdigest()
        self.assertEqual(md5_hash, expected_md5)
        
        # Testa algoritmo não suportado
        with self.assertRaises(ValueError):
            self.download_manager._calculate_file_hash(test_file, 'unsupported')
    
    def test_generate_failure_report(self):
        """
        Testa geração de relatório de falha detalhado (Requisito 2.3)
        """
        # Testa relatório para falha de verificação
        result = DownloadResult(
            success=False,
            message="Hash mismatch",
            error_type="verification_failed"
        )
        
        report = self.download_manager._generate_failure_report(
            'https://example.com/test.exe', result, 3
        )
        
        # Verifica conteúdo do relatório
        self.assertIn("Falha após 3 tentativas", report)
        self.assertIn("Hash mismatch", report)
        self.assertIn("arquivo pode estar corrompido", report)
        self.assertIn("baixe o arquivo manualmente", report)
        
        # Testa relatório para erro de conectividade
        result.error_type = "connectivity_error"
        report = self.download_manager._generate_failure_report(
            'https://example.com/test.exe', result, 3
        )
        
        self.assertIn("conexão com a internet", report)
        self.assertIn("proxy/firewall", report)
    
    @patch('env_dev.core.download_manager.test_internet_connection')
    @patch('env_dev.core.download_manager.find_best_mirror')
    @patch('requests.get')
    def test_download_with_mirrors_success(self, mock_get, mock_find_mirror, mock_internet):
        """
        Testa download bem-sucedido usando sistema de mirrors (Requisito 2.5)
        """
        # Configura mocks
        mock_internet.return_value = True
        mock_find_mirror.return_value = (
            'https://mirror.example.com/test.exe',  # melhor mirror
            ['https://example.com/test.exe', 'https://mirror.example.com/test.exe']  # todas as URLs
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
        
        # Verifica resultado
        self.assertTrue(result.success)
        self.assertTrue(result.verification_passed)
        self.assertIn("via mirror:", result.message)
        self.assertIn("mirror.example.com", result.message)
    
    @patch('env_dev.core.download_manager.test_internet_connection')
    @patch('env_dev.core.download_manager.find_best_mirror')
    def test_download_with_mirrors_connectivity_error(self, mock_find_mirror, mock_internet):
        """
        Testa tratamento de erro de conectividade no sistema de mirrors (Requisito 2.5)
        """
        # Configura mocks
        mock_internet.return_value = False
        
        # Executa download com mirrors
        result = self.download_manager.download_with_mirrors(
            'https://example.com/test.exe',
            self.test_hash,
            'sha256'
        )
        
        # Verifica resultado
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "connectivity_error")
        self.assertIn("Sem conexão com a internet", result.message)
        
        # Verifica que find_best_mirror não foi chamado
        mock_find_mirror.assert_not_called()
    
    @patch('env_dev.core.download_manager.test_internet_connection')
    @patch('env_dev.core.download_manager.find_best_mirror')
    @patch('requests.get')
    def test_download_with_mirrors_fallback_to_alternatives(self, mock_get, mock_find_mirror, mock_internet):
        """
        Testa fallback para mirrors alternativos quando o melhor falha (Requisito 2.5)
        """
        # Configura mocks
        mock_internet.return_value = True
        mock_find_mirror.return_value = (
            'https://mirror1.example.com/test.exe',  # melhor mirror (vai falhar)
            [
                'https://example.com/test.exe',  # original
                'https://mirror1.example.com/test.exe',  # melhor (falha)
                'https://mirror2.example.com/test.exe'   # alternativo (sucesso)
            ]
        )
        
        # Primeira tentativa (melhor mirror) falha, segunda (alternativo) sucede
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = requests.exceptions.RequestException("Mirror error")
        
        mock_response_success = Mock()
        mock_response_success.headers = {'content-length': str(len(self.test_content))}
        mock_response_success.iter_content.return_value = [self.test_content]
        mock_response_success.raise_for_status.return_value = None
        
        # Configura sequência de respostas: falha no melhor mirror, sucesso no alternativo
        # O download_with_retry faz 3 tentativas para cada URL
        mock_get.side_effect = [
            # Tentativas com o melhor mirror (todas falham)
            mock_response_fail,  # Tentativa 1
            mock_response_fail,  # Tentativa 2  
            mock_response_fail,  # Tentativa 3
            # Tentativas com URL original (todas falham)
            mock_response_fail,  # Tentativa 1
            mock_response_fail,  # Tentativa 2
            mock_response_fail,  # Tentativa 3
            # Tentativas com mirror alternativo (sucesso na primeira)
            mock_response_success,  # Sucesso
        ]
        
        # Executa download com mirrors
        result = self.download_manager.download_with_mirrors(
            'https://example.com/test.exe',
            self.test_hash,
            'sha256'
        )
        
        # Verifica resultado
        self.assertTrue(result.success)
        self.assertTrue(result.verification_passed)
        self.assertIn("via mirror alternativo:", result.message)
        self.assertIn("mirror2.example.com", result.message)
    
    @patch('env_dev.core.download_manager.check_url_availability')
    def test_check_connectivity_and_mirrors(self, mock_check_availability):
        """
        Testa verificação de conectividade e disponibilidade de mirrors
        """
        # Configura mock para simular disponibilidade
        def mock_availability(url, timeout=5):
            if "mirror1" in url:
                return True
            elif "mirror2" in url:
                return False
            else:
                return True  # URL original
        
        mock_check_availability.side_effect = mock_availability
        
        # Configura mirrors config mock
        self.download_manager.mirrors_config = {
            'example.com': [
                'https://example.com',
                'https://mirror1.example.com',
                'https://mirror2.example.com'
            ]
        }
        
        # Executa verificação
        connectivity_status = self.download_manager.check_connectivity_and_mirrors(
            'https://example.com/test.exe'
        )
        
        # Verifica resultado
        self.assertIsInstance(connectivity_status, dict)
        self.assertTrue(len(connectivity_status) > 0)
        
        # Verifica se URLs foram testadas
        mock_check_availability.assert_called()
        self.assertGreater(mock_check_availability.call_count, 0)
    
    @patch('env_dev.core.download_manager.test_internet_connection')
    @patch('env_dev.core.download_manager.generate_alternative_urls')
    def test_get_download_urls_with_mirrors(self, mock_generate_urls, mock_internet):
        """
        Testa geração de URLs de download com mirrors automáticos (Requisito 2.5)
        """
        mock_internet.return_value = True
        mock_generate_urls.return_value = [
            'https://example.com/test.exe',
            'https://mirror1.example.com/test.exe',
            'https://mirror2.example.com/test.exe'
        ]
        
        # Dados do componente com URL principal
        component_data = {
            'name': 'test_component',
            'download_url': 'https://example.com/test.exe',
            'mirror_urls': ['https://manual-mirror.com/test.exe']
        }
        
        # Obtém URLs de download
        urls = self.download_manager.get_download_urls(component_data)
        
        # Verifica resultado
        self.assertIsInstance(urls, list)
        self.assertGreater(len(urls), 1)  # Deve ter mais que apenas a URL original
        self.assertEqual(urls[0], 'https://example.com/test.exe')  # URL original primeiro
        self.assertIn('https://manual-mirror.com/test.exe', urls)  # Mirror manual incluído
        
        # Verifica que generate_alternative_urls foi chamado
        mock_generate_urls.assert_called_once()
    
    @patch('env_dev.core.download_manager.test_internet_connection')
    def test_download_file_with_mirrors_integration(self, mock_internet):
        """
        Testa integração completa do download_file com sistema de mirrors (Requisito 2.5)
        """
        mock_internet.return_value = True
        
        # Componente com checksum válido
        component_with_checksum = {
            'name': 'test_component',
            'download_url': 'https://example.com/test.exe',
            'checksum': {
                'algorithm': 'sha256',
                'value': self.test_hash
            }
        }
        
        # Mock do método download_with_mirrors para simular sucesso
        original_method = self.download_manager.download_with_mirrors
        def mock_download_with_mirrors(url, expected_hash, algorithm='sha256'):
            # Simula sucesso com mirror
            return DownloadResult(
                success=True,
                file_path=os.path.join(self.temp_dir, 'test.exe'),
                message="Download verificado com sucesso (SHA256) (via mirror: https://mirror.example.com/test.exe)",
                verification_passed=True
            )
        
        self.download_manager.download_with_mirrors = mock_download_with_mirrors
        
        try:
            # Executa download
            result = self.download_manager.download_file(
                component_with_checksum,
                self.temp_dir
            )
            
            # Verifica resultado
            self.assertTrue(result.success)
            self.assertTrue(result.verification_passed)
            self.assertIn("via mirror:", result.message)
            
        finally:
            # Restaura método original
            self.download_manager.download_with_mirrors = original_method
    
    def test_enhanced_download_progress_formatting(self):
        """
        Testa formatação aprimorada do DownloadProgress (Requisito 2.4)
        """
        from datetime import datetime
        
        # Cria progresso com dados detalhados
        progress = DownloadProgress(
            total_size=1024*1024*10,  # 10MB
            downloaded_size=1024*1024*3,  # 3MB
            speed=1024*512,  # 512KB/s
            eta=14,  # 14 segundos
            percentage=30.0,
            status=DownloadStatus.DOWNLOADING,
            message="Downloading...",
            start_time=datetime.now(),
            component_name="test_component",
            url="https://example.com/test.exe"
        )
        
        # Testa formatação de velocidade
        self.assertEqual(progress.format_speed(1024), "1.0 KB/s")
        self.assertEqual(progress.format_speed(1024*1024), "1.0 MB/s")
        self.assertEqual(progress.format_speed(512), "512.0 B/s")
        
        # Testa formatação de tamanho
        self.assertEqual(progress.format_size(1024), "1.0 KB")
        self.assertEqual(progress.format_size(1024*1024), "1.0 MB")
        self.assertEqual(progress.format_size(512), "512 B")
        
        # Testa formatação de tempo
        self.assertEqual(progress.format_time(30), "30s")
        self.assertEqual(progress.format_time(90), "1m 30s")
        self.assertEqual(progress.format_time(3661), "1h 1m")
        
        # Testa atualização de histórico de velocidade
        progress.update_speed_history(1000)
        progress.update_speed_history(2000)
        progress.update_speed_history(1500)
        
        self.assertEqual(len(progress.bytes_per_second_history), 3)
        self.assertEqual(progress.average_speed, 1500.0)  # (1000+2000+1500)/3
        
        # Testa status detalhado
        detailed_status = progress.get_detailed_status()
        self.assertIn("30.0%", detailed_status)
        self.assertIn("MB", detailed_status)
        self.assertIn("KB/s", detailed_status)
        self.assertIn("ETA:", detailed_status)
    
    def test_progress_tracking_callbacks(self):
        """
        Testa sistema de callbacks de progresso (Requisito 2.4)
        """
        progress_updates = []
        
        def progress_callback(progress):
            progress_updates.append(progress)
        
        # Simula download com callback
        component_data = {
            'name': 'test_component',
            'download_url': 'https://example.com/test.exe',
            'checksum': {
                'algorithm': 'sha256',
                'value': self.test_hash
            }
        }
        
        # Mock do método _download_from_url para simular progresso
        original_method = self.download_manager._download_from_url
        def mock_download_from_url(url, file_path, component_name, progress_callback=None):
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
        
        self.download_manager._download_from_url = mock_download_from_url
        
        try:
            # Executa download com callback diretamente no método _download_from_url
            success, error = self.download_manager._download_from_url(
                'https://example.com/test.exe',
                os.path.join(self.temp_dir, 'test.exe'),
                'test_component',
                progress_callback
            )
            
            # Verifica se callbacks foram chamados
            self.assertGreater(len(progress_updates), 0)
            
            # Verifica se progresso foi atualizado corretamente
            first_progress = progress_updates[0]
            self.assertEqual(first_progress.component_name, "test.exe")
            self.assertEqual(first_progress.url, "https://example.com/test.exe")
            
        finally:
            # Restaura método original
            self.download_manager._download_from_url = original_method
    
    def test_detailed_download_logging(self):
        """
        Testa logs detalhados de operações de download (Requisito 2.4)
        """
        # Importa o sistema de progress tracking
        from progress_tracking_extension import progress_tracker, DownloadLog
        
        # Inicia tracking de download
        download_id = "test_download_123"
        component_name = "test_component"
        url = "https://example.com/test.exe"
        
        download_log = progress_tracker.start_download_tracking(download_id, component_name, url)
        
        # Verifica se log foi criado
        self.assertEqual(download_log.download_id, download_id)
        self.assertEqual(download_log.component_name, component_name)
        self.assertEqual(download_log.url, url)
        self.assertEqual(download_log.status, "started")
        
        # Simula progresso
        progress = DownloadProgress(
            total_size=1000,
            downloaded_size=500,
            speed=100,
            eta=5,
            percentage=50,
            status=DownloadStatus.DOWNLOADING,
            component_name=component_name,
            url=url
        )
        
        progress_tracker.update_download_progress(download_id, progress)
        
        # Verifica se progresso foi atualizado
        active_downloads = progress_tracker.get_active_downloads()
        self.assertEqual(len(active_downloads), 1)
        self.assertEqual(active_downloads[0].downloaded_size, 500)
        
        # Completa download
        progress_tracker.complete_download_tracking(
            download_id, 
            success=True, 
            verification_passed=True,
            mirror_used="https://mirror.example.com"
        )
        
        # Verifica se download foi removido dos ativos
        active_downloads = progress_tracker.get_active_downloads()
        self.assertEqual(len(active_downloads), 0)
        
        # Verifica estatísticas
        stats = progress_tracker.get_download_statistics()
        self.assertEqual(stats['total_downloads'], 1)
        self.assertEqual(stats['successful_downloads'], 1)
        self.assertEqual(stats['success_rate'], 100.0)
    
    def test_progress_notifications_system(self):
        """
        Testa sistema de notificações de progresso para interface (Requisito 2.4)
        """
        from progress_tracking_extension import progress_tracker, ProgressNotification
        
        notifications_received = []
        
        def notification_callback(notification: ProgressNotification):
            notifications_received.append(notification)
        
        # Registra callback
        progress_tracker.register_progress_callback(notification_callback)
        
        try:
            # Inicia download
            download_id = "test_notification_123"
            progress_tracker.start_download_tracking(download_id, "test_component", "https://example.com/test.exe")
            
            # Verifica notificação de início
            self.assertEqual(len(notifications_received), 1)
            self.assertEqual(notifications_received[0].notification_type, 'started')
            self.assertEqual(notifications_received[0].download_id, download_id)
            
            # Simula progresso
            progress = DownloadProgress(
                total_size=1000,
                downloaded_size=250,
                speed=50,
                eta=15,
                percentage=25,
                status=DownloadStatus.DOWNLOADING,
                component_name="test_component"
            )
            
            progress_tracker.update_download_progress(download_id, progress)
            
            # Verifica notificação de progresso
            self.assertEqual(len(notifications_received), 2)
            self.assertEqual(notifications_received[1].notification_type, 'progress')
            self.assertEqual(notifications_received[1].progress.percentage, 25)
            
            # Completa download
            progress_tracker.complete_download_tracking(download_id, success=True)
            
            # Verifica notificação de conclusão
            self.assertEqual(len(notifications_received), 3)
            self.assertEqual(notifications_received[2].notification_type, 'completed')
            
            # Testa serialização de notificação
            notification_dict = notifications_received[1].to_dict()
            self.assertIn('download_id', notification_dict)
            self.assertIn('progress', notification_dict)
            self.assertIn('timestamp', notification_dict)
            
        finally:
            # Remove callback
            progress_tracker.unregister_progress_callback(notification_callback)


if __name__ == '__main__':
    unittest.main()