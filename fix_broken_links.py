#!/usr/bin/env python3
"""
Script para corrigir automaticamente os links quebrados encontrados na validação
"""

import yaml
from pathlib import Path
from typing import Dict, List

class LinkFixer:
    def __init__(self):
        self.fixes = {
            # AI Tools
            "LM Studio": "https://releases.lmstudio.ai/windows/x64/0.2.15/LM%20Studio-0.2.15-Setup.exe",
            
            # Backup & Sync
            "WinDirStat": "https://sourceforge.net/projects/windirstat/files/latest/download",
            
            # Common Utils
            "HardLinkShellExt_X64": "https://schinagl.priv.at/nt/hardlinkshellext/linkshellextension.html",
            
            # Editors
            "Cursor IDE": "https://download.cursor.sh/windows/nsis/x64",
            
            # Emulators
            "RetroArch (Windows)": "https://buildbot.libretro.com/stable/1.19.1/windows/x86_64/RetroArch.7z",
            "Mesen": "https://github.com/SourMesen/Mesen2/releases/latest/download/Mesen-Windows.zip",
            "mGBA": "https://github.com/mgba-emu/mgba/releases/latest/download/mGBA-0.11.1-win64.7z",
            "VBA-M (VisualBoyAdvance-M)": "https://github.com/visualboyadvance-m/visualboyadvance-m/releases/latest/download/visualboyadvance-m-Win-x64.zip",
            "PCSX2 (Windows)": "https://github.com/PCSX2/pcsx2/releases/latest/download/pcsx2-v2.0.2-windows-x64-Qt.7z",
            "RPCS3 (Windows)": "https://github.com/RPCS3/rpcs3-binaries-win/releases/latest/download/rpcs3-v0.0.32-16445-4d5ff071_win64.7z",
            "Citra (Windows)": "https://github.com/PabloMK7/citra/releases/latest/download/citra-windows-msvc.zip",
            "Yuzu (Windows)": "https://github.com/suyu-emu/suyu/releases/latest/download/suyu-windows-msvc.zip",
            
            # Game Launchers
            "GOG Galaxy": "https://webinstallers.gog-statics.com/download/GOG_Galaxy_2.0.exe",
            
            # Modding Tools
            "Vortex (Nexus Mods Manager)": "https://github.com/Nexus-Mods/Vortex/releases/latest/download/Vortex-1.11.4-installer.exe",
            
            # Optimization
            "MSI Afterburner": "https://download.msi.com/uti_exe/vga/MSIAfterburnerSetup.zip",
        }
        
        self.alternatives = {
            "LM Studio": ["https://lmstudio.ai/download"],
            "WinDirStat": ["https://github.com/shanselman/windirstat/releases/latest"],
            "Cursor IDE": ["https://cursor.sh/download"],
            "RetroArch (Windows)": ["https://www.retroarch.com/index.php?page=platforms"],
            "MSI Afterburner": ["https://www.guru3d.com/download/msi-afterburner-beta-download/"],
            "Citra (Windows)": ["https://github.com/PabloMK7/citra/releases/latest"],
            "Yuzu (Windows)": ["https://github.com/suyu-emu/suyu/releases/latest"],
        }
        
        self.notes = {
            "Citra (Windows)": "Projeto original descontinuado, usando fork do PabloMK7",
            "Yuzu (Windows)": "Projeto original descontinuado, usando fork Suyu",
            "HardLinkShellExt_X64": "Link redirecionado para página oficial",
        }
    
    def fix_yaml_file(self, file_path: Path) -> bool:
        """Corrige links em um arquivo YAML específico"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return False
            
            changes_made = False
            
            for component_name, component_data in data.items():
                if isinstance(component_data, dict) and component_name in self.fixes:
                    old_url = component_data.get('download_url', '')
                    new_url = self.fixes[component_name]
                    
                    if old_url != new_url:
                        print(f"  🔧 Corrigindo {component_name}")
                        print(f"     Antigo: {old_url}")
                        print(f"     Novo:   {new_url}")
                        
                        component_data['download_url'] = new_url
                        changes_made = True
                        
                        # Adicionar alternativas se disponíveis
                        if component_name in self.alternatives:
                            component_data['alternative_urls'] = self.alternatives[component_name]
                        
                        # Adicionar notas se disponíveis
                        if component_name in self.notes:
                            component_data['notes'] = self.notes[component_name]
                        
                        # Marcar hash para recálculo
                        if 'hash' in component_data:
                            component_data['hash'] = 'HASH_NEEDS_UPDATE'
            
            if changes_made:
                # Fazer backup do arquivo original
                backup_path = file_path.with_suffix('.yaml.backup')
                if not backup_path.exists():
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
                
                # Salvar arquivo corrigido
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
                
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Erro ao processar {file_path}: {e}")
            return False
    
    def fix_all_components(self) -> Dict[str, int]:
        """Corrige todos os arquivos de componentes"""
        components_dir = Path("env_dev/config/components")
        
        if not components_dir.exists():
            print("❌ Diretório de componentes não encontrado!")
            return {"error": 1}
        
        results = {"fixed": 0, "processed": 0, "errors": 0}
        
        print("🔧 Iniciando correção de links quebrados...")
        print("=" * 60)
        
        for yaml_file in components_dir.glob("*.yaml"):
            print(f"\n📁 Processando {yaml_file.name}...")
            results["processed"] += 1
            
            try:
                if self.fix_yaml_file(yaml_file):
                    results["fixed"] += 1
                    print(f"  ✅ {yaml_file.name} atualizado com sucesso")
                else:
                    print(f"  ℹ️ {yaml_file.name} não precisou de correções")
            except Exception as e:
                results["errors"] += 1
                print(f"  ❌ Erro em {yaml_file.name}: {e}")
        
        return results
    
    def generate_update_report(self, results: Dict[str, int]) -> str:
        """Gera relatório das correções aplicadas"""
        report = []
        report.append("# 🔧 RELATÓRIO DE CORREÇÕES APLICADAS")
        report.append("=" * 50)
        report.append("")
        
        report.append("## 📊 Resumo")
        report.append(f"- Arquivos processados: {results['processed']}")
        report.append(f"- Arquivos corrigidos: {results['fixed']}")
        report.append(f"- Erros encontrados: {results['errors']}")
        report.append("")
        
        report.append("## 🔧 Correções Aplicadas")
        for component, new_url in self.fixes.items():
            report.append(f"### {component}")
            report.append(f"- **Nova URL**: {new_url}")
            
            if component in self.alternatives:
                report.append("- **Alternativas**:")
                for alt in self.alternatives[component]:
                    report.append(f"  - {alt}")
            
            if component in self.notes:
                report.append(f"- **Nota**: {self.notes[component]}")
            
            report.append("")
        
        report.append("## ⚠️ Ações Necessárias")
        report.append("1. **Recalcular hashes** dos arquivos atualizados")
        report.append("2. **Testar downloads** para verificar funcionamento")
        report.append("3. **Atualizar documentação** se necessário")
        report.append("4. **Executar nova validação** para confirmar correções")
        
        return "\n".join(report)

def main():
    fixer = LinkFixer()
    
    # Aplicar correções
    results = fixer.fix_all_components()
    
    if "error" in results:
        return 1
    
    # Gerar relatório
    report = fixer.generate_update_report(results)
    
    # Salvar relatório
    with open("link_fixes_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("\n" + "=" * 60)
    print("📊 RESUMO FINAL:")
    print(f"  📁 Arquivos processados: {results['processed']}")
    print(f"  🔧 Arquivos corrigidos: {results['fixed']}")
    print(f"  ❌ Erros encontrados: {results['errors']}")
    print(f"  📄 Relatório salvo em: link_fixes_report.md")
    
    if results['fixed'] > 0:
        print("\n✅ Correções aplicadas com sucesso!")
        print("🔄 Execute 'python validate_repositories.py' para validar as correções")
    else:
        print("\nℹ️ Nenhuma correção foi necessária")
    
    return 0

if __name__ == "__main__":
    exit(main())