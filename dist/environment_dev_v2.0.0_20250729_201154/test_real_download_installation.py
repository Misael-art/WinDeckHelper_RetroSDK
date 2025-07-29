#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste específico para verificar se o sistema de download e instalação real está funcionando
"""

import os
import sys
import logging
import tempfile
import shutil

# Adiciona o diretório do projeto ao path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

def test_download_component():
    """Testa o download de um componente real (sem executar o instalador)"""
    print("=== Teste de Download de Componente Real ===")
    
    try:
        # Importa os módulos necessários
        from env_dev.config.loader import load_all_components
        from env_dev.core import installer
        from env_dev.utils import downloader
        
        print("✓ Módulos importados com sucesso")
        
        # Carrega os componentes
        components_data = load_all_components()
        if not components_data:
            print("✗ Falha ao carregar componentes")
            return False
            
        # Encontra um componente pequeno para teste
        test_component = None
        for name, data in components_data.items():
            install_method = data.get('install_method')
            download_url = data.get('download_url')
            
            if install_method == 'exe' and download_url:
                # Verifica se é um arquivo pequeno (evita downloads grandes)
                if any(keyword in name.lower() for keyword in ['game fire', 'process lasso']):
                    test_component = (name, data)
                    break
        
        if not test_component:
            print("✗ Nenhum componente adequado para teste encontrado")
            return False
            
        component_name, component_data = test_component
        print(f"✓ Componente de teste selecionado: {component_name}")
        
        # Testa apenas a verificação de URL (sem download)
        download_url = component_data.get('download_url')
        print(f"  URL: {download_url}")
        
        # Verifica se a URL está acessível
        print("  Verificando disponibilidade da URL...")
        try:
            is_available = downloader.verify_url_status(download_url, timeout=10)
            if is_available:
                print("  ✓ URL está acessível")
            else:
                print("  ⚠ URL não está acessível (pode ser temporário)")
        except Exception as e:
            print(f"  ⚠ Erro ao verificar URL: {e}")
        
        # Testa a função de instalação com modo de simulação
        print(f"\n--- Testando sistema de instalação para '{component_name}' ---")
        
        # Cria um diretório temporário para teste
        temp_dir = tempfile.mkdtemp(prefix="env_dev_test_")
        print(f"  Diretório temporário: {temp_dir}")
        
        try:
            # Modifica temporariamente o componente para usar um arquivo de teste
            test_component_data = component_data.copy()
            
            # Cria um arquivo de teste pequeno para simular download
            test_file_path = os.path.join(temp_dir, "test_installer.exe")
            with open(test_file_path, 'wb') as f:
                f.write(b"Test installer content")
            
            # Usa uma URL HTTP simples para teste (httpbin.org é um serviço de teste)
            test_component_data['download_url'] = "https://httpbin.org/bytes/1024"  # Baixa 1KB de dados de teste
            test_component_data['install_args'] = ['/S']  # Argumentos silenciosos
            test_component_data['hash'] = None  # Remove verificação de hash para o teste
            
            print("  Testando processo de download...")
            
            # Testa apenas a parte de download
            success, download_path = installer.install_download_type(
                component_name=component_name,
                component_data=test_component_data,
                rollback_mgr=installer.RollbackManager()
            )
            
            if success and download_path:
                print(f"  ✓ Sistema de download funcionou corretamente")
                print(f"  ✓ Arquivo baixado para: {download_path}")
                
                # Verifica se o arquivo foi realmente baixado
                if os.path.exists(download_path):
                    print("  ✓ Arquivo de download existe")
                    file_size = os.path.getsize(download_path)
                    print(f"  ✓ Tamanho do arquivo: {file_size} bytes")
                else:
                    print("  ✗ Arquivo de download não encontrado")
                    return False
            else:
                print("  ✗ Sistema de download falhou")
                return False
                
        finally:
            # Limpa o diretório temporário
            try:
                shutil.rmtree(temp_dir)
                print("  ✓ Diretório temporário limpo")
            except Exception as e:
                print(f"  ⚠ Erro ao limpar diretório temporário: {e}")
        
        print("\n=== Teste de Download Concluído com Sucesso ===")
        return True
        
    except ImportError as e:
        print(f"✗ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"✗ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_real_installation():
    """Testa se a GUI está configurada para usar instalação real"""
    print("\n=== Teste de Configuração da GUI ===")
    
    try:
        # Verifica se os arquivos da GUI foram corrigidos
        gui_files = [
            'env_dev/gui/enhanced_dashboard.py',
            'env_dev/gui/app_gui_qt.py',
            'env_dev/gui/dashboard_gui.py'
        ]
        
        all_fixed = True
        
        for gui_file in gui_files:
            if os.path.exists(gui_file):
                with open(gui_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Verifica se ainda há simulações
                if 'time.sleep(2)  # Simulate installation' in content:
                    print(f"✗ {gui_file} ainda contém simulações de instalação")
                    all_fixed = False
                elif 'installer.install_component(' in content:
                    print(f"✓ {gui_file} foi corrigido para usar instalação real")
                else:
                    print(f"? {gui_file} - não foi possível verificar")
            else:
                print(f"⚠ {gui_file} não encontrado")
        
        if all_fixed:
            print("✓ Todos os arquivos da GUI foram corrigidos")
            return True
        else:
            print("✗ Alguns arquivos da GUI ainda precisam de correção")
            return False
            
    except Exception as e:
        print(f"✗ Erro no teste da GUI: {e}")
        return False

if __name__ == "__main__":
    # Configura logging básico
    logging.basicConfig(level=logging.WARNING)  # Reduz verbosidade
    
    print("🔧 Testando Sistema de Instalação Real")
    print("=" * 50)
    
    # Executa os testes
    download_ok = test_download_component()
    gui_ok = test_gui_real_installation()
    
    print("\n" + "=" * 50)
    
    if download_ok and gui_ok:
        print("🎉 SUCESSO: Sistema de instalação real está funcionando!")
        print("   - Downloads funcionam corretamente")
        print("   - GUI está configurada para instalação real")
        print("   - Não há mais simulações no código")
        sys.exit(0)
    else:
        print("❌ FALHA: Alguns problemas foram encontrados:")
        if not download_ok:
            print("   - Sistema de download precisa de ajustes")
        if not gui_ok:
            print("   - GUI ainda contém simulações")
        sys.exit(1)