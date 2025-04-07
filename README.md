# Proyecto de Suspensión / Hibernación de Tareas Rutinarias

Este proyecto permite suspender / hibernar el sistema para luego despertar y reanudar la ejecución de dichas tareas rutinarias.

## Requisitos

- Git
- Bash
- Python 3
- Permisos para ejecutar scripts con `sudo`

## Instalación

1. Clona el repositorio:

   ```bash
   git clone <URL_DEL_REPOSITORIO>
   ```

2. Crea y activa el entorno virtual:

   ```bash
   uv venv
   source venv/bin/activate
   ```

3. Sincroniza las dependencias:

   ```bash
   uv sync
   ```

4. Otorga permisos de ejecución a los scripts:

    ```bash
    chmod +x ./scripts/*.sh
    chmod +x ./src/*.py
    ```

## Ejecución de Calibración

Para analizar los tiempos de ejecución, incluyendo el tiempo de la tarea y el overhead después de la suspensión, ejecuta:

```bash
sudo ./scripts/run_calibration.sh
```

Este script utiliza el siguiente comando para calibrar los parámetros del sistema:

```bash
#!/bin/bash
# Script to run calibration for task and suspend timing

set -euo pipefail

# Configurable parameters
MODE="mem"                        # "mem" for suspend-to-RAM, "disk" for hibernation
TASK_CMD="./scripts/my_task.sh"
LOG_FILE="./logs/calibration_log.csv"

# Run calibration
echo "Running calibration..."
python3 ./src/calibrate_params.py \
    --mode "$MODE" \
    --task-cmd "$TASK_CMD" \
    --log-file "$LOG_FILE"
```

## Benchmark Programado

Para evaluar el comportamiento del sistema con la ejecución programada de la tarea, se utiliza el script de benchmark. Este ejecuta el programa `scheduled_benchmark.py` que planifica la tarea de ejemplo para el minuto más próximo, espera un breve periodo después de la ejecución antes de hibernar y despierta justo a tiempo para prepararse para la siguiente ejecución.

Los resultados del benchmark se registran en un archivo de log, en el cual se pueden visualizar tiempos clave como el inicio programado, el inicio real de la tarea, la duración de la tarea y los tiempos relacionados con la suspensión y reanudación. Para ver el detalle completo de las columnas, consulta el archivo de log.

### Ejecución del Benchmark

Para iniciar el benchmark, ejecuta el siguiente comando:

```bash
sudo ./scripts/run_benchmark.sh
```

### Código del Script de Benchmark

```bash
#!/bin/bash
# Script to run scheduled benchmark

set -euo pipefail

# Parameters
MODE="mem"
PERIOD=60
ACTIVE_DELAY=5.0
PRE_WAKEUP_DELAY=6.0
ITERATIONS=3
TASK_CMD="./scripts/my_task.sh"
LOG_FILE="./logs/scheduled_benchmark2.csv"

# Run benchmark script in src/
echo "Starting scheduled benchmark..."
python3 ./src/scheduled_benchmark.py \
    --mode "$MODE" \
    --period "$PERIOD" \
    --active-delay "$ACTIVE_DELAY" \
    --pre-wakeup-delay "$PRE_WAKEUP_DELAY" \
    --iterations "$ITERATIONS" \
    --task-cmd "$TASK_CMD" \
    --log-file "$LOG_FILE"
```

### NOTAS ADICIONALES

- Los parámetros son calculados basándose en el benchmark. Se utiliza `rtcwake` para la hibernación.
  
- Se recomienda comenzar con el modo mem (S3) y, si el equipo lo soporta, probar también el modo disk (S4) para la hibernación.
  
- Revisa el archivo de log para analizar en detalle los tiempos medidos en cada iteración.

## Implementación con systemd

Para integrar la ejecución de la rutina en el sistema, se utiliza systemd. A continuación se describen los pasos para copiar y configurar los archivos de servicio y timer.

### Copiado de Archivos

1. Copia los archivos `routine-task.service` y `routine-task.timer` que se encuentran en la carpeta `scripts/systemd` a la carpeta `/etc/systemd/system` con permisos de superusuario:

   ```bash
   sudo cp scripts/systemd/routine-task.service /etc/systemd/system/
   sudo cp scripts/systemd/routine-task.timer /etc/systemd/system/
   ```

2. Copia el archivo `routine-wrapper.sh` a la carpeta `/usr/local/bin`:

   ```bash
   sudo cp scripts/systemd/routine-wrapper.sh /usr/local/bin/
   ```

### Contenido de routine-task.service

```ini
[Unit]
Description=Run routine task and suspend to S3 (memory) mode
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/routine_wrapper.sh

[Install]
WantedBy=multi-user.target
```

### Contenido de routine-task.timer

