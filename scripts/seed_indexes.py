"""
Seed Azure AI Search indexes with demo documents.
Crea los índices si no existen y sube documentos de muestra para las 3 preguntas demo.
"""

import json
import sys
from pathlib import Path

import requests
from azure.identity import DefaultAzureCredential

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "backend" / "agents"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from config import SEARCH_ENDPOINT

SEARCH_API_VERSION = "2024-07-01"

credential = DefaultAzureCredential()
token = credential.get_token("https://search.azure.com/.default").token
HEADERS = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}

INDEX_SCHEMA = {
    "fields": [
        {"name": "id",           "type": "Edm.String",          "key": True,  "searchable": False},
        {"name": "title",        "type": "Edm.String",          "key": False, "searchable": True,  "retrievable": True},
        {"name": "content",      "type": "Edm.String",          "key": False, "searchable": True,  "retrievable": True},
        {"name": "category",     "type": "Edm.String",          "key": False, "searchable": True,  "retrievable": True, "filterable": True},
        {"name": "url",          "type": "Edm.String",          "key": False, "searchable": False, "retrievable": True},
        {"name": "lastModified", "type": "Edm.DateTimeOffset",  "key": False, "searchable": False, "retrievable": True, "filterable": True},
    ],
    "semantic": {
        "configurations": [{
            "name": "default",
            "prioritizedFields": {
                "titleField": {"fieldName": "title"},
                "prioritizedContentFields": [{"fieldName": "content"}],
            }
        }]
    }
}


