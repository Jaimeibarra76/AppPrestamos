from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from firebase_admin import db

from datetime import datetime, timedelta
import locale

prestamos_bp = Blueprint('prestamos', __name__)



@prestamos_bp.route('/ver_prestamos')
def ver_prestamos():
    # Obtener la lista de préstamos de Firebase
    prestamos_ref = db.reference('prestamos').order_by_child('cliente_id').get()  # Suponiendo que el ID del asesor se guarda en la sesión
    clientes_ref = db.reference('clientes').order_by_child('id_asesor').get()  # Suponiendo que el ID del asesor se guarda en la sesión
    movimientos_ref = db.reference('movimientos').order_by_child('prestamo_id').get()
    catalogo_semanas_ref = db.reference('catalogo_semanas').get()
    # Crear un diccionario con las claves de clientes mapeadas a sus nombres
    clientes = {cliente_key: cliente_data['nombre'] for cliente_key, cliente_data in clientes_ref.items()}

    prestamos = []
      # Lista para almacenar los préstamos formateados

    if prestamos_ref:
        for prestamo_id, prestamo_data in prestamos_ref.items():
            cliente_id = prestamo_data.get('cliente_id')
            cliente_nombre = clientes.get(cliente_id, 'Desconocido')  # Obtén el nombre del cliente de los datos precargados
            
            semanas_id = prestamo_data.get('semanas_id', 0)
            catalogo_semanas = catalogo_semanas_ref.get(semanas_id, {})
            multa_semanas = float(catalogo_semanas.get('multa', 0))
            semanas = catalogo_semanas.get('semanas', 0)

            movimiento = []  # Para almacenar los movimientos asociados
            totalMultas = 0
            semanasPagadas = 0
            totalPagado = 0

            # Filtramos los movimientos solo para el préstamo actual
            if movimientos_ref:
                for movimiento_id, movimiento_data in movimientos_ref.items():
                    if movimiento_data.get('prestamo_id') == prestamo_id:
                        semanasPagadas += 1  # Sumar las semanas pagadas
                        if movimiento_data.get('BitMulta') == True:  # Si tiene multa
                            movimiento.append({
                                'id': movimiento_id
                            })
                            totalMultas += multa_semanas  # Acumular la multa
                            totalPagado += float(movimiento_data.get('monto', 0)) - multa_semanas  # Resta de multa al total pagado
                        else:
                            totalPagado += float(movimiento_data.get('monto', 0))  # Si no tiene multa, acumula el monto

            # Agregar los datos procesados del préstamo a la lista
            prestamos.append({
                'id': prestamo_id,
                'cliente': cliente_nombre,
                'monto': prestamo_data.get('monto', 0),
                'montoCMulta': prestamo_data.get('montoCMulta', 0),
                'semanas': semanas,
                'estado': prestamo_data.get('estado', 'Desconocido'),
                'CMulta': len(movimiento),  # Número de movimientos con multa
                'TotalMulta': totalMultas,
                'SemanasPagadas': semanasPagadas,
                'totalPagado': totalPagado
            })

    return render_template('ver_prestamos.html', prestamos=prestamos)



@prestamos_bp.route('/agregar_prestamo', methods=['GET', 'POST'])
def agregar_prestamo():
    if request.method == 'POST':
        cliente_id = request.form['cliente_id']
        semanas_id = request.form['semanas']
        monto = float(request.form['monto'])
        pago = float(request.form['pago'])
        fecha = request.form['fecha']

        # Obtener la cantidad de semanas desde el catálogo de semanas usando semanas_id
        catalogo_semanas = db.reference('catalogo_semanas').child(semanas_id).get()
        cantidad_semanas = catalogo_semanas['semanas'] if catalogo_semanas else 0
        fecha_str = datetime.strptime(fecha, '%Y-%m-%d').date()
        # Fecha de inicio (fecha actual)
        fecha_inicio = fecha_str
        
        # Calcular la fecha de término sumando la cantidad de semanas a la fecha de inicio
        fecha_termino = fecha_inicio + timedelta(weeks=int(cantidad_semanas))

        # Lógica para agregar el préstamo en Firebase
        nuevo_prestamo = {
            'cliente_id': cliente_id,
            'semanas_id': semanas_id,
            'monto': monto,
            'pagoxSemana': pago,
            'montoCMulta': monto,
            'estado': 'Activo',
            'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),  # Guardar como string
            'fecha_termino': fecha_termino.strftime('%Y-%m-%d')  # Guardar como string # Puedes agregar más campos según sea necesario
        }

        # Agregar el nuevo préstamo a Firebase Realtime Database
        db.reference('prestamos').push(nuevo_prestamo)
        flash('Préstamo agregado exitosamente', 'success')
        return redirect(url_for('prestamos.ver_prestamos'))  # Redirige a la vista de préstamos
    catalogo_semanas = db.reference('catalogo_semanas').get() 
    # Obtener la lista de clientes para mostrar en el formulario
    clientes = db.reference('clientes').get()
    return render_template('agregar_prestamo.html', clientes=clientes ,catalogo_semanas=catalogo_semanas)


