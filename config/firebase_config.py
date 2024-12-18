import firebase_admin
from firebase_admin import credentials, db
import os
import json

firebase_config = os.getenv('FIREBASE_CONFIG')

if not firebase_config:
    raise ValueError("La variable de entorno FIREBASE_CONFIG no está configurada.")

# Convertir el contenido JSON en un diccionario
firebase_config_dict = json.loads(firebase_config)

# Inicializar Firebase con las credenciales
cred = credentials.Certificate(firebase_config_dict)

#cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://prestamos-c2d1c-default-rtdb.firebaseio.com/'  # Reemplaza esto con la URL de tu base de datos
})

def obtener_clientes(id_asesor):
    ref = db.reference('clientes')
    prestamos_ref = db.reference('prestamos').get()
    movimientos_ref = db.reference('movimientos').get()
    if ref.get() is None:
        ref.set({})

    # Realizamos las consultas específicas desde Firebase para limitar los datos que se obtienen
    clientes_data = ref.order_by_child('id_asesor').equal_to(id_asesor).get()
    prestamos_data = db.reference('prestamos').order_by_child('cliente_id').get()
    movimientos_data = db.reference('movimientos').order_by_child('prestamo_id').get()

    clientes = []
    if clientes_data:
        for cliente_id, data in clientes_data.items():
            totalPrestamos = 0
            prestamosActivos = 0
            cMulta = 0
            
            # Filtrar solo los préstamos del cliente actual
            cliente_prestamos = [p for p in prestamos_data.values() if p.get('cliente_id') == cliente_id]
            
            for prestamo_data in cliente_prestamos:
                semanasPagadas = 0
                
                # Filtrar los movimientos que corresponden a este préstamo
                cliente_movimientos = [m for m in movimientos_data.values() if m.get('prestamo_id') == prestamo_data.get('id')]
                
                for movimiento_data in cliente_movimientos:
                    semanasPagadas += 1
                    if movimiento_data.get('BitMulta') == True:
                        cMulta += 1
                
                totalPrestamos += 1
                if prestamo_data.get('estado') != 'Pagado':
                    prestamosActivos += 1

            # Calificación del cliente basada en el total de préstamos y multas
            CalificacionCliente = ''
            CalifBuena = float(totalPrestamos * 2)
            CalifRegular = float(totalPrestamos * 3)
            CalifMala = float(totalPrestamos * 4)
            CalifGenerada = 0
            if totalPrestamos > 0 and cMulta > 0:
                CalifGenerada = cMulta / totalPrestamos
            
            # Asignar la calificación
            if CalifGenerada <= CalifBuena and CalifGenerada > 0:
                CalificacionCliente = 'Bueno'
            elif CalifGenerada <= CalifRegular and CalifGenerada > 0:
                CalificacionCliente = 'Regular'
            elif CalifGenerada <= CalifMala and CalifGenerada > 0:
                CalificacionCliente = 'Malo'
            else:
                CalificacionCliente = 'Sin Calificación'

            # Agregar los datos del cliente a la lista
            clientes.append({
                'id': cliente_id,
                'nombre': data['nombre'],
                'direccion': data['direccion'],
                'telefono': data['telefono'],
                'id_asesor': data['id_asesor'],
                'totalPrestamos': totalPrestamos,
                'prestamosActivos': prestamosActivos,
                'cMulta': cMulta,
                'calificacionCliente': CalificacionCliente,
            })
        
    return clientes


def agregar_cliente(nombre, direccion, telefono, id_asesor):
    ref = db.reference('clientes')

    # Verifica si el nodo 'clientes' existe
    if ref.get() is None:
        ref.set({})

    # Crea un nuevo cliente en el nodo
    nuevo_cliente_ref = ref.push()  # Crea una nueva referencia única para el cliente
    nuevo_cliente_ref.set({
        'nombre': nombre,
        'direccion': direccion,
        'telefono': telefono,
        'id_asesor': id_asesor
    })
