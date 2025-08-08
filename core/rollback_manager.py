#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo RollbackManager do Environment Dev

Este módulo contém a classe RollbackManager, responsável por gerenciar
operações de rollback transacionais durante a instalação de componentes.
"""

import logging
import os
import shutil
import subprocess
import json
import tempfile
from typing import List, Dict, Any, Optional

# Importa o sistema de gestão de erros (se necessário para logar erros de rollback)
from utils.error_handler import file_error, handle_exception, ErrorSeverity, ErrorCategory

# Importa o sistema de log
from utils.log_manager import setup_logging, ROLLBACK

# Logger principal
logger = logging.getLogger(__name__)

class RollbackManager:
    """
    Gerencia o rollback de ações realizadas durante a instalação de um componente.

    Mantém uma pilha de operações de 'undo' que podem ser executadas
    em ordem reversa caso a instalação falhe.
    """

    def __init__(self):
        """Inicializa o RollbackManager para uma nova transação."""
        self._undo_stack: List[Dict[str, Any]] = []
        self._transaction_active: bool = False
        self._current_component: Optional[str] = None
        logger.debug("RollbackManager inicializado.")

    def start_transaction(self, component_name: str):
        """
        Inicia uma nova transação de rollback para um componente específico.

        Limpa qualquer estado anterior e marca a transação como ativa.

        Args:
            component_name: O nome do componente sendo instalado.
        """
        if self._transaction_active:
            logger.warning(f"Tentando iniciar nova transação para '{component_name}' enquanto uma transação para '{self._current_component}' já está ativa. Limpando a anterior.")
            self.clear_transaction() # Garante que não haja sobreposição

        self._undo_stack = []
        self._transaction_active = True
        self._current_component = component_name
        logger.info(f"Transação de rollback iniciada para o componente: {component_name}")

    def register_action(self, undo_operation: Dict[str, Any]):
        """
        Registra uma operação de 'undo' na pilha.

        Esta função deve ser chamada *antes* da execução da ação
        correspondente que modifica o sistema.

        Args:
            undo_operation: Um dicionário descrevendo a ação de undo.
                            Ex: {'component': 'CompA', 'step': 'Extracting',
                                 'undo_action': 'delete_path',
                                 'parameters': {'path': '/path/to/extract'}}
        """
        if not self._transaction_active:
            logger.warning(f"Tentativa de registrar ação de undo sem transação ativa para o componente '{undo_operation.get('component', 'Desconhecido')}'. Ignorando.")
            return

        if not undo_operation or 'undo_action' not in undo_operation or 'parameters' not in undo_operation:
             logger.error(f"Tentativa de registrar operação de undo inválida: {undo_operation}")
             return

        # Adiciona informações contextuais se não existirem
        undo_operation.setdefault('component', self._current_component)
        undo_operation.setdefault('step', 'Ação Desconhecida') # Idealmente, o chamador fornece isso

        self._undo_stack.append(undo_operation)
        logger.debug(f"Ação de undo registrada para '{self._current_component}': {undo_operation['undo_action']} - {undo_operation.get('step', '')}")

    def add_action(self, undo_action: str, parameters: Dict[str, Any], step: str = None):
        """
        Alias para register_action com interface simplificada.
        
        Args:
            undo_action: Tipo da ação de undo (ex: 'delete_path', 'run_command')
            parameters: Parâmetros para a ação de undo
            step: Descrição da etapa (opcional)
        """
        undo_operation = {
            'undo_action': undo_action,
            'parameters': parameters
        }
        if step:
            undo_operation['step'] = step
            
        self.register_action(undo_operation)

    def commit_transaction(self):
        """
        Confirma a transação atual, indicando que a instalação foi bem-sucedida.

        Limpa a pilha de undo, pois o rollback não é mais necessário.
        """
        if not self._transaction_active:
            logger.debug("Tentativa de commit sem transação ativa. Ignorando.")
            return

        logger.rollback(f"Transação de rollback confirmada (commit) para o componente: {self._current_component}")
        self.clear_transaction()

    def trigger_rollback(self):
        """
        Inicia o processo de rollback, executando as ações de undo registradas
        em ordem reversa.
        """
        if not self._transaction_active:
            logger.error("Tentativa de acionar rollback sem transação ativa.")
            return

        logger.rollback("Acionando rollback para o componente: %s", self._current_component)
        logger.rollback(f"Total de {len(self._undo_stack)} ações de undo a serem executadas.")

        # Envia status de rollback para a GUI
        try:
            from env_dev.core.installer_wrapper import send_status_update
            send_status_update({
                'type': 'rollback',
                'component': self._current_component,
                'status': 'IN_PROGRESS',
                'message': f'Iniciando rollback com {len(self._undo_stack)} ações'
            })
        except ImportError:
            logger.debug("Não foi possível importar send_status_update para notificar rollback")

        # Executa as ações em ordem reversa (LIFO)
        rollback_success = True
        total_actions = len(self._undo_stack)
        completed_actions = 0

        while self._undo_stack:
            undo_op = self._undo_stack.pop()
            undo_action = undo_op.get('undo_action')
            parameters = undo_op.get('parameters', {})
            step = undo_op.get('step', 'Ação Desconhecida')
            component = undo_op.get('component', self._current_component)

            logger.rollback(f"Executando undo para '{component}' (Etapa: {step}): {undo_action} com params {parameters}")

            # Atualiza progresso do rollback
            try:
                from env_dev.core.installer_wrapper import send_status_update
                completed_actions += 1
                progress = int((completed_actions / total_actions) * 100) if total_actions > 0 else 100
                send_status_update({
                    'type': 'rollback',
                    'component': component,
                    'status': 'IN_PROGRESS',
                    'progress': progress,
                    'message': f'Revertendo: {step}'
                })
            except ImportError:
                pass

            try:
                if undo_action == 'delete_path':
                    self._undo_delete_path(parameters.get('path'))
                elif undo_action == 'run_command':
                    self._undo_run_command(parameters.get('command'))
                elif undo_action == 'run_script':
                    self._undo_run_script(
                        parameters.get('script_path'),
                        parameters.get('args'),
                        parameters.get('cwd')
                    )
                elif undo_action == 'restore_env':
                    self._undo_restore_env(
                        parameters.get('variable_name'),
                        parameters.get('original_value'),
                        parameters.get('scope', 'user')
                    )
                elif undo_action == 'unset_env':
                    self._undo_unset_env(
                        parameters.get('variable_name'),
                        parameters.get('scope', 'user')
                    )
                elif undo_action == 'remove_path':
                    self._undo_remove_path(
                        parameters.get('path_to_remove'),
                        parameters.get('scope', 'user')
                    )
                elif undo_action == 'restore_efi':
                    self._undo_restore_efi(
                        parameters.get('backup_path'),
                        parameters.get('efi_drive_letter')
                    )
                elif undo_action == 'modify_json':
                    self._undo_modify_json(
                        parameters.get('file_path'),
                        parameters.get('operation', 'remove_key'),
                        parameters.get('key'),
                        parameters.get('value')
                    )
                elif undo_action == 'chocolatey_uninstall':
                    self._undo_chocolatey_uninstall(
                        parameters.get('package_name'),
                        parameters.get('component_name')
                    )
                elif undo_action == 'remove_directory':
                    self._undo_remove_directory(
                        parameters.get('path'),
                        parameters.get('component_name')
                    )
                else:
                    logger.error(f"Tipo de ação de undo desconhecido: {undo_action}. Ignorando.")

            except Exception as e:
                # Registrar erro na execução do undo, mas continuar com os outros (melhor esforço)
                err = handle_exception(
                    e,
                    message=f"Erro ao executar ação de undo '{undo_action}' para '{component}'",
                    category=ErrorCategory.INSTALLATION,  # Categoria correta
                    severity=ErrorSeverity.ERROR,
                    context=undo_op
                )
                err.log()
                logger.error(f"Falha ao executar undo para '{component}' (Etapa: {step}): {undo_action}. Continuando rollback...")
                rollback_success = False

                # Notifica erro no rollback
                try:
                    from env_dev.core.installer_wrapper import send_status_update
                    send_status_update({
                        'type': 'error',
                        'component': component,
                        'category': 'ROLLBACK',
                        'message': f'Erro ao reverter {step}: {str(e)}',
                        'severity': 'WARNING',  # WARNING porque continuamos o rollback
                        'recoverable': True
                    })
                except ImportError:
                    pass

        # Status final do rollback
        status = 'SUCCESS' if rollback_success else 'PARTIAL'
        logger.rollback(f"Rollback {status.lower()} para o componente: {self._current_component}")

        # Notifica conclusão do rollback
        try:
            from env_dev.core.installer_wrapper import send_status_update
            send_status_update({
                'type': 'rollback',
                'component': self._current_component,
                'status': status,
                'message': f'Rollback {status.lower()} para {self._current_component}'
            })
        except ImportError:
            pass

        self.clear_transaction() # Limpa o estado após o rollback

    def clear_transaction(self):
        """Limpa o estado da transação atual."""
        self._undo_stack = []
        self._transaction_active = False
        self._current_component = None
        logger.rollback("Estado da transação de rollback limpo.")

    # --- Métodos Privados para Executar Ações de Undo ---

    def _undo_restore_efi(self, backup_path: Optional[str], efi_drive_letter: Optional[str] = None):
        """
        Restaura a partição EFI a partir de um backup.

        Args:
            backup_path: Caminho para o backup da partição EFI
            efi_drive_letter: Letra da unidade da partição EFI (opcional)
        """
        if not backup_path or not os.path.exists(backup_path):
            logger.error(f"Backup da partição EFI não encontrado: {backup_path}")
            return False

        logger.rollback(f"Restaurando partição EFI a partir do backup: {backup_path}")

        # Verificar se o backup contém os arquivos necessários
        if not os.path.exists(os.path.join(backup_path, "EFI")):
            logger.error(f"Backup inválido: diretório EFI não encontrado em {backup_path}")
            return False

        # Se a letra da unidade não foi fornecida, tentar encontrar a partição EFI
        temp_drive_created = False
        efi_path = None

        try:
            # Executar script PowerShell para restaurar a partição EFI
            script_content = f"""
            # Encontrar e montar a partição EFI se necessário
            $efiDriveLetter = "{efi_drive_letter if efi_drive_letter else ''}"
            $backupPath = "{backup_path.replace('\\', '\\\\')}"
            $tempDriveCreated = $false

            if (-not $efiDriveLetter) {{
                Write-Host "Procurando partição EFI..." -ForegroundColor Yellow
                $disks = Get-Disk | Where-Object {{$_.PartitionStyle -eq "GPT"}}

                foreach ($disk in $disks) {{
                    $efiPartitions = $disk | Get-Partition | Where-Object {{$_.GptType -eq "{{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}}"}}

                    if ($efiPartitions) {{
                        try {{
                            # Obter volume da partição EFI
                            $efiVolume = $efiPartitions[0] | Get-Volume

                            # Se não tiver letra de unidade, atribuir uma temporária
                            if (-not $efiVolume.DriveLetter) {{
                                $driveLetter = 69 # Letra 'E'
                                while ([char]$driveLetter -le 90) {{
                                    $letter = [char]$driveLetter
                                    if (-not (Get-Volume -DriveLetter $letter -ErrorAction SilentlyContinue)) {{
                                        $efiPartitions[0] | Add-PartitionAccessPath -AccessPath "${{letter}}:"
                                        $efiVolume = Get-Volume -DriveLetter $letter
                                        $efiDriveLetter = $letter
                                        $tempDriveCreated = $true
                                        Write-Host "Atribuída letra temporária $letter à partição EFI" -ForegroundColor Yellow
                                        break
                                    }}
                                    $driveLetter++
                                }}
                            }} else {{
                                $efiDriveLetter = $efiVolume.DriveLetter
                            }}

                            if ($efiVolume.DriveLetter) {{
                                break
                            }}
                        }} catch {{
                            Write-Host "Erro ao acessar partição EFI: $_" -ForegroundColor Red
                        }}
                    }}
                }}
            }}

            if (-not $efiDriveLetter) {{
                Write-Host "Não foi possível encontrar ou montar a partição EFI" -ForegroundColor Red
                exit 1
            }}

            $efiPath = "${{efiDriveLetter}}:"
            Write-Host "Partição EFI encontrada em $efiPath" -ForegroundColor Green

            # Verificar se o diretório EFI existe na partição
            if (-not (Test-Path "$efiPath\EFI")) {{
                Write-Host "Diretório EFI não encontrado em $efiPath. Criando..." -ForegroundColor Yellow
                New-Item -Path "$efiPath\EFI" -ItemType Directory -Force | Out-Null
            }}

            # Fazer backup do estado atual antes da restauração
            $tempBackupDir = "$env:TEMP\EFI_Temp_Backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
            New-Item -Path $tempBackupDir -ItemType Directory -Force | Out-Null
            Write-Host "Criando backup temporário do estado atual em $tempBackupDir..." -ForegroundColor Yellow
            Copy-Item -Path "$efiPath\EFI" -Destination $tempBackupDir -Recurse -Force -ErrorAction SilentlyContinue

            # Restaurar o backup
            Write-Host "Restaurando backup para a partição EFI..." -ForegroundColor Green
            try {{
                # Limpar diretório EFI
                if (Test-Path "$efiPath\EFI") {{
                    Remove-Item -Path "$efiPath\EFI" -Recurse -Force
                }}

                # Copiar arquivos do backup
                Copy-Item -Path "$backupPath\EFI" -Destination "$efiPath\" -Recurse -Force

                Write-Host "Restauração concluída com sucesso!" -ForegroundColor Green

                # Salvar informações sobre a restauração
                $restoreInfo = @{{
                    Date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                    BackupPath = $backupPath
                    EfiPath = $efiPath
                    TempBackupPath = $tempBackupDir
                    Success = $true
                }}

                $restoreInfo | ConvertTo-Json | Out-File -FilePath "$env:TEMP\efi_restore_result.json" -Encoding utf8 -Force
            }} catch {{
                Write-Host "Erro durante a restauração: $_" -ForegroundColor Red

                # Tentar restaurar o estado anterior
                Write-Host "Tentando restaurar o estado anterior..." -ForegroundColor Yellow
                try {{
                    if (Test-Path "$efiPath\EFI") {{
                        Remove-Item -Path "$efiPath\EFI" -Recurse -Force
                    }}
                    Copy-Item -Path "$tempBackupDir\EFI" -Destination "$efiPath\" -Recurse -Force
                    Write-Host "Estado anterior restaurado." -ForegroundColor Green
                }} catch {{
                    Write-Host "Falha ao restaurar estado anterior: $_" -ForegroundColor Red
                }}

                $restoreInfo = @{{
                    Date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                    BackupPath = $backupPath
                    EfiPath = $efiPath
                    TempBackupPath = $tempBackupDir
                    Success = $false
                    Error = "$_"
                }}

                $restoreInfo | ConvertTo-Json | Out-File -FilePath "$env:TEMP\efi_restore_result.json" -Encoding utf8 -Force
                exit 1
            }}

            # Limpar letra de unidade temporária se foi criada
            if ($tempDriveCreated) {{
                try {{
                    $efiPartitions[0] | Remove-PartitionAccessPath -AccessPath "$efiPath"
                    Write-Host "Removida letra de unidade temporária $efiDriveLetter" -ForegroundColor Yellow
                }} catch {{
                    Write-Host "Erro ao remover letra de unidade temporária: $_" -ForegroundColor Yellow
                }}
            }}
            """

            # Salvar o script em um arquivo temporário
            script_path = os.path.join(tempfile.gettempdir(), "restore_efi.ps1")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script_content)

            # Executar o script PowerShell
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path],
                capture_output=True,
                text=True,
                check=False
            )

            # Verificar o resultado
            if result.returncode != 0:
                logger.error(f"Erro ao restaurar partição EFI: {result.stderr}")
                return False

            # Verificar se o arquivo de resultado existe
            result_path = os.path.join(tempfile.gettempdir(), "efi_restore_result.json")
            if os.path.exists(result_path):
                try:
                    with open(result_path, "r", encoding="utf-8") as f:
                        restore_result = json.load(f)

                    if restore_result.get("Success", False):
                        logger.rollback(f"Partição EFI restaurada com sucesso para {restore_result.get('EfiPath')}")
                        return True
                    else:
                        logger.error(f"Falha ao restaurar partição EFI: {restore_result.get('Error', 'Erro desconhecido')}")
                        return False
                except Exception as e:
                    logger.error(f"Erro ao ler resultado da restauração: {e}")
                    return False

            # Se chegou aqui, assumimos que a restauração foi bem-sucedida
            logger.rollback("Partição EFI restaurada com sucesso")
            return True

        except Exception as e:
            err = handle_exception(
                e,
                message=f"Erro inesperado ao restaurar partição EFI a partir de {backup_path}",
                category=ErrorCategory.ROLLBACK,
                severity=ErrorSeverity.ERROR
            )
            err.log()
            return False

    def _undo_delete_path(self, path: Optional[str]):
        """Executa a ação de undo para deletar um arquivo ou diretório."""
        if not path or not os.path.exists(path):
            logger.warning(f"Undo 'delete_path': Caminho não fornecido ou não existe: {path}. Ignorando.")
            return

        try:
            if os.path.isfile(path):
                os.remove(path)
                logger.info(f"Undo 'delete_path': Arquivo removido: {path}")
            elif os.path.isdir(path):
                shutil.rmtree(path)
                logger.info(f"Undo 'delete_path': Diretório removido: {path}")
            else:
                 logger.warning(f"Undo 'delete_path': Caminho não é arquivo nem diretório: {path}")
        except OSError as e:
            err = file_error(
                f"Erro ao executar undo 'delete_path' para {path}: {e}",
                file_path=path,
                severity=ErrorSeverity.ERROR
            )
            err.log()
            # Lança a exceção para ser capturada pelo loop principal de rollback
            raise

    def _undo_run_command(self, command: Optional[List[str]]):
        """Executa a ação de undo para rodar um comando (ex: desinstalador)."""
        if not command or not isinstance(command, list) or len(command) == 0:
            logger.warning(f"Undo 'run_command': Comando inválido ou não fornecido: {command}. Ignorando.")
            return

        logger.info(f"Undo 'run_command': Executando: {' '.join(command)}")
        try:
            # Usar capture_output=True para evitar poluir o log principal, mas logar em caso de erro
            result = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore')
            if result.returncode != 0:
                logger.error(f"Undo 'run_command' falhou (Código: {result.returncode}): {' '.join(command)}")
                logger.error(f"  stdout: {result.stdout.strip()}")
                logger.error(f"  stderr: {result.stderr.strip()}")
                # Lança exceção para indicar falha no undo
                raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout, stderr=result.stderr)
            else:
                 logger.info(f"Undo 'run_command' concluído com sucesso: {' '.join(command)}")

        except FileNotFoundError as e:
             err = handle_exception(
                e,
                message=f"Erro ao executar undo 'run_command': Comando '{command[0]}' não encontrado.",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.EXECUTION,
                context={"command": ' '.join(command)}
            )
             err.log()
             raise
        except Exception as e:
            # Captura outras exceções do subprocess
            err = handle_exception(
                e,
                message=f"Erro inesperado ao executar undo 'run_command' {' '.join(command)}: {e}",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.EXECUTION,
                context={"command": ' '.join(command)}
            )
            err.log()
            raise

    # --- Métodos adicionais para ações de undo ---

    def _undo_run_script(self, script_path: Optional[str], args: Optional[List[str]] = None, cwd: Optional[str] = None):
        """Executa um script de undo para reverter ações de um script anterior."""
        if not script_path or not os.path.isfile(script_path):
            logger.warning(f"Undo 'run_script': Script não fornecido ou não existe: {script_path}. Ignorando.")
            return

        if args is None:
            args = []

        logger.info(f"Undo 'run_script': Executando script: {script_path} {' '.join(args) if args else ''}")
        try:
            # Determina o tipo de script com base na extensão
            if script_path.lower().endswith('.ps1'):
                cmd = ['powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', script_path] + args
            elif script_path.lower().endswith('.bat') or script_path.lower().endswith('.cmd'):
                cmd = [script_path] + args
            else:
                # Assume que é um executável
                cmd = [script_path] + args

            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore')
            if result.returncode != 0:
                logger.error(f"Undo 'run_script' falhou (Código: {result.returncode}): {script_path}")
                logger.error(f"  stdout: {result.stdout.strip()}")
                logger.error(f"  stderr: {result.stderr.strip()}")
                # Loga erro mas não interrompe o rollback
            else:
                logger.info(f"Undo 'run_script' concluído com sucesso: {script_path}")

        except Exception as e:
            logger.error(f"Erro ao executar undo 'run_script' {script_path}: {e}")
            # Continua com o rollback mesmo em caso de erro

    def _undo_restore_env(self, variable_name: Optional[str], original_value: Optional[str], scope: str = 'user'):
        """Restaura uma variável de ambiente para seu valor original."""
        if not variable_name:
            logger.warning("Undo 'restore_env': Nome da variável não fornecido. Ignorando.")
            return

        try:
            from env_dev.utils import env_manager
            logger.info(f"Undo 'restore_env': Restaurando variável '{variable_name}' para '{original_value}'")
            env_manager.set_env_var(variable_name, original_value, scope)
        except Exception as e:
            logger.error(f"Erro ao restaurar variável de ambiente '{variable_name}': {e}")

    def _undo_unset_env(self, variable_name: Optional[str], scope: str = 'user'):
        """Remove uma variável de ambiente."""
        if not variable_name:
            logger.warning("Undo 'unset_env': Nome da variável não fornecido. Ignorando.")
            return

        try:
            from env_dev.utils import env_manager
            logger.info(f"Undo 'unset_env': Removendo variável '{variable_name}'")
            env_manager.unset_env_var(variable_name, scope)
        except Exception as e:
            logger.error(f"Erro ao remover variável de ambiente '{variable_name}': {e}")

    def _undo_remove_path(self, path_to_remove: Optional[str], scope: str = 'user'):
        """Remove um caminho da variável PATH."""
        if not path_to_remove:
            logger.warning("Undo 'remove_path': Caminho não fornecido. Ignorando.")
            return

        try:
            from env_dev.utils import env_manager
            logger.info(f"Undo 'remove_path': Removendo '{path_to_remove}' do PATH")
            env_manager.remove_from_path(path_to_remove, scope)
        except Exception as e:
            logger.error(f"Erro ao remover '{path_to_remove}' do PATH: {e}")

    def _undo_modify_json(self, file_path: Optional[str], operation: str = 'remove_key', key: Optional[str] = None, value: Any = None):
        """Modifica um arquivo JSON para desfazer uma operação anterior."""
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"Undo 'modify_json': Arquivo não fornecido ou não existe: {file_path}. Ignorando.")
            return

        if not key and operation != 'restore_file':
            logger.warning("Undo 'modify_json': Chave não fornecida para operação {operation}. Ignorando.")
            return

        try:
            import json

            # Faz backup do arquivo antes de modificá-lo
            backup_path = f"{file_path}.bak"
            try:
                import shutil
                shutil.copy2(file_path, backup_path)
                logger.debug(f"Backup do arquivo JSON criado: {backup_path}")
            except Exception as backup_e:
                logger.warning(f"Não foi possível criar backup do arquivo JSON: {backup_e}")

            # Carrega o arquivo JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Executa a operação solicitada
            if operation == 'remove_key':
                if isinstance(data, dict) and key in data:
                    logger.info(f"Undo 'modify_json': Removendo chave '{key}' de {file_path}")
                    del data[key]
                else:
                    logger.warning(f"Chave '{key}' não encontrada em {file_path}")

            elif operation == 'add_key':
                if isinstance(data, dict):
                    logger.info(f"Undo 'modify_json': Adicionando chave '{key}' com valor {value} em {file_path}")
                    data[key] = value
                else:
                    logger.warning(f"Arquivo JSON {file_path} não é um dicionário. Não é possível adicionar chave.")

            elif operation == 'restore_file':
                # Restaura o arquivo de um backup
                if os.path.exists(backup_path):
                    logger.info(f"Undo 'modify_json': Restaurando {file_path} do backup")
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    logger.warning(f"Arquivo de backup {backup_path} não encontrado")

            else:
                logger.warning(f"Operação '{operation}' não suportada para undo 'modify_json'")
                return

            # Salva as alterações
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Undo 'modify_json': Operação '{operation}' concluída com sucesso em {file_path}")

        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON de {file_path}: {e}")
        except Exception as e:
            logger.error(f"Erro ao executar undo 'modify_json' em {file_path}: {e}")

    def _undo_delete_registry_key(self, key_path: str, value_name: Optional[str] = None, value_data: Any = None, value_type: str = "REG_SZ"):
        """
        Restaura uma chave ou valor do registro que foi deletado.
        
        Args:
            key_path: Caminho da chave do registro (ex: HKEY_LOCAL_MACHINE\\SOFTWARE\\MyApp)
            value_name: Nome do valor (None para restaurar a chave inteira)
            value_data: Dados do valor a ser restaurado
            value_type: Tipo do valor (REG_SZ, REG_DWORD, etc.)
        """
        try:
            import winreg
            
            logger.rollback(f"Restaurando registro: {key_path}")
            
            # Separa a hive da chave
            parts = key_path.split('\\', 1)
            if len(parts) != 2:
                logger.error(f"Caminho de registro inválido: {key_path}")
                return False
                
            hive_name, subkey = parts
            
            # Mapeia nomes de hive para constantes
            hive_map = {
                'HKEY_LOCAL_MACHINE': winreg.HKEY_LOCAL_MACHINE,
                'HKEY_CURRENT_USER': winreg.HKEY_CURRENT_USER,
                'HKEY_CLASSES_ROOT': winreg.HKEY_CLASSES_ROOT,
                'HKEY_USERS': winreg.HKEY_USERS,
                'HKEY_CURRENT_CONFIG': winreg.HKEY_CURRENT_CONFIG
            }
            
            hive = hive_map.get(hive_name)
            if hive is None:
                logger.error(f"Hive de registro desconhecida: {hive_name}")
                return False
            
            if value_name is None:
                # Restaurar chave inteira
                try:
                    winreg.CreateKey(hive, subkey)
                    logger.info(f"Chave de registro restaurada: {key_path}")
                    return True
                except Exception as e:
                    logger.error(f"Erro ao restaurar chave de registro {key_path}: {e}")
                    return False
            else:
                # Restaurar valor específico
                try:
                    with winreg.OpenKey(hive, subkey, 0, winreg.KEY_SET_VALUE) as key:
                        # Mapeia tipos de valor
                        type_map = {
                            'REG_SZ': winreg.REG_SZ,
                            'REG_DWORD': winreg.REG_DWORD,
                            'REG_BINARY': winreg.REG_BINARY,
                            'REG_EXPAND_SZ': winreg.REG_EXPAND_SZ,
                            'REG_MULTI_SZ': winreg.REG_MULTI_SZ
                        }
                        
                        reg_type = type_map.get(value_type, winreg.REG_SZ)
                        winreg.SetValueEx(key, value_name, 0, reg_type, value_data)
                        logger.info(f"Valor de registro restaurado: {key_path}\\{value_name}")
                        return True
                except Exception as e:
                    logger.error(f"Erro ao restaurar valor de registro {key_path}\\{value_name}: {e}")
                    return False
                    
        except ImportError:
            logger.error("Módulo winreg não disponível (não é Windows?)")
            return False
        except Exception as e:
            logger.error(f"Erro geral ao restaurar registro: {e}")
            return False
    
    def _undo_create_registry_key(self, key_path: str, value_name: Optional[str] = None):
        """
        Remove uma chave ou valor do registro que foi criado.
        
        Args:
            key_path: Caminho da chave do registro
            value_name: Nome do valor (None para remover a chave inteira)
        """
        try:
            import winreg
            
            logger.rollback(f"Removendo registro criado: {key_path}")
            
            # Separa a hive da chave
            parts = key_path.split('\\', 1)
            if len(parts) != 2:
                logger.error(f"Caminho de registro inválido: {key_path}")
                return False
                
            hive_name, subkey = parts
            
            # Mapeia nomes de hive para constantes
            hive_map = {
                'HKEY_LOCAL_MACHINE': winreg.HKEY_LOCAL_MACHINE,
                'HKEY_CURRENT_USER': winreg.HKEY_CURRENT_USER,
                'HKEY_CLASSES_ROOT': winreg.HKEY_CLASSES_ROOT,
                'HKEY_USERS': winreg.HKEY_USERS,
                'HKEY_CURRENT_CONFIG': winreg.HKEY_CURRENT_CONFIG
            }
            
            hive = hive_map.get(hive_name)
            if hive is None:
                logger.error(f"Hive de registro desconhecida: {hive_name}")
                return False
            
            if value_name is None:
                # Remover chave inteira
                try:
                    winreg.DeleteKey(hive, subkey)
                    logger.info(f"Chave de registro removida: {key_path}")
                    return True
                except FileNotFoundError:
                    logger.warning(f"Chave de registro já não existe: {key_path}")
                    return True
                except Exception as e:
                    logger.error(f"Erro ao remover chave de registro {key_path}: {e}")
                    return False
            else:
                # Remover valor específico
                try:
                    with winreg.OpenKey(hive, subkey, 0, winreg.KEY_SET_VALUE) as key:
                        winreg.DeleteValue(key, value_name)
                        logger.info(f"Valor de registro removido: {key_path}\\{value_name}")
                        return True
                except FileNotFoundError:
                    logger.warning(f"Valor de registro já não existe: {key_path}\\{value_name}")
                    return True
                except Exception as e:
                    logger.error(f"Erro ao remover valor de registro {key_path}\\{value_name}: {e}")
                    return False
                    
        except ImportError:
            logger.error("Módulo winreg não disponível (não é Windows?)")
            return False
        except Exception as e:
            logger.error(f"Erro geral ao remover registro: {e}")
            return False
    
    def _undo_modify_registry_value(self, key_path: str, value_name: str, old_value: Any, old_type: str = "REG_SZ"):
        """
        Restaura o valor anterior de uma entrada do registro.
        
        Args:
            key_path: Caminho da chave do registro
            value_name: Nome do valor
            old_value: Valor anterior a ser restaurado
            old_type: Tipo do valor anterior
        """
        return self._undo_delete_registry_key(key_path, value_name, old_value, old_type)
    
    def _undo_create_service(self, service_name: str):
        """
        Remove um serviço do Windows que foi criado.
        
        Args:
            service_name: Nome do serviço
        """
        try:
            import subprocess
            
            logger.rollback(f"Removendo serviço criado: {service_name}")
            
            # Para o serviço primeiro
            try:
                subprocess.run(['sc', 'stop', service_name], 
                             capture_output=True, check=False)
            except Exception:
                pass  # Ignora erro se o serviço já estiver parado
            
            # Remove o serviço
            result = subprocess.run(['sc', 'delete', service_name], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Serviço removido com sucesso: {service_name}")
                return True
            else:
                logger.error(f"Erro ao remover serviço {service_name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao remover serviço {service_name}: {e}")
            return False
    
    def _undo_install_driver(self, driver_inf_path: str):
        """
        Remove um driver que foi instalado.
        
        Args:
            driver_inf_path: Caminho para o arquivo .inf do driver
        """
        try:
            import subprocess
            
            logger.rollback(f"Removendo driver instalado: {driver_inf_path}")
            
            # Usa pnputil para remover o driver
            result = subprocess.run(['pnputil', '/delete-driver', driver_inf_path, '/uninstall'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Driver removido com sucesso: {driver_inf_path}")
                return True
            else:
                logger.warning(f"Aviso ao remover driver {driver_inf_path}: {result.stderr}")
                # Tenta método alternativo
                result2 = subprocess.run(['pnputil', '/delete-driver', driver_inf_path], 
                                       capture_output=True, text=True)
                if result2.returncode == 0:
                    logger.info(f"Driver removido com método alternativo: {driver_inf_path}")
                    return True
                else:
                    logger.error(f"Erro ao remover driver {driver_inf_path}: {result2.stderr}")
                    return False
                    
        except Exception as e:
            logger.error(f"Erro ao remover driver {driver_inf_path}: {e}")
            return False
    
    def _undo_chocolatey_uninstall(self, package_name: Optional[str], component_name: Optional[str] = None):
        """
        Desinstala um pacote Chocolatey que foi instalado.
        
        Args:
            package_name: Nome do pacote Chocolatey
            component_name: Nome do componente (para logs)
        """
        if not package_name:
            logger.error("Nome do pacote Chocolatey não fornecido para rollback")
            return False
            
        try:
            logger.rollback(f"Desinstalando pacote Chocolatey: {package_name}")
            
            # Executa comando de desinstalação do Chocolatey
            result = subprocess.run(
                ['choco', 'uninstall', package_name, '-y'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos de timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Pacote Chocolatey desinstalado com sucesso: {package_name}")
                return True
            else:
                logger.warning(f"Aviso ao desinstalar pacote {package_name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout ao desinstalar pacote Chocolatey: {package_name}")
            return False
        except Exception as e:
            logger.error(f"Erro ao desinstalar pacote Chocolatey {package_name}: {e}")
            return False
    
    def _undo_remove_directory(self, path: Optional[str], component_name: Optional[str] = None):
        """
        Remove um diretório que foi criado durante a instalação.
        
        Args:
            path: Caminho do diretório a ser removido
            component_name: Nome do componente (para logs)
        """
        if not path:
            logger.error("Caminho do diretório não fornecido para rollback")
            return False
            
        try:
            if os.path.exists(path) and os.path.isdir(path):
                logger.rollback(f"Removendo diretório criado: {path}")
                shutil.rmtree(path)
                logger.info(f"Diretório removido com sucesso: {path}")
                return True
            else:
                logger.debug(f"Diretório não existe ou não é um diretório: {path}")
                return True  # Considera sucesso se já não existe
                
        except Exception as e:
            logger.error(f"Erro ao remover diretório {path}: {e}")
            return False

# Exemplo de uso (apenas para ilustração, não será executado diretamente)
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    manager = RollbackManager()
    comp = "MeuComponenteTeste"

    manager.start_transaction(comp)

    # Simula registro de ações
    manager.register_action({
        'step': 'Extraindo Arquivos',
        'undo_action': 'delete_path',
        'parameters': {'path': './temp_extract_dir_teste'}
    })
    # Cria um diretório para teste
    os.makedirs('./temp_extract_dir_teste', exist_ok=True)
    print("Diretório de teste criado.")

    manager.register_action({
        'step': 'Executando Comando Falso',
        'undo_action': 'run_command',
        'parameters': {'command': ['cmd', '/c', 'echo Comando de undo executado']}
    })

    print("\nSimulando falha e acionando rollback...")
    manager.trigger_rollback()

    print("\nVerificando se o diretório de teste foi removido:")
    if not os.path.exists('./temp_extract_dir_teste'):
        print("Diretório removido com sucesso pelo rollback.")
    else:
        print("ERRO: Diretório não foi removido pelo rollback.")

    print("\nTentando commitar (não deve fazer nada pois o rollback já ocorreu):")
    manager.commit_transaction()