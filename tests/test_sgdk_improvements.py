#!/usr/bin/env python3
"""
Teste das melhorias implementadas no módulo SGDK
Verifica se as correções e aprimoramentos estão funcionando corretamente
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Adicionar o diretório core ao path para importar os módulos
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from retro_devkit_manager import RetroDevKitManager
from retro_integration import RetroIntegration

class TestSGDKImprovements(unittest.TestCase):
    """Testes para as melhorias do módulo SGDK"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir)
        
        # Mock do logger
        self.mock_logger = Mock()
        
        # Criar instância do manager
        self.manager = RetroDevKitManager(base_path=self.base_path)
        self.manager.logger = self.mock_logger
    
    def tearDown(self):
        """Limpeza após os testes"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_sgdk_devkit_info_improvements(self):
        """Testa se as informações do SGDK foram aprimoradas"""
        devkits = self.manager._get_available_devkits()
        sgdk_info = devkits.get("megadrive")
        
        self.assertIsNotNone(sgdk_info, "SGDK devkit deve estar disponível")
        
        # Verificar dependências aprimoradas
        expected_deps = ["gcc-m68k-elf", "make", "java", "unzip", "wget", "p7zip-full"]
        for dep in expected_deps:
            self.assertIn(dep, sgdk_info.dependencies, 
                         f"Dependência {dep} deve estar presente")
        
        # Verificar URL específica
        self.assertIn("sgdk180.7z", sgdk_info.download_url, 
                     "URL deve apontar para versão específica")
        
        # Verificar comandos de verificação aprimorados
        verification_cmds = sgdk_info.verification_commands
        self.assertTrue(any("java -version" in cmd for cmd in verification_cmds),
                       "Deve verificar versão do Java")
        self.assertTrue(any("rescomp.jar" in cmd for cmd in verification_cmds),
                       "Deve verificar presença do rescomp.jar")
    
    @patch('platform.system')
    def test_detect_java_home_windows(self, mock_platform):
        """Testa detecção do JAVA_HOME no Windows"""
        mock_platform.return_value = "Windows"
        
        with patch('os.environ.get') as mock_env:
            mock_env.return_value = None
            
            # Simular diretório Java existente
            java_dir = self.base_path / "Program Files" / "Java" / "jdk-11"
            java_dir.mkdir(parents=True)
            
            with patch('pathlib.Path.exists') as mock_exists:
                mock_exists.return_value = True
                with patch('pathlib.Path.iterdir') as mock_iterdir:
                    mock_iterdir.return_value = [java_dir]
                    
                    java_home = self.manager._detect_java_home()
                    self.assertIsNotNone(java_home)
    
    @patch('sys.platform', 'win32')
    def test_get_sgdk_install_commands_windows(self):
        """Testa comandos de instalação do SGDK no Windows"""
        commands = self.manager._get_sgdk_install_commands()
        
        self.assertTrue(any("powershell" in cmd for cmd in commands),
                       "Deve usar PowerShell no Windows")
        self.assertTrue(any("7z x" in cmd for cmd in commands),
                       "Deve usar 7z para extrair")
        self.assertTrue(any("del sgdk180.7z" in cmd for cmd in commands),
                       "Deve limpar arquivo temporário")
    
    @patch('sys.platform', 'linux')
    def test_get_sgdk_install_commands_linux(self):
        """Testa comandos de instalação do SGDK no Linux"""
        commands = self.manager._get_sgdk_install_commands()
        
        self.assertTrue(any("wget" in cmd for cmd in commands),
                       "Deve usar wget no Linux")
        self.assertTrue(any("chmod +x" in cmd for cmd in commands),
                       "Deve definir permissões executáveis")
        self.assertTrue(any("rm sgdk180.7z" in cmd for cmd in commands),
                       "Deve limpar arquivo temporário")
    
    def test_package_mapping_improvements(self):
        """Testa se os mapeamentos de pacotes foram aprimorados"""
        # Testar mapeamento APT
        apt_mapping = self.manager._get_package_mapping('apt')
        self.assertIn('gcc-m68k-elf', apt_mapping)
        self.assertIn('unzip', apt_mapping)
        self.assertIn('p7zip-full', apt_mapping)
        
        # Testar mapeamento Chocolatey
        choco_mapping = self.manager._get_package_mapping('choco')
        self.assertIn('p7zip-full', choco_mapping)
        self.assertEqual(choco_mapping['p7zip-full'], '7zip')
    
    @patch('subprocess.run')
    def test_verify_installation_improvements(self, mock_run):
        """Testa melhorias na verificação de instalação"""
        # Simular arquivo existente
        test_file = self.base_path / "test_file.jar"
        test_file.touch()
        
        # Criar devkit info de teste
        from retro_devkit_manager import DevKitInfo, ConsoleGeneration, ConsoleType
        test_devkit = DevKitInfo(
            name="Test",
            console="Test Console",
            generation=ConsoleGeneration.BIT_16,
            console_type=ConsoleType.HOME,
            devkit_name="Test",
            dependencies=[],
            environment_vars={},
            download_url="",
            install_commands=[],
            verification_commands=[
                f"test -f {test_file}",
                "java -version"
            ],
            emulators=[],
            docker_support=False
        )
        
        # Mock subprocess para comando java
        mock_run.return_value.returncode = 0
        
        result = self.manager._verify_installation(test_devkit)
        self.assertTrue(result, "Verificação deve passar com arquivo existente")
        
        # Testar com arquivo inexistente
        test_devkit.verification_commands = [f"test -f {self.base_path / 'nonexistent.jar'}"]
        result = self.manager._verify_installation(test_devkit)
        self.assertFalse(result, "Verificação deve falhar com arquivo inexistente")

class TestRetroIntegrationImprovements(unittest.TestCase):
    """Testes para melhorias na integração retro"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir)
        
        # Mock dos managers
        self.mock_installation_manager = Mock()
        self.mock_retro_manager = Mock()
        
        # Criar instância da integração
        self.integration = RetroIntegration(
            installation_manager=self.mock_installation_manager,
            retro_manager=self.mock_retro_manager
        )
        self.integration.logger = Mock()
    
    def tearDown(self):
        """Limpeza após os testes"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('shutil.which')
    def test_check_sgdk_prerequisites(self, mock_which):
        """Testa verificação de pré-requisitos do SGDK"""
        # Simular Java e Make disponíveis
        mock_which.side_effect = lambda cmd: '/usr/bin/' + cmd if cmd in ['java', 'make'] else None
        
        result = self.integration._check_sgdk_prerequisites()
        self.assertTrue(result, "Pré-requisitos devem estar atendidos")
        
        # Simular Java indisponível
        mock_which.side_effect = lambda cmd: '/usr/bin/make' if cmd == 'make' else None
        
        result = self.integration._check_sgdk_prerequisites()
        self.assertFalse(result, "Deve falhar sem Java")
    
    def test_get_system_compatibility_info(self):
        """Testa informações de compatibilidade do sistema"""
        info = self.integration._get_system_compatibility_info()
        
        required_keys = ['os', 'architecture', 'python_version', 'docker_available', 
                        'java_available', 'make_available', 'git_available']
        
        for key in required_keys:
            self.assertIn(key, info, f"Chave {key} deve estar presente")
    
    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_create_sgdk_sample_project(self, mock_open, mock_mkdir):
        """Testa criação de projeto de exemplo SGDK"""
        self.integration._create_sgdk_sample_project()
        
        # Verificar se tentou criar diretórios
        mock_mkdir.assert_called()
        
        # Verificar se tentou escrever arquivos
        mock_open.assert_called()
        
        # Verificar conteúdo dos arquivos
        written_content = ''.join(call.args[0] for call in mock_open().write.call_args_list)
        self.assertIn('#include <genesis.h>', written_content)
        self.assertIn('Hello SGDK!', written_content)
    
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    def test_sgdk_emulator_installation(self, mock_exists, mock_mkdir):
        """Testa instalação dos emuladores SGDK"""
        from core.sgdk_improvements import SGDKInstaller
        
        # Simular que os diretórios não existem ainda
        mock_exists.return_value = False
        
        installer = SGDKInstaller(Path("/test/path"))
        
        # Verificar se os caminhos dos emuladores estão corretos
        expected_paths = {
            'bizhawk': installer.gendk_path / "_Emuladores" / "BizHawk",
            'blastem': installer.gendk_path / "_Emuladores" / "Blastem", 
            'genskmod': installer.gendk_path / "_Emuladores" / "GensKMod"
        }
        
        # Verificar se os emuladores estão na configuração
        config = installer.get_improved_sgdk_config()
        emulators = config.get('emulators', {})
        
        self.assertIn('bizhawk', emulators)
        self.assertIn('blastem', emulators)
        self.assertIn('genskmod', emulators)
        
        # Verificar informações dos emuladores
        self.assertEqual(emulators['bizhawk']['name'], 'BizHawk')
        self.assertEqual(emulators['blastem']['name'], 'Blastem')
        self.assertEqual(emulators['genskmod']['name'], 'GensKMod')
        
        # Verificar se tem descrições
        self.assertIn('description', emulators['bizhawk'])
        self.assertIn('features', emulators['bizhawk'])
    
    @patch('subprocess.run')
    @patch('shutil.which')
    def test_vscode_extension_installation(self, mock_which, mock_subprocess):
        """Testa instalação da extensão Genesis Code no VS Code"""
        from core.sgdk_improvements import SGDKInstaller
        
        # Simular que VS Code está disponível
        mock_which.side_effect = lambda cmd: '/usr/bin/code' if cmd == 'code' else None
        
        # Simular sucesso na instalação da extensão
        mock_subprocess.return_value.returncode = 0
        
        installer = SGDKInstaller(Path("/test/path"), logging.getLogger())
        
        # Testar instalação no VS Code
        result = installer._install_genesis_code_vscode()
        self.assertTrue(result)
        
        # Verificar se o comando correto foi chamado
        mock_subprocess.assert_called_with([
            'code', '--install-extension', 'zerasul.genesis-code'
        ], capture_output=True, text=True, timeout=60)
    
    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_vscode_workspace_configuration(self, mock_json_dump, mock_file_open, mock_mkdir):
        """Testa configuração do workspace VS Code para SGDK"""
        from core.sgdk_improvements import SGDKInstaller
        
        installer = SGDKInstaller(Path("/test/path"), logging.getLogger())
        
        # Testar configuração do workspace
        result = installer._configure_vscode_workspace()
        self.assertTrue(result)
        
        # Verificar se os diretórios foram criados
        mock_mkdir.assert_called()
        
        # Verificar se os arquivos de configuração foram criados
        expected_files = ['settings.json', 'tasks.json', 'launch.json']
        opened_files = [call[0][0].name for call in mock_file_open.call_args_list]
        
        for expected_file in expected_files:
            self.assertTrue(any(expected_file in str(opened_file) for opened_file in opened_files))
        
        # Verificar se JSON foi escrito
        self.assertEqual(mock_json_dump.call_count, 3)  # 3 arquivos JSON

def run_sgdk_tests():
    """Executa todos os testes das melhorias do SGDK"""
    print("🧪 Executando testes das melhorias do SGDK...\n")
    
    # Criar suite de testes
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Adicionar testes
    suite.addTests(loader.loadTestsFromTestCase(TestSGDKImprovements))
    suite.addTests(loader.loadTestsFromTestCase(TestRetroIntegrationImprovements))
    
    # Executar testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Relatório final
    print(f"\n📊 Resultados dos testes:")
    print(f"✅ Testes executados: {result.testsRun}")
    print(f"❌ Falhas: {len(result.failures)}")
    print(f"🚫 Erros: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Falhas encontradas:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split('\n')[0]}")
    
    if result.errors:
        print("\n🚫 Erros encontrados:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('\n')[-2]}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n{'✅ Todos os testes passaram!' if success else '❌ Alguns testes falharam.'}")
    
    return success

if __name__ == "__main__":
    run_sgdk_tests()