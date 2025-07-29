Você é um assistente de desenvolvimento para o PROJETO e especialista em automação de sistemas e scriptingque  que DEVE:
1.  SEMPRE consultar e seguir @AI_GUIDELINES.md antes de qualquer ação
2.  Validar TODAS as solicitações usando a matriz de validação definida
3.  Registrar TODAS as ações no formato de log especificado

✅
MEU COMANDO:
DEV:


## 🚨
CONTEXTO:

*   Manter rigidamente a estrutura do projeto conforme o @AI_GUIDELINES.md
*   você deve ser capaz de seguir as instruções e realizar as tarefas sem ambiguidade.

## 📋
PROCESSO OBRIGATÓRIO:

1.  Consultar AI_GUIDELINES.md
2.  Executar checklist pré-implementação
3.  Validar em todas as camadas
4.  Gerar log de auditoria
5.  Retornar resultado padronizado
6.  Confirme se deu certo e se possível faça testes
7.  Avalie a necessidade de atualizar @docs/VERSION.md para manter Histórico de versões atualizado


## ----------------------------------------------------------------------- ## 
Você é um assistente de desenvolvimento para o PROJETO e especialista em automação de sistemas e scriptingque  que DEVE:
1.  SEMPRE consultar e seguir @AI_GUIDELINES.md antes de qualquer ação
2.  Validar TODAS as solicitações usando a matriz de validação definida
3.  Registrar TODAS as ações no formato de log especificado

✅
MEU COMANDO:
DEV:

O processo anterior foi interrompido devido ao contexto ser longo, de continuidade com atenção a coesão do código usando extra requests

## 🚨
CONTEXTO:

*   Manter rigidamente a estrutura do projeto conforme o @AI_GUIDELINES.md
*   você deve ser capaz de seguir as instruções e realizar as tarefas sem ambiguidade.

## 📋
PROCESSO OBRIGATÓRIO:

1.  Consultar AI_GUIDELINES.md
2.  Executar checklist pré-implementação
3.  Validar em todas as camadas
4.  Gerar log de auditoria
5.  Retornar resultado padronizado
6.  Confirme se deu certo e se possível faça testes
7.  Avalie a necessidade de atualizar @docs/VERSION.md para manter Histórico de versões atualizado

## ----------------------------------------------------------------------- ## 

Você é um assistente de desenvolvimento para o PROJETO e especialista em automação de sistemas e scriptingque  que DEVE:
1.  SEMPRE consultar e seguir @AI_GUIDELINES.md antes de qualquer ação
2.  Validar TODAS as solicitações usando a matriz de validação definida
3.  Registrar TODAS as ações no formato de log especificado

✅
MEU COMANDO:
DEV: suba esta versão no github

## 🚨
CONTEXTO:

*   Manter rigidamente a estrutura do projeto conforme o @AI_GUIDELINES.md
*   você deve ser capaz de seguir as instruções e realizar as tarefas sem ambiguidade.

## 📋
PROCESSO OBRIGATÓRIO:

1.  Consultar AI_GUIDELINES.md
2.  Executar checklist pré-implementação
3.  Validar em todas as camadas
4.  Gerar log de auditoria
5.  Retornar resultado padronizado
6.  Confirme se deu certo e se possível faça testes
7.  Avalie a necessidade de atualizar @docs/VERSION.md para manter Histórico de versões atualizado

## ----------------------------------------------------------------------- ## 


Você é um assistente de desenvolvimento para o PROJETO e especialista em automação de sistemas e scriptingque DEVE:
1.  SEMPRE consultar e seguir @AI_GUIDELINES.md antes de qualquer ação
2.  Validar TODAS as solicitações usando a matriz de validação definida
3.  Registrar TODAS as ações no formato de log especificado

✅
MEU COMANDO:
DEV: Desenvolva um script PowerShell totalmente automatizado para instalar e configurar os seguintes tweaks no Windows 11 em um Steam Deck (LCD). O script deve ser executado sem intervenção manual, com logs detalhados e tratamento de erros. Use ferramentas como Chocolatey/Winget para instalações e inclua comentários explicativos.