@prestamos_bp.route('/ver_prestamos_cliente/<cliente_id>')
def ver_prestamos_cliente(cliente_id):
    # Obtener la lista de préstamos de Firebase
    prestamos_ref = db.reference('prestamos').order_by_child('cliente_id').get()  # Suponiendo que el ID del asesor se guarda en la sesión
    clientes_ref = db.reference('clientes').order_by_child('id_asesor').get()  # Suponiendo que el ID del asesor se guarda en la sesión
    movimientos_ref = db.reference('movimientos').order_by_child('prestamo_id').get()
    cliente_ref = db.reference('clientes').child(cliente_id).get()
    clientes = {cliente_key: cliente_data['nombre'] for cliente_key, cliente_data in clientes_ref.items()}
    cliente_nombre = cliente_ref.get('nombre')

    prestamos = []  # Lista para almacenar los préstamos del cliente específico

    if prestamos_ref:
        for prestamo_id, prestamo_data in prestamos_ref.items():
            semanas_id = prestamo_data.get('semanas_id', 0)
            catalogo_semanas = db.reference('catalogo_semanas').child(semanas_id).get()
            multa_semanas = float(catalogo_semanas['multa'] if catalogo_semanas else 0)
            semanas = (catalogo_semanas['semanas'] if catalogo_semanas else 0)
            movimiento = []
            totalMultas = 0
            semanasPagadas = 0
            totalPagado = 0
            if movimientos_ref:
                for movimiento_id, movimiento_data in movimientos_ref.items():
                    semanasPagadas = semanasPagadas +1
                    if movimiento_data.get('prestamo_id') == prestamo_id: 
                        totalPagado = totalPagado + float(movimiento_data.get('monto',0)) - multa_semanas # Filtrar por prestamo_id
                        if movimiento_data.get('BitMulta') == True:  # Filtrar por prestamo_id
                            movimiento.append({
                                'id': movimiento_id
                            })
                            totalMultas = totalMultas + multa_semanas
            if prestamo_data.get('cliente_id') == cliente_id:  # Filtrar por el cliente_id
                prestamos.append({
                    'id': prestamo_id,
                    'cliente': cliente_nombre,
                    'monto': prestamo_data.get('monto', 0),
                    'montoCMulta': prestamo_data.get('montoCMulta', 0),
                    'semanas': semanas,
                    'estado': prestamo_data.get('estado', 'Desconocido'),
                    'CMulta': len(movimiento),
                    'TotalMulta': totalMultas,
                    'SemanasPagadas':semanasPagadas,
                    "totalPagado":totalPagado,
                    
                })

    return render_template('ver_prestamos_cliente.html', prestamos=prestamos, cliente_id=cliente_id, nombreCliente = cliente_nombre)

