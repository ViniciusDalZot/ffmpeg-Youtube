import os
import subprocess
from flask_socketio import emit

class LogManager:
    base_path = '/etc/camerastwspeed/'

    def get_log_file(self, nomecamera):
        log_file = os.path.join(self.base_path, f"{nomecamera}.log")
        if os.path.exists(log_file):
            return log_file
        return None

    def tail_log(self, log_file, n=10):
        process = subprocess.Popen(['tail', '-n', str(n), log_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return stdout.decode('utf-8').splitlines()

    def follow_log(self, log_file):
        process = subprocess.Popen(['tail', '-f', log_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            line = process.stdout.readline()
            if not line:
                break
            emit('log_update', {'log': line.decode('utf-8').strip()})
