import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useTCG } from '../contexts/TCGContext'
import { useQuery } from '@tanstack/react-query'
import { inventoryService, adminService, apiService } from '../services/api'
import { TCG_CATEGORIES, TCGType } from '../utils/tcgCategories'

interface QuickActionProps {
  title: string
  description: string
  icon: string
  path: string
  color: string
}

interface MetricCardProps {
  title: string
  value: string | number
  change?: string
  icon: string
  color: string
}

interface RecentActivityItem {
  id: string
  action: string
  timestamp: string
  details: string
  type: 'success' | 'info' | 'warning'
}

const Home: React.FC = () => {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { selectedTCG, setSelectedTCG } = useTCG()
  const [recentActivity, setRecentActivity] = useState<RecentActivityItem[]>([
    {
      id: '1',
      action: 'Inventory Upload',
      timestamp: '2 hours ago',
      details: 'Uploaded 1,247 cards from TCGPlayer export',
      type: 'success'
    },
    {
      id: '2', 
      action: 'EV Calculation',
      timestamp: '4 hours ago',
      details: 'Calculated EV for Duskmourn Draft Booster Box',
      type: 'info'
    },
    {
      id: '3',
      action: 'Price Update',
      timestamp: '1 day ago', 
      details: 'Updated prices for 342 Magic cards',
      type: 'success'
    }
  ])

  // Fetch dashboard data
  const { data: inventoryData } = useQuery({
    queryKey: ['inventory-summary'],
    queryFn: () => inventoryService.getInventory(),
    enabled: !!user,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  const { data: systemStatus } = useQuery({
    queryKey: ['system-status'],
    queryFn: () => apiService.healthCheck(),
    refetchInterval: 30000, // 30 seconds
  })

  const quickActions: QuickActionProps[] = [
    {
      title: 'Upload Inventory',
      description: 'Import your TCGPlayer inventory',
      icon: '📤',
      path: '/repricer',
      color: 'blue',
    },
    {
      title: 'Calculate EV',
      description: 'Run booster box simulation',
      icon: '🎰',
      path: '/ev-tools',
      color: 'purple',
    },
    {
      title: 'Track Prices',
      description: 'Monitor Pokemon prices',
      icon: '⚡',
      path: '/pokemon-tracker',
      color: 'yellow',
    },
    {
      title: 'Convert Files',
      description: 'Process Manabox exports',
      icon: '📦',
      path: '/manabox',
      color: 'green',
    },
  ]

  const handleQuickAction = (path: string) => {
    if (user) {
      navigate(path)
    } else {
      navigate('/login')
    }
  }

  const getColorClasses = (color: string) => {
    const colors = {
      blue: 'from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700',
      purple: 'from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700',
      yellow: 'from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700',
      green: 'from-green-500 to-green-600 hover:from-green-600 hover:to-green-700',
      indigo: 'from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700',
      gray: 'from-gray-500 to-gray-600 hover:from-gray-600 hover:to-gray-700',
      red: 'from-red-500 to-red-600 hover:from-red-600 hover:to-red-700',
    }
    return colors[color as keyof typeof colors] || colors.blue
  }

  // Helper components
  const MetricCard: React.FC<MetricCardProps> = ({ title, value, change, icon, color }) => (
    <div className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {change && (
            <p className={`text-sm mt-1 ${
              change.startsWith('+') ? 'text-green-600' : 'text-red-600'
            }`}>
              {change}
            </p>
          )}
        </div>
        <div className={`text-3xl opacity-80`}>
          {icon}
        </div>
      </div>
    </div>
  )

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Dashboard Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl text-white p-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">
              {user ? `Welcome back, ${user.username}!` : 'Welcome to TCG Scraper'}
            </h1>
            <p className="text-blue-100">
              Your comprehensive dashboard for trading card management
            </p>
          </div>
          <div className="text-6xl opacity-80">🎯</div>
        </div>
        
        {/* TCG Selection in Header */}
        <div className="mt-6">
          <div className="flex flex-wrap gap-2">
            {Object.values(TCG_CATEGORIES).map((tcg) => (
              <button
                key={tcg.id}
                onClick={() => setSelectedTCG(tcg.id)}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  selectedTCG === tcg.id
                    ? 'bg-white text-blue-600 shadow-md'
                    : 'bg-blue-500/20 text-blue-100 hover:bg-blue-500/30'
                }`}
              >
                {tcg.icon} {tcg.id === 'magic' ? 'MTG' : tcg.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {user ? (
        <>
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard
              title="Total Cards"
              value={inventoryData?.total_cards || '---'}
              change="+12% this week"
              icon="📊"
              color="blue"
            />
            <MetricCard
              title="Inventory Value"
              value={inventoryData?.total_value ? `$${inventoryData.total_value.toLocaleString()}` : '$---'}
              change="+5.2% this month"
              icon="💰"
              color="green"
            />
            <MetricCard
              title="Recent EV Sims"
              value="24"
              change="+8 today"
              icon="🎰"
              color="purple"
            />
            <MetricCard
              title="System Status"
              value={systemStatus?.status === 'healthy' ? 'Online' : 'Checking...'}
              icon={systemStatus?.status === 'healthy' ? '✅' : '⏳'}
              color={systemStatus?.status === 'healthy' ? 'green' : 'yellow'}
            />
          </div>

          {/* Main Dashboard Content */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Quick Actions */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Quick Actions</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {quickActions.map((action, index) => (
                    <div
                      key={index}
                      className="group cursor-pointer"
                      onClick={() => handleQuickAction(action.path)}
                    >
                      <div className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-all duration-200 group-hover:shadow-md">
                        <div className="flex items-center space-x-3">
                          <div className="text-2xl">{action.icon}</div>
                          <div>
                            <h3 className="font-semibold text-gray-900 group-hover:text-blue-600">
                              {action.title}
                            </h3>
                            <p className="text-sm text-gray-600">{action.description}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* View All Tools Button */}
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <button
                    onClick={() => navigate('/tools')}
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium py-3 px-4 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200"
                  >
                    View All Tools →
                  </button>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Recent Activity</h2>
              <div className="space-y-4">
                {recentActivity.map((activity) => (
                  <div key={activity.id} className="flex items-start space-x-3">
                    <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                      activity.type === 'success' ? 'bg-green-500' : 
                      activity.type === 'info' ? 'bg-blue-500' : 'bg-yellow-500'
                    }`} />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{activity.action}</p>
                      <p className="text-xs text-gray-600 mt-1">{activity.details}</p>
                      <p className="text-xs text-gray-500 mt-1">{activity.timestamp}</p>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-6 pt-6 border-t border-gray-200">
                <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                  View All Activity →
                </button>
              </div>
            </div>
          </div>

          {/* Current TCG Focus */}
          <div className="bg-gradient-to-r from-gray-50 to-blue-50 rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Current Focus: {TCG_CATEGORIES[selectedTCG]?.name || selectedTCG}
                </h3>
                <p className="text-gray-700">
                  {selectedTCG === 'magic' && 
                    'Optimized for MTG inventory management, EV calculations, and price tracking.'}
                  {selectedTCG === 'pokemon' && 
                    'Specialized tools for Pokemon card price tracking and collection management.'}
                  {selectedTCG === 'all' && 
                    'Access to all available tools for comprehensive TCG management.'}
                </p>
              </div>
              <div className="text-4xl">
                {TCG_CATEGORIES[selectedTCG]?.icon || '🎴'}
              </div>
            </div>
          </div>
        </>
      ) : (
        /* Not Logged In State */
        <div className="text-center py-16">
          <div className="text-6xl mb-6">🔐</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Login to Access Your Dashboard</h2>
          <p className="text-gray-600 mb-8 max-w-md mx-auto">
            Sign in to view your inventory metrics, recent activity, and access all TCG management tools.
          </p>
          <div className="space-x-4">
            <button
              onClick={() => navigate('/login')}
              className="bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium py-3 px-6 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200"
            >
              Login
            </button>
            <button
              onClick={() => navigate('/register')}
              className="bg-white text-gray-700 border border-gray-300 font-medium py-3 px-6 rounded-lg hover:bg-gray-50 transition-all duration-200"
            >
              Sign Up
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default Home