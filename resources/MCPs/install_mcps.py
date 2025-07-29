import os
import subprocess
import sys
import json
import glob
from pathlib import Path

# Configuração embutida
MCP_CONFIG = {
    "base_path": "C:/MCPs Servers",
    "mcp_settings_path": "C:/MCPs Servers/mcp-settings.json",
    "mcps": [
        {"name": "Figma-Context-MCP", "type": "Node"},
        {"name": "magic-mcp", "type": "Node"},
        {"name": "markdownify-mcp", "type": "Node"},
        {"name": "mcp-playwright", "type": "Node"},
        {"name": "mcp-server-neon", "type": "Node"},
        {"name": "mcp-youtube", "type": "Node"},
        {"name": "memory-mcp", "type": "Node"},
        {"name": "slack-mcp", "type": "Node"},
        {"name": "Software-planning-mcp", "type": "Node"},
        {"name": "codegen-mcp-server", "type": "Python"},
        {"name": "sqlite-mcp", "type": "Python"},
        {"name": "supabase-mcp-server", "type": "Python"},
        # Novos MCPs adicionados
        {"name": "github-mcp", "type": "Node"},
        {"name": "sequential-thinking-mcp", "type": "Node"},
        {"name": "gemini-thinking-mcp", "type": "Node"},
        {"name": "puppeteer-mcp", "type": "Node"},
        {"name": "desktop-commander-mcp", "type": "Python"},
        {"name": "browser-tools-mcp", "type": "Node"} # Nome do diretório conforme info
    ]
}

def install_python_deps():
    """Instala dependências Python necessárias"""
    required = {'pyyaml', 'setuptools'}
    try:
        import yaml
        import setuptools
    except ImportError:
        print("Instalando dependências Python...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', *required], check=True)

def run_command(command_args, cwd):
    """Executa comando com tratamento robusto"""
    try:
        result = subprocess.run(
            command_args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            shell=True,
            timeout=300
        )
        return (result.returncode == 0, result.stdout.strip())
    except Exception as e:
        return (False, str(e))

def find_npm():
    """Encontra o caminho do npm"""
    paths = [
        os.path.join(os.environ.get('ProgramFiles', ''), 'nodejs', 'npm.cmd'),
        os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'nodejs', 'npm.cmd'),
        os.path.join(os.environ.get('LocalAppData', ''), 'Programs', 'nodejs', 'npm.cmd'),
        'npm'  # Fallback
    ]
    for path in paths:
        if path == 'npm' or os.path.exists(path):
            return path
    return 'npm'

def install_node_mcp(mcp_path, mcp_name):
    """Instala MCP Node.js"""
    package_json = os.path.join(mcp_path, 'package.json')
    if not os.path.exists(package_json):
        raise FileNotFoundError(f"package.json não encontrado em {mcp_path}")

    npm_path = find_npm()
    print(f"Instalando {mcp_name}...")

    success, output = run_command([npm_path, 'install'], mcp_path)
    if not success:
        raise RuntimeError(f"Falha na instalação: {output}")

    with open(package_json, 'r') as f:
        pkg = json.load(f)
        if 'scripts' in pkg and 'build' in pkg['scripts']:
            print(f"Construindo {mcp_name}...")
            success, output = run_command([npm_path, 'run', 'build'], mcp_path)
            if not success:
                raise RuntimeError(f"Falha no build: {output}")

def install_python_mcp(mcp_path, mcp_name):
    """Instala MCP Python"""
    req_files = [
        os.path.join(mcp_path, 'requirements.txt'),
        os.path.join(mcp_path, 'pyproject.toml')
    ]

    if not any(os.path.exists(f) for f in req_files):
        raise FileNotFoundError(f"Nenhum arquivo de requisitos encontrado em {mcp_path}")

    venv_path = os.path.join(mcp_path, '.venv')
    python_exec = os.path.join(venv_path, 'Scripts', 'python') if os.name == 'nt' else os.path.join(venv_path, 'bin', 'python')

    if not os.path.exists(venv_path):
        print(f"Criando venv para {mcp_name}...")
        success, output = run_command([sys.executable, '-m', 'venv', venv_path], mcp_path)
        if not success:
            raise RuntimeError(f"Falha ao criar venv: {output}")

    print(f"Verificando pip em {mcp_name}...")
    success, output = run_command([python_exec, '-m', 'pip', '--version'], mcp_path)
    if not success:
        print(f"Instalando pip em {mcp_name}...")
        success, output = run_command([python_exec, '-m', 'ensurepip', '--upgrade'], mcp_path)
        if not success:
            raise RuntimeError(f"Falha ao instalar pip: {output}")

    print(f"Instalando {mcp_name}...")
    if os.path.exists(req_files[1]):  # pyproject.toml
        cmd = [python_exec, '-m', 'pip', 'install', '-e', '.']
    else:  # requirements.txt
        cmd = [python_exec, '-m', 'pip', 'install', '-r', 'requirements.txt']

    success, output = run_command(cmd, mcp_path)
    if not success:
        raise RuntimeError(f"Falha na instalação: {output}")

