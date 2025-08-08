# -*- coding: utf-8 -*-
"""
Integrity Validator para Environment Dev Script
Sistema completo de validação de integridade com certificados SSL,
sanitização de logs e criptografia de configurações
"""

import os
import logging
import hashlib
import ssl
import socket
import json
import base64
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from urllib.parse import urlparse
import tempfile

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography import x509
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False
    logger.warning("Cryptography library not available - some features will be disabled")

logger = logging.getLogger(__name__)

class IntegrityStatus(Enum):
    """Status de integridade"""
    VALID = "valid"
    INVALID = "invalid"
    CORRUPTED = "corrupted"
    MISSING = "missing"
    UNKNOWN = "unknown"

class CertificateStatus(Enum):
    """Status do certificado"""
    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    UNTRUSTED = "untrusted"
    INVALID = "invalid"

@dataclass
class IntegrityResult:
    """Resultado da validação de integridade"""
    file_path: str
    status: IntegrityStatus
    expected_hash: Optional[str] = None
    calculated_hash: Optional[str] = None
    algorithm: str = "sha256"
    file_size: int = 0
    last_modified: Optional[datetime] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class CertificateValidationResult:
    """Resultado da validação de certificado"""
    hostname: str
    status: CertificateStatus
    certificate_info: Dict[str, Any] = field(default_factory=dict)
    chain_valid: bool = False
    expiry_date: Optional[datetime] = None
    issuer: Optional[str] = None
    subject: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class EncryptionResult:
    """Resultado da operação de criptografia"""
    success: bool
    encrypted_data: Optional[bytes] = None
    decrypted_data: Optional[str] = None
    key_id: Optional[str] = None
    algorithm: str = "Fernet"
    error_message: Optional[str] = None

