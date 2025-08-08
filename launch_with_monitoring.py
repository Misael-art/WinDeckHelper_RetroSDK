#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lançador da Aplicação com Monitoramento Completo

Este script lança o Sistema de Instalação Robusto com monitoramento em tempo real
de todas as operações, métricas de performance e logs detalhados.
"""

import asyncio
import sys
import os
import time
import psutil
import threading
from pathlib import Path
from datetime import datetime
import json
import logging
from typing import Dict, Any, List
import signal

# Adicionar core ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

try:
    from core.robust_installation_system import RobustInstallationSystem
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    sys.exit(1)

# Configurar logging avançado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/application_monitoring.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SystemMonitor:
    """Monitor de sistema em tempo real"""
    
    def __init__(self):
        self.monitoring = False
        self.metrics = {
            'cpu_usage': [],
            'memory_usage': [],
            'disk_usage': [],
            'network_io': [],
            'process_count': [],
            'timestamps': []
        }
        self.start_time = None
        
    def start_monitoring(self):
        """Inicia monitoramento em thread separada"""
        self.monitoring = True
        self.start_time = time.time()
        
        def monitor_loop():
            while self.monitoring:
                try:
                    # Coletar métricas
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    net_io = psutil.net_io_counters()
                    process_count = len(psutil.pids())
                    
                    # Armazenar métricas
                    timestamp = time.time()
                    self.metrics['cpu_usage'].append(cpu_percent)
                    self.metrics['memory_usage'].append(memory.percent)
                    self.metrics['disk_usage'].append(disk.percent)
                    self.metrics['network_io'].append({
                        'bytes_sent': net_io.bytes_sent,
                        'bytes_recv': net_io.bytes_recv
                    })
                    self.metrics['process_count'].append(process_count)
                    self.metrics['timestamps'].append(timestamp)
                    
                    # Manter apenas últimos 100 pontos
                    for key in self.metrics:
                        if len(self.metrics[key]) > 100:
                            self.metrics[key] = self.metrics[key][-100:]
                    
                    # Log de métricas críticas
                    if cpu_percent > 80:
                        logger.warning(f"🔥 CPU alta: {cpu_percent:.1f}%")
                    if memory.percent > 85:
                        logger.warning(f"🔥 Memória alta: {memory.percent:.1f}%")
                    
                except Exception as e:
                    logger.error(f"Erro no monitoramento: {e}")
                
                time.sleep(2)  # Coletar a cada 2 segundos
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        logger.info("📊 Monitoramento de sistema iniciado")
    
    def stop_monitoring(self):
        """Para o monitoramento"""
        self.monitoring = False
        logger.info("📊 Monitoramento de sistema parado")
    
    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumo das métricas"""
        if not self.metrics['cpu_usage']:
            return {}
        
        runtime = time.time() - self.start_time if self.start_time else 0
        
        return {
            'runtime_seconds': runtime,
            'runtime_formatted': f"{runtime/60:.1f} minutos",
            'avg_cpu_usage': sum(self.metrics['cpu_usage']) / len(self.metrics['cpu_usage']),
            'max_cpu_usage': max(self.metrics['cpu_usage']),
            'avg_memory_usage': sum(self.metrics['memory_usage']) / len(self.metrics['memory_usage']),
            'max_memory_usage': max(self.metrics['memory_usage']),
            'samples_collected': len(self.metrics['cpu_usage'])
        }


