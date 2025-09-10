import React, { useState } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  CircularProgress,
  Chip,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material'
import { Search, TrendingUp, AttachMoney } from '@mui/icons-material'
import { useQuery } from '@tanstack/react-query'
import { pokemonService } from '../services/api'

interface PokemonCard {
  name: string
  set_name: string
  price: number
  foil_price?: number
  rarity: string
  last_updated: string
  price_change_24h?: number
  price_change_7d?: number
}

const PokemonTracker: React.FC = () => {
  const [selectedSet, setSelectedSet] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState<string>('')

  const { data: priceData, isLoading, error, refetch } = useQuery({
    queryKey: ['pokemon-prices', selectedSet],
    queryFn: () => pokemonService.getPrices(selectedSet || undefined),
    enabled: true,
  })

  const filteredCards = React.useMemo(() => {
    if (!priceData?.prices) return []
    
    return priceData.prices.filter((card: PokemonCard) =>
      card.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      card.set_name.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }, [priceData?.prices, searchTerm])

  const uniqueSets = React.useMemo(() => {
    if (!priceData?.prices) return []
    
    const sets = Array.from(new Set(priceData.prices.map((card: PokemonCard) => card.set_name)))
    return sets.sort()
  }, [priceData?.prices])

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  const getPriceChangeColor = (change?: number) => {
    if (!change) return 'default'
    return change > 0 ? 'success' : change < 0 ? 'error' : 'default'
  }

  const getPriceChangeText = (change?: number) => {
    if (!change) return 'No data'
    const prefix = change > 0 ? '+' : ''
    return `${prefix}${change.toFixed(2)}%`
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        ⚡ Pokemon Price Tracker
      </Typography>

      {/* Controls */}
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
            <Grid item xs={12} sm={4}>
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
            <Grid item xs={12} sm={4}>
              <Button
                variant="contained"
                onClick={() => refetch()}
                disabled={isLoading}
                startIcon={isLoading ? <CircularProgress size={20} /> : <TrendingUp />}
                fullWidth
              >
                Refresh Prices
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Summary Stats */}
      {priceData?.prices && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              📊 Market Summary
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={3}>
                <Chip
                  icon={<AttachMoney />}
                  label={`${filteredCards.length} Cards Tracked`}
                  color="primary"
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <Chip
                  label={`${uniqueSets.length} Sets Available`}
                  color="secondary"
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <Chip
                  label={`Avg Price: ${formatCurrency(
                    filteredCards.reduce((sum, card) => sum + card.price, 0) / filteredCards.length || 0
                  )}`}
                  color="success"
                  variant="outlined"
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <Chip
                  label={`Last Updated: ${priceData.last_updated ? formatDate(priceData.last_updated) : 'Unknown'}`}
                  color="info"
                  variant="outlined"
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load Pokemon prices. Please try again later.
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <CircularProgress sx={{ mb: 2 }} />
            <Typography>Loading Pokemon prices...</Typography>
          </CardContent>
        </Card>
      )}

      {/* Price Table */}
      {!isLoading && filteredCards.length > 0 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Card Name</strong></TableCell>
                <TableCell><strong>Set</strong></TableCell>
                <TableCell><strong>Rarity</strong></TableCell>
                <TableCell align="right"><strong>Normal Price</strong></TableCell>
                <TableCell align="right"><strong>Foil Price</strong></TableCell>
                <TableCell align="center"><strong>24h Change</strong></TableCell>
                <TableCell align="center"><strong>7d Change</strong></TableCell>
                <TableCell align="center"><strong>Last Updated</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredCards.map((card, index) => (
                <TableRow key={index} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {card.name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip size="small" label={card.set_name} variant="outlined" />
                  </TableCell>
                  <TableCell>
                    <Chip 
                      size="small" 
                      label={card.rarity} 
                      color={
                        card.rarity.toLowerCase().includes('rare') ? 'warning' :
                        card.rarity.toLowerCase().includes('common') ? 'default' :
                        'secondary'
                      }
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2" fontWeight="medium">
                      {formatCurrency(card.price)}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2" fontWeight="medium">
                      {card.foil_price ? formatCurrency(card.foil_price) : 'N/A'}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      size="small"
                      label={getPriceChangeText(card.price_change_24h)}
                      color={getPriceChangeColor(card.price_change_24h)}
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      size="small"
                      label={getPriceChangeText(card.price_change_7d)}
                      color={getPriceChangeColor(card.price_change_7d)}
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Typography variant="caption" color="text.secondary">
                      {formatDate(card.last_updated)}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* No Results */}
      {!isLoading && filteredCards.length === 0 && priceData?.prices && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No cards found
            </Typography>
            <Typography color="text.secondary">
              Try adjusting your search terms or set filter.
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  )
}

export default PokemonTracker
