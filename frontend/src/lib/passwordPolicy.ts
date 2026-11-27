/**
 * Política mínima de contraseñas (F2-08): longitud mínima compartida por
 * todos los flujos de creación y cambio de contraseña (registro de
 * paciente/usuario, actualización de contraseña de personal).
 *
 * Se usa en el cliente para devolver una retroalimentación clara antes de
 * enviar al backend; el backend es quien autoritariamente rechaza con 422.
 * No se añaden reglas de composición no solicitadas (mayúsculas, números,
 * símbolos, etc.).
 */
export const MIN_PASSWORD_LENGTH = 8

export function minPasswordErrorMessage(length = MIN_PASSWORD_LENGTH): string {
    return `La contraseña debe tener al menos ${length} caracteres`
}

export function isValidPasswordLength(value: string): boolean {
    return typeof value === "string" && value.length >= MIN_PASSWORD_LENGTH
}
