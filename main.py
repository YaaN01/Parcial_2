import heapq
import json
from datetime import datetime
from typing import List


class Tarea:
    def __init__(self, nombre: str, prioridad: int, fecha_limite: str, dependencias: List["Tarea"] = None):
        self.nombre = nombre
        self.prioridad = prioridad
        self.fecha_limite = datetime.strptime(fecha_limite, "%Y-%m-%d")
        self.dependencias = dependencias if dependencias else []
        self.completada = False

    def __lt__(self, otra_tarea):
        if self.prioridad == otra_tarea.prioridad:
            return self.fecha_limite < otra_tarea.fecha_limite
        return self.prioridad < otra_tarea.prioridad

    def __str__(self):
        # Formato legible para imprimir
        return f"{self.nombre} (Prioridad: {self.prioridad}, Fecha límite: {self.fecha_limite.strftime('%Y-%m-%d')}, Completada: {self.completada})"

    def to_dict(self):
        return {
            "nombre": self.nombre,
            "prioridad": self.prioridad,
            "fecha_limite": self.fecha_limite.strftime("%Y-%m-%d"),
            "dependencias": [dep.nombre for dep in self.dependencias],
            "completada": self.completada
        }

    @classmethod
    def from_dict(cls, data, todas_tareas):
        tarea = cls(data["nombre"], data["prioridad"], data["fecha_limite"])
        tarea.completada = data["completada"]
        tarea.dependencias = [todas_tareas[dep_nombre] for dep_nombre in data["dependencias"]]
        return tarea



class GestorTareas:
    def __init__(self, archivo_tareas="tareas.json"):
        self.tareas = {}
        self.heap = []
        self.archivo_tareas = archivo_tareas
        self.cargar_tareas()

    def agregar_tarea(self, tarea: Tarea):
        if tarea.nombre in self.tareas:
            print(f"La tarea '{tarea.nombre}' ya existe. No se puede agregar una tarea repetida.")
            return

        self.tareas[tarea.nombre] = tarea
        heapq.heappush(self.heap, tarea)
        self.guardar_tareas()
        print(f"Tarea '{tarea.nombre}' agregada exitosamente.")

    def tareas_pendientes(self):
        tareas_ordenadas = sorted(self.heap, key=lambda tarea: (tarea.prioridad, tarea.fecha_limite))
        return [str(tarea) for tarea in tareas_ordenadas]

    def completar_tarea(self, nombre: str):
        if nombre not in self.tareas:
            print(f"Tarea '{nombre}' no encontrada.")
            return

        tarea = self.tareas[nombre]

        # 1. Comprobar si todas las dependencias están completadas
        if not self.comprobar_dependencias_completadas(tarea):
            print(f"No se puede completar la tarea '{nombre}' porque no todas sus dependencias están completadas.")
            return

        # 2. Completar la tarea
        tarea.completada = True
        self.tareas = {k: v for k, v in self.tareas.items() if not v.completada}
        heapq.heapify(self.heap)
        self.guardar_tareas()
        print(f"Tarea '{nombre}' completada y eliminada.")

        # 3. Revisar otras tareas y devolver las que tienen todas sus dependencias completadas
        self.revisar_dependencias_completadas()

    def comprobar_dependencias_completadas(self, tarea: Tarea):
        """Comprueba si todas las dependencias de una tarea están completadas."""
        for dependencia in tarea.dependencias:
            if not dependencia.completada:
                return False
        return True

    def revisar_dependencias_completadas(self):
        """Revisa todas las tareas y muestra las que tienen todas sus dependencias completadas, ordenadas por prioridad."""
        tareas_completadas = []
        
        for tarea in self.tareas.values():
            if self.comprobar_dependencias_completadas(tarea) and not tarea.completada:
                tareas_completadas.append(tarea)

        # Ordenar las tareas por prioridad
        tareas_completadas = sorted(tareas_completadas, key=lambda tarea: (tarea.prioridad, tarea.fecha_limite))

        # Mostrar las tareas que tienen todas sus dependencias completadas
        if tareas_completadas:
            print("Tareas con todas sus dependencias completadas, ordenadas por prioridad:")
            for tarea in tareas_completadas:
                print(f"- {tarea.nombre} (Prioridad: {tarea.prioridad}, Fecha límite: {tarea.fecha_limite.strftime('%Y-%m-%d')})")
        else:
            print("No hay tareas con todas sus dependencias completadas.")

    def siguiente_tarea(self):
        while self.heap:
            tarea = heapq.heappop(self.heap)
            if not tarea.completada:
                heapq.heappush(self.heap, tarea)
                return tarea
        return None


    def tareas_por_fecha_limite(self):
        tareas_ordenadas = sorted(self.heap, key=lambda tarea: tarea.fecha_limite)
        return [str(tarea) for tarea in tareas_ordenadas]

    def guardar_tareas(self):
        data = [tarea.to_dict() for tarea in self.tareas.values()]
        with open(self.archivo_tareas, "w") as f:
            json.dump(data, f, indent=4)

    def cargar_tareas(self):
        try:
            # Leer los datos del archivo JSON
            with open(self.archivo_tareas, "r") as f:
                data = json.load(f)

            # Primero, crea todas las tareas sin asignar dependencias
            todas_tareas = {tarea_data["nombre"]: Tarea(
                tarea_data["nombre"], 
                tarea_data["prioridad"], 
                tarea_data["fecha_limite"], 
                []  # Dependencias vacías por ahora
            ) for tarea_data in data}

            # Luego, asigna las dependencias después de haber creado todas las tareas
            for tarea_data in data:
                tarea = todas_tareas[tarea_data["nombre"]]
                # Asignar las dependencias usando las tareas ya creadas
                tarea.dependencias = [todas_tareas[dep_nombre] for dep_nombre in tarea_data["dependencias"]]

            # Ahora que las dependencias están asignadas, reorganizamos las tareas en el heap
            self.tareas = todas_tareas
            self.heap = [tarea for tarea in self.tareas.values() if not tarea.completada]
            heapq.heapify(self.heap)

        except FileNotFoundError:
            print(f"No se encontró el archivo '{self.archivo_tareas}'.")
