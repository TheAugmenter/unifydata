'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Search,
  Sparkles,
  CheckCircle2,
  ChevronRight,
  Loader2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { useCompleteOnboarding } from '@/hooks/use-onboarding'

const exampleQueries = [
  {
    query: 'What are our Q4 deals?',
    description: 'Find all deals closing in Q4',
    category: 'Sales',
  },
  {
    query: 'Show me recent conversations about pricing',
    description: 'Search across Slack and emails',
    category: 'Conversations',
  },
  {
    query: 'Who is working on Project Alpha?',
    description: 'Find team members and related documents',
    category: 'Team',
  },
  {
    query: 'Find the product roadmap document',
    description: 'Search across Drive, Notion, and more',
    category: 'Documents',
  },
]

export function FirstSearchTutorial() {
  const router = useRouter()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedExample, setSelectedExample] = useState<number | null>(null)
  const completeOnboarding = useCompleteOnboarding()

  const handleTrySearch = () => {
    completeOnboarding.mutate(undefined, {
      onSuccess: () => {
        // Redirect to dashboard with search query
        if (searchQuery) {
          router.push(`/dashboard?q=${encodeURIComponent(searchQuery)}`)
        } else {
          router.push('/dashboard')
        }
      },
    })
  }

  const handleSelectExample = (index: number) => {
    setSelectedExample(index)
    setSearchQuery(exampleQueries[index].query)
  }

  const handleSkip = () => {
    completeOnboarding.mutate(undefined, {
      onSuccess: () => {
        router.push('/dashboard')
      },
    })
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-4">
      <div className="w-full max-w-4xl">
        <Card className="border-2 shadow-xl">
          <CardHeader className="text-center pb-4">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                <Sparkles className="w-8 h-8 text-primary" />
              </div>
            </div>
            <CardTitle className="text-3xl font-bold">
              Try Your First Search
            </CardTitle>
            <CardDescription className="text-lg">
              Ask a question in natural language and see the magic happen
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Search input */}
            <div className="space-y-4">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="Ask anything... (e.g., 'What are our Q4 deals?')"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-12 h-14 text-lg"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && searchQuery) {
                      handleTrySearch()
                    }
                  }}
                />
              </div>
              <p className="text-sm text-muted-foreground text-center">
                Type your question or select an example below
              </p>
            </div>

            {/* Example queries */}
            <div className="space-y-3">
              <h4 className="font-semibold text-sm text-muted-foreground">
                Try these example searches:
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {exampleQueries.map((example, index) => (
                  <button
                    key={index}
                    onClick={() => handleSelectExample(index)}
                    className={`p-4 rounded-lg border-2 transition-all text-left ${
                      selectedExample === index
                        ? 'border-primary bg-primary/5 shadow-sm'
                        : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <Search className="w-4 h-4 text-primary" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-sm">
                            {example.query}
                          </span>
                          {selectedExample === index && (
                            <CheckCircle2 className="w-4 h-4 text-primary" />
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {example.description}
                        </p>
                        <span className="inline-block mt-2 text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                          {example.category}
                        </span>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Features */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
              <h4 className="font-semibold mb-3 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-primary" />
                AI-Powered Search Features
              </h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>
                    <strong>Natural Language:</strong> Ask questions like you would to a
                    colleague
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>
                    <strong>Semantic Search:</strong> Finds related content even without
                    exact matches
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>
                    <strong>Context Aware:</strong> Understands dates, people, and
                    projects automatically
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>
                    <strong>Multi-Source:</strong> Searches across all connected data
                    sources simultaneously
                  </span>
                </li>
              </ul>
            </div>
          </CardContent>

          <CardFooter className="flex justify-between pt-6">
            <Button variant="outline" onClick={handleSkip}>
              Skip tutorial
            </Button>

            <div className="text-sm text-muted-foreground">
              Step 3 of 3
            </div>

            <Button
              onClick={handleTrySearch}
              disabled={!searchQuery || completeOnboarding.isPending}
              size="lg"
            >
              {completeOnboarding.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Loading...
                </>
              ) : (
                <>
                  Try Search
                  <ChevronRight className="w-4 h-4 ml-2" />
                </>
              )}
            </Button>
          </CardFooter>
        </Card>

        {/* Bottom hint */}
        <p className="text-center text-sm text-muted-foreground mt-6">
          You're almost done! After this, you'll be ready to start using UnifyData.AI
        </p>
      </div>
    </div>
  )
}
