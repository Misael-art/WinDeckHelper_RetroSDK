#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste Rápido do SGDK - Environment Dev

Script simplificado para verificação rápida do SGDK e dependências críticas.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def test_java():
    """Teste rápido do Java"""
    print("☕ Testando Java...")
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("   ✅ Java instalado e funcionando")
            # Verificar JAVA_HOME
            java_home = os.environ.get('JAVA_HOME')
            if java_home:
                print(f"   ✅ JAVA_HOME: {java_home}")
            else:
                print("   ⚠️ JAVA_HOME não configurado")
            return True
        else:
            print("   ❌ Java não funciona corretamente")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("   ❌ Java não encontrado")
        return False

def test_make():
    """Teste rápido do Make"""
    print("🔨 Testando Make...")
    try:
        result = subprocess.run(['make', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("   ✅ Make instalado e funcionando")
            return True
        else:
            print("   ❌ Make não funciona corretamente")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("   ❌ Make não encontrado")
        return False

def test_sgdk():
    """Teste rápido do SGDK"""
    print("🎮 Testando SGDK...")
    
    # Verificar SGDK_HOME
    sgdk_home = os.environ.get('SGDK_HOME')
    if not sgdk_home:
        print("   ❌ SGDK_HOME não configurado")
        return False
    
    sgdk_path = Path(sgdk_home)
    if not sgdk_path.exists():
        print(f"   ❌ Diretório SGDK não existe: {sgdk_home}")
        return False
    
    print(f"   ✅ SGDK_HOME: {sgdk_home}")
    
    # Verificar estrutura básica
    required_dirs = ['bin', 'inc', 'lib']
    missing_dirs = []
    
    for dir_name in required_dirs:
        if not (sgdk_path / dir_name).exists():
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"   ❌ Diretórios ausentes: {', '.join(missing_dirs)}")
        return False
    
    print("   ✅ Estrutura de diretórios OK")
    
    # Verificar alguns arquivos importantes
    important_files = [
        'inc/genesis.h',
        'lib/libmd.a' if platform.system() != 'Windows' else 'lib/libmd.lib'
    ]
    
    for file_path in important_files:
        if (sgdk_path / file_path).exists():
            print(f"   ✅ {file_path} encontrado")
        else:
            print(f"   ⚠️ {file_path} não encontrado")
    
    return True

def test_compilation():
    """Teste de compilação simples"""
    print("🔨 Testando compilação simples...")
    
    sgdk_home = os.environ.get('SGDK_HOME')
    if not sgdk_home:
        print("   ❌ SGDK_HOME necessário para teste de compilação")
        return False
    
    # Criar arquivo de teste temporário
    test_dir = Path.cwd() / 'temp_test'
    test_dir.mkdir(exist_ok=True)
    
    test_file = test_dir / 'hello.c'
    test_content = '''
#include <genesis.h>

int main() {
    VDP_drawText("Hello World!", 1, 1);
    return 0;
}
'''
    
    try:
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Tentar compilar usando gcc diretamente (mais simples)
        gcc_cmd = [
            'gcc',
            '-I', str(Path(sgdk_home) / 'inc'),
            '-c',
            str(test_file),
            '-o', str(test_dir / 'hello.o')
        ]
        
        result = subprocess.run(gcc_cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("   ✅ Compilação de teste bem-sucedida")
            success = True
        else:
            print("   ❌ Falha na compilação de teste")
            if result.stderr:
                print(f"   Erro: {result.stderr[:100]}...")
            success = False
            
    except Exception as e:
        print(f"   ❌ Erro no teste de compilação: {e}")
        success = False
    finally:
        # Limpar arquivos temporários
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)
    
    return success

def main():
    """Função principal do teste rápido"""
    print("🚀 TESTE RÁPIDO DO SGDK")
    print("=" * 40)
    
    # Informações básicas
    print(f"Sistema: {platform.system()} {platform.architecture()[0]}")
    print(f"Python: {platform.python_version()}")
    print("")
    
    # Testes das dependências
    java_ok = test_java()
    make_ok = test_make()
    sgdk_ok = test_sgdk()
    
    print("")
    print("📋 RESUMO:")
    print("-" * 20)
    
    deps_ok = java_ok and make_ok
    
    if deps_ok and sgdk_ok:
        print("✅ SGDK e dependências: OK")
        print("🎮 Pronto para desenvolvimento!")
        
        # Teste opcional de compilação
        print("")
        compile_ok = test_compilation()
        if compile_ok:
            print("🏆 Sistema totalmente funcional!")
        else:
            print("⚠️ SGDK instalado, mas compilação pode ter problemas")
            
        return True
    else:
        print("❌ Problemas detectados:")
        if not java_ok:
            print("   - Java não instalado/configurado")
        if not make_ok:
            print("   - Make não instalado/configurado")
        if not sgdk_ok:
            print("   - SGDK não instalado/configurado")
        
        print("")
        print("🔧 Execute o Environment Dev para instalar os componentes")
        return False

if __name__ == '__main__':
    success = main()
    print("")
    if success:
        print("🎉 Teste concluído com sucesso!")
    else:
        print("⚠️ Teste detectou problemas que precisam ser corrigidos.")
    
    input("\nPressione Enter para sair...")
    sys.exit(0 if success else 1)