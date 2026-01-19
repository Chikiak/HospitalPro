import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import Input from '../../../components/ui/Input'
import Button from '../../../components/ui/Button'

const registerSchema = z.object({
    dni: z
        .string()
        .length(11, 'El DNI debe tener exactamente 11 caracteres')
        .regex(/^\d+$/, 'El DNI debe contener solo números'),
    full_name: z.string().min(3, 'El nombre completo debe tener al menos 3 caracteres'),
    password: z.string().min(6, 'La contraseña debe tener al menos 6 caracteres'),
    confirmPassword: z.string().min(1, 'Debe confirmar su contraseña'),
}).refine((data) => data.password === data.confirmPassword, {
    message: "Las contraseñas no coinciden",
    path: ["confirmPassword"],
})

type RegisterFormData = z.infer<typeof registerSchema>

interface RegisterFormProps {
    onSubmit?: (data: Omit<RegisterFormData, 'confirmPassword'>) => void | Promise<void>
}

export default function RegisterForm({ onSubmit }: RegisterFormProps) {
    const {
        register,
        handleSubmit,
        formState: { errors, isSubmitting },
    } = useForm<RegisterFormData>({
        resolver: zodResolver(registerSchema),
    })

    const handleFormSubmit = async (data: RegisterFormData) => {
        if (onSubmit) {
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
            const { confirmPassword, ...registerData } = data
            await onSubmit(registerData)
        }
    }

    return (
        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
            <Input
                {...register('dni')}
                label="DNI"
                type="text"
                placeholder="Ingrese su DNI (11 dígitos)"
                error={errors.dni?.message}
            />

            <Input
                {...register('full_name')}
                label="Nombre Completo"
                type="text"
                placeholder="Ingrese su nombre completo"
                error={errors.full_name?.message}
            />

            <Input
                {...register('password')}
                label="Contraseña"
                type="password"
                placeholder="Mínimo 6 caracteres"
                error={errors.password?.message}
                autoComplete="new-password"
            />

            <Input
                {...register('confirmPassword')}
                label="Confirmar Contraseña"
                type="password"
                placeholder="Repita su contraseña"
                error={errors.confirmPassword?.message}
                autoComplete="new-password"
            />

            <Button
                type="submit"
                isLoading={isSubmitting}
                className="w-full"
            >
                Crear Cuenta
            </Button>
        </form>
    )
}
