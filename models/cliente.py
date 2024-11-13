# models/cliente.py

class Cliente:
    def __init__(self, nombre, direccion, telefono, id_asesor):
        self.nombre = nombre
        self.direccion = direccion
        self.telefono = telefono
        self.id_asesor = id_asesor

    def to_dict(self):
        return {
            'nombre': self.nombre,
            'direccion': self.direccion,
            'telefono': self.telefono,
            'id_asesor': self.id_asesor
        }
