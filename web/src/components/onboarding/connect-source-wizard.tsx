'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Database,
  CheckCircle2,
  ChevronRight,
  Loader2,
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
import { useUpdateOnboardingProgress } from '@/hooks/use-onboarding'
import Image from 'next/image'

interface DataSource {
  id: string
  name: string
  description: string
  icon: string
  color: string
  comingSoon?: boolean
}

const dataSources: DataSource[] = [
  {
    id: 'salesforce',
    name: 'Salesforce',
    description: 'CRM data, opportunities, accounts, contacts',
    icon: '☁️',
    color: 'bg-blue-500',
  },
  {
    id: 'slack',
    name: 'Slack',
    description: 'Messages, channels, files, and conversations',
    icon: '💬',
    color: 'bg-purple-500',
  },
  {
    id: 'google-drive',
    name: 'Google Drive',
    description: 'Documents, spreadsheets, presentations',
    icon: '📁',
    color: 'bg-yellow-500',
  },
  {
    id: 'notion',
    name: 'Notion',
    description: 'Notes, wikis, databases, and documentation',
    icon: '📝',
    color: 'bg-gray-800',
  },
  {
    id: 'gmail',
    name: 'Gmail',
    description: 'Emails, attachments, and threads',
    icon: '✉️',
    color: 'bg-red-500',
  },
]

export function ConnectSourceWizard() {
  const router = useRouter()
  const [selectedSource, setSelectedSource] = useState<string | null>(null)
  const updateProgress = useUpdateOnboardingProgress()

  const handleConnect = () => {
    if (!selectedSource) return

    // TODO: Implement OAuth flow for selected source
    // For now, we'll just move to the next step
    updateProgress.mutate(
      {
        onboarding_step: 2,
        onboarding_completed: false,
      },
      {
        onSuccess: () => {
          router.push('/onboarding/first-search')
        },
      }
    )
  }

  const handleSkip = () => {
    updateProgress.mutate(
      {
        onboarding_step: 2,
        onboarding_completed: false,
      },
      {
        onSuccess: () => {
          router.push('/onboarding/first-search')
        },
      }
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-4">
      <div className="w-full max-w-4xl">
        <Card className="border-2 shadow-xl">
          <CardHeader className="text-center pb-4">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                <Database className="w-8 h-8 text-primary" />
              </div>
            </div>
            <CardTitle className="text-3xl font-bold">
              Connect Your First Data Source
            </CardTitle>
            <CardDescription className="text-lg">
              Choose a data source to connect and start searching
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Info box */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-900">
                <strong>Tip:</strong> You can connect multiple data sources later from
                your dashboard. For now, let's start with one to get you familiar with
                the platform.
              </p>
            </div>

            {/* Data sources grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {dataSources.map((source) => (
                <button
                  key={source.id}
                  onClick={() => setSelectedSource(source.id)}
                  disabled={source.comingSoon}
                  className={`relative p-6 rounded-lg border-2 transition-all text-left ${
                    selectedSource === source.id
                      ? 'border-primary bg-primary/5 shadow-md'
                      : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
                  } ${source.comingSoon ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  <div className="flex items-start gap-4">
                    <div className={`w-12 h-12 rounded-lg ${source.color} flex items-center justify-center text-2xl flex-shrink-0`}>
                      {source.icon}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-lg">{source.name}</h3>
                        {selectedSource === source.id && (
                          <CheckCircle2 className="w-5 h-5 text-primary" />
                        )}
                        {source.comingSoon && (
                          <span className="text-xs bg-gray-200 text-gray-600 px-2 py-1 rounded">
                            Coming Soon
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {source.description}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            {/* Features list */}
            <div className="bg-gray-50 rounded-lg p-6">
              <h4 className="font-semibold mb-3">What happens when you connect?</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Secure OAuth connection - we never store your credentials</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Your data is encrypted at rest and in transit</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Initial sync starts automatically after connection</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>You can disconnect anytime from settings</span>
                </li>
              </ul>
            </div>
          </CardContent>

          <CardFooter className="flex justify-between pt-6">
            <Button variant="outline" onClick={handleSkip}>
              Skip for now
            </Button>

            <div className="text-sm text-muted-foreground">
              Step 2 of 3
            </div>

            <Button
              onClick={handleConnect}
              disabled={!selectedSource || updateProgress.isPending}
            >
              {updateProgress.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Connecting...
                </>
              ) : (
                <>
                  Connect {selectedSource ? dataSources.find(s => s.id === selectedSource)?.name : ''}
                  <ChevronRight className="w-4 h-4 ml-2" />
                </>
              )}
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  )
}
