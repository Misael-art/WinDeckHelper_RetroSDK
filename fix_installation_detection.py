#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir o sistema de detecção de instalação dos devkits retro
Substitui comandos Unix por verificações nativas Python e corrige caminhos
"""

import os
import sys
from pathlib import Path
import logging
import shutil

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def fix_retro_devkit_manager():
    """Corrige o RetroDevKitManager para usar verificações nativas Python"""
    logger.info("🔧 Corrigindo RetroDevKitManager...")
    
    manager_file = Path("core/retro_devkit_manager.py")
    if not manager_file.exists():
        logger.error(f"❌ Arquivo não encontrado: {manager_file}")
        return False
    
    # Ler conteúdo atual
    with open(manager_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup do arquivo original
    backup_file = manager_file.with_suffix('.py.backup')
    shutil.copy2(manager_file, backup_file)
    logger.info(f"📋 Backup criado: {backup_file}")
    
    # Substituições necessárias
    replacements = [
        # Corrigir método _verify_installation
        (
            '''    def _verify_installation(self, devkit: DevKitInfo) -> bool:
        """Verifica se a instalação foi bem-sucedida"""
        self.logger.info(f"Verificando instalação do {devkit.name}")
        
        for command in devkit.verification_commands:
            # CORREÇÃO: Melhor tratamento para comandos de teste de arquivo
            if command.startswith("test -f"):
                file_path = command.split("test -f ")[1]
                if not Path(file_path).exists():
                    self.logger.error(f"Arquivo não encontrado: {file_path}")
                    return False
                continue
            
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self.logger.error(f"Verificação falhou para: {command}")
                self.logger.error(f"Saída: {result.stderr}")
                return False
                
        self.logger.info(f"✅ {devkit.name} instalado com sucesso!")
        return True''',
            '''    def _verify_installation(self, devkit: DevKitInfo) -> bool:
        """Verifica se a instalação foi bem-sucedida"""
        self.logger.info(f"Verificando instalação do {devkit.name}")
        
        for command in devkit.verification_commands:
            # CORREÇÃO: Usar verificação nativa Python para arquivos
            if command.startswith("test -f") or command.startswith("file_exists:"):
                # Extrair caminho do arquivo
                if command.startswith("test -f"):
                    file_path = command.split("test -f ")[1].strip()
                else:
                    file_path = command.split("file_exists:")[1].strip()
                
                # Normalizar caminho para Windows
                file_path = file_path.replace('/', os.sep).replace('\\\\', os.sep)
                
                if not Path(file_path).exists():
                    self.logger.error(f"Arquivo não encontrado: {file_path}")
                    return False
                else:
                    self.logger.info(f"✅ Arquivo encontrado: {file_path}")
                continue
            
            # Para outros comandos, executar normalmente
            try:
                result = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    self.logger.error(f"Verificação falhou para: {command}")
                    self.logger.error(f"Saída: {result.stderr}")
                    return False
                else:
                    self.logger.info(f"✅ Comando executado com sucesso: {command}")
            except subprocess.TimeoutExpired:
                self.logger.error(f"Timeout na verificação: {command}")
                return False
            except Exception as e:
                self.logger.error(f"Erro na verificação {command}: {e}")
                return False
                
        self.logger.info(f"✅ {devkit.name} instalado com sucesso!")
        return True'''
        ),
        
        # Corrigir comandos de verificação do SGDK
        (
            '''                verification_commands=[
                    "java -version",
                    "make --version",
                    f"test -f {self.base_path / 'sgdk' / 'bin' / 'rescomp.jar'}",
                    f"test -f {self.base_path / 'sgdk' / 'inc' / 'genesis.h'}"
                ],''',
            '''                verification_commands=[
                    "java -version",
                    "make --version",
                    f"file_exists:{self.base_path / 'retro_devkits' / 'sgdk' / 'bin' / 'rescomp.jar'}",
                    f"file_exists:{self.base_path / 'retro_devkits' / 'sgdk' / 'inc' / 'genesis.h'}",
                    f"file_exists:{self.base_path / 'retro_devkits' / 'sgdk' / 'bin' / 'gcc' / 'bin' / 'm68k-elf-gcc.exe'}"
                ],'''
        ),
        
        # Corrigir método get_installation_status
        (
            '''    def get_installation_status(self) -> Dict[str, bool]:
        """Verifica status de instalação de todos os devkits"""
        status = {}
        
        for devkit_id, devkit in self.devkits.items():
            # Verificar se comandos de verificação funcionam
            is_installed = True
            for command in devkit.verification_commands:
                result = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    text=True
                )
                if result.returncode != 0:
                    is_installed = False
                    break
                    
            status[devkit_id] = is_installed
            
        return status''',
            '''    def get_installation_status(self) -> Dict[str, bool]:
        """Verifica status de instalação de todos os devkits"""
        status = {}
        
        for devkit_id, devkit in self.devkits.items():
            # Usar método _verify_installation melhorado
            try:
                is_installed = self._verify_installation(devkit)
                status[devkit_id] = is_installed
            except Exception as e:
                self.logger.error(f"Erro ao verificar {devkit_id}: {e}")
                status[devkit_id] = False
            
        return status'''
        )
    ]
    
    # Aplicar substituições
    modified_content = content
    for old, new in replacements:
        if old in modified_content:
            modified_content = modified_content.replace(old, new)
            logger.info(f"✅ Substituição aplicada")
        else:
            logger.warning(f"⚠️ Padrão não encontrado para substituição")
    
    # Salvar arquivo modificado
    with open(manager_file, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    logger.info(f"✅ {manager_file} corrigido com sucesso!")
    return True

def create_improved_sgdk_verification():
    """Cria uma função melhorada de verificação específica para SGDK"""
    logger.info("🔧 Criando verificação melhorada para SGDK...")
    
    verification_code = '''
def verify_sgdk_installation(base_path: Path) -> bool:
    """Verificação específica e robusta para SGDK"""
    sgdk_path = base_path / "retro_devkits" / "sgdk"
    
    # Verificar se diretório principal existe
    if not sgdk_path.exists():
        return False
    
    # Arquivos essenciais para verificar
    essential_files = [
        sgdk_path / "inc" / "genesis.h",
        sgdk_path / "bin" / "rescomp.jar",
        sgdk_path / "makefile.gen",
        sgdk_path / "common.mk"
    ]
    
    # Verificar arquivos essenciais
    for file_path in essential_files:
        if not file_path.exists():
            return False
    
    # Verificar se há pelo menos alguns arquivos de biblioteca
    lib_path = sgdk_path / "lib"
    if lib_path.exists():
        lib_files = list(lib_path.glob("*.a"))
        if len(lib_files) == 0:
            return False
    
    # Verificar se há arquivos de include
    inc_path = sgdk_path / "inc"
    if inc_path.exists():
        inc_files = list(inc_path.glob("*.h"))
        if len(inc_files) < 5:  # Deve ter pelo menos alguns headers
            return False
    
    return True
'''
    
    # Adicionar ao arquivo do manager
    manager_file = Path("core/retro_devkit_manager.py")
    with open(manager_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Adicionar a função antes da classe RetroDevKitManager
    if "def verify_sgdk_installation" not in content:
        insertion_point = content.find("class RetroDevKitManager:")
        if insertion_point != -1:
            new_content = content[:insertion_point] + verification_code + "\n\n" + content[insertion_point:]
            
            with open(manager_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info("✅ Função de verificação SGDK adicionada")
        else:
            logger.error("❌ Não foi possível encontrar a classe RetroDevKitManager")
    else:
        logger.info("ℹ️ Função de verificação SGDK já existe")

def test_fixed_detection():
    """Testa o sistema de detecção corrigido"""
    logger.info("🧪 Testando sistema de detecção corrigido...")
    
    try:
        # Recarregar módulo
        if 'core.retro_devkit_manager' in sys.modules:
            del sys.modules['core.retro_devkit_manager']
        
        from core.retro_devkit_manager import RetroDevKitManager
        
        manager = RetroDevKitManager()
        status = manager.get_installation_status()
        
        logger.info("📊 Status após correções:")
        for devkit_id, is_installed in status.items():
            logger.info(f"  {'✅' if is_installed else '❌'} {devkit_id}: {'Instalado' if is_installed else 'Não instalado'}")
        
        # Verificar especificamente o SGDK
        if 'megadrive' in status:
            sgdk_status = status['megadrive']
            logger.info(f"\n🎯 SGDK Status: {'INSTALADO' if sgdk_status else 'NÃO INSTALADO'}")
            
            # Se ainda não está detectado, verificar manualmente
            if not sgdk_status:
                logger.info("🔍 Verificação manual do SGDK...")
                sgdk_path = Path("C:/Users/misae/RetroDevKits/retro_devkits/sgdk")
                
                if sgdk_path.exists():
                    logger.info(f"✅ Diretório SGDK existe: {sgdk_path}")
                    
                    # Verificar conteúdo
                    subdirs = [d for d in sgdk_path.iterdir() if d.is_dir()]
                    files = [f for f in sgdk_path.iterdir() if f.is_file()]
                    
                    logger.info(f"📁 Subdiretórios: {[d.name for d in subdirs]}")
                    logger.info(f"📄 Arquivos: {[f.name for f in files[:10]]}...")  # Primeiros 10
                    
                    # Verificar se parece ser código fonte vs. binários compilados
                    has_makefile = (sgdk_path / "makefile.gen").exists()
                    has_src = (sgdk_path / "src").exists()
                    has_inc = (sgdk_path / "inc").exists()
                    has_bin = (sgdk_path / "bin").exists() and len(list((sgdk_path / "bin").iterdir())) > 0
                    
                    logger.info(f"📋 Análise do SGDK:")
                    logger.info(f"  - Makefile: {'✅' if has_makefile else '❌'}")
                    logger.info(f"  - Diretório src: {'✅' if has_src else '❌'}")
                    logger.info(f"  - Diretório inc: {'✅' if has_inc else '❌'}")
                    logger.info(f"  - Diretório bin (com conteúdo): {'✅' if has_bin else '❌'}")
                    
                    if has_makefile and has_src and has_inc and not has_bin:
                        logger.warning("⚠️ SGDK parece ser código fonte não compilado!")
                        logger.info("💡 Sugestão: Execute a compilação do SGDK")
                else:
                    logger.error(f"❌ Diretório SGDK não encontrado: {sgdk_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao testar detecção: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    logger.info("🔧 CORREÇÃO DO SISTEMA DE DETECÇÃO DE DEVKITS")
    logger.info("=" * 50)
    
    # Aplicar correções
    if fix_retro_devkit_manager():
        logger.info("✅ RetroDevKitManager corrigido")
    else:
        logger.error("❌ Falha ao corrigir RetroDevKitManager")
        return
    
    # Adicionar verificação melhorada
    create_improved_sgdk_verification()
    
    # Testar correções
    logger.info("\n" + "=" * 50)
    test_fixed_detection()
    
    logger.info("\n" + "=" * 50)
    logger.info("✅ Correções aplicadas!")
    
    logger.info("\n💡 PRÓXIMOS PASSOS:")
    logger.info("1. Se SGDK aparece como código fonte não compilado, execute a compilação")
    logger.info("2. Instale extensões VSCode manualmente se necessário")
    logger.info("3. Configure emuladores para teste")
    logger.info("4. Teste a criação de um projeto SGDK")

if __name__ == "__main__":
    main()