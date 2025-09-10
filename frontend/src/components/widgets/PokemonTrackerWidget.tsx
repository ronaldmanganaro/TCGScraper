import React from 'react'

interface PokemonTrackerWidgetProps {
  selectedTCG: string
}

const PokemonTrackerWidget: React.FC<PokemonTrackerWidgetProps> = ({ selectedTCG }) => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">⚡ Pokemon Price Tracker</h2>
        <p className="text-gray-600">Track Pokemon card prices and market trends for {selectedTCG}</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
        <div className="text-6xl mb-4">⚡</div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Coming Soon</h3>
        <p className="text-gray-600">
          Pokemon price tracking functionality is being developed. This will include price history charts, set filtering, and market analysis.
        </p>
      </div>
    </div>
  )
}

export default PokemonTrackerWidget




