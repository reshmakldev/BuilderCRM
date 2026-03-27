import os
import logging
from waitress import serve
from real_estate_crm.wsgi import application  # <-- CHANGE to your project name

# ---------------- CONFIG ----------------
PROJECT_ROOT = r"D:\My-Projects\ANTIGRAVITY\CRM"   # <-- CHANGE to your project path
LOG_FILE = os.path.join(PROJECT_ROOT, "service.log")
HOST = "0.0.0.0"
PORT = 8070
# ----------------------------------------

# Ensure working directory
os.chdir(PROJECT_ROOT)

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logging.info("Starting Django server")

# Ensure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "real_estate_crm.settings")  # <-- CHANGE

try:
    serve(application, host=HOST, port=PORT)
except Exception:
    logging.exception("Server crashed")
