import React from 'react'

interface QuickActionsProps {
  selectedTCG: string
}

const QuickActions: React.FC<QuickActionsProps> = ({ selectedTCG }) => {
  return (
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
  )
}

export default QuickActions




