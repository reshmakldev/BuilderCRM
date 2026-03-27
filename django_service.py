import os
import sys
import win32service
import win32serviceutil
import win32event
from waitress import serve
from django.core.wsgi import get_wsgi_application
import logging

# Set up logging for debugging
logging.basicConfig(
    filename='D:\\My-Projects\\ANTIGRAVITY\\CRM\\django_service.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DjangoService(win32serviceutil.ServiceFramework):
    _svc_name_ = "DjangoWebService"
    _svc_display_name_ = "Django Web Service"
    _svc_description_ = "A Windows service running a Django web server using Waitress."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        logging.info("Initializing Django service...")

        try:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
            self.application = get_wsgi_application()
        except Exception as e:
            logging.error(f"Error initializing WSGI application: {e}")

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.running = False
        logging.info("Stopping Django service...")

    def SvcDoRun(self):
        logging.info("Service is running...")
        serve(self.application, host='0.0.0.0', port=8080)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(DjangoService)
