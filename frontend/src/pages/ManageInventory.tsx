import React, { useState, useRef, useCallback } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  TextField,
  Grid,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Chip,
  Alert,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tabs,
  Tab,
  Paper,
  CircularProgress,
  FormControlLabel,
  Checkbox,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TableContainer,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  IconButton,
  Tooltip,
} from '@mui/material'
import {
  Inventory,
  Search,
  Edit,
  Delete,
  Refresh,
  TrendingUp,
  AttachMoney,
  CloudUpload,
  PictureAsPdf,
  Timeline,
  Assessment,
  Upload,
  FilterList,
  PriceChange,
  ExpandMore,
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { DataGrid, GridColDef, GridRowSelectionModel, GridFilterModel, GridSortModel } from '@mui/x-data-grid'
import { inventoryService, repricerService } from '../services/api'

interface InventoryItem {
  id: number
  product_name: string
  set_name: string
  rarity: string
  condition: string
  quantity: number
  price: number
  tcg_player_id?: string
  game?: string
}

interface InventorySnapshot {
  id: number
  snapshot_date: string
  total_items: number
  total_cards: number
  total_value: number
  avg_card_value: number
  file_name?: string
  file_size?: number
  upload_timestamp?: string
  metadata?: any
}

interface RepricerInventoryItem {
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

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`inventory-tabpanel-${index}`}
      aria-labelledby={`inventory-tab-${index}`}
      {...other}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  )
}

