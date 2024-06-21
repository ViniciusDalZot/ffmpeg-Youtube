import os
import subprocess
from ping3 import ping

class CameraManager:
    base_path = '/etc/camerastwspeed/'

    def __init__(self):
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def create_camera_script(self, nomecamera, ipcamera, usuariocamera, senhacamera, chaveyoutube, portartsp):
        script_content = f'''...'''  # Mantenha o conteúdo do script original
        script_file = os.path.join(self.base_path, f"{nomecamera}.sh")
        with open(script_file, 'w') as f:
            f.write(script_content)
        os.chmod(script_file, 0o777)

    def start_stream(self, nomecamera):
        script_file = os.path.join(self.base_path, f"{nomecamera}.sh")
        subprocess.run(script_file, shell=True)

    def stop_stream(self, nomecamera):
        detalhes = self.get_camera_details(nomecamera)
        endereco_ip_camera = detalhes.get('ip')
        awk_command = '{print $2}'
        comando_busca = f'ps -ef | grep "{endereco_ip_camera}" | grep -v grep | awk \'{awk_command}\' | xargs kill -9'
        subprocess.run(comando_busca, shell=True)
        subprocess.run(['pkill', '-f', 'ffmpeg'])

    def ping_camera(self, ip):
        if ip:
            response_time = ping(ip, timeout=0.2)
            if response_time is None:
                return 'Sem Comunicação'
            return f"{response_time * 1000:.2f}"
        return 'IP não encontrado'

    def list_cameras(self):
        return [f.replace('.sh', '') for f in os.listdir(self.base_path) if f.endswith('.sh')]
