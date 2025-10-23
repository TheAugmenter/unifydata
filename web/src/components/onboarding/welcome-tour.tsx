'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Search,
  Zap,
  Network,
  TrendingUp,
  ChevronRight,
  ChevronLeft,
  X
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { useUpdateOnboardingProgress, useSkipOnboarding } from '@/hooks/use-onboarding'

interface TourStep {
  title: string
  description: string
  icon: React.ReactNode
  details: string[]
}

const tourSteps: TourStep[] = [
  {
    title: 'Welcome to UnifyData.AI',
    description: 'Your enterprise AI-powered unified search platform',
    icon: <Search className="w-12 h-12 text-primary" />,
    details: [
      'Search across all your business tools from one place',
      'Connect Salesforce, Slack, Google Drive, Notion, Gmail and more',
      'Find information instantly with AI-powered semantic search',
      'Never lose track of important data again',
    ],
  },
  {
    title: 'AI-Powered Intelligence',
    description: 'Ask questions in natural language and get instant answers',
    icon: <Zap className="w-12 h-12 text-primary" />,
    details: [
      'Use natural language queries like "What are our Q4 deals?"',
      'AI understands context and finds relevant information',
      'Get results ranked by relevance and recency',
      'Semantic search finds related content automatically',
    ],
  },
  {
    title: 'Knowledge Graph',
    description: 'Visualize relationships between people, projects, and data',
    icon: <Network className="w-12 h-12 text-primary" />,
    details: [
      'See how information is connected across systems',
      'Discover relationships between people, projects, and documents',
      'Interactive visualization helps you understand your data',
      'Click on any node to explore connections',
    ],
  },
  {
    title: 'Enterprise Security',
    description: 'Your data is secure with enterprise-grade protection',
    icon: <TrendingUp className="w-12 h-12 text-primary" />,
    details: [
      'End-to-end encryption for all data',
      'Role-based access control',
      'SOC 2 Type II compliant infrastructure',
      'Your data never leaves your control',
    ],
  },
]

export function WelcomeTour() {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState(0)
  const updateProgress = useUpdateOnboardingProgress()
  const skipOnboarding = useSkipOnboarding()

  const isLastStep = currentStep === tourSteps.length - 1
  const currentTourStep = tourSteps[currentStep]

  const handleNext = () => {
    if (isLastStep) {
      // Move to next onboarding step (connect data source)
      updateProgress.mutate(
        {
          onboarding_step: 1,
          onboarding_completed: false,
        },
        {
          onSuccess: () => {
            router.push('/onboarding/connect-source')
          },
        }
      )
    } else {
      setCurrentStep((prev) => prev + 1)
    }
  }

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1)
    }
  }

  const handleSkip = () => {
    skipOnboarding.mutate(undefined, {
      onSuccess: () => {
        router.push('/dashboard')
      },
    })
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-4">
      <div className="w-full max-w-3xl">
        {/* Skip button */}
        <div className="flex justify-end mb-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleSkip}
            disabled={skipOnboarding.isPending}
          >
            <X className="w-4 h-4 mr-2" />
            Skip tour
          </Button>
        </div>

        {/* Main card */}
        <Card className="border-2 shadow-xl">
          <CardHeader className="text-center pb-4">
            <div className="flex justify-center mb-4">
              {currentTourStep.icon}
            </div>
            <CardTitle className="text-3xl font-bold">
              {currentTourStep.title}
            </CardTitle>
            <CardDescription className="text-lg">
              {currentTourStep.description}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            <ul className="space-y-3">
              {currentTourStep.details.map((detail, index) => (
                <li key={index} className="flex items-start gap-3">
                  <div className="mt-1 w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <div className="w-2 h-2 rounded-full bg-primary" />
                  </div>
                  <span className="text-muted-foreground">{detail}</span>
                </li>
              ))}
            </ul>

            {/* Progress indicator */}
            <div className="flex justify-center gap-2 pt-6">
              {tourSteps.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentStep(index)}
                  className={`w-2 h-2 rounded-full transition-all ${
                    index === currentStep
                      ? 'bg-primary w-8'
                      : 'bg-gray-300 hover:bg-gray-400'
                  }`}
                  aria-label={`Go to step ${index + 1}`}
                />
              ))}
            </div>
          </CardContent>

          <CardFooter className="flex justify-between pt-6">
            <Button
              variant="outline"
              onClick={handlePrevious}
              disabled={currentStep === 0}
            >
              <ChevronLeft className="w-4 h-4 mr-2" />
              Previous
            </Button>

            <div className="text-sm text-muted-foreground">
              Step {currentStep + 1} of {tourSteps.length}
            </div>

            <Button
              onClick={handleNext}
              disabled={updateProgress.isPending}
            >
              {isLastStep ? 'Get Started' : 'Next'}
              <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          </CardFooter>
        </Card>

        {/* Bottom hint */}
        <p className="text-center text-sm text-muted-foreground mt-6">
          This tour will help you get started with UnifyData.AI in just a few minutes
        </p>
      </div>
    </div>
  )
}