@prestamos_bp.route('/ver_movimientos/<prestamo_id>')
def ver_movimientos(prestamo_id):
    try:
        locale.setlocale(locale.LC_TIME, 'es_US.UTF-8')  # Intenta usar español de EE.UU.
    except locale.Error:
        
        locale.setlocale(locale.LC_TIME, 'C') 
    #locale.setlocale(locale.LC_TIME, 'es_ES.utf8') 
     # Obtener los datos del préstamo específico
    prestamo_ref = db.reference(f'prestamos/{prestamo_id}')
    prestamo_data = prestamo_ref.get() or {}

    cliente_id = prestamo_data.get('cliente_id')
    cliente_ref = db.reference('clientes').child(cliente_id).get()
    cliente_nombre = cliente_ref.get('nombre')

    # Guardar semanas y cantidad en variables con valores predeterminados si no existen
    cantidad = float(prestamo_data.get('monto'))
    cantidadPagar = float(prestamo_data.get('monto')) * float(prestamo_data.get('pagoxSemana'))
    cantidadCmulta = float(prestamo_data.get('montoCMulta'))
    semanas_id = prestamo_data.get('semanas_id', 0)
    pagoxSemana = float(prestamo_data.get('pagoxSemana', 0))
    estado = prestamo_data.get('estado','Desconocido')
    catalogo_semanas = db.reference('catalogo_semanas').child(semanas_id).get()
    cantidad_semanas = catalogo_semanas['semanas'] if catalogo_semanas else 0
    multa_semanas = float(catalogo_semanas['multa'] if catalogo_semanas else 0)
    cantidadPagar = pagoxSemana * cantidad_semanas

    fecha_inicio_obj = datetime.strptime(prestamo_data['fecha_inicio'], '%Y-%m-%d')
    fecha_termino_obj = datetime.strptime(prestamo_data['fecha_termino'], '%Y-%m-%d')

    # Formatear las fechas al estilo "24 de marzo del 2025"
    fecha_inicio_formateada = fecha_inicio_obj.strftime('%d de %B del %Y')
    fecha_termino_formateada = fecha_termino_obj.strftime('%d de %B del %Y')

    if not prestamo_ref:
        # Si no se encuentra el préstamo, redirigir o manejar el error
        return "Préstamo no encontrado", 404
    
    # Obtener la referencia a los movimientos del préstamo
    movimientos_ref = db.reference('movimientos').get()

    movimientos = []  # Lista para almacenar los movimientos del préstamo específico
    es_lunes = datetime.now().weekday() == 0

    
    

    # Mensaje de depuración
    totalPen = cantidadPagar ##float(prestamo_data.get('monto'))
    TotalPMulta = float(prestamo_data.get('monto'))

    if movimientos_ref:
        multaTotal = 0
        for movimiento_id, movimiento_data in movimientos_ref.items():
            
            aplicaMulta = 0  # Mostrar datos del movimiento
            

            if movimiento_data.get('prestamo_id') == prestamo_id: 
                if movimiento_data.get('BitMulta') == True:
                    aplicaMulta = multa_semanas
                    multaTotal = multaTotal + multa_semanas
                totalCMulta = TotalPMulta + multaTotal
                totalPen =  totalPen - float(movimiento_data.get('monto', 0)) + aplicaMulta
                fecha_raw = movimiento_data.get('fechaPago', None )
                if fecha_raw:  # Solo entra si tiene valor y no es None o vacío
                    if isinstance(fecha_raw, str):
                        try:
                            # Si viene en formato ISO (por ejemplo "2025-10-11T00:00:00")
                            fecha_convertida = datetime.fromisoformat(fecha_raw)
                        except ValueError:
                            try:
                                # Si viene en formato "YYYY-MM-DD"
                                fecha_convertida = datetime.strptime(fecha_raw, '%Y-%m-%d')
                            except ValueError:
                                # Si no coincide con ningún formato, deja la fecha como None
                                fecha_convertida = None
                else:
                    fecha_convertida = None
                  # Filtrar por prestamo_id
                movimientos.append({
                    'id': movimiento_id,
                    'monto': float(movimiento_data.get('monto', 0)) - aplicaMulta,
                    'multa': aplicaMulta,
                    'montoCmulta': float(movimiento_data.get('monto', 0)),
                    'totalPen': totalPen,
                    'totalCMulta': float(totalCMulta),
                    'semana': movimiento_data.get('semana', 0),
                    'fechaPago': fecha_convertida,     
                    'BitMulta' : bool(movimiento_data.get('BitMulta')) 
                })

 # Mostrar movimientos encontrados

    return render_template('ver_movimientos.html', movimientos=movimientos, prestamo_id=prestamo_id, prestamo=prestamo_ref, Cantidad = cantidad, 
                           Semanas=cantidad_semanas,es_lunes= es_lunes, fecha_inicio = fecha_inicio_formateada, fecha_termino = fecha_termino_formateada,
                           multa_semanas=multa_semanas,cantidadCmulta = cantidadCmulta, estado= estado, PagoxSemana=pagoxSemana, CantidadPagar=cantidadPagar ,cliente_nombre=cliente_nombre)

