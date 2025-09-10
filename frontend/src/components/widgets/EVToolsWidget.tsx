import React, { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { evToolsService } from '../../services/api'

interface EVToolsWidgetProps {
  selectedTCG: string
}

const EVToolsWidget: React.FC<EVToolsWidgetProps> = ({ selectedTCG }) => {
  const [activeTab, setActiveTab] = useState<'box' | 'precon'>('box')
  const [setCode, setSetCode] = useState('dft')
  const [boxesToOpen, setBoxesToOpen] = useState(1)
  const [preconName, setPreconName] = useState('')
  const [preconSet, setPreconSet] = useState('')
  const [simulationHistory, setSimulationHistory] = useState<any[]>([])

  const boxSimMutation = useMutation({
    mutationFn: ({ setCode, boxes }: { setCode: string; boxes: number }) =>
      evToolsService.simulateBoosterBox(setCode, boxes),
    onSuccess: (data) => {
      setSimulationHistory(prev => [data, ...prev.slice(0, 4)]) // Keep last 5 results
    }
  })

  const preconMutation = useMutation({
    mutationFn: ({ name, set }: { name: string; set: string }) =>
      evToolsService.calculatePreconEV(name, set),
    onSuccess: (data) => {
      setSimulationHistory(prev => [data, ...prev.slice(0, 4)])
    }
  })

  const handleBoxSimulation = () => {
    boxSimMutation.mutate({ setCode, boxes: boxesToOpen })
  }

  const handlePreconCalculation = () => {
    preconMutation.mutate({ name: preconName, set: preconSet })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">🎰 EV Tools</h2>
        <p className="text-gray-600">Calculate expected values for {selectedTCG} products</p>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('box')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'box'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Booster Box EV
            </button>
            <button
              onClick={() => setActiveTab('precon')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'precon'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Precon EV
            </button>
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'box' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Booster Box Simulation</h3>
                <p className="text-gray-600 mb-4">Simulate expected value from booster box pulls</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Set Code
                  </label>
                  <input
                    type="text"
                    value={setCode}
                    onChange={(e) => setSetCode(e.target.value)}
                    placeholder="e.g., dft"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Boxes to Open
                  </label>
                  <input
                    type="number"
                    value={boxesToOpen}
                    onChange={(e) => setBoxesToOpen(Number(e.target.value))}
                    min="1"
                    max="100"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div className="flex items-end">
                  <button
                    onClick={handleBoxSimulation}
                    disabled={boxSimMutation.isPending}
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium py-2 px-4 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 disabled:opacity-50"
                  >
                    {boxSimMutation.isPending ? (
                      <div className="flex items-center justify-center">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Simulating...
                      </div>
                    ) : (
                      'Simulate!'
                    )}
                  </button>
                </div>
              </div>

              {boxSimMutation.isSuccess && (
                <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-3">Simulation Results</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center">
                      <p className="text-2xl font-bold text-green-600">
                        ${boxSimMutation.data.total_ev}
                      </p>
                      <p className="text-sm text-gray-600">Total EV</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-blue-600">
                        ${boxSimMutation.data.average_ev_per_box}
                      </p>
                      <p className="text-sm text-gray-600">Average per Box</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-purple-600">
                        {boxSimMutation.data.boxes_opened}
                      </p>
                      <p className="text-sm text-gray-600">Boxes Opened</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'precon' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Preconstructed Deck EV</h3>
                <p className="text-gray-600 mb-4">Calculate the expected value of preconstructed decks</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Precon Name
                  </label>
                  <input
                    type="text"
                    value={preconName}
                    onChange={(e) => setPreconName(e.target.value)}
                    placeholder="e.g., Eternal Might"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Set Code
                  </label>
                  <input
                    type="text"
                    value={preconSet}
                    onChange={(e) => setPreconSet(e.target.value)}
                    placeholder="e.g., DFT"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div className="flex items-end">
                  <button
                    onClick={handlePreconCalculation}
                    disabled={preconMutation.isPending}
                    className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-medium py-2 px-4 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all duration-200 disabled:opacity-50"
                  >
                    {preconMutation.isPending ? (
                      <div className="flex items-center justify-center">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Calculating...
                      </div>
                    ) : (
                      'Calculate EV'
                    )}
                  </button>
                </div>
              </div>

              {preconMutation.isSuccess && (
                <div className="bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg p-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-3">Precon EV Results</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center">
                      <p className="text-2xl font-bold text-purple-600">
                        ${preconMutation.data.total_ev}
                      </p>
                      <p className="text-sm text-gray-600">Total EV</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-pink-600">
                        {preconMutation.data.summary?.unique_cards || 0}
                      </p>
                      <p className="text-sm text-gray-600">Unique Cards</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-indigo-600">
                        {preconMutation.data.precon_name}
                      </p>
                      <p className="text-sm text-gray-600">Precon Name</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Simulation History */}
      {simulationHistory.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Simulations</h3>
          <div className="space-y-3">
            {simulationHistory.map((result, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">
                    {result.set_code || result.precon_name} 
                    {result.boxes_opened && ` (${result.boxes_opened} boxes)`}
                  </p>
                  <p className="text-sm text-gray-600">
                    {new Date().toLocaleTimeString()}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-semibold text-gray-900">
                    ${result.total_ev || result.average_ev_per_box}
                  </p>
                  <p className="text-sm text-gray-600">
                    {result.boxes_opened ? 'Total EV' : 'EV'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default EVToolsWidget




