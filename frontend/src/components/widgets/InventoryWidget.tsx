import React from 'react'

interface InventoryWidgetProps {
  selectedTCG: string
}

const InventoryWidget: React.FC<InventoryWidgetProps> = ({ selectedTCG }) => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">📋 Inventory Management</h2>
        <p className="text-gray-600">View and manage your complete {selectedTCG} card inventory</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
        <div className="text-6xl mb-4">📋</div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Coming Soon</h3>
        <p className="text-gray-600">
          Inventory management functionality will be implemented here. This will include viewing, editing, and organizing your card collection.
        </p>
      </div>
    </div>
  )
}

export default InventoryWidget