@prestamos_bp.route('/agregar_pago/<prestamo_id>', methods=['GET', 'POST'])
def agregar_pago(prestamo_id):
    if request.method == 'POST':
       
        movimientos_ref = db.reference('movimientos').get()
        prestamo_ref = db.reference(f'prestamos/{prestamo_id}')
        prestamo_data = prestamo_ref.get() or {}
        semanas_id = prestamo_data.get('semanas_id', 0)
         #float(prestamo_data.get('monto', 0))
        pagoxSemana = float(prestamo_data.get('pagoxSemana', 0))
        pagoxSemana = float(request.form.get('monto', 0))
        aplicarMulta = request.form.get('aplicar_Multa')
        fechaPago = request.form.get('fechaPago')
        catalogo_semanas = db.reference('catalogo_semanas').child(semanas_id).get()
        multa_semanas = float(catalogo_semanas['multa'] if catalogo_semanas else 0)
        semanas = int(catalogo_semanas['semanas'])
        montoPrestamo =  pagoxSemana * semanas
        movimientos = [] 
        movimientosMulta = []
        sumaPagado=0 # Lista para almacenar los movimientos del préstamo específico
        es_lunes = datetime.now().weekday() == 0
        if movimientos_ref:
            for movimiento_id, movimiento_data in movimientos_ref.items():
                if movimiento_data.get('prestamo_id') == prestamo_id:  # Filtrar por prestamo_id
                    movimientos.append({
                        'id': movimiento_id
                    })
                    if(aplicarMulta =='Aplica'):
                        sumaPagado =  sumaPagado + float(movimiento_data.get('monto',0)) - multa_semanas
                    else:
                       sumaPagado =  sumaPagado + float(movimiento_data.get('monto',0)) 
                # if movimiento_data.get('BitMulta') == True:  # Filtrar por prestamo_id
                #     movimientosMulta.append({
                #         'id': movimiento_id
                #     })
        monto = pagoxSemana
        
        if prestamo_data:
            if(aplicarMulta =='Aplica'):
                montoCMulta = float(prestamo_data.get('montoCMulta',0)) + multa_semanas
                prestamo_ref.update({
                    'montoCMulta' : montoCMulta
                })
        # Obtener la cantidad de movimientos registrados
        cantidad_movimientos = len(movimientos)
        # cantidad_Multa = len(movimientosMulta)>0 if True else False 


        semana = cantidad_movimientos + 1
        montoCMulta = float(monto) + multa_semanas   
        sumaPagado2 = sumaPagado + float(monto)   

        monto2= 0
        if(es_lunes):
            monto2 = monto
        else :
            if(aplicarMulta =='Aplica'):
                monto2 = montoCMulta
            else:
                monto2=monto


        bitMulta = False
        if(es_lunes):
            bitMulta = False
        else:
            if(aplicarMulta =='Aplica'):
                bitMulta = True
            else:
                bitMulta = False
        # Guardar el nuevo movimiento en Firebase

        if(sumaPagado2 == montoPrestamo):
            if prestamo_data:
                    prestamo_ref.update({
                        'estado' : 'Pagado'
                    })

        if(cantidad_movimientos<= semanas ):
            db.reference('movimientos').push({
                'prestamo_id': prestamo_id,
                'monto': monto2,
                'semana': semana,
                'fechaPago': fechaPago,
                "BitMulta" : bitMulta
            })
            if(semana == semanas):
                if prestamo_data:
                    prestamo_ref.update({
                        'estado' : 'Pagado'
                    })
        else:
            if prestamo_data:
                prestamo_ref.update({
                    'estado' : 'Pagado'
                })
        return redirect(url_for('prestamos.ver_movimientos', prestamo_id=prestamo_id))

    return render_template('agregar_pago.html', prestamo_id=prestamo_id)


@prestamos_bp.route('/catalogo_semanas', methods=['GET', 'POST'])
def catalogo_semanas():
    if request.method == 'POST':
        # Obtener los datos del formulario
        semanas = request.form.get('semanas')
        multa = request.form.get('multa')

        # Validar que los datos sean correctos
        if semanas and multa:
            catalogo_ref = db.reference('catalogo_semanas')
            nuevo_registro = catalogo_ref.push({
                'semanas': int(semanas),
                'multa': float(multa)
            })
            flash('Registro agregado exitosamente', 'success')
        else:
            flash('Por favor, completa todos los campos', 'danger')

    # Obtener los registros existentes
    registros = db.reference('catalogo_semanas').get() or {}

    return render_template('semanas.html', registros=registros)


@prestamos_bp.route('/eliminar_prestamo/<prestamo_id>', methods=['GET'])
def eliminar_prestamo(prestamo_id):
    # Eliminar el cliente con el ID proporcionado
    try:
        # Obtener la referencia al cliente específico en la base de datos
        prestamos_ref = db.reference(f'prestamos/{prestamo_id}')
        
        # Eliminar el cliente de la base de datos
        prestamos_ref.delete()
        

    except Exception as e:
        flash(f'Error al eliminar el cliente: {str(e)}', 'danger')
    
    return redirect(url_for('prestamos.ver_prestamos'))

@prestamos_bp.route('/eliminar_movimiento/<movimiento_id>,<prestamo_id>', methods=['GET'])
def eliminar_movimiento(movimiento_id, prestamo_id):

    # Eliminar el cliente con el ID proporcionado
    try:
        # Obtener la referencia al cliente específico en la base de datos
        prestamos_ref = db.reference(f'movimientos/{movimiento_id}')
        
        # Eliminar el cliente de la base de datos
        prestamos_ref.delete()
        

    except Exception as e:
        flash(f'Error al eliminar el cliente: {str(e)}', 'danger')
    
    return redirect(url_for('prestamos.ver_movimientos', prestamo_id=prestamo_id))

