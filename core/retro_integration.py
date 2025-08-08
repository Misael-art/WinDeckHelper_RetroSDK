"""
Integração do RetroDevKitManager com o sistema principal
Conecta os devkits retro ao fluxo de instalação principal
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from .retro_devkit_manager import RetroDevKitManager, ConsoleGeneration, ConsoleType
from .installation_manager import InstallationManager
from .configuration_manager_enhanced import EnhancedConfigurationManager as ConfigurationManager

class RetroIntegration:
    """Integra devkits retro ao sistema de instalação principal"""
    
    def __init__(self, installation_manager: InstallationManager, config_manager: ConfigurationManager):
        self.installation_manager = installation_manager
        self.config_manager = config_manager
        self.retro_manager = RetroDevKitManager()
        self.logger = logging.getLogger(__name__)
        
    def register_retro_apps(self) -> None:
        """Registra todos os devkits como aplicações instaláveis"""
        self.logger.info("Registrando devkits retro como aplicações")
        
        categories = self.retro_manager.list_available_devkits()
        
        for category_name, devkits in categories.items():
            if not devkits:
                continue
                
            # Criar categoria no sistema principal
            category_id = category_name.lower().replace(' ', '_').replace('-', '_')
            
            for devkit_info in devkits:
                self._register_single_devkit(devkit_info, category_id)
    
    def _register_single_devkit(self, devkit_info: Dict[str, Any], category_id: str) -> None:
        """Registra um devkit individual como aplicação"""
        devkit_id = devkit_info['id']
        devkit = self.retro_manager.devkits[devkit_id]
        
        # Configuração da aplicação para o sistema principal
        app_config = {
            'name': devkit.name,
            'description': f"Kit de desenvolvimento para {devkit.console}",
            'category': category_id,
            'subcategory': 'retro_development',
            'tags': ['development', 'retro', 'gamedev', devkit.generation.value],
            'priority': 'medium',
            'size_mb': 500,  # Estimativa
            'dependencies': devkit.dependencies,
            'environment_vars': devkit.environment_vars,
            'verification_commands': devkit.verification_commands,
            'emulators': devkit.emulators,
            'docker_support': devkit.docker_support,
            'install_method': 'retro_devkit',
            'devkit_id': devkit_id
        }
        
        # Registrar no sistema de instalação
        self.installation_manager.register_application(devkit_id, app_config)
        
        self.logger.debug(f"Registrado devkit: {devkit_id}")
    
    def install_retro_devkit(self, devkit_id: str, use_docker: bool = None) -> bool:
        """
        Instala um devkit retro específico com verificações aprimoradas
        
        Args:
            devkit_id: ID do devkit
            use_docker: Forçar uso do Docker (None = auto-detectar)
            
        Returns:
            bool: Sucesso da instalação
        """
        if devkit_id not in self.retro_manager.devkits:
            self.logger.error(f"DevKit {devkit_id} não encontrado")
            return False
            
        # CORREÇÃO: Verificação de pré-requisitos específicos para SGDK
        if devkit_id == "megadrive" and not self._check_sgdk_prerequisites():
            self.logger.error("Pré-requisitos do SGDK não atendidos")
            return False
            
        # Auto-detectar Docker se não especificado
        if use_docker is None:
            use_docker = self._should_use_docker(devkit_id)
            
        self.logger.info(f"Instalando devkit {devkit_id} (Docker: {use_docker})")
        
        # Notificar início da instalação
        self.installation_manager.notify_installation_start(devkit_id)
        
        try:
            # Instalar usando o RetroDevKitManager
            success = self.retro_manager.install_devkit(devkit_id, use_docker)
            
            if success:
                # CORREÇÃO: Verificação pós-instalação mais robusta
                if not self._verify_devkit_installation(devkit_id):
                    self.logger.error(f"Verificação pós-instalação falhou para {devkit_id}")
                    success = False
                
                if success:
                    # Atualizar configuração do sistema
                    self._update_system_config(devkit_id)
                    
                    # Notificar sucesso
                    self.installation_manager.notify_installation_success(devkit_id)
                    
                    # CORREÇÃO: Cria projeto de exemplo para SGDK
                    if devkit_id == "megadrive":
                        self._create_sgdk_sample_project()
                    
                    self.logger.info(f"✅ DevKit {devkit_id} instalado com sucesso")
            
            if not success:
                self.installation_manager.notify_installation_failure(devkit_id, "Falha na instalação ou verificação")
                self.logger.error(f"❌ Falha na instalação do DevKit {devkit_id}")
                
            return success
            
        except Exception as e:
            self.installation_manager.notify_installation_failure(devkit_id, str(e))
            self.logger.error(f"Erro na instalação do DevKit {devkit_id}: {e}")
            return False
    
    def _should_use_docker(self, devkit_id: str) -> bool:
        """Determina se deve usar Docker para um devkit específico"""
        devkit = self.retro_manager.devkits[devkit_id]
        
        # Usar Docker se:
        # 1. DevKit suporta Docker
        # 2. Sistema tem Docker disponível
        # 3. Configuração do usuário permite
        
        if not devkit.docker_support:
            return False
            
        # Verificar se Docker está disponível
        import shutil
        if not shutil.which('docker'):
            return False
            
        # Verificar configuração do usuário
        docker_preference = self.config_manager.get_setting('retro_devkits.use_docker', 'auto')
        
        if docker_preference == 'always':
            return True
        elif docker_preference == 'never':
            return False
        else:  # 'auto'
            # Usar Docker para devkits mais complexos
            complex_devkits = ['saturn', 'nintendo64', 'psp', 'nds']
            return devkit_id in complex_devkits
    
    def _update_system_config(self, devkit_id: str) -> None:
        """Atualiza configuração do sistema após instalação"""
        devkit = self.retro_manager.devkits[devkit_id]
        
        # Adicionar variáveis de ambiente ao sistema
        env_config = self.config_manager.get_setting('environment_variables', {})
        env_config.update(devkit.environment_vars)
        self.config_manager.set_setting('environment_variables', env_config)
        
        # Registrar devkit como instalado
        installed_devkits = self.config_manager.get_setting('installed_devkits', [])
        if devkit_id not in installed_devkits:
            installed_devkits.append(devkit_id)
            self.config_manager.set_setting('installed_devkits', installed_devkits)
        
        # Salvar configurações
        self.config_manager.save_config()
    
    def batch_install_by_generation(self, generation: ConsoleGeneration, use_docker: bool = None) -> Dict[str, bool]:
        """
        Instala todos os devkits de uma geração específica
        
        Args:
            generation: Geração de console (8-bit, 16-bit, 32-bit)
            use_docker: Usar Docker para instalações
            
        Returns:
            Dict[str, bool]: Resultado da instalação para cada devkit
        """
        self.logger.info(f"Instalação em lote para geração {generation.value}")
        
        results = {}
        devkits_to_install = [
            devkit_id for devkit_id, devkit in self.retro_manager.devkits.items()
            if devkit.generation == generation
        ]
        
        for devkit_id in devkits_to_install:
            results[devkit_id] = self.install_retro_devkit(devkit_id, use_docker)
            
        return results
    
    def batch_install_by_type(self, console_type: ConsoleType, use_docker: bool = None) -> Dict[str, bool]:
        """
        Instala todos os devkits de um tipo específico (home/portable)
        
        Args:
            console_type: Tipo de console (home/portable)
            use_docker: Usar Docker para instalações
            
        Returns:
            Dict[str, bool]: Resultado da instalação para cada devkit
        """
        self.logger.info(f"Instalação em lote para tipo {console_type.value}")
        
        results = {}
        devkits_to_install = [
            devkit_id for devkit_id, devkit in self.retro_manager.devkits.items()
            if devkit.console_type == console_type
        ]
        
        for devkit_id in devkits_to_install:
            results[devkit_id] = self.install_retro_devkit(devkit_id, use_docker)
            
        return results
    
    def create_development_workspace(self, workspace_name: str, devkit_ids: List[str]) -> bool:
        """
        Cria um workspace de desenvolvimento com múltiplos devkits
        
        Args:
            workspace_name: Nome do workspace
            devkit_ids: Lista de IDs dos devkits a incluir
            
        Returns:
            bool: Sucesso da criação
        """
        workspace_path = Path.home() / "RetroWorkspaces" / workspace_name
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Criando workspace {workspace_name} em {workspace_path}")
        
        # Criar estrutura do workspace
        (workspace_path / "projects").mkdir(exist_ok=True)
        (workspace_path / "shared").mkdir(exist_ok=True)
        (workspace_path / "tools").mkdir(exist_ok=True)
        (workspace_path / "emulators").mkdir(exist_ok=True)
        (workspace_path / "docs").mkdir(exist_ok=True)
        
        # CORREÇÃO: Criar estruturas específicas para SGDK se incluído
        if "megadrive" in devkit_ids:
            (workspace_path / "projects" / "sgdk_samples").mkdir(exist_ok=True)
            (workspace_path / "shared" / "sgdk_resources").mkdir(exist_ok=True)
        
        # Criar configuração do workspace
        workspace_config = {
            'name': workspace_name,
            'created_at': str(Path.cwd()),
            'devkits': devkit_ids,
            'projects': [],
            'shared_resources': [],
            'version': '1.0'
        }
        
        config_file = workspace_path / "workspace.json"
        import json
        with open(config_file, 'w') as f:
            json.dump(workspace_config, f, indent=2)
        
        # Criar scripts de ativação
        self._create_workspace_scripts(workspace_path, devkit_ids)
        
        # CORREÇÃO: Criar documentação básica
        self._create_workspace_documentation(workspace_path, devkit_ids)
        
        self.logger.info(f"✅ Workspace {workspace_name} criado com sucesso")
        return True
    
    def _create_workspace_documentation(self, workspace_path: Path, devkit_ids: List[str]) -> None:
        """Cria documentação básica para o workspace"""
        docs_path = workspace_path / "docs"
        
        # README principal
        readme = docs_path / "README.md"
        with open(readme, 'w') as f:
            f.write(f"# Workspace Retro: {workspace_path.name}\n\n")
            f.write("## DevKits Incluídos\n\n")
            
            for devkit_id in devkit_ids:
                if devkit_id in self.retro_manager.devkits:
                    devkit = self.retro_manager.devkits[devkit_id]
                    f.write(f"- **{devkit.name}**: {devkit.console}\n")
            
            f.write("\n## Estrutura do Projeto\n\n")
            f.write("- `projects/`: Seus projetos de desenvolvimento\n")
            f.write("- `shared/`: Recursos compartilhados\n")
            f.write("- `tools/`: Ferramentas auxiliares\n")
            f.write("- `emulators/`: Emuladores para teste\n")
            f.write("- `docs/`: Documentação\n")
            
            if "megadrive" in devkit_ids:
                f.write("\n## SGDK (Mega Drive)\n\n")
                f.write("Para compilar projetos SGDK:\n")
                f.write("```bash\n")
                f.write("cd projects/seu_projeto_sgdk\n")
                f.write("make\n")
                f.write("```\n")
    
    def _create_workspace_scripts(self, workspace_path: Path, devkit_ids: List[str]) -> None:
        """Cria scripts de ativação do workspace"""
        
        # Script de ativação para Windows
        activate_bat = workspace_path / "activate.bat"
        with open(activate_bat, 'w') as f:
            f.write("@echo off\n")
            f.write(f"echo Ativando workspace retro: {workspace_path.name}\n")
            f.write("echo.\n")
            
            for devkit_id in devkit_ids:
                if devkit_id in self.retro_manager.devkits:
                    devkit = self.retro_manager.devkits[devkit_id]
                    f.write(f"echo Configurando {devkit.name}...\n")
                    
                    for var, value in devkit.environment_vars.items():
                        if var == 'PATH':
                            f.write(f"set PATH={value};%PATH%\n")
                        else:
                            f.write(f"set {var}={value}\n")
            
            f.write("echo.\n")
            f.write("echo Workspace ativo! Use 'deactivate' para sair.\n")
            f.write("cmd /k\n")
        
        # Script de ativação para Unix
        activate_sh = workspace_path / "activate.sh"
        with open(activate_sh, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write(f"echo 'Ativando workspace retro: {workspace_path.name}'\n")
            f.write("echo\n")
            
            for devkit_id in devkit_ids:
                if devkit_id in self.retro_manager.devkits:
                    devkit = self.retro_manager.devkits[devkit_id]
                    f.write(f"echo 'Configurando {devkit.name}...'\n")
                    
                    for var, value in devkit.environment_vars.items():
                        if var == 'PATH':
                            f.write(f"export PATH='{value}:$PATH'\n")
                        else:
                            f.write(f"export {var}='{value}'\n")
            
            f.write("echo\n")
            f.write("echo 'Workspace ativo! Use \"deactivate\" para sair.'\n")
            f.write("bash\n")
        
        # Tornar executável
        activate_sh.chmod(0o755)
        
        # CORREÇÃO: Script específico para SGDK se incluído
        if any(devkit_id == "megadrive" for devkit_id in devkit_ids):
            self._create_sgdk_workspace_scripts(workspace_path)
    
    def get_retro_installation_summary(self) -> Dict[str, Any]:
        """Retorna resumo das instalações de devkits retro com informações aprimoradas"""
        status = self.retro_manager.get_installation_status()
        categories = self.retro_manager.list_available_devkits()
        
        summary = {
            'total_devkits': len(self.retro_manager.devkits),
            'installed_count': sum(1 for installed in status.values() if installed),
            'installation_status': status,
            'categories': {},
            'recommendations': self._get_installation_recommendations(),
            'system_info': self._get_system_compatibility_info()
        }
        
        # Organizar por categoria
        for category_name, devkits in categories.items():
            if devkits:
                category_status = {
                    'total': len(devkits),
                    'installed': sum(1 for dk in devkits if status.get(dk['id'], False)),
                    'devkits': [
                        {
                            'id': dk['id'],
                            'name': dk['name'],
                            'installed': status.get(dk['id'], False),
                            'compatible': self._check_devkit_compatibility(dk['id'])
                        }
                        for dk in devkits
                    ]
                }
                summary['categories'][category_name] = category_status
        
        return summary
    
    def _get_system_compatibility_info(self) -> Dict[str, Any]:
        """Retorna informações de compatibilidade do sistema"""
        import platform
        import shutil
        
        return {
            'os': platform.system(),
            'architecture': platform.machine(),
            'python_version': platform.python_version(),
            'docker_available': shutil.which('docker') is not None,
            'java_available': shutil.which('java') is not None,
            'make_available': shutil.which('make') is not None,
            'git_available': shutil.which('git') is not None
        }
    
    def _check_devkit_compatibility(self, devkit_id: str) -> bool:
        """Verifica compatibilidade de um devkit específico com o sistema"""
        if devkit_id not in self.retro_manager.devkits:
            return False
            
        # Para SGDK, verificar pré-requisitos específicos
        if devkit_id == "megadrive":
            return self._check_sgdk_prerequisites()
            
        # Para outros devkits, verificação básica
        return True
    
    def _check_sgdk_prerequisites(self) -> bool:
        """Verifica pré-requisitos específicos para SGDK"""
        import shutil
        import os
        from pathlib import Path
        
        # Verificar se Java está disponível
        java_found = False
        if shutil.which('java'):
            java_found = True
        else:
            # Verificar locais comuns de instalação do Java
            java_paths = [
                "C:\\Program Files\\Eclipse Adoptium\\jdk-21.0.6.7-hotspot\\bin\\java.exe",
                "C:\\Program Files\\Java\\jdk*\\bin\\java.exe",
                "C:\\Program Files (x86)\\Java\\jdk*\\bin\\java.exe"
            ]
            
            for java_path in java_paths:
                if '*' in java_path:
                    # Usar glob para padrões com wildcard
                    import glob
                    matches = glob.glob(java_path)
                    if matches and Path(matches[0]).exists():
                        java_found = True
                        self.logger.info(f"Java encontrado em: {matches[0]}")
                        break
                elif Path(java_path).exists():
                    java_found = True
                    self.logger.info(f"Java encontrado em: {java_path}")
                    break
        
        if not java_found:
            self.logger.warning("Java não encontrado - necessário para algumas ferramentas do SGDK")
            return False
            
        # Verificar se make está disponível
        if not shutil.which('make'):
            self.logger.warning("Make não encontrado - necessário para compilação")
            return False
            
        return True
    
    def _verify_devkit_installation(self, devkit_id: str) -> bool:
        """Verifica se a instalação do devkit foi bem-sucedida"""
        devkit = self.retro_manager.devkits[devkit_id]
        
        # Executar comandos de verificação específicos do devkit
        for cmd in devkit.verification_commands:
            try:
                import subprocess
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    self.logger.error(f"Comando de verificação falhou: {cmd}")
                    return False
            except subprocess.TimeoutExpired:
                self.logger.error(f"Timeout na verificação: {cmd}")
                return False
            except Exception as e:
                self.logger.error(f"Erro na verificação {cmd}: {e}")
                return False
        
        return True
    
    def _create_sgdk_sample_project(self) -> None:
        """Cria um projeto de exemplo para SGDK"""
        try:
            sample_path = Path.home() / "RetroProjects" / "SGDK_Sample"
            sample_path.mkdir(parents=True, exist_ok=True)
            
            # Criar main.c básico
            main_c = sample_path / "main.c"
            with open(main_c, 'w') as f:
                f.write('''
#include <genesis.h>

int main()
{
    // Inicializar sistema
    SYS_disableInts();
    VDP_setScreenWidth320();
    VDP_setScreenHeight224();
    SYS_enableInts();
    
    // Exibir texto
    VDP_drawText("Hello SGDK!", 10, 10);
    VDP_drawText("Press START to continue", 8, 12);
    
    while(1)
    {
        if(JOY_readJoypad(JOY_1) & BUTTON_START)
        {
            VDP_clearPlane(BG_A, TRUE);
            VDP_drawText("SGDK is working!", 9, 10);
        }
        
        SYS_doVBlankProcess();
    }
    
    return 0;
}
''')
            
            # Criar Makefile
            makefile = sample_path / "Makefile"
            with open(makefile, 'w') as f:
                f.write('''
include $(SGDK_ROOT)/makefile.gen
''')
            
            self.logger.info(f"Projeto de exemplo SGDK criado em {sample_path}")
            
        except Exception as e:
            self.logger.error(f"Erro ao criar projeto de exemplo SGDK: {e}")
    
    def _get_installation_recommendations(self) -> List[Dict[str, str]]:
        """Gera recomendações de instalação baseadas no sistema"""
        recommendations = []
        
        # Recomendações para iniciantes
        recommendations.append({
            'title': 'Para Iniciantes',
            'description': 'Comece com Game Boy (GBDK-2020) - mais simples e bem documentado',
            'devkits': ['gameboy'],
            'reason': 'Curva de aprendizado suave e excelente documentação'
        })
        
        # Recomendações por popularidade
        recommendations.append({
            'title': 'Mais Populares',
            'description': 'DevKits com maior comunidade e recursos',
            'devkits': ['gameboy', 'snes', 'megadrive', 'gba'],
            'reason': 'Grande comunidade, muitos tutoriais e ferramentas'
        })
        
        # Recomendações por facilidade
        recommendations.append({
            'title': 'Instalação Mais Fácil',
            'description': 'DevKits com instalação simplificada',
            'devkits': ['gameboy', 'gba', 'nds'],
            'reason': 'DevKitPro oferece instaladores automáticos'
        })
        
        # CORREÇÃO: Recomendação específica para SGDK
        recommendations.append({
            'title': 'Mega Drive/Genesis (SGDK)',
            'description': 'Excelente para desenvolvimento 16-bit com C',
            'devkits': ['megadrive'],
            'reason': 'SGDK oferece desenvolvimento em C com boa documentação e exemplos'
        })
        
        return recommendations
    
    def export_devkit_list(self, format: str = 'json') -> str:
        """
        Exporta lista de devkits em formato específico
        
        Args:
            format: Formato de exportação ('json', 'yaml', 'csv')
            
        Returns:
            str: Dados exportados
        """
        categories = self.retro_manager.list_available_devkits()
        status = self.retro_manager.get_installation_status()
        
        export_data = []
        for category_name, devkits in categories.items():
            for devkit in devkits:
                export_data.append({
                    'category': category_name,
                    'id': devkit['id'],
                    'name': devkit['name'],
                    'console': devkit['console'],
                    'devkit': devkit['devkit'],
                    'emulators': ', '.join(devkit['emulators']),
                    'docker_support': devkit['docker_support'],
                    'installed': status.get(devkit['id'], False)
                })
        
        if format.lower() == 'json':
            import json
            return json.dumps(export_data, indent=2)
        
        elif format.lower() == 'yaml':
            try:
                import yaml
                return yaml.dump(export_data, default_flow_style=False)
            except ImportError:
                return "YAML não disponível. Instale PyYAML."
        
        elif format.lower() == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            if export_data:
                writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
                writer.writeheader()
                writer.writerows(export_data)
            
            return output.getvalue()
        
        else:
            return f"Formato '{format}' não suportado. Use: json, yaml, csv"
    
    def _create_sgdk_workspace_scripts(self, workspace_path: Path) -> None:
        """Cria scripts específicos para SGDK no workspace"""
        
        # Script para criar novo projeto SGDK
        new_project_bat = workspace_path / "new_sgdk_project.bat"
        with open(new_project_bat, 'w') as f:
            f.write("@echo off\n")
            f.write("set /p PROJECT_NAME=Nome do projeto SGDK: \n")
            f.write("mkdir projects\\%PROJECT_NAME%\n")
            f.write("cd projects\\%PROJECT_NAME%\n")
            f.write("echo #include ^<genesis.h^> > main.c\n")
            f.write("echo. >> main.c\n")
            f.write("echo int main() >> main.c\n")
            f.write("echo { >> main.c\n")
            f.write("echo     return 0; >> main.c\n")
            f.write("echo } >> main.c\n")
            f.write("echo include $(SGDK_ROOT)/makefile.gen > Makefile\n")
            f.write("echo Projeto %PROJECT_NAME% criado com sucesso!\n")
        
        # Script Unix equivalente
        new_project_sh = workspace_path / "new_sgdk_project.sh"
        with open(new_project_sh, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("read -p 'Nome do projeto SGDK: ' PROJECT_NAME\n")
            f.write("mkdir -p projects/$PROJECT_NAME\n")
            f.write("cd projects/$PROJECT_NAME\n")
            f.write("cat > main.c << EOF\n")
            f.write("#include <genesis.h>\n")
            f.write("\n")
            f.write("int main()\n")
            f.write("{\n")
            f.write("    return 0;\n")
            f.write("}\n")
            f.write("EOF\n")
            f.write("echo 'include $(SGDK_ROOT)/makefile.gen' > Makefile\n")
            f.write("echo 'Projeto $PROJECT_NAME criado com sucesso!'\n")
        
        new_project_sh.chmod(0o755)


# Exemplo de uso
if __name__ == "__main__":
    # Simulação de uso (normalmente seria integrado ao sistema principal)
    from .installation_manager import InstallationManager
    from .configuration_manager_enhanced import EnhancedConfigurationManager as ConfigurationManager
    
    config_manager = ConfigurationManager()
    installation_manager = InstallationManager(config_manager)
    
    retro_integration = RetroIntegration(installation_manager, config_manager)
    
    # Registrar todos os devkits
    retro_integration.register_retro_apps()
    
    # Mostrar resumo
    summary = retro_integration.get_retro_installation_summary()
    print("Resumo dos DevKits Retro:")
    print(f"Total: {summary['total_devkits']}")
    print(f"Instalados: {summary['installed_count']}")