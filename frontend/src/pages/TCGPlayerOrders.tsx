import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Alert,
  CircularProgress,
  Grid,
  Chip,
  Paper,
  IconButton,
  Tooltip,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Fab,
  Stepper,
  Step,
  StepLabel,
  Container,
  Badge,
  useTheme,
  alpha,
  Checkbox,
  FormControlLabel,
  Slider,
  Collapse,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material'
import {
  CloudUpload,
  Print,
  LocalShipping,
  Receipt,
  ContentCopy,
  Settings,
  Save,
  FileUpload,
  CheckCircle,
  Error,
  Info,
  Search,
  Close,
  Refresh,
  FilterList,
  ExpandMore,
  ExpandLess,
  CheckCircleOutline,
  Visibility,
  VisibilityOff
} from '@mui/icons-material'
import { tcgplayerService } from '../services/api'

interface OrderItem {
  quantity: number
  description: string
  price: number
  total_price: number
}

interface Order {
  order_number: string
  order_date: string
  shipping_method: string
  buyer_name: string
  seller_name: string
  shipping_address: {
    raw: string
    parsed: any
  }
  items: OrderItem[]
}

interface ShippingLabel {
  order_number: string
  order_date: string
  shipping_method: string
  recipient: {
    name: string
    address_line_1: string
    address_line_2: string
    city: string
    state: string
    zip_code: string
    country: string
  }
  sender: {
    name: string
    business_name: string
  }
  package: {
    total_items: number
    total_value: number
    estimated_weight_oz: number
    contents: string
  }
  tracking_required: boolean
  insurance_required: boolean
}

