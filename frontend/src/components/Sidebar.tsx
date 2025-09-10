import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

interface MenuItemProps {
  text: string
  icon: string
  path: string
  adminOnly?: boolean
}

interface SidebarProps {
  collapsed?: boolean
}

const Sidebar: React.FC<SidebarProps> = ({ collapsed = false }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const { user } = useAuth()

  const menuItems: MenuItemProps[] = [
    { text: 'Dashboard', icon: '🏠', path: '/' },
    { text: 'All Tools', icon: '🛠️', path: '/tools' },
    { text: 'EV Tools', icon: '🎰', path: '/ev-tools' },
    { text: 'Pokemon Tracker', icon: '⚡', path: '/pokemon-tracker' },
    { text: 'Manabox', icon: '📦', path: '/manabox' },
    { text: 'Manage Inventory', icon: '📋', path: '/inventory' },
    { text: 'TCGPlayer Orders', icon: '🖨️', path: '/tcgplayer-orders' },
  ]

  const adminItems: MenuItemProps[] = [
    { text: 'Cloud Control', icon: '☁️', path: '/cloud-control', adminOnly: true },
    { text: 'Update TCGPlayer IDs', icon: '🔄', path: '/update-tcgplayer-ids', adminOnly: true },
  ]

  const handleNavigation = (path: string) => {
    navigate(path)
  }

  const isSelected = (path: string) => location.pathname === path

  if (!user) return null

  return (
    <>
      {/* Main Navigation */}
      <nav className="space-y-1">
        {menuItems.map((item) => (
          <div key={item.text} className="relative group">
            <button
              onClick={() => handleNavigation(item.path)}
              className={`w-full flex items-center ${
                collapsed ? 'justify-center px-2' : 'space-x-3 px-4'
              } py-3 text-left rounded-lg transition-all duration-200 ${
                isSelected(item.path)
                  ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-600'
                  : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
              }`}
              title={collapsed ? item.text : undefined}
            >
              <span className="text-xl">{item.icon}</span>
              {!collapsed && (
                <span className="font-medium">{item.text}</span>
              )}
            </button>
            
            {/* Tooltip for collapsed sidebar */}
            {collapsed && (
              <div className="absolute left-full top-1/2 transform -translate-y-1/2 ml-2 px-2 py-1 bg-gray-900 text-white text-sm rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50">
                {item.text}
              </div>
            )}
          </div>
        ))}
      </nav>

      {/* Admin Section */}
      {user.is_admin && (
        <>
          <div className="mt-8 mb-4">
            {!collapsed && (
              <h3 className="px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Admin Tools
              </h3>
            )}
            {collapsed && (
              <div className="border-t border-gray-200 mx-2"></div>
            )}
          </div>
          <nav className="space-y-1">
            {adminItems.map((item) => (
              <div key={item.text} className="relative group">
                <button
                  onClick={() => handleNavigation(item.path)}
                  className={`w-full flex items-center ${
                    collapsed ? 'justify-center px-2' : 'space-x-3 px-4'
                  } py-3 text-left rounded-lg transition-all duration-200 ${
                    isSelected(item.path)
                      ? 'bg-purple-50 text-purple-700 border-r-2 border-purple-600'
                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                  title={collapsed ? item.text : undefined}
                >
                  <span className="text-xl">{item.icon}</span>
                  {!collapsed && (
                    <span className="font-medium">{item.text}</span>
                  )}
                </button>
                
                {/* Tooltip for collapsed sidebar */}
                {collapsed && (
                  <div className="absolute left-full top-1/2 transform -translate-y-1/2 ml-2 px-2 py-1 bg-gray-900 text-white text-sm rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50">
                    {item.text}
                  </div>
                )}
              </div>
            ))}
          </nav>
        </>
      )}
    </>
  )
}

export default Sidebar