import logging


class ColorFormatter(logging.Formatter):
    COLOR_MAP = {
        "ERROR": "\033[31m",  # Rouge
        "WARNING": "\033[33m",  # Jaune/Orange
        "INFO": "\033[32m",  # Vert
    }
    RESET = "\033[0m"

    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)

    def format(self, record):
        # Formater la date selon le format spécifié
        record.asctime = self.formatTime(record, self.datefmt)
        date_str = f"[{record.asctime}] "

        # Construire le reste du message
        color = self.COLOR_MAP.get(record.levelname, self.RESET)
        message = f"{record.levelname}: {record.getMessage()}"
        colored_message = f"{color}{message}{self.RESET}"

        # Combiner la date non colorée avec le message coloré
        return f"{date_str}{colored_message}"


# Configurer le logger 'hybridrouter'
logger = logging.getLogger("hybridrouter")
logger.setLevel(logging.DEBUG)  # Définir le niveau de log souhaité

# Définir le format avec la date
log_format = "[%(asctime)s] %(levelname)s: %(message)s"
date_format = "%d/%b/%Y %H:%M:%S"

# Initialiser le ColorFormatter avec le format et le format de date
color_formatter = ColorFormatter(fmt=log_format, datefmt=date_format)

# Créer un handler pour la sortie console et appliquer le formatter
handler = logging.StreamHandler()
handler.setFormatter(color_formatter)

# Ajouter le handler au logger
logger.addHandler(handler)
