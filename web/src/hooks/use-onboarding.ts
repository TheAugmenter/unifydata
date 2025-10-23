/**
 * Onboarding hooks
 */
'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { onboardingApi } from '@/lib/api/onboarding'

const ONBOARDING_QUERY_KEY = ['onboarding', 'progress']

export function useOnboardingProgress() {
  return useQuery({
    queryKey: ONBOARDING_QUERY_KEY,
    queryFn: onboardingApi.getProgress,
  })
}

export function useUpdateOnboardingProgress() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: onboardingApi.updateProgress,
    onSuccess: (data) => {
      queryClient.setQueryData(ONBOARDING_QUERY_KEY, data)
    },
    onError: () => {
      toast.error('Failed to update onboarding progress')
    },
  })
}

export function useSkipOnboarding() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: onboardingApi.skip,
    onSuccess: (data) => {
      queryClient.setQueryData(ONBOARDING_QUERY_KEY, data)
      toast.success('Onboarding skipped')
    },
    onError: () => {
      toast.error('Failed to skip onboarding')
    },
  })
}

export function useCompleteOnboarding() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: onboardingApi.complete,
    onSuccess: (data) => {
      queryClient.setQueryData(ONBOARDING_QUERY_KEY, data)
      toast.success('Onboarding completed!', {
        description: 'Welcome to UnifyData.AI',
      })
    },
    onError: () => {
      toast.error('Failed to complete onboarding')
    },
  })
}
