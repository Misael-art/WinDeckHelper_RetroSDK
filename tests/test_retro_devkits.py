"""Testes unitários para o sistema de retro devkits
Testa todas as funcionalidades dos managers de retro devkits"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Adicionar o diretório core ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from retro_devkit_manager import RetroDevkitManager
from retro_devkit_detector import RetroDevkitDetector, DetectionResult
from retro_devkit_config import RetroDevkitConfigManager, DevkitConfig, EmulatorConfig
from retro_devkit_logger import RetroDevkitLogger
from component_manager import ComponentManager, ComponentType, ComponentInfo

class TestRetroDevkitManager(unittest.TestCase):
    """Testes para RetroDevkitManager"""
    
    def setUp(self):
        """Configuração para cada teste"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.logger = Mock()
        self.manager = RetroDevkitManager(self.temp_dir, self.logger)
        
    def tearDown(self):
        """Limpeza após cada teste"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
    def test_init(self):
        """Testa inicialização do manager"""
        self.assertEqual(self.manager.base_path, self.temp_dir)
        self.assertEqual(self.manager.logger, self.logger)
        self.assertIsNotNone(self.manager.devkit_managers)
        
    def test_get_supported_devkits(self):
        """Testa obtenção de devkits suportados"""
        devkits = self.manager.get_supported_devkits()
        expected_devkits = ['gbdk', 'snes', 'psx', 'n64', 'gba', 'neogeo', 'nes', 'saturn']
        
        for devkit in expected_devkits:
            self.assertIn(devkit, devkits)
            
    def test_get_supported_emulators(self):
        """Testa obtenção de emuladores suportados"""
        emulators = self.manager.get_supported_emulators()
        self.assertIsInstance(emulators, list)
        self.assertGreater(len(emulators), 0)
        
    @patch('retro_devkit_manager.RetroDevkitManager._get_devkit_manager')
    def test_install_devkit_success(self, mock_get_manager):
        """Testa instalação bem-sucedida de devkit"""
        mock_devkit_manager = Mock()
        mock_devkit_manager.install.return_value = True
        mock_get_manager.return_value = mock_devkit_manager
        
        result = self.manager.install_devkit('gbdk')
        
        self.assertTrue(result)
        mock_devkit_manager.install.assert_called_once()
        
    @patch('retro_devkit_manager.RetroDevkitManager._get_devkit_manager')
    def test_install_devkit_failure(self, mock_get_manager):
        """Testa falha na instalação de devkit"""
        mock_devkit_manager = Mock()
        mock_devkit_manager.install.return_value = False
        mock_get_manager.return_value = mock_devkit_manager
        
        result = self.manager.install_devkit('gbdk')
        
        self.assertFalse(result)
        
    def test_install_unsupported_devkit(self):
        """Testa instalação de devkit não suportado"""
        result = self.manager.install_devkit('unsupported_devkit')
        self.assertFalse(result)
        
    @patch('retro_devkit_manager.RetroDevkitManager._get_devkit_manager')
    def test_uninstall_devkit(self, mock_get_manager):
        """Testa desinstalação de devkit"""
        mock_devkit_manager = Mock()
        mock_devkit_manager.uninstall.return_value = True
        mock_get_manager.return_value = mock_devkit_manager
        
        result = self.manager.uninstall_devkit('gbdk')
        
        self.assertTrue(result)
        mock_devkit_manager.uninstall.assert_called_once()
        
class TestRetroDevkitDetector(unittest.TestCase):
    """Testes para RetroDevkitDetector"""
    
    def setUp(self):
        """Configuração para cada teste"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.logger = Mock()
        self.detector = RetroDevkitDetector(self.temp_dir, self.logger)
        
    def tearDown(self):
        """Limpeza após cada teste"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
    def test_init(self):
        """Testa inicialização do detector"""
        self.assertEqual(self.detector.base_path, self.temp_dir)
        self.assertEqual(self.detector.logger, self.logger)
        self.assertIsNotNone(self.detector.devkit_checks)
        
    def test_detect_all_devkits(self):
        """Testa detecção de todos os devkits"""
        results = self.detector.detect_all_devkits()
        
        self.assertIsInstance(results, dict)
        expected_devkits = ['gbdk', 'snes', 'psx', 'n64', 'gba', 'neogeo', 'nes', 'saturn']
        
        for devkit in expected_devkits:
            self.assertIn(devkit, results)
            self.assertIsInstance(results[devkit], DetectionResult)
            
    def test_detect_specific_devkit(self):
        """Testa detecção de devkit específico"""
        result = self.detector.detect_devkit('gbdk')
        
        self.assertIsInstance(result, DetectionResult)
        self.assertEqual(result.devkit_name, 'gbdk')
        
    def test_detect_nonexistent_devkit(self):
        """Testa detecção de devkit inexistente"""
        result = self.detector.detect_devkit('nonexistent')
        
        self.assertIsInstance(result, DetectionResult)
        self.assertEqual(result.devkit_name, 'nonexistent')
        self.assertFalse(result.is_installed)
        self.assertEqual(result.confidence, 0.0)
        
    @patch('pathlib.Path.exists')
    def test_check_file_exists_true(self, mock_exists):
        """Testa verificação de arquivo existente"""
        mock_exists.return_value = True
        
        result = self.detector._check_file_exists('/fake/path/file.exe')
        
        self.assertTrue(result)
        
    @patch('pathlib.Path.exists')
    def test_check_file_exists_false(self, mock_exists):
        """Testa verificação de arquivo inexistente"""
        mock_exists.return_value = False
        
        result = self.detector._check_file_exists('/fake/path/file.exe')
        
        self.assertFalse(result)
        
    def test_generate_summary(self):
        """Testa geração de resumo"""
        summary = self.detector.generate_summary()
        
        self.assertIsInstance(summary, str)
        self.assertIn('DETECÇÃO DE RETRO DEVKITS', summary)
        
    def test_generate_detailed_report(self):
        """Testa geração de relatório detalhado"""
        report = self.detector.generate_detailed_report()
        
        self.assertIsInstance(report, str)
        self.assertIn('RELATÓRIO DETALHADO', report)
        
class TestRetroDevkitConfigManager(unittest.TestCase):
    """Testes para RetroDevkitConfigManager"""
    
    def setUp(self):
        """Configuração para cada teste"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.logger = Mock()
        self.config_manager = RetroDevkitConfigManager(self.temp_dir, self.logger)
        
    def tearDown(self):
        """Limpeza após cada teste"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
    def test_init(self):
        """Testa inicialização do gerenciador de configuração"""
        self.assertEqual(self.config_manager.base_path, self.temp_dir)
        self.assertEqual(self.config_manager.logger, self.logger)
        
    def test_create_default_config(self):
        """Testa criação de configuração padrão"""
        config = self.config_manager.create_default_config()
        
        self.assertIsNotNone(config)
        self.assertIsNotNone(config.devkits)
        self.assertIsNotNone(config.emulators)
        
    def test_add_devkit_config(self):
        """Testa adição de configuração de devkit"""
        devkit_config = DevkitConfig(
            name='test_devkit',
            installation_path=Path('/test/path'),
            version='1.0.0',
            is_enabled=True
        )
        
        result = self.config_manager.add_devkit_config(devkit_config)
        self.assertTrue(result)
        
    def test_add_emulator_config(self):
        """Testa adição de configuração de emulador"""
        emulator_config = EmulatorConfig(
            name='test_emulator',
            executable_path=Path('/test/emulator.exe'),
            supported_formats=['.rom'],
            is_enabled=True
        )
        
        result = self.config_manager.add_emulator_config(emulator_config)
        self.assertTrue(result)
        
    def test_get_devkit_config(self):
        """Testa obtenção de configuração de devkit"""
        # Primeiro adicionar uma configuração
        devkit_config = DevkitConfig(
            name='test_devkit',
            installation_path=Path('/test/path'),
            version='1.0.0',
            is_enabled=True
        )
        self.config_manager.add_devkit_config(devkit_config)
        
        # Depois recuperar
        retrieved_config = self.config_manager.get_devkit_config('test_devkit')
        
        self.assertIsNotNone(retrieved_config)
        self.assertEqual(retrieved_config.name, 'test_devkit')
        
    def test_get_nonexistent_devkit_config(self):
        """Testa obtenção de configuração inexistente"""
        config = self.config_manager.get_devkit_config('nonexistent')
        self.assertIsNone(config)
        
class TestRetroDevkitLogger(unittest.TestCase):
    """Testes para RetroDevkitLogger"""
    
    def setUp(self):
        """Configuração para cada teste"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.logger_manager = RetroDevkitLogger(self.temp_dir)
        
    def tearDown(self):
        """Limpeza após cada teste"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
    def test_init(self):
        """Testa inicialização do gerenciador de logs"""
        self.assertEqual(self.logger_manager.base_path, self.temp_dir)
        self.assertIsNotNone(self.logger_manager.log_dir)
        
    def test_get_main_logger(self):
        """Testa obtenção do logger principal"""
        logger = self.logger_manager.get_main_logger()
        
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, 'retro_devkits')
        
    def test_get_devkit_logger(self):
        """Testa obtenção de logger específico de devkit"""
        logger = self.logger_manager.get_devkit_logger('gbdk')
        
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, 'retro_devkits.gbdk')
        
    def test_enable_debug_mode(self):
        """Testa habilitação do modo debug"""
        self.logger_manager.enable_debug_mode()
        
        logger = self.logger_manager.get_main_logger()
        self.assertEqual(logger.level, 10)  # DEBUG level
        
    def test_disable_debug_mode(self):
        """Testa desabilitação do modo debug"""
        self.logger_manager.disable_debug_mode()
        
        logger = self.logger_manager.get_main_logger()
        self.assertEqual(logger.level, 20)  # INFO level
        
    def test_log_installation_progress(self):
        """Testa log de progresso de instalação"""
        # Este teste verifica se o método não gera exceções
        try:
            self.logger_manager.log_installation_progress('gbdk', 'downloading', 50)
            result = True
        except Exception:
            result = False
            
        self.assertTrue(result)
        
class TestComponentManager(unittest.TestCase):
    """Testes para ComponentManager"""
    
    def setUp(self):
        """Configuração para cada teste"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Criar estrutura de diretórios necessária
        config_dir = self.temp_dir / "config" / "components"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Criar arquivo de componentes de teste
        test_components = {
            'test_component': {
                'category': 'Test',
                'description': 'Test component',
                'download_url': 'http://test.com/download',
                'install_method': 'auto',
                'verify_actions': [
                    {'type': 'file_exists', 'path': 'test_file.exe'}
                ]
            }
        }
        
        with open(config_dir / "test_components.yaml", 'w') as f:
            import yaml
            yaml.dump(test_components, f)
            
        # Mock dos managers de retro devkits
        with patch('component_manager.RetroDevkitManager'), \
             patch('component_manager.RetroDevkitDetector'), \
             patch('component_manager.RetroDevkitConfigManager'), \
             patch('component_manager.RetroDevkitLogger'), \
             patch('component_manager.InstallationManager'), \
             patch('component_manager.DownloadManager'), \
             patch('component_manager.StorageManager'):
            
            self.component_manager = ComponentManager(self.temp_dir)
        
    def tearDown(self):
        """Limpeza após cada teste"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
    def test_init(self):
        """Testa inicialização do gerenciador de componentes"""
        self.assertEqual(self.component_manager.base_path, self.temp_dir)
        self.assertIsNotNone(self.component_manager.components)
        
    def test_load_all_components(self):
        """Testa carregamento de todos os componentes"""
        # Componentes já são carregados na inicialização
        self.assertGreater(len(self.component_manager.components), 0)
        
    def test_get_component(self):
        """Testa obtenção de componente específico"""
        component = self.component_manager.get_component('test_component')
        
        self.assertIsNotNone(component)
        self.assertEqual(component.name, 'test_component')
        
    def test_get_nonexistent_component(self):
        """Testa obtenção de componente inexistente"""
        component = self.component_manager.get_component('nonexistent')
        self.assertIsNone(component)
        
    def test_get_components_by_type(self):
        """Testa obtenção de componentes por tipo"""
        components = self.component_manager.get_components_by_type(ComponentType.TOOL)
        
        self.assertIsInstance(components, list)
        
    def test_get_components_by_category(self):
        """Testa obtenção de componentes por categoria"""
        components = self.component_manager.get_components_by_category('Test')
        
        self.assertIsInstance(components, list)
        self.assertGreater(len(components), 0)
        
    @patch('pathlib.Path.exists')
    def test_is_component_installed_true(self, mock_exists):
        """Testa verificação de componente instalado"""
        mock_exists.return_value = True
        
        result = self.component_manager.is_component_installed('test_component')
        
        # Como o componente de teste tem verify_actions, deve verificar o arquivo
        # O resultado depende do mock
        self.assertIsInstance(result, bool)
        
    def test_get_installation_status(self):
        """Testa obtenção de status de instalação"""
        status = self.component_manager.get_installation_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn('total_components', status)
        self.assertIn('installed_count', status)
        self.assertIn('by_type', status)
        self.assertIn('components', status)
        
    def test_generate_installation_report(self):
        """Testa geração de relatório de instalação"""
        report = self.component_manager.generate_installation_report()
        
        self.assertIsInstance(report, str)
        self.assertIn('RELATÓRIO DE COMPONENTES', report)
        
    def test_refresh_component_status(self):
        """Testa atualização de status dos componentes"""
        result = self.component_manager.refresh_component_status()
        
        # Deve retornar True se não houver erros
        self.assertTrue(result)
        
class TestIntegration(unittest.TestCase):
    """Testes de integração entre componentes"""
    
    def setUp(self):
        """Configuração para testes de integração"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Limpeza após testes de integração"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
    @patch('component_manager.RetroDevkitManager')
    @patch('component_manager.RetroDevkitDetector')
    def test_manager_detector_integration(self, mock_detector, mock_manager):
        """Testa integração entre manager e detector"""
        # Configurar mocks
        mock_detector_instance = Mock()
        mock_detector.return_value = mock_detector_instance
        
        mock_manager_instance = Mock()
        mock_manager.return_value = mock_manager_instance
        
        # Simular detecção
        detection_result = DetectionResult(
            devkit_name='gbdk',
            is_installed=True,
            confidence=0.9,
            installation_path=Path('/fake/path'),
            version='4.1.0'
        )
        
        mock_detector_instance.detect_all_devkits.return_value = {
            'gbdk': detection_result
        }
        
        # Criar component manager
        with patch('component_manager.RetroDevkitConfigManager'), \
             patch('component_manager.RetroDevkitLogger'), \
             patch('component_manager.InstallationManager'), \
             patch('component_manager.DownloadManager'), \
             patch('component_manager.StorageManager'):
            
            component_manager = ComponentManager(self.temp_dir)
            
        # Verificar se a integração funciona
        self.assertIsNotNone(component_manager.retro_detector)
        self.assertIsNotNone(component_manager.retro_manager)
        