const TCGPlayerOrders: React.FC = () => {
  const theme = useTheme()
  
  // Main state
  const [loading, setLoading] = useState(false)
  const [orders, setOrders] = useState<Order[]>([])
  const [shippingLabels, setShippingLabels] = useState<ShippingLabel[]>([])
  const [extractionSummary, setExtractionSummary] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  
  // UI state
  const [activeStep, setActiveStep] = useState(0)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedLabels, setSelectedLabels] = useState<string[]>([])
  const [selectAll, setSelectAll] = useState(false)
  const [printing, setPrinting] = useState(false)
  const [printProgress, setPrintProgress] = useState(0)
  const [priceFilter, setPriceFilter] = useState({ min: 0, max: 1000 })
  const [showFilters, setShowFilters] = useState(false)
  const [completedOrders, setCompletedOrders] = useState<string[]>([])
  const [showCompleted, setShowCompleted] = useState(true)
  const [filterPreset, setFilterPreset] = useState<string>('all')
  const [stampThresholds, setStampThresholds] = useState(() => {
    const saved = localStorage.getItem('stampThresholds')
    return saved ? JSON.parse(saved) : { recommended: 20, required: 50 }
  })
  const [thresholdDialogOpen, setThresholdDialogOpen] = useState(false)
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false)
  
  // Settings state
  const [returnAddress, setReturnAddress] = useState({
    businessName: localStorage.getItem('returnAddress.businessName') || 'Your Business Name',
    name: localStorage.getItem('returnAddress.name') || 'Your Name',
    street: localStorage.getItem('returnAddress.street') || '123 Your Street',
    city: localStorage.getItem('returnAddress.city') || 'Your City',
    state: localStorage.getItem('returnAddress.state') || 'ST',
    zipCode: localStorage.getItem('returnAddress.zipCode') || '12345'
  })

  const steps = [
    { label: 'Upload PDF', description: 'Select and upload your TCGPlayer order PDF' },
    { label: 'Review Orders', description: 'Verify extracted order information' },
    { label: 'Generate Labels', description: 'Create and print shipping labels' }
  ]

  // Save stamp thresholds to localStorage
  useEffect(() => {
    localStorage.setItem('stampThresholds', JSON.stringify(stampThresholds))
  }, [stampThresholds])

  // Handle filter preset changes
  const handlePresetChange = (preset: string) => {
    setFilterPreset(preset)
    switch (preset) {
      case 'stamp-eligible':
        setPriceFilter({ min: 0, max: stampThresholds.recommended - 0.01 })
        break
      case 'tracking-required':
        setPriceFilter({ min: stampThresholds.required, max: 1000 })
        break
      case 'mid-range':
        setPriceFilter({ min: stampThresholds.recommended, max: stampThresholds.required - 0.01 })
        break
      case 'all':
      default:
        setPriceFilter({ min: 0, max: 1000 })
        break
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (file.type !== 'application/pdf') {
      setError('Please select a PDF file')
      return
    }

    setLoading(true)
    setError(null)
    setOrders([])
    setShippingLabels([])
    setExtractionSummary(null)
    setActiveStep(0)

    try {
      const result = await tcgplayerService.extractOrders(file)
      
      if (result.success) {
        setOrders(result.orders)
        setShippingLabels(result.shipping_labels)
        setExtractionSummary(result.extraction_summary)
        setActiveStep(1) // Move to review step
      } else {
        setError('Failed to process PDF file')
      }
    } catch (err) {
      setError('Error processing file. Please try again.')
      console.error('Upload error:', err)
    } finally {
      setLoading(false)
    }
  }

  const saveReturnAddress = () => {
    Object.entries(returnAddress).forEach(([key, value]) => {
      localStorage.setItem(`returnAddress.${key}`, value)
    })
    setSettingsOpen(false)
  }

  const clearData = () => {
    setOrders([])
    setShippingLabels([])
    setExtractionSummary(null)
    setError(null)
    setActiveStep(0)
    setSelectedLabels([])
    setSelectAll(false)
    setSearchQuery('')
    setCompletedOrders([])
    setPriceFilter({ min: 0, max: 1000 })
  }

  const handleCompleteOrders = () => {
    if (selectedLabels.length === 0) {
      alert('Please select orders to mark as completed')
      return
    }
    
    const confirmMessage = `Mark ${selectedLabels.length} order${selectedLabels.length !== 1 ? 's' : ''} as completed?\n\nThis indicates you've printed the shipping label(s) externally.`
    
    if (confirm(confirmMessage)) {
      setCompletedOrders(prev => [...new Set([...prev, ...selectedLabels])])
      setSelectedLabels([]) // Clear selection after completing
      console.log(`Marked ${selectedLabels.length} orders as completed`)
    }
  }

  const handleUncompleteOrder = (orderNumber: string) => {
    setCompletedOrders(prev => prev.filter(id => id !== orderNumber))
  }

  const handleLabelSelection = (orderNumber: string) => {
    setSelectedLabels(prev => 
      prev.includes(orderNumber) 
        ? prev.filter(id => id !== orderNumber)
        : [...prev, orderNumber]
    )
  }

  const getFilteredLabels = () => {
    return shippingLabels.filter(label => {
      // Text search filter
      const matchesSearch = searchQuery === '' || 
        label.order_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
        label.recipient.name.toLowerCase().includes(searchQuery.toLowerCase())
      
      // Price filter
      const orderTotal = label.package.total_value
      const matchesPrice = orderTotal >= priceFilter.min && orderTotal <= priceFilter.max
      
      // Completed filter
      const isCompleted = completedOrders.includes(label.order_number)
      const matchesCompletedFilter = showCompleted || !isCompleted
      
      return matchesSearch && matchesPrice && matchesCompletedFilter
    })
  }

  const handleSelectAll = () => {
    const filteredLabels = getFilteredLabels()
    const filteredOrderNumbers = filteredLabels.map(label => label.order_number)
    
    if (selectAll || filteredOrderNumbers.every(orderNum => selectedLabels.includes(orderNum))) {
      // Deselect all filtered labels
      setSelectedLabels(prev => prev.filter(orderNum => !filteredOrderNumbers.includes(orderNum)))
      setSelectAll(false)
    } else {
      // Select all filtered labels
      setSelectedLabels(prev => [...new Set([...prev, ...filteredOrderNumbers])])
      setSelectAll(true)
    }
  }

  const handleBulkPrint = () => {
    const labelsToPrint = selectedLabels.length > 0 
      ? shippingLabels.filter(label => selectedLabels.includes(label.order_number))
      : shippingLabels
    
    if (labelsToPrint.length === 0) {
      alert('Please select labels to print')
      return
    }
    
    setPrinting(true)
    console.log(`Generating PDF with ${labelsToPrint.length} labels:`, labelsToPrint.map(l => l.order_number))
    
    // Generate and download PDF instead of opening print window
    generatePDF(labelsToPrint)
  }

  const generatePDF = (labelsToPrint: ShippingLabel[]) => {
    // Create a print window for PDF generation (mimicking Streamlit's approach)
    const printWindow = window.open('', '_blank')
    if (!printWindow) {
      alert('Please allow popups for this site to generate PDF')
      setPrinting(false)
      return
    }

    // Generate HTML for all labels - each label gets its own 4x6 page
    const allLabelsHtml = labelsToPrint.map((label, index) => `
      <div class="label-page" style="page-break-after: ${index < labelsToPrint.length - 1 ? 'always' : 'auto'};">
        <div class="shipping-label">
          <div class="label-number">Label ${index + 1} of ${labelsToPrint.length}</div>
          
          <!-- Return Address (Top Left) -->
          <div class="return-address">
            <strong>${returnAddress.businessName}</strong><br>
            ${returnAddress.name}<br>
            ${returnAddress.street}<br>
            ${returnAddress.city}, ${returnAddress.state} ${returnAddress.zipCode}<br>
            USA
          </div>
          
          <!-- Stamp Area (Top Right) -->
          <div class="stamp-area">
            <div class="stamp-text">STAMP</div>
            <div class="stamp-text">HERE</div>
          </div>
          
          <!-- Shipping Address (Center) -->
          <div class="shipping-address">
            ${label.recipient.name}<br>
            ${label.recipient.address_line_1}<br>
            ${label.recipient.address_line_2 ? label.recipient.address_line_2 + '<br>' : ''}
            ${label.recipient.city}, ${label.recipient.state} ${label.recipient.zip_code}<br>
            ${label.recipient.country}
          </div>
          
          <!-- Order Info (Bottom Left) -->
          <div class="order-info">
            Order: ${label.order_number}<br>
            Date: ${new Date(label.order_date).toLocaleDateString()}<br>
            Method: ${label.shipping_method}<br>
            Items: ${label.package.total_items} | Weight: ${label.package.estimated_weight_oz} oz | Value: $${label.package.total_value.toFixed(2)}
          </div>
          
          <!-- Tracking Info (Bottom Right) -->
          <div class="tracking-info">
            ${label.tracking_required ? '<span class="tracking-required">TRACKING REQUIRED</span>' : ''}
            ${label.insurance_required ? '<span class="insurance-required">INSURANCE REQUIRED</span>' : ''}
          </div>
        </div>
      </div>
    `).join('')

    const printContent = `
      <html>
        <head>
          <title>Shipping Labels - ${labelsToPrint.length} Labels</title>
          <style>
            @media print {
              @page { 
                margin: 0; 
                size: 6in 4in landscape; 
              }
              body { 
                margin: 0; 
                padding: 0;
              }
              .label-page {
                page-break-inside: avoid;
                page-break-after: always;
              }
              .label-page:last-child {
                page-break-after: auto;
              }
            }
            
            body { 
              font-family: Arial, sans-serif; 
              margin: 0; 
              padding: 0;
              background: white;
            }
            
            .label-page {
              width: 6in;
              height: 4in;
              margin: 0;
              padding: 0;
              background: white;
            }
            
            .shipping-label {
              width: 6in;
              height: 4in;
              border: 2px solid #000;
              position: relative;
              background: white;
              box-sizing: border-box;
            }
            
            .label-number {
              position: absolute;
              top: 0.05in;
              left: 0.1in;
              font-size: 8px;
              color: #666;
            }
            
            .return-address {
              position: absolute;
              top: 0.2in;
              left: 0.15in;
              font-size: 11px;
              line-height: 1.2;
              max-width: 2.2in;
            }
            
            .stamp-area {
              position: absolute;
              top: 0.2in;
              right: 0.15in;
              width: 1.2in;
              height: 0.8in;
              border: 2px dashed #666;
              text-align: center;
              font-size: 10px;
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              color: #666;
            }
            
            .stamp-text {
              line-height: 1;
              margin: 1px 0;
            }
            
            .shipping-address {
              position: absolute;
              top: 1.8in;
              left: 2.2in;
              right: 0.15in;
              font-size: 18px;
              line-height: 1.3;
              font-weight: bold;
              text-align: left;
            }
            
            .order-info {
              position: absolute;
              bottom: 0.15in;
              left: 0.15in;
              font-size: 9px;
              color: #666;
              line-height: 1.1;
            }
            
            .tracking-info {
              position: absolute;
              bottom: 0.15in;
              right: 0.15in;
              font-size: 9px;
              text-align: right;
            }
            
            .tracking-required {
              background: #ffeb3b;
              padding: 1px 3px;
              border-radius: 2px;
              font-weight: bold;
              font-size: 7px;
            }
            
            .insurance-required {
              background: #f44336;
              color: white;
              padding: 1px 3px;
              border-radius: 2px;
              font-weight: bold;
              margin-left: 3px;
              font-size: 7px;
            }
            
            @media screen {
              .label-page {
                margin: 0.25in auto;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
              }
              .shipping-label {
                transform-origin: center;
                transform: scale(0.8);
              }
            }
          </style>
        </head>
        <body>
          ${allLabelsHtml}
          
          <script>
            // Auto-open print dialog for PDF generation
            window.onload = function() {
              setTimeout(function() {
                window.print();
              }, 500);
            }
            
            // Handle after print (PDF save)
            window.addEventListener('afterprint', function() {
              setTimeout(function() {
                window.close();
              }, 1000);
            });
          </script>
        </body>
      </html>
    `

    printWindow.document.write(printContent)
    printWindow.document.close()
    
    // Reset printing state
    setTimeout(() => {
      setPrinting(false)
    }, 1000)
  }



  const handlePrintLabel = (label: ShippingLabel) => {
    const printWindow = window.open('', '_blank')
    if (!printWindow) return

    const printContent = `
      <html>
        <head>
          <title>Shipping Label - ${label.order_number}</title>
          <style>
            @media print {
              @page { margin: 0.5in; size: 8.5in 11in; }
            }
            body { 
              font-family: Arial, sans-serif; 
              margin: 0; 
              padding: 20px;
              background: white;
            }
            .envelope {
              width: 8in;
              height: 5in;
              border: 2px solid #000;
              position: relative;
              background: white;
              margin: 0 auto;
            }
            .return-address {
              position: absolute;
              top: 0.5in;
              left: 0.5in;
              font-size: 12px;
              line-height: 1.3;
              max-width: 2.5in;
            }
            .stamp-area {
              position: absolute;
              top: 0.5in;
              right: 0.5in;
              width: 1.2in;
              height: 0.8in;
              border: 2px dashed #666;
              text-align: center;
              font-size: 10px;
              display: flex;
              align-items: center;
              justify-content: center;
              color: #666;
            }
            .shipping-address {
              position: absolute;
              top: 2in;
              left: 3in;
              font-size: 14px;
              line-height: 1.4;
              font-weight: bold;
              max-width: 3in;
            }
            .order-info {
              position: absolute;
              bottom: 0.3in;
              left: 0.5in;
              font-size: 10px;
              color: #666;
            }
            .tracking-info {
              position: absolute;
              bottom: 0.3in;
              right: 0.5in;
              font-size: 10px;
              text-align: right;
            }
            .tracking-required {
              background: #ffeb3b;
              padding: 2px 4px;
              border-radius: 3px;
              font-weight: bold;
            }
            .insurance-required {
              background: #f44336;
              color: white;
              padding: 2px 4px;
              border-radius: 3px;
              font-weight: bold;
              margin-left: 5px;
            }
          </style>
        </head>
        <body>
          <div class="envelope">
            <!-- Return Address (Top Left) -->
            <div class="return-address">
              <strong>${returnAddress.businessName}</strong><br>
              ${returnAddress.name}<br>
              ${returnAddress.street}<br>
              ${returnAddress.city}, ${returnAddress.state} ${returnAddress.zipCode}<br>
              USA
            </div>
            
            <!-- Stamp Area (Top Right) -->
            <div class="stamp-area">
              STAMP<br>HERE
            </div>
            
            <!-- Shipping Address (Center) -->
            <div class="shipping-address">
              ${label.recipient.name}<br>
              ${label.recipient.address_line_1}<br>
              ${label.recipient.address_line_2 ? label.recipient.address_line_2 + '<br>' : ''}
              ${label.recipient.city}, ${label.recipient.state} ${label.recipient.zip_code}<br>
              ${label.recipient.country}
            </div>
            
            <!-- Order Info (Bottom Left) -->
            <div class="order-info">
              Order: ${label.order_number}<br>
              Date: ${new Date(label.order_date).toLocaleDateString()}<br>
              Method: ${label.shipping_method}<br>
              Items: ${label.package.total_items} | Weight: ${label.package.estimated_weight_oz} oz | Value: $${label.package.total_value.toFixed(2)}
            </div>
            
            <!-- Tracking Info (Bottom Right) -->
            <div class="tracking-info">
              ${label.tracking_required ? '<span class="tracking-required">TRACKING REQUIRED</span>' : ''}
              ${label.insurance_required ? '<span class="insurance-required">INSURANCE REQUIRED</span>' : ''}
            </div>
          </div>
        </body>
      </html>
    `

    printWindow.document.write(printContent)
    printWindow.document.close()
    printWindow.print()
  }

  const copyAddressToClipboard = (label: ShippingLabel) => {
    const address = [
      label.recipient.name,
      label.recipient.address_line_1,
      label.recipient.address_line_2,
      `${label.recipient.city}, ${label.recipient.state} ${label.recipient.zip_code}`,
      label.recipient.country
    ].filter(Boolean).join('\n')

    navigator.clipboard.writeText(address)
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box>
            <Typography variant="h3" component="h1" sx={{ fontWeight: 700, mb: 1 }}>
              📦 Order Processing (Hot Reload ✅)
            </Typography>
            <Typography variant="h6" color="text.secondary">
              Upload, process, and print TCGPlayer orders with ease
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Tooltip title="Settings">
              <IconButton onClick={() => setSettingsOpen(true)}>
                <Settings />
              </IconButton>
            </Tooltip>
            {shippingLabels.length > 0 && (
              <>
                <Tooltip title="Clear all data and start over">
                  <Button
                    variant="outlined"
                    startIcon={<Refresh />}
                    onClick={clearData}
                    size="large"
                  >
                    New PDF
                  </Button>
                </Tooltip>
                <Badge badgeContent={selectedLabels.length || shippingLabels.length} color="primary">
                  <Button
                    variant="contained"
                    startIcon={<Print />}
                    onClick={handleBulkPrint}
                    size="large"
                    disabled={selectedLabels.length === 0}
                  >
                    Generate PDF ({selectedLabels.length} Label{selectedLabels.length !== 1 ? 's' : ''})
                  </Button>
                </Badge>
              </>
            )}
          </Box>
        </Box>

        {/* Progress Stepper */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Stepper activeStep={activeStep} orientation="horizontal">
            {steps.map((step) => (
              <Step key={step.label}>
                <StepLabel>{step.label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </Paper>
      </Box>

      {/* Upload Section - Only show if no data processed */}
      {shippingLabels.length === 0 && (
        <Card 
          sx={{ 
            mb: 4, 
            background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)} 0%, ${alpha(theme.palette.secondary.main, 0.1)} 100%)`,
            border: `2px dashed ${theme.palette.primary.main}`,
            transition: 'all 0.3s ease',
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: theme.shadows[8]
            }
          }}
        >
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <FileUpload sx={{ fontSize: 64, color: theme.palette.primary.main, mb: 2 }} />
            
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
              Upload Your PDF
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 500, mx: 'auto' }}>
              Drag and drop your TCGPlayer order PDF here, or click to browse. We'll extract all order information automatically.
            </Typography>
            
            <input
              accept="application/pdf"
              style={{ display: 'none' }}
              id="pdf-upload"
              type="file"
              onChange={handleFileUpload}
              disabled={loading}
            />
            <label htmlFor="pdf-upload">
              <Button
                variant="contained"
                component="span"
                startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <CloudUpload />}
                disabled={loading}
                size="large"
                sx={{ 
                  px: 4, 
                  py: 1.5,
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  borderRadius: 2
                }}
              >
                {loading ? 'Processing PDF...' : 'Select PDF File'}
              </Button>
            </label>

            {error && (
              <Alert 
                severity="error" 
                sx={{ mt: 3, maxWidth: 600, mx: 'auto' }}
                icon={<Error />}
              >
                {error}
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Extraction Summary */}
      {extractionSummary && (
        <Card sx={{ mb: 4, bgcolor: alpha(theme.palette.success.main, 0.05) }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <CheckCircle sx={{ color: theme.palette.success.main, mr: 2 }} />
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                Processing Complete!
              </Typography>
            </Box>
            
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'background.paper' }}>
                  <Receipt sx={{ fontSize: 40, color: theme.palette.primary.main, mb: 1 }} />
                  <Typography variant="h4" sx={{ fontWeight: 700, color: theme.palette.primary.main }}>
                    {extractionSummary.orders_found}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Orders Found
                  </Typography>
                </Paper>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'background.paper' }}>
                  <Receipt sx={{ fontSize: 40, color: theme.palette.success.main, mb: 1 }} />
                  <Typography variant="h4" sx={{ fontWeight: 700, color: theme.palette.success.main }}>
                    {formatCurrency(orders.reduce((sum, order) => sum + order.items.reduce((itemSum, item) => itemSum + item.total_price, 0), 0))}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Value
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Shipping Labels */}
      {shippingLabels.length > 0 && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            {/* Header */}
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="h5" sx={{ fontWeight: 600 }}>
                  🏷️ Shipping Labels
                </Typography>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={getFilteredLabels().every(label => selectedLabels.includes(label.order_number)) && getFilteredLabels().length > 0}
                      onChange={handleSelectAll}
                      indeterminate={
                        selectedLabels.length > 0 && 
                        !getFilteredLabels().every(label => selectedLabels.includes(label.order_number)) &&
                        getFilteredLabels().some(label => selectedLabels.includes(label.order_number))
                      }
                    />
                  }
                  label="Select All"
                />
              </Box>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                <Chip 
                  label={`${getFilteredLabels().length} of ${shippingLabels.length} Showing`} 
                  color={getFilteredLabels().length !== shippingLabels.length ? "primary" : "default"}
                />
                <Chip 
                  label={`${selectedLabels.length} Selected`} 
                  color={selectedLabels.length > 0 ? "secondary" : "default"}
                />
              </Box>
            </Box>

            {/* Filters */}
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap', mb: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
              <TextField
                size="small"
                placeholder="Search orders..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />
                }}
                sx={{ minWidth: 200 }}
              />
              <FormControl size="small" sx={{ minWidth: 140 }}>
                <InputLabel>Filter Preset</InputLabel>
                <Select
                  value={filterPreset}
                  onChange={(e) => handlePresetChange(e.target.value)}
                  label="Filter Preset"
                >
                  <MenuItem value="all">All Orders</MenuItem>
                  <MenuItem value="stamp-eligible">📮 Stamp Eligible (&lt;${stampThresholds.recommended})</MenuItem>
                  <MenuItem value="mid-range">📦 Mid Range (${stampThresholds.recommended}-${stampThresholds.required})</MenuItem>
                  <MenuItem value="tracking-required">🔍 Tracking Required (${stampThresholds.required}+)</MenuItem>
                </Select>
              </FormControl>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                <TextField
                  size="small"
                  type="number"
                  label="Min $"
                  value={priceFilter.min}
                  onChange={(e) => {
                    setPriceFilter(prev => ({ ...prev, min: Number(e.target.value) || 0 }))
                    setFilterPreset('custom')
                  }}
                  sx={{ width: 80 }}
                />
                <Typography variant="body2" color="text.secondary">-</Typography>
                <TextField
                  size="small"
                  type="number"
                  label="Max $"
                  value={priceFilter.max}
                  onChange={(e) => {
                    setPriceFilter(prev => ({ ...prev, max: Number(e.target.value) || 1000 }))
                    setFilterPreset('custom')
                  }}
                  sx={{ width: 80 }}
                />
              </Box>
              <Tooltip title="Configure Stamp Thresholds">
                <IconButton 
                  size="small" 
                  onClick={() => setThresholdDialogOpen(true)}
                  sx={{ color: 'text.secondary' }}
                >
                  <Settings />
                </IconButton>
              </Tooltip>
            </Box>
            
            <Grid container spacing={3}>
              {getFilteredLabels()
                .map((label, index) => (
                <Grid item xs={12} lg={6} xl={4} key={index}>
                  <Card 
                    variant="outlined" 
                    sx={{ 
                      height: '100%',
                      transition: 'all 0.2s ease',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: theme.shadows[8]
                      }
                    }}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Checkbox
                            checked={selectedLabels.includes(label.order_number)}
                            onChange={() => handleLabelSelection(label.order_number)}
                            sx={{ mr: 2 }}
                          />
                          <Box>
                            <Typography variant="h6" sx={{ fontWeight: 600 }}>
                              #{label.order_number}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              {new Date(label.order_date).toLocaleDateString()}
                            </Typography>
                          </Box>
                        </Box>
                        <Box>
                          <Tooltip title="Copy Address">
                            <IconButton size="small" onClick={() => copyAddressToClipboard(label)}>
                              <ContentCopy />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Print This Label">
                            <IconButton 
                              size="small" 
                              onClick={() => handlePrintLabel(label)} 
                              sx={{ 
                                color: theme.palette.primary.main,
                                '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.1) }
                              }}
                            >
                              <Print />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </Box>
                      
                      <Box sx={{ bgcolor: alpha(theme.palette.grey[500], 0.1), p: 2, borderRadius: 1, mb: 2 }}>
                        <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
                          Ship To:
                        </Typography>
                        <Typography variant="body2" sx={{ lineHeight: 1.4 }}>
                          {label.recipient.name}<br />
                          {label.recipient.address_line_1}<br />
                          {label.recipient.address_line_2 && `${label.recipient.address_line_2}\n`}
                          {label.recipient.city}, {label.recipient.state} {label.recipient.zip_code}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                        <Chip 
                          size="small" 
                          label={label.shipping_method} 
                          variant="outlined" 
                        />
                        {label.tracking_required && (
                          <Chip size="small" label="Tracking" color="warning" />
                        )}
                        {label.insurance_required && (
                          <Chip size="small" label="Insurance" color="error" />
                        )}
                      </Box>
                      
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2" color="text.secondary">
                          {label.package.total_items} items • {label.package.estimated_weight_oz} oz
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600, color: theme.palette.success.main }}>
                          {formatCurrency(label.package.total_value)}
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Settings Dialog */}
      <Dialog 
        open={settingsOpen} 
        onClose={() => setSettingsOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6">Return Address Settings</Typography>
            <IconButton onClick={() => setSettingsOpen(false)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Business Name"
                  value={returnAddress.businessName}
                  onChange={(e) => setReturnAddress({...returnAddress, businessName: e.target.value})}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Your Name"
                  value={returnAddress.name}
                  onChange={(e) => setReturnAddress({...returnAddress, name: e.target.value})}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Street Address"
                  value={returnAddress.street}
                  onChange={(e) => setReturnAddress({...returnAddress, street: e.target.value})}
                />
              </Grid>
              <Grid item xs={8}>
                <TextField
                  fullWidth
                  label="City"
                  value={returnAddress.city}
                  onChange={(e) => setReturnAddress({...returnAddress, city: e.target.value})}
                />
              </Grid>
              <Grid item xs={2}>
                <TextField
                  fullWidth
                  label="State"
                  value={returnAddress.state}
                  onChange={(e) => setReturnAddress({...returnAddress, state: e.target.value})}
                  inputProps={{ maxLength: 2, style: { textTransform: 'uppercase' } }}
                />
              </Grid>
              <Grid item xs={2}>
                <TextField
                  fullWidth
                  label="ZIP"
                  value={returnAddress.zipCode}
                  onChange={(e) => setReturnAddress({...returnAddress, zipCode: e.target.value})}
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={saveReturnAddress}
            startIcon={<Save />}
          >
            Save Address
          </Button>
        </DialogActions>
      </Dialog>

      {/* Stamp Threshold Configuration Dialog */}
      <Dialog 
        open={thresholdDialogOpen} 
        onClose={() => setThresholdDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Settings />
            Stamp Threshold Configuration
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Configure the price thresholds for different shipping methods on TCGPlayer.
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  type="number"
                  label="Stamp Recommended Threshold"
                  value={stampThresholds.recommended}
                  onChange={(e) => setStampThresholds(prev => ({ 
                    ...prev, 
                    recommended: Number(e.target.value) || 20 
                  }))}
                  helperText="Orders below this amount are eligible for stamp shipping"
                  InputProps={{
                    startAdornment: <Typography sx={{ mr: 1 }}>$</Typography>
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  type="number"
                  label="Tracking Required Threshold"
                  value={stampThresholds.required}
                  onChange={(e) => setStampThresholds(prev => ({ 
                    ...prev, 
                    required: Number(e.target.value) || 50 
                  }))}
                  helperText="Orders above this amount require tracking (cannot use stamps)"
                  InputProps={{
                    startAdornment: <Typography sx={{ mr: 1 }}>$</Typography>
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>Filter Presets:</Typography>
                  <Typography variant="body2" color="text.secondary">
                    📮 <strong>Stamp Eligible:</strong> $0 - ${stampThresholds.recommended - 0.01}<br/>
                    📦 <strong>Mid Range:</strong> ${stampThresholds.recommended} - ${stampThresholds.required - 0.01}<br/>
                    🔍 <strong>Tracking Required:</strong> ${stampThresholds.required}+
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setThresholdDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={() => setThresholdDialogOpen(false)}
            startIcon={<Save />}
          >
            Save Thresholds
          </Button>
        </DialogActions>
      </Dialog>

      {/* Floating Action Button - Only show when labels are selected */}
      {selectedLabels.length > 0 && (
        <Fab
          color="primary"
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            zIndex: 1000
          }}
          onClick={handleBulkPrint}
        >
          <Badge badgeContent={selectedLabels.length} color="secondary">
            <Print />
          </Badge>
        </Fab>
      )}
    </Container>
  )
}

export default TCGPlayerOrders
