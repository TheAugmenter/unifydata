/**
 * Onboarding API
 */
import apiClient from '@/lib/api-client'

export interface OnboardingProgress {
  onboarding_step: number
  onboarding_completed: boolean
  message: string
}

export const onboardingApi = {
  /**
   * Get onboarding progress
   */
  getProgress: async (): Promise<OnboardingProgress> => {
    const response = await apiClient.get<OnboardingProgress>('/onboarding/progress')
    return response.data
  },

  /**
   * Update onboarding progress
   */
  updateProgress: async (data: {
    onboarding_step: number
    onboarding_completed: boolean
  }): Promise<OnboardingProgress> => {
    const response = await apiClient.put<OnboardingProgress>('/onboarding/progress', data)
    return response.data
  },

  /**
   * Skip onboarding
   */
  skip: async (): Promise<OnboardingProgress> => {
    const response = await apiClient.post<OnboardingProgress>('/onboarding/skip')
    return response.data
  },

  /**
   * Complete onboarding
   */
  complete: async (): Promise<OnboardingProgress> => {
    const response = await apiClient.post<OnboardingProgress>('/onboarding/complete')
    return response.data
  },
}
