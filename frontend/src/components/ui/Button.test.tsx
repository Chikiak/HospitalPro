import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Button from './Button'

describe('Button', () => {
  it('renders children correctly', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
  })

  it('calls onClick handler when clicked', async () => {
    const handleClick = vi.fn()
    const user = userEvent.setup()
    
    render(<Button onClick={handleClick}>Click me</Button>)
    
    await user.click(screen.getByRole('button', { name: /click me/i }))
    
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('renders primary variant with correct styles', () => {
    render(<Button variant="primary">Primary</Button>)
    const button = screen.getByRole('button', { name: /primary/i })
    
    expect(button).toHaveClass('bg-teal-700')
    expect(button).toHaveClass('text-white')
  })

  it('renders outline variant with correct styles', () => {
    render(<Button variant="outline">Outline</Button>)
    const button = screen.getByRole('button', { name: /outline/i })
    
    expect(button).toHaveClass('border-2')
    expect(button).toHaveClass('border-teal-700')
    expect(button).toHaveClass('text-teal-700')
  })

  it('renders ghost variant with correct styles', () => {
    render(<Button variant="ghost">Ghost</Button>)
    const button = screen.getByRole('button', { name: /ghost/i })
    
    expect(button).toHaveClass('text-teal-700')
  })

  it('is disabled when isLoading is true', () => {
    render(<Button isLoading>Loading</Button>)
    const button = screen.getByRole('button')
    
    expect(button).toBeDisabled()
  })

  it('shows loading text when isLoading is true', () => {
    render(<Button isLoading>Submit</Button>)
    
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>)
    const button = screen.getByRole('button', { name: /disabled/i })
    
    expect(button).toBeDisabled()
  })

  it('does not call onClick when disabled', async () => {
    const handleClick = vi.fn()
    const user = userEvent.setup()
    
    render(<Button onClick={handleClick} disabled>Disabled</Button>)
    
    await user.click(screen.getByRole('button', { name: /disabled/i }))
    
    expect(handleClick).not.toHaveBeenCalled()
  })

  it('forwards ref correctly', () => {
    const ref = vi.fn()
    render(<Button ref={ref}>Button</Button>)
    
    expect(ref).toHaveBeenCalled()
  })
})
