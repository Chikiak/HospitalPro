# SGT-H: Sistema de Gestión de Turnos y Alertas Hospitalarias

Este proyecto implementa una solución integral para la gestión de citas médicas y laboratorios dentro de la red interna del hospital. El sistema moderniza la interacción paciente-hospital, integrándose de forma segura con la infraestructura de base de datos Oracle existente (Historias Clínicas) y optimizando el flujo de ingreso de datos.

## 🛠 Stack Tecnológico Seleccionado

Se ha seleccionado un stack moderno, robusto y escalable, priorizando la seguridad de datos médicos y la velocidad de respuesta.

### Backend (Lógica y Datos)
*   **Lenguaje:** Python 3.11+
*   **Framework API:** FastAPI (Alto rendimiento, asíncrono y auto-documentado).
*   **Base de Datos Local:** PostgreSQL (Gestión de usuarios, turnos y **datos de triaje**).
*   **Integración Legacy:** Librería `oracledb` para consultas de solo lectura a la Base de Datos Oracle.
*   **Procesamiento de Documentos:**
    *   `Pandas` + `OpenPyXL`: Generación de hojas de cálculo Excel para médicos.
    *   `WeasyPrint`: Generación de PDF clínicos profesionales.

### Frontend (Interfaz de Usuario)
*   **Framework:** React (Vite) + TypeScript.
*   **Estilos:** Tailwind CSS (Diseño limpio y adaptativo).
*   **Gestión de Estado:** TanStack Query.

---

## 📋 Funcionalidades y Flujos de Trabajo

### 1. 🏥 Paciente (Registro y Triaje)
El sistema digitaliza el proceso de admisión para evitar papeles y entrevistas repetitivas.

*   **Registro con "Triaje Digital":**
    *   Al crear la cuenta, además de sus datos de identificación (DNI + Fecha Nacimiento), el paciente debe completar un **Formulario de Admisión**.
    *   **Datos capturados:** Datos reque
    *   *Beneficio:* Estos datos quedan guardados digitalmente listos para ser usados por el médico, eliminando la necesidad de interrogatorios básicos repetitivos.
*   **Acceso Simplificado:**
    *   **Usuario:** Se utiliza el **DNI/Cédula** como identificador único.
*   **Reserva de Turnos Inteligente:**
    *   Algoritmo de "Los 3 turnos disponibles más cercanos" para agilizar la asignación de citas (Especialidad o Laboratorio).
*   **Historia Clínica y Alertas:**
    *   Visualización e impresión (PDF) de la Historia Clínica (solo si está validado).
    *   **Alertas:** Notificación automática cuando el laboratorio actualiza resultados en la base central.

### 2. 👨‍⚕️ Médicos (Optimización de Tiempo)
Herramientas diseñadas para reducir la carga administrativa manual de re-escritura.

*   **Exportación de Datos de Pacientes (El "Puente"):**
    *   Cuando un paciente nuevo llega a consulta, el médico **no necesita volver a preguntarle ni teclear manualmente** sus antecedentes.
    *   El sistema permite descargar un archivo **Excel (.xlsx)** estructurado con toda la información que el paciente cargó durante su registro (alergias, antecedentes, etc.).
    *   El médico puede copiar y pegar estos datos directamente en el sistema de Historias Clínicas (Oracle), ahorrando valiosos minutos de consulta.
*   **Validación de Identidad (Seguridad):**
    *   Botón de "Validar Paciente": Confirma que el usuario web corresponde al DNI físico presentado, habilitando al paciente el acceso futuro a sus resultados online.
*   **Agenda Digital:** Visualización de turnos pendientes.

### 3. ⚙️ Administrador
*   **Gestión de Disponibilidad:** Definición de la "Plantilla Semanal" de horarios y especialistas.
*   **Configuración Global:** Ajuste de duración de turnos.

---

## 🔐 Modelo de Seguridad y Datos

### Arquitectura de Datos Híbrida
1.  **Base de Datos Local (PostgreSQL):** Almacena usuarios, turnos y, crucialmente, los **Datos del Formulario de Admisión** que aún no han sido pasados a la historia clínica oficial.
2.  **Base de Datos Externa (Oracle - Solo Lectura):** El sistema consulta esta base para mostrar historiales ya consolidados, pero **NUNCA escribe** en ella para evitar corromper datos sensibles. La escritura la hace el médico (vía Excel/Manual) o el laboratorio.

### Seguridad de Identidad (Niveles de Acceso)
Para evitar errores de tipeo en el DNI o suplantación:
1.  **Nivel 1 (No Validado):** El usuario se registra (DNI + Fecha Nacimiento + Formulario Admisión). Puede sacar turno, pero **NO** puede ver historias clínicas ni resultados.
2.  **Nivel 2 (Validado):** Se activa solo cuando el personal del hospital confirma presencialmente la identidad. Habilita la descarga de PDFs y visualización de historial.