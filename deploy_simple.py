#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deploy Simple - Script Simplificado de Deployment
Versão simplificada sem emojis para compatibilidade com Windows.
"""

import os
import sys
import subprocess
import logging
import time
from pathlib import Path
from datetime import datetime
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Deployment simplificado"""
    print("Environment Dev Deep Evaluation - Deployment Completo")
    print("=" * 60)
    print(f"Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    project_root = Path.cwd()
    deployment_dir = project_root / "deployment"
    
    # Verificar se o pacote já foi criado
    package_dir = deployment_dir / "EnvironmentDevDeepEvaluation_Portable"
    
    if package_dir.exists():
        print("\nPacote de deployment encontrado!")
        print(f"Localizacao: {package_dir}")
        
        # Verificar estrutura básica
        exe_dir = package_dir / "EnvironmentDevDeepEvaluation"
        exe_file = exe_dir / "EnvironmentDevDeepEvaluation.exe"
        
        if exe_file.exists():
            exe_size = exe_file.stat().st_size / (1024 * 1024)
            print(f"Executavel: {exe_file.name} ({exe_size:.1f} MB)")
        
        # Contar arquivos
        total_files = sum(1 for _ in package_dir.rglob('*') if _.is_file())
        total_size = sum(f.stat().st_size for f in package_dir.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        
        print(f"Total de arquivos: {total_files}")
        print(f"Tamanho total: {size_mb:.1f} MB")
        
        # Verificar componentes essenciais
        components = [
            ("Executavel", exe_dir.exists()),
            ("Configuracoes", (package_dir / "config").exists()),
            ("Documentacao", (package_dir / "docs").exists()),
            ("Script Windows", (package_dir / "Iniciar_Environment_Dev.bat").exists()),
            ("Script Linux/Mac", (package_dir / "iniciar_environment_dev.sh").exists()),
            ("Arquivo Info", (package_dir / "LEIA-ME.txt").exists()),
        ]
        
        print("\nComponentes do pacote:")
        all_ok = True
        for name, exists in components:
            status = "OK" if exists else "AUSENTE"
            print(f"  {name}: {status}")
            if not exists:
                all_ok = False
        
        # Gerar relatório final
        report = {
            "deployment_info": {
                "project": "Environment Dev Deep Evaluation",
                "version": "2.0.0",
                "timestamp": datetime.now().isoformat(),
                "package_location": str(package_dir)
            },
            "package_stats": {
                "total_files": total_files,
                "total_size_mb": round(size_mb, 1),
                "executable_size_mb": round(exe_size, 1) if exe_file.exists() else 0
            },
            "components": {name: exists for name, exists in components},
            "status": "success" if all_ok else "partial"
        }
        
        # Salvar relatório
        report_file = project_root / f"deployment_final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\nRelatorio salvo: {report_file}")
        
        if all_ok:
            print("\n" + "="*60)
            print("DEPLOYMENT CONCLUIDO COM SUCESSO!")
            print("="*60)
            print(f"Pacote: Environment Dev Deep Evaluation v2.0")
            print(f"Localizacao: {package_dir}")
            print(f"Tamanho: {size_mb:.1f} MB")
            print("\nComo usar:")
            print("1. Windows: Execute 'Iniciar_Environment_Dev.bat'")
            print("2. Linux/Mac: Execute './iniciar_environment_dev.sh'")
            print("3. Ou execute diretamente o executavel")
            print("\nO pacote esta pronto para distribuicao!")
            return True
        else:
            print("\nALGUNS COMPONENTES ESTAO AUSENTES!")
            print("Verifique os itens marcados como 'AUSENTE' acima.")
            return False
    else:
        print("\nPacote de deployment nao encontrado!")
        print("Execute primeiro: python build_deployment.py")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)