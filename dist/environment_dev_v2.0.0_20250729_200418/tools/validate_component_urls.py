#!/usr/bin/env python3
"""
Script para validar e corrigir URLs de download nos componentes.

Este script:
1. Verifica todas as URLs de download nos arquivos YAML
2. Testa a acessibilidade das URLs
3. Sugere URLs alternativas quando possível
4. Gera relatório de URLs problemáticas

Uso: python validate_component_urls.py [--fix] [--timeout 30]
"""

import os
import sys
import yaml
import requests
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse
import time

# Adiciona o diretório raiz ao path para importar módulos do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

from env_dev.utils.log_manager import LogManager
from env_dev.utils.network import NetworkUtils

class URLValidator:
    def __init__(self, fix_mode: bool = False, timeout: int = 30):
        self.fix_mode = fix_mode
        self.timeout = timeout
        self.logger = LogManager().get_logger("URLValidator")
        self.network_utils = NetworkUtils()
        self.components_dir = Path(__file__).parent.parent / "env_dev" / "config" / "components"
        
        # Estatísticas
        self.total_urls = 0
        self.valid_urls = 0
        self.invalid_urls = 0
        self.fixed_urls = 0
        
        # URLs problemáticas
        self.problematic_urls = []
        
        # Mapeamento de URLs conhecidas para correção
        self.url_fixes = {
            # Exemplos de correções conhecidas
            "https://github.com/microsoft/vcpkg/archive/master.zip": "https://github.com/microsoft/vcpkg/archive/refs/heads/master.zip",
            # Adicione mais correções conforme necessário
        }
        
        # Padrões de URL para sugestões automáticas
        self.url_patterns = {
            "github_releases": "https://api.github.com/repos/{owner}/{repo}/releases/latest",
            "github_archive": "https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
        }
    
    def find_yaml_files(self) -> List[Path]:
        """Encontra todos os arquivos YAML na pasta de componentes"""
        return list(self.components_dir.glob("*.yaml"))
    
    def extract_urls_from_file(self, file_path: Path) -> List[Tuple[str, str, str]]:
        """Extrai todas as URLs de download de um arquivo YAML"""
        urls = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if data:
                for component_name, component_data in data.items():
                    if isinstance(component_data, dict):
                        download_url = component_data.get('download_url')
                        if download_url and download_url != 'HASH_PENDENTE_VERIFICACAO':
                            urls.append((str(file_path), component_name, download_url))
            
        except Exception as e:
            self.logger.error(f"Erro ao processar {file_path}: {e}")
        
        return urls
    
    def validate_url(self, url: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Valida uma URL e retorna status, erro e sugestão de correção"""
        try:
            # Verifica se a URL está na lista de correções conhecidas
            if url in self.url_fixes:
                suggested_url = self.url_fixes[url]
                self.logger.info(f"URL conhecida com problema, sugerindo: {suggested_url}")
                return False, "URL conhecida como problemática", suggested_url
            
            # Faz uma requisição HEAD para verificar se a URL existe
            response = requests.head(url, timeout=self.timeout, allow_redirects=True)
            
            if response.status_code == 200:
                return True, None, None
            elif response.status_code == 404:
                # Tenta sugerir uma URL alternativa
                suggestion = self.suggest_alternative_url(url)
                return False, f"HTTP {response.status_code} - Não encontrado", suggestion
            else:
                return False, f"HTTP {response.status_code}", None
                
        except requests.exceptions.Timeout:
            return False, "Timeout na conexão", None
        except requests.exceptions.ConnectionError:
            return False, "Erro de conexão", None
        except requests.exceptions.RequestException as e:
            return False, f"Erro na requisição: {str(e)}", None
        except Exception as e:
            return False, f"Erro inesperado: {str(e)}", None
    
    def suggest_alternative_url(self, url: str) -> Optional[str]:
        """Sugere uma URL alternativa baseada em padrões conhecidos"""
        try:
            parsed = urlparse(url)
            
            # Para URLs do GitHub
            if 'github.com' in parsed.netloc:
                path_parts = parsed.path.strip('/').split('/')
                if len(path_parts) >= 2:
                    owner, repo = path_parts[0], path_parts[1]
                    
                    # Se for um link de release, tenta a API para pegar o latest
                    if 'releases/download' in parsed.path:
                        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
                        try:
                            response = requests.get(api_url, timeout=10)
                            if response.status_code == 200:
                                latest_release = response.json()
                                assets = latest_release.get('assets', [])
                                if assets:
                                    # Retorna o primeiro asset (pode ser melhorado)
                                    return assets[0]['browser_download_url']
                        except:
                            pass
                    
                    # Se for um arquivo de archive, tenta o formato correto
                    elif 'archive' in parsed.path:
                        return f"https://github.com/{owner}/{repo}/archive/refs/heads/master.zip"
            
            return None
            
        except Exception:
            return None
    
    def update_url_in_file(self, file_path: str, component_name: str, old_url: str, new_url: str) -> bool:
        """Atualiza uma URL em um arquivo YAML"""
        try:
            if not self.fix_mode:
                self.logger.info(f"[DRY RUN] Atualizaria {component_name} em {file_path}")
                return True
            
            # Carrega o arquivo
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Atualiza a URL
            if data and component_name in data:
                if isinstance(data[component_name], dict):
                    data[component_name]['download_url'] = new_url
                    
                    # Backup do arquivo original
                    backup_path = Path(file_path).with_suffix('.yaml.backup')
                    if not backup_path.exists():
                        import shutil
                        shutil.copy2(file_path, backup_path)
                    
                    # Salva o arquivo atualizado
                    with open(file_path, 'w', encoding='utf-8') as f:
                        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
                    
                    self.logger.success(f"URL atualizada para {component_name}: {new_url}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar URL em {file_path}: {e}")
            return False
    
    def validate_all_urls(self) -> Dict:
        """Valida todas as URLs encontradas nos arquivos YAML"""
        self.logger.info("Iniciando validação de URLs...")
        
        yaml_files = self.find_yaml_files()
        all_urls = []
        
        # Coleta todas as URLs
        for file_path in yaml_files:
            urls = self.extract_urls_from_file(file_path)
            all_urls.extend(urls)
        
        self.total_urls = len(all_urls)
        self.logger.info(f"Encontradas {self.total_urls} URLs para validar")
        
        results = {
            'valid': [],
            'invalid': [],
            'fixed': []
        }
        
        # Valida cada URL
        for i, (file_path, component_name, url) in enumerate(all_urls, 1):
            self.logger.info(f"[{i}/{self.total_urls}] Validando {component_name}: {url}")
            
            is_valid, error, suggestion = self.validate_url(url)
            
            if is_valid:
                self.valid_urls += 1
                results['valid'].append({
                    'file': file_path,
                    'component': component_name,
                    'url': url
                })
                self.logger.success(f"✅ {component_name}: URL válida")
            else:
                self.invalid_urls += 1
                problem_info = {
                    'file': file_path,
                    'component': component_name,
                    'url': url,
                    'error': error,
                    'suggestion': suggestion
                }
                
                results['invalid'].append(problem_info)
                self.problematic_urls.append(problem_info)
                
                self.logger.error(f"❌ {component_name}: {error}")
                
                # Tenta corrigir se há sugestão e modo fix está ativo
                if suggestion and self.fix_mode:
                    self.logger.info(f"Tentando corrigir com: {suggestion}")
                    
                    # Valida a URL sugerida primeiro
                    is_suggestion_valid, _, _ = self.validate_url(suggestion)
                    if is_suggestion_valid:
                        if self.update_url_in_file(file_path, component_name, url, suggestion):
                            self.fixed_urls += 1
                            results['fixed'].append({
                                'file': file_path,
                                'component': component_name,
                                'old_url': url,
                                'new_url': suggestion
                            })
                            self.logger.success(f"🔧 {component_name}: URL corrigida!")
                        else:
                            self.logger.error(f"Falha ao atualizar arquivo para {component_name}")
                    else:
                        self.logger.warning(f"URL sugerida também é inválida: {suggestion}")
                elif suggestion:
                    self.logger.info(f"💡 Sugestão: {suggestion}")
            
            # Pequena pausa para não sobrecarregar os servidores
            time.sleep(0.5)
        
        return results
    
    def generate_report(self, results: Dict) -> str:
        """Gera um relatório detalhado dos resultados"""
        report = []
        report.append("=" * 80)
        report.append("RELATÓRIO DE VALIDAÇÃO DE URLs")
        report.append("=" * 80)
        report.append(f"Total de URLs verificadas: {self.total_urls}")
        report.append(f"URLs válidas: {self.valid_urls} ({self.valid_urls/self.total_urls*100:.1f}%)")
        report.append(f"URLs inválidas: {self.invalid_urls} ({self.invalid_urls/self.total_urls*100:.1f}%)")
        
        if self.fix_mode:
            report.append(f"URLs corrigidas: {self.fixed_urls}")
        
        report.append("")
        
        if results['invalid']:
            report.append("URLs PROBLEMÁTICAS:")
            report.append("-" * 40)
            for item in results['invalid']:
                report.append(f"Componente: {item['component']}")
                report.append(f"Arquivo: {item['file']}")
                report.append(f"URL: {item['url']}")
                report.append(f"Erro: {item['error']}")
                if item['suggestion']:
                    report.append(f"Sugestão: {item['suggestion']}")
                report.append("")
        
        if results['fixed']:
            report.append("URLs CORRIGIDAS:")
            report.append("-" * 40)
            for item in results['fixed']:
                report.append(f"Componente: {item['component']}")
                report.append(f"Arquivo: {item['file']}")
                report.append(f"URL antiga: {item['old_url']}")
                report.append(f"URL nova: {item['new_url']}")
                report.append("")
        
        return "\n".join(report)
    
    def run(self) -> bool:
        """Executa a validação completa"""
        if self.fix_mode:
            self.logger.info("MODO CORREÇÃO ATIVO - URLs serão corrigidas quando possível")
        else:
            self.logger.info("MODO VALIDAÇÃO - Apenas verificando URLs")
        
        results = self.validate_all_urls()
        
        # Gera e salva o relatório
        report = self.generate_report(results)
        
        report_file = Path(__file__).parent.parent / "url_validation_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"Relatório salvo em: {report_file}")
        
        # Exibe resumo no console
        print("\n" + "=" * 50)
        print("RESUMO DA VALIDAÇÃO")
        print("=" * 50)
        print(f"Total de URLs: {self.total_urls}")
        print(f"URLs válidas: {self.valid_urls}")
        print(f"URLs inválidas: {self.invalid_urls}")
        if self.fix_mode:
            print(f"URLs corrigidas: {self.fixed_urls}")
        
        return self.invalid_urls == 0

def main():
    parser = argparse.ArgumentParser(description="Valida URLs de download nos componentes")
    parser.add_argument('--fix', action='store_true', help="Tenta corrigir URLs problemáticas automaticamente")
    parser.add_argument('--timeout', type=int, default=30, help="Timeout para requisições HTTP (segundos)")
    
    args = parser.parse_args()
    
    validator = URLValidator(fix_mode=args.fix, timeout=args.timeout)
    success = validator.run()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()