# -*- coding: utf-8 -*-
"""
Sistema de Verificação Robusta para Environment Dev Script
Substitui verificações frágeis por métodos mais confiáveis
"""

import os
import sys
import logging
import subprocess
import winreg
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class VerificationMethod(Enum):
    """Métodos de verificação disponíveis"""
    REGISTRY = "registry"
    FILE_EXISTS = "file_exists"
    COMMAND = "command"
    VERSION_CHECK = "version_check"
    SERVICE = "service"
    PROCESS = "process"

@dataclass
class VerificationResult:
    """Resultado de uma verificação"""
    success: bool
    method: VerificationMethod
    details: Dict[str, Any]
    message: str
    version: Optional[str] = None
    path: Optional[str] = None

class RobustVerifier:
    """
    Sistema robusto de verificação de instalações
    """
    
    def __init__(self):
        self.verification_cache = {}
        self.registry_roots = {
            'HKLM': winreg.HKEY_LOCAL_MACHINE,
            'HKCU': winreg.HKEY_CURRENT_USER,
            'HKCR': winreg.HKEY_CLASSES_ROOT,
            'HKU': winreg.HKEY_USERS,
            'HKCC': winreg.HKEY_CURRENT_CONFIG
        }
    
    def verify_registry_key(self, root: str, key_path: str, value_name: str = None) -> VerificationResult:
        """
        Verifica existência de chave/valor no registro do Windows
        
        Args:
            root: Raiz do registro (HKLM, HKCU, etc.)
            key_path: Caminho da chave
            value_name: Nome do valor (opcional)
            
        Returns:
            Resultado da verificação
        """
        try:
            if root not in self.registry_roots:
                return VerificationResult(
                    success=False,
                    method=VerificationMethod.REGISTRY,
                    details={'error': f'Raiz de registro inválida: {root}'},
                    message=f"Raiz de registro {root} não suportada"
                )
            
            registry_key = winreg.OpenKey(self.registry_roots[root], key_path)
            
            if value_name:
                # Verifica valor específico
                try:
                    value, reg_type = winreg.QueryValueEx(registry_key, value_name)
                    winreg.CloseKey(registry_key)
                    
                    return VerificationResult(
                        success=True,
                        method=VerificationMethod.REGISTRY,
                        details={
                            'root': root,
                            'key_path': key_path,
                            'value_name': value_name,
                            'value': str(value),
                            'type': reg_type
                        },
                        message=f"Valor encontrado no registro: {value}",
                        path=str(value) if isinstance(value, str) else None
                    )
                except FileNotFoundError:
                    winreg.CloseKey(registry_key)
                    return VerificationResult(
                        success=False,
                        method=VerificationMethod.REGISTRY,
                        details={'error': f'Valor {value_name} não encontrado'},
                        message=f"Valor {value_name} não existe na chave"
                    )
            else:
                # Apenas verifica se a chave existe
                winreg.CloseKey(registry_key)
                return VerificationResult(
                    success=True,
                    method=VerificationMethod.REGISTRY,
                    details={'root': root, 'key_path': key_path},
                    message="Chave encontrada no registro"
                )
                
        except FileNotFoundError:
            return VerificationResult(
                success=False,
                method=VerificationMethod.REGISTRY,
                details={'error': 'Chave não encontrada'},
                message=f"Chave {key_path} não existe no registro"
            )
        except Exception as e:
            logger.error(f"Erro ao verificar registro: {e}")
            return VerificationResult(
                success=False,
                method=VerificationMethod.REGISTRY,
                details={'error': str(e)},
                message=f"Erro na verificação do registro: {e}"
            )
    
    def verify_file_exists(self, file_paths: List[str], require_all: bool = False) -> VerificationResult:
        """
        Verifica existência de arquivos
        
        Args:
            file_paths: Lista de caminhos para verificar
            require_all: Se True, todos os arquivos devem existir
            
        Returns:
            Resultado da verificação
        """
        found_files = []
        missing_files = []
        
        for file_path in file_paths:
            expanded_path = os.path.expandvars(file_path)
            if os.path.exists(expanded_path):
                found_files.append(expanded_path)
            else:
                missing_files.append(file_path)
        
        if require_all:
            success = len(missing_files) == 0
            message = "Todos os arquivos encontrados" if success else f"Arquivos ausentes: {missing_files}"
        else:
            success = len(found_files) > 0
            message = f"Encontrados {len(found_files)} de {len(file_paths)} arquivos"
        
        return VerificationResult(
            success=success,
            method=VerificationMethod.FILE_EXISTS,
            details={
                'found_files': found_files,
                'missing_files': missing_files,
                'require_all': require_all
            },
            message=message,
            path=found_files[0] if found_files else None
        )
    
    def verify_command_version(self, command: str, version_args: List[str] = None, 
                             expected_pattern: str = None) -> VerificationResult:
        """
        Verifica comando e opcionalmente sua versão
        
        Args:
            command: Comando para verificar
            version_args: Argumentos para obter versão (ex: ['--version'])
            expected_pattern: Padrão regex esperado na saída
            
        Returns:
            Resultado da verificação
        """
        try:
            # Primeiro verifica se o comando existe
            result = subprocess.run(
                [command] + (version_args or ['--version']),
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout.strip() or result.stderr.strip()
                
                # Extrai versão se possível
                version = self._extract_version(output)
                
                success = True
                message = f"Comando {command} disponível"
                
                if expected_pattern:
                    import re
                    if re.search(expected_pattern, output):
                        message += f" (padrão encontrado)"
                    else:
                        success = False
                        message = f"Comando {command} encontrado mas padrão não corresponde"
                
                return VerificationResult(
                    success=success,
                    method=VerificationMethod.COMMAND,
                    details={
                        'command': command,
                        'output': output,
                        'return_code': result.returncode
                    },
                    message=message,
                    version=version
                )
            else:
                return VerificationResult(
                    success=False,
                    method=VerificationMethod.COMMAND,
                    details={
                        'command': command,
                        'error': result.stderr,
                        'return_code': result.returncode
                    },
                    message=f"Comando {command} falhou (código {result.returncode})"
                )
                
        except FileNotFoundError:
            return VerificationResult(
                success=False,
                method=VerificationMethod.COMMAND,
                details={'error': 'Comando não encontrado'},
                message=f"Comando {command} não está disponível"
            )
        except subprocess.TimeoutExpired:
            return VerificationResult(
                success=False,
                method=VerificationMethod.COMMAND,
                details={'error': 'Timeout'},
                message=f"Comando {command} demorou muito para responder"
            )
        except Exception as e:
            return VerificationResult(
                success=False,
                method=VerificationMethod.COMMAND,
                details={'error': str(e)},
                message=f"Erro ao verificar comando {command}: {e}"
            )
    
    def verify_service_status(self, service_name: str) -> VerificationResult:
        """
        Verifica status de um serviço do Windows
        
        Args:
            service_name: Nome do serviço
            
        Returns:
            Resultado da verificação
        """
        try:
            result = subprocess.run(
                ['sc', 'query', service_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout
                # Extrai estado do serviço
                state = "UNKNOWN"
                for line in output.split('\n'):
                    if 'STATE' in line:
                        state = line.split()[-1] if line.split() else "UNKNOWN"
                        break
                
                is_running = 'RUNNING' in state
                
                return VerificationResult(
                    success=True,
                    method=VerificationMethod.SERVICE,
                    details={
                        'service_name': service_name,
                        'state': state,
                        'is_running': is_running,
                        'output': output
                    },
                    message=f"Serviço {service_name} está {state}"
                )
            else:
                return VerificationResult(
                    success=False,
                    method=VerificationMethod.SERVICE,
                    details={
                        'service_name': service_name,
                        'error': result.stderr,
                        'return_code': result.returncode
                    },
                    message=f"Serviço {service_name} não encontrado"
                )
                
        except Exception as e:
            return VerificationResult(
                success=False,
                method=VerificationMethod.SERVICE,
                details={'error': str(e)},
                message=f"Erro ao verificar serviço {service_name}: {e}"
            )
    
    def verify_component(self, component_data: Dict) -> List[VerificationResult]:
        """
        Verifica um componente usando múltiplos métodos
        
        Args:
            component_data: Dados do componente com configurações de verificação
            
        Returns:
            Lista de resultados de verificação
        """
        results = []
        verification_config = component_data.get('verification', {})
        
        # Verificação por registro
        if 'registry' in verification_config:
            reg_config = verification_config['registry']
            result = self.verify_registry_key(
                reg_config.get('root', 'HKLM'),
                reg_config['key'],
                reg_config.get('value')
            )
            results.append(result)
        
        # Verificação por arquivos
        if 'files' in verification_config:
            files_config = verification_config['files']
            result = self.verify_file_exists(
                files_config.get('paths', []),
                files_config.get('require_all', False)
            )
            results.append(result)
        
        # Verificação por comando
        if 'command' in verification_config:
            cmd_config = verification_config['command']
            result = self.verify_command_version(
                cmd_config['name'],
                cmd_config.get('version_args'),
                cmd_config.get('expected_pattern')
            )
            results.append(result)
        
        # Verificação por serviço
        if 'service' in verification_config:
            service_config = verification_config['service']
            result = self.verify_service_status(service_config['name'])
            results.append(result)
        
        return results
    
    def _extract_version(self, output: str) -> Optional[str]:
        """
        Extrai versão de uma saída de comando
        
        Args:
            output: Saída do comando
            
        Returns:
            Versão extraída ou None
        """
        import re
        
        # Padrões comuns de versão
        patterns = [
            r'version\s+([0-9]+(?:\.[0-9]+)*)',
            r'v([0-9]+(?:\.[0-9]+)*)',
            r'([0-9]+(?:\.[0-9]+)+)',
            r'Version:\s*([0-9]+(?:\.[0-9]+)*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def get_comprehensive_status(self, component_data: Dict) -> Dict[str, Any]:
        """
        Obtém status abrangente de um componente
        
        Args:
            component_data: Dados do componente
            
        Returns:
            Dicionário com status detalhado
        """
        results = self.verify_component(component_data)
        
        # Analisa resultados
        successful_verifications = [r for r in results if r.success]
        failed_verifications = [r for r in results if not r.success]
        
        # Determina status geral
        if not results:
            overall_status = "no_verification"
        elif len(successful_verifications) == len(results):
            overall_status = "fully_verified"
        elif successful_verifications:
            overall_status = "partially_verified"
        else:
            overall_status = "not_verified"
        
        # Coleta informações de versão e caminho
        versions = [r.version for r in successful_verifications if r.version]
        paths = [r.path for r in successful_verifications if r.path]
        
        return {
            'overall_status': overall_status,
            'verification_count': len(results),
            'successful_count': len(successful_verifications),
            'failed_count': len(failed_verifications),
            'versions': versions,
            'paths': paths,
            'results': [{
                'method': r.method.value,
                'success': r.success,
                'message': r.message,
                'version': r.version,
                'path': r.path
            } for r in results]
        }

# Instância global
robust_verifier = RobustVerifier()