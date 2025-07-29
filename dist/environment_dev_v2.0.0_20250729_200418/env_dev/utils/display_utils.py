import logging
import ctypes
import subprocess
import re
import os
import sys

# Constantes para tipos de display
DISPLAY_TYPE_LCD = "LCD"
DISPLAY_TYPE_OLED10 = "OLED10"
DISPLAY_TYPE_OLED11 = "OLED11"
DISPLAY_TYPE_UNKNOWN = "UNKNOWN"

def get_display_type():
    """
    Detecta o tipo de display do sistema Windows.
    
    Esta função tenta determinar se o display é LCD ou OLED com base nas propriedades
    do monitor e nos metadados do sistema.
    
    Returns:
        str: Tipo de display detectado: 'LCD', 'OLED10', 'OLED11' ou 'UNKNOWN'.
    """
    logging.info("Detectando tipo de display...")
    
    # Método 1: Usar WMI para obter informações do monitor
    try:
        if sys.platform != 'win32':
            logging.warning("Detecção de display só é suportada no Windows")
            return DISPLAY_TYPE_UNKNOWN
            
        # Usa PowerShell para acessar WMI (mais confiável que wmi Python em alguns sistemas)
        ps_command = 'Get-CimInstance -Namespace root\\wmi -ClassName WmiMonitorBasicDisplayParams | Format-List *'
        result = subprocess.run(['powershell', '-Command', ps_command], 
                              capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode != 0:
            logging.warning(f"Erro ao executar comando PowerShell: {result.stderr}")
            # Continua para outros métodos de detecção
        else:
            output = result.stdout
            
            # Analisa a saída para extrair dimensões do display
            width_match = re.search(r'MaxHorizontalImageSize\s*:\s*(\d+)', output)
            height_match = re.search(r'MaxVerticalImageSize\s*:\s*(\d+)', output)
            year_match = re.search(r'YearOfManufacture\s*:\s*(\d+)', output)
            
            if width_match and height_match:
                max_width = int(width_match.group(1))
                max_height = int(height_match.group(1))
                year = int(year_match.group(1)) if year_match else 0
                
                logging.debug(f"Dimensões de display detectadas: {max_width}x{max_height}, Ano: {year}")
                
                # Nenhuma dimensão válida, provavelmente display virtual
                if max_width == 0 or max_height == 0:
                    logging.info("Dimensões de display zeradas, possível display virtual")
                    return DISPLAY_TYPE_UNKNOWN
                
                # Calcula a proporção do display
                aspect_ratio = max_width / max_height
                
                # Lógica de detecção baseada em dimensões
                if aspect_ratio > 1.7:
                    # Widescreen, provavelmente LCD
                    logging.info(f"Display widescreen (proporção {aspect_ratio:.2f}), provavelmente LCD")
                    return DISPLAY_TYPE_LCD
                elif max_width < 20:
                    # Display pequeno, provavelmente OLED
                    if year >= 2021:
                        logging.info(f"Display pequeno (ano >= 2021), provavelmente OLED11")
                        return DISPLAY_TYPE_OLED11
                    else:
                        logging.info(f"Display pequeno (ano < 2021), provavelmente OLED10")
                        return DISPLAY_TYPE_OLED10
                else:
                    # Padrão para LCD
                    logging.info("Padrão para LCD com base nas dimensões")
                    return DISPLAY_TYPE_LCD
    
    except Exception as e:
        logging.error(f"Erro ao detectar tipo de display: {e}")
    
    # Método 2: Detectar baseado no EDID (dados de identificação de display estendido)
    try:
        edid_cmd = 'Get-CimInstance -Namespace root\\wmi -ClassName WmiMonitorID | ' + \
                  'Select-Object -ExpandProperty UserFriendlyName | ' + \
                  'ForEach-Object { [System.Text.Encoding]::ASCII.GetString($_.Where({$_ -ne 0})) }'
        
        result = subprocess.run(['powershell', '-Command', edid_cmd], 
                             capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0 and result.stdout.strip():
            model_name = result.stdout.strip().lower()
            logging.debug(f"Nome do monitor detectado: {model_name}")
            
            # Procura por palavras-chave que indicam tecnologia OLED
            if 'oled' in model_name:
                if 'v11' in model_name or '11' in model_name:
                    return DISPLAY_TYPE_OLED11
                else:
                    return DISPLAY_TYPE_OLED10
    
    except Exception as e:
        logging.error(f"Erro ao detectar modelo do display: {e}")
    
    # Método 3: Se todos os métodos acima falharem, retorna padrão LCD
    logging.info("Não foi possível determinar o tipo de display com certeza, retornando LCD como padrão")
    return DISPLAY_TYPE_LCD

if __name__ == "__main__":
    # Configuração básica de logging para testes
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Executa a detecção como teste
    display_type = get_display_type()
    print(f"Tipo de display detectado: {display_type}") 