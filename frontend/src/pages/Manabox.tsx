import React, { useState } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Grid,
  Divider,
} from '@mui/material'
import { CloudUpload, Download, Transform } from '@mui/icons-material'
import { useMutation } from '@tanstack/react-query'
import { manaboxService } from '../services/api'

interface ConvertedCard {
  name: string
  set_name: string
  quantity: number
  condition: string
  foil: boolean
  price?: number
}

interface ConversionStats {
  total_cards: number
  unique_cards: number
  total_value?: number
  sets_found: number
}

const Manabox: React.FC = () => {
  const [convertedData, setConvertedData] = useState<ConvertedCard[]>([])
  const [conversionStats, setConversionStats] = useState<ConversionStats | null>(null)

  const convertMutation = useMutation({
    mutationFn: (file: File) => manaboxService.convertCSV(file),
    onSuccess: (data) => {
      setConvertedData(data.converted_data)
      setConversionStats(data.conversion_stats)
    },
  })

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (!file.name.toLowerCase().endsWith('.csv')) {
      alert('Please select a CSV file')
      return
    }

    convertMutation.mutate(file)
  }

  const handleDownload = () => {
    if (convertedData.length === 0) return

    // Create CSV content
    const headers = ['Name', 'Set', 'Quantity', 'Condition', 'Foil', 'Price']
    const csvContent = [
      headers.join(','),
      ...convertedData.map(card => [
        `"${card.name}"`,
        `"${card.set_name}"`,
        card.quantity,
        `"${card.condition}"`,
        card.foil ? 'Yes' : 'No',
        card.price?.toFixed(2) || '0.00'
      ].join(','))
    ].join('\n')

    // Create and download file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `manabox_converted_${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  const uniqueSets = React.useMemo(() => {
    const sets = Array.from(new Set(convertedData.map(card => card.set_name)))
    return sets.sort()
  }, [convertedData])

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        📦 Manabox Converter
      </Typography>

      {/* Upload Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Upload Manabox CSV
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Convert your ManaBox collection export to TCGPlayer format. Upload your CSV file exported from ManaBox.
          </Typography>
          
          <input
            accept=".csv"
            style={{ display: 'none' }}
            id="csv-upload"
            type="file"
            onChange={handleFileUpload}
            disabled={convertMutation.isPending}
          />
          <label htmlFor="csv-upload">
            <Button
              variant="contained"
              component="span"
              startIcon={convertMutation.isPending ? <CircularProgress size={20} /> : <CloudUpload />}
              disabled={convertMutation.isPending}
              sx={{ mt: 2 }}
            >
              {convertMutation.isPending ? 'Converting...' : 'Upload CSV File'}
            </Button>
          </label>

          {convertMutation.isError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              Conversion failed. Please check that your file is a valid ManaBox CSV export.
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Conversion Stats */}
      {conversionStats && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              📊 Conversion Summary
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={3}>
                <Chip
                  icon={<Transform />}
                  label={`${conversionStats.total_cards} Total Cards`}
                  color="primary"
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <Chip
                  label={`${conversionStats.unique_cards} Unique Cards`}
                  color="secondary"
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <Chip
                  label={`${conversionStats.sets_found} Sets Found`}
                  color="info"
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <Chip
                  label={`Est. Value: ${conversionStats.total_value ? formatCurrency(conversionStats.total_value) : 'N/A'}`}
                  color="success"
                  variant="outlined"
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Download Section */}
      {convertedData.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              📥 Download Converted Data
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Your ManaBox data has been successfully converted to TCGPlayer format.
            </Typography>
            <Button
              variant="contained"
              color="success"
              startIcon={<Download />}
              onClick={handleDownload}
              sx={{ mt: 1 }}
            >
              Download TCGPlayer CSV
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Sets Summary */}
      {uniqueSets.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              📚 Sets in Collection
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {uniqueSets.map((set) => (
                <Chip
                  key={set}
                  label={`${set} (${convertedData.filter(card => card.set_name === set).length})`}
                  variant="outlined"
                  size="small"
                />
              ))}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Converted Data Table */}
      {convertedData.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              🔍 Converted Data Preview ({convertedData.length} cards)
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 600 }}>
              <Table stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Card Name</strong></TableCell>
                    <TableCell><strong>Set</strong></TableCell>
                    <TableCell align="center"><strong>Qty</strong></TableCell>
                    <TableCell><strong>Condition</strong></TableCell>
                    <TableCell align="center"><strong>Foil</strong></TableCell>
                    <TableCell align="right"><strong>Price</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {convertedData.map((card, index) => (
                    <TableRow key={index} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {card.name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip size="small" label={card.set_name} variant="outlined" />
                      </TableCell>
                      <TableCell align="center">
                        <Chip size="small" label={card.quantity} color="primary" />
                      </TableCell>
                      <TableCell>
                        <Chip 
                          size="small" 
                          label={card.condition} 
                          color={
                            card.condition.toLowerCase().includes('mint') ? 'success' :
                            card.condition.toLowerCase().includes('played') ? 'warning' :
                            'default'
                          }
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          size="small"
                          label={card.foil ? 'Foil' : 'Normal'}
                          color={card.foil ? 'secondary' : 'default'}
                          variant={card.foil ? 'filled' : 'outlined'}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="medium">
                          {card.price ? formatCurrency(card.price) : 'N/A'}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Instructions */}
      {convertedData.length === 0 && !convertMutation.isPending && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              📋 How to Use
            </Typography>
            <Typography variant="body2" paragraph>
              1. Export your collection from ManaBox as a CSV file
            </Typography>
            <Typography variant="body2" paragraph>
              2. Upload the CSV file using the button above
            </Typography>
            <Typography variant="body2" paragraph>
              3. Review the converted data in the preview table
            </Typography>
            <Typography variant="body2" paragraph>
              4. Download the converted file in TCGPlayer format
            </Typography>
            <Typography variant="body2" paragraph>
              5. Import the downloaded CSV into TCGPlayer or your preferred platform
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  )
}

export default Manabox