DOCUMENTS = {
    "index-politicas": [
        {
            "id": "pol-001",
            "title": "Proceso de Postmortem Blameless — Guía Completa DevOps Days CORP",
            "category": "postmortem",
            "url": "wiki-interno/politicas/postmortem",
            "content": """
# Proceso de Postmortem Blameless — Guía Completa DevOps Days CORP

## Objetivo
El postmortem blameless es el proceso formal de análisis de incidentes de DevOps Days CORP.
Su objetivo es aprender del incidente sin buscar culpables individuales, enfocándose en mejorar
sistemas, procesos, alertas y runbooks. Ningún ingeniero es responsable del incidente; el sistema lo es.

## Cuándo es obligatorio
- Incidentes SEV-1 y SEV-2: postmortem obligatorio dentro de las 48 horas del cierre.
- SEV-3 con impacto relevante en usuarios finales o pérdida de datos: recomendado.
- Outages de más de 15 minutos en el entorno de producción.
- Deploys que requirieron rollback y afectaron a usuarios.

## Estructura del documento de postmortem
1. **Resumen ejecutivo**: qué ocurrió, duración total, impacto cuantificado (usuarios afectados, requests fallidos, pérdida de ingresos estimada).
2. **Timeline detallado**: cronología de eventos con timestamps en UTC. Incluir: primer síntoma detectado, primera alerta disparada, inicio de respuesta, acciones tomadas, resolución, comunicación externa.
3. **Causa raíz (5 Whys)**: análisis sistemático que llega a la causa sistémica, no a la persona. Ejemplo: "¿Por qué cayó el servicio? Porque el deployment aumentó el uso de memoria. ¿Por qué? Porque no había límite de memoria configurado..."
4. **Factores contribuyentes**: condiciones del sistema que permitieron el incidente (falta de tests, alertas insuficientes, documentación desactualizada).
5. **Qué funcionó bien**: monitoreo que detectó rápido, runbooks que funcionaron, comunicación efectiva.
6. **Action items**: tareas concretas, con owner asignado, fecha límite y ticket de Jira. Ejemplo: "Agregar memory limits a todos los deployments del squad — owner: @jperez — fecha: 2025-02-15 — PLAT-1234".

## Principios blameless
- Ningún ingeniero es responsable del incidente; el sistema lo es.
- Las personas tomaron las mejores decisiones posibles con la información disponible en ese momento.
- El foco es en mejorar procesos, alertas y runbooks, no en sancionar conductas.
- Los postmortems se publican en el canal #postmortems de Slack y son accesibles a toda la empresa.
- Los action items tienen prioridad sobre features nuevas; se trackean en el sprint siguiente.

## Plataforma y template
Los postmortems se documentan en Confluence bajo el espacio /DevOps/Postmortems.
Template oficial: https://confluence.devopsdays.corp/postmortem-template
El facilitador completa el template durante o inmediatamente después de la reunión.

## Facilitador y reunión
- Facilitador: on-call manager o tech lead del equipo afectado.
- Duración máxima: 60 minutos.
- Participantes: equipo on-call + stakeholders clave + representante de producto si aplica.
- La reunión NO es para determinar culpables; si el tono se vuelve punitivo, el facilitador debe redirigir.
- Se graba la reunión (con consentimiento) y se archiva en Confluence.

## Seguimiento
Los action items se crean como tickets en Jira proyecto PLAT o en el proyecto del equipo dueño.
El SRE lead revisa el avance de action items en la reunión semanal de operaciones (#weekly-ops).
""",
        },
        {
            "id": "pol-002",
            "title": "Política de On-Call y Rotaciones de Guardia — DevOps Days CORP",
            "category": "on-call",
            "url": "wiki-interno/politicas/on-call",
            "content": """
# Política de On-Call y Rotaciones de Guardia — DevOps Days CORP

## Alcance
Esta política aplica a todos los ingenieros de los squads de producto y plataforma que
participen en rotaciones de guardia para los servicios productivos de DevOps Days CORP.

## Estructura de rotaciones
- Ciclos de 7 días (lunes 09:00 ART a lunes siguiente 09:00 ART).
- Cada squad mantiene: 1 ingeniero primary on-call + 1 ingeniero secondary (backup).
- Las rotaciones se configuran y gestionan en PagerDuty bajo la escalation policy "DevOps Days CORP On-Call".
- El calendario de rotaciones se publica con 4 semanas de anticipación en #on-call-schedule.
- Cambios de turno deben acordarse entre los ingenieros involucrados y notificarse en PagerDuty con al menos 24 hs de anticipación.

## Responsabilidades del ingeniero on-call
- Responder a alertas de PagerDuty dentro del SLA de tiempo de respuesta según severidad.
- Triagear el incidente: confirmar impacto, clasificar severidad, iniciar puente de incidente si es SEV-1/SEV-2.
- Notificar en el canal #incidentes de Slack con el template: "[SEV-X] Descripción corta — investigando".
- Escalar a secondary o a especialistas si no puede resolver dentro del tiempo definido.
- Documentar acciones tomadas en el ticket de PagerDuty o Jira para facilitar el postmortem.

## Compensación de guardia
- Guardia activa 9x5 (horario laboral): 0.5x hora normal por hora de disponibilidad.
- Guardia 24x7: 1x hora normal por hora de disponibilidad.
- Llamado fuera de horario (SEV-1/SEV-2): mínimo 2 horas de compensación por incidente.
- Más de 3 incidentes SEV-1 en una semana de guardia: compensación adicional según política de RRHH.
- Detalle completo: https://wiki.devopsdays.corp/politicas/guardia-compensacion

## Preparación para la guardia
- El ingeniero que toma la guardia debe leer los últimos 3 postmortems del squad antes de iniciar.
- Verificar accesos: AWS Console, kubectl (prod-us-east-1), PagerDuty, Datadog, ArgoCD, Vault.
- Revisar alertas abiertas o degradaciones conocidas al hacer el handoff.
- Handoff documentado en el canal #on-call-handoff con estado actual de servicios.

## Herramientas requeridas
- PagerDuty móvil instalado y configurado con notificaciones habilitadas.
- VPN activa en caso de necesitar acceso a recursos internos.
- Acceso a runbooks en: https://wiki.devopsdays.corp/runbooks
""",
        },
        {
            "id": "pol-003",
            "title": "Definición de Niveles de Severidad de Incidentes — Clasificación y Respuesta",
            "category": "severidad",
            "url": "wiki-interno/politicas/severidad-incidentes",
            "content": """
# Definición de Niveles de Severidad de Incidentes — DevOps Days CORP

## Propósito
Contar con una clasificación uniforme de severidad permite coordinar la respuesta,
comunicar el impacto a stakeholders y cumplir los compromisos de SLA con clientes.

## Tabla de severidades

### SEV-1 — Crítico (Production Down)
- **Definición**: servicio de producción completamente caído o inaccesible para todos los usuarios. Pérdida de datos en curso. Impacto en ingresos directo y medible.
- **Ejemplos**: API gateway caída, base de datos de producción inaccesible, falla de autenticación total.
- **Tiempo de primera respuesta**: 5 minutos desde alerta.
- **Escalado automático**: si no hay respuesta en 10 minutos, PagerDuty escala al manager y al CTO.
- **Comunicación**: actualización en #incidentes cada 15 minutos. Comunicado externo a clientes si supera 30 minutos.
- **Postmortem**: obligatorio, dentro de las 24 horas del cierre.

### SEV-2 — Alto (Degradación significativa)
- **Definición**: funcionalidad core degradada o no disponible para un subconjunto de usuarios. Workaround posible pero incómodo.
- **Ejemplos**: latencia p99 > 5 segundos, tasa de error > 5%, funcionalidad de pagos degradada.
- **Tiempo de primera respuesta**: 15 minutos desde alerta.
- **Escalado**: si no hay resolución en 1 hora, escalar al tech lead del equipo.
- **Comunicación**: actualización en #incidentes cada 30 minutos.
- **Postmortem**: obligatorio, dentro de las 48 horas del cierre.

### SEV-3 — Medio (Impacto menor)
- **Definición**: funcionalidad secundaria afectada. Workaround disponible. Pequeño porcentaje de usuarios impactados.
- **Ejemplos**: fallo en un job de batch no crítico, dashboard de analytics lento, feature flag no funcionando.
- **Tiempo de primera respuesta**: 2 horas en horario laboral (9:00–18:00 ART).
- **Escalado**: si no hay resolución en 8 horas, escalar al on-call primary.
- **Postmortem**: opcional, recomendado si hubo impacto visible para usuarios.

### SEV-4 — Bajo (Degradación mínima)
- **Definición**: incidente sin impacto visible para usuarios finales. Afecta herramientas internas o ambientes no productivos.
- **Ejemplos**: fallo en pipeline de CI/CD de staging, alerta de capacidad preventiva, degradación en entorno de desarrollo.
- **Tiempo de primera respuesta**: próximo día hábil.
- **Escalado**: ticket en Jira, sin guardia involucrada.
- **Postmortem**: no requerido.

## Clasificación inicial
El ingeniero on-call es responsable de clasificar la severidad inicial al abrir el incidente.
La severidad puede ajustarse durante la investigación si el impacto real difiere.
Ante la duda, clasificar como severidad más alta y ajustar a la baja si corresponde.

## Herramientas
- Alertas gestionadas en PagerDuty: https://devopsdays.pagerduty.com
- Estado de servicios publicado en: https://status.devopsdays.corp
- Canal de comunicación de incidentes: #incidentes en Slack.
""",
        },
        {
            "id": "pol-004",
            "title": "Política de SLA, SLO y Error Budget — Compromisos de Disponibilidad DevOps Days CORP",
            "category": "sla-slo",
            "url": "wiki-interno/politicas/sla-slo-error-budget",
            "content": """
# Política de SLA, SLO y Error Budget — DevOps Days CORP

## Definiciones
- **SLA (Service Level Agreement)**: compromiso contractual externo con clientes. Incumplir el SLA implica penalidades económicas o créditos de servicio.
- **SLO (Service Level Objective)**: objetivo interno más estricto que el SLA. Si el SLO se rompe, actuamos antes de comprometer el SLA.
- **Error Budget**: margen de tiempo o porcentaje de errores permitidos antes de romper el SLO. Se consume con cada incidente o deploy fallido.

## SLOs vigentes (servicios críticos)

| Servicio             | Métrica          | SLO     | SLA externo |
|----------------------|------------------|---------|-------------|
| API Gateway          | Disponibilidad   | 99.95%  | 99.9%       |
| Servicio de Pagos    | Disponibilidad   | 99.99%  | 99.95%      |
| API de Autenticación | Disponibilidad   | 99.9%   | 99.5%       |
| Panel de Usuarios    | Latencia p99     | < 1.5 s | < 3 s       |
| Jobs de Procesamiento| Tasa de éxito    | 99.5%   | 99.0%       |

## Error budget mensual
- Disponibilidad 99.9% → 43.8 minutos de downtime permitido por mes.
- Disponibilidad 99.95% → 21.9 minutos de downtime permitido por mes.
- Disponibilidad 99.99% → 4.4 minutos de downtime permitido por mes.

## Política de congelamiento de deploys (Error Budget Policy)
Cuando el error budget de un servicio cae por debajo del 20% restante en el mes:
1. El equipo debe congelar deploys de features nuevas hasta el mes siguiente o hasta que el presupuesto se recupere.
2. Solo se permiten deploys de fixes de confiabilidad, rollbacks y parches de seguridad.
3. El SRE lead debe aprobar cualquier excepción.
4. Se notifica al equipo de producto con la razón y el plazo estimado de la restricción.

## Seguimiento de SLOs
- Dashboard Grafana: https://grafana.devopsdays.corp/d/slo-prod (actualización en tiempo real).
- Reporte mensual de SLOs enviado automáticamente a #slo-reports cada primer lunes del mes.
- El equipo de producto recibe un resumen mensual en #product-reliability.
- Revisión trimestral de SLOs con el CTO para ajustar objetivos según el crecimiento.

## Cómo se miden los SLOs
Los SLOs se miden con Prometheus + Grafana (métricas de infraestructura) y Datadog APM (métricas de aplicación).
Las alertas de SLO burn rate se configuran en Grafana Alerting con ventanas de 1h, 6h y 24h.
Documentación de burn rate alerts: https://wiki.devopsdays.corp/sre/burn-rate-alerts
""",
        },
        {
            "id": "pol-005",
            "title": "Política de Escalación de Incidentes — Árbol de Escalado y Comunicación",
            "category": "escalacion",
            "url": "wiki-interno/politicas/escalacion",
            "content": """
# Política de Escalación de Incidentes — DevOps Days CORP

## Objetivo
Garantizar que los incidentes críticos lleguen a las personas correctas en el menor tiempo
posible, sin crear fatiga de alertas ni dependencia excesiva de escalaciones innecesarias.

## Principio general
El ingeniero on-call intenta resolver por su cuenta durante el tiempo de respuesta definido.
Si no hay progreso claro, escala proactivamente. Es mejor escalar de más que resolver tarde.
Escalar no es un signo de debilidad: es responsabilidad profesional.

## Árbol de escalado por severidad

### SEV-1
1. **0–5 min**: ingeniero primary on-call responde, abre puente de incidente en Zoom (link fijo: https://devopsdays.corp/war-room) y notifica en #incidentes.
2. **5–10 min**: si no hay respuesta del primary, PagerDuty escala automáticamente al secondary on-call.
3. **10–15 min**: si el secondary no responde, PagerDuty escala al on-call manager del squad.
4. **15 min**: el on-call manager notifica al VP de Ingeniería y al CTO por Slack y SMS.
5. **30 min sin resolución**: comunicado externo a clientes via https://status.devopsdays.corp.

### SEV-2
1. **0–15 min**: primary on-call investiga y notifica en #incidentes.
2. **15–60 min**: si no hay progreso, escalar al tech lead del squad propietario del servicio.
3. **60 min sin resolución**: on-call manager toma conocimiento y facilita recursos adicionales.

### SEV-3 y SEV-4
- Gestión en horario laboral normal. Sin escalación nocturna.
- Ticket en Jira con componente "On-Call" y severidad asignada.

## Cómo escalar en PagerDuty
```
# Escalar manualmente a una política de escalado diferente desde la app móvil:
Incidente → Escalar → Seleccionar política → Confirmar

# O via API:
curl -X POST https://api.pagerduty.com/incidents/<ID>/manual_escalations \
  -H "Authorization: Token token=<API_KEY>" \
  -d '{"manual_escalation": {"escalation_level": 2}}'
```

## Comunicación durante el incidente
- Canal primario: #incidentes en Slack.
- Puente de voz: https://devopsdays.corp/war-room (Zoom, link permanente).
- Actualizaciones de estado externas: https://status.devopsdays.corp (acceso de edición en #incidentes).
- Template de update: "[SEV-X][HH:MM UTC] Estado: <investigando/mitigando/resuelto>. Impacto: <descripción>. Próxima actualización en <N> minutos."

## Post-incidente
Una vez resuelto, el on-call primary:
1. Cierra la alerta en PagerDuty.
2. Publica en #incidentes: "Resuelto a las HH:MM UTC. RCA pendiente de postmortem."
3. Abre el ticket de postmortem en Confluence si corresponde.
4. Actualiza https://status.devopsdays.corp con el estado "Resolved".
""",
        },
    ],

    "index-runbooks": [
        {
            "id": "run-001",
            "title": "Runbook: Resolución de CrashLoopBackOff en EKS — Paso a Paso",
            "category": "kubernetes",
            "url": "wiki-interno/runbooks/kubernetes/crashloopbackoff",
            "content": """
# Runbook: Resolución de CrashLoopBackOff en EKS — Paso a Paso

## Síntomas
El pod entra en estado CrashLoopBackOff: el contenedor inicia, falla con código de salida
no-cero, y Kubernetes lo reinicia con backoff exponencial (10s, 20s, 40s… hasta 5 minutos).

## Diagnóstico inicial

### Paso 1 — Identificar pods afectados
```bash
kubectl get pods -n <namespace> | grep CrashLoop
kubectl describe pod <pod-name> -n <namespace>
```
En la sección "Events" y "Last State" buscar: OOMKilled, Error, exit code, liveness probe failure.

### Paso 2 — Revisar logs del contenedor crasheado
```bash
# Logs del contenedor actual (puede estar vacíos si crashea muy rápido)
kubectl logs <pod-name> -n <namespace>

# Logs del contenedor anterior — CLAVE para ver el error real
kubectl logs <pod-name> -n <namespace> --previous

# Si hay múltiples contenedores en el pod
kubectl logs <pod-name> -n <namespace> -c <container-name> --previous
```

## Causas más frecuentes y resolución

### Causa A — OOMKilled (memoria insuficiente)
`kubectl describe pod` muestra `OOMKilled` en "Last State → Reason".
```yaml
# Fix: aumentar memory limits en el manifiesto del deployment
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"   # ajustar según perfil real de la app
    cpu: "500m"
```
Verificar el consumo real antes de ajustar: Grafana dashboard /d/k8s-pods → "Memory Usage by Pod".

### Causa B — Error de aplicación (exit code 1 o mayor)
Revisar stack trace completo en los logs con `--previous`.
Opciones: corregir el bug y hacer nuevo deploy, o hacer rollback si es un deploy reciente.
```bash
kubectl rollout undo deployment/<deployment-name> -n <namespace>
kubectl rollout status deployment/<deployment-name> -n <namespace>
```

### Causa C — Liveness probe fallando antes de que la app esté lista
`kubectl describe pod` muestra "Liveness probe failed" en Events.
```yaml
# Fix: aumentar initialDelaySeconds para dar tiempo al arranque
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30   # era 10, aumentar según tiempo real de arranque
  periodSeconds: 10
  failureThreshold: 3
```

### Causa D — ConfigMap o Secret faltante o con clave incorrecta
Exit code 1 con mensaje "environment variable not found" o "file not found" en los logs.
```bash
# Verificar que el ConfigMap existe en el namespace correcto
kubectl get configmap <nombre> -n <namespace>

# Verificar que el Secret existe
kubectl get secret <nombre> -n <namespace>

# Ver las claves disponibles en el Secret (sin mostrar valores)
kubectl describe secret <nombre> -n <namespace>
```

### Causa E — ImagePullBackOff / imagen inexistente
`kubectl describe pod` muestra "Failed to pull image" o "ErrImagePull".
Verificar que el tag de imagen existe en ECR:
```bash
aws ecr describe-images --repository-name <repo> --image-ids imageTag=<tag> --region us-east-1
```
Fix: corregir el tag en el manifiesto del deployment o en ArgoCD.

## Escalado
Si en 30 minutos no se resuelve: clasificar como SEV-2, abrir puente en #incidentes, y
notificar al tech lead del equipo owner del servicio.

## Dashboard de referencia
Grafana: https://grafana.devopsdays.corp/d/k8s-pods — filtrar por namespace, buscar pods "Not Running".
Datadog: https://app.datadoghq.com → Containers → filtrar por `kube_namespace:<namespace>`.
""",
        },
        {
            "id": "run-002",
            "title": "Runbook: Alta Utilización de CPU y Memoria en Nodos EKS — Diagnóstico y Mitigación",
            "category": "performance",
            "url": "wiki-interno/runbooks/kubernetes/alto-cpu-memoria",
            "content": """
# Runbook: Alta Utilización de CPU y Memoria en Nodos EKS — Diagnóstico y Mitigación

## Síntomas
- Alerta de Datadog: "Node CPU utilization > 85% for 10 minutes" o "Node memory usage > 90%".
- Pods en estado Pending por falta de recursos (Insufficient CPU / Insufficient memory).
- Throttling de CPU visible en métricas: `container_cpu_cfs_throttled_periods_total`.
- Latencia elevada en servicios que corren en los nodos afectados.

## Diagnóstico paso a paso

### Paso 1 — Identificar nodos y pods con mayor consumo
```bash
# Uso de recursos por nodo
kubectl top nodes

# Uso de recursos por pod en el namespace afectado
kubectl top pods -n <namespace> --sort-by=cpu
kubectl top pods -n <namespace> --sort-by=memory

# Ver qué pods están en Pending y por qué
kubectl get pods -n <namespace> | grep Pending
kubectl describe pod <pending-pod> -n <namespace>
# Buscar en Events: "Insufficient cpu" o "Insufficient memory"
```

### Paso 2 — Revisar métricas históricas
Dashboard Grafana: https://grafana.devopsdays.corp/d/eks-nodes
- CPU utilization por nodo (últimas 2 horas).
- Memory utilization por nodo.
- Pod count por nodo.
- Network I/O (descartar que sea un problema de red, no de CPU/mem).

### Paso 3 — Identificar el workload que consume más recursos
```bash
# Recursos solicitados y límites por namespace
kubectl describe nodes | grep -A 5 "Allocated resources"

# Pods sin limits definidos (candidatos a consumo descontrolado)
kubectl get pods -n <namespace> -o json | jq '.items[] | select(.spec.containers[].resources.limits == null) | .metadata.name'
```

## Acciones de mitigación inmediata

### Opción A — Escalar horizontalmente el deployment que satura
```bash
kubectl scale deployment <nombre> --replicas=<cantidad> -n <namespace>
# Verificar que los nuevos pods arranquen correctamente
kubectl rollout status deployment/<nombre> -n <namespace>
```

### Opción B — Escalar el cluster (agregar nodos)
El cluster prod-us-east-1 tiene auto-scaling configurado. Si los pods están en Pending
por más de 5 minutos, el Cluster Autoscaler debería agregar nodos automáticamente.
Para forzarlo o verificar:
```bash
kubectl get nodes --watch
# Revisar logs del Cluster Autoscaler
kubectl logs -n kube-system -l app=cluster-autoscaler --tail=50
```
Si el autoscaler no actúa, escalar el node group manualmente desde AWS Console:
EKS → Clusters → prod-us-east-1 → Node Groups → Escalar.

### Opción C — Identificar y reiniciar pods con memory leak
```bash
# Reiniciar un deployment específico (rolling restart)
kubectl rollout restart deployment/<nombre> -n <namespace>
```

## Escalado
Si la utilización de nodos supera el 95% o hay pods en Pending por más de 10 minutos:
clasificar como SEV-2 y notificar al equipo de Plataforma en #platform.
""",
        },
        {
            "id": "run-003",
            "title": "Runbook: Connection Pool Exhausted en Base de Datos — RDS y Aurora PostgreSQL",
            "category": "database",
            "url": "wiki-interno/runbooks/database/connection-pool-exhausted",
            "content": """
# Runbook: Connection Pool Exhausted en Base de Datos — RDS y Aurora PostgreSQL

## Síntomas
- Error en logs de aplicación: "too many clients already", "connection pool exhausted",
  "FATAL: remaining connection slots are reserved", "OperationalError: could not connect to server".
- Alerta de Datadog: "DB connections > 90% of max_connections".
- Latencia de queries elevada o timeouts masivos desde la aplicación.
- Error rate alto en endpoints que acceden a base de datos.

## Configuración de conexiones en DevOps Days CORP
- RDS PostgreSQL producción: `max_connections = 500` (instancia db.r6g.xlarge).
- Aurora PostgreSQL producción: `max_connections = 1000` (serverless v2 configurado con hasta 16 ACUs).
- PgBouncer activo como connection pooler frente a todas las instancias RDS/Aurora productivas.
- Pool size de PgBouncer: 100 conexiones por database pool.

## Diagnóstico paso a paso

### Paso 1 — Verificar cantidad de conexiones activas
Desde AWS Console → RDS → Performance Insights → métrica "DatabaseConnections".
O directamente si tenés acceso a psql (requiere bastion host o EKS pod con cliente):
```sql
-- Conexiones activas por estado y usuario
SELECT state, usename, count(*)
FROM pg_stat_activity
GROUP BY state, usename
ORDER BY count DESC;

-- Conexiones idle que están bloqueando el pool
SELECT pid, usename, application_name, state, query_start, state_change, query
FROM pg_stat_activity
WHERE state = 'idle'
ORDER BY state_change;
```

### Paso 2 — Acceder al bastion para ejecutar queries de diagnóstico
```bash
# Conectar al bastion host (requiere VPN activa)
ssh -i ~/.ssh/devopsdays-bastion.pem ec2-user@bastion.devopsdays.corp

# Conectar a la base de datos (credenciales en Vault)
vault kv get secret/devops/platform/rds-prod
psql -h prod-db.cluster-xxxxxxxxx.us-east-1.rds.amazonaws.com -U admin -d devopsdays_prod
```

### Paso 3 — Terminar conexiones idle si están saturando el pool
```sql
-- Terminar conexiones idle por más de 10 minutos (con cuidado en producción)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND state_change < NOW() - INTERVAL '10 minutes'
  AND usename != 'rdsadmin';
```

### Paso 4 — Verificar estado de PgBouncer
```bash
# Conectar a la consola admin de PgBouncer
psql -h pgbouncer.devopsdays.corp -p 6432 -U pgbouncer pgbouncer

# Ver estadísticas de pool
SHOW POOLS;
SHOW STATS;
SHOW CLIENTS;
```

## Mitigación inmediata
1. Escalar horizontalmente los pods de la aplicación reduciendo conexiones por pod (si usan pool interno como SQLAlchemy o HikariCP, reducir pool_size en config).
2. Reiniciar los pods que tengan conexiones zombie (rolling restart del deployment).
3. Si PgBouncer está saturado, reiniciarlo: `kubectl rollout restart deployment/pgbouncer -n data`.

## Escalado
Si no se resuelve en 20 minutos o hay pérdida de datos: SEV-1, escalar al DBA on-call.
Contacto DBA: PagerDuty policy "Database On-Call".
""",
        },
        {
            "id": "run-004",
            "title": "Runbook: Certificado SSL Expirado o Error TLS — Diagnóstico y Renovación",
            "category": "seguridad",
            "url": "wiki-interno/runbooks/seguridad/cert-expirado-ssl",
            "content": """
# Runbook: Certificado SSL Expirado o Error TLS — Diagnóstico y Renovación

## Síntomas
- Usuarios reportan "Your connection is not private" o ERR_CERT_DATE_INVALID en el navegador.
- Alerta de Datadog: "SSL certificate expiring in < 7 days" o "SSL certificate expired".
- Alerta de PagerDuty: policy "Cert Expiry Monitor".
- Errores en logs: "certificate has expired", "SSL handshake failed", "x509: certificate signed by unknown authority".
- Health checks de ALB o NLB empezando a fallar con TLS errors.

## Inventario de certificados en DevOps Days CORP
Los certificados se gestionan en tres lugares:
1. **AWS ACM (Certificate Manager)**: certificados para ALB/NLB y CloudFront. Renovación automática si el dominio está en Route53.
2. **cert-manager en EKS**: certificados para Ingress de Kubernetes, emitidos por Let's Encrypt vía ACME. Renovación automática 30 días antes de la expiración.
3. **HashiCorp Vault PKI**: certificados internos para comunicación servicio-a-servicio (mTLS). Rotación automática configurable.

## Diagnóstico paso a paso

### Paso 1 — Verificar qué certificado está fallando
```bash
# Verificar certificado de un dominio externo
openssl s_client -connect api.devopsdays.corp:443 -servername api.devopsdays.corp 2>/dev/null | openssl x509 -noout -dates

# Verificar certificado de un servicio interno en Kubernetes
kubectl get certificate -n <namespace>
kubectl describe certificate <cert-name> -n <namespace>

# Ver estado de todos los certificados gestionados por cert-manager
kubectl get certificates -A
```

### Paso 2 — Certificados en AWS ACM
Si el dominio está en Route53 y el certificado es de ACM, la renovación debería ser automática.
Verificar en AWS Console → ACM → buscar el certificado → verificar estado "Issued" y fecha de expiración.
Si está en estado "Pending validation": revisar que los registros DNS de validación existen en Route53.
```bash
aws acm describe-certificate --certificate-arn <arn> --region us-east-1 | jq '.Certificate.Status'
```

### Paso 3 — Certificados de cert-manager (Let's Encrypt)
```bash
# Ver si cert-manager está intentando renovar
kubectl get certificaterequests -n <namespace>
kubectl describe certificaterequest <nombre> -n <namespace>

# Forzar renovación manual si la automática falló
kubectl delete secret <tls-secret-name> -n <namespace>
# cert-manager detectará la falta del secret y creará uno nuevo automáticamente

# Ver logs de cert-manager para diagnosticar errores
kubectl logs -n cert-manager -l app=cert-manager --tail=100
```

### Paso 4 — Error "x509: certificate signed by unknown authority" en comunicación interna
Este error indica que el cliente no confía en la CA interna de Vault.
Verificar que el bundle de CA de Vault PKI está montado en el pod cliente:
```bash
kubectl describe pod <pod-name> -n <namespace> | grep -A 5 "vault-ca"
```
Solución: refrescar el bundle de CA desde Vault y reiniciar los pods afectados.

## Renovación de emergencia (certificado ya expirado)
Si el certificado ya expiró y la renovación automática no funcionó:
1. Para ACM: re-solicitar el certificado manualmente en AWS Console → ACM → Request certificate.
2. Para cert-manager: borrar el secret TLS para forzar re-emisión (ver Paso 3).
3. Notificar en #incidentes con severidad SEV-1 si el servicio está caído.

## Monitoreo preventivo
Alerta configurada en Datadog para certificados que expiran en menos de 30 días.
Dashboard: https://grafana.devopsdays.corp/d/cert-expiry
""",
        },
        {
            "id": "run-005",
            "title": "Runbook: Procedimiento de Rollback de Deploy en Producción — ArgoCD y kubectl",
            "category": "deployment",
            "url": "wiki-interno/runbooks/deployment/rollback-produccion",
            "content": """
# Runbook: Procedimiento de Rollback de Deploy en Producción — ArgoCD y kubectl

## Cuándo ejecutar un rollback
- Error rate aumentó > 5% en los 15 minutos post-deploy.
- Latencia p99 aumentó > 50% respecto al baseline pre-deploy.
- Alertas de SEV-1 o SEV-2 disparadas en los 15 minutos post-deploy.
- Funcionalidad crítica rota según reporte de QA o usuarios.
- El ingeniero on-call tiene dudas sobre la estabilidad: ante la duda, hacer rollback.

## Principio de rollback
En DevOps Days CORP, los deploys se realizan exclusivamente via GitOps (ArgoCD).
El rollback siempre es preferible a intentar hotfixes rápidos en producción bajo presión.

## Método 1 — Rollback via ArgoCD UI (recomendado)
1. Abrir ArgoCD: https://argocd.devopsdays.corp
2. Navegar a la aplicación afectada (ej: `squad-payments-api`).
3. Hacer click en "History and Rollback" (ícono de reloj en la barra superior).
4. Seleccionar el deployment anterior al que quieres volver (identificar por timestamp y Git SHA).
5. Hacer click en "Rollback" → confirmar.
6. ArgoCD desplegará el manifiesto de esa versión anterior. Monitorear el progreso en la UI.
7. Verificar que los pods del nuevo rollout están en Running:
```bash
kubectl rollout status deployment/<nombre> -n production
kubectl get pods -n production | grep <app-name>
```

## Método 2 — Rollback via kubectl (si ArgoCD no está disponible)
```bash
# Ver historial de versiones del deployment
kubectl rollout history deployment/<deployment-name> -n production

# Rollback a la versión anterior inmediata
kubectl rollout undo deployment/<deployment-name> -n production

# Rollback a una versión específica del historial
kubectl rollout undo deployment/<deployment-name> -n production --to-revision=<N>

# Verificar estado del rollout
kubectl rollout status deployment/<deployment-name> -n production
```
NOTA: el rollback via kubectl crea divergencia entre el estado del cluster y el repo de Git.
Luego del incidente, el equipo debe actualizar el repo para que ArgoCD no revierta el rollback.

## Método 3 — Rollback via Git (reverting el commit de deploy)
Si el rollback involucra cambios de configuración complejos o múltiples manifiestos:
```bash
# Revertir el commit de deploy en el repo k8s-manifests
git revert <commit-sha>
git push origin main
# ArgoCD detectará el cambio y sincronizará automáticamente
```

## Verificación post-rollback
1. Esperar 5 minutos y verificar en Datadog APM que error rate vuelve a baseline.
2. Verificar latencia p99 en Datadog: https://app.datadoghq.com → APM → Services → <servicio>.
3. Confirmar que health checks del ALB están en healthy.
4. Notificar en #incidentes: "Rollback completado a versión <tag/SHA>. Error rate normalizado. Monitoreando."
5. Abrir ticket de postmortem en Confluence si el rollback causó > 5 min de degradación.

## Qué NO hacer durante un rollback
- No hacer hotfixes en producción bajo presión: siempre rollback primero, fix después.
- No omitir la verificación post-rollback: el rollback puede introducir otros problemas.
- No olvidar actualizar el repo de Git si hiciste rollback con kubectl directamente.
""",
        },
    ],

    "index-herramientas": [
        {
            "id": "her-001",
            "title": "HashiCorp Vault — Gestión de Secretos y Credenciales en DevOps Days CORP",
            "category": "secrets",
            "url": "wiki-interno/herramientas/vault",
            "content": """
# HashiCorp Vault — Gestión de Secretos y Credenciales en DevOps Days CORP

## ¿Qué es Vault y para qué lo usamos?
Vault es la herramienta oficial de DevOps Days CORP para la gestión centralizada de secretos,
credenciales de base de datos, certificados TLS, tokens de API y claves de cifrado.
Toda credencial que antes vivía en un .env, un ConfigMap de Kubernetes o un email debe estar en Vault.

## Entornos disponibles
- Producción: https://vault.devopsdays.corp (alta disponibilidad, 3 nodos en us-east-1)
- Staging: https://vault-stg.devopsdays.corp
- Autenticación: SSO via Azure AD (OIDC). Usá tu cuenta corporativa @devopsdays.corp.

## Acceso desde CLI

### Login inicial
```bash
# Instalar vault CLI si no lo tenés: brew install vault (macOS) o desde https://releases.hashicorp.com/vault
export VAULT_ADDR="https://vault.devopsdays.corp"

# Login con Azure AD (abrirá el navegador para autenticarte con tu cuenta corporativa)
vault login -method=oidc

# Verificar que el login funcionó
vault token lookup
```

### Operaciones básicas
```bash
# Leer un secreto (KV v2)
vault kv get secret/devops/<equipo>/<nombre-secreto>

# Leer solo el valor de un campo específico
vault kv get -field=password secret/devops/payments/rds-credentials

# Listar secretos disponibles para tu equipo
vault kv list secret/devops/<equipo>/

# Crear o actualizar un secreto
vault kv put secret/devops/<equipo>/<nombre> key1=value1 key2=value2
```

## Acceso desde aplicaciones en Kubernetes (Vault Agent Injector)
Las aplicaciones en EKS acceden a Vault automáticamente via el Vault Agent Injector,
que inyecta los secretos como archivos o variables de entorno en el pod:
```yaml
# Anotaciones en el manifiesto del deployment
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "<nombre-del-k8s-role>"
  vault.hashicorp.com/agent-inject-secret-db-creds: "secret/devops/<equipo>/rds-credentials"
  vault.hashicorp.com/agent-inject-template-db-creds: |
    {{- with secret "secret/devops/<equipo>/rds-credentials" -}}
    DB_PASSWORD={{ .Data.data.password }}
    DB_USER={{ .Data.data.username }}
    {{- end }}
```

## Roles y estructura de permisos
- Cada equipo tiene su propio path: `secret/devops/<nombre-equipo>/`
- Los roles de Kubernetes y las policies de Vault se gestionan via Terraform en el repo `infra/vault-policies`.
- Para solicitar acceso a un path nuevo: crear PR en `infra/vault-policies` o abrir ticket en #platform.
- Acceso de solo lectura para aplicaciones; acceso de escritura solo para ingenieros con aprobación.

## Rotación de secretos
- **Credenciales de base de datos** (Dynamic Secrets): se generan y rotan automáticamente cada 1 hora. Vault crea un usuario de BD temporal y lo elimina cuando expira. Cero secretos de larga duración.
- **API keys de servicios externos**: rotación manual cada 90 días. Alerta en PagerDuty: policy "Vault Secret Expiry".
- **Certificados TLS internos** (Vault PKI): renovación automática 30 días antes de expirar.

## Troubleshooting frecuente
- **403 permission denied**: tu rol no tiene acceso al path solicitado. Revisar en #platform.
- **Token expired**: re-autenticar con `vault login -method=oidc`. Los tokens de CLI duran 8 horas.
- **Secret not found**: verificar el path exacto con `vault kv list`. Los paths son case-sensitive.
- **Vault Agent no inyecta secretos**: verificar que las anotaciones están en el template del pod, no en el metadata del deployment.

## Contacto y soporte
Canal de Slack: #platform. On-call de plataforma: PagerDuty policy "Platform On-Call".
Documentación completa: https://wiki.devopsdays.corp/herramientas/vault
""",
        },
        {
            "id": "her-002",
            "title": "Kubernetes y Amazon EKS — Guía de Acceso y Operación para DevOps Days CORP",
            "category": "kubernetes",
            "url": "wiki-interno/herramientas/kubernetes-eks",
            "content": """
# Kubernetes y Amazon EKS — Guía de Acceso y Operación para DevOps Days CORP

## Clusters disponibles
| Cluster          | Ambiente    | Región      | Propósito                          |
|------------------|-------------|-------------|-------------------------------------|
| prod-us-east-1   | Producción  | us-east-1   | Workloads productivos               |
| staging          | Staging     | us-east-1   | Validación pre-producción           |
| dev-shared       | Desarrollo  | us-east-1   | Desarrollo y testing de squads      |

## Acceso inicial al cluster

### Prerrequisitos
- AWS CLI configurado con perfil SSO: `aws configure sso --profile devopsdays-prod`
- kubectl instalado: https://kubernetes.io/docs/tasks/tools/
- Acceso IAM al cluster (solicitar al equipo de Plataforma vía #platform)

### Configurar kubeconfig
```bash
# Producción
aws eks update-kubeconfig --name prod-us-east-1 --region us-east-1 --profile devopsdays-prod

# Staging
aws eks update-kubeconfig --name staging --region us-east-1 --profile devopsdays-staging

# Verificar acceso
kubectl get nodes
kubectl get namespaces
```

## Namespaces y organización
Cada squad tiene namespaces dedicados:
- `squad-<nombre>`: workloads del squad en producción.
- `squad-<nombre>-staging`: workloads del squad en staging.
- `infra`: componentes de infraestructura compartida (ingress, cert-manager, monitoring).
- `data`: workloads de datos (PgBouncer, jobs de ETL, Kafka).

```bash
# Listar namespaces de tu squad
kubectl get ns | grep squad-<nombre>

# Establecer namespace por defecto para tu sesión
kubectl config set-context --current --namespace=squad-<nombre>
```

## Operaciones frecuentes

### Ver estado de pods y logs
```bash
kubectl get pods -n <namespace>
kubectl logs <pod-name> -n <namespace> --follow
kubectl describe pod <pod-name> -n <namespace>
```

### Ejecutar un pod de debugging temporal
```bash
# Pod con herramientas de red (curl, dig, nc)
kubectl run debug-pod --image=nicolaka/netshoot -n <namespace> --rm -it -- bash

# Pod con cliente de PostgreSQL
kubectl run psql-debug --image=postgres:15 -n <namespace> --rm -it -- bash
```

## Deploys y GitOps
Los deploys en producción se realizan EXCLUSIVAMENTE via ArgoCD.
No se permiten `kubectl apply` directos en el namespace de producción.
Los manifests de Kubernetes viven en el repo: https://github.com/devopsdays-corp/k8s-manifests

## Herramientas de observabilidad
- **Grafana** (dashboards): https://grafana.devopsdays.corp — dashboards de nodos, pods, namespaces, SLOs.
- **Datadog** (APM, logs, trazas): https://app.datadoghq.com — Service Map, tracing distribuido, log management.
- **Prometheus** (métricas raw): acceso via Grafana o `kubectl port-forward svc/prometheus 9090:9090 -n monitoring`.
- **Lens** (UI de escritorio para kubectl): recomendado para operaciones de debugging. https://k8slens.dev

## Resource Quotas en producción
Los namespaces de producción tienen Resource Quotas configuradas. Si un deploy falla por quota:
```bash
kubectl describe resourcequota -n <namespace>
```
Para aumentar la quota: abrir PR en `infra/k8s-quotas/` o ticket en #platform.
""",
        },
        {
            "id": "her-003",
            "title": "Terraform — Flujo de Trabajo de Infraestructura como Código en DevOps Days CORP",
            "category": "iac",
            "url": "wiki-interno/herramientas/terraform",
            "content": """
# Terraform — Flujo de Trabajo de Infraestructura como Código en DevOps Days CORP

## Repositorio y estructura
Todo el código de infraestructura vive en: https://github.com/devopsdays-corp/infra
```
infra/
├── terraform/
│   ├── prod/           # Infraestructura de producción
│   │   ├── eks/        # Cluster EKS y node groups
│   │   ├── rds/        # Bases de datos RDS/Aurora
│   │   ├── networking/ # VPC, subnets, security groups
│   │   └── iam/        # Roles y policies de IAM
│   ├── staging/        # Infraestructura de staging
│   └── shared/         # Recursos compartidos (Route53, ACM, ECR)
├── modules/            # Módulos reutilizables internos
└── vault-policies/     # Políticas de Vault gestionadas con Terraform
```

## Flujo de trabajo estándar (GitOps)

### 1. Preparar el entorno local
```bash
# Instalar tfenv para gestionar versiones de Terraform
brew install tfenv
tfenv install 1.7.4
tfenv use 1.7.4

# Autenticarse en AWS con SSO
aws sso login --profile devopsdays-prod
```

### 2. Desarrollar el cambio
```bash
cd infra/terraform/prod/<servicio>

# Inicializar (primera vez o después de cambiar providers/modules)
terraform init

# Ver qué cambios se aplicarán
terraform plan -out=tfplan

# Revisar el plan cuidadosamente antes de hacer PR
```

### 3. Pull Request y CI
Al abrir un PR, GitHub Actions ejecuta automáticamente:
- `terraform fmt -check`: verifica formato del código.
- `terraform validate`: valida la sintaxis.
- `terraform plan`: genera el plan y lo comenta en el PR.
- **checkov**: escaneo de seguridad de la infraestructura.
El plan debe ser revisado y aprobado por al menos 1 miembro del equipo de Plataforma.

### 4. Apply automático
Al hacer merge a `main`, GitHub Actions ejecuta `terraform apply` automáticamente.
El apply se loguea en: https://github.com/devopsdays-corp/infra/actions

## State backend
```hcl
# Backend configurado en cada módulo
terraform {
  backend "s3" {
    bucket         = "devopsdays-terraform-state"
    key            = "prod/eks/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

## Módulos internos disponibles
- `modules/eks-cluster`: cluster EKS con node groups, IRSA, y addons estándar.
- `modules/rds-aurora`: Aurora PostgreSQL con backups, monitoring, y alertas.
- `modules/vault-policy`: crea paths de Vault y policies para un equipo.
- `modules/ecr-repo`: repositorio ECR con políticas de lifecycle y replicación.
- `modules/alb-ingress`: ALB con certificado ACM y reglas de routing.

## Acceso y permisos
Roles IAM asignados via SSO (grupos en Azure AD):
- `terraform-prod-admins`: write sobre recursos de producción.
- `terraform-staging-admins`: write sobre recursos de staging.
- `terraform-readonly`: solo `terraform plan`, sin apply.
Para solicitar acceso: ticket en #platform con justificación.

## Buenas prácticas en DevOps Days CORP
- Siempre usar `terraform plan` antes de cualquier cambio.
- No usar `terraform apply` local en producción: usar el pipeline de CI/CD.
- Los cambios destructivos (destroy, replace) requieren aprobación del CTO o VP de Ingeniería.
- Variables sensibles nunca en el código: usar Vault o SSM Parameter Store.
- Canal de dudas: #infra-terraform en Slack.
""",
        },
        {
            "id": "her-004",
            "title": "ArgoCD — Despliegues GitOps en Kubernetes para DevOps Days CORP",
            "category": "gitops",
            "url": "wiki-interno/herramientas/argocd",
            "content": """
# ArgoCD — Despliegues GitOps en Kubernetes para DevOps Days CORP

## ¿Qué es ArgoCD y cómo lo usamos?
ArgoCD es la herramienta de GitOps que sincroniza el estado del cluster de Kubernetes con el
estado declarado en el repositorio `k8s-manifests`. Todo deploy en producción pasa por ArgoCD.
No se permite `kubectl apply` directo en producción: el repositorio Git es la única fuente de verdad.

## Acceso
- ArgoCD UI: https://argocd.devopsdays.corp
- Autenticación: SSO con tu cuenta Azure AD @devopsdays.corp.
- ArgoCD CLI: `argocd login argocd.devopsdays.corp --sso`

## Estructura del repositorio k8s-manifests
```
k8s-manifests/
├── apps/
│   ├── squad-payments/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── hpa.yaml
│   │   └── kustomization.yaml
│   └── squad-auth/
├── infra/
│   ├── ingress-nginx/
│   ├── cert-manager/
│   └── monitoring/
└── argocd/
    └── applications/     # Definiciones de ArgoCD Applications
```

## Cómo hacer un deploy

### Deploy normal (vía PR)
1. Modificar el manifiesto correspondiente en `k8s-manifests/apps/<squad>/` (ej: actualizar el tag de imagen en `deployment.yaml`).
2. Crear un Pull Request. El CI (GitHub Actions) valida los manifests con `kubeval` y `kustomize build`.
3. Obtener aprobación de al menos 1 peer del equipo.
4. Hacer merge a `main`.
5. ArgoCD detecta el cambio (polling cada 3 minutos o webhook inmediato) y sincroniza.
6. Monitorear el sync en ArgoCD UI o con:
```bash
argocd app get <app-name> --watch
# o
kubectl rollout status deployment/<nombre> -n <namespace>
```

### Deploy de emergencia (sync manual)
```bash
# Forzar sincronización inmediata sin esperar el polling
argocd app sync <app-name>

# Sincronizar con prune (eliminar recursos no declarados en Git)
argocd app sync <app-name> --prune

# Ver diferencias entre el estado deseado (Git) y el estado actual del cluster
argocd app diff <app-name>
```

## Rollback via ArgoCD
```bash
# Ver historial de deploys
argocd app history <app-name>

# Rollback a un deployment anterior (por número de revision)
argocd app rollback <app-name> <revision-number>
```
O desde la UI: Application → History and Rollback → seleccionar revision → Rollback.

## Sincronización automática vs manual
- **Apps de producción**: sync manual (requiere aprobación humana antes de sincronizar).
- **Apps de staging**: sync automático habilitado, ArgoCD sincroniza automáticamente al detectar cambios.
- **Apps de infra (cert-manager, ingress, monitoring)**: sync manual con aprobación del equipo de Plataforma.

## Alertas de ArgoCD
Cuando una app está en estado `OutOfSync` o `Degraded`, Datadog genera una alerta.
Si ves una app en estado rojo en ArgoCD:
1. Revisar el diff: `argocd app diff <app-name>`.
2. Revisar los eventos del pod: `kubectl describe pod <pod> -n <namespace>`.
3. Si es un drift no deseado (alguien hizo `kubectl apply` directo), sincronizar con `argocd app sync <app-name>`.

## Contacto
Canal de Slack: #deployments. Dudas de configuración: #platform.
Documentación de ArgoCD: https://argo-cd.readthedocs.io
Wiki interna: https://wiki.devopsdays.corp/herramientas/argocd
""",
        },
        {
            "id": "her-005",
            "title": "Datadog y Grafana — Monitoreo, Alertas y Observabilidad en DevOps Days CORP",
            "category": "monitoring",
            "url": "wiki-interno/herramientas/datadog-grafana",
            "content": """
# Datadog y Grafana — Monitoreo, Alertas y Observabilidad en DevOps Days CORP

## Stack de observabilidad
DevOps Days CORP usa dos herramientas complementarias de observabilidad:
- **Datadog**: APM (trazas distribuidas), log management, métricas de aplicación, alertas de negocio.
- **Grafana**: dashboards de infraestructura, SLOs, métricas de Kubernetes (fuente: Prometheus y CloudWatch).

## Acceso
- Datadog: https://app.datadoghq.com — login con tu cuenta corporativa (SSO via Azure AD).
- Grafana: https://grafana.devopsdays.corp — login con SSO.
- Prometheus (métricas raw): acceso indirecto via Grafana o port-forward.

## Datadog — Casos de uso principales

### APM y Service Map
El Service Map de Datadog muestra las dependencias entre servicios y el estado de salud de cada uno.
Acceso: APM → Service Map. Útil para identificar qué servicio está generando errores en una cadena de llamadas.

### Log Management
Todos los logs de aplicaciones en EKS se envían a Datadog automáticamente via el Datadog Agent (DaemonSet).
```
# Búsqueda de logs en Datadog Log Explorer:
service:<nombre-servicio> status:error @http.status_code:5*
env:production @error.kind:NullPointerException

# Buscar logs de un pod específico
kube_pod_name:<pod-name> kube_namespace:<namespace>
```

### Alertas
Las alertas de producción se configuran en Datadog Monitors y se enrutan a PagerDuty.
- Monitor de error rate: alerta cuando error rate > 1% por más de 5 minutos.
- Monitor de latencia: alerta cuando p99 > 2 segundos por más de 3 minutos.
- Monitor de disponibilidad: alerta cuando uptime SLO < 99.9% en ventana de 7 días.
Para crear o modificar alertas: https://app.datadoghq.com/monitors/manage

### Dashboards de Datadog relevantes
- **Service Overview**: APM → Services → seleccionar servicio → Overview.
- **Infrastructure List**: Infrastructure → Hosts → filtrar por tag `env:production`.
- **Container Map**: Infrastructure → Containers → ver consumo de recursos por pod.

## Grafana — Casos de uso principales

### Dashboards de Kubernetes
- **Node Overview**: /d/eks-nodes — CPU, memoria, disco y red por nodo.
- **Pod Overview**: /d/k8s-pods — estado de pods, reinicios, CPU y memoria por pod.
- **Namespace Overview**: /d/k8s-namespaces — recursos consumidos por namespace.
- **SLO Dashboard**: /d/slo-prod — error budget restante, burn rate actual, histórico de SLOs.

### Alertas de infraestructura
Las alertas de infraestructura (CPU de nodos, uso de disco, memoria de pods) se configuran en
Grafana Alerting y se enrutan a PagerDuty o al canal #alerts-infra de Slack según la severidad.

### Crear un nuevo dashboard
Los dashboards se gestionan como código en el repo `infra/grafana-dashboards/` (formato JSON).
Para agregar un nuevo dashboard:
1. Diseñarlo en la UI de Grafana (staging).
2. Exportarlo como JSON: Dashboard → Share → Export → Save to file.
3. Crear PR en `infra/grafana-dashboards/` con el JSON.
4. El pipeline de CI importa el dashboard en producción al hacer merge.

## Prácticas de alerting en DevOps Days CORP
- **Alertar sobre síntomas, no causas**: alertar cuando el usuario se ve afectado (error rate alto, latencia alta), no cuando la CPU está al 80%.
- **Evitar alert fatigue**: cada alerta debe ser accionable y tener un runbook asociado.
- **SLO burn rate alerts**: configurar alertas de burn rate en ventanas de 1h, 6h y 24h para detectar degradaciones antes de que consuman todo el error budget.
- Referencia: https://wiki.devopsdays.corp/sre/burn-rate-alerts

## Contacto
- Dudas de Datadog: #observability en Slack.
- Dudas de Grafana/Prometheus: #infra-monitoring en Slack.
- On-call de observabilidad: PagerDuty policy "Platform On-Call".
""",
        },
    ],
}


