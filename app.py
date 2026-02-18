import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secreto_fps_123'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Diccionario para trackear salud de jugadores
jugadores_stats = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/usuarios')
def ver_usuarios():
    return render_template('usuarios_lista.html')

@app.route('/guardar_usuario', methods=['POST'])
def guardar_usuario():
    try:
        datos = request.get_json(silent=True)
        if not datos or 'username' not in datos:
            return jsonify({"status": "error", "message": "Datos inválidos"}), 400
        nombre = datos.get('username').strip().upper()
        ruta_base = os.path.dirname(os.path.abspath(__file__))
        ruta_lista = os.path.join(ruta_base, 'templates', 'usuarios_lista.html')
        if not os.path.exists(ruta_lista):
            with open(ruta_lista, 'w', encoding='utf-8') as f:
                f.write("<h1>Lista de Soldados</h1>\n")
        with open(ruta_lista, 'a', encoding='utf-8') as f:
            f.write(f"<p>SOLDADO: {nombre}</p>\n")
        return jsonify({"status": "success", "message": "REGISTRO EXITOSO"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- EVENTOS MULTIJUGADOR EXTENDIDOS ---

@socketio.on('join')
def on_join(data):
    sid = request.sid
    nombre = data.get('name', f'Recluta_{sid[:4]}')
    jugadores_stats[sid] = {'name': nombre, 'hp': 100}
    emit('new_player', {'id': sid, 'name': nombre}, broadcast=True, include_self=False)

@socketio.on('move')
def on_move(data):
    emit('player_moved', {
        'id': request.sid,
        'x': data['x'], 'y': data['y'], 'z': data['z'], 'ry': data['ry']
    }, broadcast=True, include_self=False)

@socketio.on('shoot_hit')
def on_shoot_hit(data):
    target_id = data.get('target_id')
    shooter_id = request.sid
    
    if target_id in jugadores_stats:
        jugadores_stats[target_id]['hp'] -= 25 # Daño por disparo
        
        if jugadores_stats[target_id]['hp'] <= 0:
            jugadores_stats[target_id]['hp'] = 100 # Reset para respawn
            # Notificar muerte a todos para el Kill Feed
            emit('kill_event', {
                'killer': jugadores_stats[shooter_id]['name'],
                'victim': jugadores_stats[target_id]['name'],
                'victim_id': target_id
            }, broadcast=True)
        else:
            # Notificar solo al jugador golpeado que perdió vida
            emit('take_damage', {'new_hp': jugadores_stats[target_id]['hp']}, room=target_id)

@socketio.on('disconnect')
def on_disconnect():
    if request.sid in jugadores_stats:
        del jugadores_stats[request.sid]
    emit('player_left', {'id': request.sid}, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)