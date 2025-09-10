import React from 'react'
import { Box, Typography, Card, CardContent, Alert } from '@mui/material'

const UpdateTCGPlayerIDs: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        🔄 Update TCGPlayer IDs
      </Typography>
      <Card>
        <CardContent>
          <Alert severity="info">
            TCGPlayer ID update functionality will be implemented here.
            This is an admin-only feature for updating card database IDs.
          </Alert>
        </CardContent>
      </Card>
    </Box>
  )
}

export default UpdateTCGPlayerIDs
