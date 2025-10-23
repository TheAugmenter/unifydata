'use client'

import { useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Search, Database, TrendingUp, Zap } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export default function DashboardPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const initialQuery = searchParams.get('q') || ''

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">UnifyData.AI</h1>
            <Button variant="outline" size="sm">
              Settings
            </Button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search bar */}
        <div className="mb-8">
          <div className="relative max-w-3xl mx-auto">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <Input
              type="text"
              placeholder="Search across all your data sources..."
              defaultValue={initialQuery}
              className="pl-12 h-14 text-lg shadow-lg"
            />
          </div>
        </div>

        {/* Welcome message */}
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome to UnifyData.AI
          </h2>
          <p className="text-lg text-gray-600">
            Your unified search platform is ready. Start searching or connect more data sources.
          </p>
        </div>

        {/* Stats cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Connected Sources
              </CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">0</div>
              <p className="text-xs text-muted-foreground">
                Connect your first data source
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Total Searches
              </CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">0</div>
              <p className="text-xs text-muted-foreground">
                Start searching to see stats
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                AI Insights
              </CardTitle>
              <Zap className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">0</div>
              <p className="text-xs text-muted-foreground">
                Generated from your data
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Quick actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>
              Get started with these common tasks
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4">
            <Button className="w-full justify-start" variant="outline">
              <Database className="mr-2 h-4 w-4" />
              Connect a Data Source
            </Button>
            <Button className="w-full justify-start" variant="outline">
              <Search className="mr-2 h-4 w-4" />
              Try Example Searches
            </Button>
            <Button className="w-full justify-start" variant="outline">
              <Zap className="mr-2 h-4 w-4" />
              View Knowledge Graph
            </Button>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
