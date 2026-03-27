import win32serviceutil
import win32service
import win32event
import subprocess
import signal
import os
import sys
import colorama

class DjangoService(win32serviceutil.ServiceFramework):
    _svc_name_ = "CRM"
    _svc_display_name_ = "CRM"
    _project_path = r"D:\My-Projects\ANTIGRAVITY\CRM\dist"

    def __init__(self, args):
        super().__init__(args)
        self.stop_event = win32event.CreateEvent(None, True, False, None)
        self.process = None  # Track the subprocess

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        
        # Terminate the Django process
        if self.process:
            self.process.send_signal(signal.SIGTERM)  # Graceful termination
            try:
                self.process.wait(timeout=5)  # Wait for exit
            except subprocess.TimeoutExpired:
                self.process.kill()  # Force kill if needed

        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)

        self.process = subprocess.Popen(
            [os.path.join(self._project_path, "manage.exe"), "runserver", "0.0.0.0:8921", "--noreload"],
            stdout=open(os.path.join(self._project_path, "logs", "crm_log.log"), "w"),
            stderr=open(os.path.join(self._project_path, "logs", "crm_errorlog.log"), "w")
        )

        self.process.communicate()  # Wait until process ends


colorama.init(strip=True)  # Disable ANSI colors in Windows Service
os.environ["PYTHONUNBUFFERED"] = "1"  # Prevents log flushing issues

os.chdir(r"D:\My-Projects\ANTIGRAVITY\CRM\dist")

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(DjangoService)
