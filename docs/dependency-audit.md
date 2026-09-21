# Auditoría de dependencias

El workflow `Codacy CI` ejecuta las pruebas en Python 3.13 y 3.14, envía
la cobertura a Codacy y audita los paquetes instalados con `pip-audit`.
El auditor se instala en un entorno separado para no modificar los paquetes
que se acaban de probar. Cada ejecución conserva `pip-audit.json` como
artefacto, incluso cuando la auditoría falla.

## Excepciones temporales aceptadas el 2026-09-21

`splent_framework==1.7.1` exige exactamente `Flask==3.1.0` y
`python-dotenv==1.0.1`. La versión 1.14.5 del framework, consultada en PyPI
el 2026-09-21, conserva ambas restricciones. Actualizar solo estos dos
paquetes impide resolver la instalación. Se ha decidido conservar SPLENT
con estas excepciones específicas; no equivalen a corregir las vulnerabilidades.

| Aviso | Corrección publicada | Riesgo y condiciones |
| --- | --- | --- |
| [CVE-2025-47278](https://github.com/advisories/GHSA-4grg-w6v8-c28g) | Flask 3.1.1 | La rotación con `SECRET_KEY_FALLBACKS` puede firmar sesiones con una clave antigua. El repositorio no configura esa opción; revisar antes de habilitarla. |
| [CVE-2026-27205](https://github.com/advisories/GHSA-68rp-wp8r-4726) | Flask 3.1.3 | Ciertos accesos a las claves de sesión no añaden `Vary: Cookie`. Puede exponer respuestas personalizadas si un proxy las cachea. La configuración real del proxy de producción no se ha verificado; no cachear respuestas autenticadas y revisar esa configuración. |
| [CVE-2026-28684](https://github.com/advisories/GHSA-mf9w-mj56-hr94) | python-dotenv 1.2.2 | `set_key()`/`unset_key()` pueden seguir enlaces simbólicos al reescribir `.env`. No hay llamadas a esas funciones en el código de la aplicación ni de Rosemary revisado. Restringir la escritura del directorio de configuración y revisar cualquier nueva herramienta que modifique `.env`. |

Solo se excluyen estos tres identificadores mediante `--ignore-vuln`.
Cualquier otro aviso de vulnerabilidad sigue haciendo fallar el job.
Rosemary, instalado en modo editable desde este repositorio, se omite con
`--skip-editable`; sus dependencias instaladas sí se auditan.
No se usa `continue-on-error` ni se desactiva la auditoría.

Revisar las excepciones antes del **2026-10-21**, al actualizar SPLENT o al
cambiar el manejo de sesiones, caché o archivos `.env`, lo que ocurra primero.
Esta fecha es un compromiso de revisión manual, no una caducidad automática.
Cuando SPLENT permita las versiones corregidas:

1. Actualizar Flask a 3.1.3 o posterior y python-dotenv a 1.2.2 o posterior,
   junto con una versión compatible del framework.
2. Eliminar las tres exclusiones de `scripts/audit-dependencies.sh`.
3. Ejecutar `pip check`, las pruebas con MariaDB y la auditoría completa en
   ambas versiones de Python antes de desplegar.

## Guía para estudiar el workflow

- `on`: cuándo se ejecuta (push a `main` y pull requests hacia `main`).
- `jobs`: el trabajo que ejecuta GitHub en una máquina Ubuntu.
- `strategy.matrix`: repite el trabajo con Python 3.13 y 3.14.
- `services`: arranca MariaDB para las pruebas; se elimina al terminar el job.
- `steps`: las tareas, ejecutadas en orden. `uses` invoca una acción preparada
  y `run` ejecuta comandos de terminal.
- `env`: variables que necesita un paso. El token de Codacy viene de `secrets`.

El recorrido es: descargar código → preparar Python → instalar dependencias →
consultar versiones antiguas → ejecutar pruebas y medir cobertura → enviar
cobertura → auditar seguridad → guardar el informe.

La consulta de versiones antiguas es informativa: un paquete desactualizado
no necesariamente tiene vulnerabilidades. La auditoría sí falla si encuentra
avisos no exceptuados. Su código está en `scripts/audit-dependencies.sh` para
que el YAML muestre con claridad las etapas del trabajo.

El informe se guarda aunque la auditoría falle, siempre que se haya generado
y la ejecución no haya sido cancelada. Guardarlo no convierte el fallo en éxito.