```ini
[Unit]
Description=Timer to execute routine task every minute

[Timer]
OnCalendar=*-*-* *:*:00
Persistent=true

[Install]
WantedBy=timers.target
```

## Configuración e Inicio del Timer

Después de copiar los archivos, es necesario recargar la configuración de systemd y habilitar/iniciar el timer. Ejecuta los siguientes comandos:

1. Recarga la configuración de systemd:

    ```bash
   sudo systemctl daemon-reload
   ```

2. Habilita el timer para que se inicie automáticamente en el arranque:

    ```bash
   sudo systemctl enable routine-task.timer
   ```

3. Inicia el timer:

    ```bash
   sudo systemctl start routine-task.timer
   ```

Comando adicional:

Si deseas verificar el estado del timer, puedes utilizar:

```bash
sudo systemctl status routine-task.timer
```

---

## Documentación técnica

### Overview de ACPI y Estados de Energía

El `Advanced Configuration and Power Interface (ACPI)` es un estándar abierto diseñado para permitir que los sistemas operativos gestionen de manera eficiente la configuración del hardware y el consumo de energía de los dispositivos.

ACPI define varios estados de energía que permiten optimizar el consumo energético del sistema. Estos se clasifican principalmente en `estados globales (Gx)` y `estados de suspensión (Sx)`.

### Tabla de Estados ACPI

| **Estado Global (Gx)**     | **Estado de Suspensión (Sx)** | **Descripción**                                                                                                                                               |
|----------------------------|-------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **G0** (Funcionamiento)    | S0                            | El sistema está completamente encendido y operativo.                                                                                                          |
| **G1** (Suspensión)        | S1                            | Suspensión ligera. CPU en reposo, pero con estado y caché preservados.                                                                                        |
|                            | S2                            | Similar a S1, pero con más componentes apagados, incluida la CPU.                                                                                             |
|                            | S3                            | "Suspensión a RAM": el sistema guarda el estado en RAM y apaga casi todos los componentes.                                                                   |
|                            | S4                            | "Hibernación": el contenido de la RAM se guarda en disco y el sistema se apaga casi completamente.                                                           |
| **G2** (Apagado suave)     | S5                            | Apagado completo del sistema, pero con capacidad de encendido remoto (Wake-on-LAN, etc.).                                                                     |
| **G3** (Apagado mecánico)  | —                             | Desconexión total de energía; solo es posible encenderlo mediante una acción física (por ejemplo, presionar un botón físico de encendido).                   |

En sistemas Linux, estos estados son utilizados mediante interfaces como `/sys/power/state`, `systemctl suspend`, `systemctl hibernate`, entre otros. La correcta implementación de ACPI por parte del firmware y el kernel es esencial para garantizar un comportamiento estable y eficiente durante transiciones de energía.

> Este overview es la base para entender cómo una rutina de hibernación se integra con el sistema operativo y el hardware a través de ACPI.

---

## Resumen de los temporizadores en systemd

Los temporizadores en systemd (`.timer`) son unidades que permiten programar la ejecución de servicios (`.service`) en momentos específicos o tras ciertos intervalos, ofreciendo una alternativa moderna a las tareas programadas con `cron`.

### Tipos de temporizadores

Existen dos tipos principales de temporizadores en systemd:

- **Temporizadores en tiempo real (realtime timers):** Se activan en eventos de calendario específicos, utilizando la opción `OnCalendar=`. Por ejemplo, para ejecutar una tarea diariamente a las 3 AM:

  ```ini
  [Timer]
  OnCalendar=*-*-* 03:00:00
  ```

- **Temporizadores monotónicos (monotonic timers):** Se activan después de un período relativo a un punto de inicio variable, como el arranque del sistema. Ejemplos incluyen:

    ```ini
    [Timer]
    OnBootSec=5min          # 5 minutos después del arranque
    OnUnitActiveSec=1h      # 1 hora después de que la unidad asociada esté activa
    ```

## Descripción general de `rtcwake`

El comando `rtcwake` en Linux permite gestionar los estados de suspensión del sistema y programar su reactivación en un momento específico. Utiliza la funcionalidad del reloj en tiempo real (RTC) de la placa base para establecer alarmas que despiertan el sistema después de un período determinado o en una hora específica.

### Modos de suspensión

- **standby**: :Este es el modo por defecto, ahorra poca energía, pero la transición a un sistema en funcionamiento es muy rápida (ACPI state S1)
- **mem**: Suspende a RAM y ofrece un ahorro significativo de energía (ACPI state S3)
- **disk**: Suspende a disco. Este estado ofrece el mayor ahorro de energía (ACPI state S4)

### Uso básico

```bash
sudo rtcwake -m [modo] -s [segundos]
```
