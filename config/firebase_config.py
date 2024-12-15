import firebase_admin
from firebase_admin import credentials, db
from models.cliente import Cliente 
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

    clientes_data = ref.order_by_child('id_asesor').equal_to(id_asesor).get()

    clientes = []
    if clientes_data:
        
        for cliente_id, data in clientes_data.items():
            totalPrestamos = 0
            pretamosActivos = 0 
            cMulta = 0
            if prestamos_ref:
                
                for prestamo_id, prestamo_data in prestamos_ref.items():
                    semanas_id = prestamo_data.get('semanas_id', 0)
                    catalogo_semanas = db.reference('catalogo_semanas').child(semanas_id).get()
                    multa_semanas = float(catalogo_semanas['multa'] if catalogo_semanas else 0)
                    totalMultas = 0
                    semanasPagadas = 0
                    
                    
                    if prestamo_data.get('cliente_id') == cliente_id:
                        if movimientos_ref:
                            for movimiento_id, movimiento_data in movimientos_ref.items():
                                semanasPagadas = semanasPagadas +1
                                if movimiento_data.get('prestamo_id') == prestamo_id:  # Filtrar por prestamo_id
                                    if movimiento_data.get('BitMulta') == True:  # Filtrar por prestamo_id
                                        totalMultas = totalMultas + multa_semanas
                                        cMulta = cMulta +1
                        totalPrestamos = totalPrestamos + 1 
                        if prestamo_data.get('estado') != 'Pagado':
                            pretamosActivos = pretamosActivos+1
             # Agrega el ID del cliente al objeto
            CalificacionCliente=''
            CalifBuena = float( totalPrestamos * 2)
            CalifRegular = float(  totalPrestamos * 3)
            CalifMala =float(  totalPrestamos * 4)
            CalifGenerada = 0
            if totalPrestamos > 0  and cMulta >0:
                CalifGenerada = cMulta /  totalPrestamos
            if CalifGenerada <= CalifBuena and CalifGenerada >0:
                CalificacionCliente = 'Bueno'
            elif CalifGenerada <= CalifRegular and CalifGenerada >0:
                CalificacionCliente = 'Regular'
            elif CalifGenerada <= CalifMala and CalifGenerada >0:
                CalificacionCliente = 'Malo'
            else:
                CalificacionCliente = 'Sin Calificación'


            clientes.append({
                'id':cliente_id,
                'nombre' : data['nombre'],
                'direccion' : data['direccion'],
                'telefono' : data['telefono'],
                'id_asesor' : data['id_asesor'],
                'totalPrestamos' : totalPrestamos,
                'pretamosActivos' : pretamosActivos,
                'cMulta' : cMulta,
                'calificacionCliente' : CalificacionCliente,

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
