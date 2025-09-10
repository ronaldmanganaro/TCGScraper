import React, { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useTCG } from '../contexts/TCGContext'
import { TCG_CATEGORIES, TCGType } from '../utils/tcgCategories'
import RepricerWidget from '../components/widgets/RepricerWidget'
import EVToolsWidget from '../components/widgets/EVToolsWidget'
import PokemonTrackerWidget from '../components/widgets/PokemonTrackerWidget'
import ManaboxWidget from '../components/widgets/ManaboxWidget'
import InventoryWidget from '../components/widgets/InventoryWidget'
import TCGPlayerOrdersWidget from '../components/widgets/TCGPlayerOrdersWidget'
import CloudControlWidget from '../components/widgets/CloudControlWidget'
import StatsOverview from '../components/dashboard/StatsOverview'
import QuickActions from '../components/dashboard/QuickActions'

type WidgetType = 'repricer' | 'ev-tools' | 'pokemon' | 'manabox' | 'inventory' | 'orders' | 'cloud-control' | 'overview'

const Dashboard: React.FC = () => {
  const { user } = useAuth()
  const { selectedTCG, setSelectedTCG } = useTCG()
  const [activeWidget, setActiveWidget] = useState<WidgetType>('overview')
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(() => {
    const saved = localStorage.getItem('sidebarCollapsed')
    return saved ? JSON.parse(saved) : false
  })

  // Persist sidebar state
  useEffect(() => {
    localStorage.setItem('sidebarCollapsed', JSON.stringify(sidebarCollapsed))
  }, [sidebarCollapsed])

  const widgets = [
    { id: 'overview', name: 'Overview', icon: '📊', component: StatsOverview },
    { id: 'repricer', name: 'Repricer', icon: '💲', component: RepricerWidget },
    { id: 'ev-tools', name: 'EV Tools', icon: '🎰', component: EVToolsWidget },
    { id: 'pokemon', name: 'Pokemon Tracker', icon: '⚡', component: PokemonTrackerWidget },
    { id: 'manabox', name: 'Manabox', icon: '📦', component: ManaboxWidget },
    { id: 'inventory', name: 'Inventory', icon: '📋', component: InventoryWidget },
    { id: 'orders', name: 'TCGPlayer Orders', icon: '🖨️', component: TCGPlayerOrdersWidget },
  ]

  const adminWidgets = [
    { id: 'cloud-control', name: 'Cloud Control', icon: '☁️', component: CloudControlWidget },
  ]

  const tcgOptions = Object.values(TCG_CATEGORIES).map(tcg => ({
    label: `${tcg.icon} ${tcg.name}`,
    value: tcg.id
  }))

  const ActiveComponent = widgets.find(w => w.id === activeWidget)?.component || 
                          adminWidgets.find(w => w.id === activeWidget)?.component ||
                          StatsOverview

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {/* Sidebar Toggle Button */}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              <svg 
                className="w-5 h-5 text-gray-600" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                {sidebarCollapsed ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                )}
              </svg>
            </button>
            
            <div>
              <h1 className="text-2xl font-bold text-gray-900">TCG Dashboard</h1>
              <p className="text-gray-600">Manage your trading card business</p>
            </div>
          </div>
          
          {/* TCG Selector */}
          <div className="flex items-center space-x-3">
            <span className="text-sm font-medium text-gray-700">Current TCG:</span>
            <select
              value={selectedTCG}
              onChange={(e) => setSelectedTCG(e.target.value as TCGType)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {tcgOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="flex">
        {/* Sidebar Navigation */}
        <div 
          className={`${
            sidebarCollapsed ? 'w-16' : 'w-64'
          } bg-white border-r border-gray-200 min-h-screen transition-all duration-300 ease-in-out`}
        >
          <div className="p-4">
            <nav className="space-y-1">
              {widgets.map((widget) => (
                <div key={widget.id} className="relative group">
                  <button
                    onClick={() => setActiveWidget(widget.id as WidgetType)}
                    className={`w-full flex items-center ${
                      sidebarCollapsed ? 'justify-center px-2' : 'space-x-3 px-4'
                    } py-3 text-left rounded-lg transition-all duration-200 ${
                      activeWidget === widget.id
                        ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-600'
                        : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                    title={sidebarCollapsed ? widget.name : undefined}
                  >
                    <span className="text-xl">{widget.icon}</span>
                    {!sidebarCollapsed && (
                      <span className="font-medium">{widget.name}</span>
                    )}
                  </button>
                  
                  {/* Tooltip for collapsed sidebar */}
                  {sidebarCollapsed && (
                    <div className="absolute left-full top-1/2 transform -translate-y-1/2 ml-2 px-2 py-1 bg-gray-900 text-white text-sm rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50">
                      {widget.name}
                    </div>
                  )}
                </div>
              ))}

              {/* Admin Section */}
              {user?.is_admin && (
                <>
                  <div className="mt-6 mb-3">
                    {!sidebarCollapsed && (
                      <h3 className="px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                        Admin Tools
                      </h3>
                    )}
                    {sidebarCollapsed && (
                      <div className="border-t border-gray-200 mx-2"></div>
                    )}
                  </div>
                  {adminWidgets.map((widget) => (
                    <div key={widget.id} className="relative group">
                      <button
                        onClick={() => setActiveWidget(widget.id as WidgetType)}
                        className={`w-full flex items-center ${
                          sidebarCollapsed ? 'justify-center px-2' : 'space-x-3 px-4'
                        } py-3 text-left rounded-lg transition-all duration-200 ${
                          activeWidget === widget.id
                            ? 'bg-purple-50 text-purple-700 border-r-2 border-purple-600'
                            : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                        }`}
                        title={sidebarCollapsed ? widget.name : undefined}
                      >
                        <span className="text-xl">{widget.icon}</span>
                        {!sidebarCollapsed && (
                          <span className="font-medium">{widget.name}</span>
                        )}
                      </button>
                      
                      {/* Tooltip for collapsed sidebar */}
                      {sidebarCollapsed && (
                        <div className="absolute left-full top-1/2 transform -translate-y-1/2 ml-2 px-2 py-1 bg-gray-900 text-white text-sm rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50">
                          {widget.name}
                        </div>
                      )}
                    </div>
                  ))}
                </>
              )}
            </nav>
          </div>
        </div>

        {/* Main Content Area */}
        <div className={`flex-1 p-6 transition-all duration-300 ease-in-out ${
          sidebarCollapsed ? 'ml-0' : 'ml-0'
        }`}>
          <ActiveComponent selectedTCG={selectedTCG} />
        </div>
      </div>
    </div>
  )
}

export default Dashboard

