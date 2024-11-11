import schedule
import time
from main import generate_and_upload_podcast
from config import UPLOAD_SCHEDULE

def schedule_podcast():
    # Example UPLOAD_SCHEDULE: 'Monday at 08:00'
    day, time_str = UPLOAD_SCHEDULE.split(' at ')
    schedule.every().__getattribute__(day.lower()).at(time_str).do(generate_and_upload_podcast)

    print(f"Scheduled podcast generation and upload every {UPLOAD_SCHEDULE}.")

    while True:
        schedule.run_pending()
        time.sleep(60)  # Wait one minute between checks

if __name__ == '__main__':
    schedule_podcast()