class IntegrityValidator:
    """
    Validador de integridade completo com suporte a:
    - Validação de certificados SSL
    - Sanitização de logs
    - Criptografia de configurações
    - Proteção de backups
    """
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.config_dir = self.base_path / "config"
        self.keys_dir = self.base_path / "keys"
        self.logs_dir = self.base_path / "logs"
        
        # Cria diretórios necessários
        for directory in [self.config_dir, self.keys_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Configurações de segurança
        self.encryption_keys: Dict[str, bytes] = {}
        self.trusted_ca_certs: Set[str] = set()
        self.sensitive_patterns = self._load_sensitive_patterns()
        
        # Inicializa sistema de criptografia
        if HAS_CRYPTOGRAPHY:
            self._initialize_encryption()
        
        logger.info("Integrity Validator inicializado")
    
    def validate_file_integrity(self, file_path: str, expected_hash: str, 
                               algorithm: str = "sha256") -> IntegrityResult:
        """
        Valida integridade de um arquivo usando hash
        
        Args:
            file_path: Caminho do arquivo
            expected_hash: Hash esperado
            algorithm: Algoritmo de hash
            
        Returns:
            IntegrityResult: Resultado da validação
        """
        logger.debug(f"Validando integridade: {file_path}")
        
        file_path_obj = Path(file_path)
        
        result = IntegrityResult(
            file_path=file_path,
            expected_hash=expected_hash,
            algorithm=algorithm,
            status=IntegrityStatus.UNKNOWN
        )
        
        try:
            # Verifica se arquivo existe
            if not file_path_obj.exists():
                result.status = IntegrityStatus.MISSING
                result.details["error"] = "Arquivo não encontrado"
                return result
            
            # Obtém informações do arquivo
            stat_info = file_path_obj.stat()
            result.file_size = stat_info.st_size
            result.last_modified = datetime.fromtimestamp(stat_info.st_mtime)
            
            # Calcula hash do arquivo
            calculated_hash = self._calculate_file_hash(file_path_obj, algorithm)
            result.calculated_hash = calculated_hash
            
            # Compara hashes
            if calculated_hash.lower() == expected_hash.lower():
                result.status = IntegrityStatus.VALID
                result.details["message"] = "Integridade verificada com sucesso"
            else:
                result.status = IntegrityStatus.INVALID
                result.details["error"] = "Hash não confere"
                result.details["hash_mismatch"] = {
                    "expected": expected_hash,
                    "calculated": calculated_hash
                }
            
            logger.debug(f"Validação concluída: {result.status.value}")
            return result
            
        except Exception as e:
            logger.error(f"Erro na validação de integridade: {e}")
            result.status = IntegrityStatus.CORRUPTED
            result.details["error"] = str(e)
            return result
    
    def validate_ssl_certificate(self, hostname: str, port: int = 443, 
                                timeout: int = 10) -> CertificateValidationResult:
        """
        Valida certificado SSL de um servidor (Requisito 11.2)
        
        Args:
            hostname: Nome do host
            port: Porta (padrão: 443)
            timeout: Timeout em segundos
            
        Returns:
            CertificateValidationResult: Resultado da validação
        """
        logger.debug(f"Validando certificado SSL: {hostname}:{port}")
        
        result = CertificateValidationResult(
            hostname=hostname,
            status=CertificateStatus.UNKNOWN
        )
        
        try:
            # Cria contexto SSL
            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            
            # Conecta ao servidor
            with socket.create_connection((hostname, port), timeout=timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # Obtém certificado
                    cert_der = ssock.getpeercert(binary_form=True)
                    cert_info = ssock.getpeercert()
                    
                    if HAS_CRYPTOGRAPHY and cert_der:
                        # Análise detalhada com cryptography
                        cert = x509.load_der_x509_certificate(cert_der)
                        
                        # Informações básicas
                        result.subject = cert.subject.rfc4514_string()
                        result.issuer = cert.issuer.rfc4514_string()
                        result.expiry_date = cert.not_valid_after
                        
                        # Verifica validade temporal
                        now = datetime.utcnow()
                        if cert.not_valid_before <= now <= cert.not_valid_after:
                            result.status = CertificateStatus.VALID
                        elif now > cert.not_valid_after:
                            result.status = CertificateStatus.EXPIRED
                            result.errors.append("Certificado expirado")
                        else:
                            result.status = CertificateStatus.INVALID
                            result.errors.append("Certificado ainda não válido")
                        
                        # Informações detalhadas
                        result.certificate_info = {
                            "version": cert.version.name,
                            "serial_number": str(cert.serial_number),
                            "not_valid_before": cert.not_valid_before.isoformat(),
                            "not_valid_after": cert.not_valid_after.isoformat(),
                            "signature_algorithm": cert.signature_algorithm_oid._name,
                            "public_key_algorithm": cert.public_key().__class__.__name__
                        }
                        
                        # Verifica SAN (Subject Alternative Names)
                        try:
                            san_ext = cert.extensions.get_extension_for_oid(x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
                            san_names = [name.value for name in san_ext.value]
                            result.certificate_info["san"] = san_names
                            
                            # Verifica se hostname está no SAN
                            if hostname not in san_names:
                                result.warnings.append(f"Hostname {hostname} não encontrado no SAN")
                        except x509.ExtensionNotFound:
                            result.warnings.append("Extensão SAN não encontrada")
                        
                        # Verifica uso da chave
                        try:
                            key_usage = cert.extensions.get_extension_for_oid(x509.ExtensionOID.KEY_USAGE)
                            result.certificate_info["key_usage"] = {
                                "digital_signature": key_usage.value.digital_signature,
                                "key_encipherment": key_usage.value.key_encipherment,
                                "key_agreement": key_usage.value.key_agreement if hasattr(key_usage.value, 'key_agreement') else False
                            }
                        except x509.ExtensionNotFound:
                            result.warnings.append("Extensão Key Usage não encontrada")
                        
                        result.chain_valid = True
                        
                    else:
                        # Fallback para validação básica
                        if cert_info:
                            result.subject = cert_info.get('subject', [])
                            result.issuer = cert_info.get('issuer', [])
                            
                            # Verifica expiração
                            not_after = cert_info.get('notAfter')
                            if not_after:
                                expiry = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                                result.expiry_date = expiry
                                
                                if datetime.utcnow() > expiry:
                                    result.status = CertificateStatus.EXPIRED
                                    result.errors.append("Certificado expirado")
                                else:
                                    result.status = CertificateStatus.VALID
                            
                            result.certificate_info = cert_info
                            result.chain_valid = True
            
            logger.debug(f"Validação SSL concluída: {result.status.value}")
            return result
            
        except ssl.SSLError as e:
            logger.warning(f"Erro SSL para {hostname}: {e}")
            result.status = CertificateStatus.INVALID
            result.errors.append(f"Erro SSL: {e}")
            return result
        except socket.timeout:
            logger.warning(f"Timeout na conexão com {hostname}")
            result.status = CertificateStatus.UNKNOWN
            result.errors.append("Timeout na conexão")
            return result
        except Exception as e:
            logger.error(f"Erro na validação SSL: {e}")
            result.status = CertificateStatus.INVALID
            result.errors.append(f"Erro inesperado: {e}")
            return result
    
    def sanitize_log_data(self, log_data: str, preserve_structure: bool = True) -> str:
        """
        Sanitiza dados de log removendo informações sensíveis (Requisito 11.2)
        
        Args:
            log_data: Dados do log para sanitizar
            preserve_structure: Se deve preservar estrutura dos dados
            
        Returns:
            str: Dados sanitizados
        """
        logger.debug("Sanitizando dados de log")
        
        sanitized_data = log_data
        
        try:
            # Aplica padrões de sanitização
            for pattern_name, pattern_info in self.sensitive_patterns.items():
                regex_pattern = pattern_info["pattern"]
                replacement = pattern_info.get("replacement", "[REDACTED]")
                
                if preserve_structure and pattern_info.get("preserve_length", False):
                    # Preserva comprimento original
                    def length_preserving_replacement(match):
                        original = match.group(0)
                        if len(original) <= 4:
                            return "*" * len(original)
                        else:
                            # Mostra primeiros e últimos caracteres
                            return original[:2] + "*" * (len(original) - 4) + original[-2:]
                    
                    sanitized_data = re.sub(regex_pattern, length_preserving_replacement, sanitized_data, flags=re.IGNORECASE)
                else:
                    sanitized_data = re.sub(regex_pattern, replacement, sanitized_data, flags=re.IGNORECASE)
            
            # Sanitização adicional para estruturas JSON
            if self._is_json_like(sanitized_data):
                sanitized_data = self._sanitize_json_structure(sanitized_data)
            
            logger.debug("Sanitização de log concluída")
            return sanitized_data
            
        except Exception as e:
            logger.error(f"Erro na sanitização de log: {e}")
            # Em caso de erro, retorna versão mais conservadora
            return "[LOG DATA SANITIZATION ERROR]"
    
    def encrypt_configuration(self, config_data: str, key_id: str = "default") -> EncryptionResult:
        """
        Criptografa dados de configuração sensíveis (Requisito 11.2)
        
        Args:
            config_data: Dados de configuração para criptografar
            key_id: ID da chave de criptografia
            
        Returns:
            EncryptionResult: Resultado da criptografia
        """
        logger.debug(f"Criptografando configuração com chave: {key_id}")
        
        if not HAS_CRYPTOGRAPHY:
            return EncryptionResult(
                success=False,
                error_message="Biblioteca cryptography não disponível"
            )
        
        try:
            # Obtém ou gera chave
            encryption_key = self._get_or_create_key(key_id)
            
            # Criptografa dados
            fernet = Fernet(encryption_key)
            encrypted_data = fernet.encrypt(config_data.encode('utf-8'))
            
            # Salva dados criptografados
            encrypted_file = self.config_dir / f"{key_id}_encrypted.dat"
            with open(encrypted_file, 'wb') as f:
                f.write(encrypted_data)
            
            result = EncryptionResult(
                success=True,
                encrypted_data=encrypted_data,
                key_id=key_id,
                algorithm="Fernet"
            )
            
            logger.debug("Criptografia de configuração concluída")
            return result
            
        except Exception as e:
            logger.error(f"Erro na criptografia: {e}")
            return EncryptionResult(
                success=False,
                error_message=str(e)
            )
    
    def decrypt_configuration(self, key_id: str = "default") -> EncryptionResult:
        """
        Descriptografa dados de configuração
        
        Args:
            key_id: ID da chave de descriptografia
            
        Returns:
            EncryptionResult: Resultado da descriptografia
        """
        logger.debug(f"Descriptografando configuração com chave: {key_id}")
        
        if not HAS_CRYPTOGRAPHY:
            return EncryptionResult(
                success=False,
                error_message="Biblioteca cryptography não disponível"
            )
        
        try:
            # Obtém chave
            if key_id not in self.encryption_keys:
                return EncryptionResult(
                    success=False,
                    error_message=f"Chave {key_id} não encontrada"
                )
            
            encryption_key = self.encryption_keys[key_id]
            
            # Lê dados criptografados
            encrypted_file = self.config_dir / f"{key_id}_encrypted.dat"
            if not encrypted_file.exists():
                return EncryptionResult(
                    success=False,
                    error_message=f"Arquivo criptografado não encontrado: {encrypted_file}"
                )
            
            with open(encrypted_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Descriptografa dados
            fernet = Fernet(encryption_key)
            decrypted_data = fernet.decrypt(encrypted_data).decode('utf-8')
            
            result = EncryptionResult(
                success=True,
                decrypted_data=decrypted_data,
                key_id=key_id,
                algorithm="Fernet"
            )
            
            logger.debug("Descriptografia de configuração concluída")
            return result
            
        except Exception as e:
            logger.error(f"Erro na descriptografia: {e}")
            return EncryptionResult(
                success=False,
                error_message=str(e)
            )
    
    def protect_backup_with_permissions(self, backup_path: str, 
                                      restricted_access: bool = True) -> bool:
        """
        Protege backup com permissões adequadas (Requisito 11.2)
        
        Args:
            backup_path: Caminho do backup
            restricted_access: Se deve aplicar acesso restrito
            
        Returns:
            bool: True se proteção foi aplicada com sucesso
        """
        logger.debug(f"Protegendo backup: {backup_path}")
        
        try:
            backup_path_obj = Path(backup_path)
            
            if not backup_path_obj.exists():
                logger.error(f"Backup não encontrado: {backup_path}")
                return False
            
            if os.name == 'nt':  # Windows
                # Aplica permissões no Windows
                import stat
                
                if restricted_access:
                    # Remove permissões de escrita para outros usuários
                    current_mode = backup_path_obj.stat().st_mode
                    new_mode = current_mode & ~(stat.S_IWGRP | stat.S_IWOTH)
                    backup_path_obj.chmod(new_mode)
                    
                    # Tenta aplicar ACL mais restritiva (requer pywin32)
                    try:
                        import win32security
                        import win32api
                        import ntsecuritycon
                        
                        # Obtém SID do usuário atual
                        user_sid = win32security.GetTokenInformation(
                            win32security.GetCurrentProcessToken(),
                            win32security.TokenUser
                        )[0]
                        
                        # Cria DACL restritiva
                        dacl = win32security.ACL()
                        dacl.AddAccessAllowedAce(
                            win32security.ACL_REVISION,
                            ntsecuritycon.FILE_ALL_ACCESS,
                            user_sid
                        )
                        
                        # Aplica DACL
                        sd = win32security.SECURITY_DESCRIPTOR()
                        sd.SetSecurityDescriptorDacl(1, dacl, 0)
                        win32security.SetFileSecurity(
                            str(backup_path_obj),
                            win32security.DACL_SECURITY_INFORMATION,
                            sd
                        )
                        
                        logger.debug("ACL restritiva aplicada no Windows")
                        
                    except ImportError:
                        logger.debug("pywin32 não disponível - usando chmod básico")
                    except Exception as e:
                        logger.warning(f"Erro ao aplicar ACL: {e}")
                
            else:  # Unix/Linux
                if restricted_access:
                    # Permissões apenas para o proprietário (600)
                    backup_path_obj.chmod(0o600)
                else:
                    # Permissões de leitura para grupo (640)
                    backup_path_obj.chmod(0o640)
            
            # Cria arquivo de metadados de proteção
            metadata_file = backup_path_obj.with_suffix(backup_path_obj.suffix + '.meta')
            metadata = {
                "protected_at": datetime.now().isoformat(),
                "restricted_access": restricted_access,
                "original_permissions": oct(backup_path_obj.stat().st_mode)[-3:],
                "integrity_hash": self._calculate_file_hash(backup_path_obj, "sha256")
            }
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            # Protege também o arquivo de metadados
            if restricted_access:
                metadata_file.chmod(0o600 if os.name != 'nt' else backup_path_obj.stat().st_mode)
            
            logger.info(f"Backup protegido com sucesso: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao proteger backup: {e}")
            return False
    
    def verify_backup_integrity(self, backup_path: str) -> IntegrityResult:
        """
        Verifica integridade de um backup protegido
        
        Args:
            backup_path: Caminho do backup
            
        Returns:
            IntegrityResult: Resultado da verificação
        """
        logger.debug(f"Verificando integridade do backup: {backup_path}")
        
        backup_path_obj = Path(backup_path)
        metadata_file = backup_path_obj.with_suffix(backup_path_obj.suffix + '.meta')
        
        result = IntegrityResult(
            file_path=backup_path,
            status=IntegrityStatus.UNKNOWN
        )
        
        try:
            # Verifica se backup existe
            if not backup_path_obj.exists():
                result.status = IntegrityStatus.MISSING
                result.details["error"] = "Arquivo de backup não encontrado"
                return result
            
            # Verifica se metadados existem
            if not metadata_file.exists():
                result.status = IntegrityStatus.UNKNOWN
                result.details["warning"] = "Metadados de proteção não encontrados"
                # Continua com verificação básica
                return self.validate_file_integrity(backup_path, "", "sha256")
            
            # Carrega metadados
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            expected_hash = metadata.get("integrity_hash")
            if not expected_hash:
                result.status = IntegrityStatus.UNKNOWN
                result.details["error"] = "Hash de integridade não encontrado nos metadados"
                return result
            
            # Valida integridade
            return self.validate_file_integrity(backup_path, expected_hash, "sha256")
            
        except Exception as e:
            logger.error(f"Erro na verificação de integridade do backup: {e}")
            result.status = IntegrityStatus.CORRUPTED
            result.details["error"] = str(e)
            return result
    
    def generate_integrity_report(self, paths: List[str]) -> Dict[str, Any]:
        """
        Gera relatório de integridade para múltiplos arquivos
        
        Args:
            paths: Lista de caminhos para verificar
            
        Returns:
            Dict: Relatório de integridade detalhado
        """
        logger.info(f"Gerando relatório de integridade para {len(paths)} arquivos")
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_files": len(paths),
            "results": [],
            "summary": {
                "valid": 0,
                "invalid": 0,
                "missing": 0,
                "corrupted": 0,
                "unknown": 0
            }
        }
        
        for path in paths:
            try:
                # Tenta encontrar hash esperado (implementação básica)
                expected_hash = self._find_expected_hash(path)
                
                if expected_hash:
                    result = self.validate_file_integrity(path, expected_hash)
                else:
                    # Gera hash atual como referência
                    current_hash = self._calculate_file_hash(Path(path), "sha256")
                    result = IntegrityResult(
                        file_path=path,
                        status=IntegrityStatus.UNKNOWN,
                        calculated_hash=current_hash,
                        algorithm="sha256"
                    )
                    result.details["note"] = "Hash esperado não encontrado - usando hash atual como referência"
                
                # Adiciona ao relatório
                report["results"].append({
                    "file_path": result.file_path,
                    "status": result.status.value,
                    "expected_hash": result.expected_hash,
                    "calculated_hash": result.calculated_hash,
                    "algorithm": result.algorithm,
                    "file_size": result.file_size,
                    "last_modified": result.last_modified.isoformat() if result.last_modified else None,
                    "details": result.details
                })
                
                # Atualiza sumário
                report["summary"][result.status.value] += 1
                
            except Exception as e:
                logger.error(f"Erro ao processar {path}: {e}")
                report["results"].append({
                    "file_path": path,
                    "status": "error",
                    "error": str(e)
                })
                report["summary"]["unknown"] += 1
        
        # Calcula estatísticas
        total_valid = report["summary"]["valid"]
        total_files = report["total_files"]
        
        report["statistics"] = {
            "integrity_rate": (total_valid / total_files * 100) if total_files > 0 else 0,
            "files_with_issues": total_files - total_valid,
            "critical_issues": report["summary"]["corrupted"] + report["summary"]["invalid"]
        }
        
        logger.info(f"Relatório gerado: {total_valid}/{total_files} arquivos íntegros")
        return report    

    # Métodos auxiliares privados
    def _calculate_file_hash(self, file_path: Path, algorithm: str = "sha256") -> str:
        """Calcula hash de um arquivo"""
        hash_algorithms = {
            'md5': hashlib.md5,
            'sha1': hashlib.sha1,
            'sha256': hashlib.sha256,
            'sha512': hashlib.sha512
        }
        
        if algorithm.lower() not in hash_algorithms:
            raise ValueError(f"Algoritmo {algorithm} não suportado")
        
        hash_func = hash_algorithms[algorithm.lower()]()
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_func.update(chunk)
            
            return hash_func.hexdigest()
            
        except Exception as e:
            logger.error(f"Erro ao calcular hash de {file_path}: {e}")
            raise
    
    def _initialize_encryption(self):
        """Inicializa sistema de criptografia"""
        if not HAS_CRYPTOGRAPHY:
            return
        
        try:
            # Carrega chaves existentes
            self._load_encryption_keys()
            
            # Cria chave padrão se não existir
            if "default" not in self.encryption_keys:
                self._generate_encryption_key("default")
            
            logger.debug("Sistema de criptografia inicializado")
            
        except Exception as e:
            logger.error(f"Erro na inicialização da criptografia: {e}")
    
    def _get_or_create_key(self, key_id: str) -> bytes:
        """Obtém chave existente ou cria nova"""
        if key_id in self.encryption_keys:
            return self.encryption_keys[key_id]
        
        return self._generate_encryption_key(key_id)
    
    def _generate_encryption_key(self, key_id: str) -> bytes:
        """Gera nova chave de criptografia"""
        if not HAS_CRYPTOGRAPHY:
            raise RuntimeError("Cryptography library not available")
        
        # Gera chave Fernet
        key = Fernet.generate_key()
        self.encryption_keys[key_id] = key
        
        # Salva chave em arquivo protegido
        key_file = self.keys_dir / f"{key_id}.key"
        with open(key_file, 'wb') as f:
            f.write(key)
        
        # Protege arquivo de chave
        if os.name != 'nt':
            key_file.chmod(0o600)
        
        logger.info(f"Nova chave de criptografia gerada: {key_id}")
        return key
    
    def _load_encryption_keys(self):
        """Carrega chaves de criptografia existentes"""
        try:
            for key_file in self.keys_dir.glob("*.key"):
                key_id = key_file.stem
                
                with open(key_file, 'rb') as f:
                    key = f.read()
                
                self.encryption_keys[key_id] = key
                logger.debug(f"Chave carregada: {key_id}")
                
        except Exception as e:
            logger.warning(f"Erro ao carregar chaves: {e}")
    
    def _load_sensitive_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Carrega padrões de dados sensíveis para sanitização"""
        return {
            "email": {
                "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                "replacement": "[EMAIL]",
                "preserve_length": True
            },
            "phone": {
                "pattern": r'(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
                "replacement": "[PHONE]",
                "preserve_length": True
            },
            "ssn": {
                "pattern": r'\b\d{3}-\d{2}-\d{4}\b',
                "replacement": "[SSN]",
                "preserve_length": True
            },
            "credit_card": {
                "pattern": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
                "replacement": "[CARD]",
                "preserve_length": True
            },
            "ip_address": {
                "pattern": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
                "replacement": "[IP]",
                "preserve_length": False
            },
            "password": {
                "pattern": r'(?i)(password|pwd|pass|secret|key)\s*[:=]\s*[^\s\n\r]+',
                "replacement": r'\1: [REDACTED]',
                "preserve_length": False
            },
            "token": {
                "pattern": r'(?i)(token|auth|bearer)\s*[:=]\s*[A-Za-z0-9+/=]{20,}',
                "replacement": r'\1: [TOKEN]',
                "preserve_length": False
            },
            "api_key": {
                "pattern": r'(?i)(api[_-]?key|apikey)\s*[:=]\s*[A-Za-z0-9]{20,}',
                "replacement": r'\1: [API_KEY]',
                "preserve_length": False
            },
            "hash": {
                "pattern": r'\b[a-fA-F0-9]{32,128}\b',
                "replacement": "[HASH]",
                "preserve_length": False
            },
            "path": {
                "pattern": r'[A-Za-z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*',
                "replacement": "[PATH]",
                "preserve_length": False
            },
            "url": {
                "pattern": r'https?://[^\s<>"{}|\\^`[\]]+',
                "replacement": "[URL]",
                "preserve_length": False
            }
        }
    
    def _is_json_like(self, data: str) -> bool:
        """Verifica se dados parecem ser JSON"""
        stripped = data.strip()
        return (stripped.startswith('{') and stripped.endswith('}')) or \
               (stripped.startswith('[') and stripped.endswith(']'))
    
    def _sanitize_json_structure(self, json_data: str) -> str:
        """Sanitiza estrutura JSON preservando formato"""
        try:
            parsed = json.loads(json_data)
            sanitized = self._sanitize_json_object(parsed)
            return json.dumps(sanitized, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            # Se não for JSON válido, aplica sanitização de texto
            return self.sanitize_log_data(json_data, preserve_structure=False)
    
    def _sanitize_json_object(self, obj: Any) -> Any:
        """Sanitiza objeto JSON recursivamente"""
        if isinstance(obj, dict):
            sanitized = {}
            for key, value in obj.items():
                # Sanitiza chave
                sanitized_key = self._sanitize_json_key(key)
                # Sanitiza valor
                sanitized_value = self._sanitize_json_object(value)
                sanitized[sanitized_key] = sanitized_value
            return sanitized
        elif isinstance(obj, list):
            return [self._sanitize_json_object(item) for item in obj]
        elif isinstance(obj, str):
            return self._sanitize_json_string(obj)
        else:
            return obj
    
    def _sanitize_json_key(self, key: str) -> str:
        """Sanitiza chave JSON"""
        sensitive_keys = [
            'password', 'pwd', 'pass', 'secret', 'key', 'token', 'auth',
            'api_key', 'apikey', 'private_key', 'access_token', 'refresh_token'
        ]
        
        if key.lower() in sensitive_keys:
            return f"{key}_[REDACTED]"
        
        return key
    
    def _sanitize_json_string(self, value: str) -> str:
        """Sanitiza string dentro de JSON"""
        # Aplica padrões de sanitização mais conservadores para JSON
        for pattern_name, pattern_info in self.sensitive_patterns.items():
            if pattern_name in ['password', 'token', 'api_key', 'hash']:
                regex_pattern = pattern_info["pattern"]
                replacement = pattern_info["replacement"]
                value = re.sub(regex_pattern, replacement, value, flags=re.IGNORECASE)
        
        return value
    
    def _find_expected_hash(self, file_path: str) -> Optional[str]:
        """Tenta encontrar hash esperado para um arquivo"""
        # Implementação básica - procura por arquivo .hash adjacente
        hash_file = Path(file_path + ".hash")
        
        if hash_file.exists():
            try:
                with open(hash_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    # Assume formato "hash algorithm" ou apenas "hash"
                    parts = content.split()
                    return parts[0] if parts else None
            except Exception as e:
                logger.debug(f"Erro ao ler arquivo de hash {hash_file}: {e}")
        
        # Procura em arquivo de manifesto
        manifest_file = Path(file_path).parent / "manifest.json"
        if manifest_file.exists():
            try:
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    
                    filename = Path(file_path).name
                    if filename in manifest:
                        return manifest[filename].get('hash')
            except Exception as e:
                logger.debug(f"Erro ao ler manifesto {manifest_file}: {e}")
        
        return None
    
    def create_integrity_manifest(self, directory: str, output_file: Optional[str] = None) -> str:
        """
        Cria manifesto de integridade para um diretório
        
        Args:
            directory: Diretório para criar manifesto
            output_file: Arquivo de saída (opcional)
            
        Returns:
            str: Caminho do arquivo de manifesto criado
        """
        logger.info(f"Criando manifesto de integridade para: {directory}")
        
        directory_path = Path(directory)
        if not directory_path.exists():
            raise ValueError(f"Diretório não encontrado: {directory}")
        
        manifest = {
            "created_at": datetime.now().isoformat(),
            "directory": str(directory_path.absolute()),
            "algorithm": "sha256",
            "files": {}
        }
        
        # Processa todos os arquivos no diretório
        for file_path in directory_path.rglob("*"):
            if file_path.is_file():
                try:
                    relative_path = file_path.relative_to(directory_path)
                    file_hash = self._calculate_file_hash(file_path, "sha256")
                    file_stat = file_path.stat()
                    
                    manifest["files"][str(relative_path)] = {
                        "hash": file_hash,
                        "size": file_stat.st_size,
                        "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                    }
                    
                except Exception as e:
                    logger.warning(f"Erro ao processar {file_path}: {e}")
        
        # Salva manifesto
        if not output_file:
            output_file = directory_path / "integrity_manifest.json"
        else:
            output_file = Path(output_file)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Manifesto criado: {output_file} ({len(manifest['files'])} arquivos)")
        return str(output_file)
    
    def verify_integrity_manifest(self, manifest_file: str) -> Dict[str, Any]:
        """
        Verifica integridade usando manifesto
        
        Args:
            manifest_file: Arquivo de manifesto
            
        Returns:
            Dict: Resultado da verificação
        """
        logger.info(f"Verificando integridade usando manifesto: {manifest_file}")
        
        manifest_path = Path(manifest_file)
        if not manifest_path.exists():
            raise ValueError(f"Manifesto não encontrado: {manifest_file}")
        
        # Carrega manifesto
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        base_directory = Path(manifest["directory"])
        algorithm = manifest.get("algorithm", "sha256")
        
        results = {
            "manifest_file": str(manifest_path),
            "base_directory": str(base_directory),
            "verified_at": datetime.now().isoformat(),
            "total_files": len(manifest["files"]),
            "results": [],
            "summary": {
                "valid": 0,
                "invalid": 0,
                "missing": 0,
                "modified": 0,
                "new_files": 0
            }
        }
        
        # Verifica arquivos do manifesto
        for relative_path, file_info in manifest["files"].items():
            file_path = base_directory / relative_path
            expected_hash = file_info["hash"]
            
            result = self.validate_file_integrity(str(file_path), expected_hash, algorithm)
            
            # Verifica se arquivo foi modificado
            if file_path.exists():
                current_stat = file_path.stat()
                expected_modified = datetime.fromisoformat(file_info["modified"])
                current_modified = datetime.fromtimestamp(current_stat.st_mtime)
                
                if abs((current_modified - expected_modified).total_seconds()) > 1:
                    result.details["time_modified"] = True
                    if result.status == IntegrityStatus.VALID:
                        results["summary"]["modified"] += 1
            
            results["results"].append({
                "file_path": str(relative_path),
                "status": result.status.value,
                "expected_hash": result.expected_hash,
                "calculated_hash": result.calculated_hash,
                "details": result.details
            })
            
            results["summary"][result.status.value] += 1
        
        # Verifica arquivos novos (não no manifesto)
        current_files = set()
        for file_path in base_directory.rglob("*"):
            if file_path.is_file() and file_path != manifest_path:
                relative_path = file_path.relative_to(base_directory)
                current_files.add(str(relative_path))
        
        manifest_files = set(manifest["files"].keys())
        new_files = current_files - manifest_files
        
        for new_file in new_files:
            results["results"].append({
                "file_path": new_file,
                "status": "new",
                "details": {"note": "Arquivo não estava no manifesto original"}
            })
            results["summary"]["new_files"] += 1
        
        # Calcula estatísticas finais
        total_expected = results["total_files"]
        valid_files = results["summary"]["valid"]
        
        results["statistics"] = {
            "integrity_rate": (valid_files / total_expected * 100) if total_expected > 0 else 0,
            "files_with_issues": total_expected - valid_files,
            "new_files_found": len(new_files)
        }
        
        logger.info(f"Verificação concluída: {valid_files}/{total_expected} arquivos íntegros")
        return results
    
    def get_integrity_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do validador de integridade
        
        Returns:
            Dict: Estatísticas detalhadas
        """
        stats = {
            "encryption_keys_loaded": len(self.encryption_keys),
            "cryptography_available": HAS_CRYPTOGRAPHY,
            "sensitive_patterns_count": len(self.sensitive_patterns),
            "base_path": str(self.base_path),
            "directories": {
                "config": str(self.config_dir),
                "keys": str(self.keys_dir),
                "logs": str(self.logs_dir)
            }
        }
        
        # Estatísticas de arquivos de chave
        if self.keys_dir.exists():
            key_files = list(self.keys_dir.glob("*.key"))
            stats["key_files_on_disk"] = len(key_files)
        
        # Estatísticas de configurações criptografadas
        if self.config_dir.exists():
            encrypted_files = list(self.config_dir.glob("*_encrypted.dat"))
            stats["encrypted_config_files"] = len(encrypted_files)
        
        return stats


# Instância global do validador de integridade
integrity_validator = IntegrityValidator()