Tweaks a Implementar:
Gyroscope (SteamDeckGyroDSU)
Clone o repositório: https://github.com/rafael89h/SteamDeckGyroDSU
Instale dependências (Python, drivers) e configure o serviço para inicializar automaticamente.
Modo de Desempenho (RyzenAdj)
Baixe o RyzenAdj (binário ou via compilação).
Aplique os comandos:
bash
Copy
1
ryzenadj --stapm-limit=15000 --fast-limit=15000 --slow-limit=10000  
Crie um agendamento de tarefa para aplicar o TDP no boot.
Desativar Game Bar e Game Mode
Execute:
powershell
Copy
1
2
Disable-GameBarTips  
Set-ItemProperty -Path "HKCU:\Software\Microsoft\GameBar" -Name "AutoGameModeEnabled" -Value 0  
Mover Arquivo de Paginação
Detecte SSDs externos (ex: D:\).
Redirecione o pagefile para o SSD via registro do Windows:
powershell
Copy
1
Set-WmiInstance -Path "Win32_PageFileSetting.Name='D:\\pagefile.sys'" -Arguments @{InitialSize=4096; MaximumSize=8192}  
Desativar OneDrive e Cortana
Remova OneDrive:
powershell
Copy
1
2
taskkill /f /im OneDrive.exe  
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Microsoft\OneDrive"  
Desative Cortana via Política de Grupo ou Registro.
Compactação NTFS
Aplique compressão em pastas críticas:
powershell
Copy
1
compact /c /i /q "C:\Windows\System32"  
Monitoramento (HWInfo/Decky Loader)
Instale o HWInfo (via Chocolatey) e configure alertas de temperatura.
Instale o Decky Loader para Windows: https://github.com/ACCESS-DENIIED/Decky-Loader-For-Windows.git.
Controle de Fans (ThrottleStop)
Baixe o ThrottleStop e crie um perfil para ajustar curvas de ventoinha.
Configure agendamento de tarefa para aplicar configurações no boot.
Keystone
Instale o Keystone (ferramenta de perfis de TDP/GPU).
Configure perfis para jogos e desktop.
Corrigir Relógio (Registro)
Execute:
powershell
Copy
1
reg add "HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\TimeZoneInformation" /v RealTimeIsUniversal /d 1 /t REG_DWORD /f  
Requisitos Adicionais:
Verifique se o script está sendo executado como Administrador.
Baixe dependências automaticamente (ex: Python, Git).
Trate erros (ex: falha no download, permissões).
Crie logs em C:\TweakLogs.
Reinicie serviços/aplicações conforme necessário.

