import React, { useState, useCallback } from 'react'
import { useMutation } from '@tanstack/react-query'
import { repricerService } from '../../services/api'

interface RepricerWidgetProps {
  selectedTCG: string
}

interface InventoryItem {
  id: string
  'Product Name': string
  'Set Name': string
  'Rarity': string
  'Total Quantity': number
  'TCG Marketplace Price': number
  'TCG Market Price': number
  'Product Line': string
}

const RepricerWidget: React.FC<RepricerWidgetProps> = ({ selectedTCG }) => {
  const [uploadedData, setUploadedData] = useState<InventoryItem[]>([])
  const [filteredData, setFilteredData] = useState<InventoryItem[]>([])
  const [selectedItems, setSelectedItems] = useState<string[]>([])
  const [filters, setFilters] = useState({
    minPrice: 0,
    maxPrice: 1000,
    searchText: '',
  })

  // File upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => repricerService.uploadInventory(file),
    onSuccess: (data) => {
      setUploadedData(data.data_preview)
      setFilteredData(data.data_preview)
    },
  })

  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      uploadMutation.mutate(file)
    }
  }, [uploadMutation])

  const handleFilterChange = (key: string, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }))
    
    // Apply filters immediately
    const filtered = uploadedData.filter(item => {
      const price = item['TCG Marketplace Price']
      const name = item['Product Name'].toLowerCase()
      const searchTerm = filters.searchText.toLowerCase()
      
      return price >= filters.minPrice && 
             price <= filters.maxPrice && 
             (searchTerm === '' || name.includes(searchTerm))
    })
    setFilteredData(filtered)
  }

  const toggleItemSelection = (id: string) => {
    setSelectedItems(prev => 
      prev.includes(id) 
        ? prev.filter(item => item !== id)
        : [...prev, id]
    )
  }

  const selectAll = () => {
    setSelectedItems(filteredData.map(item => item.id))
  }

  const clearSelection = () => {
    setSelectedItems([])
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">💲 Repricer</h2>
          <p className="text-gray-600">Upload and manage your inventory pricing for {selectedTCG}</p>
        </div>
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Inventory</h3>
        
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-gray-400 transition-colors">
          <input
            type="file"
            accept=".csv"
            onChange={handleFileUpload}
            className="hidden"
            id="file-upload"
            disabled={uploadMutation.isPending}
          />
          <label 
            htmlFor="file-upload" 
            className="cursor-pointer flex flex-col items-center space-y-2"
          >
            <div className="text-4xl">📤</div>
            <p className="text-lg font-medium text-gray-900">
              {uploadMutation.isPending ? 'Uploading...' : 'Click to upload CSV'}
            </p>
            <p className="text-sm text-gray-500">
              Supports TCGPlayer inventory exports
            </p>
          </label>
        </div>

        {uploadMutation.isError && (
          <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            Upload failed. Please check your file format.
          </div>
        )}

        {uploadMutation.isSuccess && (
          <div className="mt-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
            Successfully uploaded {uploadedData.length} items
          </div>
        )}
      </div>

      {/* Filters and Data */}
      {uploadedData.length > 0 && (
        <>
          {/* Filters */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Filters</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Search Products
                </label>
                <input
                  type="text"
                  value={filters.searchText}
                  onChange={(e) => handleFilterChange('searchText', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Search by card name..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Min Price ($)
                </label>
                <input
                  type="number"
                  value={filters.minPrice}
                  onChange={(e) => handleFilterChange('minPrice', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Price ($)
                </label>
                <input
                  type="number"
                  value={filters.maxPrice}
                  onChange={(e) => handleFilterChange('maxPrice', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Selection Controls */}
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <span className="text-sm font-medium text-gray-700">
                  {selectedItems.length} of {filteredData.length} items selected
                </span>
                <button
                  onClick={selectAll}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  Select All
                </button>
                <button
                  onClick={clearSelection}
                  className="text-sm text-gray-600 hover:text-gray-700 font-medium"
                >
                  Clear Selection
                </button>
              </div>
              
              {selectedItems.length > 0 && (
                <div className="flex items-center space-x-2">
                  <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                    Update Prices
                  </button>
                  <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
                    Export Selected
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Data Table */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <input
                        type="checkbox"
                        checked={selectedItems.length === filteredData.length && filteredData.length > 0}
                        onChange={selectedItems.length === filteredData.length ? clearSelection : selectAll}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Product
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Set
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quantity
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Current Price
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Market Price
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Difference
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredData.map((item, index) => {
                    const difference = item['TCG Marketplace Price'] - item['TCG Market Price']
                    const percentDiff = item['TCG Market Price'] > 0 
                      ? ((difference / item['TCG Market Price']) * 100).toFixed(1)
                      : '0.0'
                    
                    return (
                      <tr key={index} className={selectedItems.includes(item.id) ? 'bg-blue-50' : 'hover:bg-gray-50'}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="checkbox"
                            checked={selectedItems.includes(item.id)}
                            onChange={() => toggleItemSelection(item.id)}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm font-medium text-gray-900">{item['Product Name']}</div>
                          <div className="text-sm text-gray-500">{item['Rarity']}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {item['Set Name']}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {item['Total Quantity']}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          ${item['TCG Marketplace Price'].toFixed(2)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          ${item['TCG Market Price'].toFixed(2)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            difference > 0 
                              ? 'bg-green-100 text-green-800' 
                              : difference < 0 
                              ? 'bg-red-100 text-red-800' 
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {difference >= 0 ? '+' : ''}{percentDiff}%
                          </span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default RepricerWidget




