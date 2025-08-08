# -*- coding: utf-8 -*-
"""
Configuration Manager Aprimorado para Environment Dev Script
Sistema robusto de configuração com validação de esquemas YAML,
migração automática e versionamento
"""

import os
import logging
import yaml
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import jsonschema
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)

class ConfigFormat(Enum):
    """Formatos de configuração suportados"""
    YAML = "yaml"
    JSON = "json"
    INI = "ini"

class ConfigVersion(Enum):
    """Versões de configuração"""
    V1_0 = "1.0"
    V1_1 = "1.1"
    V2_0 = "2.0"
    CURRENT = "2.0"

@dataclass
class ConfigValidationResult:
    """Resultado da validação de configuração"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    schema_version: Optional[str] = None
    config_version: Optional[str] = None

@dataclass
class MigrationResult:
    """Resultado da migração de configuração"""
    success: bool
    from_version: str
    to_version: str
    changes_made: List[str] = field(default_factory=list)
    backup_path: Optional[str] = None
    errors: List[str] = field(default_factory=list)

class EnhancedConfigurationManager:
    """
    Gerenciador de configuração aprimorado com:
    - Validação robusta de esquemas YAML/JSON
    - Migração automática de configurações antigas
    - Versionamento de configurações
    - Backup automático antes de mudanças
    """
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.config_dir = self.base_path / "config"
        self.schemas_dir = self.config_dir / "schemas"
        self.backups_dir = self.config_dir / "backups"
        
        # Cria diretórios necessários
        for directory in [self.config_dir, self.schemas_dir, self.backups_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Cache de configurações carregadas
        self.config_cache: Dict[str, Dict[str, Any]] = {}
        self.schemas_cache: Dict[str, Dict[str, Any]] = {}
        
        # Configurações do sistema
        self.current_version = ConfigVersion.CURRENT.value
        self.auto_migrate = True
        self.create_backups = True
        
        # Inicializa esquemas padrão
        self._initialize_default_schemas()
        
        logger.info("Enhanced Configuration Manager inicializado")
    
    def load_config(self, config_name: str, validate_schema: bool = True,
                   auto_migrate: bool = None) -> Dict[str, Any]:
        """
        Carrega configuração com validação e migração automática
        
        Args:
            config_name: Nome da configuração (sem extensão)
            validate_schema: Se deve validar contra esquema
            auto_migrate: Se deve migrar automaticamente (None = usar padrão)
            
        Returns:
            Dict: Configuração carregada e validada
        """
        logger.info(f"Carregando configuração: {config_name}")
        
        # Verifica cache primeiro
        if config_name in self.config_cache:
            logger.debug(f"Configuração {config_name} obtida do cache")
            return self.config_cache[config_name].copy()
        
        # Encontra arquivo de configuração
        config_file = self._find_config_file(config_name)
        if not config_file:
            raise FileNotFoundError(f"Configuração {config_name} não encontrada")
        
        # Carrega configuração
        config_data = self._load_config_file(config_file)
        
        # Verifica versão e migra se necessário
        if auto_migrate is None:
            auto_migrate = self.auto_migrate
        
        if auto_migrate:
            config_data = self._check_and_migrate_config(config_name, config_data, config_file)
        
        # Valida esquema se solicitado
        if validate_schema:
            validation_result = self.validate_config_schema(config_name, config_data)
            if not validation_result.is_valid:
                error_msg = f"Configuração {config_name} inválida: {validation_result.errors}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    logger.warning(f"Configuração {config_name}: {warning}")
        
        # Adiciona ao cache
        self.config_cache[config_name] = config_data.copy()
        
        logger.info(f"Configuração {config_name} carregada com sucesso")
        return config_data
    
    def save_config(self, config_name: str, config_data: Dict[str, Any],
                   format_type: ConfigFormat = ConfigFormat.YAML,
                   validate_before_save: bool = True) -> bool:
        """
        Salva configuração com validação e backup
        
        Args:
            config_name: Nome da configuração
            config_data: Dados da configuração
            format_type: Formato do arquivo
            validate_before_save: Se deve validar antes de salvar
            
        Returns:
            bool: True se salvou com sucesso
        """
        logger.info(f"Salvando configuração: {config_name}")
        
        try:
            # Valida antes de salvar se solicitado
            if validate_before_save:
                validation_result = self.validate_config_schema(config_name, config_data)
                if not validation_result.is_valid:
                    logger.error(f"Configuração inválida: {validation_result.errors}")
                    return False
            
            # Adiciona metadados de versão
            config_with_metadata = config_data.copy()
            config_with_metadata['_metadata'] = {
                'version': self.current_version,
                'created_at': datetime.now().isoformat(),
                'format': format_type.value
            }
            
            # Determina arquivo de destino
            config_file = self.config_dir / f"{config_name}.{format_type.value}"
            
            # Cria backup se arquivo existir
            if config_file.exists() and self.create_backups:
                self._create_config_backup(config_file)
            
            # Salva configuração
            if format_type == ConfigFormat.YAML:
                with open(config_file, 'w', encoding='utf-8') as f:
                    yaml.dump(config_with_metadata, f, default_flow_style=False, 
                             allow_unicode=True, indent=2)
            elif format_type == ConfigFormat.JSON:
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config_with_metadata, f, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"Formato {format_type} não suportado para salvamento")
            
            # Atualiza cache
            self.config_cache[config_name] = config_data.copy()
            
            logger.info(f"Configuração {config_name} salva com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar configuração {config_name}: {e}")
            return False
    
    def validate_config_schema(self, config_name: str, 
                              config_data: Dict[str, Any]) -> ConfigValidationResult:
        """
        Valida configuração contra esquema YAML/JSON
        
        Args:
            config_name: Nome da configuração
            config_data: Dados para validar
            
        Returns:
            ConfigValidationResult: Resultado da validação
        """
        logger.debug(f"Validando esquema da configuração: {config_name}")
        
        result = ConfigValidationResult(is_valid=True)
        
        try:
            # Carrega esquema
            schema = self._load_schema(config_name)
            if not schema:
                result.warnings.append(f"Esquema não encontrado para {config_name}")
                return result
            
            # Extrai versão da configuração
            config_version = config_data.get('_metadata', {}).get('version', '1.0')
            result.config_version = config_version
            result.schema_version = schema.get('version', '1.0')
            
            # Valida usando jsonschema
            validate(instance=config_data, schema=schema)
            
            # Validações customizadas adicionais
            custom_errors = self._perform_custom_validations(config_name, config_data)
            if custom_errors:
                result.errors.extend(custom_errors)
                result.is_valid = False
            
            logger.debug(f"Validação de esquema concluída: {'✓' if result.is_valid else '✗'}")
            
        except ValidationError as e:
            result.is_valid = False
            result.errors.append(f"Erro de validação: {e.message}")
            if e.path:
                result.errors.append(f"Caminho: {' -> '.join(str(p) for p in e.path)}")
        except Exception as e:
            result.is_valid = False
            result.errors.append(f"Erro inesperado na validação: {e}")
        
        return result
    
    def migrate_config(self, config_name: str, target_version: str = None) -> MigrationResult:
        """
        Migra configuração para versão mais recente
        
        Args:
            config_name: Nome da configuração
            target_version: Versão de destino (None = versão atual)
            
        Returns:
            MigrationResult: Resultado da migração
        """
        if target_version is None:
            target_version = self.current_version
        
        logger.info(f"Migrando configuração {config_name} para versão {target_version}")
        
        # Encontra arquivo de configuração
        config_file = self._find_config_file(config_name)
        if not config_file:
            return MigrationResult(
                success=False,
                from_version="unknown",
                to_version=target_version,
                errors=[f"Configuração {config_name} não encontrada"]
            )
        
        # Carrega configuração atual
        config_data = self._load_config_file(config_file)
        current_version = config_data.get('_metadata', {}).get('version', '1.0')
        
        result = MigrationResult(
            success=False,
            from_version=current_version,
            to_version=target_version
        )
        
        # Verifica se migração é necessária
        if current_version == target_version:
            result.success = True
            result.changes_made.append("Nenhuma migração necessária - versão já atual")
            return result
        
        try:
            # Cria backup antes da migração
            if self.create_backups:
                backup_path = self._create_config_backup(config_file)
                result.backup_path = str(backup_path)
            
            # Executa migração
            migrated_data = self._perform_migration(config_data, current_version, target_version)
            
            if migrated_data:
                # Salva configuração migrada
                success = self.save_config(config_name, migrated_data, validate_before_save=True)
                
                if success:
                    result.success = True
                    result.changes_made.append(f"Migração de {current_version} para {target_version}")
                    
                    # Remove do cache para forçar recarregamento
                    if config_name in self.config_cache:
                        del self.config_cache[config_name]
                    
                    logger.info(f"Migração de {config_name} concluída com sucesso")
                else:
                    result.errors.append("Falha ao salvar configuração migrada")
            else:
                result.errors.append("Falha na execução da migração")
        
        except Exception as e:
            logger.error(f"Erro na migração de {config_name}: {e}")
            result.errors.append(str(e))
        
        return result
    
    def create_config_template(self, config_name: str, 
                              template_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Cria template de configuração com valores padrão
        
        Args:
            config_name: Nome da configuração
            template_data: Dados do template (None = usar padrão)
            
        Returns:
            bool: True se criou com sucesso
        """
        logger.info(f"Criando template de configuração: {config_name}")
        
        try:
            if template_data is None:
                template_data = self._get_default_template(config_name)
            
            # Adiciona metadados
            template_with_metadata = template_data.copy()
            template_with_metadata['_metadata'] = {
                'version': self.current_version,
                'created_at': datetime.now().isoformat(),
                'is_template': True,
                'description': f"Template de configuração para {config_name}"
            }
            
            # Salva template
            template_file = self.config_dir / f"{config_name}_template.yaml"
            
            with open(template_file, 'w', encoding='utf-8') as f:
                yaml.dump(template_with_metadata, f, default_flow_style=False,
                         allow_unicode=True, indent=2)
            
            logger.info(f"Template {config_name} criado: {template_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar template {config_name}: {e}")
            return False
    
    def get_config_info(self, config_name: str) -> Dict[str, Any]:
        """
        Obtém informações detalhadas sobre uma configuração
        
        Args:
            config_name: Nome da configuração
            
        Returns:
            Dict: Informações da configuração
        """
        info = {
            'name': config_name,
            'exists': False,
            'file_path': None,
            'format': None,
            'version': None,
            'size': 0,
            'last_modified': None,
            'is_cached': config_name in self.config_cache,
            'validation_status': None,
            'schema_available': False
        }
        
        try:
            # Encontra arquivo
            config_file = self._find_config_file(config_name)
            if config_file:
                info['exists'] = True
                info['file_path'] = str(config_file)
                info['format'] = config_file.suffix[1:]  # Remove o ponto
                
                # Informações do arquivo
                stat = config_file.stat()
                info['size'] = stat.st_size
                info['last_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                
                # Carrega para obter versão
                config_data = self._load_config_file(config_file)
                info['version'] = config_data.get('_metadata', {}).get('version', 'unknown')
                
                # Verifica se há esquema
                schema = self._load_schema(config_name)
                info['schema_available'] = schema is not None
                
                # Valida se há esquema
                if schema:
                    validation_result = self.validate_config_schema(config_name, config_data)
                    info['validation_status'] = 'valid' if validation_result.is_valid else 'invalid'
                    if not validation_result.is_valid:
                        info['validation_errors'] = validation_result.errors
        
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    def list_configurations(self) -> List[Dict[str, Any]]:
        """
        Lista todas as configurações disponíveis
        
        Returns:
            List: Lista de informações das configurações
        """
        configurations = []
        
        try:
            # Procura arquivos de configuração
            for config_file in self.config_dir.glob("*.yaml"):
                if not config_file.name.endswith("_template.yaml"):
                    config_name = config_file.stem
                    info = self.get_config_info(config_name)
                    configurations.append(info)
            
            for config_file in self.config_dir.glob("*.json"):
                if not config_file.name.endswith("_template.json"):
                    config_name = config_file.stem
                    # Evita duplicatas se já foi processado como YAML
                    if not any(c['name'] == config_name for c in configurations):
                        info = self.get_config_info(config_name)
                        configurations.append(info)
        
        except Exception as e:
            logger.error(f"Erro ao listar configurações: {e}")
        
        return configurations
    
    def cleanup_old_backups(self, max_age_days: int = 30, max_count: int = 10) -> int:
        """
        Limpa backups antigos de configuração
        
        Args:
            max_age_days: Idade máxima em dias
            max_count: Número máximo de backups por configuração
            
        Returns:
            int: Número de backups removidos
        """
        logger.info(f"Limpando backups antigos (>{max_age_days} dias, >{max_count} por config)")
        
        removed_count = 0
        cutoff_date = datetime.now().timestamp() - (max_age_days * 24 * 3600)
        
        try:
            # Agrupa backups por configuração
            backup_groups = {}
            
            for backup_file in self.backups_dir.glob("*.backup"):
                # Extrai nome da configuração do nome do arquivo
                # Formato: config_name_YYYYMMDD_HHMMSS.backup
                parts = backup_file.stem.split('_')
                if len(parts) >= 3:
                    config_name = '_'.join(parts[:-2])  # Reconstrói nome original
                    
                    if config_name not in backup_groups:
                        backup_groups[config_name] = []
                    
                    backup_groups[config_name].append(backup_file)
            
            # Processa cada grupo
            for config_name, backups in backup_groups.items():
                # Ordena por data de modificação (mais recente primeiro)
                backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                # Remove backups antigos
                for backup_file in backups:
                    should_remove = False
                    
                    # Remove se muito antigo
                    if backup_file.stat().st_mtime < cutoff_date:
                        should_remove = True
                    
                    # Remove se excede contagem máxima
                    elif len(backups) > max_count and backup_file in backups[max_count:]:
                        should_remove = True
                    
                    if should_remove:
                        try:
                            backup_file.unlink()
                            removed_count += 1
                            logger.debug(f"Backup removido: {backup_file.name}")
                        except Exception as e:
                            logger.warning(f"Erro ao remover backup {backup_file}: {e}")
        
        except Exception as e:
            logger.error(f"Erro na limpeza de backups: {e}")
        
        logger.info(f"Limpeza concluída: {removed_count} backups removidos")
        return removed_count    

    # Métodos auxiliares privados
    def _find_config_file(self, config_name: str) -> Optional[Path]:
        """Encontra arquivo de configuração por nome"""
        # Prioridade: YAML > JSON > INI
        for extension in ['yaml', 'yml', 'json']:
            config_file = self.config_dir / f"{config_name}.{extension}"
            if config_file.exists():
                return config_file
        return None
    
    def _load_config_file(self, config_file: Path) -> Dict[str, Any]:
        """Carrega arquivo de configuração baseado na extensão"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(f) or {}
                elif config_file.suffix.lower() == '.json':
                    return json.load(f) or {}
                else:
                    raise ValueError(f"Formato não suportado: {config_file.suffix}")
        except Exception as e:
            logger.error(f"Erro ao carregar {config_file}: {e}")
            raise
    
    def _load_schema(self, config_name: str) -> Optional[Dict[str, Any]]:
        """Carrega esquema de validação para uma configuração"""
        if config_name in self.schemas_cache:
            return self.schemas_cache[config_name]
        
        schema_file = self.schemas_dir / f"{config_name}_schema.json"
        
        if not schema_file.exists():
            return None
        
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema = json.load(f)
                self.schemas_cache[config_name] = schema
                return schema
        except Exception as e:
            logger.error(f"Erro ao carregar esquema {schema_file}: {e}")
            return None
    
    def _check_and_migrate_config(self, config_name: str, config_data: Dict[str, Any], 
                                 config_file: Path) -> Dict[str, Any]:
        """Verifica versão e migra configuração se necessário"""
        current_version = config_data.get('_metadata', {}).get('version', '1.0')
        
        if current_version != self.current_version:
            logger.info(f"Migrando {config_name} de {current_version} para {self.current_version}")
            
            migration_result = self.migrate_config(config_name, self.current_version)
            
            if migration_result.success:
                # Recarrega configuração migrada
                return self._load_config_file(config_file)
            else:
                logger.warning(f"Falha na migração de {config_name}: {migration_result.errors}")
        
        return config_data
    
    def _perform_migration(self, config_data: Dict[str, Any], 
                          from_version: str, to_version: str) -> Optional[Dict[str, Any]]:
        """Executa migração de configuração entre versões"""
        try:
            migrated_data = config_data.copy()
            
            # Migração 1.0 -> 1.1
            if from_version == "1.0" and to_version >= "1.1":
                migrated_data = self._migrate_v1_0_to_v1_1(migrated_data)
            
            # Migração 1.1 -> 2.0
            if from_version <= "1.1" and to_version >= "2.0":
                migrated_data = self._migrate_v1_1_to_v2_0(migrated_data)
            
            # Atualiza metadados
            if '_metadata' not in migrated_data:
                migrated_data['_metadata'] = {}
            
            migrated_data['_metadata'].update({
                'version': to_version,
                'migrated_at': datetime.now().isoformat(),
                'previous_version': from_version
            })
            
            return migrated_data
            
        except Exception as e:
            logger.error(f"Erro na migração: {e}")
            return None
    
    def _migrate_v1_0_to_v1_1(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migra configuração da versão 1.0 para 1.1"""
        migrated = config_data.copy()
        
        # Exemplo de migração: renomeia campos antigos
        if 'old_field_name' in migrated:
            migrated['new_field_name'] = migrated.pop('old_field_name')
        
        # Adiciona novos campos com valores padrão
        if 'new_feature_enabled' not in migrated:
            migrated['new_feature_enabled'] = True
        
        return migrated
    
    def _migrate_v1_1_to_v2_0(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migra configuração da versão 1.1 para 2.0"""
        migrated = config_data.copy()
        
        # Exemplo: reestrutura configurações aninhadas
        if 'legacy_settings' in migrated:
            legacy = migrated.pop('legacy_settings')
            migrated['advanced_settings'] = {
                'feature_flags': legacy.get('flags', {}),
                'performance': legacy.get('perf', {}),
                'security': legacy.get('sec', {})
            }
        
        # Adiciona configurações de segurança obrigatórias
        if 'security' not in migrated:
            migrated['security'] = {
                'encryption_enabled': True,
                'audit_logging': True,
                'input_validation': True
            }
        
        return migrated
    
    def _perform_custom_validations(self, config_name: str, 
                                   config_data: Dict[str, Any]) -> List[str]:
        """Executa validações customizadas específicas por configuração"""
        errors = []
        
        try:
            # Validações específicas por tipo de configuração
            if config_name == 'components':
                errors.extend(self._validate_components_config(config_data))
            elif config_name == 'security':
                errors.extend(self._validate_security_config(config_data))
            elif config_name == 'download':
                errors.extend(self._validate_download_config(config_data))
            
            # Validações gerais
            errors.extend(self._validate_general_config(config_data))
            
        except Exception as e:
            errors.append(f"Erro na validação customizada: {e}")
        
        return errors
    
    def _validate_components_config(self, config_data: Dict[str, Any]) -> List[str]:
        """Valida configuração de componentes"""
        errors = []
        
        components = config_data.get('components', {})
        
        for comp_name, comp_config in components.items():
            # Verifica campos obrigatórios
            required_fields = ['download_url', 'checksum', 'install_method']
            for field in required_fields:
                if field not in comp_config:
                    errors.append(f"Componente {comp_name}: campo obrigatório '{field}' ausente")
            
            # Valida URL
            download_url = comp_config.get('download_url', '')
            if download_url and not (download_url.startswith('http://') or download_url.startswith('https://')):
                errors.append(f"Componente {comp_name}: URL inválida")
            
            # Valida checksum
            checksum = comp_config.get('checksum', {})
            if isinstance(checksum, dict):
                if 'value' not in checksum or 'algorithm' not in checksum:
                    errors.append(f"Componente {comp_name}: checksum deve ter 'value' e 'algorithm'")
        
        return errors
    
    def _validate_security_config(self, config_data: Dict[str, Any]) -> List[str]:
        """Valida configuração de segurança"""
        errors = []
        
        security = config_data.get('security', {})
        
        # Verifica configurações críticas
        if not security.get('encryption_enabled', False):
            errors.append("Criptografia deve estar habilitada em produção")
        
        if not security.get('input_validation', False):
            errors.append("Validação de entrada deve estar habilitada")
        
        # Valida configurações de auditoria
        audit_config = security.get('audit', {})
        if audit_config.get('enabled', False):
            if not audit_config.get('log_file'):
                errors.append("Arquivo de log de auditoria deve ser especificado")
        
        return errors
    
    def _validate_download_config(self, config_data: Dict[str, Any]) -> List[str]:
        """Valida configuração de download"""
        errors = []
        
        download = config_data.get('download', {})
        
        # Valida timeouts
        timeout = download.get('timeout', 30)
        if not isinstance(timeout, int) or timeout <= 0:
            errors.append("Timeout de download deve ser um número positivo")
        
        # Valida número máximo de tentativas
        max_retries = download.get('max_retries', 3)
        if not isinstance(max_retries, int) or max_retries < 0:
            errors.append("Número máximo de tentativas deve ser um número não-negativo")
        
        return errors
    
    def _validate_general_config(self, config_data: Dict[str, Any]) -> List[str]:
        """Validações gerais aplicáveis a todas as configurações"""
        errors = []
        
        # Verifica metadados
        metadata = config_data.get('_metadata', {})
        if not metadata.get('version'):
            errors.append("Versão da configuração deve ser especificada nos metadados")
        
        # Verifica se não há campos com valores None críticos
        def check_none_values(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if value is None and key in ['download_url', 'checksum', 'install_method']:
                        errors.append(f"Campo crítico '{current_path}' não pode ser None")
                    elif isinstance(value, (dict, list)):
                        check_none_values(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_none_values(item, f"{path}[{i}]")
        
        check_none_values(config_data)
        
        return errors
    
    def _create_config_backup(self, config_file: Path) -> Path:
        """Cria backup de um arquivo de configuração"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{config_file.stem}_{timestamp}.backup"
        backup_path = self.backups_dir / backup_name
        
        shutil.copy2(config_file, backup_path)
        logger.debug(f"Backup criado: {backup_path}")
        
        return backup_path
    
    def _initialize_default_schemas(self):
        """Inicializa esquemas padrão para validação"""
        # Esquema para configuração de componentes
        components_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Components Configuration Schema",
            "version": "2.0",
            "type": "object",
            "properties": {
                "_metadata": {
                    "type": "object",
                    "properties": {
                        "version": {"type": "string"},
                        "created_at": {"type": "string"},
                        "format": {"type": "string"}
                    },
                    "required": ["version"]
                },
                "components": {
                    "type": "object",
                    "patternProperties": {
                        "^[a-zA-Z0-9_-]+$": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "version": {"type": "string"},
                                "description": {"type": "string"},
                                "download_url": {
                                    "type": "string",
                                    "pattern": "^https?://.+"
                                },
                                "checksum": {
                                    "type": "object",
                                    "properties": {
                                        "value": {"type": "string"},
                                        "algorithm": {
                                            "type": "string",
                                            "enum": ["md5", "sha1", "sha256", "sha512"]
                                        }
                                    },
                                    "required": ["value", "algorithm"]
                                },
                                "install_method": {
                                    "type": "string",
                                    "enum": ["executable", "msi", "archive", "script"]
                                },
                                "dependencies": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "conflicts": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "required": ["download_url", "checksum", "install_method"]
                        }
                    }
                }
            },
            "required": ["_metadata", "components"]
        }
        
        # Esquema para configuração de segurança
        security_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Security Configuration Schema",
            "version": "2.0",
            "type": "object",
            "properties": {
                "_metadata": {
                    "type": "object",
                    "properties": {
                        "version": {"type": "string"},
                        "created_at": {"type": "string"}
                    },
                    "required": ["version"]
                },
                "security": {
                    "type": "object",
                    "properties": {
                        "encryption_enabled": {"type": "boolean"},
                        "input_validation": {"type": "boolean"},
                        "audit_logging": {"type": "boolean"},
                        "max_input_length": {"type": "integer", "minimum": 1},
                        "allowed_file_extensions": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "blocked_file_extensions": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "trusted_domains": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["encryption_enabled", "input_validation"]
                }
            },
            "required": ["_metadata", "security"]
        }
        
        # Salva esquemas se não existirem
        schemas = {
            "components": components_schema,
            "security": security_schema
        }
        
        for schema_name, schema_data in schemas.items():
            schema_file = self.schemas_dir / f"{schema_name}_schema.json"
            
            if not schema_file.exists():
                try:
                    with open(schema_file, 'w', encoding='utf-8') as f:
                        json.dump(schema_data, f, indent=2, ensure_ascii=False)
                    logger.debug(f"Esquema padrão criado: {schema_file}")
                except Exception as e:
                    logger.error(f"Erro ao criar esquema {schema_name}: {e}")
    
    def _get_default_template(self, config_name: str) -> Dict[str, Any]:
        """Retorna template padrão para uma configuração"""
        templates = {
            "components": {
                "components": {
                    "example_component": {
                        "name": "Example Component",
                        "version": "1.0.0",
                        "description": "Exemplo de componente",
                        "download_url": "https://example.com/download.exe",
                        "checksum": {
                            "value": "abcdef1234567890",
                            "algorithm": "sha256"
                        },
                        "install_method": "executable",
                        "dependencies": [],
                        "conflicts": []
                    }
                }
            },
            "security": {
                "security": {
                    "encryption_enabled": True,
                    "input_validation": True,
                    "audit_logging": True,
                    "max_input_length": 65536,
                    "allowed_file_extensions": [".txt", ".json", ".yaml"],
                    "blocked_file_extensions": [".exe", ".bat", ".cmd"],
                    "trusted_domains": ["github.com", "microsoft.com"]
                }
            },
            "download": {
                "download": {
                    "timeout": 30,
                    "max_retries": 3,
                    "chunk_size": 8192,
                    "verify_ssl": True,
                    "user_agent": "Environment-Dev-Script/2.0"
                }
            }
        }
        
        return templates.get(config_name, {
            "example_setting": "example_value",
            "description": f"Template padrão para {config_name}"
        })
    
    def get_configuration_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do gerenciador de configuração
        
        Returns:
            Dict: Estatísticas detalhadas
        """
        stats = {
            "total_configurations": 0,
            "cached_configurations": len(self.config_cache),
            "available_schemas": len(self.schemas_cache),
            "current_version": self.current_version,
            "auto_migrate_enabled": self.auto_migrate,
            "backup_creation_enabled": self.create_backups,
            "configuration_formats": {"yaml": 0, "json": 0, "ini": 0},
            "total_backups": 0,
            "directories": {
                "config": str(self.config_dir),
                "schemas": str(self.schemas_dir),
                "backups": str(self.backups_dir)
            }
        }
        
        try:
            # Conta configurações por formato
            for config_file in self.config_dir.glob("*"):
                if config_file.is_file() and not config_file.name.endswith("_template.yaml"):
                    stats["total_configurations"] += 1
                    
                    if config_file.suffix.lower() in ['.yaml', '.yml']:
                        stats["configuration_formats"]["yaml"] += 1
                    elif config_file.suffix.lower() == '.json':
                        stats["configuration_formats"]["json"] += 1
                    elif config_file.suffix.lower() == '.ini':
                        stats["configuration_formats"]["ini"] += 1
            
            # Conta backups
            if self.backups_dir.exists():
                stats["total_backups"] = len(list(self.backups_dir.glob("*.backup")))
            
            # Conta esquemas disponíveis no disco
            if self.schemas_dir.exists():
                stats["schemas_on_disk"] = len(list(self.schemas_dir.glob("*_schema.json")))
            
        except Exception as e:
            stats["error"] = str(e)
        
        return stats


# Instância global do gerenciador de configuração aprimorado
enhanced_config_manager = EnhancedConfigurationManager()