def ensure_index(index_name: str):
    url = f"{SEARCH_ENDPOINT}/indexes/{index_name}?api-version={SEARCH_API_VERSION}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        fields = [f["name"] for f in r.json().get("fields", [])]
        print(f"  [OK]  indice '{index_name}' existe — campos: {fields}")
    else:
        print(f"  [WARN] indice '{index_name}' no encontrado ({r.status_code}), creando...")
        body = {"name": index_name, **INDEX_SCHEMA}
        rc = requests.put(url, headers=HEADERS, json=body)
        if rc.status_code in (200, 201):
            print(f"  [OK]  indice '{index_name}' creado")
        else:
            print(f"  [ERR] crear '{index_name}': {rc.status_code} {rc.text[:200]}")


def upload_documents(index_name: str, docs: list):
    url = f"{SEARCH_ENDPOINT}/indexes/{index_name}/docs/index?api-version={SEARCH_API_VERSION}"
    body = {"value": [{"@search.action": "mergeOrUpload", **d} for d in docs]}
    r = requests.post(url, headers=HEADERS, json=body)
    if r.status_code in (200, 207):
        results = r.json().get("value", [])
        ok = sum(1 for x in results if x.get("status"))
        print(f"  [OK]  {ok}/{len(docs)} documentos subidos a '{index_name}'")
    else:
        print(f"  [ERR] upload a '{index_name}': {r.status_code} {r.text[:300]}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Seeding índices internos de Azure AI Search")
    print("=" * 60)

    for index_name, docs in DOCUMENTS.items():
        print(f"\n>> {index_name} ({len(docs)} documentos)")
        ensure_index(index_name)
        upload_documents(index_name, docs)

    print("\n" + "=" * 60)
    print("  Listo. Reiniciá el backend para que Foundry IQ indexe.")
    print("=" * 60 + "\n")
