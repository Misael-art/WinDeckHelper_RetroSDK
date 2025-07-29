#!/usr/bin/env python3
"""
Script principal para executar todas as melhorias do projeto.

Este script coordena a execução de:
1. Atualização de hashes pendentes
2. Validação e correção de URLs
3. Migração de componentes legados
4. Validação de configurações
5. Geração de relatório consolidado

Uso: python run_improvements.py [--dry-run] [--skip-urls] [--skip-migration] [--fix-minor]
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Adiciona o diretório raiz ao path para importar módulos do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

from env_dev.utils.log_manager import LogManager

class ProjectImprovementRunner:
    def __init__(self, dry_run: bool = False, skip_urls: bool = False, 
                 skip_migration: bool = False, fix_minor: bool = False):
        self.dry_run = dry_run
        self.skip_urls = skip_urls
        self.skip_migration = skip_migration
        self.fix_minor = fix_minor
        
        self.logger = LogManager().get_logger("ImprovementRunner")
        self.project_root = Path(__file__).parent.parent
        self.tools_dir = Path(__file__).parent
        
        # Resultados de cada etapa
        self.results = {
            'hash_update': {'success': False, 'message': ''},
            'url_validation': {'success': False, 'message': ''},
            'legacy_migration': {'success': False, 'message': ''},
            'config_validation': {'success': False, 'message': ''}
        }
        
        # Scripts disponíveis
        self.scripts = {
            'update_hashes': self.tools_dir / 'update_pending_hashes.py',
            'validate_urls': self.tools_dir / 'validate_component_urls.py',
            'migrate_legacy': self.tools_dir / 'migrate_legacy_components.py',
            'validate_configs': self.tools_dir / 'validate_component_configs.py'
        }
    
    def check_prerequisites(self) -> bool:
        """Verifica se todos os scripts necessários existem"""
        missing_scripts = []
        
        for script_name, script_path in self.scripts.items():
            if not script_path.exists():
                missing_scripts.append(script_name)
        
        if missing_scripts:
            self.logger.error(f"Scripts não encontrados: {', '.join(missing_scripts)}")
            return False
        
        return True
    
    def run_script(self, script_path: Path, args: List[str] = None) -> Dict:
        """Executa um script Python e retorna o resultado"""
        if args is None:
            args = []
        
        cmd = [sys.executable, str(script_path)] + args
        
        try:
            self.logger.info(f"Executando: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=300  # 5 minutos de timeout
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Script timeout (5 minutos)',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
    
    def step_1_update_hashes(self) -> bool:
        """Etapa 1: Atualiza hashes pendentes"""
        self.logger.info("=" * 60)
        self.logger.info("ETAPA 1: Atualizando hashes pendentes")
        self.logger.info("=" * 60)
        
        args = []
        if self.dry_run:
            args.append('--dry-run')
        
        result = self.run_script(self.scripts['update_hashes'], args)
        
        self.results['hash_update']['success'] = result['success']
        
        if result['success']:
            self.results['hash_update']['message'] = "Hashes atualizados com sucesso"
            self.logger.success("✅ Hashes atualizados com sucesso")
        else:
            self.results['hash_update']['message'] = f"Erro: {result['stderr']}"
            self.logger.error(f"❌ Erro ao atualizar hashes: {result['stderr']}")
        
        if result['stdout']:
            self.logger.info("Saída do script:")
            print(result['stdout'])
        
        return result['success']
    
    def step_2_validate_urls(self) -> bool:
        """Etapa 2: Valida e corrige URLs"""
        if self.skip_urls:
            self.logger.info("Pulando validação de URLs (--skip-urls)")
            self.results['url_validation']['success'] = True
            self.results['url_validation']['message'] = "Pulado pelo usuário"
            return True
        
        self.logger.info("=" * 60)
        self.logger.info("ETAPA 2: Validando URLs de download")
        self.logger.info("=" * 60)
        
        args = ['--timeout', '15']  # Timeout menor para não demorar muito
        if not self.dry_run:  # Só corrige se não for dry run
            args.append('--fix')
        
        result = self.run_script(self.scripts['validate_urls'], args)
        
        self.results['url_validation']['success'] = result['success']
        
        if result['success']:
            self.results['url_validation']['message'] = "URLs validadas com sucesso"
            self.logger.success("✅ URLs validadas com sucesso")
        else:
            self.results['url_validation']['message'] = f"Erro: {result['stderr']}"
            self.logger.error(f"❌ Erro ao validar URLs: {result['stderr']}")
        
        if result['stdout']:
            self.logger.info("Saída do script:")
            print(result['stdout'])
        
        return result['success']
    
    def step_3_migrate_legacy(self) -> bool:
        """Etapa 3: Migra componentes legados"""
        if self.skip_migration:
            self.logger.info("Pulando migração de componentes legados (--skip-migration)")
            self.results['legacy_migration']['success'] = True
            self.results['legacy_migration']['message'] = "Pulado pelo usuário"
            return True
        
        self.logger.info("=" * 60)
        self.logger.info("ETAPA 3: Migrando componentes legados")
        self.logger.info("=" * 60)
        
        args = []
        if self.dry_run:
            args.append('--dry-run')
        
        result = self.run_script(self.scripts['migrate_legacy'], args)
        
        self.results['legacy_migration']['success'] = result['success']
        
        if result['success']:
            self.results['legacy_migration']['message'] = "Componentes migrados com sucesso"
            self.logger.success("✅ Componentes migrados com sucesso")
        else:
            self.results['legacy_migration']['message'] = f"Erro: {result['stderr']}"
            self.logger.error(f"❌ Erro ao migrar componentes: {result['stderr']}")
        
        if result['stdout']:
            self.logger.info("Saída do script:")
            print(result['stdout'])
        
        return result['success']
    
    def step_4_validate_configs(self) -> bool:
        """Etapa 4: Valida configurações"""
        self.logger.info("=" * 60)
        self.logger.info("ETAPA 4: Validando configurações")
        self.logger.info("=" * 60)
        
        args = []
        if self.fix_minor:
            args.append('--fix-minor')
        
        result = self.run_script(self.scripts['validate_configs'], args)
        
        self.results['config_validation']['success'] = result['success']
        
        if result['success']:
            self.results['config_validation']['message'] = "Configurações validadas com sucesso"
            self.logger.success("✅ Configurações validadas com sucesso")
        else:
            self.results['config_validation']['message'] = f"Problemas encontrados: {result['stderr']}"
            self.logger.warning(f"⚠️ Problemas encontrados na validação: {result['stderr']}")
        
        if result['stdout']:
            self.logger.info("Saída do script:")
            print(result['stdout'])
        
        return result['success']
    
    def generate_consolidated_report(self) -> str:
        """Gera um relatório consolidado de todas as melhorias"""
        report = []
        report.append("=" * 80)
        report.append("RELATÓRIO CONSOLIDADO DE MELHORIAS DO PROJETO")
        report.append("=" * 80)
        report.append(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Modo: {'DRY RUN' if self.dry_run else 'EXECUÇÃO REAL'}")
        report.append("")
        
        # Resumo geral
        total_steps = len(self.results)
        successful_steps = sum(1 for r in self.results.values() if r['success'])
        
        report.append("RESUMO GERAL:")
        report.append(f"Total de etapas: {total_steps}")
        report.append(f"Etapas bem-sucedidas: {successful_steps}")
        report.append(f"Taxa de sucesso: {successful_steps/total_steps*100:.1f}%")
        report.append("")
        
        # Detalhes de cada etapa
        step_names = {
            'hash_update': 'Atualização de Hashes',
            'url_validation': 'Validação de URLs',
            'legacy_migration': 'Migração de Componentes Legados',
            'config_validation': 'Validação de Configurações'
        }
        
        report.append("DETALHES DAS ETAPAS:")
        report.append("-" * 40)
        
        for step_key, step_name in step_names.items():
            result = self.results[step_key]
            status = "✅ SUCESSO" if result['success'] else "❌ FALHA"
            
            report.append(f"{step_name}: {status}")
            report.append(f"  Mensagem: {result['message']}")
            report.append("")
        
        # Recomendações
        report.append("RECOMENDAÇÕES:")
        report.append("-" * 40)
        
        if not self.results['hash_update']['success']:
            report.append("- Execute manualmente: python tools/update_pending_hashes.py")
        
        if not self.results['url_validation']['success'] and not self.skip_urls:
            report.append("- Verifique URLs problemáticas no relatório url_validation_report.txt")
        
        if not self.results['legacy_migration']['success'] and not self.skip_migration:
            report.append("- Execute manualmente: python tools/migrate_legacy_components.py")
        
        if not self.results['config_validation']['success']:
            report.append("- Corrija os problemas listados no relatório validation_report.txt")
        
        if all(r['success'] for r in self.results.values()):
            report.append("- Todas as melhorias foram aplicadas com sucesso!")
            report.append("- Execute os testes do sistema para verificar se tudo está funcionando")
            report.append("- Considere fazer commit das alterações no controle de versão")
        
        report.append("")
        report.append("PRÓXIMOS PASSOS SUGERIDOS:")
        report.append("- Implementar testes automatizados")
        report.append("- Melhorar documentação de troubleshooting")
        report.append("- Expandir suporte para mais distribuições Linux")
        report.append("- Implementar sistema de rollback mais robusto")
        
        return "\n".join(report)
    
    def run(self) -> bool:
        """Executa todas as melhorias"""
        self.logger.info("Iniciando execução de melhorias do projeto...")
        
        if not self.check_prerequisites():
            return False
        
        if self.dry_run:
            self.logger.info("MODO DRY RUN - Nenhuma alteração será feita")
        
        # Executa cada etapa
        steps = [
            self.step_1_update_hashes,
            self.step_2_validate_urls,
            self.step_3_migrate_legacy,
            self.step_4_validate_configs
        ]
        
        for i, step in enumerate(steps, 1):
            try:
                step()
            except Exception as e:
                self.logger.error(f"Erro inesperado na etapa {i}: {e}")
                # Continua com as próximas etapas mesmo se uma falhar
        
        # Gera relatório consolidado
        report = self.generate_consolidated_report()
        
        report_file = self.project_root / "improvement_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"Relatório consolidado salvo em: {report_file}")
        
        # Exibe resumo final
        successful_steps = sum(1 for r in self.results.values() if r['success'])
        total_steps = len(self.results)
        
        print("\n" + "=" * 60)
        print("RESUMO FINAL DAS MELHORIAS")
        print("=" * 60)
        print(f"Etapas executadas: {total_steps}")
        print(f"Etapas bem-sucedidas: {successful_steps}")
        print(f"Taxa de sucesso: {successful_steps/total_steps*100:.1f}%")
        
        if successful_steps == total_steps:
            print("\n🎉 Todas as melhorias foram aplicadas com sucesso!")
        else:
            print(f"\n⚠️ {total_steps - successful_steps} etapa(s) falharam. Verifique o relatório.")
        
        return successful_steps == total_steps

def main():
    parser = argparse.ArgumentParser(description="Executa todas as melhorias do projeto")
    parser.add_argument('--dry-run', action='store_true', 
                       help="Executa sem fazer alterações (apenas simula)")
    parser.add_argument('--skip-urls', action='store_true', 
                       help="Pula a validação de URLs (pode ser demorada)")
    parser.add_argument('--skip-migration', action='store_true', 
                       help="Pula a migração de componentes legados")
    parser.add_argument('--fix-minor', action='store_true', 
                       help="Corrige problemas menores automaticamente")
    
    args = parser.parse_args()
    
    runner = ProjectImprovementRunner(
        dry_run=args.dry_run,
        skip_urls=args.skip_urls,
        skip_migration=args.skip_migration,
        fix_minor=args.fix_minor
    )
    
    success = runner.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()