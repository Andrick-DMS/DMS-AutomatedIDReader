# DMS-AutomatedIDReader
Sistema de autocompleté de formularios de invitados en Lenel, con lector de cedulas.
La versión v1, cuenta con las siguientes caracteristicas:

Leer datos desde cédulas costarricenses mediante lector físico.

Decodificar correctamente la información contenida.

Reconocer los campos relevantes (número de cédula, nombre, apellidos, etc.).

Escribir automáticamente los datos en los formularios del sistema Lenel.

Implementación de un sistema de licenciamiento para el uso del software.

Generador de instaladores que integre el sistema de licencias.

Control de versiones para facilitar el mantenimiento y actualizaciones del software.

Sistema de registros (logs) para obtener trazabilidad más específica y detallada de cada proceso.


La versión 2 fue la base de la 3, pero por motivos de desarrollo fue mejor cargar la 3 directamente.

La versión v3, cuenta con las siguientes caracteristicas:
Lectura y Decodificación del QR
El sistema detecta automáticamente el puerto COM del lector.
Se decodifica el QR con algoritmo XOR según estructura oficial del TSE.
Se extraen datos personales: nombre, apellidos, cédula, sexo, fecha de nacimiento y de expiración.
Autocompletado de Formularios
Se simula escritura mediante pyautogui para ingresar los datos en aplicaciones como Lenel.
Compatible con configuraciones personalizadas.
Sistema de Licenciamiento
El sistema solicita una licencia en el primer inicio.
La licencia se almacena localmente en caché.
Registro en logs de activación por cliente y fecha.
Sistema de Configuraciones
Carpeta configs/ contiene distintas configuraciones personalizadas.
Cada configuración permite definir:
Campos a llenar
Orden de llenado
Cantidad de tabulaciones por campo
Configuración activa puede ser seleccionada mediante interfaz gráfica.
Posibilidad de crear nuevas configuraciones desde la bandeja del sistema.
Interfaz de Usuario y Accesibilidad
El sistema corre en segundo plano y se gestiona desde el ícono en la bandeja del sistema.
Se puede:
Salir del servicio
Cambiar configuración activa
Crear nuevas configuraciones
Generador de Instaladores
Se cuenta con un Dashboard independiente para generar instaladores con:
Licencia única para cada cliente
Archivos empaquetados en un ZIP
Registro de clientes y licencias emitidas
La versión v3.2, cuenta con las siguientes caracteristicas:
Presenta la misma funcionalidad, solo se le agrego el logo y el icon de la empresa para su distribución
