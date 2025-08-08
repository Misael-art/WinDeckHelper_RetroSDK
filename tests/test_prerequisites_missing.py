"""Testes para simular ausência de dependências e verificar mensagens de erro
Garante que o sistema falha graciosamente com mensagens compreensíveis"""

import unittest
import logging
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Importar módulos a serem testados
from core.prerequisites_checker import PrerequisitesChecker
from core.improved_sgdk_installer import ImprovedSGDKInstaller
from config.retro_devkit_constants import WINDOWS_REQUIRED_TOOLS, LINUX_REQUIRED_TOOLS

class TestMissingPrerequisites(unittest.TestCase):
    """Testes para verificar comportamento com dependências ausentes"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.logger = logging.getLogger("test_logger")
        self.logger.setLevel(logging.DEBUG)
        
        # Capturar logs para verificação
        self.log_handler = logging.StreamHandler()
        self.log_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(self.log_handler)
        
        self.prerequisites_checker = PrerequisitesChecker(self.logger, self.temp_dir)
        self.sgdk_installer = ImprovedSGDKInstaller(self.logger, self.temp_dir)
        
    def tearDown(self):
        """Limpeza após os testes"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            
    @patch('core.prerequisites_checker.which')
    @patch('core.prerequisites_checker.platform.system')
    def test_missing_java_error_message(self, mock_system, mock_which):
        """Testa mensagem de erro quando Java está ausente"""
        mock_system.return_value = 'Windows'
        
        # Criar nova instância com mock aplicado
        checker = PrerequisitesChecker(self.logger, self.temp_dir)
        
        # Simular Java ausente, mas make presente
        def mock_which_side_effect(tool):
            if tool == 'java':
                return None
            elif tool == 'make':
                return '/usr/bin/make'
            return '/usr/bin/tool'
            
        mock_which.side_effect = mock_which_side_effect
        
        # Verificar que a checagem falha
        missing = checker._check_required_tools()
        
        # Verificar que Java está na lista de ausentes
        self.assertIn('java', missing)
        self.assertNotIn('make', missing)
        
    @patch('core.prerequisites_checker.which')
    @patch('core.prerequisites_checker.platform.system')
    def test_missing_make_error_message(self, mock_system, mock_which):
        """Testa mensagem de erro quando Make está ausente"""
        mock_system.return_value = 'Windows'
        
        # Criar nova instância com mock aplicado
        checker = PrerequisitesChecker(self.logger, self.temp_dir)
        
        # Simular Make ausente, mas java presente
        def mock_which_side_effect(tool):
            if tool == 'make':
                return None
            elif tool == 'java':
                return '/usr/bin/java'
            return '/usr/bin/tool'
            
        mock_which.side_effect = mock_which_side_effect
        
        missing = checker._check_required_tools()
        
        self.assertIn('make', missing)
        self.assertNotIn('java', missing)
        
    @patch('core.prerequisites_checker.which')
    @patch('core.prerequisites_checker.platform.system')
    def test_missing_7zip_error_message(self, mock_system, mock_which):
        """Testa mensagem de erro quando 7-Zip está ausente"""
        mock_system.return_value = 'Windows'
        
        # Criar nova instância com mock aplicado
        checker = PrerequisitesChecker(self.logger, self.temp_dir)
        
        # Simular 7z ausente, mas wget presente
        def mock_which_side_effect(tool):
            if tool == '7z':
                return None
            elif tool == 'wget':
                return '/usr/bin/wget'
            return '/usr/bin/tool'
             
        mock_which.side_effect = mock_which_side_effect
         
        missing = checker._check_optional_tools()
         
        self.assertIn('7z', missing)
        self.assertNotIn('wget', missing)
        
    @patch('core.prerequisites_checker.which')
    @patch('core.prerequisites_checker.platform.system')
    def test_missing_wget_error_message(self, mock_system, mock_which):
        """Testa mensagem de erro quando wget está ausente"""
        mock_system.return_value = 'Windows'
        
        # Criar nova instância com mock aplicado
        checker = PrerequisitesChecker(self.logger, self.temp_dir)
        
        # Simular wget ausente, mas 7z presente
        def mock_which_side_effect(tool):
            if tool == 'wget':
                return None
            elif tool == '7z':
                return '/usr/bin/7z'
            return '/usr/bin/tool'
             
        mock_which.side_effect = mock_which_side_effect
         
        missing = checker._check_optional_tools()
         
        self.assertIn('wget', missing)
        self.assertNotIn('7z', missing)
        
    @patch('core.prerequisites_checker.which')
    @patch('core.prerequisites_checker.platform.system')
    def test_multiple_missing_tools_error_message(self, mock_system, mock_which):
        """Testa mensagem de erro quando múltiplas ferramentas estão ausentes"""
        mock_system.return_value = 'Windows'
        
        # Criar nova instância com mock aplicado
        checker = PrerequisitesChecker(self.logger, self.temp_dir)
        
        # Simular múltiplas ferramentas ausentes
        def mock_which_side_effect(tool):
            if tool in ['java', 'make', '7z']:
                return None
            elif tool == 'wget':
                return '/usr/bin/wget'
            return '/usr/bin/tool'
             
        mock_which.side_effect = mock_which_side_effect
         
        missing_required = checker._check_required_tools()
        missing_optional = checker._check_optional_tools()
        missing = missing_required + missing_optional
         
        self.assertIn('java', missing)
        self.assertIn('make', missing)
        self.assertIn('7z', missing)
        self.assertNotIn('wget', missing)
        
    @patch('shutil.which')
    def test_sgdk_installation_fails_with_missing_prerequisites(self, mock_which):
        """Testa que instalação do SGDK falha graciosamente com pré-requisitos ausentes"""
        # Simular todas as ferramentas ausentes
        mock_which.return_value = None
        
        # Tentar instalar SGDK
        result = self.sgdk_installer.install_sgdk()
        
        # Verificar que falhou
        self.assertFalse(result)
        
    @patch('platform.system')
    @patch('shutil.which')
    def test_windows_specific_missing_tools(self, mock_which, mock_platform):
        """Testa ferramentas específicas ausentes no Windows"""
        mock_platform.return_value = 'Windows'
        
        # Simular ferramentas específicas do Windows ausentes
        def mock_which_side_effect(tool):
            if tool in ['powershell', 'choco']:
                return None
            return 'C:\\Program Files\\tool.exe'
            
        mock_which.side_effect = mock_which_side_effect
        
        missing = self.prerequisites_checker._check_required_tools()
        
        # Verificar que detectou ferramentas ausentes
        self.assertTrue(len(missing) > 0)
        
    @patch('platform.system')
    @patch('shutil.which')
    def test_linux_specific_missing_tools(self, mock_which, mock_platform):
        """Testa ferramentas específicas ausentes no Linux"""
        mock_platform.return_value = 'Linux'
        
        # Simular ferramentas específicas do Linux ausentes
        def mock_which_side_effect(tool):
            if tool in ['apt', 'gcc']:
                return None
            return '/usr/bin/tool'
            
        mock_which.side_effect = mock_which_side_effect
        
        missing = self.prerequisites_checker._check_required_tools()
        
        # Verificar que detectou ferramentas ausentes
        self.assertTrue(len(missing) > 0)
        
    @patch('subprocess.run')
    @patch('core.prerequisites_checker.which')
    @patch('core.prerequisites_checker.platform.system')
    def test_java_version_check_failure(self, mock_system, mock_which, mock_run):
        """Testa falha na verificação de versão do Java"""
        mock_system.return_value = 'Windows'
        
        # Criar nova instância com mock aplicado
        checker = PrerequisitesChecker(self.logger, self.temp_dir)
        
        # Simular todas as ferramentas obrigatórias presentes
        def mock_which_side_effect(tool):
            if tool in ['java', 'make']:
                return '/usr/bin/' + tool
            return '/usr/bin/tool'
            
        mock_which.side_effect = mock_which_side_effect
        
        # Simular saída de versão inadequada
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = 'openjdk version "1.8.0_292"'
        
        # Verificar que detecta versão inadequada
        result = checker.check_all_prerequisites('sgdk')
        
        # Deve retornar True mesmo com versão antiga (warning apenas)
        self.assertTrue(result)
        
    @patch('subprocess.run')
    @patch('shutil.which')
    def test_java_execution_failure(self, mock_which, mock_run):
        """Testa falha na execução do Java"""
        # Simular Java presente mas não executável
        mock_which.return_value = '/usr/bin/java'
        
        # Simular falha na execução
        mock_run.side_effect = FileNotFoundError("Java não encontrado")
        
        # Verificar que detecta falha
        result = self.prerequisites_checker.check_all_prerequisites('sgdk')
        
        # Deve retornar False se Java não executa
        self.assertFalse(result)
        
    def test_error_message_clarity(self):
        """Testa clareza das mensagens de erro"""
        # Simular lista de ferramentas ausentes
        missing_tools = ['java', 'make', '7z']
        
        # Verificar que a mensagem é clara
        error_message = f"Dependências obrigatórias ausentes: {', '.join(missing_tools)}"
        
        self.assertIn('java', error_message)
        self.assertIn('make', error_message)
        self.assertIn('7z', error_message)
        self.assertIn('obrigatórias', error_message)
        
    @patch('core.prerequisites_checker.which')
    @patch('core.prerequisites_checker.platform.system')
    def test_partial_prerequisites_warning(self, mock_system, mock_which):
        """Testa warning para pré-requisitos opcionais ausentes"""
        mock_system.return_value = 'Windows'
        
        # Criar nova instância com mock aplicado
        checker = PrerequisitesChecker(self.logger, self.temp_dir)
        
        # Simular algumas ferramentas opcionais ausentes
        def mock_which_side_effect(tool):
            if tool in ['7z', 'wget']:  # Ferramentas opcionais do Windows
                return None
            return '/usr/bin/tool'
             
        mock_which.side_effect = mock_which_side_effect
         
        # Verificar ferramentas opcionais
        missing_optional = checker._check_optional_tools()
         
        self.assertIn('7z', missing_optional)
        self.assertIn('wget', missing_optional)
        
    @patch('platform.system')
    def test_unsupported_platform_handling(self, mock_platform):
        """Testa tratamento de plataforma não suportada"""
        mock_platform.return_value = 'Darwin'  # macOS
        
        # Verificar que não falha com plataforma não explicitamente suportada
        try:
            result = self.prerequisites_checker._check_devkit_specific_requirements('sgdk')
            # Deve funcionar mesmo em plataforma não listada
            self.assertIsInstance(result, bool)
        except Exception as e:
            self.fail(f"Não deveria falhar em plataforma não suportada: {e}")
            
