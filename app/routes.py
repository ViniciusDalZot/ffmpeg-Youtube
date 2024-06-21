from flask import Blueprint, render_template, request, redirect, url_for
import subprocess
import os
import re
from ping3 import ping
from .utils import create_script, obter_detalhes_camera, atualizar_info_camera, tail_log, follow_log
from flask_socketio import emit
import threading

main = Blueprint('main', __name__)

@main.route('/')
def index():
    cameras = [f.replace('.sh', '') for f in os.listdir('/etc/cameras/') if f.endswith('.sh')]
    camera_statuses = []
    for camera in cameras:
        detalhes = obter_detalhes_camera(camera)
        ip = detalhes.get('ip')
        response_time = ping(ip, timeout=0.2)
        response_time = 'Sem Comunicação' if response_time is None else f"{response_time * 1000:.2f}"
        camera_statuses.append({
            'name': camera,
            'ip': ip,
            'usuario': detalhes.get('usuario'),
            'senha': detalhes.get('senha'),
            'ping': response_time
        })
    return render_template('index.html', cameras=camera_statuses)

@main.route('/add_camera_page')
def add_camera_page():
    return render_template('addcamera.html')

@main.route('/add_camera', methods=['POST'])
def add_camera():
    nomecamera = request.form['nomecamera']
    ipcamera = request.form['ipcamera']
    usuariocamera = request.form['usuariocamera']
    senhacamera = request.form['senhacamera']
    chaveyoutube = request.form['chaveyoutube']
    portartsp = request.form['portartsp']
    protocolo = request.form['protocolo']
    create_script(nomecamera, ipcamera, usuariocamera, senhacamera, chaveyoutube, portartsp, protocolo)
    cron_job = f"*/20 * * * * /etc/cameras/{nomecamera}.sh 2>&1"
    subprocess.run(f'(crontab -l; echo "{cron_job}") | crontab -', shell=True)
    return redirect(url_for('main.index'))

@main.route('/start_stream/<nomecamera>', methods=['POST'])
def start_stream(nomecamera):
    script_file = os.path.join('/etc/cameras/', f"{nomecamera}.sh")
    subprocess.run(script_file, shell=True)
    return redirect(url_for('main.index'))

@main.route('/view_logs/<nomecamera>')
def view_logs(nomecamera):
    return render_template('view_logs.html', nomecamera=nomecamera)

@main.route('/edit_camera/<camera_name>', methods=['GET', 'POST'])
def edit_camera(camera_name):
    if request.method == 'POST':
        new_ip = request.form.get('ipcamera')
        new_user = request.form.get('usuariocamera')
        new_password = request.form.get('senhacamera')
        new_portartsp = request.form.get('portartsp')
        new_protocolo = request.form.get('protocolo')
        atualizar_info_camera(camera_name, ip=new_ip, usuario=new_user, senha=new_password, portartsp=new_portartsp, protocolo=new_protocolo)
        return redirect(url_for('main.index'))
    detalhes = obter_detalhes_camera(camera_name)
    return render_template('edit_camera.html', camera_name=camera_name, detalhes=detalhes)

@main.route('/stop_stream/<nomecamera>', methods=['POST'])
def stop_stream(nomecamera):
    detalhes = obter_detalhes_camera(nomecamera)
    endereco_ip_camera = detalhes.get('ip')
    awk_command = '{print $2}'
    comando_busca = f'ps -ef | grep "{endereco_ip_camera}" | grep -v grep | awk \'{awk_command}\' | xargs kill -9'
    processo = subprocess.Popen(comando_busca, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    saida, erro = processo.communicate()
    if erro:
        print(f"Erro ao executar o comando: {erro.decode()}")
    if saida:
        subprocess.run(['pkill', '-f', 'ffmpeg'])
        print("Processo ffmpeg encerrado.")
    return redirect(url_for('main.index'))

@socketio.on('start_log')
def handle_start_log(data):
    nomecamera = data['nomecamera']
    log_file = os.path.join('/etc/cameras/', f"{nomecamera}.log")
    if os.path.exists(log_file):
        last_lines = tail_log(log_file, 10)
        for line in last_lines:
            emit('log_update', {'log': line})
        threading.Thread(target=follow_log, args=(log_file,)).start()
    else:
        emit('log_update', {'log': 'Log file not found.'})
