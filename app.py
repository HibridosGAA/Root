from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secreto_fps_123'
# Permitimos conexiones desde cualquier origen para evitar errores de CORS
socketio = SocketIO(app, cors_allowed_origins="*")

# --- CONFIGURACIÓN DE RUTAS ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/usuarios')
def ver_usuarios():
    # Render prefiere que usemos rutas relativas simples
    return render_template('usuarios_lista.html')

@app.route('/guardar_usuario', methods=['POST'])
def guardar_usuario():
    datos = request.get_json(silent=True)
    if datos and 'username' in datos:
        nombre = datos.get('username').strip().upper()
        
        ruta_base = os.path.dirname(os.path.abspath(__file__))
        ruta_lista = os.path.join(ruta_base, 'templates', 'usuarios_lista.html')
        
        # Verificación (Nota: En Render esto se reinicia con cada despliegue)
        if os.path.exists(ruta_lista):
            with open(ruta_lista, 'r', encoding='utf-8') as f:
                if f"SOLDADO: {nombre}" in f.read():
                    return jsonify({"status": "error", "message": "ID YA REGISTRADO"}), 409

        try:
            with open(ruta_lista, 'a', encoding='utf-8') as f:
                f.write(f"<p>SOLDADO: {nombre}</p>\n")
            return jsonify({"status": "success", "message": "Registro exitoso"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
            
    return jsonify({"status": "error", "message": "Datos inválidos"}), 400

# --- LÓGICA MULTIJUGADOR (Socket.IO) ---

@socketio.on('join')
def on_join(data):
    # Usamos type: ignore para que Pylance no se queje del sid
    sid = request.sid # type: ignore
    emit('new_player', {'id': sid, 'name': data['name']}, broadcast=True, include_self=False)

@socketio.on('move')
def on_move(data):
    emit('player_moved', {'id': request.sid, 'x': data['x'], 'y': data['y'], 'z': data['z'], 'ry': data['ry']}, broadcast=True, include_self=False) # type: ignore
@socketio.on('disconnect')
def on_disconnect():
    emit('player_left', {'id': request.sid}, broadcast=True)

if __name__ == '__main__':
    # Importante para Render: el puerto lo define la variable de entorno PORT
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)