
import subprocess
import time
import datetime


if __name__ == "__main__":
    # Replace 'script.py' with the name of the Python script you want to run
    script_path = "speedtest.py"
    schedule_time = "23:38"
    repeat_count = 2
    while True:
        current_time = datetime.datetime.now().strftime("%H:%M")
        if current_time == schedule_time:
            for i in range(repeat_count):
                subprocess.run(["python", script_path])
            break
        else:
            time.sleep(1)
