#!/usr/bin/env python3
"""
Script para validar todos os repositórios e URLs de download do projeto
"""

import requests
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any
import time

class RepositoryValidator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.results = {}
        
    def validate_url(self, url: str, timeout: int = 10) -> Dict[str, Any]:
        """Valida uma URL específica"""
        try:
            response = self.session.head(url, timeout=timeout, allow_redirects=True)
            return {
                'status': 'valid',
                'status_code': response.status_code,
                'final_url': response.url,
                'content_type': response.headers.get('content-type', ''),
                'content_length': response.headers.get('content-length', 'unknown')
            }
        except requests.exceptions.RequestException as e:
            return {
                'status': 'invalid',
                'error': str(e),
                'status_code': None
            }
    
    def get_github_alternatives(self, repo_url: str) -> List[str]:
        """Gera URLs alternativas para repositórios GitHub"""
        alternatives = []
        
        if 'github.com' in repo_url:
            # Extrair owner/repo
            parts = repo_url.split('/')
            if len(parts) >= 5:
                owner = parts[3]
                repo = parts[4]
                
                # Mirrors alternativos
                alternatives.extend([
                    f"https://gitee.com/{owner}/{repo}",  # Gitee mirror
                    f"https://gitlab.com/{owner}/{repo}",  # GitLab mirror
                    f"https://codeberg.org/{owner}/{repo}",  # Codeberg
                    f"https://git.sr.ht/~{owner}/{repo}",  # SourceHut
                ])
                
                # Releases alternativas
                if '/releases/' in repo_url:
                    alternatives.extend([
                        f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip",
                        f"https://github.com/{owner}/{repo}/archive/refs/heads/master.zip",
                    ])
        
        return alternatives
    
    def validate_retro_devkits(self) -> Dict[str, Any]:
        """Valida URLs dos devkits retro"""
        print("🎮 Validando DevKits Retro...")
        
        devkits = {
            # 8-bit Home Consoles
            "nes": {
                "name": "NES Development Kit (CC65)",
                "primary_url": "https://github.com/cc65/cc65/releases/latest",
                "alternatives": [
                    "https://cc65.github.io/",
                    "https://github.com/cc65/cc65/archive/refs/heads/master.zip"
                ]
            },
            "atari2600": {
                "name": "Atari 2600 Development Kit",
                "primary_url": "https://github.com/stella-emu/stella/releases/latest",
                "alternatives": [
                    "https://stella-emu.github.io/",
                    "https://sourceforge.net/projects/stella/"
                ]
            },
            "mastersystem": {
                "name": "Master System Development Kit (DevKitSMS)",
                "primary_url": "https://github.com/sverx/devkitSMS/releases/latest",
                "alternatives": [
                    "https://github.com/sverx/devkitSMS/archive/refs/heads/master.zip"
                ]
            },
            
            # 8-bit Portable Consoles
            "gameboy": {
                "name": "Game Boy Development Kit (GBDK-2020)",
                "primary_url": "https://github.com/gbdk-2020/gbdk-2020/releases/latest",
                "alternatives": [
                    "https://gbdk-2020.github.io/gbdk-2020/",
                    "https://github.com/gbdk-2020/gbdk-2020/archive/refs/heads/develop.zip"
                ]
            },
            "neogeopocket": {
                "name": "Neo Geo Pocket Development Kit",
                "primary_url": "https://github.com/sodthor/ngpcdev/releases/latest",
                "alternatives": [
                    "https://github.com/sodthor/ngpcdev/archive/refs/heads/master.zip"
                ]
            },
            "wonderswan": {
                "name": "WonderSwan Development Kit",
                "primary_url": "https://github.com/WonderfulToolchain/wonderful-i8086/releases/latest",
                "alternatives": [
                    "https://wonderful.asie.pl/",
                    "https://github.com/WonderfulToolchain/wonderful-i8086/archive/refs/heads/main.zip"
                ]
            },
            
            # 16-bit Home Consoles
            "snes": {
                "name": "Super Nintendo Development Kit (libSFX)",
                "primary_url": "https://github.com/Optiroc/libSFX/releases/latest",
                "alternatives": [
                    "https://github.com/Optiroc/libSFX/archive/refs/heads/master.zip"
                ]
            },
            "megadrive": {
                "name": "Sega Mega Drive Development Kit (SGDK)",
                "primary_url": "https://github.com/Stephane-D/SGDK/releases/latest",
                "alternatives": [
                    "https://github.com/Stephane-D/SGDK/archive/refs/heads/master.zip",
                    "https://sgdk.readthedocs.io/"
                ]
            },
            "neogeo": {
                "name": "Neo Geo Development Kit (NGDevKit)",
                "primary_url": "https://github.com/dciabrin/ngdevkit/releases/latest",
                "alternatives": [
                    "https://github.com/dciabrin/ngdevkit/archive/refs/heads/master.zip"
                ]
            },
            
            # 16-bit Portable Consoles
            "atarilynx": {
                "name": "Atari Lynx Development Kit",
                "primary_url": "https://github.com/cc65/cc65/releases/latest",
                "alternatives": [
                    "https://cc65.github.io/",
                    "https://github.com/42Bastian/new_bll"
                ]
            },
            "pcengine": {
                "name": "PC-Engine Development Kit (HuC)",
                "primary_url": "https://github.com/uli/huc/releases/latest",
                "alternatives": [
                    "https://github.com/uli/huc/archive/refs/heads/master.zip"
                ]
            },
            
            # 32-bit Home Consoles
            "playstation1": {
                "name": "PlayStation 1 Development Kit (PSn00bSDK)",
                "primary_url": "https://github.com/Lameguy64/PSn00bSDK/releases/latest",
                "alternatives": [
                    "https://github.com/Lameguy64/PSn00bSDK/archive/refs/heads/master.zip",
                    "https://lameguy64.github.io/PSn00bSDK/"
                ]
            },
            "saturn": {
                "name": "Sega Saturn Development Kit (Jo-Engine + Yaul)",
                "primary_url": "https://github.com/johannes-fetz/joengine/releases/latest",
                "alternatives": [
                    "https://github.com/yaul-org/yaul/releases/latest",
                    "https://jo-engine.org/",
                    "https://yaul.org/"
                ]
            },
            "nintendo64": {
                "name": "Nintendo 64 Development Kit (libdragon)",
                "primary_url": "https://github.com/DragonMinded/libdragon/releases/latest",
                "alternatives": [
                    "https://libdragon.dev/",
                    "https://github.com/DragonMinded/libdragon/archive/refs/heads/trunk.zip"
                ]
            },
            
            # 32-bit Portable Consoles
            "psp": {
                "name": "PlayStation Portable Development Kit (PSPSDK)",
                "primary_url": "https://github.com/pspdev/psptoolchain/releases/latest",
                "alternatives": [
                    "https://github.com/pspdev/pspdev/releases/latest",
                    "https://pspdev.github.io/"
                ]
            },
            "nds": {
                "name": "Nintendo DS Development Kit (devkitARM)",
                "primary_url": "https://github.com/devkitPro/installer/releases/latest",
                "alternatives": [
                    "https://devkitpro.org/wiki/Getting_Started",
                    "https://github.com/devkitPro/pacman/releases/latest"
                ]
            },
            "gba": {
                "name": "Game Boy Advance Development Kit (devkitARM)",
                "primary_url": "https://github.com/devkitPro/installer/releases/latest",
                "alternatives": [
                    "https://devkitpro.org/wiki/Getting_Started",
                    "https://github.com/devkitPro/pacman/releases/latest"
                ]
            }
        }
        
        results = {}
        for devkit_id, info in devkits.items():
            print(f"  Validando {info['name']}...")
            
            # Validar URL principal
            primary_result = self.validate_url(info['primary_url'])
            
            # Validar alternativas
            alt_results = []
            for alt_url in info['alternatives']:
                alt_result = self.validate_url(alt_url)
                alt_results.append({
                    'url': alt_url,
                    'result': alt_result
                })
                time.sleep(0.5)  # Rate limiting
            
            results[devkit_id] = {
                'name': info['name'],
                'primary_url': info['primary_url'],
                'primary_result': primary_result,
                'alternatives': alt_results
            }
            
            time.sleep(1)  # Rate limiting
        
        return results
    
    def validate_component_files(self) -> Dict[str, Any]:
        """Valida URLs dos arquivos de componentes"""
        print("📦 Validando Componentes do Sistema...")
        
        components_dir = Path("env_dev/config/components")
        results = {}
        
        if not components_dir.exists():
            return {"error": "Diretório de componentes não encontrado"}
        
        for yaml_file in components_dir.glob("*.yaml"):
            print(f"  Processando {yaml_file.name}...")
            
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                file_results = {}
                
                for component_name, component_data in data.items():
                    if isinstance(component_data, dict) and 'download_url' in component_data:
                        url = component_data['download_url']
                        
                        # Pular URLs que não são links diretos
                        if url.startswith('http'):
                            result = self.validate_url(url)
                            file_results[component_name] = {
                                'url': url,
                                'result': result,
                                'category': component_data.get('category', 'Unknown'),
                                'description': component_data.get('description', '')
                            }
                            time.sleep(0.5)
                
                results[yaml_file.stem] = file_results
                
            except Exception as e:
                results[yaml_file.stem] = {"error": str(e)}
        
        return results
    
    def generate_report(self, retro_results: Dict, component_results: Dict) -> str:
        """Gera relatório completo"""
        report = []
        report.append("# 📋 RELATÓRIO COMPLETO DE VALIDAÇÃO DE REPOSITÓRIOS")
        report.append("=" * 80)
        report.append("")
        
        # Resumo Executivo
        total_retro = len(retro_results)
        valid_retro = sum(1 for r in retro_results.values() 
                         if r.get('primary_result', {}).get('status') == 'valid')
        
        total_components = sum(len(comps) for comps in component_results.values() 
                              if isinstance(comps, dict) and 'error' not in comps)
        valid_components = sum(
            sum(1 for comp in comps.values() 
                if isinstance(comp, dict) and comp.get('result', {}).get('status') == 'valid')
            for comps in component_results.values() 
            if isinstance(comps, dict) and 'error' not in comps
        )
        
        report.append("## 📊 RESUMO EXECUTIVO")
        report.append(f"- **DevKits Retro**: {valid_retro}/{total_retro} válidos ({valid_retro/total_retro*100:.1f}%)")
        report.append(f"- **Componentes Sistema**: {valid_components}/{total_components} válidos ({valid_components/total_components*100:.1f}%)")
        report.append("")
        
        # DevKits Retro
        report.append("## 🎮 DEVKITS RETRO")
        report.append("")
        
        for devkit_id, info in retro_results.items():
            status = "✅" if info['primary_result']['status'] == 'valid' else "❌"
            report.append(f"### {status} {info['name']} (`{devkit_id}`)")
            report.append(f"**URL Principal**: {info['primary_url']}")
            
            if info['primary_result']['status'] == 'valid':
                report.append(f"- Status: {info['primary_result']['status_code']}")
                if info['primary_result'].get('final_url') != info['primary_url']:
                    report.append(f"- Redirecionado para: {info['primary_result']['final_url']}")
            else:
                report.append(f"- ❌ Erro: {info['primary_result'].get('error', 'Unknown')}")
            
            # Alternativas válidas
            valid_alts = [alt for alt in info['alternatives'] 
                         if alt['result']['status'] == 'valid']
            if valid_alts:
                report.append("**Alternativas Válidas**:")
                for alt in valid_alts:
                    report.append(f"- {alt['url']}")
            
            report.append("")
        
        # Componentes do Sistema
        report.append("## 📦 COMPONENTES DO SISTEMA")
        report.append("")
        
        for file_name, components in component_results.items():
            if isinstance(components, dict) and 'error' not in components:
                report.append(f"### 📁 {file_name.replace('_', ' ').title()}")
                
                for comp_name, comp_info in components.items():
                    status = "✅" if comp_info['result']['status'] == 'valid' else "❌"
                    report.append(f"**{status} {comp_name}**")
                    report.append(f"- Categoria: {comp_info['category']}")
                    report.append(f"- URL: {comp_info['url']}")
                    
                    if comp_info['result']['status'] == 'valid':
                        report.append(f"- Status: {comp_info['result']['status_code']}")
                    else:
                        report.append(f"- ❌ Erro: {comp_info['result'].get('error', 'Unknown')}")
                    
                    report.append("")
        
        return "\n".join(report)

def main():
    print("🔍 Iniciando validação completa de repositórios...")
    
    validator = RepositoryValidator()
    
    # Validar DevKits Retro
    retro_results = validator.validate_retro_devkits()
    
    # Validar Componentes do Sistema
    component_results = validator.validate_component_files()
    
    # Gerar relatório
    report = validator.generate_report(retro_results, component_results)
    
    # Salvar relatório
    with open("repository_validation_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    # Salvar dados JSON para processamento posterior
    with open("repository_validation_data.json", "w", encoding="utf-8") as f:
        json.dump({
            'retro_devkits': retro_results,
            'system_components': component_results
        }, f, indent=2, ensure_ascii=False)
    
    print("✅ Validação concluída!")
    print("📄 Relatório salvo em: repository_validation_report.md")
    print("📊 Dados JSON salvos em: repository_validation_data.json")

if __name__ == "__main__":
    main()