class ApplicationLauncher:
    """Lançador principal da aplicação com monitoramento"""
    
    def __init__(self):
        self.system = None
        self.monitor = SystemMonitor()
        self.running = False
        self.results = {}
        
        # Configurar handler para CTRL+C
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Criar diretórios necessários
        Path("logs").mkdir(exist_ok=True)
        Path("reports").mkdir(exist_ok=True)
        
        logger.info("🚀 LANÇADOR DA APLICAÇÃO INICIALIZADO")
    
    def _signal_handler(self, signum, frame):
        """Handler para interrupção do usuário"""
        logger.info("\n⚠️  Interrupção detectada. Finalizando aplicação...")
        self.running = False
        self.monitor.stop_monitoring()
        self._generate_final_report()
        sys.exit(0)
    
    async def launch_application(self):
        """Lança a aplicação principal com monitoramento completo"""
        try:
            logger.info("="*80)
            logger.info("🎯 LANÇANDO SISTEMA DE INSTALAÇÃO ROBUSTO")
            logger.info("="*80)
            
            # Iniciar monitoramento
            self.monitor.start_monitoring()
            self.running = True
            
            # Inicializar sistema
            logger.info("🔧 Inicializando Sistema de Instalação Robusto...")
            self.system = RobustInstallationSystem()
            
            # Executar operações principais
            await self._execute_main_operations()
            
            # Monitoramento contínuo
            await self._continuous_monitoring()
            
        except Exception as e:
            logger.error(f"❌ Erro crítico na aplicação: {e}")
            raise
        finally:
            self.monitor.stop_monitoring()
            self._generate_final_report()
    
    async def _execute_main_operations(self):
        """Executa as operações principais do sistema"""
        operations = [
            ("Varredura de Componentes", self._scan_components),
            ("Detecção Unificada", self._unified_detection),
            ("Validação de Dependências", self._validate_dependencies),
            ("Análise de Armazenamento", self._analyze_storage),
            ("Verificação Steam Deck", self._check_steam_deck)
        ]
        
        for operation_name, operation_func in operations:
            try:
                logger.info(f"\n🔄 Executando: {operation_name}")
                start_time = time.time()
                
                result = await operation_func()
                
                execution_time = time.time() - start_time
                self.results[operation_name] = {
                    'result': result,
                    'execution_time': execution_time,
                    'success': True
                }
                
                logger.info(f"✅ {operation_name} concluída em {execution_time:.2f}s")
                
            except Exception as e:
                logger.error(f"❌ Erro em {operation_name}: {e}")
                self.results[operation_name] = {
                    'error': str(e),
                    'success': False
                }
    
    async def _scan_components(self):
        """Executa varredura de componentes"""
        components = await self.system.scan_components()
        
        # Análise detalhada
        categories = {}
        methods = {}
        
        for comp in components.values():
            # Por categoria
            if comp.category not in categories:
                categories[comp.category] = 0
            categories[comp.category] += 1
            
            # Por método
            if comp.install_method not in methods:
                methods[comp.install_method] = 0
            methods[comp.install_method] += 1
        
        result = {
            'total_components': len(components),
            'categories': dict(sorted(categories.items(), key=lambda x: x[1], reverse=True)),
            'install_methods': dict(sorted(methods.items(), key=lambda x: x[1], reverse=True)),
            'top_categories': list(categories.keys())[:5]
        }
        
        logger.info(f"📋 {result['total_components']} componentes carregados")
        logger.info(f"📊 {len(result['categories'])} categorias diferentes")
        
        return result
    
    async def _unified_detection(self):
        """Executa detecção unificada"""
        detection_results = await self.system.unified_detection()
        
        detected = [r for r in detection_results.values() if r.detected]
        not_detected = [r for r in detection_results.values() if not r.detected]
        
        # Análise por método de detecção
        methods = {}
        for result in detected:
            method = result.detection_method
            if method not in methods:
                methods[method] = 0
            methods[method] += 1
        
        # Análise por confiança
        high_confidence = [r for r in detected if r.confidence >= 0.8]
        medium_confidence = [r for r in detected if 0.5 <= r.confidence < 0.8]
        low_confidence = [r for r in detected if r.confidence < 0.5]
        
        result = {
            'total_scanned': len(detection_results),
            'detected': len(detected),
            'not_detected': len(not_detected),
            'detection_rate': len(detected) / len(detection_results) * 100,
            'methods': methods,
            'confidence_distribution': {
                'high': len(high_confidence),
                'medium': len(medium_confidence),
                'low': len(low_confidence)
            },
            'detected_components': [
                {
                    'name': r.component,
                    'version': r.version,
                    'method': r.detection_method,
                    'confidence': r.confidence
                }
                for r in detected[:10]  # Top 10
            ]
        }
        
        logger.info(f"🔍 {result['detected']}/{result['total_scanned']} componentes detectados")
        logger.info(f"📈 Taxa de detecção: {result['detection_rate']:.1f}%")
        
        return result
    
    async def _validate_dependencies(self):
        """Valida dependências"""
        # Selecionar componentes com dependências
        components_with_deps = [
            name for name, comp in self.system.components.items() 
            if comp.dependencies
        ][:15]  # Primeiros 15
        
        if not components_with_deps:
            return {'message': 'Nenhum componente com dependências encontrado'}
        
        validation = await self.system.validate_dependencies(components_with_deps)
        
        result = {
            'components_analyzed': len(components_with_deps),
            'valid': validation['valid'],
            'missing_dependencies': len(validation['missing_dependencies']),
            'circular_dependencies': len(validation['circular_dependencies']),
            'installation_order': validation['installation_order'][:10]  # Primeiros 10
        }
        
        logger.info(f"🔗 {result['components_analyzed']} componentes analisados")
        logger.info(f"✅ Dependências válidas: {'Sim' if result['valid'] else 'Não'}")
        
        return result
    
    async def _analyze_storage(self):
        """Analisa requisitos de armazenamento"""
        # Estimativas de tamanho por categoria
        size_estimates = {
            'ide': 500, 'editor': 300, 'runtime': 200, 'ai tools': 2000,
            'game development': 1000, 'emulator': 100, 'graphics': 800
        }
        
        total_size = 0
        category_sizes = {}
        
        for comp in self.system.components.values():
            category_lower = comp.category.lower()
            estimated_size = 0
            
            for key, size in size_estimates.items():
                if key in category_lower:
                    estimated_size = size
                    break
            
            if estimated_size > 0:
                total_size += estimated_size
                if comp.category not in category_sizes:
                    category_sizes[comp.category] = 0
                category_sizes[comp.category] += estimated_size
        
        # Informações do disco atual
        disk_usage = psutil.disk_usage('.')
        
        result = {
            'estimated_total_mb': total_size,
            'estimated_total_gb': round(total_size / 1024, 2),
            'category_sizes': dict(sorted(category_sizes.items(), key=lambda x: x[1], reverse=True)),
            'disk_info': {
                'total_gb': round(disk_usage.total / (1024**3), 2),
                'used_gb': round(disk_usage.used / (1024**3), 2),
                'free_gb': round(disk_usage.free / (1024**3), 2),
                'usage_percent': round(disk_usage.used / disk_usage.total * 100, 1)
            }
        }
        
        logger.info(f"💾 Espaço estimado necessário: {result['estimated_total_gb']} GB")
        logger.info(f"💿 Espaço livre disponível: {result['disk_info']['free_gb']} GB")
        
        return result
    
    async def _check_steam_deck(self):
        """Verifica configurações Steam Deck"""
        steam_deck_components = [
            comp for comp in self.system.components.values()
            if 'steam deck' in comp.category.lower() or 'steamdeck' in comp.name.lower()
        ]
        
        result = {
            'steam_deck_detected': self.system.is_steam_deck,
            'steam_deck_components': len(steam_deck_components),
            'optimizations_active': self.system.is_steam_deck,
            'component_names': [comp.name for comp in steam_deck_components[:5]]
        }
        
        logger.info(f"🎮 Steam Deck detectado: {'Sim' if result['steam_deck_detected'] else 'Não'}")
        logger.info(f"🔧 Componentes específicos: {result['steam_deck_components']}")
        
        return result
    
    async def _continuous_monitoring(self):
        """Monitoramento contínuo da aplicação"""
        logger.info("\n🔄 Iniciando monitoramento contínuo...")
        logger.info("Pressione CTRL+C para finalizar a aplicação")
        
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                
                # Métricas do sistema
                metrics = self.monitor.get_summary()
                if metrics:
                    logger.info(f"📊 Ciclo {cycle_count} - CPU: {metrics['avg_cpu_usage']:.1f}% | "
                              f"RAM: {metrics['avg_memory_usage']:.1f}% | "
                              f"Runtime: {metrics['runtime_formatted']}")
                
                # Verificar componentes detectados periodicamente
                if cycle_count % 10 == 0:  # A cada 10 ciclos
                    logger.info("🔍 Executando verificação periódica...")
                    detected_count = len([r for r in self.system.detection_cache.values() if r.detected])
                    logger.info(f"📈 Componentes detectados: {detected_count}")
                
                # Aguardar próximo ciclo
                await asyncio.sleep(5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Erro no monitoramento contínuo: {e}")
                await asyncio.sleep(1)
    
    def _generate_final_report(self):
        """Gera relatório final da execução"""
        try:
            # Coletar métricas finais
            system_metrics = self.monitor.get_summary()
            system_report = self.system.generate_installation_report() if self.system else {}
            
            final_report = {
                'execution_timestamp': datetime.now().isoformat(),
                'system_metrics': system_metrics,
                'system_report': system_report,
                'operation_results': self.results,
                'performance_summary': {
                    'total_operations': len(self.results),
                    'successful_operations': len([r for r in self.results.values() if r.get('success', False)]),
                    'total_execution_time': sum(r.get('execution_time', 0) for r in self.results.values()),
                    'average_cpu_usage': system_metrics.get('avg_cpu_usage', 0),
                    'peak_memory_usage': system_metrics.get('max_memory_usage', 0)
                }
            }
            
            # Salvar relatório
            report_file = Path("reports") / f"application_execution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(final_report, f, indent=2, ensure_ascii=False)
            
            # Log do resumo
            logger.info("\n" + "="*80)
            logger.info("📊 RELATÓRIO FINAL DE EXECUÇÃO")
            logger.info("="*80)
            
            if system_metrics:
                logger.info(f"⏱️  Tempo de execução: {system_metrics['runtime_formatted']}")
                logger.info(f"🖥️  CPU média: {system_metrics['avg_cpu_usage']:.1f}%")
                logger.info(f"💾 RAM máxima: {system_metrics['max_memory_usage']:.1f}%")
            
            perf = final_report['performance_summary']
            logger.info(f"✅ Operações bem-sucedidas: {perf['successful_operations']}/{perf['total_operations']}")
            logger.info(f"⚡ Tempo total de operações: {perf['total_execution_time']:.2f}s")
            
            logger.info(f"📄 Relatório salvo em: {report_file}")
            logger.info("="*80)
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório final: {e}")


async def main():
    """Função principal"""
    try:
        launcher = ApplicationLauncher()
        await launcher.launch_application()
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Aplicação interrompida pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)