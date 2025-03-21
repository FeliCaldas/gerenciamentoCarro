import logging
import os
from datetime import datetime

class CustomFormatter(logging.Formatter):
    """Formatador personalizado com cores"""
    grey = "\x1b[38;20m"
    blue = "\x1b[34;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: blue + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

def cleanup_old_logs(days=15):
    """Remove logs mais antigos que o número de dias especificado"""
    if not os.path.exists('logs'):
        return
        
    current_time = datetime.now()
    for filename in os.listdir('logs'):
        if not filename.endswith('.log'):
            continue
            
        file_path = os.path.join('logs', filename)
        file_time = datetime.fromtimestamp(os.path.getctime(file_path))
        
        if (current_time - file_time).days > days:
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Erro ao remover log antigo {filename}: {e}")

def setup_logger(name):
    """Configura e retorna um logger personalizado"""
    # Limpa logs antigos antes de criar novo logger
    cleanup_old_logs()
    
    # Cria o diretório de logs se não existir
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    # Cria o logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Evita duplicação de handlers
    if not logger.handlers:
        # Handler para console com cores
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(CustomFormatter())
        logger.addHandler(console_handler)
        
        # Handler para arquivo
        file_handler = logging.FileHandler(
            f'logs/{name}_{datetime.now().strftime("%Y%m%d")}.log'
        )
        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    return logger
