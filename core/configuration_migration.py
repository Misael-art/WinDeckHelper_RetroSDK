# -*- coding: utf-8 -*-
"""
Sistema de migração de configuração para Environment Dev
Migra configurações existentes para o novo sistema de catálogo de runtime
"""

import os
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import configparser
import xml.etree.ElementTree as ET
import yaml
import sqlite3

from runtime_catalog_manager import RuntimeInfo, RuntimeStatus
from configuration_manager import ConfigProfile
from security_manager import SecurityLevel

@dataclass
class MigrationResult:
    """Resultado de uma migração"""
    success: bool
    migrated_items: int
    skipped_items: int
    errors: List[str]
    warnings: List[str]
    backup_path: Optional[Path] = None
    migration_time: Optional[datetime] = None

@dataclass
class LegacyConfig:
    """Configuração legada detectada"""
    config_type: str  # 'json', 'ini', 'xml', 'yaml', 'registry', 'database'
    file_path: Path
    version: str
    last_modified: datetime
    size_bytes: int
    contains_runtimes: bool
    contains_settings: bool
    estimated_complexity: str  # 'simple', 'moderate', 'complex'

class ConfigurationMigrator:
    """Migrador de configurações legadas"""
    
    def __init__(self, target_data_dir: Path):
        """Inicializar migrador"""
        self.target_data_dir = target_data_dir
        self.backup_dir = target_data_dir / "migration_backups"
        self.logger = logging.getLogger("ConfigMigrator")
        
        # Criar diretórios necessários
        self.target_data_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Padrões de arquivos de configuração conhecidos
        self.config_patterns = {
            "environment_dev_v1": {
                "patterns": ["env_dev.json", "environment_dev.config", ".env_dev/*"],
                "type": "json",
                "priority": 100
            },
            "runtime_configs": {
                "patterns": ["runtimes.json", "runtime_catalog.json", "installed_runtimes.db"],
                "type": "mixed",
                "priority": 90
            },
            "package_managers": {
                "patterns": ["package_managers.ini", "pm_config.xml"],
                "type": "mixed",
                "priority": 80
            },
            "user_preferences": {
                "patterns": ["preferences.yaml", "settings.json", "user_config.ini"],
                "type": "mixed",
                "priority": 70
            },
            "steam_deck_configs": {
                "patterns": ["steamdeck.json", "deck_settings.yaml", "gaming_mode.config"],
                "type": "mixed",
                "priority": 85
            }
        }
        
        # Mapeamentos de migração
        self.field_mappings = {
            "runtime_name": "name",
            "runtime_version": "version",
            "install_path": "installation_path",
            "download_link": "download_url",
            "package_size": "install_size",
            "dependencies": "dependencies",
            "platforms": "supported_platforms",
            "hash": "checksum",
            "category": "category",
            "tags": "tags",
            "description": "description"
        }
    
    def discover_legacy_configurations(self, search_paths: List[Path]) -> List[LegacyConfig]:
        """Descobrir configurações legadas"""
        discovered_configs = []
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
                
            self.logger.info(f"Procurando configurações em: {search_path}")
            
            # Buscar por padrões conhecidos
            for config_name, config_info in self.config_patterns.items():
                for pattern in config_info["patterns"]:
                    matches = list(search_path.rglob(pattern))
                    
                    for match in matches:
                        if match.is_file():
                            legacy_config = self._analyze_config_file(match, config_info["type"])
                            if legacy_config:
                                discovered_configs.append(legacy_config)
        
        # Ordenar por prioridade e complexidade
        discovered_configs.sort(key=lambda c: (
            -self._get_config_priority(c.file_path.name),
            c.estimated_complexity
        ))
        
        self.logger.info(f"Descobertas {len(discovered_configs)} configurações legadas")
        return discovered_configs
    
    def _analyze_config_file(self, file_path: Path, config_type: str) -> Optional[LegacyConfig]:
        """Analisar arquivo de configuração"""
        try:
            stat = file_path.stat()
            
            # Detectar tipo real do arquivo
            actual_type = self._detect_file_type(file_path)
            if actual_type:
                config_type = actual_type
            
            # Analisar conteúdo
            contains_runtimes, contains_settings = self._analyze_content(file_path, config_type)
            
            # Estimar complexidade
            complexity = self._estimate_complexity(file_path, stat.st_size, contains_runtimes, contains_settings)
            
            return LegacyConfig(
                config_type=config_type,
                file_path=file_path,
                version=self._detect_version(file_path, config_type),
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                size_bytes=stat.st_size,
                contains_runtimes=contains_runtimes,
                contains_settings=contains_settings,
                estimated_complexity=complexity
            )
            
        except Exception as e:
            self.logger.warning(f"Erro ao analisar {file_path}: {e}")
            return None
    
    def _detect_file_type(self, file_path: Path) -> Optional[str]:
        """Detectar tipo real do arquivo"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(1024)  # Ler primeiros 1KB
            
            # Detectar JSON
            if content.strip().startswith(('{', '[')):
                try:
                    json.loads(content)
                    return "json"
                except:
                    pass
            
            # Detectar YAML
            if any(line.strip().endswith(':') for line in content.split('\n')[:10]):
                try:
                    yaml.safe_load(content)
                    return "yaml"
                except:
                    pass
            
            # Detectar XML
            if content.strip().startswith('<?xml') or content.strip().startswith('<'):
                try:
                    ET.fromstring(content)
                    return "xml"
                except:
                    pass
            
            # Detectar INI
            if '[' in content and ']' in content:
                try:
                    config = configparser.ConfigParser()
                    config.read_string(content)
                    return "ini"
                except:
                    pass
            
            return None
            
        except Exception:
            return None
    
    def _analyze_content(self, file_path: Path, config_type: str) -> Tuple[bool, bool]:
        """Analisar conteúdo do arquivo"""
        contains_runtimes = False
        contains_settings = False
        
        try:
            if config_type == "json":
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Verificar indicadores de runtimes
                runtime_indicators = ['runtimes', 'runtime', 'packages', 'installations', 'catalog']
                settings_indicators = ['settings', 'preferences', 'config', 'options', 'user']
                
                content_str = json.dumps(data).lower()
                contains_runtimes = any(indicator in content_str for indicator in runtime_indicators)
                contains_settings = any(indicator in content_str for indicator in settings_indicators)
            
            elif config_type == "yaml":
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                content_str = yaml.dump(data).lower()
                contains_runtimes = any(key in content_str for key in ['runtime', 'package', 'install'])
                contains_settings = any(key in content_str for key in ['setting', 'config', 'preference'])
            
            elif config_type == "ini":
                config = configparser.ConfigParser()
                config.read(file_path)
                
                sections = [section.lower() for section in config.sections()]
                contains_runtimes = any('runtime' in section or 'package' in section for section in sections)
                contains_settings = any('setting' in section or 'config' in section for section in sections)
            
            elif config_type == "xml":
                tree = ET.parse(file_path)
                root = tree.getroot()
                
                xml_str = ET.tostring(root, encoding='unicode').lower()
                contains_runtimes = any(tag in xml_str for tag in ['runtime', 'package', 'installation'])
                contains_settings = any(tag in xml_str for tag in ['setting', 'config', 'preference'])
            
        except Exception as e:
            self.logger.warning(f"Erro ao analisar conteúdo de {file_path}: {e}")
        
        return contains_runtimes, contains_settings
    
    def _estimate_complexity(self, file_path: Path, size_bytes: int, has_runtimes: bool, has_settings: bool) -> str:
        """Estimar complexidade da migração"""
        # Fatores de complexidade
        complexity_score = 0
        
        # Tamanho do arquivo
        if size_bytes > 1024 * 1024:  # > 1MB
            complexity_score += 3
        elif size_bytes > 100 * 1024:  # > 100KB
            complexity_score += 2
        elif size_bytes > 10 * 1024:  # > 10KB
            complexity_score += 1
        
        # Conteúdo
        if has_runtimes:
            complexity_score += 2
        if has_settings:
            complexity_score += 1
        
        # Tipo de arquivo
        if file_path.suffix.lower() in ['.db', '.sqlite', '.sqlite3']:
            complexity_score += 3
        elif file_path.suffix.lower() in ['.xml']:
            complexity_score += 2
        
        # Classificar complexidade
        if complexity_score >= 6:
            return "complex"
        elif complexity_score >= 3:
            return "moderate"
        else:
            return "simple"
    
    def _detect_version(self, file_path: Path, config_type: str) -> str:
        """Detectar versão da configuração"""
        try:
            if config_type == "json":
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Procurar campos de versão comuns
                version_fields = ['version', 'config_version', 'schema_version', 'app_version']
                for field in version_fields:
                    if field in data:
                        return str(data[field])
            
            # Versão padrão baseada na data de modificação
            stat = file_path.stat()
            mod_date = datetime.fromtimestamp(stat.st_mtime)
            
            if mod_date.year >= 2024:
                return "2.x"
            elif mod_date.year >= 2023:
                return "1.x"
            else:
                return "legacy"
                
        except Exception:
            return "unknown"
    
    def _get_config_priority(self, filename: str) -> int:
        """Obter prioridade de migração baseada no nome do arquivo"""
        filename_lower = filename.lower()
        
        for config_name, config_info in self.config_patterns.items():
            for pattern in config_info["patterns"]:
                if pattern.replace("*", "").replace("/", "") in filename_lower:
                    return config_info["priority"]
        
        return 50  # Prioridade padrão
    
    def migrate_configuration(self, legacy_config: LegacyConfig) -> MigrationResult:
        """Migrar uma configuração específica"""
        start_time = datetime.now()
        result = MigrationResult(
            success=False,
            migrated_items=0,
            skipped_items=0,
            errors=[],
            warnings=[],
            migration_time=start_time
        )
        
        try:
            self.logger.info(f"Iniciando migração de {legacy_config.file_path}")
            
            # 1. Criar backup
            backup_path = self._create_backup(legacy_config.file_path)
            result.backup_path = backup_path
            
            # 2. Carregar dados legados
            legacy_data = self._load_legacy_data(legacy_config)
            if not legacy_data:
                result.errors.append("Falha ao carregar dados legados")
                return result
            
            # 3. Migrar runtimes
            if legacy_config.contains_runtimes:
                runtime_result = self._migrate_runtimes(legacy_data, legacy_config.config_type)
                result.migrated_items += runtime_result["migrated"]
                result.skipped_items += runtime_result["skipped"]
                result.errors.extend(runtime_result["errors"])
                result.warnings.extend(runtime_result["warnings"])
            
            # 4. Migrar configurações
            if legacy_config.contains_settings:
                settings_result = self._migrate_settings(legacy_data, legacy_config.config_type)
                result.migrated_items += settings_result["migrated"]
                result.skipped_items += settings_result["skipped"]
                result.errors.extend(settings_result["errors"])
                result.warnings.extend(settings_result["warnings"])
            
            # 5. Verificar sucesso
            result.success = len(result.errors) == 0 and result.migrated_items > 0
            result.migration_time = datetime.now() - start_time
            
            if result.success:
                self.logger.info(f"Migração concluída: {result.migrated_items} itens migrados")
            else:
                self.logger.error(f"Migração falhou: {len(result.errors)} erros")
            
        except Exception as e:
            result.errors.append(f"Erro geral na migração: {e}")
            self.logger.error(f"Erro na migração de {legacy_config.file_path}: {e}")
        
        return result
    
    def _create_backup(self, file_path: Path) -> Path:
        """Criar backup do arquivo original"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(file_path, backup_path)
        self.logger.info(f"Backup criado: {backup_path}")
        
        return backup_path
    
    def _load_legacy_data(self, legacy_config: LegacyConfig) -> Optional[Dict[str, Any]]:
        """Carregar dados do arquivo legado"""
        try:
            if legacy_config.config_type == "json":
                with open(legacy_config.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            elif legacy_config.config_type == "yaml":
                with open(legacy_config.file_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            
            elif legacy_config.config_type == "ini":
                config = configparser.ConfigParser()
                config.read(legacy_config.file_path)
                
                # Converter para dicionário
                data = {}
                for section in config.sections():
                    data[section] = dict(config[section])
                return data
            
            elif legacy_config.config_type == "xml":
                tree = ET.parse(legacy_config.file_path)
                root = tree.getroot()
                
                # Converter XML para dicionário (simplificado)
                return self._xml_to_dict(root)
            
            elif legacy_config.file_path.suffix.lower() in ['.db', '.sqlite', '.sqlite3']:
                return self._load_sqlite_data(legacy_config.file_path)
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados legados: {e}")
            return None
    
    def _xml_to_dict(self, element) -> Dict[str, Any]:
        """Converter elemento XML para dicionário"""
        result = {}
        
        # Atributos
        if element.attrib:
            result.update(element.attrib)
        
        # Texto
        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            result['text'] = element.text.strip()
        
        # Filhos
        for child in element:
            child_data = self._xml_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    
    def _load_sqlite_data(self, db_path: Path) -> Dict[str, Any]:
        """Carregar dados de banco SQLite"""
        data = {}
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Obter lista de tabelas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            for table_name, in tables:
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                # Obter nomes das colunas
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Converter para lista de dicionários
                data[table_name] = [
                    dict(zip(columns, row)) for row in rows
                ]
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar SQLite {db_path}: {e}")
        
        return data
    
    def _migrate_runtimes(self, legacy_data: Dict[str, Any], config_type: str) -> Dict[str, Any]:
        """Migrar dados de runtimes"""
        result = {
            "migrated": 0,
            "skipped": 0,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Encontrar dados de runtimes na estrutura legada
            runtime_data = self._extract_runtime_data(legacy_data)
            
            if not runtime_data:
                result["warnings"].append("Nenhum dado de runtime encontrado")
                return result
            
            # Migrar cada runtime
            for legacy_runtime in runtime_data:
                try:
                    migrated_runtime = self._convert_legacy_runtime(legacy_runtime)
                    
                    if migrated_runtime:
                        # Salvar runtime migrado
                        self._save_migrated_runtime(migrated_runtime)
                        result["migrated"] += 1
                    else:
                        result["skipped"] += 1
                        result["warnings"].append(f"Runtime inválido ignorado: {legacy_runtime}")
                        
                except Exception as e:
                    result["errors"].append(f"Erro ao migrar runtime: {e}")
                    result["skipped"] += 1
            
        except Exception as e:
            result["errors"].append(f"Erro na migração de runtimes: {e}")
        
        return result
    
    def _extract_runtime_data(self, legacy_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrair dados de runtimes da estrutura legada"""
        runtime_data = []
        
        # Procurar em diferentes estruturas possíveis
        possible_keys = ['runtimes', 'runtime', 'packages', 'installations', 'catalog', 'items']
        
        for key in possible_keys:
            if key in legacy_data:
                data = legacy_data[key]
                
                if isinstance(data, list):
                    runtime_data.extend(data)
                elif isinstance(data, dict):
                    # Se for dicionário, pode ser {nome: dados}
                    for name, runtime_info in data.items():
                        if isinstance(runtime_info, dict):
                            runtime_info['name'] = name
                            runtime_data.append(runtime_info)
                        else:
                            # Dados simples
                            runtime_data.append({'name': name, 'value': runtime_info})
        
        return runtime_data
    
    def _convert_legacy_runtime(self, legacy_runtime: Dict[str, Any]) -> Optional[RuntimeInfo]:
        """Converter runtime legado para novo formato"""
        try:
            # Mapear campos usando mapeamentos definidos
            mapped_data = {}
            
            for legacy_field, new_field in self.field_mappings.items():
                if legacy_field in legacy_runtime:
                    mapped_data[new_field] = legacy_runtime[legacy_field]
            
            # Campos obrigatórios com valores padrão
            required_fields = {
                'name': legacy_runtime.get('name', 'unknown'),
                'version': legacy_runtime.get('version', '1.0.0'),
                'description': legacy_runtime.get('description', 'Migrated runtime'),
                'category': legacy_runtime.get('category', 'migrated'),
                'tags': legacy_runtime.get('tags', ['migrated']),
                'download_url': legacy_runtime.get('download_url', ''),
                'install_size': int(legacy_runtime.get('install_size', 0)),
                'dependencies': legacy_runtime.get('dependencies', []),
                'supported_platforms': legacy_runtime.get('supported_platforms', ['current']),
                'checksum': legacy_runtime.get('checksum', '')
            }
            
            # Mesclar dados mapeados com campos obrigatórios
            final_data = {**required_fields, **mapped_data}
            
            # Criar RuntimeInfo
            return RuntimeInfo(**final_data)
            
        except Exception as e:
            self.logger.error(f"Erro ao converter runtime legado: {e}")
            return None
    
    def _save_migrated_runtime(self, runtime: RuntimeInfo):
        """Salvar runtime migrado"""
        # Salvar no arquivo de runtimes migrados
        migrated_file = self.target_data_dir / "migrated_runtimes.json"
        
        # Carregar runtimes existentes
        migrated_runtimes = []
        if migrated_file.exists():
            try:
                with open(migrated_file, 'r', encoding='utf-8') as f:
                    migrated_runtimes = json.load(f)
            except Exception:
                pass
        
        # Adicionar novo runtime
        migrated_runtimes.append(asdict(runtime))
        
        # Salvar arquivo atualizado
        with open(migrated_file, 'w', encoding='utf-8') as f:
            json.dump(migrated_runtimes, f, indent=2, ensure_ascii=False)
    
    def _migrate_settings(self, legacy_data: Dict[str, Any], config_type: str) -> Dict[str, Any]:
        """Migrar configurações"""
        result = {
            "migrated": 0,
            "skipped": 0,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Extrair configurações
            settings_data = self._extract_settings_data(legacy_data)
            
            if not settings_data:
                result["warnings"].append("Nenhuma configuração encontrada")
                return result
            
            # Criar perfil de configuração migrado
            profile = ConfigProfile(
                name="migrated_profile",
                description="Profile migrated from legacy configuration",
                settings=settings_data
            )
            
            # Salvar perfil
            self._save_migrated_profile(profile)
            result["migrated"] = len(settings_data)
            
        except Exception as e:
            result["errors"].append(f"Erro na migração de configurações: {e}")
        
        return result
    
    def _extract_settings_data(self, legacy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrair dados de configurações"""
        settings = {}
        
        # Procurar configurações em diferentes estruturas
        settings_keys = ['settings', 'preferences', 'config', 'options', 'user_config']
        
        for key in settings_keys:
            if key in legacy_data and isinstance(legacy_data[key], dict):
                settings.update(legacy_data[key])
        
        # Adicionar configurações de nível raiz que não são runtimes
        excluded_keys = ['runtimes', 'runtime', 'packages', 'installations', 'catalog']
        
        for key, value in legacy_data.items():
            if key not in excluded_keys and not key.startswith('_'):
                if isinstance(value, (str, int, float, bool, list)):
                    settings[f"legacy.{key}"] = value
        
        return settings
    
    def _save_migrated_profile(self, profile: ConfigProfile):
        """Salvar perfil migrado"""
        profiles_file = self.target_data_dir / "migrated_profiles.json"
        
        # Carregar perfis existentes
        profiles = []
        if profiles_file.exists():
            try:
                with open(profiles_file, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
            except Exception:
                pass
        
        # Adicionar novo perfil
        profiles.append(asdict(profile))
        
        # Salvar arquivo atualizado
        with open(profiles_file, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
    
    def migrate_all_configurations(self, search_paths: List[Path]) -> Dict[str, Any]:
        """Migrar todas as configurações encontradas"""
        start_time = datetime.now()
        
        # Descobrir configurações
        legacy_configs = self.discover_legacy_configurations(search_paths)
        
        # Resultados da migração
        migration_summary = {
            "total_configs": len(legacy_configs),
            "successful_migrations": 0,
            "failed_migrations": 0,
            "total_items_migrated": 0,
            "total_items_skipped": 0,
            "migration_results": [],
            "start_time": start_time,
            "end_time": None,
            "duration": None
        }
        
        # Migrar cada configuração
        for legacy_config in legacy_configs:
            self.logger.info(f"Migrando: {legacy_config.file_path}")
            
            result = self.migrate_configuration(legacy_config)
            migration_summary["migration_results"].append({
                "config_path": str(legacy_config.file_path),
                "success": result.success,
                "migrated_items": result.migrated_items,
                "skipped_items": result.skipped_items,
                "errors": result.errors,
                "warnings": result.warnings
            })
            
            if result.success:
                migration_summary["successful_migrations"] += 1
            else:
                migration_summary["failed_migrations"] += 1
            
            migration_summary["total_items_migrated"] += result.migrated_items
            migration_summary["total_items_skipped"] += result.skipped_items
        
        # Finalizar resumo
        end_time = datetime.now()
        migration_summary["end_time"] = end_time
        migration_summary["duration"] = (end_time - start_time).total_seconds()
        
        # Salvar resumo da migração
        summary_file = self.target_data_dir / "migration_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(migration_summary, f, indent=2, default=str, ensure_ascii=False)
        
        self.logger.info(f"Migração concluída: {migration_summary['successful_migrations']}/{migration_summary['total_configs']} configurações migradas")
        
        return migration_summary

# Função de conveniência
def migrate_legacy_configurations(target_dir: Path, search_paths: List[Path]) -> Dict[str, Any]:
    """Migrar configurações legadas para novo sistema"""
    migrator = ConfigurationMigrator(target_dir)
    return migrator.migrate_all_configurations(search_paths)

# Exemplo de uso
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Diretórios de busca
    search_paths = [
        Path.home() / ".environment_dev",
        Path.home() / "AppData" / "Local" / "EnvironmentDev",
        Path.cwd() / "config",
        Path("/etc/environment_dev") if os.name != 'nt' else Path("C:/ProgramData/EnvironmentDev")
    ]
    
    # Diretório de destino
    target_dir = Path.home() / ".environment_dev_v2"
    
    # Executar migração
    try:
        summary = migrate_legacy_configurations(target_dir, search_paths)
        
        print("\n=== Resumo da Migração ===")
        print(f"Configurações encontradas: {summary['total_configs']}")
        print(f"Migrações bem-sucedidas: {summary['successful_migrations']}")
        print(f"Migrações falharam: {summary['failed_migrations']}")
        print(f"Itens migrados: {summary['total_items_migrated']}")
        print(f"Itens ignorados: {summary['total_items_skipped']}")
        print(f"Tempo total: {summary['duration']:.2f}s")
        
    except Exception as e:
        print(f"Erro na migração: {e}")