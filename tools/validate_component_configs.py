#!/usr/bin/env python3
"""
Script para validar configurações dos componentes YAML.

Este script:
1. Valida a estrutura dos arquivos YAML
2. Verifica campos obrigatórios
3. Testa a sintaxe e consistência
4. Valida URLs e hashes
5. Verifica dependências

Uso: python validate_component_configs.py [--fix-minor] [--component NOME]
"""

import os
import sys
import yaml
import json
import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse

# Adiciona o diretório raiz ao path para importar módulos do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

from env_dev.utils.log_manager import LogManager

class ComponentConfigValidator:
    def __init__(self, fix_minor: bool = False):
        self.fix_minor = fix_minor
        self.logger = LogManager().get_logger("ConfigValidator")
        
        # Caminhos
        self.project_root = Path(__file__).parent.parent
        self.components_dir = self.project_root / "env_dev" / "config" / "components"
        
        # Estatísticas
        self.total_components = 0
        self.valid_components = 0
        self.invalid_components = 0
        self.warnings = 0
        self.errors = 0
        self.fixed_issues = 0
        
        # Resultados detalhados
        self.validation_results = []
        
        # Schema de validação
        self.required_fields = {
            'download_url': str,
            'installation_method': str,
            'hash': str,
            'category': str
        }
        
        self.optional_fields = {
            'silent_args': str,
            'description': str,
            'dependencies': list,
            'post_install': list,
            'verification': dict,
            'version': str,
            'architecture': str,
            'supported_os': list,
            'file_size': int,
            'extract_to': str,
            'executable_path': str
        }
        
        self.valid_installation_methods = [
            'installer', 'msi', 'zip', 'portable', 'script', 'registry', 'manual'
        ]
        
        self.valid_categories = [
            'development', 'gaming', 'media', 'system', 'drivers', 'utilities',
            'security', 'network', 'productivity', 'graphics'
        ]
        
        self.verification_fields = {
            'registry_key': str,
            'file_path': str,
            'command_exists': str,
            'service_name': str,
            'process_name': str
        }
    
    def find_yaml_files(self) -> List[Path]:
        """Encontra todos os arquivos YAML na pasta de componentes"""
        if not self.components_dir.exists():
            self.logger.error(f"Diretório de componentes não encontrado: {self.components_dir}")
            return []
        
        return list(self.components_dir.glob("*.yaml"))
    
    def load_yaml_file(self, file_path: Path) -> Tuple[Optional[Dict], List[str]]:
        """Carrega um arquivo YAML e retorna dados e erros"""
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if data is None:
                errors.append("Arquivo YAML vazio")
                return None, errors
            
            if not isinstance(data, dict):
                errors.append("Arquivo YAML deve conter um dicionário")
                return None, errors
            
            return data, errors
            
        except yaml.YAMLError as e:
            errors.append(f"Erro de sintaxe YAML: {e}")
            return None, errors
        except Exception as e:
            errors.append(f"Erro ao carregar arquivo: {e}")
            return None, errors
    
    def validate_url(self, url: str) -> List[str]:
        """Valida uma URL"""
        errors = []
        
        if not url:
            errors.append("URL vazia")
            return errors
        
        if url == "HASH_PENDENTE_VERIFICACAO":
            errors.append("URL ainda não configurada (HASH_PENDENTE_VERIFICACAO)")
            return errors
        
        try:
            parsed = urlparse(url)
            if not parsed.scheme:
                errors.append("URL sem esquema (http/https)")
            if not parsed.netloc:
                errors.append("URL sem domínio")
            if parsed.scheme not in ['http', 'https', 'ftp']:
                errors.append(f"Esquema de URL não suportado: {parsed.scheme}")
        except Exception as e:
            errors.append(f"URL malformada: {e}")
        
        return errors
    
    def validate_hash(self, hash_value: str) -> List[str]:
        """Valida um hash"""
        errors = []
        
        if not hash_value:
            errors.append("Hash vazio")
            return errors
        
        if hash_value == "HASH_PENDENTE_VERIFICACAO":
            errors.append("Hash pendente de verificação")
            return errors
        
        # Valida formato SHA256 (64 caracteres hexadecimais)
        if not re.match(r'^[a-fA-F0-9]{64}$', hash_value):
            errors.append("Hash deve ser SHA256 (64 caracteres hexadecimais)")
        
        return errors
    
    def validate_verification(self, verification: Dict) -> List[str]:
        """Valida a seção de verificação"""
        errors = []
        warnings = []
        
        if not isinstance(verification, dict):
            errors.append("Verificação deve ser um dicionário")
            return errors
        
        # Verifica se pelo menos um método de verificação está presente
        verification_methods = ['registry_key', 'file_path', 'command_exists', 'service_name', 'process_name']
        has_verification = any(verification.get(method) for method in verification_methods)
        
        if not has_verification:
            warnings.append("Nenhum método de verificação configurado")
        
        # Valida tipos dos campos
        for field, expected_type in self.verification_fields.items():
            if field in verification:
                value = verification[field]
                if value and not isinstance(value, expected_type):
                    errors.append(f"Campo verification.{field} deve ser {expected_type.__name__}")
        
        return errors
    
    def validate_dependencies(self, dependencies: List, all_components: Dict) -> List[str]:
        """Valida dependências"""
        errors = []
        
        if not isinstance(dependencies, list):
            errors.append("Dependências devem ser uma lista")
            return errors
        
        for dep in dependencies:
            if not isinstance(dep, str):
                errors.append(f"Dependência deve ser string: {dep}")
                continue
            
            # Verifica se a dependência existe
            if dep not in all_components:
                errors.append(f"Dependência não encontrada: {dep}")
        
        return errors
    
    def validate_component(self, component_name: str, component_data: Dict, all_components: Dict) -> Dict:
        """Valida um componente específico"""
        result = {
            'component': component_name,
            'valid': True,
            'errors': [],
            'warnings': [],
            'fixes_applied': []
        }
        
        # Valida campos obrigatórios
        for field, expected_type in self.required_fields.items():
            if field not in component_data:
                result['errors'].append(f"Campo obrigatório ausente: {field}")
                result['valid'] = False
            else:
                value = component_data[field]
                if not isinstance(value, expected_type):
                    result['errors'].append(f"Campo {field} deve ser {expected_type.__name__}")
                    result['valid'] = False
        
        # Valida campos opcionais
        for field, expected_type in self.optional_fields.items():
            if field in component_data:
                value = component_data[field]
                if value is not None and not isinstance(value, expected_type):
                    result['errors'].append(f"Campo {field} deve ser {expected_type.__name__}")
                    result['valid'] = False
        
        # Validações específicas
        if 'download_url' in component_data:
            url_errors = self.validate_url(component_data['download_url'])
            result['errors'].extend(url_errors)
            if url_errors:
                result['valid'] = False
        
        if 'hash' in component_data:
            hash_errors = self.validate_hash(component_data['hash'])
            if hash_errors:
                result['warnings'].extend(hash_errors)
        
        if 'installation_method' in component_data:
            method = component_data['installation_method']
            if method not in self.valid_installation_methods:
                result['errors'].append(f"Método de instalação inválido: {method}")
                result['valid'] = False
        
        if 'category' in component_data:
            category = component_data['category']
            if category not in self.valid_categories:
                result['warnings'].append(f"Categoria não padrão: {category}")
        
        if 'verification' in component_data:
            verification_errors = self.validate_verification(component_data['verification'])
            result['errors'].extend(verification_errors)
            if verification_errors:
                result['valid'] = False
        
        if 'dependencies' in component_data:
            dep_errors = self.validate_dependencies(component_data['dependencies'], all_components)
            result['errors'].extend(dep_errors)
            if dep_errors:
                result['valid'] = False
        
        # Correções menores automáticas
        if self.fix_minor:
            # Adiciona campos padrão se ausentes
            if 'description' not in component_data:
                component_data['description'] = f"Componente {component_name}"
                result['fixes_applied'].append("Adicionada descrição padrão")
                self.fixed_issues += 1
            
            if 'dependencies' not in component_data:
                component_data['dependencies'] = []
                result['fixes_applied'].append("Adicionada lista de dependências vazia")
                self.fixed_issues += 1
            
            if 'post_install' not in component_data:
                component_data['post_install'] = []
                result['fixes_applied'].append("Adicionada lista de pós-instalação vazia")
                self.fixed_issues += 1
        
        return result
    
    def collect_all_components(self, yaml_files: List[Path]) -> Dict[str, Any]:
        """Coleta todos os componentes de todos os arquivos"""
        all_components = {}
        
        for file_path in yaml_files:
            data, errors = self.load_yaml_file(file_path)
            if data:
                all_components.update(data)
        
        return all_components
    
    def validate_file(self, file_path: Path, all_components: Dict) -> List[Dict]:
        """Valida um arquivo YAML específico"""
        results = []
        
        self.logger.info(f"Validando {file_path.name}...")
        
        data, file_errors = self.load_yaml_file(file_path)
        
        if file_errors:
            results.append({
                'file': str(file_path),
                'component': None,
                'valid': False,
                'errors': file_errors,
                'warnings': [],
                'fixes_applied': []
            })
            return results
        
        if not data:
            return results
        
        # Valida cada componente no arquivo
        for component_name, component_data in data.items():
            if not isinstance(component_data, dict):
                results.append({
                    'file': str(file_path),
                    'component': component_name,
                    'valid': False,
                    'errors': ["Dados do componente devem ser um dicionário"],
                    'warnings': [],
                    'fixes_applied': []
                })
                continue
            
            result = self.validate_component(component_name, component_data, all_components)
            result['file'] = str(file_path)
            results.append(result)
            
            self.total_components += 1
            if result['valid']:
                self.valid_components += 1
            else:
                self.invalid_components += 1
            
            self.errors += len(result['errors'])
            self.warnings += len(result['warnings'])
        
        # Salva arquivo se houve correções
        if self.fix_minor and any(r['fixes_applied'] for r in results if r['component']):
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
                self.logger.success(f"Correções aplicadas em {file_path.name}")
            except Exception as e:
                self.logger.error(f"Erro ao salvar correções em {file_path}: {e}")
        
        return results
    
    def validate_specific_component(self, component_name: str) -> bool:
        """Valida um componente específico"""
        yaml_files = self.find_yaml_files()
        all_components = self.collect_all_components(yaml_files)
        
        if component_name not in all_components:
            self.logger.error(f"Componente {component_name} não encontrado")
            return False
        
        # Encontra o arquivo que contém o componente
        for file_path in yaml_files:
            data, _ = self.load_yaml_file(file_path)
            if data and component_name in data:
                results = self.validate_file(file_path, all_components)
                
                # Filtra apenas o componente específico
                component_results = [r for r in results if r['component'] == component_name]
                self.validation_results.extend(component_results)
                
                return len(component_results) > 0 and component_results[0]['valid']
        
        return False
    
    def validate_all_components(self) -> bool:
        """Valida todos os componentes"""
        yaml_files = self.find_yaml_files()
        
        if not yaml_files:
            self.logger.error("Nenhum arquivo YAML encontrado")
            return False
        
        self.logger.info(f"Encontrados {len(yaml_files)} arquivos YAML")
        
        # Coleta todos os componentes primeiro (para validar dependências)
        all_components = self.collect_all_components(yaml_files)
        
        # Valida cada arquivo
        for file_path in yaml_files:
            results = self.validate_file(file_path, all_components)
            self.validation_results.extend(results)
        
        return self.invalid_components == 0
    
    def generate_report(self) -> str:
        """Gera um relatório detalhado da validação"""
        report = []
        report.append("=" * 80)
        report.append("RELATÓRIO DE VALIDAÇÃO DE CONFIGURAÇÕES")
        report.append("=" * 80)
        report.append(f"Total de componentes: {self.total_components}")
        report.append(f"Componentes válidos: {self.valid_components}")
        report.append(f"Componentes inválidos: {self.invalid_components}")
        report.append(f"Total de erros: {self.errors}")
        report.append(f"Total de avisos: {self.warnings}")
        
        if self.fix_minor:
            report.append(f"Correções aplicadas: {self.fixed_issues}")
        
        if self.total_components > 0:
            success_rate = (self.valid_components / self.total_components) * 100
            report.append(f"Taxa de sucesso: {success_rate:.1f}%")
        
        report.append("")
        
        # Detalhes dos problemas
        if self.validation_results:
            report.append("DETALHES DOS PROBLEMAS:")
            report.append("-" * 40)
            
            for result in self.validation_results:
                if result['errors'] or result['warnings']:
                    report.append(f"Arquivo: {Path(result['file']).name}")
                    if result['component']:
                        report.append(f"Componente: {result['component']}")
                    
                    if result['errors']:
                        report.append("Erros:")
                        for error in result['errors']:
                            report.append(f"  - {error}")
                    
                    if result['warnings']:
                        report.append("Avisos:")
                        for warning in result['warnings']:
                            report.append(f"  - {warning}")
                    
                    if result['fixes_applied']:
                        report.append("Correções aplicadas:")
                        for fix in result['fixes_applied']:
                            report.append(f"  - {fix}")
                    
                    report.append("")
        
        return "\n".join(report)
    
    def run(self, specific_component: Optional[str] = None) -> bool:
        """Executa a validação"""
        if self.fix_minor:
            self.logger.info("MODO CORREÇÃO ATIVO - Problemas menores serão corrigidos")
        
        if specific_component:
            self.logger.info(f"Validando componente específico: {specific_component}")
            success = self.validate_specific_component(specific_component)
        else:
            self.logger.info("Validando todos os componentes...")
            success = self.validate_all_components()
        
        # Gera e salva o relatório
        report = self.generate_report()
        
        report_file = self.project_root / "validation_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"Relatório salvo em: {report_file}")
        
        # Exibe resumo no console
        print("\n" + "=" * 50)
        print("RESUMO DA VALIDAÇÃO")
        print("=" * 50)
        print(f"Total: {self.total_components}")
        print(f"Válidos: {self.valid_components}")
        print(f"Inválidos: {self.invalid_components}")
        print(f"Erros: {self.errors}")
        print(f"Avisos: {self.warnings}")
        if self.fix_minor:
            print(f"Correções: {self.fixed_issues}")
        
        return success

def main():
    parser = argparse.ArgumentParser(description="Valida configurações dos componentes YAML")
    parser.add_argument('--fix-minor', action='store_true', help="Corrige problemas menores automaticamente")
    parser.add_argument('--component', type=str, help="Valida apenas um componente específico")
    
    args = parser.parse_args()
    
    validator = ComponentConfigValidator(fix_minor=args.fix_minor)
    success = validator.run(specific_component=args.component)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()