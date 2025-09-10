import React, { useState } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Grid,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
} from '@mui/material'
import { Casino, Calculate } from '@mui/icons-material'
import { useMutation } from '@tanstack/react-query'
import { evToolsService } from '../services/api'

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
      id={`ev-tabpanel-${index}`}
      aria-labelledby={`ev-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  )
}

const EVTools: React.FC = () => {
  const [tabValue, setTabValue] = useState(0)
  const [setCode, setSetCode] = useState('dft')
  const [boxesToOpen, setBoxesToOpen] = useState(1)
  const [preconName, setPreconName] = useState('')
  const [preconSet, setPreconSet] = useState('')

  const boxSimMutation = useMutation({
    mutationFn: ({ setCode, boxes }: { setCode: string; boxes: number }) =>
      evToolsService.simulateBoosterBox(setCode, boxes),
  })

  const preconMutation = useMutation({
    mutationFn: ({ name, set }: { name: string; set: string }) =>
      evToolsService.calculatePreconEV(name, set),
  })

  const handleBoxSimulation = () => {
    boxSimMutation.mutate({ setCode, boxes: boxesToOpen })
  }

  const handlePreconCalculation = () => {
    preconMutation.mutate({ name: preconName, set: preconSet })
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        🎰 EV Tools
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="Booster Box EV" />
          <Tab label="Precon EV" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Booster Box EV Calculator
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
              Simulate expected value from booster box pulls.
            </Typography>

            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Set Code"
                  value={setCode}
                  onChange={(e) => setSetCode(e.target.value)}
                  placeholder="e.g., dft"
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Boxes to Open"
                  type="number"
                  value={boxesToOpen}
                  onChange={(e) => setBoxesToOpen(Number(e.target.value))}
                  inputProps={{ min: 1, max: 100 }}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <Button
                  variant="contained"
                  onClick={handleBoxSimulation}
                  disabled={boxSimMutation.isPending}
                  startIcon={boxSimMutation.isPending ? <CircularProgress size={20} /> : <Casino />}
                  fullWidth
                >
                  Simulate!
                </Button>
              </Grid>
            </Grid>

            {boxSimMutation.isSuccess && (
              <Alert severity="success" sx={{ mt: 2 }}>
                <Typography variant="h6">
                  Total EV: ${boxSimMutation.data.total_ev}
                </Typography>
                <Typography>
                  Average per box: ${boxSimMutation.data.average_ev_per_box}
                </Typography>
                <Typography>
                  Boxes opened: {boxSimMutation.data.boxes_opened}
                </Typography>
              </Alert>
            )}

            {boxSimMutation.isError && (
              <Alert severity="error" sx={{ mt: 2 }}>
                Failed to simulate booster box. Please check the set code.
              </Alert>
            )}
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Preconstructed Deck EV Calculator
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
              Calculate the expected value of preconstructed decks.
            </Typography>

            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Precon Name"
                  value={preconName}
                  onChange={(e) => setPreconName(e.target.value)}
                  placeholder="e.g., Eternal Might"
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Set Code"
                  value={preconSet}
                  onChange={(e) => setPreconSet(e.target.value)}
                  placeholder="e.g., DFT"
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <Button
                  variant="contained"
                  onClick={handlePreconCalculation}
                  disabled={preconMutation.isPending}
                  startIcon={preconMutation.isPending ? <CircularProgress size={20} /> : <Calculate />}
                  fullWidth
                >
                  Calculate EV
                </Button>
              </Grid>
            </Grid>

            {preconMutation.isSuccess && (
              <Alert severity="success" sx={{ mt: 2 }}>
                <Typography variant="h6">
                  Total EV: ${preconMutation.data.total_ev}
                </Typography>
                <Typography>
                  Precon: {preconMutation.data.precon_name}
                </Typography>
                <Typography>
                  Cards analyzed: {preconMutation.data.summary?.unique_cards || 0}
                </Typography>
              </Alert>
            )}

            {preconMutation.isError && (
              <Alert severity="error" sx={{ mt: 2 }}>
                Failed to calculate precon EV. Please check the precon name and set code.
              </Alert>
            )}
          </CardContent>
        </Card>
      </TabPanel>
    </Box>
  )
}

export default EVTools
