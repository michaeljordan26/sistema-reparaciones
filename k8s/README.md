# Sprint 6 – Despliegue en Kubernetes

El mismo sistema de Docker Compose, desplegado en el **Kubernetes de Docker Desktop**.

| Archivo | Qué crea |
|---|---|
| `00-namespace.yaml` | Namespace `taller`, que agrupa todo |
| `01-configmap.yaml` | ConfigMap `taller-config`: direcciones entre servicios (no secretas) |
| `02-frontend-nginx.yaml` | ConfigMap con la configuración de nginx para Kubernetes |
| `11-ms-usuarios.yaml` … `17-ms-reportes.yaml` | Por microservicio: **StatefulSet** de PostgreSQL con su disco + **Deployment** de la API + 2 **Services** |
| `20-frontend.yaml` | Deployment de la interfaz (2 réplicas) + Service **NodePort 30173** |
| Secret `taller-secretos` | Lo crea `k8s-iniciar.bat` desde el `.env` (claves fuera de GitHub) |

En total: 1 namespace, 2 ConfigMaps, 1 Secret, 7 StatefulSets, 8 Deployments y 15 Services.

## Desplegar

1. Docker Desktop → Settings → Kubernetes → **Enable Kubernetes** (tipo kubeadm) → Apply & restart.
2. `kubectl get nodes` debe mostrar `docker-desktop   Ready`.
3. Doble clic en **`k8s-iniciar.bat`**. Abre http://localhost:30173

## Demostración en clase

| Qué mostrar | Comando |
|---|---|
| Todos los pods | `kubectl get pods -n taller` |
| Servicios y el NodePort | `kubectl get svc -n taller` |
| Discos de las bases | `kubectl get pvc -n taller` |
| **Escalar** a 3 copias | `kubectl scale deployment ms-ordenes --replicas=3 -n taller` |
| **Autorreparación**: borrar un pod y ver que vuelve | `kubectl delete pod -l app=ms-clientes -n taller` y luego `kubectl get pods -n taller -w` |
| Registros de un servicio | `kubectl logs -f deployment/ms-ordenes -n taller` |
| Swagger de un servicio | `kubectl port-forward svc/ms-ordenes 8003:8003 -n taller` y abrir http://localhost:8003/docs |
| Borrar todo | `k8s-detener.bat` (o `kubectl delete namespace taller`) |

## Docker Compose vs. Kubernetes

| | Docker Compose | Kubernetes |
|---|---|---|
| Si un contenedor se cae | `restart: on-failure` | El Deployment crea otro pod automáticamente |
| Escalar | Manual, un contenedor por servicio | `kubectl scale` reparte la carga entre réplicas |
| Salud | healthcheck de la base | startup, readiness y liveness probes en cada API |
| Orden de arranque | `depends_on` | initContainer que espera a la base |
| Claves | archivo `.env` | Secret de Kubernetes |
| Datos | volúmenes de Docker | PersistentVolumeClaims del StatefulSet |