Gerenciamento de Energia Avançado
Perfis de TDP Dinâmicos :
Instale o Keystone (https://github.com/keystone-enclave/keystone ) e configure dois perfis:
Jogos : TDP de 15W (use ryzenadj --stapm-limit=15000).
Desktop : TDP de 8W (use ryzenadj --stapm-limit=8000).
Crie atalhos para alternar perfis via PowerShell .
Desativar Sleep Mode :
Execute:
powershell
Copy
1
powercfg /change standby-timeout-ac 0  # Desativa sleep no modo AC [[4]]  
2. Armazenamento e Sistema
Habilitar TRIM para SSD :
powershell
Copy
1
Optimize-Volume -DriveLetter C -ReTrim -Verbose  # Mantém SSD rápido [[4]]  
3. Controles e Entradas
Mapeamento de Botões (Durazno) :
Baixe e instale o Durazno (https://github.com/ramensoftware/durazno ).
Configure dead zones e sensibilidade via DuraznoConfig.exe.
Desativar Trackpads em Jogos :
Crie um script AutoHotkey que desative os trackpads ao detectar processos de jogos (ex: steam.exe, epicgameslauncher.exe).
4. Rede e Conectividade
Prioridade de Rede (Process Lasso) :
Instale o Process Lasso (via Chocolatey) e configure regras para priorizar tráfego de jogos.
Exemplo:
powershell
Copy
1
choco install -y processlasso  
Conexão Ethernet :
Detecte adaptadores USB-C/Ethernet e defina métrica de rota prioritária via netsh interface.
5. Experiência do Usuário
Customização da Central de Ações :
Remova atalhos como "Focus Assist" via registro:
powershell
Copy
1
Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" -Name "ShowTaskViewButton"  
Rainmeter :
Instale o Rainmeter e widgets de monitoramento (ex: HWInfo):
powershell
Copy
1
choco install -y rainmeter  
6. Backup e Restauração
Criar Imagem do Sistema :
Use wbadmin para criar um snapshot:
powershell
Copy
1
wbadmin start backup -backupTarget:D: -include:C: -quiet  
Hiren’s BootCD :
Baixe a ISO e crie um USB bootável (instruções manuais necessárias).

os mesmos devem ser listados na área Tweaks do progama

## 🚨
CONTEXTO:

*   Manter rigidamente a estrutura do projeto conforme o @AI_GUIDELINES.md
*   você deve ser capaz de seguir as instruções e realizar as tarefas sem ambiguidade.

## 📋
PROCESSO OBRIGATÓRIO:

1.  Consultar AI_GUIDELINES.md
2.  Executar checklist pré-implementação
3.  Validar em todas as camadas
4.  Gerar log de auditoria
5.  Retornar resultado padronizado
6.  Confirme se deu certo e se possível faça testes
7.  Avalie a necessidade de atualizar @docs/VERSION.md para manter Histórico de versões atualizado

## ----------------------------------------------------------------------------

Você é um assistente de desenvolvimento para o PROJETO e especialista em automação de sistemas e scriptingque  que DEVE:
1.  SEMPRE consultar e seguir #file:AI_GUIDELINES.md antes de qualquer ação
2.  Validar TODAS as solicitações usando a matriz de validação definida
3.  Registrar TODAS as ações no formato de log especificado

✅
MEU COMANDO:
DEV:

faça a aplicação do plano para termos  estrutura mais coesa e manutenível. O plano inclui:

- Uma nova estrutura de diretórios organizada por responsabilidades (core, environment, installation, tweaks)
- Módulos independentes com responsabilidades bem definidas
- Sistema de logging centralizado e consistente
- Interface de usuário modular e responsiva
- Tratamento de erros robusto em todos os níveis
Foram criados exemplos práticos de implementação para demonstrar como seria a estrutura modularizada:

- Um módulo de instalação de drivers que encapsula toda a lógica de detecção e instalação
- Um script principal que orquestra a execução dos módulos
O plano de implementação foi dividido em 5 fases, com um cronograma estimado e análise de riscos. Esta modularização resolverá os problemas de manutenção e risco de quebra constante do script principal, tornando o projeto mais sustentável a longo prazo

## 🚨
CONTEXTO:

*   Manter rigidamente a estrutura do projeto conforme o @AI_GUIDELINES.md e @file:docs\MODULARIZACAO.md
*   você deve ser capaz de seguir as instruções e realizar as tarefas sem ambiguidade.

## 📋
PROCESSO OBRIGATÓRIO:

1.  Consultar AI_GUIDELINES.md
2.  Executar checklist pré-implementação
3.  Validar em todas as camadas
4.  Gerar log de auditoria
5.  Retornar resultado padronizado
6.  Confirme se deu certo e se possível faça testes
7.  Avalie a necessidade de atualizar @docs/VERSION.md para manter Histórico de versões atualizado

## ----------------------------------------------------------------------------

Você é um assistente de desenvolvimento para o PROJETO e especialista em automação de sistemas e scriptingque  que DEVE:
1.  SEMPRE consultar e seguir @AI_GUIDELINES.md antes de qualquer ação
2.  Validar TODAS as solicitações usando a matriz de validação definida
3.  Registrar TODAS as ações no formato de log especificado

✅
MEU COMANDO:
DEV:

faça uma proposta de plano para o projeto se tornar modular, com coesão no código, logica clara e funcional para checagem de ambiente com instalação completa dos programas de forma a dar o feedback para o susuário e amigavel


## 🚨
CONTEXTO:
O projeto esta em risco pois toda logica esta em @Windeckhelper.ps1 causando o risco de quebra constante do script e dificil manutenção



*   você deve ser capaz de seguir as instruções e realizar as tarefas sem ambiguidade.

## 📋
PROCESSO OBRIGATÓRIO:

1.  Consultar AI_GUIDELINES.md
2.  Executar checklist pré-implementação
3.  Validar em todas as camadas
4.  Gerar log de auditoria
5.  Retornar resultado padronizado
6.  Confirme se deu certo e se possível faça testes
7.  Avalie a necessidade de atualizar @docs/VERSION.md para manter Histórico de versões atualizado