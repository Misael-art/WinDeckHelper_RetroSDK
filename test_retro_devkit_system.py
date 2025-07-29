#!/usr/bin/env python3
"""
Teste abrangente do sistema de DevKits Retro
Valida instalação, configuração e integração completa
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Adicionar o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from env_dev.core.retro_devkit_manager import RetroDevKitManager, ConsoleGeneration, ConsoleType
from env_dev.core.retro_integration import RetroIntegration
from env_dev.core.configuration_manager_enhanced import EnhancedConfigurationManager as ConfigurationManager
from env_dev.core.installation_manager import InstallationManager

class RetroDevKitTester:
    """Tester completo para o sistema de DevKits Retro"""
    
    def __init__(self):
        self.temp_dir = None
        self.setup_test_environment()
        
    def setup_test_environment(self):
        """Configura ambiente de teste isolado"""
        self.temp_dir = tempfile.mkdtemp(prefix="retro_devkit_test_")
        print(f"🔧 Ambiente de teste criado em: {self.temp_dir}")
        
        # Configurar managers com diretório temporário
        self.config_manager = ConfigurationManager(base_path=self.temp_dir)
        self.installation_manager = InstallationManager(self.temp_dir)
        self.retro_manager = RetroDevKitManager(base_path=self.temp_dir)
        self.retro_integration = RetroIntegration(self.installation_manager, self.config_manager)
        
    def cleanup(self):
        """Limpa ambiente de teste"""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
            print(f"🧹 Ambiente de teste limpo: {self.temp_dir}")
    
    def test_devkit_initialization(self):
        """Testa inicialização dos devkits"""
        print("\n📋 Testando inicialização dos DevKits...")
        
        # Verificar se todos os devkits foram carregados
        devkits = self.retro_manager.devkits
        assert len(devkits) > 0, "Nenhum devkit foi carregado"
        
        # Verificar categorias esperadas
        expected_consoles = [
            'nes', 'gameboy', 'snes', 'megadrive', 'playstation1', 
            'gba', 'nds', 'psp', 'saturn', 'nintendo64'
        ]
        
        found_consoles = []
        for console_id in expected_consoles:
            if console_id in devkits:
                found_consoles.append(console_id)
                devkit = devkits[console_id]
                
                # Validar estrutura do devkit
                assert devkit.name, f"DevKit {console_id} sem nome"
                assert devkit.console, f"DevKit {console_id} sem console"
                assert devkit.devkit_name, f"DevKit {console_id} sem nome do devkit"
                assert devkit.dependencies, f"DevKit {console_id} sem dependências"
                assert devkit.environment_vars, f"DevKit {console_id} sem variáveis de ambiente"
                
                print(f"  ✅ {console_id}: {devkit.name}")
        
        print(f"📊 {len(found_consoles)}/{len(expected_consoles)} consoles esperados encontrados")
        return True
    
    def test_devkit_categories(self):
        """Testa categorização dos devkits"""
        print("\n🏷️ Testando categorização dos DevKits...")
        
        categories = self.retro_manager.list_available_devkits()
        
        expected_categories = [
            "8-bit Home Consoles",
            "8-bit Portable Consoles", 
            "16-bit Home Consoles",
            "16-bit Portable Consoles",
            "32-bit Home Consoles",
            "32-bit Portable Consoles"
        ]
        
        for category in expected_categories:
            assert category in categories, f"Categoria {category} não encontrada"
            devkits_in_category = categories[category]
            
            if devkits_in_category:
                print(f"  ✅ {category}: {len(devkits_in_category)} devkits")
                
                # Verificar estrutura dos devkits na categoria
                for devkit in devkits_in_category:
                    assert 'id' in devkit, "DevKit sem ID"
                    assert 'name' in devkit, "DevKit sem nome"
                    assert 'console' in devkit, "DevKit sem console"
                    assert 'emulators' in devkit, "DevKit sem emuladores"
            else:
                print(f"  ⚠️ {category}: vazia")
        
        return True
    
    def test_environment_variables(self):
        """Testa configuração de variáveis de ambiente"""
        print("\n🌍 Testando variáveis de ambiente...")
        
        # Testar alguns devkits específicos
        test_devkits = ['gameboy', 'snes', 'psp']
        
        for devkit_id in test_devkits:
            if devkit_id in self.retro_manager.devkits:
                devkit = self.retro_manager.devkits[devkit_id]
                env_vars = devkit.environment_vars
                
                assert env_vars, f"DevKit {devkit_id} sem variáveis de ambiente"
                
                # Verificar se as variáveis fazem sentido
                for var, value in env_vars.items():
                    assert var, "Variável de ambiente sem nome"
                    assert value, "Variável de ambiente sem valor"
                    assert isinstance(value, str), "Valor da variável deve ser string"
                
                print(f"  ✅ {devkit_id}: {len(env_vars)} variáveis configuradas")
        
        return True
    
    def test_integration_registration(self):
        """Testa registro dos devkits no sistema principal"""
        print("\n🔗 Testando integração com sistema principal...")
        
        # Registrar devkits
        self.retro_integration.register_retro_apps()
        
        # Verificar se foram registrados
        registered_apps = self.installation_manager.get_registered_applications()
        
        retro_apps = [app for app in registered_apps if 'retro' in app.get('tags', [])]
        assert len(retro_apps) > 0, "Nenhum devkit retro foi registrado"
        
        print(f"  ✅ {len(retro_apps)} devkits registrados no sistema principal")
        
        # Verificar estrutura de um app registrado
        sample_app = retro_apps[0]
        required_fields = ['name', 'description', 'category', 'dependencies', 'environment_vars']
        
        for field in required_fields:
            assert field in sample_app, f"Campo {field} ausente no app registrado"
        
        return True
    
    def test_installation_simulation(self):
        """Simula instalação de devkits (sem executar comandos reais)"""
        print("\n⚙️ Testando simulação de instalação...")
        
        # Mock dos comandos do sistema para evitar instalação real
        with patch('subprocess.run') as mock_run:
            # Configurar mock para simular sucesso
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            
            # Testar instalação de um devkit simples
            test_devkit = 'gameboy'
            
            if test_devkit in self.retro_manager.devkits:
                # Simular instalação
                success = self.retro_integration.install_retro_devkit(test_devkit, use_docker=False)
                
                # Verificar se a instalação foi "bem-sucedida"
                print(f"  ✅ Simulação de instalação do {test_devkit}: {'Sucesso' if success else 'Falha'}")
                
                # Verificar se comandos foram chamados
                assert mock_run.called, "Nenhum comando de instalação foi executado"
                
        return True
    
    def test_project_template_creation(self):
        """Testa criação de templates de projeto"""
        print("\n📁 Testando criação de templates de projeto...")
        
        test_devkit = 'gameboy'
        project_name = "test_retro_project"
        project_path = Path(self.temp_dir) / project_name
        
        # Criar template
        success = self.retro_manager.create_project_template(
            test_devkit, 
            project_name, 
            str(project_path)
        )
        
        assert success, "Falha na criação do template"
        assert project_path.exists(), "Diretório do projeto não foi criado"
        
        # Verificar estrutura do projeto
        expected_files = ['Makefile', 'README.md']
        expected_dirs = ['src', 'assets', 'build']
        
        for file_name in expected_files:
            file_path = project_path / file_name
            assert file_path.exists(), f"Arquivo {file_name} não foi criado"
            assert file_path.stat().st_size > 0, f"Arquivo {file_name} está vazio"
        
        for dir_name in expected_dirs:
            dir_path = project_path / dir_name
            assert dir_path.exists(), f"Diretório {dir_name} não foi criado"
            assert dir_path.is_dir(), f"{dir_name} não é um diretório"
        
        # Verificar conteúdo do arquivo principal
        main_file = project_path / "src" / "main.c"
        assert main_file.exists(), "Arquivo main.c não foi criado"
        
        with open(main_file, 'r') as f:
            content = f.read()
            assert project_name in content, "Nome do projeto não está no código"
            assert "Game Boy" in content, "Referência ao console não encontrada"
        
        print(f"  ✅ Template criado com sucesso em {project_path}")
        return True
    
    def test_workspace_creation(self):
        """Testa criação de workspace de desenvolvimento"""
        print("\n🏗️ Testando criação de workspace...")
        
        workspace_name = "test_retro_workspace"
        devkit_ids = ['gameboy', 'snes']
        
        # Criar workspace
        success = self.retro_integration.create_development_workspace(
            workspace_name, 
            devkit_ids
        )
        
        assert success, "Falha na criação do workspace"
        
        # Verificar estrutura do workspace
        workspace_path = Path.home() / "RetroWorkspaces" / workspace_name
        
        if workspace_path.exists():
            expected_dirs = ['projects', 'shared', 'tools', 'emulators']
            expected_files = ['workspace.json', 'activate.bat', 'activate.sh']
            
            for dir_name in expected_dirs:
                dir_path = workspace_path / dir_name
                assert dir_path.exists(), f"Diretório {dir_name} não foi criado"
            
            for file_name in expected_files:
                file_path = workspace_path / file_name
                assert file_path.exists(), f"Arquivo {file_name} não foi criado"
            
            # Verificar configuração do workspace
            config_file = workspace_path / "workspace.json"
            with open(config_file, 'r') as f:
                config = json.load(f)
                assert config['name'] == workspace_name
                assert config['devkits'] == devkit_ids
            
            print(f"  ✅ Workspace criado com sucesso")
            
            # Limpar workspace de teste
            shutil.rmtree(workspace_path)
        
        return True
    
    def test_batch_operations(self):
        """Testa operações em lote"""
        print("\n📦 Testando operações em lote...")
        
        # Testar instalação por geração (simulada)
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            
            # Instalar todos os devkits de 8-bit
            results = self.retro_integration.batch_install_by_generation(
                ConsoleGeneration.BIT_8, 
                use_docker=False
            )
            
            assert len(results) > 0, "Nenhum devkit de 8-bit encontrado"
            print(f"  ✅ Instalação em lote 8-bit: {len(results)} devkits processados")
            
            # Testar instalação por tipo
            results = self.retro_integration.batch_install_by_type(
                ConsoleType.PORTABLE, 
                use_docker=False
            )
            
            assert len(results) > 0, "Nenhum devkit portátil encontrado"
            print(f"  ✅ Instalação em lote portáteis: {len(results)} devkits processados")
        
        return True
    
    def test_export_functionality(self):
        """Testa funcionalidade de exportação"""
        print("\n📤 Testando exportação de dados...")
        
        # Testar exportação JSON
        json_data = self.retro_integration.export_devkit_list('json')
        assert json_data, "Exportação JSON falhou"
        
        # Verificar se é JSON válido
        try:
            parsed_json = json.loads(json_data)
            assert isinstance(parsed_json, list), "JSON exportado não é uma lista"
            assert len(parsed_json) > 0, "Lista JSON está vazia"
            print("  ✅ Exportação JSON válida")
        except json.JSONDecodeError:
            assert False, "JSON exportado é inválido"
        
        # Testar exportação CSV
        csv_data = self.retro_integration.export_devkit_list('csv')
        assert csv_data, "Exportação CSV falhou"
        assert 'category,id,name' in csv_data, "Cabeçalho CSV não encontrado"
        print("  ✅ Exportação CSV válida")
        
        return True
    
    def test_installation_summary(self):
        """Testa geração de resumo de instalação"""
        print("\n📊 Testando resumo de instalação...")
        
        summary = self.retro_integration.get_retro_installation_summary()
        
        # Verificar estrutura do resumo
        required_fields = ['total_devkits', 'installed_count', 'installation_status', 'categories', 'recommendations']
        
        for field in required_fields:
            assert field in summary, f"Campo {field} ausente no resumo"
        
        assert isinstance(summary['total_devkits'], int), "total_devkits deve ser inteiro"
        assert isinstance(summary['installed_count'], int), "installed_count deve ser inteiro"
        assert isinstance(summary['categories'], dict), "categories deve ser dict"
        assert isinstance(summary['recommendations'], list), "recommendations deve ser lista"
        
        print(f"  ✅ Resumo gerado: {summary['total_devkits']} devkits total")
        
        # Verificar recomendações
        recommendations = summary['recommendations']
        assert len(recommendations) > 0, "Nenhuma recomendação gerada"
        
        for rec in recommendations:
            assert 'title' in rec, "Recomendação sem título"
            assert 'devkits' in rec, "Recomendação sem devkits"
            assert isinstance(rec['devkits'], list), "devkits deve ser lista"
        
        print(f"  ✅ {len(recommendations)} recomendações geradas")
        
        return True
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("🚀 Iniciando testes do sistema de DevKits Retro")
        print("=" * 60)
        
        tests = [
            self.test_devkit_initialization,
            self.test_devkit_categories,
            self.test_environment_variables,
            self.test_integration_registration,
            self.test_installation_simulation,
            self.test_project_template_creation,
            self.test_workspace_creation,
            self.test_batch_operations,
            self.test_export_functionality,
            self.test_installation_summary
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                test()
                passed += 1
                print(f"✅ {test.__name__}")
            except Exception as e:
                failed += 1
                print(f"❌ {test.__name__}: {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 Resultados dos testes:")
        print(f"  ✅ Passou: {passed}")
        print(f"  ❌ Falhou: {failed}")
        print(f"  📈 Taxa de sucesso: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            print("\n🎉 Todos os testes passaram! Sistema de DevKits Retro está funcionando corretamente.")
        else:
            print(f"\n⚠️ {failed} teste(s) falharam. Verifique os erros acima.")
        
        return failed == 0


def main():
    """Função principal"""
    tester = RetroDevKitTester()
    
    try:
        success = tester.run_all_tests()
        
        if success:
            print("\n🎯 Demonstração das funcionalidades:")
            
            # Mostrar devkits disponíveis
            print("\n📋 DevKits Disponíveis:")
            categories = tester.retro_manager.list_available_devkits()
            for category, devkits in categories.items():
                if devkits:
                    print(f"\n  {category}:")
                    for devkit in devkits[:3]:  # Mostrar apenas os primeiros 3
                        print(f"    • {devkit['name']} ({devkit['id']})")
                        print(f"      Emuladores: {', '.join(devkit['emulators'][:2])}")
            
            # Mostrar resumo
            print("\n📊 Resumo do Sistema:")
            summary = tester.retro_integration.get_retro_installation_summary()
            print(f"  • Total de DevKits: {summary['total_devkits']}")
            print(f"  • Categorias: {len(summary['categories'])}")
            print(f"  • Recomendações: {len(summary['recommendations'])}")
            
            # Mostrar recomendações
            print("\n💡 Recomendações para Iniciantes:")
            for rec in summary['recommendations'][:2]:
                print(f"  • {rec['title']}: {rec['description']}")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Teste interrompido pelo usuário")
        return 1
    except Exception as e:
        print(f"\n💥 Erro inesperado: {e}")
        return 1
    finally:
        tester.cleanup()


if __name__ == "__main__":
    exit(main())