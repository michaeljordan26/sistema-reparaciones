"""Este microservicio no trae datos de prueba propios: los diagnósticos, reparaciones y
garantías se generan al recorrer el flujo (colección de Postman MS4 o el frontend),
porque dependen de órdenes reales en ms-ordenes."""


def run():
    print("Datos de prueba cargados correctamente. (MS4 se llena con el flujo de trabajo)")


if __name__ == "__main__":
    run()
