# Drivers WiFi para Steam Deck

Esta pasta contém os drivers WiFi necessários para o funcionamento do Steam Deck com Windows.

## Estrutura
```
wlan_driver/
├── lcd/       # Drivers para versão LCD do Steam Deck
├── oled_10/   # Drivers para versão OLED (modelo 10)
└── oled_11/   # Drivers para versão OLED (modelo 11)
```

## Instalação
Os drivers são instalados automaticamente pelo script quando:
1. O usuário seleciona a opção "Instalar Driver WiFi"
2. O sistema detecta que o driver padrão não está instalado

## Certificado
O arquivo `drivers.cer` contém o certificado necessário para instalação dos drivers.

## Manutenção
- Atualize os drivers periodicamente conforme novas versões são lançadas
- Verifique a compatibilidade com novas versões do Windows
- Mantenha a estrutura de pastas para garantir o funcionamento do instalador automático
