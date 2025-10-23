/**
 * Authentication hooks
 */
'use client'

import { useMutation } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { authApi } from '@/lib/auth'
import type { RegisterRequest, LoginRequest, ApiError } from '@/lib/types'
import { AxiosError } from 'axios'

export function useRegister() {
  const router = useRouter()

  return useMutation({
    mutationFn: (data: RegisterRequest) => authApi.register(data),
    onSuccess: (data) => {
      toast.success('Account created successfully!', {
        description: 'Welcome to UnifyData.AI',
      })
      // Redirect to onboarding
      router.push('/onboarding')
    },
    onError: (error: AxiosError<ApiError>) => {
      const errorData = error.response?.data
      toast.error('Registration failed', {
        description: errorData?.message || 'An error occurred during registration',
      })
    },
  })
}

export function useLogin() {
  const router = useRouter()

  return useMutation({
    mutationFn: (data: LoginRequest) => authApi.login(data),
    onSuccess: (data) => {
      toast.success('Welcome back!', {
        description: 'You have successfully logged in',
      })

      // Redirect based on onboarding status
      if (data.user.onboarding_completed) {
        router.push('/dashboard')
      } else {
        router.push('/onboarding')
      }
    },
    onError: (error: AxiosError<ApiError>) => {
      const errorData = error.response?.data
      toast.error('Login failed', {
        description: errorData?.message || 'Invalid email or password',
      })
    },
  })
}

export function useLogout() {
  return () => {
    authApi.logout()
    toast.success('Logged out successfully')
  }
}
