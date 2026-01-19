import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import Input from '../../../components/ui/Input'
import Button from '../../../components/ui/Button'
import { DNI_PATTERN, DNI_VALIDATION, PASSWORD_VALIDATION } from '../../../lib/validation'

const loginSchema = z.object({
  dni: z
    .string()
    .min(1, DNI_VALIDATION.required)
    .regex(DNI_PATTERN, DNI_VALIDATION.format),
  password: z.string().min(1, PASSWORD_VALIDATION.required),
})

type LoginFormData = z.infer<typeof loginSchema>

interface LoginFormProps {
  onSubmit?: (data: LoginFormData) => void | Promise<void>
}

export default function LoginForm({ onSubmit }: LoginFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const handleFormSubmit = async (data: LoginFormData) => {
    if (onSubmit) {
      await onSubmit(data)
    }
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <Input
        {...register('dni')}
        label="DNI"
        type="text"
        placeholder="Ingrese su DNI"
        error={errors.dni?.message}
        autoComplete="username"
      />

      <Input
        {...register('password')}
        label="Contraseña"
        type="password"
        placeholder="Ingrese su contraseña"
        error={errors.password?.message}
        autoComplete="current-password"
      />

      <Button
        type="submit"
        isLoading={isSubmitting}
        className="w-full"
      >
        Iniciar Sesión
      </Button>
    </form>
  )
}
