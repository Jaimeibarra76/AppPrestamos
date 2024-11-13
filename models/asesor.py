from firebase_admin import db # Asegúrate de que la ruta sea correcta

class Asesor:
    def __init__(self, id, nombre, correo, clientes_asignados=None, rol="asesor"):
        self.id = id
        self.nombre = nombre
        self.correo = correo
        self.clientes_asignados = clientes_asignados if clientes_asignados else []
        self.rol = rol

    def guardar_en_firestore(self):
        asesor_ref = db.collection("asesores").document(self.id)
        asesor_ref.set({
            "nombre": self.nombre,
            "correo": self.correo,
            "clientes_asignados": self.clientes_asignados,
            "rol": self.rol
        })
    
    @classmethod
    def obtener_asesores(cls):
        ref = db.reference('asesores')  # Suponiendo que los asesores están en la ruta 'asesores'
        asesores_data = ref.get()
        asesores = []
        for asesor_id, asesor_info in asesores_data.items():
            asesor = cls(
                id=asesor_id,
                nombre=asesor_info['nombre']
            )
            asesores.append(asesor)
        return asesores