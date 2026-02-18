import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secreto_fps_123'
# CORS habilitado para evitar bloqueos en el despliegue
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# --- RUTAS ---

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
        
        # Asegurar que el archivo exista para evitar errores de lectura
        if not os.path.exists(ruta_lista):
            with open(ruta_lista, 'w', encoding='utf-8') as f:
                f.write("<h1>Lista de Soldados</h1>\n")

        # Guardar el nombre
        with open(ruta_lista, 'a', encoding='utf-8') as f:
            f.write(f"<p>SOLDADO: {nombre}</p>\n")
            
        return jsonify({"status": "success", "message": "REGISTRO EXITOSO"})
    except Exception as e:
        print(f"Error en servidor: {e}")
        return jsonify({"status": "error", "message": "Error interno del servidor"}), 500

# --- LÓGICA MULTIJUGADOR ---

@socketio.on('join')
def on_join(data):
    sid = request.sid # type: ignore
    # Avisar a todos que entró alguien nuevo
    emit('new_player', {'id': sid, 'name': data.get('name', 'Anon')}, broadcast=True, include_self=False)

@socketio.on('move')
def on_move(data):
    # Reenviar la posición a los demás jugadores
    emit('player_moved', {
        'id': request.sid, # type: ignore
        'x': data['x'], 
        'y': data['y'], 
        'z': data['z'], 
        'ry': data['ry']
    }, broadcast=True, include_self=False)

@socketio.on('disconnect')
def on_disconnect():
    emit('player_left', {'id': request.sid}, broadcast=True) # type: ignore

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)