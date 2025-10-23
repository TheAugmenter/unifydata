'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { WelcomeTour } from '@/components/onboarding/welcome-tour'
import { useOnboardingProgress } from '@/hooks/use-onboarding'
import { Loader2 } from 'lucide-react'

export default function OnboardingPage() {
  const router = useRouter()
  const { data: progress, isLoading } = useOnboardingProgress()

  useEffect(() => {
    if (progress) {
      // If onboarding is completed, redirect to dashboard
      if (progress.onboarding_completed) {
        router.push('/dashboard')
        return
      }

      // Redirect based on current step
      if (progress.onboarding_step === 1) {
        router.push('/onboarding/connect-source')
      } else if (progress.onboarding_step === 2) {
        router.push('/onboarding/first-search')
      } else if (progress.onboarding_step === 3) {
        router.push('/dashboard')
      }
    }
  }, [progress, router])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return <WelcomeTour />
}
