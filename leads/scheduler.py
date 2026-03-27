from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command
from core.models import ApplicationCode
import logging

logger = logging.getLogger(__name__)

def run_reassignment():
    try:
        logger.info("Starting scheduled lead reassignment task...")
        call_command('reassign_leads')
        logger.info("Scheduled reassignment task completed successfully.")
    except Exception as e:
        logger.error(f"Error in scheduled reassignment task: {str(e)}")

def start():
    # Fetch interval from ApplicationCode Master
    # Expected Key: 'SYSTEM_CONFIG', Code: 'REASSIGN_SCHEDULER_INTERVAL'
    config = ApplicationCode.objects.filter(key='SYSTEM_CONFIG', code='REASSIGN_SCHEDULER_INTERVAL').first()
    try:
        interval_hours = int(config.name) if config and config.name.isdigit() else 6
    except (ValueError, TypeError):
        interval_hours = 6

    scheduler = BackgroundScheduler()
    # Schedule to run every X hours
    scheduler.add_job(run_reassignment, 'interval', hours=interval_hours, id='lead_reassignment_task', replace_existing=True)
    
    # Also run once immediately on start to ensure leads are processed
    scheduler.add_job(run_reassignment, 'date', id='lead_reassignment_immediate')
    
    scheduler.start()
    logger.info(f"Lead reassignment scheduler started. Interval: {interval_hours} hours.")
