import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useTCG } from '../contexts/TCGContext'
import { TOOL_CATEGORIES, ADMIN_TOOLS, TCG_CATEGORIES, getToolsForTCG, getAdminToolsForTCG, TCGType } from '../utils/tcgCategories'

interface FeatureCardProps {
  title: string
  description: string
  icon: string
  path: string
  color: string
  status?: 'available' | 'coming-soon' | 'beta'
}

const Tools: React.FC = () => {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { selectedTCG, setSelectedTCG } = useTCG()
  const [searchTerm, setSearchTerm] = useState('')

  // Helper functions
  const getColorForPath = (path: string): string => {
    const colorMap: { [key: string]: string } = {
      '/': 'blue',
      '/repricer': 'blue',
      '/ev-tools': 'purple',
      '/pokemon-tracker': 'yellow',
      '/manabox': 'green',
      '/inventory': 'indigo',
      '/tcgplayer-orders': 'gray',
      '/cloud-control': 'cyan',
      '/update-tcgplayer-ids': 'orange',
    }
    return colorMap[path] || 'blue'
  }

  const getStatusForPath = (path: string): string => {
    const statusMap: { [key: string]: string } = {
      '/': 'available',
      '/repricer': 'available',
      '/ev-tools': 'available',
      '/pokemon-tracker': 'coming-soon',
      '/manabox': 'available',
      '/inventory': 'available',
      '/tcgplayer-orders': 'available',
      '/cloud-control': 'beta',
      '/update-tcgplayer-ids': 'available',
    }
    return statusMap[path] || 'available'
  }

  // Get tools based on selected TCG
  const availableTools = getToolsForTCG(selectedTCG)
  const availableAdminTools = user?.is_admin ? getAdminToolsForTCG(selectedTCG) : []

  // Convert tools to features format with status
  const features: FeatureCardProps[] = [
    ...availableTools.map(tool => ({
      title: tool.text,
      description: tool.description,
      icon: tool.icon,
      path: tool.path,
      color: getColorForPath(tool.path),
      status: getStatusForPath(tool.path) as 'available' | 'coming-soon' | 'beta',
    })),
    ...availableAdminTools.map(tool => ({
      title: tool.text,
      description: tool.description,
      icon: tool.icon,
      path: tool.path,
      color: getColorForPath(tool.path),
      status: getStatusForPath(tool.path) as 'available' | 'coming-soon' | 'beta',
    }))
  ]

  const tcgOptions = Object.values(TCG_CATEGORIES).map(tcg => ({
    label: `${tcg.icon} ${tcg.name}`,
    value: tcg.id
  }))

  const handleFeatureClick = (path: string) => {
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
      cyan: 'from-cyan-500 to-cyan-600 hover:from-cyan-600 hover:to-cyan-700',
      orange: 'from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700',
    }
    return colors[color as keyof typeof colors] || colors.blue
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'available':
        return <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Available</span>
      case 'coming-soon':
        return <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">Coming Soon</span>
      case 'beta':
        return <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">Beta</span>
      default:
        return null
    }
  }

  const filteredFeatures = features.filter(feature => {
    const matchesSearch = feature.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         feature.description.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesSearch
  })

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          TCG Management Tools
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Comprehensive toolkit for Magic: The Gathering, Pokémon, and other trading card games
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex flex-col md:flex-row gap-6">
          {/* Search */}
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search Tools
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name or description..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* TCG Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Filter by TCG
            </label>
            <div className="flex flex-wrap gap-2">
              {tcgOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setSelectedTCG(option.value as TCGType)}
                  className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                    selectedTCG === option.value
                      ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-md'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Tools Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredFeatures.map((feature, index) => (
          <div
            key={index}
            className={`bg-white rounded-2xl border border-gray-200 p-6 hover:shadow-xl transition-all duration-300 hover:-translate-y-1 cursor-pointer ${
              feature.status === 'coming-soon' ? 'opacity-75' : ''
            }`}
            onClick={() => feature.status !== 'coming-soon' && handleFeatureClick(feature.path)}
          >
            <div className="text-center mb-4">
              <div className="text-4xl mb-3">{feature.icon}</div>
              <div className="flex items-center justify-center mb-2">
                <h3 className="text-xl font-semibold text-gray-900 mr-2">
                  {feature.title}
                </h3>
                {getStatusBadge(feature.status || 'available')}
              </div>
              <p className="text-gray-600 text-sm leading-relaxed">
                {feature.description}
              </p>
            </div>
            
            <button
              disabled={feature.status === 'coming-soon'}
              className={`w-full py-3 px-4 rounded-lg font-medium transition-all duration-200 transform hover:scale-105 ${
                feature.status === 'coming-soon'
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : `bg-gradient-to-r ${getColorClasses(feature.color)} text-white`
              }`}
            >
              {feature.status === 'coming-soon' 
                ? 'Coming Soon' 
                : user 
                  ? 'Open Tool' 
                  : 'Login to Use'
              }
            </button>
          </div>
        ))}
      </div>

      {/* Results Info */}
      {filteredFeatures.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🔍</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No tools found</h3>
          <p className="text-gray-600">Try adjusting your search terms or filters.</p>
        </div>
      )}

      {filteredFeatures.length > 0 && (
        <div className="text-center text-sm text-gray-500">
          Showing {filteredFeatures.length} of {features.length} tools
        </div>
      )}

      {/* Back to Dashboard */}
      <div className="text-center pt-8">
        <button
          onClick={() => navigate('/')}
          className="bg-gradient-to-r from-gray-600 to-gray-700 text-white font-medium py-3 px-6 rounded-lg hover:from-gray-700 hover:to-gray-800 transition-all duration-200"
        >
          ← Back to Dashboard
        </button>
      </div>
    </div>
  )
}

export default Tools
