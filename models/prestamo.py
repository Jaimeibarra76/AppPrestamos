from firebase_admin import db  # Asegúrate de que la ruta sea correcta

class Prestamo:
    def __init__(self, id, cliente_id, asesor_id, monto, periodo_semanas, fecha_inicio, pago_semanal, multas=None, pagos=None):
        self.id = id
        self.cliente_id = cliente_id
        self.asesor_id = asesor_id
        self.monto = monto
        self.periodo_semanas = periodo_semanas
        self.fecha_inicio = fecha_inicio
        self.pago_semanal = pago_semanal
        self.multas = multas if multas else []
        self.pagos = pagos if pagos else []

    def guardar_en_firestore(self):
        prestamo_ref = db.collection("prestamos").document(self.id)
        prestamo_ref.set({
            "cliente_id": self.cliente_id,
            "asesor_id": self.asesor_id,
            "monto": self.monto,
            "periodo_semanas": self.periodo_semanas,
            "fecha_inicio": self.fecha_inicio,
            "pago_semanal": self.pago_semanal,
            "multas": self.multas,
            "pagos": self.pagos
        })
