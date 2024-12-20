from flask import Blueprint, render_template, request, redirect, url_for, flash,session
import firebase_admin
from firebase_admin import credentials, auth
from config.firebase_config import obtener_clientes  # Asegúrate de importar la función
from config.firebase_config import agregar_cliente,db  # Importa la función aquí  # Asegúrate de que esto esté al principio del archivo




# Crea un blueprint para el módulo de autenticación
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login_view():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            # Intenta iniciar sesión con el email y la contraseña
            user = auth.get_user_by_email(email)
            session['user_id'] = user.uid 
            
            # Aquí deberías manejar la verificación de la contraseña
            print(f'user------{user.uid}')
            # Firebase no permite verificar la contraseña directamente
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('auth.home'))  # Redirige a la página de inicio
        except Exception as e:
            flash('Error en el inicio de sesión: {}'.format(str(e)), 'danger')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            # Crea un nuevo usuario con el email y la contraseña
            user = auth.create_user(
                email=email,
                password=password
            )
            flash('Registro exitoso. Puedes iniciar sesión ahora.', 'success')
            return redirect(url_for('auth.login_view'))  # Redirige a la página de login
        except Exception as e:
            flash('Error en el registro: {}'.format(str(e)), 'danger')
    return render_template('register.html')


@auth_bp.route('/home')
def home():
    id_asesor = session.get('user_id')  # Suponiendo que el ID del asesor se guarda en la sesión
    if not id_asesor:
        return redirect(url_for('auth.login_view'))  # Redirige si no hay sesión iniciada

    clientes = obtener_clientes(id_asesor)  # Obtiene la lista de clientes
    return render_template('home.html', clientes=clientes)

@auth_bp.route('/add_cliente', methods=['GET', 'POST'])
def add_cliente():
    if request.method == 'POST':
        nombre = request.form['nombre']
        direccion = request.form['direccion']
        telefono = request.form['telefono']
        id_asesor = session.get('user_id')  # Obtiene el ID del asesor desde la sesión

        if id_asesor:  # Verifica que haya un asesor en la sesión
            agregar_cliente(nombre, direccion, telefono, id_asesor)  # Llama a la función para agregar el cliente
            flash('Cliente agregado exitosamente', 'success')
            return redirect(url_for('auth.home'))  # Redirige a la página de inicio
        else:
            flash('Error: Debes iniciar sesión como asesor', 'danger')

    return render_template('add_cliente.html')  # Carga el formulario para agregar cliente

@auth_bp.route('/edit_cliente/<cliente_id>', methods=['GET', 'POST'])
def edit_cliente(cliente_id):
    ref = db.reference('clientes/' + cliente_id)
    cliente_data = ref.get()  # Obtiene los datos del cliente usando su ID

    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.form['nombre']
        direccion = request.form['direccion']
        telefono = request.form['telefono']

        # Actualiza los datos del cliente en Firebase
        ref.update({
            'nombre': nombre,
            'direccion': direccion,
            'telefono': telefono,
        })

        flash('Cliente actualizado exitosamente', 'success')
        return redirect(url_for('auth.home'))  # Redirige a la página de inicio

    return render_template('edit_cliente.html', cliente=cliente_data)  # Muestra el formulario con datos del cliente

@auth_bp.route('/logout')
def logout():
    session.pop('user', None)
    session.clear()  # Elimina el usuario de la sesión
    flash('Has cerrado sesión exitosamente', 'success')
    return redirect(url_for('auth.login_view'))  # Redirige a la página de inicio de sesión


@auth_bp.route('/eliminar_cliente/<cliente_id>', methods=['GET'])
def eliminar_cliente(cliente_id):
    # Eliminar el cliente con el ID proporcionado
    try:
        # Obtener la referencia al cliente específico en la base de datos
        cliente_ref = db.reference(f'clientes/{cliente_id}')
        
        # Eliminar el cliente de la base de datos
        cliente_ref.delete()
        
        flash('Cliente eliminado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar el cliente: {str(e)}', 'danger')
    
    return redirect(url_for('auth.home'))




@auth_bp.route('/historial_cliente')
def historial_cliente():
    id_asesor = session.get('user_id')
    prestamos_ref = db.reference('prestamos').order_by_child('cliente_id').get()  # Suponiendo que el ID del asesor se guarda en la sesión
    clientes_ref = db.reference('clientes').order_by_child('id_asesor').equal_to(id_asesor).get()  # Suponiendo que el ID del asesor se guarda en la sesión
    movimientos_ref = db.reference('movimientos').order_by_child('prestamo_id').get()
    catalogo_semanas_ref = db.reference('catalogo_semanas').get()
    if not id_asesor:
        return redirect(url_for('auth.login_view')) 
    prestamos = []
    total = []
    sumaGeneralC = 0
    sumaGeneralI = 0
    numero =0
    if clientes_ref:
        for cliente_id, cliente_data in clientes_ref.items():
            cliente_nombre = cliente_data.get('nombre')

            # Filtramos los préstamos de este cliente directamente
            cliente_prestamos = [prestamo for prestamo in prestamos_ref.values() if prestamo.get('cliente_id') == cliente_id]

            for prestamo_data in cliente_prestamos:
                totalPagado = 0
                # Filtrar los movimientos relevantes para este préstamo
                cliente_movimientos = [movimiento for movimiento in movimientos_ref.values() if movimiento.get('prestamo_id') == prestamo_data.get('id')]

                for movimiento_data in cliente_movimientos:
                    totalPagado += float(movimiento_data.get('monto', 0))

                semanas_id = prestamo_data.get('semanas_id', 0)
                catalogo_semanas = catalogo_semanas_ref.get(semanas_id) if semanas_id else None
                multa_semanas = float(catalogo_semanas['multa'] if catalogo_semanas else 0)
                semanas = catalogo_semanas.get('semanas', 0) if catalogo_semanas else 0

                totalPrestamo = float(prestamo_data.get('monto'))
                totalPagar = semanas * float(prestamo_data.get('pagoxSemana')) - totalPagado

                # Acumular los valores generales
                sumaGeneralC += totalPrestamo
                sumaGeneralI += totalPagar
                numero += 1

                # Agregar los datos del préstamo a la lista
                prestamos.append({
                    'id': prestamo_data.get('id'),
                    'cliente': cliente_nombre,
                    'totalPrestamo': totalPrestamo,
                    'totalPagar': totalPagar,
                    'semanas': semanas,
                    'numero': numero
                })

    # Agregar la fila total
        total.append({
            'Id':0,
            'cliente':'Total',
            'totalPrestamo':sumaGeneralC,
            'totalPagar':sumaGeneralI,
            'semanas': 0,
        })



    clientes = obtener_clientes(id_asesor)  # Obtiene la lista de clientes
    return render_template('historial_cliente.html', clientes=clientes, prestamos = prestamos, totales = total)
