#!/usr/bin/env python3
"""
Demonstração do sistema de progress tracking detalhado
Implementa os requisitos da task 3.3
"""

import time
import logging
from datetime import datetime
from env_dev.core.download_manager import DownloadManager, DownloadProgress, DownloadStatus
from progress_tracking_extension import progress_tracker, ProgressNotification

# Configura logging para ver o funcionamento detalhado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def demo_progress_tracking():
    """
    Demonstração do sistema de progress tracking detalhado
    """
    print("=== Demonstração do Sistema de Progress Tracking Detalhado ===")
    
    # Lista para armazenar notificações recebidas
    notifications_received = []
    
    def progress_notification_handler(notification: ProgressNotification):
        """Handler para notificações de progresso"""
        notifications_received.append(notification)
        print(f"📢 Notificação: {notification.notification_type} - {notification.component_name}")
        if notification.progress:
            print(f"   Progresso: {notification.progress.get_detailed_status()}")
    
    # Registra handler de notificações
    progress_tracker.register_progress_callback(progress_notification_handler)
    
    print("\n1. Testando formatação de progresso detalhado...")
    
    # Cria progresso de exemplo
    progress = DownloadProgress(
        total_size=1024*1024*50,  # 50MB
        downloaded_size=1024*1024*15,  # 15MB
        speed=1024*1024*2,  # 2MB/s
        eta=17.5,  # 17.5 segundos
        percentage=30.0,
        status=DownloadStatus.DOWNLOADING,
        component_name="exemplo_componente",
        url="https://example.com/arquivo.exe"
    )
    
    # Demonstra formatação
    print(f"   Velocidade: {progress.format_speed(progress.speed)}")
    print(f"   Tamanho: {progress.format_size(progress.downloaded_size)}/{progress.format_size(progress.total_size)}")
    print(f"   Tempo restante: {progress.format_time(progress.eta)}")
    print(f"   Status detalhado: {progress.get_detailed_status()}")
    
    print("\n2. Testando sistema de tracking de downloads...")
    
    # Inicia tracking de download
    download_id = f"demo_download_{int(time.time())}"
    component_name = "componente_demo"
    url = "https://example.com/demo.exe"
    
    download_log = progress_tracker.start_download_tracking(download_id, component_name, url)
    print(f"   ✓ Download iniciado: {download_id}")
    
    # Simula progresso de download
    for i in range(0, 101, 20):
        progress = DownloadProgress(
            total_size=1000000,
            downloaded_size=i * 10000,
            speed=50000 + (i * 1000),  # Velocidade variável
            eta=(100-i) * 0.5,
            percentage=i,
            status=DownloadStatus.DOWNLOADING if i < 100 else DownloadStatus.COMPLETED,
            component_name=component_name,
            url=url
        )
        
        # Atualiza histórico de velocidade para média móvel
        progress.update_speed_history(progress.speed)
        
        progress_tracker.update_download_progress(download_id, progress)
        print(f"   📊 Progresso: {progress.get_detailed_status()}")
        
        time.sleep(0.1)  # Simula tempo de download
    
    # Completa download
    progress_tracker.complete_download_tracking(
        download_id, 
        success=True, 
        verification_passed=True,
        mirror_used="https://mirror.example.com",
        retry_count=0
    )
    print(f"   ✓ Download concluído: {download_id}")
    
    print("\n3. Testando estatísticas de download...")
    
    stats = progress_tracker.get_download_statistics()
    print(f"   Total de downloads: {stats['total_downloads']}")
    print(f"   Downloads bem-sucedidos: {stats['successful_downloads']}")
    print(f"   Taxa de sucesso: {stats['success_rate']:.1f}%")
    print(f"   Tamanho total baixado: {progress.format_size(stats['total_downloaded_size'])}")
    print(f"   Velocidade média: {progress.format_speed(stats['average_speed'])}")
    print(f"   Downloads ativos: {stats['active_downloads']}")
    
    print("\n4. Testando notificações recebidas...")
    
    print(f"   Total de notificações: {len(notifications_received)}")
    for i, notification in enumerate(notifications_received):
        print(f"   {i+1}. {notification.notification_type} - {notification.component_name} ({notification.timestamp.strftime('%H:%M:%S')})")
    
    print("\n5. Testando histórico de downloads...")
    
    history = progress_tracker.get_download_history(limit=5)
    print(f"   Downloads no histórico: {len(history)}")
    for log in history:
        duration = (log.end_time - log.start_time).total_seconds() if log.end_time else 0
        print(f"   - {log.component_name}: {log.status} em {duration:.1f}s")
    
    print("\n6. Demonstrando logs detalhados...")
    
    print("   O sistema salva logs detalhados em arquivos JSON diários:")
    print("   - Timestamp de início e fim")
    print("   - URLs utilizadas (incluindo mirrors)")
    print("   - Velocidades médias e tamanhos")
    print("   - Status de verificação de integridade")
    print("   - Número de tentativas de retry")
    print("   - Mensagens de erro detalhadas")
    
    # Remove handler de notificações
    progress_tracker.unregister_progress_callback(progress_notification_handler)
    
    print("\n✅ Demonstração do sistema de progress tracking concluída!")
    print("\nRecursos implementados:")
    print("✓ Sistema de progress tracking em tempo real")
    print("✓ Cálculo de velocidade e tempo restante com média móvel")
    print("✓ Notificações de progresso para interface")
    print("✓ Logs detalhados de operações de download")
    print("✓ Formatação legível de tamanhos, velocidades e tempos")
    print("✓ Estatísticas e histórico de downloads")
    print("✓ Sistema de callbacks para integração com interface")

if __name__ == "__main__":
    demo_progress_tracking()