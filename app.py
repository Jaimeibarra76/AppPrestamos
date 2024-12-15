from flask import Flask
from auth.login import auth_bp 
from auth.prestamos import prestamos_bp
import os  # Importa el blueprint del módulo de autenticación

def create_app():
    app = Flask(__name__)
    app.secret_key = 'tu_clave_secreta'  # Cambia esto por una clave secreta

    # Registra las rutas
    app.register_blueprint(auth_bp)
    app.register_blueprint(prestamos_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
