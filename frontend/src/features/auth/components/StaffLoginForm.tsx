import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import Input from '../../../components/ui/Input'
import Button from '../../../components/ui/Button'

const staffLoginSchema = z.object({
  password: z.string().min(1, 'La contraseña es requerida'),
})

type StaffLoginFormData = z.infer<typeof staffLoginSchema>

interface StaffLoginFormProps {
  onSubmit?: (data: StaffLoginFormData) => void | Promise<void>
}

export default function StaffLoginForm({ onSubmit }: StaffLoginFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<StaffLoginFormData>({
    resolver: zodResolver(staffLoginSchema),
  })

  const handleFormSubmit = async (data: StaffLoginFormData) => {
    if (onSubmit) {
      await onSubmit(data)
    }
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <Input
        {...register('password')}
        label="Contraseña de Personal"
        type="password"
        placeholder="Ingrese la contraseña del personal"
        error={errors.password?.message}
        autoComplete="current-password"
      />

      <Button
        type="submit"
        isLoading={isSubmitting}
        className="w-full"
      >
        Iniciar Sesión como Personal
      </Button>
    </form>
  )
}
