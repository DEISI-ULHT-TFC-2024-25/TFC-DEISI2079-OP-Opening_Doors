from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import serial
from datetime import datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


SERIAL_PORT = "COM3"
BAUD_RATE = 9600


db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    doors = db.relationship('Door', backref='user', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', criado em {self.created_at})"

    def set_password(self, password):
        
        self.password = generate_password_hash(password)

    def check_password(self, password):
        
        return check_password_hash(self.password, password)

class Door(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(10), default="fechada")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    arduino_ip = db.Column(db.String(50), nullable=False)  
    last_opened_at = db.Column(db.DateTime)  

    def __repr__(self):
        return f"Door('{self.name}', Status: {self.status}, User ID: {self.user_id}, IP: {self.arduino_ip})"




import requests

def send_to_arduino_wifi(arduino_ip, comando):
    try:
        url = f"http://{arduino_ip}/{comando}"
        resposta = requests.get(url, timeout=3)
        return {"message": resposta.text}, 200
    except Exception as e:
        return {"error": f"Erro na comunicação com o Arduino: {str(e)}"}, 500


# Função para enviar comando ao Arduino
def send_to_arduino(comando):
    try:
        # Abre a porta serial diretamente com os parâmetros corretos
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        ser.write(comando.encode())
        ser.close()
        return {"message": f"Comando '{comando}' enviado com sucesso!"}, 200
    except Exception as e:
        return {"error": f"Erro na comunicação com o Arduino: {str(e)}"}, 500


# Novo endpoint para abrir uma porta através do Arduino
@app.route('/open-door-arduino', methods=['POST'])
def open_door_arduino():
    data = request.json
    comando = data.get('comando', "ON")

    resposta, status = send_to_arduino(comando)
    return jsonify(resposta), status

# Endpoint para fechar a porta
@app.route('/close-door-arduino', methods=['POST'])
def close_door_arduino():
    data = request.json
    comando = data.get('comando', "OFF")

    resposta, status = send_to_arduino(comando)
    return jsonify(resposta), status

# Rota inicial para testar o servidor
@app.route('/')
def home():
    return "Bem-vindo ao servidor Flask!"

# Endpoint para registar um utilizador
@app.route('/register', methods=['POST'])
def register_user():
    data = request.json
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Dados inválidos!"}), 400

    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({"error": "O username já existe!"}), 400
    
    new_user = User(username=data['username'])
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Utilizador registado com sucesso!"}), 201

# Novo Endpoint para criar uma porta
@app.route('/create-door', methods=['POST'])
def create_door():
    data = request.json
    if not data or "name" not in data or "user_id" not in data or "arduino_ip" not in data:
        return jsonify({"error": "É necessário fornecer 'name', 'user_id' e 'arduino_ip'."}), 400

    user = User.query.get(data['user_id'])
    if not user:
        return jsonify({"error": "Utilizador não encontrado!"}), 404

    existing_door = Door.query.filter_by(name=data['name']).first()
    if existing_door:
        return jsonify({"error": "Já existe uma porta com esse nome!"}), 400

    new_door = Door(
        name=data['name'],
        user_id=data['user_id'],
        arduino_ip=data['arduino_ip']
    )
    db.session.add(new_door)
    db.session.commit()

    return jsonify({"message": f"Porta '{new_door.name}' criada com sucesso!"}), 201


# Endpoint para alternar estado da porta (abrir/fechar)
@app.route('/toggle-door', methods=['POST'])
def toggle_door():
    data = request.json
    door_id = data.get('door_id')

    if door_id is None:
        return jsonify({"error": "É necessário fornecer um door_id."}), 400

    door = Door.query.get(door_id)
    if not door:
        return jsonify({"error": "Porta não encontrada."}), 404

    # Alterna status local
    new_status = "fechada" if door.status == "aberta" else "aberta"
    door.status = new_status

    if new_status == "aberta":
        door.last_opened_at = datetime.now()
    db.session.commit()

    # Envia comando toggle ao Arduino via Wi-Fi
    comando = "toggle"
    resposta, status = send_to_arduino_wifi(door.arduino_ip, comando)

    return jsonify({
        "message": f"Porta '{door.name}' agora está {door.status}.",
        "last_opened_at": door.last_opened_at,
        "arduino_response": resposta
    }), status



# Endpoint para listar utilizadores
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{"id": user.id, "username": user.username, "created_at": user.created_at} for user in users])

# Endpoint para listar portas
@app.route('/doors', methods=['GET'])
def get_doors():
    doors = Door.query.all()
    return jsonify([{"id": door.id, "name": door.name, "status": door.status, "user_id": door.user_id} for door in doors])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
