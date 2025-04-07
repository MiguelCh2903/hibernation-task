#!/bin/bash
# my_task.sh
# Simulación de tarea con carga moderada de CPU y disco

echo "[$(date)] Iniciando tarea de prueba..."

# 1. Simula carga de CPU
echo "Simulando carga de CPU..."
python3 -c "for _ in range(5_000_000): pass"

# 2. Simula actividad de disco
echo "Escribiendo archivo temporal..."
dd if=/dev/urandom of=/tmp/tarea_test_file bs=1M count=10 status=none

# 3. Espera artificial
echo "Esperando 3 segundos..."
sleep 3

# 4. Limpieza
rm -f /tmp/tarea_test_file

echo "[$(date)] Tarea finalizada."
