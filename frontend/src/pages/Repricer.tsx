import React, { useState, useCallback } from 'react'
import {
  Box,
  Typography,
  Paper,
  Button,
  TextField,
  Grid,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Chip,
  Divider,
} from '@mui/material'
import { DataGrid, GridColDef, GridRowSelectionModel } from '@mui/x-data-grid'
import { Upload, FilterList, PriceChange, Download } from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { repricerService } from '../services/api'

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

interface FilterState {
  minPrice: number
  maxPrice: number
  minListing: number
  maxListing: number
  productLine: string
  setName: string
  rarityFilter: string
  searchText: string
}

const Repricer: React.FC = () => {
  const [uploadedData, setUploadedData] = useState<InventoryItem[]>([])
  const [filteredData, setFilteredData] = useState<InventoryItem[]>([])
  const [selectedRows, setSelectedRows] = useState<GridRowSelectionModel>([])
  const [filters, setFilters] = useState<FilterState>({
    minPrice: 0,
    maxPrice: 1000,
    minListing: 0,
    maxListing: 1000,
    productLine: 'All',
    setName: 'All',
    rarityFilter: 'All',
    searchText: '',
  })
  const [updateMethod, setUpdateMethod] = useState<'percentage' | 'fixed' | 'market_price'>('percentage')
  const [percentageChange, setPercentageChange] = useState<number>(0)
  const [fixedPrice, setFixedPrice] = useState<number>(0)

  const queryClient = useQueryClient()

  // File upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => repricerService.uploadInventory(file),
    onSuccess: (data) => {
      setUploadedData(data.data_preview)
      setFilteredData(data.data_preview)
    },
  })

  // Filter mutation
  const filterMutation = useMutation({
    mutationFn: (filterData: FilterState) => repricerService.filterInventory(filterData),
    onSuccess: (data) => {
      setFilteredData(data.filtered_data)
    },
  })

  // Price update mutation
  const updatePricesMutation = useMutation({
    mutationFn: (updateData: any) => repricerService.updatePrices(updateData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] })
      setSelectedRows([])
    },
  })

  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      uploadMutation.mutate(file)
    }
  }, [uploadMutation])

  const handleApplyFilters = useCallback(() => {
    filterMutation.mutate(filters)
  }, [filters, filterMutation])

  const handleUpdatePrices = useCallback(() => {
    const selectedItems = filteredData.filter(item => 
      selectedRows.includes(item.id)
    )

    const updateData = {
      updates: selectedItems,
      update_method: updateMethod,
      percentage_change: updateMethod === 'percentage' ? percentageChange : undefined,
      fixed_price: updateMethod === 'fixed' ? fixedPrice : undefined,
    }

    updatePricesMutation.mutate(updateData)
  }, [selectedRows, filteredData, updateMethod, percentageChange, fixedPrice, updatePricesMutation])

  const columns: GridColDef[] = [
    { field: 'Product Name', headerName: 'Product Name', width: 300 },
    { field: 'Set Name', headerName: 'Set Name', width: 150 },
    { field: 'Rarity', headerName: 'Rarity', width: 100 },
    { 
      field: 'Total Quantity', 
      headerName: 'Quantity', 
      width: 100,
      type: 'number',
    },
    { 
      field: 'TCG Marketplace Price', 
      headerName: 'Current Price', 
      width: 120,
      type: 'number',
      valueFormatter: (params) => `$${params.value?.toFixed(2) || '0.00'}`,
    },
    { 
      field: 'TCG Market Price', 
      headerName: 'Market Price', 
      width: 120,
      type: 'number',
      valueFormatter: (params) => `$${params.value?.toFixed(2) || '0.00'}`,
    },
    {
      field: 'difference',
      headerName: 'Difference',
      width: 120,
      renderCell: (params) => {
        const current = params.row['TCG Marketplace Price'] || 0
        const market = params.row['TCG Market Price'] || 0
        const diff = current - market
        const percentage = market > 0 ? ((diff / market) * 100).toFixed(1) : '0.0'
        
        return (
          <Chip
            label={`${diff >= 0 ? '+' : ''}${percentage}%`}
            color={diff > 0 ? 'success' : diff < 0 ? 'error' : 'default'}
            size="small"
          />
        )
      },
    },
  ]

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        💲 Repricer
      </Typography>

      {/* File Upload Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Upload Inventory
          </Typography>
          <input
            accept=".csv"
            style={{ display: 'none' }}
            id="file-upload"
            type="file"
            onChange={handleFileUpload}
          />
          <label htmlFor="file-upload">
            <Button
              variant="contained"
              component="span"
              startIcon={<Upload />}
              disabled={uploadMutation.isPending}
            >
              {uploadMutation.isPending ? 'Uploading...' : 'Upload CSV'}
            </Button>
          </label>
          
          {uploadMutation.isError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              Upload failed. Please check your file format.
            </Alert>
          )}
          
          {uploadMutation.isSuccess && (
            <Alert severity="success" sx={{ mt: 2 }}>
              Successfully uploaded {uploadedData.length} items
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Filters Section */}
      {uploadedData.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <FilterList sx={{ mr: 1, verticalAlign: 'middle' }} />
              Filters
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  fullWidth
                  label="Min Price"
                  type="number"
                  value={filters.minPrice}
                  onChange={(e) => setFilters(prev => ({ ...prev, minPrice: Number(e.target.value) }))}
                  InputProps={{ startAdornment: '$' }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  fullWidth
                  label="Max Price"
                  type="number"
                  value={filters.maxPrice}
                  onChange={(e) => setFilters(prev => ({ ...prev, maxPrice: Number(e.target.value) }))}
                  InputProps={{ startAdornment: '$' }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  fullWidth
                  label="Min Quantity"
                  type="number"
                  value={filters.minListing}
                  onChange={(e) => setFilters(prev => ({ ...prev, minListing: Number(e.target.value) }))}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  fullWidth
                  label="Max Quantity"
                  type="number"
                  value={filters.maxListing}
                  onChange={(e) => setFilters(prev => ({ ...prev, maxListing: Number(e.target.value) }))}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Search Products"
                  value={filters.searchText}
                  onChange={(e) => setFilters(prev => ({ ...prev, searchText: e.target.value }))}
                />
              </Grid>
            </Grid>
            
            <Box sx={{ mt: 2 }}>
              <Button
                variant="contained"
                onClick={handleApplyFilters}
                disabled={filterMutation.isPending}
                startIcon={filterMutation.isPending ? <CircularProgress size={20} /> : <FilterList />}
              >
                Apply Filters
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Price Update Section */}
      {selectedRows.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <PriceChange sx={{ mr: 1, verticalAlign: 'middle' }} />
              Update Prices ({selectedRows.length} items selected)
            </Typography>
            
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={4}>
                <TextField
                  select
                  fullWidth
                  label="Update Method"
                  value={updateMethod}
                  onChange={(e) => setUpdateMethod(e.target.value as any)}
                  SelectProps={{ native: true }}
                >
                  <option value="percentage">Percentage Change</option>
                  <option value="fixed">Fixed Price</option>
                  <option value="market_price">Set to Market Price</option>
                </TextField>
              </Grid>
              
              {updateMethod === 'percentage' && (
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="Percentage Change"
                    type="number"
                    value={percentageChange}
                    onChange={(e) => setPercentageChange(Number(e.target.value))}
                    InputProps={{ endAdornment: '%' }}
                  />
                </Grid>
              )}
              
              {updateMethod === 'fixed' && (
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="Fixed Price"
                    type="number"
                    value={fixedPrice}
                    onChange={(e) => setFixedPrice(Number(e.target.value))}
                    InputProps={{ startAdornment: '$' }}
                  />
                </Grid>
              )}
              
              <Grid item xs={12} sm={4}>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleUpdatePrices}
                  disabled={updatePricesMutation.isPending}
                  startIcon={updatePricesMutation.isPending ? <CircularProgress size={20} /> : <PriceChange />}
                >
                  Update Prices
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Data Grid */}
      {filteredData.length > 0 && (
        <Paper sx={{ height: 600, width: '100%' }}>
          <DataGrid
            rows={filteredData}
            columns={columns}
            checkboxSelection
            disableRowSelectionOnClick
            onRowSelectionModelChange={setSelectedRows}
            rowSelectionModel={selectedRows}
            pageSizeOptions={[25, 50, 100]}
            initialState={{
              pagination: {
                paginationModel: { pageSize: 25 },
              },
            }}
          />
        </Paper>
      )}

      {/* Success/Error Messages */}
      {updatePricesMutation.isSuccess && (
        <Alert severity="success" sx={{ mt: 2 }}>
          Prices updated successfully!
        </Alert>
      )}
      
      {updatePricesMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          Failed to update prices. Please try again.
        </Alert>
      )}
    </Box>
  )
}

export default Repricer
