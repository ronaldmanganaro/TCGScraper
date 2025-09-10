import React from 'react'

interface CloudControlWidgetProps {
  selectedTCG: string
}

const CloudControlWidget: React.FC<CloudControlWidgetProps> = ({ selectedTCG }) => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">☁️ Cloud Control</h2>
        <p className="text-gray-600">Manage cloud services and ECS tasks (Admin Only)</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
        <div className="text-6xl mb-4">☁️</div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Admin Feature</h3>
        <p className="text-gray-600">
          Cloud control and ECS management functionality will be implemented here. This is an admin-only feature for managing cloud services.
        </p>
      </div>
    </div>
  )
}

export default CloudControlWidget