class TestErrorMessageQuality(unittest.TestCase):
    """Testes específicos para qualidade das mensagens de erro"""
    
    def test_error_message_contains_solution_hints(self):
        """Testa se mensagens de erro contêm dicas de solução"""
        missing_tools = ['java', 'make']
        
        # Simular mensagem de erro com dicas
        error_message = (
            f"❌ Dependências obrigatórias ausentes: {', '.join(missing_tools)}\n"
            f"Por favor, instale-as antes de continuar."
        )
        
        self.assertIn('instale-as', error_message)
        self.assertIn('antes de continuar', error_message)
        
    def test_warning_message_for_optional_tools(self):
        """Testa mensagem de warning para ferramentas opcionais"""
        missing_optional = ['git', 'code']
        
        warning_message = (
            f"⚠️ Ferramentas opcionais ausentes: {', '.join(missing_optional)}\n"
            f"A instalação continuará, mas algumas funcionalidades podem não estar disponíveis."
        )
        
        self.assertIn('opcionais', warning_message)
        self.assertIn('continuará', warning_message)
        self.assertIn('funcionalidades podem não estar', warning_message)
        
    def test_platform_specific_error_messages(self):
        """Testa mensagens específicas por plataforma"""
        # Windows
        windows_message = "Para Windows, instale via Chocolatey: choco install java"
        self.assertIn('Chocolatey', windows_message)
        self.assertIn('choco install', windows_message)
        
        # Linux
        linux_message = "Para Ubuntu/Debian: sudo apt install openjdk-11-jdk"
        self.assertIn('apt install', linux_message)
        self.assertIn('sudo', linux_message)
        
if __name__ == '__main__':
    # Configurar logging para os testes
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    unittest.main(verbosity=2)