class TestPerformance(unittest.TestCase):
    """Testes de performance"""
    
    def setUp(self):
        """Configuração para testes de performance"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Limpeza após testes de performance"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
    def test_detector_performance(self):
        """Testa performance do detector"""
        import time
        
        logger = Mock()
        detector = RetroDevkitDetector(self.temp_dir, logger)
        
        start_time = time.time()
        results = detector.detect_all_devkits()
        end_time = time.time()
        
        detection_time = end_time - start_time
        
        # A detecção deve ser rápida (menos de 5 segundos)
        self.assertLess(detection_time, 5.0)
        self.assertIsInstance(results, dict)
        
    def test_component_loading_performance(self):
        """Testa performance do carregamento de componentes"""
        import time
        
        # Criar múltiplos arquivos de componentes
        config_dir = self.temp_dir / "config" / "components"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Criar 10 arquivos com 10 componentes cada
        for i in range(10):
            components = {}
            for j in range(10):
                components[f'component_{i}_{j}'] = {
                    'category': f'Category_{i}',
                    'description': f'Test component {i}_{j}',
                    'download_url': f'http://test.com/download_{i}_{j}',
                    'install_method': 'auto'
                }
                
            with open(config_dir / f"test_components_{i}.yaml", 'w') as f:
                import yaml
                yaml.dump(components, f)
                
        # Medir tempo de carregamento
        start_time = time.time()
        
        with patch('component_manager.RetroDevkitManager'), \
             patch('component_manager.RetroDevkitDetector'), \
             patch('component_manager.RetroDevkitConfigManager'), \
             patch('component_manager.RetroDevkitLogger'), \
             patch('component_manager.InstallationManager'), \
             patch('component_manager.DownloadManager'), \
             patch('component_manager.StorageManager'):
            
            component_manager = ComponentManager(self.temp_dir)
            
        end_time = time.time()
        loading_time = end_time - start_time
        
        # O carregamento deve ser rápido (menos de 3 segundos)
        self.assertLess(loading_time, 3.0)
        
        # Verificar se todos os componentes foram carregados
        self.assertEqual(len(component_manager.components), 100)

def run_tests():
    """Executa todos os testes"""
    # Configurar logging para testes
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Criar suite de testes
    test_suite = unittest.TestSuite()
    
    # Adicionar testes
    test_classes = [
        TestRetroDevkitManager,
        TestRetroDevkitDetector,
        TestRetroDevkitConfigManager,
        TestRetroDevkitLogger,
        TestComponentManager,
        TestIntegration,
        TestPerformance
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
        
    # Executar testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Retornar resultado
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)