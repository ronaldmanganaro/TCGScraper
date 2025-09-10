import React from 'react'

interface TCGPlayerOrdersWidgetProps {
  selectedTCG: string
}

const TCGPlayerOrdersWidget: React.FC<TCGPlayerOrdersWidgetProps> = ({ selectedTCG }) => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">🖨️ TCGPlayer Orders</h2>
        <p className="text-gray-600">Extract and process TCGPlayer order information for {selectedTCG}</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
        <div className="text-6xl mb-4">🖨️</div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Coming Soon</h3>
        <p className="text-gray-600">
          TCGPlayer order processing functionality will be implemented here. This will include PDF extraction and order printing capabilities.
        </p>
      </div>
    </div>
  )
}

export default TCGPlayerOrdersWidget




