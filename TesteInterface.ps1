# Teste básico de interface
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName PresentationFramework

# Cria uma janela básica
$form = New-Object System.Windows.Forms.Form
$form.Text = "WinDeckHelper - Teste"
$form.Size = New-Object System.Drawing.Size(800,600)
$form.StartPosition = "CenterScreen"
$form.BackColor = [System.Drawing.Color]::FromArgb(30,30,30)
$form.ForeColor = [System.Drawing.Color]::White

# Adiciona um label
$label = New-Object System.Windows.Forms.Label
$label.Location = New-Object System.Drawing.Point(10,20)
$label.Size = New-Object System.Drawing.Size(780,40)
$label.Text = "Se você consegue ver esta janela, a interface básica está funcionando."
$label.Font = New-Object System.Drawing.Font("Segoe UI", 12)
$label.ForeColor = [System.Drawing.Color]::White
$form.Controls.Add($label)

# Adiciona um botão
$button = New-Object System.Windows.Forms.Button
$button.Location = New-Object System.Drawing.Point(300,500)
$button.Size = New-Object System.Drawing.Size(200,40)
$button.Text = "Fechar"
$button.BackColor = [System.Drawing.Color]::FromArgb(0,120,212)
$button.ForeColor = [System.Drawing.Color]::White
$button.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
$button.Add_Click({ $form.Close() })
$form.Controls.Add($button)

# Mostra a janela
[System.Windows.Forms.Application]::EnableVisualStyles()
$form.ShowDialog() 