const ManageInventory: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState<string>('')
  const [selectedSet, setSelectedSet] = useState<string>('')
  const [selectedRarity, setSelectedRarity] = useState<string>('')
  const [selectedCondition, setSelectedCondition] = useState<string>('')
  const [selectedGame, setSelectedGame] = useState<string>('')
  const [dataGridFilterModel, setDataGridFilterModel] = useState<GridFilterModel>({ items: [] })
  const [dataGridSortModel, setDataGridSortModel] = useState<GridSortModel>([])
  const [selectedDataGridRows, setSelectedDataGridRows] = useState<GridRowSelectionModel>([])
  const [editDialog, setEditDialog] = useState<{
    open: boolean
    item: InventoryItem | null
  }>({
    open: false,
    item: null
  })
  const [tabValue, setTabValue] = useState<number>(0)
  const [uploadProgress, setUploadProgress] = useState<number>(0)
  const [uploadStatus, setUploadStatus] = useState<string>('')
  const [replaceAll, setReplaceAll] = useState<boolean>(false)
  const [showUploadPanel, setShowUploadPanel] = useState<boolean>(true)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // DataGrid column definitions with responsive widths
  const dataGridColumns: GridColDef[] = [
    {
      field: 'product_name',
      headerName: 'Product Name',
      flex: 2,
      minWidth: 200,
      maxWidth: 400,
      filterable: true,
      sortable: true,
      renderCell: (params) => (
        <Typography variant="body2" fontWeight="medium" noWrap>
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'game',
      headerName: 'Game',
      flex: 0.8,
      minWidth: 100,
      maxWidth: 150,
      filterable: true,
      sortable: true,
      renderCell: (params) => (
        <Chip 
          label={params.value || 'Unknown'} 
          size="small" 
          color={
            params.value === 'magic' ? 'primary' :
            params.value === 'pokemon' ? 'secondary' :
            params.value === 'yugioh' ? 'warning' :
            params.value === 'flesh_and_blood' ? 'error' :
            params.value === 'dragon_ball' ? 'info' :
            'default'
          }
        />
      ),
    },
    {
      field: 'set_name',
      headerName: 'Set',
      flex: 1,
      minWidth: 120,
      maxWidth: 200,
      filterable: true,
      sortable: true,
      renderCell: (params) => (
        <Chip 
          label={params.value} 
          size="small" 
          variant="outlined"
        />
      ),
    },
    {
      field: 'rarity',
      headerName: 'Rarity',
      flex: 0.8,
      minWidth: 100,
      maxWidth: 150,
      filterable: true,
      sortable: true,
      renderCell: (params) => (
        <Chip 
          label={params.value}
          size="small"
          color={
            params.value?.toLowerCase().includes('mythic') ? 'error' :
            params.value?.toLowerCase().includes('rare') ? 'warning' :
            params.value?.toLowerCase().includes('uncommon') ? 'info' :
            'default'
          }
        />
      ),
    },
    {
      field: 'condition',
      headerName: 'Condition',
      flex: 0.8,
      minWidth: 100,
      maxWidth: 150,
      filterable: true,
      sortable: true,
      renderCell: (params) => (
        <Chip 
          label={params.value}
          size="small"
          color={getConditionColor(params.value)}
        />
      ),
    },
    {
      field: 'quantity',
      headerName: 'Qty',
      type: 'number',
      flex: 0.6,
      minWidth: 80,
      maxWidth: 120,
      align: 'right',
      headerAlign: 'right',
      filterable: true,
      sortable: true,
    },
    {
      field: 'price',
      headerName: 'Price',
      type: 'number',
      flex: 0.8,
      minWidth: 90,
      maxWidth: 130,
      align: 'right',
      headerAlign: 'right',
      filterable: true,
      sortable: true,
      renderCell: (params) => `$${params.value.toFixed(2)}`,
    },
    {
      field: 'total_value',
      headerName: 'Total',
      type: 'number',
      flex: 1,
      minWidth: 100,
      maxWidth: 150,
      align: 'right',
      headerAlign: 'right',
      filterable: true,
      sortable: true,
      renderCell: (params) => `$${(params.row.quantity * params.row.price).toFixed(2)}`,
    },
    {
      field: 'actions',
      headerName: 'Actions',
      flex: 0.6,
      minWidth: 100,
      maxWidth: 120,
      sortable: false,
      filterable: false,
      renderCell: (params) => (
        <Box>
          <Tooltip title="Edit">
            <IconButton
              size="small"
              onClick={() => handleEditItem(params.row)}
            >
              <Edit fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete">
            <IconButton
              size="small"
              onClick={() => handleDeleteItem(params.row.id)}
              color="error"
            >
              <Delete fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      ),
    },
  ]

  // Repricer state
  const [repricerData, setRepricerData] = useState<RepricerInventoryItem[]>([])
  const [filteredRepricerData, setFilteredRepricerData] = useState<RepricerInventoryItem[]>([])
  const [selectedRepricerRows, setSelectedRepricerRows] = useState<GridRowSelectionModel>([])
  const [repricerFilters, setRepricerFilters] = useState<FilterState>({
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

  const { data: inventoryData, isLoading, error, refetch } = useQuery({
    queryKey: ['inventory'],
    queryFn: () => inventoryService.getInventory(),
    staleTime: 5 * 60 * 1000, // 5 minutes - data is fresh for 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes - keep in cache for 10 minutes
    refetchOnWindowFocus: false, // Don't refetch when window gains focus
    retry: 2, // Retry failed requests twice
  })

  const { data: snapshotsData, isLoading: snapshotsLoading, refetch: refetchSnapshots } = useQuery({
    queryKey: ['inventory-snapshots'],
    queryFn: () => inventoryService.getInventorySnapshots(),
    staleTime: 10 * 60 * 1000, // 10 minutes - snapshots change less frequently
    cacheTime: 15 * 60 * 1000, // 15 minutes
    refetchOnWindowFocus: false,
    retry: 2,
  })

  const uploadCSVMutation = useMutation({
    mutationFn: ({ file, replaceAll }: { file: File, replaceAll: boolean }) => {
      setUploadProgress(10)
      setUploadStatus('Uploading file...')
      
      // Realistic progress simulation based on file size
      const fileSizeMB = file.size / (1024 * 1024)
      let currentProgress = 10
      let progressStep = 0
      
      const progressInterval = setInterval(() => {
        // More realistic progress increments based on file size
        const increment = fileSizeMB > 1 ? Math.random() * 3 + 1 : Math.random() * 5 + 2
        currentProgress += increment
        
        // Cap at 85% until complete to show real progress
        if (currentProgress > 85) currentProgress = 85
        
        setUploadProgress(Math.round(currentProgress))
        
        // Update status messages based on progress - cycle through stages only once
        const newStep = Math.floor(currentProgress / 15)
        if (newStep !== progressStep) {
          progressStep = newStep
          switch(progressStep) {
            case 0:
              setUploadStatus('Reading CSV file...')
              break
            case 1:
              setUploadStatus('Parsing inventory data...')
              break
            case 2:
              setUploadStatus('Processing card information...')
              break
            case 3:
              setUploadStatus('Detecting game types...')
              break
            case 4:
              setUploadStatus('Saving to database...')
              break
            case 5:
              setUploadStatus('Creating inventory snapshot...')
              break
            default:
              setUploadStatus('Finalizing upload...')
              break
          }
        }
      }, fileSizeMB > 0.5 ? 1200 : 600) // More frequent updates for better UX
      
      // Store interval ID to clear it later
      ;(uploadCSVMutation as any).progressInterval = progressInterval
      
      return inventoryService.uploadInventoryCSV(file, replaceAll)
    },
    onSuccess: (data) => {
      // Clear progress interval immediately
      if ((uploadCSVMutation as any).progressInterval) {
        clearInterval((uploadCSVMutation as any).progressInterval)
        ;(uploadCSVMutation as any).progressInterval = null
      }
      
      // Complete the progress bar
      setUploadProgress(100)
      
      const message = data.success 
        ? `✅ Successfully processed ${data.processed_items || 0} items!`
        : `❌ ${data.message}`
      setUploadStatus(message)
      
      if (data.success) {
        queryClient.invalidateQueries({ queryKey: ['inventory-snapshots'] })
        queryClient.invalidateQueries({ queryKey: ['inventory'] })
        
        // Hide upload panel after successful upload
        setTimeout(() => {
          setShowUploadPanel(false)
          setUploadStatus('')
          setUploadProgress(0)
        }, 3000)
      } else {
        // Clear status after delay for failed uploads
        setTimeout(() => {
          setUploadStatus('')
          setUploadProgress(0)
        }, 8000)
      }
    },
    onError: (error: any) => {
      // Clear progress interval immediately
      if ((uploadCSVMutation as any).progressInterval) {
        clearInterval((uploadCSVMutation as any).progressInterval)
        ;(uploadCSVMutation as any).progressInterval = null
      }
      
      const errorMsg = error.response?.data?.message || error.response?.data?.detail || error.message
      setUploadStatus(`❌ Upload failed: ${errorMsg}`)
      setUploadProgress(0)
      
      setTimeout(() => {
        setUploadStatus('')
        setUploadProgress(0)
      }, 10000)
    },
  })

  // Repricer mutations
  const uploadRepricerMutation = useMutation({
    mutationFn: (file: File) => repricerService.uploadInventory(file),
    onSuccess: (data) => {
      setRepricerData(data.data_preview)
      setFilteredRepricerData(data.data_preview)
    },
  })

  const filterRepricerMutation = useMutation({
    mutationFn: (filterData: FilterState) => repricerService.filterInventory(filterData),
    onSuccess: (data) => {
      setFilteredRepricerData(data.filtered_data)
    },
  })

  const updatePricesMutation = useMutation({
    mutationFn: (updateData: any) => repricerService.updatePrices(updateData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] })
      setSelectedRepricerRows([])
    },
  })

  // Filter inventory based on selected filters
  const filteredInventory = React.useMemo(() => {
    if (!inventoryData?.inventory) return []
    
    return inventoryData.inventory.filter((item: InventoryItem) => {
      // Game filter
      if (selectedGame && item.game !== selectedGame) return false
      
      // Set filter
      if (selectedSet && item.set_name !== selectedSet) return false
      
      // Rarity filter
      if (selectedRarity && item.rarity !== selectedRarity) return false
      
      // Condition filter
      if (selectedCondition && item.condition !== selectedCondition) return false
      
      return true
    })
  }, [inventoryData?.inventory, selectedGame, selectedSet, selectedRarity, selectedCondition])

  const uniqueSets = React.useMemo(() => {
    if (!inventoryData?.inventory) return []
    return [...new Set(inventoryData.inventory.map((item: InventoryItem) => item.set_name))]
  }, [inventoryData?.inventory])

  const uniqueRarities = React.useMemo(() => {
    if (!inventoryData?.inventory) return []
    return [...new Set(inventoryData.inventory.map((item: InventoryItem) => item.rarity))]
  }, [inventoryData?.inventory])

  const totalValue = React.useMemo(() => {
    return inventoryData?.inventory?.reduce((sum: number, item: InventoryItem) => sum + (item.price * item.quantity), 0) || 0
  }, [inventoryData?.inventory])

  const handleEditItem = (item: InventoryItem) => {
    setEditDialog({ open: true, item })
  }

  const handleDeleteItem = (itemId: number) => {
    // TODO: Implement delete functionality
    console.log('Delete item:', itemId)
  }

  const handleCloseEditDialog = () => {
    setEditDialog({ open: false, item: null })
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file && (file.type === 'text/csv' || file.type === 'application/csv' || file.name.toLowerCase().endsWith('.csv'))) {
      const fileSizeKB = Math.round(file.size / 1024)
      const fileSizeMB = Math.round(file.size / (1024 * 1024))
      
      if (fileSizeMB > 0) {
        setUploadStatus(`Uploading ${fileSizeMB}MB file - this may take several minutes for large inventories...`)
      } else {
        setUploadStatus(`Uploading ${fileSizeKB}KB file...`)
      }
      
      setUploadProgress(25)
      uploadCSVMutation.mutate({ file, replaceAll })
    } else {
      setUploadStatus('Please select a CSV file')
    }
  }

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  // Repricer handlers
  const handleRepricerFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      uploadRepricerMutation.mutate(file)
    }
  }

  const handleApplyRepricerFilters = () => {
    filterRepricerMutation.mutate(repricerFilters)
  }

  const handleUpdatePrices = () => {
    const selectedItems = filteredRepricerData.filter(item => 
      selectedRepricerRows.includes(item.id)
    )

    const updateData = {
      updates: selectedItems,
      update_method: updateMethod,
      percentage_change: updateMethod === 'percentage' ? percentageChange : undefined,
      fixed_price: updateMethod === 'fixed' ? fixedPrice : undefined,
    }

    updatePricesMutation.mutate(updateData)
  }

  const chartData = React.useMemo(() => {
    if (!snapshotsData?.snapshots) return []
    
    return snapshotsData.snapshots
      .slice(-10)
      .map((snapshot: InventorySnapshot) => ({
        date: new Date(snapshot.snapshot_date).toLocaleDateString(),
        totalValue: snapshot.total_value,
        totalItems: snapshot.total_items,
        totalCards: snapshot.total_cards,
      }))
  }, [snapshotsData?.snapshots])

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount)
  }

  const getConditionColor = (condition: string) => {
    const c = condition.toLowerCase()
    if (c.includes('mint')) return 'success'
    if (c.includes('excellent') || c.includes('lightly')) return 'info'
    if (c.includes('moderately') || c.includes('played')) return 'warning'
    if (c.includes('heavily') || c.includes('damaged')) return 'error'
    return 'default'
  }

  const repricerColumns: GridColDef[] = [
    { 
      field: 'Product Name', 
      headerName: 'Product Name', 
      flex: 2,
      minWidth: 200,
      maxWidth: 400,
    },
    { 
      field: 'Set Name', 
      headerName: 'Set Name', 
      flex: 1,
      minWidth: 120,
      maxWidth: 200,
    },
    { 
      field: 'Rarity', 
      headerName: 'Rarity', 
      flex: 0.8,
      minWidth: 100,
      maxWidth: 150,
    },
    { 
      field: 'Total Quantity', 
      headerName: 'Quantity', 
      flex: 0.6,
      minWidth: 80,
      maxWidth: 120,
      type: 'number',
      align: 'right',
      headerAlign: 'right',
    },
    { 
      field: 'TCG Marketplace Price', 
      headerName: 'Current Price', 
      flex: 1,
      minWidth: 100,
      maxWidth: 150,
      type: 'number',
      align: 'right',
      headerAlign: 'right',
      valueFormatter: (params) => `$${params.value?.toFixed(2) || '0.00'}`,
    },
    { 
      field: 'TCG Market Price', 
      headerName: 'Market Price', 
      flex: 1,
      minWidth: 100,
      maxWidth: 150,
      type: 'number',
      align: 'right',
      headerAlign: 'right',
      valueFormatter: (params) => `$${params.value?.toFixed(2) || '0.00'}`,
    },
    {
      field: 'difference',
      headerName: 'Difference',
      flex: 1,
      minWidth: 100,
      maxWidth: 150,
      align: 'center',
      headerAlign: 'center',
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
        📋 Manage Inventory
      </Typography>

      {/* Tabs */}
      <Card sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="inventory tabs">
          <Tab icon={<Inventory />} label="Current Inventory" />
          <Tab icon={<Timeline />} label="Inventory Tracking" />
          <Tab icon={<PriceChange />} label="Repricer" />
        </Tabs>
      </Card>

      {/* Tab Panel 1: Current Inventory */}
      <TabPanel value={tabValue} index={0}>
        {/* Upload New Inventory Button (shown when upload panel is hidden) */}
        {!showUploadPanel && (
          <Card sx={{ mb: 3 }}>
            <CardContent sx={{ textAlign: 'center', py: 3 }}>
              <Typography variant="h6" gutterBottom>
                📋 Inventory Management
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Your inventory is up to date. Upload a new CSV file to update your inventory.
              </Typography>
              <Button
                variant="contained"
                startIcon={<CloudUpload />}
                onClick={() => setShowUploadPanel(true)}
                size="large"
              >
                Upload New Inventory
              </Button>
            </CardContent>
          </Card>
        )}

        {/* CSV Upload Section */}
        {showUploadPanel && (
          <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <CloudUpload sx={{ mr: 1, verticalAlign: 'middle' }} />
              Upload Inventory CSV
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Upload a CSV file containing your current inventory. The system will process the data and create a snapshot for tracking.
            </Typography>

            {/* Sync Mode Selection */}
            <Card sx={{ mb: 3, bgcolor: 'background.default' }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  📋 Sync Mode
                </Typography>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={replaceAll}
                      onChange={(e) => setReplaceAll(e.target.checked)}
                      color="warning"
                    />
                  }
                  label={
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        Replace entire inventory
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {replaceAll
                          ? "⚠️ This will delete all existing inventory and replace with CSV data"
                          : "✅ This will update existing items and add new ones (recommended)"}
                      </Typography>
                    </Box>
                  }
                />
              </CardContent>
            </Card>

            {/* Upload Area */}
            <Box
              sx={{
                border: '2px dashed',
                borderColor: uploadStatus.includes('failed') ? 'error.main' : 'primary.main',
                borderRadius: 2,
                p: 4,
                textAlign: 'center',
                bgcolor: 'background.default',
                cursor: 'pointer',
                '&:hover': {
                  bgcolor: 'action.hover',
                },
              }}
              onClick={() => fileInputRef.current?.click()}
            >
              <Assessment sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Click to upload CSV
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                or drag and drop your inventory CSV here
              </Typography>
              <Button variant="outlined" startIcon={<CloudUpload />}>
                Select CSV File
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                style={{ display: 'none' }}
                onChange={handleFileUpload}
              />
            </Box>

            {/* Upload Status */}
            {uploadStatus && (
              <Alert 
                severity={uploadStatus.includes('failed') ? 'error' : 'success'} 
                sx={{ mt: 2 }}
              >
                {uploadStatus}
              </Alert>
            )}

            {/* Upload Progress */}
            {uploadProgress > 0 && uploadProgress < 100 && (
              <Box sx={{ mt: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Box sx={{ width: '100%', mr: 1 }}>
                    <LinearProgress 
                      variant="determinate" 
                      value={uploadProgress}
                      sx={{ 
                        height: 8, 
                        borderRadius: 5,
                        backgroundColor: 'grey.300',
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 5,
                          backgroundColor: uploadProgress > 70 ? 'success.main' : 'primary.main'
                        }
                      }}
                    />
                  </Box>
                  <Box sx={{ minWidth: 45 }}>
                    <Typography variant="body2" color="text.secondary" fontWeight="bold">
                      {`${Math.round(uploadProgress)}%`}
                    </Typography>
                  </Box>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
                  {uploadStatus}
                </Typography>
                {uploadProgress < 85 && (
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center', mt: 0.5, fontStyle: 'italic' }}>
                    Large inventories may take several minutes to process...
                  </Typography>
                )}
              </Box>
            )}

            {/* Supported CSV Formats */}
            <Accordion sx={{ mt: 3 }}>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography variant="subtitle2">📄 Supported CSV Formats</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="body2" color="text.secondary">
                  • <strong>TCGPlayer Export:</strong> Product Name, Set Name, Quantity, Price<br />
                  • <strong>Generic Format:</strong> Card Name, Set, Quantity, Price, Condition<br />
                  • <strong>Custom Format:</strong> Any CSV with card names and quantities<br />
                  • Flexible column mapping (supports various column names)<br />
                  • Required columns: Product Name (or Card Name), Quantity<br />
                  • Optional columns: Set Name, Price, Condition, Rarity, TCGPlayer ID
                </Typography>
              </AccordionDetails>
            </Accordion>
          </CardContent>
        </Card>
        )}

        {/* Search and Filter Controls */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Search Cards"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Search />
                      </InputAdornment>
                    ),
                  }}
                  placeholder="Search by card name or set..."
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <FormControl fullWidth>
                  <InputLabel>Filter by Set</InputLabel>
                  <Select
                    value={selectedSet}
                    onChange={(e) => setSelectedSet(e.target.value)}
                    label="Filter by Set"
                  >
                    <MenuItem value="">All Sets</MenuItem>
                    {uniqueSets.map((set) => (
                      <MenuItem key={set} value={set}>
                        {set}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={3}>
                <FormControl fullWidth>
                  <InputLabel>Filter by Rarity</InputLabel>
                  <Select
                    value={selectedRarity}
                    onChange={(e) => setSelectedRarity(e.target.value)}
                    label="Filter by Rarity"
                  >
                    <MenuItem value="">All Rarities</MenuItem>
                    {uniqueRarities.map((rarity) => (
                      <MenuItem key={rarity} value={rarity}>
                        {rarity}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={2}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<Refresh />}
                  onClick={() => refetch()}
                  disabled={isLoading}
                >
                  Refresh
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Inventory sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6" color="primary">
                    Total Items
                  </Typography>
                </Box>
                <Typography variant="h4">
                  {inventoryData?.inventory?.reduce((sum: number, item: InventoryItem) => sum + item.quantity, 0) || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Assessment sx={{ mr: 1, color: 'info.main' }} />
                  <Typography variant="h6" color="info.main">
                    Unique Cards
                  </Typography>
                </Box>
                <Typography variant="h4">
                  {inventoryData?.inventory?.length || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <AttachMoney sx={{ mr: 1, color: 'success.main' }} />
                  <Typography variant="h6" color="success.main">
                    Total Value
                  </Typography>
                </Box>
                <Typography variant="h4">
                  {formatCurrency(totalValue)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <TrendingUp sx={{ mr: 1, color: 'warning.main' }} />
                  <Typography variant="h6" color="warning.main">
                    Avg Value
                  </Typography>
                </Box>
                <Typography variant="h4">
                  {formatCurrency((inventoryData?.inventory?.length || 0) > 0 ? totalValue / (inventoryData?.inventory?.length || 1) : 0)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Inventory Table */}
        {isLoading ? (
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 6 }}>
              <CircularProgress />
              <Typography variant="h6" sx={{ mt: 2 }}>
                Loading inventory...
              </Typography>
            </CardContent>
          </Card>
        ) : error ? (
          <Card>
            <CardContent>
              <Alert severity="error">
                Failed to load inventory data. Please try again.
              </Alert>
            </CardContent>
          </Card>
        ) : (inventoryData?.inventory?.length || 0) > 0 ? (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Inventory Items ({inventoryData?.inventory?.length || 0})
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Use the DataGrid above to view, filter, and manage your inventory items.
              </Typography>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 6 }}>
              <Inventory sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No inventory items found
              </Typography>
              <Typography color="text.secondary" sx={{ mb: 3 }}>
                Upload a CSV file to start managing your inventory.
              </Typography>
            </CardContent>
          </Card>
        )}

        {/* Detailed Inventory Table */}
        {(inventoryData?.inventory?.length || 0) > 0 && (
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📋 Detailed Inventory Table
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Filter and view your complete inventory with detailed information.
              </Typography>

              {/* DataGrid Info */}
              <Box sx={{ mb: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                <Typography variant="body2" color="info.contrastText">
                  💡 <strong>Pro Tip:</strong> Use the column headers to filter and sort your inventory. 
                  Click the filter icon in each column header for advanced filtering options.
                </Typography>
              </Box>

              {/* Game Filter */}
              <Box sx={{ mb: 3 }}>
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={12} sm={6} md={3}>
                    <FormControl fullWidth>
                      <InputLabel>TCG Game</InputLabel>
                      <Select
                        value={selectedGame}
                        onChange={(e) => setSelectedGame(e.target.value)}
                        label="TCG Game"
                      >
                        <MenuItem value="">All Games</MenuItem>
                        <MenuItem value="magic">Magic: The Gathering</MenuItem>
                        <MenuItem value="pokemon">Pokemon</MenuItem>
                        <MenuItem value="yugioh">Yu-Gi-Oh!</MenuItem>
                        <MenuItem value="flesh_and_blood">Flesh and Blood</MenuItem>
                        <MenuItem value="dragon_ball">Dragon Ball</MenuItem>
                        <MenuItem value="other">Other</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <FormControl fullWidth>
                      <InputLabel>Set</InputLabel>
                      <Select
                        value={selectedSet}
                        onChange={(e) => setSelectedSet(e.target.value)}
                        label="Set"
                      >
                        <MenuItem value="">All Sets</MenuItem>
                        {uniqueSets.map((set) => (
                          <MenuItem key={set} value={set}>
                            {set}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <FormControl fullWidth>
                      <InputLabel>Rarity</InputLabel>
                      <Select
                        value={selectedRarity}
                        onChange={(e) => setSelectedRarity(e.target.value)}
                        label="Rarity"
                      >
                        <MenuItem value="">All Rarities</MenuItem>
                        {uniqueRarities.map((rarity) => (
                          <MenuItem key={rarity} value={rarity}>
                            {rarity}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <FormControl fullWidth>
                      <InputLabel>Condition</InputLabel>
                      <Select
                        value={selectedCondition}
                        onChange={(e) => setSelectedCondition(e.target.value)}
                        label="Condition"
                      >
                        <MenuItem value="">All Conditions</MenuItem>
                        <MenuItem value="NM">Near Mint</MenuItem>
                        <MenuItem value="LP">Lightly Played</MenuItem>
                        <MenuItem value="MP">Moderately Played</MenuItem>
                        <MenuItem value="HP">Heavily Played</MenuItem>
                        <MenuItem value="DMG">Damaged</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                      <Button
                        variant="outlined"
                        onClick={() => {
                          setSelectedGame('')
                          setSelectedSet('')
                          setSelectedRarity('')
                          setSelectedCondition('')
                        }}
                        disabled={!selectedGame && !selectedSet && !selectedRarity && !selectedCondition}
                      >
                        Clear All Filters
                      </Button>
                    </Box>
                  </Grid>
                </Grid>
              </Box>

              {/* Inventory DataGrid */}
              <Paper sx={{ height: 600, width: '100%', overflow: 'hidden' }}>
                <DataGrid
                  rows={filteredInventory}
                  columns={dataGridColumns}
                  pageSize={25}
                  rowsPerPageOptions={[10, 25, 50, 100]}
                  checkboxSelection
                  disableSelectionOnClick
                  filterModel={dataGridFilterModel}
                  onFilterModelChange={setDataGridFilterModel}
                  sortModel={dataGridSortModel}
                  onSortModelChange={setDataGridSortModel}
                  rowSelectionModel={selectedDataGridRows}
                  onRowSelectionModelChange={setSelectedDataGridRows}
                  autoHeight={false}
                  disableColumnMenu={false}
                  disableColumnFilter={false}
                  disableColumnSelector={false}
                  sx={{
                    '& .MuiDataGrid-cell': {
                      borderRight: '1px solid #e0e0e0',
                      padding: '8px 16px',
                    },
                    '& .MuiDataGrid-columnHeaders': {
                      backgroundColor: '#f5f5f5',
                      fontWeight: 'bold',
                      borderBottom: '2px solid #e0e0e0',
                    },
                    '& .MuiDataGrid-row:hover': {
                      backgroundColor: '#f5f5f5',
                    },
                    '& .MuiDataGrid-footerContainer': {
                      borderTop: '1px solid #e0e0e0',
                    },
                    '& .MuiDataGrid-cell:focus': {
                      outline: 'none',
                    },
                    '& .MuiDataGrid-cell:focus-within': {
                      outline: 'none',
                    },
                  }}
                />
              </Paper>

              {/* DataGrid Summary */}
              <Box sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                <Grid container spacing={2}>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="body2" color="text.secondary">
                      Total Items
                    </Typography>
                    <Typography variant="h6" fontWeight="bold">
                      {filteredInventory.reduce((sum: number, item: InventoryItem) => sum + item.quantity, 0)}
                    </Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="body2" color="text.secondary">
                      Unique Cards
                    </Typography>
                    <Typography variant="h6" fontWeight="bold">
                      {filteredInventory.length}
                    </Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="body2" color="text.secondary">
                      Total Value
                    </Typography>
                    <Typography variant="h6" fontWeight="bold" color="primary">
                      {formatCurrency(filteredInventory.reduce((sum: number, item: InventoryItem) => sum + (item.price * item.quantity), 0))}
                    </Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="body2" color="text.secondary">
                      Selected Rows
                    </Typography>
                    <Typography variant="h6" fontWeight="bold">
                      {selectedDataGridRows.length}
                    </Typography>
                  </Grid>
                </Grid>
                {(selectedGame || selectedSet || selectedRarity || selectedCondition) && (
                  <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                    <Typography variant="body2" color="info.contrastText">
                      🔍 <strong>Filtered Results:</strong> Showing {filteredInventory.length} of {inventoryData?.inventory?.length || 0} cards
                      {selectedGame && ` • Game: ${selectedGame}`}
                      {selectedSet && ` • Set: ${selectedSet}`}
                      {selectedRarity && ` • Rarity: ${selectedRarity}`}
                      {selectedCondition && ` • Condition: ${selectedCondition}`}
                    </Typography>
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        )}
      </TabPanel>

      {/* Tab Panel 2: Inventory Tracking */}
      <TabPanel value={tabValue} index={1}>
        <Grid container spacing={3}>
          {/* Value Chart */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📈 Inventory Value Over Time
                </Typography>
                {chartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <RechartsTooltip formatter={(value, name) => [formatCurrency(Number(value)), name]} />
                      <Legend />
                      <Line type="monotone" dataKey="totalValue" stroke="#8884d8" name="Total Value" />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                    No data available
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Items Chart */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📦 Inventory Items Over Time
                </Typography>
                {chartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <RechartsTooltip />
                      <Bar dataKey="totalItems" fill="#ffc658" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                    No data available
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Recent Snapshots */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recent Inventory Snapshots
                </Typography>
                {snapshotsLoading ? (
                  <CircularProgress />
                ) : snapshotsData?.snapshots?.length > 0 ? (
                  <TableContainer>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Date</TableCell>
                          <TableCell align="center">Items</TableCell>
                          <TableCell align="center">Cards</TableCell>
                          <TableCell align="right">Total Value</TableCell>
                          <TableCell align="right">Avg Value</TableCell>
                          <TableCell>File</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {snapshotsData.snapshots.slice(0, 10).map((snapshot: InventorySnapshot) => (
                          <TableRow key={snapshot.id}>
                            <TableCell>
                              {new Date(snapshot.snapshot_date).toLocaleDateString()}
                            </TableCell>
                            <TableCell align="center">{snapshot.total_items}</TableCell>
                            <TableCell align="center">{snapshot.total_cards}</TableCell>
                            <TableCell align="right">
                              {formatCurrency(snapshot.total_value)}
                            </TableCell>
                            <TableCell align="right">
                              {formatCurrency(snapshot.avg_card_value)}
                            </TableCell>
                            <TableCell>
                              {snapshot.file_name ? (
                                <Chip 
                                  size="small" 
                                  icon={<PictureAsPdf />} 
                                  label={snapshot.file_name}
                                  variant="outlined"
                                />
                              ) : (
                                <Typography variant="caption" color="text.secondary">
                                  Manual entry
                                </Typography>
                              )}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                    No inventory snapshots available. Upload a CSV to start tracking.
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Tab Panel 3: Repricer */}
      <TabPanel value={tabValue} index={2}>
        {/* Use Current Inventory Section */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <PriceChange sx={{ mr: 1, verticalAlign: 'middle' }} />
              Reprice Current Inventory
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Use your uploaded inventory data to configure repricing rules and update prices.
            </Typography>
            
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <Button
                variant="contained"
                startIcon={<PriceChange />}
                onClick={() => {
                  if (inventoryData?.inventory) {
                    // Convert inventory data to repricer format
                    const repricerItems = inventoryData.inventory.map((item: InventoryItem) => ({
                      id: item.id.toString(),
                      'Product Name': item.product_name,
                      'Set Name': item.set_name,
                      'Rarity': item.rarity,
                      'Condition': item.condition,
                      'Quantity': item.quantity,
                      'Current Price': item.price,
                      'TCG Player ID': item.tcg_player_id || '',
                    }))
                    setRepricerData(repricerItems)
                    setFilteredRepricerData(repricerItems)
                  }
                }}
                disabled={!inventoryData?.inventory || inventoryData.inventory.length === 0}
              >
                Load Current Inventory ({inventoryData?.inventory?.length || 0} items)
              </Button>
              
              {repricerData.length > 0 && (
                <Button
                  variant="outlined"
                  onClick={() => {
                    setRepricerData([])
                    setFilteredRepricerData([])
                    setSelectedRepricerRows([])
                  }}
                >
                  Clear Data
                </Button>
              )}
            </Box>
            
            {repricerData.length > 0 && (
              <Alert severity="success" sx={{ mt: 2 }}>
                Loaded {repricerData.length} items from your inventory for repricing
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Filters Section */}
        {repricerData.length > 0 && (
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
                    value={repricerFilters.minPrice}
                    onChange={(e) => setRepricerFilters(prev => ({ ...prev, minPrice: Number(e.target.value) }))}
                    InputProps={{ startAdornment: '$' }}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <TextField
                    fullWidth
                    label="Max Price"
                    type="number"
                    value={repricerFilters.maxPrice}
                    onChange={(e) => setRepricerFilters(prev => ({ ...prev, maxPrice: Number(e.target.value) }))}
                    InputProps={{ startAdornment: '$' }}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <TextField
                    fullWidth
                    label="Min Quantity"
                    type="number"
                    value={repricerFilters.minListing}
                    onChange={(e) => setRepricerFilters(prev => ({ ...prev, minListing: Number(e.target.value) }))}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <TextField
                    fullWidth
                    label="Max Quantity"
                    type="number"
                    value={repricerFilters.maxListing}
                    onChange={(e) => setRepricerFilters(prev => ({ ...prev, maxListing: Number(e.target.value) }))}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Search Products"
                    value={repricerFilters.searchText}
                    onChange={(e) => setRepricerFilters(prev => ({ ...prev, searchText: e.target.value }))}
                  />
                </Grid>
              </Grid>
              
              <Box sx={{ mt: 2 }}>
                <Button
                  variant="contained"
                  onClick={handleApplyRepricerFilters}
                  disabled={filterRepricerMutation.isPending}
                  startIcon={filterRepricerMutation.isPending ? <CircularProgress size={20} /> : <FilterList />}
                >
                  Apply Filters
                </Button>
              </Box>
            </CardContent>
          </Card>
        )}

        {/* Repricing Rules Section */}
        {repricerData.length > 0 && (
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <PriceChange sx={{ mr: 1, verticalAlign: 'middle' }} />
                Repricing Rules
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Configure how prices should be updated for selected items.
              </Typography>
              
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Update Method</InputLabel>
                    <Select
                      value={updateMethod}
                      onChange={(e) => setUpdateMethod(e.target.value as 'percentage' | 'fixed' | 'market_price')}
                      label="Update Method"
                    >
                      <MenuItem value="percentage">Percentage Change</MenuItem>
                      <MenuItem value="fixed">Fixed Amount</MenuItem>
                      <MenuItem value="market_price">Market Price</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                
                {updateMethod === 'percentage' && (
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Percentage Change (%)"
                      type="number"
                      value={percentageChange}
                      onChange={(e) => setPercentageChange(Number(e.target.value))}
                      InputProps={{ endAdornment: '%' }}
                      helperText="Positive for increase, negative for decrease"
                    />
                  </Grid>
                )}
                
                {updateMethod === 'fixed' && (
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Fixed Amount ($)"
                      type="number"
                      value={fixedPrice}
                      onChange={(e) => setFixedPrice(Number(e.target.value))}
                      InputProps={{ startAdornment: '$' }}
                      helperText="Amount to add/subtract from current price"
                    />
                  </Grid>
                )}
                
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={repricerFilters.minPrice > 0}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setRepricerFilters(prev => ({ ...prev, minPrice: 0.01 }))
                          } else {
                            setRepricerFilters(prev => ({ ...prev, minPrice: 0 }))
                          }
                        }}
                      />
                    }
                    label="Only update items above minimum price"
                  />
                </Grid>
                
                {repricerFilters.minPrice > 0 && (
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Minimum Price Threshold ($)"
                      type="number"
                      value={repricerFilters.minPrice}
                      onChange={(e) => setRepricerFilters(prev => ({ ...prev, minPrice: Number(e.target.value) }))}
                      InputProps={{ startAdornment: '$' }}
                    />
                  </Grid>
                )}
              </Grid>
            </CardContent>
          </Card>
        )}

        {/* Price Update Section */}
        {selectedRepricerRows.length > 0 && (
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <PriceChange sx={{ mr: 1, verticalAlign: 'middle' }} />
                Update Prices ({selectedRepricerRows.length} items selected)
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
        {filteredRepricerData.length > 0 && (
          <Paper sx={{ height: 600, width: '100%', overflow: 'hidden' }}>
            <DataGrid
              rows={filteredRepricerData}
              columns={repricerColumns}
              checkboxSelection
              disableRowSelectionOnClick
              onRowSelectionModelChange={setSelectedRepricerRows}
              rowSelectionModel={selectedRepricerRows}
              pageSizeOptions={[25, 50, 100]}
              autoHeight={false}
              disableColumnMenu={false}
              disableColumnFilter={false}
              disableColumnSelector={false}
              initialState={{
                pagination: {
                  paginationModel: { pageSize: 25 },
                },
              }}
              sx={{
                '& .MuiDataGrid-cell': {
                  borderRight: '1px solid #e0e0e0',
                  padding: '8px 16px',
                },
                '& .MuiDataGrid-columnHeaders': {
                  backgroundColor: '#f5f5f5',
                  fontWeight: 'bold',
                  borderBottom: '2px solid #e0e0e0',
                },
                '& .MuiDataGrid-row:hover': {
                  backgroundColor: '#f5f5f5',
                },
                '& .MuiDataGrid-footerContainer': {
                  borderTop: '1px solid #e0e0e0',
                },
                '& .MuiDataGrid-cell:focus': {
                  outline: 'none',
                },
                '& .MuiDataGrid-cell:focus-within': {
                  outline: 'none',
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

        {/* Empty State */}
        {repricerData.length === 0 && !uploadRepricerMutation.isPending && (
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 6 }}>
              <PriceChange sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No pricing data uploaded
              </Typography>
              <Typography color="text.secondary" sx={{ mb: 3 }}>
                Upload a CSV file with your inventory pricing data to start repricing items.
              </Typography>
              <label htmlFor="repricer-file-upload">
                <Button variant="contained" component="span" startIcon={<Upload />}>
                  Upload CSV
                </Button>
              </label>
            </CardContent>
          </Card>
        )}
      </TabPanel>

      {/* Edit Dialog */}
      <Dialog open={editDialog.open} onClose={handleCloseEditDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Inventory Item</DialogTitle>
        <DialogContent>
          {editDialog.item && (
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Product Name"
                  value={editDialog.item.product_name}
                  onChange={(e) => setEditDialog(prev => ({
                    ...prev,
                    item: prev.item ? { ...prev.item, product_name: e.target.value } : null
                  }))}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Set Name"
                  value={editDialog.item.set_name}
                  onChange={(e) => setEditDialog(prev => ({
                    ...prev,
                    item: prev.item ? { ...prev.item, set_name: e.target.value } : null
                  }))}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Rarity"
                  value={editDialog.item.rarity}
                  onChange={(e) => setEditDialog(prev => ({
                    ...prev,
                    item: prev.item ? { ...prev.item, rarity: e.target.value } : null
                  }))}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Condition"
                  value={editDialog.item.condition}
                  onChange={(e) => setEditDialog(prev => ({
                    ...prev,
                    item: prev.item ? { ...prev.item, condition: e.target.value } : null
                  }))}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Quantity"
                  type="number"
                  value={editDialog.item.quantity}
                  onChange={(e) => setEditDialog(prev => ({
                    ...prev,
                    item: prev.item ? { ...prev.item, quantity: Number(e.target.value) } : null
                  }))}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Price"
                  type="number"
                  value={editDialog.item.price}
                  onChange={(e) => setEditDialog(prev => ({
                    ...prev,
                    item: prev.item ? { ...prev.item, price: Number(e.target.value) } : null
                  }))}
                  InputProps={{ startAdornment: '$' }}
                />
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseEditDialog}>Cancel</Button>
          <Button variant="contained">Save Changes</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default ManageInventory