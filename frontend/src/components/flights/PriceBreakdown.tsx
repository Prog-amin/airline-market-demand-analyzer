import React from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Divider,
  useTheme,
  Grid,
  Button,
} from '@mui/material';
import { FlightOffer } from '../../types/flight';
import ReceiptIcon from '@mui/icons-material/Receipt';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';

interface PriceBreakdownProps {
  flight: FlightOffer;
}

const PriceBreakdown: React.FC<PriceBreakdownProps> = ({ flight }) => {
  const theme = useTheme();
  
  // Format price with currency
  const formatPrice = (price: string | number, currency: string = 'AUD'): string => {
    const numPrice = typeof price === 'string' ? parseFloat(price) : price;
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(numPrice);
  };

  // Calculate total base fare
  const totalBaseFare = flight.travelerPricings?.reduce((sum, pricing) => {
    return sum + parseFloat(pricing.price.base || '0');
  }, 0) || 0;

  // Calculate total taxes and fees
  const totalTaxes = flight.travelerPricings?.reduce((sum, pricing) => {
    return sum + (parseFloat(pricing.price.total) - parseFloat(pricing.price.base || '0'));
  }, 0) || 0;

  // Get traveler type display name
  const getTravelerTypeName = (type: string): string => {
    const types: Record<string, string> = {
      'ADULT': 'Adult',
      'CHILD': 'Child',
      'INFANT': 'Infant',
      'SENIOR': 'Senior',
      'YOUTH': 'Youth',
      'CHD': 'Child',
      'INF': 'Infant',
      'ADT': 'Adult',
      'SNR': 'Senior',
      'YTH': 'Youth'
    };
    return types[type] || type;
  };

  // Get cabin class display name
  const getCabinClassName = (cabin: string): string => {
    const cabins: Record<string, string> = {
      'ECONOMY': 'Economy',
      'PREMIUM_ECONOMY': 'Premium Economy',
      'BUSINESS': 'Business',
      'FIRST': 'First Class',
      'ECO': 'Economy',
      'PE': 'Premium Economy',
      'BUS': 'Business',
      'F': 'First Class',
    };
    return cabins[cabin] || cabin;
  };

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={3}>
        <ReceiptIcon color="primary" sx={{ mr: 1 }} />
        <Typography variant="h6" component="h2">
          Price Breakdown
        </Typography>
      </Box>

      <TableContainer component={Paper} variant="outlined" sx={{ mb: 3 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Passenger Type</TableCell>
              <TableCell align="right">Fare</TableCell>
              <TableCell align="right">Taxes & Fees</TableCell>
              <TableCell align="right">Total</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {flight.travelerPricings?.map((pricing, idx) => {
              const baseFare = parseFloat(pricing.price.base || '0');
              const taxes = parseFloat(pricing.price.total) - baseFare;
              
              return (
                <TableRow key={idx}>
                  <TableCell>
                    {pricing.quantity}x {getTravelerTypeName(pricing.travelerType)}
                    {pricing.fareDetailsBySegment?.[0]?.cabin && (
                      <Typography variant="caption" display="block" color="text.secondary">
                        {getCabinClassName(pricing.fareDetailsBySegment[0].cabin)}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell align="right">
                    {formatPrice(pricing.price.base || '0', flight.price.currency)}
                  </TableCell>
                  <TableCell align="right">
                    {formatPrice(taxes, flight.price.currency)}
                  </TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>
                    {formatPrice(pricing.price.total, flight.price.currency)}
                  </TableCell>
                </TableRow>
              );
            })}
            
            <TableRow>
              <TableCell colSpan={2} align="right" sx={{ fontWeight: 600, borderTop: `1px solid ${theme.palette.divider}` }}>
                Subtotal:
              </TableCell>
              <TableCell align="right" sx={{ borderTop: `1px solid ${theme.palette.divider}` }}>
                {formatPrice(totalBaseFare, flight.price.currency)}
              </TableCell>
              <TableCell align="right" sx={{ borderTop: `1px solid ${theme.palette.divider}` }}>
                {formatPrice(flight.price.total, flight.price.currency)}
              </TableCell>
            </TableRow>
            
            <TableRow>
              <TableCell colSpan={3} align="right" sx={{ fontWeight: 600, borderTop: `1px solid ${theme.palette.divider}` }}>
                Taxes & Fees:
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 600, borderTop: `1px solid ${theme.palette.divider}` }}>
                {formatPrice(totalTaxes, flight.price.currency)}
              </TableCell>
            </TableRow>
            
            <TableRow>
              <TableCell colSpan={3} align="right" sx={{ fontWeight: 700, fontSize: '1.1rem', borderTop: `1px solid ${theme.palette.divider}` }}>
                Total Price:
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 700, fontSize: '1.1rem', borderTop: `1px solid ${theme.palette.divider}` }}>
                {formatPrice(flight.price.total, flight.price.currency)}
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>

      <Box mt={3}>
        <Typography variant="subtitle1" gutterBottom>
          Price Information
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          The total price includes all taxes and fees. Additional charges may apply for optional services such as seat selection, extra baggage, and in-flight meals.
        </Typography>
        
        <Box display="flex" alignItems="flex-start" mt={2} p={2} bgcolor="grey.50" borderRadius={1}>
          <InfoOutlinedIcon color="info" sx={{ mr: 1, mt: 0.5 }} />
          <Box>
            <Typography variant="body2">
              <strong>Important:</strong> Prices are per person and based on the number of travelers and cabin class selected. Fares are subject to change until ticketed.
            </Typography>
            <Typography variant="body2" mt={1}>
              <strong>Refundable:</strong> {flight.refundable ? 'Yes' : 'Non-refundable'}
            </Typography>
            {flight.lastTicketingDateTime && (
              <Typography variant="caption" display="block" color="text.secondary" mt={1}>
                Ticket must be issued by: {new Date(flight.lastTicketingDateTime).toLocaleDateString()}
              </Typography>
            )}
          </Box>
        </Box>
      </Box>

      <Box mt={4}>
        <Typography variant="subtitle1" gutterBottom>
          Payment Options
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
              <Typography variant="subtitle2" gutterBottom>Pay in Full</Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Pay the total amount now using your preferred payment method.
              </Typography>
              <Box display="flex" justifyContent="space-between" alignItems="center" mt={2}>
                <Typography variant="h6">
                  {formatPrice(flight.price.total, flight.price.currency)}
                </Typography>
                <Button variant="contained" color="primary">
                  Book Now
                </Button>
              </Box>
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
              <Typography variant="subtitle2" gutterBottom>Flexible Payment</Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Pay a deposit now and the rest later. Available on selected flights.
              </Typography>
              <Box display="flex" justifyContent="space-between" alignItems="center" mt={2}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    From {formatPrice(parseFloat(flight.price.total) * 0.2, flight.price.currency)} deposit
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Balance due 30 days before departure
                  </Typography>
                </Box>
                <Button variant="outlined" color="primary">
                  Learn More
                </Button>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Box>
      
      <Box mt={3} p={2} bgcolor="grey.50" borderRadius={1}>
        <Typography variant="body2" color="text.secondary">
          <strong>Note:</strong> The final price may vary due to currency conversion rates and additional services selected. Some flights may have additional baggage fees. Please check the airline's website for the most up-to-date information.
        </Typography>
      </Box>
    </Box>
  );
};

export default PriceBreakdown;