def generate_fallback(mcp_path, mcp_name, mcp_type, error_message):
    """Gera servidor fallback"""
    try:
        os.makedirs(mcp_path, exist_ok=True)
        ext = 'py' if mcp_type == 'Python' else 'cjs'
        fallback_file = os.path.join(mcp_path, f'fallback_server.{ext}')

        if mcp_type == 'Python':
            content = f'''import http.server
import socketserver
import json
import os

PORT = int(os.environ.get('PORT', 3000))

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({{
            'message': 'Fallback para {mcp_name}. Erro: {error_message.replace("'", "\\'")}',
            'status': 'fallback_active'
        }}).encode('utf-8'))

print(f"Fallback para {mcp_name} rodando na porta {{PORT}}")
socketserver.TCPServer(("", PORT), Handler).serve_forever()
'''
        else:
            content = f'''const http = require('http')
const port = process.env.PORT || 3000

http.createServer((req, res) => {{
    res.writeHead(200, {{ 'Content-Type': 'application/json' }})
    res.end(JSON.stringify({{
        message: 'Fallback para {mcp_name}. Erro: {error_message.replace("'", "\\'")}',
        status: 'fallback_active'
    }}))
}}).listen(port, () => console.log(`Fallback para {mcp_name} rodando na porta ${{port}}`))
'''

        with open(fallback_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return True
    except Exception as e:
        print(f"[ERRO] Falha ao gerar fallback: {str(e)}")
        return False

def update_roo_code_rules(report):
    """Gera e salva o arquivo de regras para as instalações do VS Code"""

    # Filtra MCPs que foram instalados com sucesso
    successful_mcps = [mcp for mcp in report if mcp['status'] == 'Success']

    if not successful_mcps:
        print("[AVISO] Nenhum MCP instalado com sucesso. Arquivo de regras não será gerado.")
        return

    # Estrutura base das regras (pode ser expandida com mais detalhes)
    rules_data = {
        "rules": [],
        # Adicionar outras seções como fallback_strategy, monitoring se necessário
    }

    # Adiciona regras básicas para MCPs funcionais
    for mcp_info in successful_mcps:
        # Aqui podemos adicionar lógica para gerar 'use_cases' mais específicos
        # Por enquanto, apenas listamos os MCPs ativos
        rules_data["rules"].append({
            "mcp": mcp_info['name'],
            "enabled": True,
            "type": mcp_info['type']
            # Adicionar use_cases padrão ou específicos aqui se desejado
        })

    # Tenta salvar nos caminhos base do VS Code
    appdata_path = os.environ.get('APPDATA', '')
    if not appdata_path:
        print("[AVISO] Variável APPDATA não encontrada. Não foi possível atualizar as regras do Roo Code.")
        return

    vscode_base_paths = [
        os.path.join(appdata_path, 'Code'),
        os.path.join(appdata_path, 'Code - Insiders')
    ]
    # Caminho relativo comum para configurações de extensão
    relative_rule_path = os.path.join('User', 'globalStorage', 'rooveterinaryinc.roo-cline', 'settings', 'mcp_rules.json')

    for base_path in vscode_base_paths:
        target_dir = os.path.dirname(os.path.join(base_path, relative_rule_path))
        target_file = os.path.join(base_path, relative_rule_path)

        try:
            if os.path.exists(base_path): # Verifica se a pasta base do VS Code existe
                os.makedirs(target_dir, exist_ok=True) # Garante que o diretório de settings exista
                with open(target_file, 'w', encoding='utf-8') as f:
                    json.dump(rules_data, f, indent=2, ensure_ascii=False)
                print(f"[INFO] Arquivo de regras MCP atualizado com sucesso em: {target_file}")
            # else:
                 # print(f"[INFO] Instalação do VS Code não encontrada em: {base_path}. Pulando atualização.")
        except Exception as e:
            print(f"[ERRO] Falha ao salvar arquivo de regras em {target_file}: {str(e)}")


def main():
    install_python_deps()
    report = []

    for mcp in MCP_CONFIG['mcps']:
        mcp_name = mcp['name']
        mcp_type = mcp['type']
        mcp_path = os.path.join(MCP_CONFIG['base_path'], mcp_name)
        result = {'name': mcp_name, 'type': mcp_type, 'status': 'Success'}

        if not os.path.isdir(mcp_path):
            result.update({'status': 'Skipped', 'message': 'Diretório não encontrado'})
            report.append(result)
            continue

        try:
            if mcp_type == 'Node':
                install_node_mcp(mcp_path, mcp_name)
            elif mcp_type == 'Python':
                install_python_mcp(mcp_path, mcp_name)

            result['message'] = 'Instalado com sucesso'
        except Exception as e:
            result.update({
                'status': 'Failed',
                'message': str(e),
                'fallback': 'Fallback gerado' if generate_fallback(mcp_path, mcp_name, mcp_type, str(e)) else 'Falha ao gerar fallback'
            })

        report.append(result)

    print("\nRelatório Final:")
    for item in report:
        print(f"\n{item['name']} ({item['type']}): {item['status']}")
        print(f"Mensagem: {item['message']}")
        if 'fallback' in item:
            print(f"Fallback: {item['fallback']}")

    # Atualiza arquivos de regras do Roo Code
    update_roo_code_rules(report)

def list_installed_mcps():
    """Lista MCPs instalados"""
    print("\nMCPs Configurados:")
    for mcp in MCP_CONFIG['mcps']:
        path = os.path.join(MCP_CONFIG['base_path'], mcp['name'])
        status = "Instalado" if os.path.exists(path) else "Não instalado"
        print(f"- {mcp['name']} ({mcp['type']}): {status}")

if __name__ == '__main__':
    if '--list' in sys.argv:
        list_installed_mcps()
    else:
        main()
