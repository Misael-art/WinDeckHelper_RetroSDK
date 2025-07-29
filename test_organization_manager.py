#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes para o Organization Manager
Verifica funcionalidades de limpeza, organização e otimização
"""

import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Adicionar o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from env_dev.core.organization_manager import (
    OrganizationManager, CleanupStatus, FileType,
    CleanupResult, OrganizationResult, BackupManagementResult, OptimizationResult
)

class TestOrganizationManager(unittest.TestCase):
    """Testes para o OrganizationManager"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = OrganizationManager(self.test_dir)
        
        # Criar estrutura de diretórios de teste
        self.temp_dir = self.test_dir / "temp"
        self.downloads_dir = self.test_dir / "downloads"
        self.logs_dir = self.test_dir / "logs"
        self.backups_dir = self.test_dir / "backups"
        self.cache_dir = self.test_dir / "cache"
        
        for dir_path in [self.temp_dir, self.downloads_dir, self.logs_dir, 
                        self.backups_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """Limpeza após cada teste"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_cleanup_temporary_files(self):
        """Testa limpeza de arquivos temporários"""
        # Criar arquivos temporários de teste
        old_temp_file = self.temp_dir / "old_file.tmp"
        recent_temp_file = self.temp_dir / "recent_file.tmp"
        
        # Arquivo antigo (2 dias atrás)
        old_temp_file.write_text("conteúdo antigo")
        old_time = datetime.now() - timedelta(days=2)
        os.utime(old_temp_file, (old_time.timestamp(), old_time.timestamp()))
        
        # Arquivo recente
        recent_temp_file.write_text("conteúdo recente")
        
        # Executar limpeza
        result = self.manager.cleanup_temporary_files()
        
        # Verificar resultado
        self.assertEqual(result.status, CleanupStatus.COMPLETED)
        self.assertGreater(result.files_removed, 0)
        self.assertGreater(result.space_freed, 0)
        
        # Verificar que arquivo antigo foi removido e recente mantido
        self.assertFalse(old_temp_file.exists())
        self.assertTrue(recent_temp_file.exists())
    
    def test_organize_downloads(self):
        """Testa organização de downloads"""
        # Criar arquivos de teste em downloads
        test_files = [
            ("installer.exe", "installers"),
            ("document.pdf", "documents"),
            ("archive.zip", "archives"),
            ("driver.inf", "drivers"),
            ("image.png", "images"),
            ("unknown.xyz", "others")
        ]
        
        for filename, expected_category in test_files:
            file_path = self.downloads_dir / filename
            file_path.write_text(f"conteúdo de {filename}")
        
        # Executar organização
        result = self.manager.organize_downloads()
        
        # Verificar resultado
        self.assertEqual(result.status, CleanupStatus.COMPLETED)
        self.assertEqual(result.files_moved, len(test_files))
        self.assertGreater(result.directories_created, 0)
        
        # Verificar que arquivos foram movidos para categorias corretas
        for filename, expected_category in test_files:
            category_dir = self.downloads_dir / expected_category
            self.assertTrue(category_dir.exists())
            
            # Arquivo deve estar em subdiretório por data
            found = False
            for date_dir in category_dir.iterdir():
                if date_dir.is_dir():
                    target_file = date_dir / filename
                    if target_file.exists():
                        found = True
                        break
            
            self.assertTrue(found, f"Arquivo {filename} não encontrado na categoria {expected_category}")
    
    def test_rotate_logs(self):
        """Testa rotação de logs"""
        # Criar logs de teste
        old_log = self.logs_dir / "old.log"
        recent_log = self.logs_dir / "recent.log"
        json_log = self.logs_dir / "data.json"
        
        # Log antigo (35 dias atrás)
        old_log.write_text("log antigo")
        old_time = datetime.now() - timedelta(days=35)
        os.utime(old_log, (old_time.timestamp(), old_time.timestamp()))
        
        # Log recente
        recent_log.write_text("log recente")
        json_log.write_text('{"data": "json"}')
        
        # Executar rotação
        result = self.manager.rotate_logs()
        
        # Verificar resultado
        self.assertEqual(result.status, CleanupStatus.COMPLETED)
        self.assertGreater(result.files_removed, 0)
        
        # Verificar que log antigo foi arquivado
        self.assertFalse(old_log.exists())
        self.assertTrue(recent_log.exists())
        
        # Verificar que arquivo foi para diretório archived
        archived_dir = self.logs_dir / "archived"
        self.assertTrue(archived_dir.exists())
    
    def test_manage_backups(self):
        """Testa gerenciamento de backups"""
        # Criar backups de teste
        old_backup_name = f"backup_{(datetime.now() - timedelta(days=100)).strftime('%Y%m%d_%H%M%S')}_test"
        recent_backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_test"
        
        old_backup_dir = self.backups_dir / old_backup_name
        recent_backup_dir = self.backups_dir / recent_backup_name
        
        old_backup_dir.mkdir()
        recent_backup_dir.mkdir()
        
        # Adicionar arquivos aos backups
        (old_backup_dir / "file1.txt").write_text("conteúdo 1")
        (recent_backup_dir / "file2.txt").write_text("conteúdo 2")
        
        # Executar gerenciamento
        result = self.manager.manage_backups()
        
        # Verificar resultado
        self.assertEqual(result.status, CleanupStatus.COMPLETED)
        self.assertGreater(result.backups_processed, 0)
        
        # Backup antigo deve ter sido removido
        self.assertFalse(old_backup_dir.exists())
        # Backup recente deve existir
        self.assertTrue(recent_backup_dir.exists())
    
    def test_optimize_disk_usage(self):
        """Testa otimização completa de disco"""
        # Criar arquivos de teste em vários diretórios
        (self.temp_dir / "temp.tmp").write_text("arquivo temporário")
        (self.downloads_dir / "download.exe").write_text("download")
        (self.logs_dir / "old.log").write_text("log antigo")
        
        # Tornar log antigo
        old_log = self.logs_dir / "old.log"
        old_time = datetime.now() - timedelta(days=35)
        os.utime(old_log, (old_time.timestamp(), old_time.timestamp()))
        
        # Executar otimização
        result = self.manager.optimize_disk_usage()
        
        # Verificar resultado
        self.assertEqual(result.status, CleanupStatus.COMPLETED)
        self.assertGreater(len(result.operations_performed), 0)
        self.assertGreaterEqual(result.total_space_freed, 0)
        
        # Verificar que operações foram executadas
        expected_operations = [
            "Limpeza de temporários",
            "Rotação de logs", 
            "Gerenciamento de backups"
        ]
        
        for operation in expected_operations:
            self.assertIn(operation, result.operations_performed)
    
    def test_get_file_category(self):
        """Testa categorização de arquivos"""
        categories = {
            'installers': ['.exe', '.msi'],
            'documents': ['.pdf', '.txt'],
            'others': []
        }
        
        # Testes de categorização
        test_cases = [
            (Path("test.exe"), "installers"),
            (Path("doc.pdf"), "documents"),
            (Path("unknown.xyz"), "others")
        ]
        
        for file_path, expected_category in test_cases:
            category = self.manager._get_file_category(file_path, categories)
            self.assertEqual(category, expected_category)
    
    def test_extract_backup_date(self):
        """Testa extração de data de backup"""
        # Casos válidos
        valid_cases = [
            ("backup_20250128_143000_test", datetime(2025, 1, 28, 14, 30, 0)),
            ("backup_20241225_120000_config", datetime(2024, 12, 25, 12, 0, 0))
        ]
        
        for backup_name, expected_date in valid_cases:
            extracted_date = self.manager._extract_backup_date(backup_name)
            self.assertEqual(extracted_date, expected_date)
        
        # Casos inválidos
        invalid_cases = [
            "invalid_backup_name",
            "backup_invalid_date",
            "not_a_backup"
        ]
        
        for backup_name in invalid_cases:
            extracted_date = self.manager._extract_backup_date(backup_name)
            self.assertIsNone(extracted_date)
    
    def test_directory_size_calculation(self):
        """Testa cálculo de tamanho de diretório"""
        test_dir = self.test_dir / "size_test"
        test_dir.mkdir()
        
        # Criar arquivos de tamanhos conhecidos
        file1 = test_dir / "file1.txt"
        file2 = test_dir / "file2.txt"
        
        content1 = "a" * 100  # 100 bytes
        content2 = "b" * 200  # 200 bytes
        
        file1.write_text(content1)
        file2.write_text(content2)
        
        # Calcular tamanho
        calculated_size = self.manager._get_directory_size(test_dir)
        expected_size = len(content1.encode()) + len(content2.encode())
        
        self.assertEqual(calculated_size, expected_size)
    
    def test_error_handling(self):
        """Testa tratamento de erros"""
        # Testar com diretório inexistente
        non_existent_manager = OrganizationManager(Path("/caminho/inexistente"))
        
        # Operações devem falhar graciosamente
        result = non_existent_manager.cleanup_temporary_files()
        self.assertIn(result.status, [CleanupStatus.COMPLETED, CleanupStatus.SKIPPED])
        
        result = non_existent_manager.rotate_logs()
        self.assertEqual(result.status, CleanupStatus.SKIPPED)
    
    @patch('env_dev.core.organization_manager.get_disk_space')
    def test_optimization_recommendations(self, mock_disk_space):
        """Testa geração de recomendações"""
        # Simular pouco espaço em disco
        mock_disk_space.return_value = {'free_percent': 5}
        
        result = self.manager.optimize_disk_usage()
        
        # Deve haver recomendação sobre espaço baixo
        self.assertTrue(any("espaço em disco baixo" in rec.lower() 
                          for rec in result.recommendations))
    
    def test_cleanup_result_dataclass(self):
        """Testa estrutura de dados CleanupResult"""
        result = CleanupResult(status=CleanupStatus.COMPLETED)
        
        # Verificar valores padrão
        self.assertEqual(result.files_removed, 0)
        self.assertEqual(result.directories_removed, 0)
        self.assertEqual(result.space_freed, 0)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])
        self.assertIsInstance(result.timestamp, datetime)
    
    def test_organization_result_dataclass(self):
        """Testa estrutura de dados OrganizationResult"""
        result = OrganizationResult(status=CleanupStatus.IN_PROGRESS)
        
        # Verificar valores padrão
        self.assertEqual(result.files_organized, 0)
        self.assertEqual(result.directories_created, 0)
        self.assertEqual(result.files_moved, 0)
        self.assertIsInstance(result.timestamp, datetime)


class TestOrganizationManagerIntegration(unittest.TestCase):
    """Testes de integração para o OrganizationManager"""
    
    def setUp(self):
        """Configuração para testes de integração"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = OrganizationManager(self.test_dir)
    
    def tearDown(self):
        """Limpeza após testes"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_full_workflow(self):
        """Testa fluxo completo de organização"""
        # Criar cenário realista
        self._create_realistic_scenario()
        
        # Executar operações em sequência
        temp_result = self.manager.cleanup_temporary_files()
        org_result = self.manager.organize_downloads()
        log_result = self.manager.rotate_logs()
        backup_result = self.manager.manage_backups()
        opt_result = self.manager.optimize_disk_usage()
        
        # Verificar que todas as operações foram bem-sucedidas
        results = [temp_result, org_result, log_result, backup_result, opt_result]
        
        for result in results:
            self.assertIn(result.status, [CleanupStatus.COMPLETED, CleanupStatus.SKIPPED])
        
        # Verificar que otimização executou todas as operações
        self.assertGreaterEqual(len(opt_result.operations_performed), 3)
    
    def _create_realistic_scenario(self):
        """Cria cenário realista para testes"""
        # Criar estrutura de diretórios
        dirs = ['temp', 'downloads', 'logs', 'backups', 'cache']
        for dir_name in dirs:
            (self.test_dir / dir_name).mkdir(parents=True, exist_ok=True)
        
        # Arquivos temporários
        temp_dir = self.test_dir / "temp"
        (temp_dir / "old.tmp").write_text("arquivo temporário antigo")
        (temp_dir / "recent.cache").write_text("cache recente")
        
        # Downloads diversos
        downloads_dir = self.test_dir / "downloads"
        (downloads_dir / "installer.exe").write_text("instalador")
        (downloads_dir / "document.pdf").write_text("documento")
        (downloads_dir / "archive.zip").write_text("arquivo compactado")
        
        # Logs de diferentes idades
        logs_dir = self.test_dir / "logs"
        old_log = logs_dir / "old.log"
        old_log.write_text("log antigo")
        old_time = datetime.now() - timedelta(days=35)
        os.utime(old_log, (old_time.timestamp(), old_time.timestamp()))
        
        (logs_dir / "recent.log").write_text("log recente")
        
        # Backups antigos e recentes
        backups_dir = self.test_dir / "backups"
        old_backup = backups_dir / f"backup_{(datetime.now() - timedelta(days=100)).strftime('%Y%m%d_%H%M%S')}_old"
        old_backup.mkdir()
        (old_backup / "config.txt").write_text("configuração antiga")
        
        recent_backup = backups_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_recent"
        recent_backup.mkdir()
        (recent_backup / "config.txt").write_text("configuração recente")


def run_organization_manager_demo():
    """Demonstração das funcionalidades do OrganizationManager"""
    print("=== Demonstração do Organization Manager ===\n")
    
    # Criar diretório temporário para demo
    demo_dir = Path(tempfile.mkdtemp())
    print(f"Diretório de demonstração: {demo_dir}")
    
    try:
        # Inicializar manager
        manager = OrganizationManager(demo_dir)
        
        # Criar cenário de teste
        print("\n1. Criando cenário de teste...")
        _create_demo_scenario(demo_dir)
        
        # Demonstrar limpeza de temporários
        print("\n2. Limpeza de arquivos temporários:")
        temp_result = manager.cleanup_temporary_files()
        print(f"   Status: {temp_result.status.value}")
        print(f"   Arquivos removidos: {temp_result.files_removed}")
        print(f"   Espaço liberado: {temp_result.space_freed} bytes")
        
        # Demonstrar organização de downloads
        print("\n3. Organização de downloads:")
        org_result = manager.organize_downloads()
        print(f"   Status: {org_result.status.value}")
        print(f"   Arquivos organizados: {org_result.files_moved}")
        print(f"   Diretórios criados: {org_result.directories_created}")
        
        # Demonstrar rotação de logs
        print("\n4. Rotação de logs:")
        log_result = manager.rotate_logs()
        print(f"   Status: {log_result.status.value}")
        print(f"   Logs arquivados: {log_result.files_removed}")
        
        # Demonstrar otimização completa
        print("\n5. Otimização completa:")
        opt_result = manager.optimize_disk_usage()
        print(f"   Status: {opt_result.status.value}")
        print(f"   Espaço total liberado: {opt_result.total_space_freed} bytes")
        print(f"   Operações realizadas: {', '.join(opt_result.operations_performed)}")
        
        if opt_result.recommendations:
            print("\n   Recomendações:")
            for rec in opt_result.recommendations:
                print(f"   - {rec}")
        
        print("\n=== Demonstração concluída ===")
        
    finally:
        # Limpar diretório de demonstração
        if demo_dir.exists():
            shutil.rmtree(demo_dir)


def _create_demo_scenario(base_dir: Path):
    """Cria cenário de demonstração"""
    # Criar estrutura de diretórios
    dirs = ['temp', 'downloads', 'logs', 'backups']
    for dir_name in dirs:
        (base_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    # Arquivos temporários
    temp_dir = base_dir / "temp"
    (temp_dir / "old_file.tmp").write_text("arquivo temporário antigo")
    (temp_dir / "cache.cache").write_text("arquivo de cache")
    
    # Downloads
    downloads_dir = base_dir / "downloads"
    (downloads_dir / "installer.exe").write_text("instalador de software")
    (downloads_dir / "document.pdf").write_text("documento PDF")
    (downloads_dir / "archive.zip").write_text("arquivo compactado")
    (downloads_dir / "image.png").write_text("imagem PNG")
    
    # Logs antigos
    logs_dir = base_dir / "logs"
    old_log = logs_dir / "old_application.log"
    old_log.write_text("log de aplicação antigo")
    old_time = datetime.now() - timedelta(days=35)
    os.utime(old_log, (old_time.timestamp(), old_time.timestamp()))
    
    (logs_dir / "recent.log").write_text("log recente")


if __name__ == "__main__":
    # Executar testes
    print("Executando testes do Organization Manager...\n")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n" + "="*50)
    
    # Executar demonstração
    run_organization_manager_demo()
cl
ass TestOrganizationManagerTask62(unittest.TestCase):
    """Testes específicos para funcionalidades da task 6.2"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = OrganizationManager(self.test_dir)
        
        # Criar estrutura de diretórios de teste
        for dir_name in ['temp', 'downloads', 'logs', 'backups', 'cache']:
            (self.test_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """Limpeza após cada teste"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_detect_and_remove_unnecessary_files(self):
        """Testa detecção e remoção de arquivos desnecessários"""
        # Criar arquivos desnecessários
        unnecessary_files = [
            "test.pyc",
            "backup.bak", 
            "old_file.old",
            "Thumbs.db",
            ".DS_Store"
        ]
        
        for filename in unnecessary_files:
            file_path = self.test_dir / filename
            file_path.write_text(f"conteúdo de {filename}")
        
        # Criar diretório __pycache__
        pycache_dir = self.test_dir / "__pycache__"
        pycache_dir.mkdir()
        (pycache_dir / "module.pyc").write_text("bytecode")
        
        # Executar remoção
        result = self.manager.detect_and_remove_unnecessary_files()
        
        # Verificar resultado
        self.assertEqual(result.status, CleanupStatus.COMPLETED)
        self.assertGreater(result.files_removed, 0)
        self.assertGreater(result.space_freed, 0)
        
        # Verificar que arquivos foram removidos
        for filename in unnecessary_files:
            file_path = self.test_dir / filename
            self.assertFalse(file_path.exists(), f"Arquivo {filename} deveria ter sido removido")
        
        # Verificar que diretório __pycache__ foi removido
        self.assertFalse(pycache_dir.exists())
    
    def test_archive_old_logs(self):
        """Testa arquivamento de logs antigos"""
        logs_dir = self.test_dir / "logs"
        
        # Criar logs de diferentes idades
        old_log = logs_dir / "old.log"
        recent_log = logs_dir / "recent.log"
        
        old_log.write_text("log muito antigo" * 1000)  # Arquivo maior
        recent_log.write_text("log recente")
        
        # Tornar um log muito antigo (100 dias)
        old_time = datetime.now() - timedelta(days=100)
        os.utime(old_log, (old_time.timestamp(), old_time.timestamp()))
        
        # Executar arquivamento
        result = self.manager.archive_old_logs(archive_age_days=90)
        
        # Verificar resultado
        self.assertEqual(result.status, CleanupStatus.COMPLETED)
        self.assertGreater(result.files_removed, 0)
        
        # Log antigo deve ter sido arquivado
        self.assertFalse(old_log.exists())
        # Log recente deve permanecer
        self.assertTrue(recent_log.exists())
        
        # Verificar que arquivo foi para diretório archived
        archived_dir = logs_dir / "archived"
        self.assertTrue(archived_dir.exists())
    
    def test_intelligent_backup_management(self):
        """Testa gerenciamento inteligente de backups"""
        backups_dir = self.test_dir / "backups"
        
        # Criar backups de diferentes idades
        backup_dates = [
            datetime.now() - timedelta(days=1),    # Recente
            datetime.now() - timedelta(days=10),   # Semanal
            datetime.now() - timedelta(days=40),   # Mensal
            datetime.now() - timedelta(days=200),  # Muito antigo
            datetime.now() - timedelta(days=400)   # Extremamente antigo
        ]
        
        backup_dirs = []
        for i, backup_date in enumerate(backup_dates):
            backup_name = f"backup_{backup_date.strftime('%Y%m%d_%H%M%S')}_test{i}"
            backup_dir = backups_dir / backup_name
            backup_dir.mkdir()
            (backup_dir / f"file{i}.txt").write_text(f"conteúdo do backup {i}")
            backup_dirs.append(backup_dir)
        
        # Executar gerenciamento inteligente
        result = self.manager.intelligent_backup_management()
        
        # Verificar resultado
        self.assertEqual(result.status, CleanupStatus.COMPLETED)
        self.assertGreater(result.backups_processed, 0)
        
        # Backups muito antigos devem ter sido removidos
        self.assertFalse(backup_dirs[3].exists())  # 200 dias
        self.assertFalse(backup_dirs[4].exists())  # 400 dias
        
        # Backups recentes devem permanecer
        self.assertTrue(backup_dirs[0].exists())   # 1 dia
    
    def test_advanced_disk_optimization(self):
        """Testa otimização avançada de disco"""
        # Criar cenário com vários tipos de arquivos
        self._create_advanced_test_scenario()
        
        # Executar otimização avançada
        result = self.manager.advanced_disk_optimization()
        
        # Verificar resultado
        self.assertEqual(result.status, CleanupStatus.COMPLETED)
        self.assertGreater(len(result.operations_performed), 0)
        self.assertGreaterEqual(result.total_space_freed, 0)
        
        # Verificar que operações avançadas foram executadas
        expected_operations = [
            "Remoção de arquivos desnecessários",
            "Arquivamento de logs antigos",
            "Gerenciamento inteligente de backups"
        ]
        
        for operation in expected_operations:
            self.assertIn(operation, result.operations_performed)
        
        # Verificar que análise de disco foi feita
        self.assertIn('directory_sizes', result.details)
        self.assertIn('total_managed_size', result.details)
        
        # Verificar que recomendações foram geradas
        self.assertGreater(len(result.recommendations), 0)
    
    def test_disk_usage_analysis(self):
        """Testa análise de uso de disco"""
        # Criar arquivos de tamanhos conhecidos
        (self.test_dir / "downloads" / "large_file.exe").write_text("x" * 1000)
        (self.test_dir / "logs" / "large_log.log").write_text("y" * 500)
        
        result = OptimizationResult(status=CleanupStatus.IN_PROGRESS)
        self.manager._analyze_disk_usage(result)
        
        # Verificar que análise foi feita
        self.assertIn('directory_sizes', result.details)
        self.assertIn('total_managed_size', result.details)
        
        # Verificar que diretórios foram analisados
        directory_sizes = result.details['directory_sizes']
        self.assertIn('downloads', directory_sizes)
        self.assertIn('logs', directory_sizes)
        
        # Verificar tamanhos
        self.assertGreater(directory_sizes['downloads'], 0)
        self.assertGreater(directory_sizes['logs'], 0)
    
    def test_advanced_recommendations(self):
        """Testa geração de recomendações avançadas"""
        result = OptimizationResult(status=CleanupStatus.COMPLETED)
        result.total_space_freed = 50 * 1024 * 1024  # 50MB
        result.details = {
            'directory_sizes': {
                'downloads': 100 * 1024 * 1024,  # 100MB
                'backups': 200 * 1024 * 1024,    # 200MB
                'logs': 50 * 1024 * 1024         # 50MB
            },
            'largest_directories': [
                ('backups', 200 * 1024 * 1024),
                ('downloads', 100 * 1024 * 1024),
                ('logs', 50 * 1024 * 1024)
            ]
        }
        
        self.manager._generate_advanced_recommendations(result)
        
        # Verificar que recomendações foram geradas
        self.assertGreater(len(result.recommendations), 0)
        
        # Verificar que há recomendação sobre espaço liberado
        space_recommendations = [r for r in result.recommendations if "50" in r and "MB" in r]
        self.assertGreater(len(space_recommendations), 0)
        
        # Verificar que há recomendação sobre diretórios grandes
        dir_recommendations = [r for r in result.recommendations if "backups" in r]
        self.assertGreater(len(dir_recommendations), 0)
    
    def _create_advanced_test_scenario(self):
        """Cria cenário avançado para testes"""
        # Arquivos desnecessários
        (self.test_dir / "test.pyc").write_text("bytecode")
        (self.test_dir / "backup.bak").write_text("backup")
        
        # Logs antigos
        logs_dir = self.test_dir / "logs"
        old_log = logs_dir / "old.log"
        old_log.write_text("log antigo")
        old_time = datetime.now() - timedelta(days=100)
        os.utime(old_log, (old_time.timestamp(), old_time.timestamp()))
        
        # Backups antigos
        backups_dir = self.test_dir / "backups"
        old_backup = backups_dir / f"backup_{(datetime.now() - timedelta(days=200)).strftime('%Y%m%d_%H%M%S')}_old"
        old_backup.mkdir()
        (old_backup / "config.txt").write_text("configuração antiga")
        
        # Arquivos temporários
        temp_dir = self.test_dir / "temp"
        (temp_dir / "temp.tmp").write_text("temporário")
        
        # Downloads para organizar
        downloads_dir = self.test_dir / "downloads"
        (downloads_dir / "installer.exe").write_text("instalador")


def run_advanced_organization_demo():
    """Demonstração das funcionalidades avançadas do OrganizationManager (task 6.2)"""
    print("=== Demonstração Avançada do Organization Manager (Task 6.2) ===\n")
    
    # Criar diretório temporário para demo
    demo_dir = Path(tempfile.mkdtemp())
    print(f"Diretório de demonstração: {demo_dir}")
    
    try:
        # Inicializar manager
        manager = OrganizationManager(demo_dir)
        
        # Criar cenário avançado
        print("\n1. Criando cenário avançado de teste...")
        _create_advanced_demo_scenario(demo_dir)
        
        # Demonstrar remoção de arquivos desnecessários
        print("\n2. Remoção de arquivos desnecessários:")
        unnecessary_result = manager.detect_and_remove_unnecessary_files()
        print(f"   Status: {unnecessary_result.status.value}")
        print(f"   Arquivos removidos: {unnecessary_result.files_removed}")
        print(f"   Diretórios removidos: {unnecessary_result.directories_removed}")
        print(f"   Espaço liberado: {format_size(unnecessary_result.space_freed)}")
        
        # Demonstrar arquivamento de logs
        print("\n3. Arquivamento de logs antigos:")
        archive_result = manager.archive_old_logs(archive_age_days=30)
        print(f"   Status: {archive_result.status.value}")
        print(f"   Logs arquivados: {archive_result.files_removed}")
        print(f"   Espaço liberado: {format_size(archive_result.space_freed)}")
        
        # Demonstrar gerenciamento inteligente de backups
        print("\n4. Gerenciamento inteligente de backups:")
        intelligent_result = manager.intelligent_backup_management()
        print(f"   Status: {intelligent_result.status.value}")
        print(f"   Backups processados: {intelligent_result.backups_processed}")
        print(f"   Backups removidos: {intelligent_result.backups_removed}")
        print(f"   Backups arquivados: {intelligent_result.backups_archived}")
        print(f"   Espaço liberado: {format_size(intelligent_result.space_freed)}")
        
        # Demonstrar otimização avançada
        print("\n5. Otimização avançada completa:")
        advanced_result = manager.advanced_disk_optimization()
        print(f"   Status: {advanced_result.status.value}")
        print(f"   Espaço total liberado: {format_size(advanced_result.total_space_freed)}")
        print(f"   Operações realizadas: {len(advanced_result.operations_performed)}")
        
        for i, operation in enumerate(advanced_result.operations_performed, 1):
            print(f"     {i}. {operation}")
        
        if advanced_result.recommendations:
            print("\n   Recomendações avançadas:")
            for rec in advanced_result.recommendations:
                print(f"   - {rec}")
        
        # Mostrar análise detalhada
        if 'directory_sizes' in advanced_result.details:
            print("\n6. Análise de uso de espaço:")
            directory_sizes = advanced_result.details['directory_sizes']
            for dir_name, size in directory_sizes.items():
                print(f"   {dir_name}: {format_size(size)}")
        
        print("\n=== Demonstração avançada concluída ===")
        
    finally:
        # Limpar diretório de demonstração
        if demo_dir.exists():
            shutil.rmtree(demo_dir)


def _create_advanced_demo_scenario(base_dir: Path):
    """Cria cenário avançado de demonstração"""
    # Criar estrutura de diretórios
    dirs = ['temp', 'downloads', 'logs', 'backups', 'cache']
    for dir_name in dirs:
        (base_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    # Arquivos desnecessários
    unnecessary_files = [
        "module.pyc",
        "backup.bak",
        "old_config.old",
        "Thumbs.db",
        ".DS_Store"
    ]
    
    for filename in unnecessary_files:
        (base_dir / filename).write_text(f"conteúdo desnecessário de {filename}")
    
    # Diretório __pycache__
    pycache_dir = base_dir / "__pycache__"
    pycache_dir.mkdir()
    (pycache_dir / "module.pyc").write_text("bytecode compilado")
    (pycache_dir / "another.pyc").write_text("mais bytecode")
    
    # Logs antigos de diferentes tamanhos
    logs_dir = base_dir / "logs"
    
    # Log pequeno antigo
    small_old_log = logs_dir / "small_old.log"
    small_old_log.write_text("log pequeno antigo")
    old_time = datetime.now() - timedelta(days=100)
    os.utime(small_old_log, (old_time.timestamp(), old_time.timestamp()))
    
    # Log grande antigo
    large_old_log = logs_dir / "large_old.log"
    large_old_log.write_text("log grande antigo\n" * 10000)  # > 1MB
    os.utime(large_old_log, (old_time.timestamp(), old_time.timestamp()))
    
    # Log recente
    (logs_dir / "recent.log").write_text("log recente")
    
    # Backups de diferentes idades
    backups_dir = base_dir / "backups"
    
    backup_scenarios = [
        (1, "recente"),      # 1 dia atrás
        (10, "semanal"),     # 10 dias atrás  
        (40, "mensal"),      # 40 dias atrás
        (200, "antigo"),     # 200 dias atrás
        (400, "muito_antigo") # 400 dias atrás
    ]
    
    for days_ago, suffix in backup_scenarios:
        backup_date = datetime.now() - timedelta(days=days_ago)
        backup_name = f"backup_{backup_date.strftime('%Y%m%d_%H%M%S')}_{suffix}"
        backup_dir = backups_dir / backup_name
        backup_dir.mkdir()
        
        # Adicionar arquivos ao backup
        (backup_dir / "config.json").write_text(f'{{"backup": "{suffix}", "date": "{backup_date}"}}')
        (backup_dir / "data.txt").write_text(f"dados do backup {suffix}")
    
    # Downloads diversos
    downloads_dir = base_dir / "downloads"
    download_files = [
        ("installer.exe", "instalador de software"),
        ("document.pdf", "documento importante"),
        ("archive.zip", "arquivo compactado"),
        ("image.png", "imagem de exemplo")
    ]
    
    for filename, content in download_files:
        (downloads_dir / filename).write_text(content)
    
    # Arquivos temporários
    temp_dir = base_dir / "temp"
    (temp_dir / "temp_file.tmp").write_text("arquivo temporário")
    (temp_dir / "cache.cache").write_text("arquivo de cache")


if __name__ == "__main__":
    # Executar testes originais
    print("Executando testes do Organization Manager...\n")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n" + "="*50)
    
    # Executar demonstração avançada
    run_advanced_organization_demo()