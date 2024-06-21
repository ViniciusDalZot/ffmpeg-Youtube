import os
import re
import subprocess

base_path = "/etc/cameras/"

def create_script(nomecamera, ipcamera, usuariocamera, senhacamera, chaveyoutube, portartsp, protocolo):
    script_content = f'''#! /bin/bash
date=$(date "+DATE: %d/%m/%Y %T")
ipcamera='{ipcamera}'
nomecamera='{nomecamera}'
usuariocamera='{usuariocamera}'
senhacamera='{senhacamera}'
chaveyoutube='{chaveyoutube}'
processocamera=$(ps -aux |grep -v grep | grep -o "{ipcamera}" | wc -l | grep -v grep;)
processomanu=$(ps -ef | grep "{chaveyoutube}" | grep 'twspeed' | grep -v grep | wc -l | grep -v grep;)
portartsp='{portartsp}'
protocolo='{protocolo}'
function SteamingCamera () {{
    log_file="/etc/cameras/$nomecamera.log"
    if [ "$processocamera" -ge "1" ]; then
        echo "" >> "$log_file"
        ps -ef | grep $chaveyoutube | grep 'manutencao' | grep -v grep | awk '{{print $2}}' | xargs kill -9;
    else
        ps -ef | grep "$chaveyoutube" | grep 'manutencao' | grep -v grep | awk '{{print $2}}' | xargs kill -9;
        echo "" >> "$log_file"
        ffmpeg -f lavfi -i anullsrc -rtsp_transport $protocolo -i "rtsp://$usuariocamera:$senhacamera@$ipcamera:$portartsp/cam/realmonitor?channel=1&subtype=0" \
-vf "movie=logo1.png [watermark]; [in][watermark] overlay=10:10" \
-tune zerolatency -preset medium -pix_fmt yuv420p \
-c:v libx264 -x264opts keyint=48:min-keyint=48:no-scenecut -b:v 2000k \
-c:a aac -strict experimental -f flv rtmp://a.rtmp.youtube.com/live2/$chaveyoutube >> "$log_file" 2>&1
    fi
}}

function SteamingManutencao () {{
    if [ "$processomanu" -ge "1" ]; then
        ps -ef | grep "$ipcamera" | grep -v grep | awk '{{print $2}}' | xargs kill -9;
        echo "$date - Camera da $nomecamera com IP $ipcamera | Usuario: $usuariocamera | Senha: $senhacamera |  esta inacessivel" >> {base_path}$nomecamera.log
    else
        ps -ef | grep "$ipcamera" | grep -v grep | awk '{{print $2}}' | xargs kill -9;
        echo "$date - Camera da $nomecamera com IP $ipcamera| Usuario: $usuariocamera | Senha: $senhacamera |  esta inacessivel" >> {base_path}$nomecamera.log
        ffmpeg -stream_loop -1 -re -i {base_path}twspeed.mp4 -c:v libx264 -preset ultrafast -bufsize 5 -r 30 -b:v 500k -maxrate 1000k -f flv rtmp://a.rtmp.youtube.com/live2/$chaveyoutube &> /dev/null &
    fi
}}
ping=$(ping -c 2 "$ipcamera" | grep 'received' | awk -F',' '{{print $2}}' | awk '{{print $1}}');
if [ "$ping" -ge 1 ]; then
    SteamingCamera;
else
    SteamingManutencao;
fi
'''
    script_file = os.path.join(base_path, f"{nomecamera}.sh")
    with open(script_file, 'w') as f:
        f.write(script_content)
    os.chmod(script_file, 0o755)

def obter_detalhes_camera(nomecamera):
    script_file = os.path.join(base_path, f"{nomecamera}.sh")
    detalhes = {}
    if os.path.exists(script_file):
        with open(script_file, 'r') as f:
            content = f.read()
            detalhes['ip'] = re.search(r"ipcamera='(.*)'", content).group(1)
            detalhes['usuario'] = re.search(r"usuariocamera='(.*)'", content).group(1)
            detalhes['senha'] = re.search(r"senhacamera='(.*)'", content).group(1)
            detalhes['portartsp'] = re.search(r"portartsp='(.*)'", content).group(1)
            detalhes['protocolo'] = re.search(r"protocolo='(.*)'", content).group(1)
    return detalhes

def atualizar_info_camera(nomecamera, **novos_detalhes):
    script_file = os.path.join(base_path, f"{nomecamera}.sh")
    if os.path.exists(script_file):
        with open(script_file, 'r') as f:
            content = f.read()
        for key, value in novos_detalhes.items():
            content = re.sub(fr"{key}='.*'", f"{key}='{value}'", content)
        with open(script_file, 'w') as f:
            f.write(content)

def tail_log(log_file, lines=10):
    return subprocess.check_output(['tail', f'-n {lines}', log_file]).decode('utf-8').splitlines()

def follow_log(log_file):
    process = subprocess.Popen(['tail', '-f', log_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        line = process.stdout.readline()
        if not line:
            break
        emit('log_update', {'log': line.decode('utf-8').strip()})
