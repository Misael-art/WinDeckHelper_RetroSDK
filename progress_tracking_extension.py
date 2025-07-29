# -*- coding: utf-8 -*-
"""
Extensão do DownloadManager com funcionalidades avançadas de progress tracking
Para ser integrada ao download_manager.py
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import threading
import json
import os

@dataclass
class ProgressNotification:
    """Notificação de progresso para interface"""
    download_id: str
    component_name: str
    progress: 'DownloadProgress'
    timestamp: datetime
    notification_type: str  # 'started', 'progress', 'completed', 'failed'
    
    def to_dict(self) -> Dict:
        """Converte para dicionário para serialização"""
        return {
            'download_id': self.download_id,
            'component_name': self.component_name,
            'timestamp': self.timestamp.isoformat(),
            'notification_type': self.notification_type,
            'progress': {
                'total_size': self.progress.total_size,
                'downloaded_size': self.progress.downloaded_size,
                'percentage': self.progress.percentage,
                'speed': self.progress.speed,
                'average_speed': self.progress.average_speed,
                'eta': self.progress.eta,
                'status': self.progress.status.value,
                'message': self.progress.message,
                'elapsed_time': self.progress.elapsed_time,
                'url': self.progress.url
            }
        }

@dataclass
class DownloadLog:
    """Log detalhado de operação de download"""
    download_id: str
    component_name: str
    url: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "started"
    total_size: int = 0
    downloaded_size: int = 0
    average_speed: float = 0.0
    error_message: str = ""
    retry_count: int = 0
    verification_passed: bool = False
    mirror_used: str = ""
    
    def to_dict(self) -> Dict:
        """Converte para dicionário para serialização"""
        return {
            'download_id': self.download_id,
            'component_name': self.component_name,
            'url': self.url,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'total_size': self.total_size,
            'downloaded_size': self.downloaded_size,
            'average_speed': self.average_speed,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'verification_passed': self.verification_passed,
            'mirror_used': self.mirror_used
        }

class ProgressTracker:
    """
    Sistema avançado de tracking de progresso para downloads
    Implementa notificações em tempo real e logs detalhados
    """
    
    def __init__(self):
        self.active_downloads: Dict[str, DownloadLog] = {}
        self.progress_callbacks: List[Callable[[ProgressNotification], None]] = []
        self.download_logs: List[DownloadLog] = []
        self.lock = threading.Lock()
        self.logs_dir = "logs"
        
        # Cria diretório de logs
        os.makedirs(self.logs_dir, exist_ok=True)
    
    def register_progress_callback(self, callback: Callable[[ProgressNotification], None]):
        """Registra callback para notificações de progresso"""
        with self.lock:
            self.progress_callbacks.append(callback)
    
    def unregister_progress_callback(self, callback: Callable[[ProgressNotification], None]):
        """Remove callback de notificações de progresso"""
        with self.lock:
            if callback in self.progress_callbacks:
                self.progress_callbacks.remove(callback)
    
    def start_download_tracking(self, download_id: str, component_name: str, url: str) -> DownloadLog:
        """Inicia tracking de um novo download"""
        with self.lock:
            download_log = DownloadLog(
                download_id=download_id,
                component_name=component_name,
                url=url,
                start_time=datetime.now()
            )
            
            self.active_downloads[download_id] = download_log
            self.download_logs.append(download_log)
            
            # Notifica início do download
            self._send_notification(download_id, component_name, None, 'started')
            
            return download_log
    
    def update_download_progress(self, download_id: str, progress: 'DownloadProgress'):
        """Atualiza progresso de um download"""
        with self.lock:
            if download_id in self.active_downloads:
                download_log = self.active_downloads[download_id]
                download_log.total_size = progress.total_size
                download_log.downloaded_size = progress.downloaded_size
                download_log.average_speed = progress.average_speed
                
                # Notifica progresso
                self._send_notification(download_id, download_log.component_name, progress, 'progress')
    
    def complete_download_tracking(self, download_id: str, success: bool, 
                                 error_message: str = "", verification_passed: bool = False,
                                 mirror_used: str = "", retry_count: int = 0):
        """Completa tracking de um download"""
        with self.lock:
            if download_id in self.active_downloads:
                download_log = self.active_downloads[download_id]
                download_log.end_time = datetime.now()
                download_log.status = "completed" if success else "failed"
                download_log.error_message = error_message
                download_log.verification_passed = verification_passed
                download_log.mirror_used = mirror_used
                download_log.retry_count = retry_count
                
                # Remove dos downloads ativos
                del self.active_downloads[download_id]
                
                # Notifica conclusão
                notification_type = 'completed' if success else 'failed'
                self._send_notification(download_id, download_log.component_name, None, notification_type)
                
                # Salva log detalhado
                self._save_download_log(download_log)
    
    def _send_notification(self, download_id: str, component_name: str, 
                          progress: Optional['DownloadProgress'], notification_type: str):
        """Envia notificação para todos os callbacks registrados"""
        if not self.progress_callbacks:
            return
            
        # Cria progresso vazio se não fornecido
        if progress is None:
            from env_dev.core.download_manager import DownloadProgress, DownloadStatus
            progress = DownloadProgress(
                total_size=0,
                downloaded_size=0,
                speed=0,
                eta=0,
                percentage=0,
                status=DownloadStatus.PENDING,
                component_name=component_name
            )
        
        notification = ProgressNotification(
            download_id=download_id,
            component_name=component_name,
            progress=progress,
            timestamp=datetime.now(),
            notification_type=notification_type
        )
        
        # Envia para todos os callbacks
        for callback in self.progress_callbacks:
            try:
                callback(notification)
            except Exception as e:
                print(f"Erro no callback de progresso: {e}")
    
    def _save_download_log(self, download_log: DownloadLog):
        """Salva log detalhado de download em arquivo"""
        try:
            log_file = os.path.join(self.logs_dir, f"download_log_{datetime.now().strftime('%Y%m%d')}.json")
            
            # Carrega logs existentes ou cria lista vazia
            logs = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                except:
                    logs = []
            
            # Adiciona novo log
            logs.append(download_log.to_dict())
            
            # Salva logs atualizados
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Erro ao salvar log de download: {e}")
    
    def get_active_downloads(self) -> List[DownloadLog]:
        """Retorna lista de downloads ativos"""
        with self.lock:
            return list(self.active_downloads.values())
    
    def get_download_history(self, limit: int = 100) -> List[DownloadLog]:
        """Retorna histórico de downloads"""
        with self.lock:
            return self.download_logs[-limit:]
    
    def get_download_statistics(self) -> Dict:
        """Retorna estatísticas de downloads"""
        with self.lock:
            total_downloads = len(self.download_logs)
            successful_downloads = sum(1 for log in self.download_logs if log.status == "completed")
            failed_downloads = sum(1 for log in self.download_logs if log.status == "failed")
            
            total_size = sum(log.downloaded_size for log in self.download_logs if log.status == "completed")
            
            if successful_downloads > 0:
                avg_speed = sum(log.average_speed for log in self.download_logs if log.status == "completed") / successful_downloads
            else:
                avg_speed = 0
            
            return {
                'total_downloads': total_downloads,
                'successful_downloads': successful_downloads,
                'failed_downloads': failed_downloads,
                'success_rate': (successful_downloads / total_downloads * 100) if total_downloads > 0 else 0,
                'total_downloaded_size': total_size,
                'average_speed': avg_speed,
                'active_downloads': len(self.active_downloads)
            }

# Instância global do progress tracker
progress_tracker = ProgressTracker()