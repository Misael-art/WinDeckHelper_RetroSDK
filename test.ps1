# Script de teste para verificar o ambiente PowerShell
Add-Type -AssemblyName PresentationFramework
[System.Windows.Forms.MessageBox]::Show("Teste de execução do PowerShell", "WinDeckHelper Test")

# Verifica se está rodando como administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($isAdmin) {
    [System.Windows.Forms.MessageBox]::Show("Executando como administrador", "WinDeckHelper Test")
} else {
    [System.Windows.Forms.MessageBox]::Show("Não está executando como administrador", "WinDeckHelper Test")
} 