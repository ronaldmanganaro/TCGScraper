import React from 'react'

interface ManaboxWidgetProps {
  selectedTCG: string
}

const ManaboxWidget: React.FC<ManaboxWidgetProps> = ({ selectedTCG }) => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">📦 Manabox Converter</h2>
        <p className="text-gray-600">Convert ManaBox CSV files to TCGPlayer format for {selectedTCG}</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
        <div className="text-6xl mb-4">📦</div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Coming Soon</h3>
        <p className="text-gray-600">
          Manabox CSV conversion functionality will be implemented here. This will allow converting ManaBox exports to TCGPlayer format.
        </p>
      </div>
    </div>
  )
}

export default ManaboxWidget




