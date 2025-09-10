import { Routes, Route } from 'react-router-dom'
import Login from './pages/Login'
import Register from './pages/Register'
import Home from './pages/Home'
import Tools from './pages/Tools'
import Repricer from './pages/Repricer'
import EVTools from './pages/EVTools'
import PokemonTracker from './pages/PokemonTracker'
import Manabox from './pages/Manabox'
import ManageInventory from './pages/ManageInventory'
import TCGPlayerOrders from './pages/TCGPlayerOrders'
import CloudControl from './pages/CloudControl'
import UpdateTCGPlayerIDs from './pages/UpdateTCGPlayerIDs'
import ProtectedRoute from './components/ProtectedRoute'
import Navbar from './components/Navbar'
import Sidebar from './components/Sidebar'
import { useAuth } from './contexts/AuthContext'
import { useState, useEffect } from 'react'

function App() {
  const { user } = useAuth()
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(() => {
    const saved = localStorage.getItem('sidebarCollapsed')
    return saved ? JSON.parse(saved) : false
  })

  // Persist sidebar state
  useEffect(() => {
    localStorage.setItem('sidebarCollapsed', JSON.stringify(sidebarCollapsed))
  }, [sidebarCollapsed])

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={<Home />} />
          <Route path="/tools" element={<Tools />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="flex pt-16">
        {/* Collapsible Sidebar */}
        <div 
          className={`${
            sidebarCollapsed ? 'w-16' : 'w-64'
          } bg-white border-r border-gray-200 min-h-screen transition-all duration-300 ease-in-out fixed left-0 top-16 z-40`}
        >
          <div className="p-4">
            {/* Sidebar Toggle Button */}
            <div className="mb-4">
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
            </div>
            
            <Sidebar collapsed={sidebarCollapsed} />
          </div>
        </div>

        {/* Main Content Area */}
        <div 
          className={`flex-1 transition-all duration-300 ease-in-out ${
            sidebarCollapsed ? 'ml-16' : 'ml-64'
          }`}
        >
          <div className="p-6">
            <Routes>
              <Route path="/" element={<ProtectedRoute><Home /></ProtectedRoute>} />
              <Route path="/tools" element={<ProtectedRoute><Tools /></ProtectedRoute>} />
              <Route path="/repricer" element={<ProtectedRoute><Repricer /></ProtectedRoute>} />
              <Route path="/ev-tools" element={<ProtectedRoute><EVTools /></ProtectedRoute>} />
              <Route path="/pokemon-tracker" element={<ProtectedRoute><PokemonTracker /></ProtectedRoute>} />
              <Route path="/manabox" element={<ProtectedRoute><Manabox /></ProtectedRoute>} />
              <Route path="/inventory" element={<ProtectedRoute><ManageInventory /></ProtectedRoute>} />
              <Route path="/tcgplayer-orders" element={<ProtectedRoute><TCGPlayerOrders /></ProtectedRoute>} />
              <Route path="/cloud-control" element={<ProtectedRoute><CloudControl /></ProtectedRoute>} />
              <Route path="/update-tcgplayer-ids" element={<ProtectedRoute><UpdateTCGPlayerIDs /></ProtectedRoute>} />
            </Routes>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App