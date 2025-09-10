import React from 'react'

interface StatsOverviewProps {
  selectedTCG: string
}

const StatsOverview: React.FC<StatsOverviewProps> = ({ selectedTCG }) => {
  const stats = [
    { label: 'Total Inventory Value', value: '$12,485', change: '+5.2%', changeType: 'positive' },
    { label: 'Cards in Stock', value: '1,247', change: '+12', changeType: 'positive' },
    { label: 'Orders This Month', value: '89', change: '+15.3%', changeType: 'positive' },
    { label: 'Average Sale Price', value: '$24.50', change: '-2.1%', changeType: 'negative' },
  ]

  const recentActivity = [
    { action: 'Price updated', item: 'Black Lotus (Beta)', time: '2 minutes ago', type: 'update' },
    { action: 'New order', item: 'Lightning Bolt x4', time: '15 minutes ago', type: 'sale' },
    { action: 'Inventory added', item: 'Booster Box - Dominaria', time: '1 hour ago', type: 'inventory' },
    { action: 'EV calculated', item: 'Duskmourn Box Simulation', time: '2 hours ago', type: 'analysis' },
  ]

  const topCards = [
    { name: 'Black Lotus', set: 'Beta', price: '$8,500', quantity: 1 },
    { name: 'Mox Ruby', set: 'Beta', price: '$2,200', quantity: 2 },
    { name: 'Time Walk', set: 'Beta', price: '$1,800', quantity: 1 },
    { name: 'Ancestral Recall', set: 'Beta', price: '$1,500', quantity: 1 },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Dashboard Overview</h2>
        <p className="text-gray-600 mt-1">Welcome back! Here's what's happening with your {selectedTCG} business.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div key={index} className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900 mt-2">{stat.value}</p>
              </div>
              <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                stat.changeType === 'positive' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {stat.change}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
          <div className="space-y-4">
            {recentActivity.map((activity, index) => (
              <div key={index} className="flex items-center space-x-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
                  activity.type === 'update' ? 'bg-blue-100 text-blue-600' :
                  activity.type === 'sale' ? 'bg-green-100 text-green-600' :
                  activity.type === 'inventory' ? 'bg-purple-100 text-purple-600' :
                  'bg-orange-100 text-orange-600'
                }`}>
                  {activity.type === 'update' ? '📝' :
                   activity.type === 'sale' ? '💰' :
                   activity.type === 'inventory' ? '📦' : '📊'}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{activity.action}</p>
                  <p className="text-sm text-gray-600">{activity.item}</p>
                </div>
                <p className="text-xs text-gray-400">{activity.time}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Top Value Cards */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Highest Value Cards</h3>
          <div className="space-y-4">
            {topCards.map((card, index) => (
              <div key={index} className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">{card.name}</p>
                  <p className="text-sm text-gray-600">{card.set}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-gray-900">{card.price}</p>
                  <p className="text-xs text-gray-500">Qty: {card.quantity}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-6 text-white">
        <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="bg-white/20 hover:bg-white/30 rounded-lg p-4 text-left transition-colors">
            <div className="text-2xl mb-2">📤</div>
            <p className="font-medium">Upload Inventory</p>
            <p className="text-sm opacity-90">Add new cards to your collection</p>
          </button>
          <button className="bg-white/20 hover:bg-white/30 rounded-lg p-4 text-left transition-colors">
            <div className="text-2xl mb-2">🎰</div>
            <p className="font-medium">Run EV Simulation</p>
            <p className="text-sm opacity-90">Calculate booster box values</p>
          </button>
          <button className="bg-white/20 hover:bg-white/30 rounded-lg p-4 text-left transition-colors">
            <div className="text-2xl mb-2">💲</div>
            <p className="font-medium">Update Prices</p>
            <p className="text-sm opacity-90">Reprice your inventory</p>
          </button>
        </div>
      </div>
    </div>
  )
}

export default StatsOverview




