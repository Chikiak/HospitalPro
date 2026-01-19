/**
 * Validation constants used across the application
 */

/**
 * DNI (Documento Nacional de Identidad) validation pattern
 * Expects exactly 11 digits
 */
export const DNI_PATTERN = /^\d{11}$/

/**
 * DNI validation error messages
 */
export const DNI_VALIDATION = {
  required: 'El DNI es requerido',
  format: 'El DNI debe tener exactamente 11 dígitos',
} as const

/**
 * Password validation error messages
 */
export const PASSWORD_VALIDATION = {
  required: 'La contraseña es requerida',
} as const
