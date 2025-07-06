import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Grid,
  Paper,
  Tabs,
  Tab,
  IconButton,
  useTheme,
  useMediaQuery,
  Chip,
} from '@mui/material';
import { FlightOffer } from '../../types/flight';
import FlightTimeline from './FlightTimeline';
import PriceBreakdown from './PriceBreakdown';
import CabinDetails from './CabinDetails';
import AirportInfo from './AirportInfo';
import { ArrowBack as BackIcon } from '@mui/icons-material';

interface FlightDetailsProps {
  flight: FlightOffer;
  onBack: () => void;
  onSelect?: (flight: FlightOffer) => void;
}

const FlightDetails: React.FC<FlightDetailsProps> = ({ flight, onBack, onSelect }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [activeTab, setActiveTab] = useState(0);
  
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };
  
  const handleBookNow = () => {
    if (onSelect) {
      onSelect(flight);
    } else {
      console.log('Proceeding to booking for flight:', flight.id);
      // navigate(`/book/${flight.id}`);
    }
  };
  
  // Calculate total duration and get departure/arrival info
  const totalDuration = flight.itineraries[0].duration;
  const departure = flight.itineraries[0].segments[0].departure;
  const arrival = flight.itineraries[0].segments[flight.itineraries[0].segments.length - 1].arrival;
  const stops = flight.itineraries[0].segments.length - 1;
  const cabinClass = flight.travelerPricings?.[0]?.fareOption || 'ECONOMY';
  
  // Format price helper function
  const formatPrice = (price: number, currency: string = 'AUD'): string => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };
  
  return (
    <Box>
      {/* Header with back button */}
      <Box display="flex" alignItems="center" mb={3}>
        <IconButton onClick={onBack} sx={{ mr: 1 }}>
          <BackIcon />
        </IconButton>
        <Typography variant="h5" component="h1">
          Flight Details
        </Typography>
      </Box>
      
      {/* Flight summary card */}
      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={8}>
              <Box display="flex" flexDirection={isMobile ? 'column' : 'row'} 
                alignItems={isMobile ? 'flex-start' : 'center'} mb={1}>
                <Box display="flex" alignItems="center" mr={3} mb={isMobile ? 1 : 0}>
                  <Box 
                    component="img"
                    src={`https://logo.clearbit.com/${flight.validatingAirlineCodes?.[0]?.toLowerCase()}.com`}
                    alt={flight.validatingAirlineCodes?.[0] || 'Airline'}
                    sx={{ 
                      width: 40, 
                      height: 40, 
                      mr: 1.5,
                      borderRadius: '50%',
                      objectFit: 'cover',
                      bgcolor: 'background.paper',
                      p: 0.5,
                      border: '1px solid',
                      borderColor: 'divider',
                    }}
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.src = `https://via.placeholder.com/40?text=${flight.validatingAirlineCodes?.[0]?.charAt(0) || 'F'}`;
                    }}
                  />
                  <Box>
                    <Typography variant="subtitle1" fontWeight={500}>
                      {flight.validatingAirlineCodes?.join(', ')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Flight {flight.itineraries[0].segments[0].carrierCode} {flight.itineraries[0].segments[0].number}
                    </Typography>
                  </Box>
                </Box>
                
                <Box display="flex" alignItems="center">
                  <Box textAlign="center" mx={isMobile ? 0 : 2}>
                    <Typography variant="h6">
                      {new Date(departure.at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {departure.iataCode}
                    </Typography>
                  </Box>
                  
                  <Box textAlign="center" mx={isMobile ? 1 : 2} sx={{ minWidth: 100 }}>
                    <Typography variant="body2" color="text.secondary">
                      {Math.floor(totalDuration / 60)}h {totalDuration % 60}m
                    </Typography>
                    <Box sx={{ position: 'relative', height: 2, bgcolor: 'divider', my: 1 }}>
                      <Box
                        sx={{
                          position: 'absolute',
                          top: '50%',
                          left: '50%',
                          transform: 'translate(-50%, -50%)',
                          bgcolor: 'background.paper',
                          px: 1,
                        }}
                      >
                        <Box component="span" sx={{ color: 'primary.main' }}>→</Box>
                      </Box>
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      {stops === 0 ? 'Non-stop' : `${stops} stop${stops > 1 ? 's' : ''}`}
                    </Typography>
                  </Box>
                  
                  <Box textAlign="center" mx={isMobile ? 0 : 2}>
                    <Typography variant="h6">
                      {new Date(arrival.at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {arrival.iataCode}
                    </Typography>
                  </Box>
                </Box>
              </Box>
              
              <Box display="flex" flexWrap="wrap" gap={1}>
                <Chip 
                  label={cabinClass.charAt(0).toUpperCase() + cabinClass.slice(1).toLowerCase()} 
                  size="small" 
                  variant="outlined" 
                  color="primary"
                />
                <Chip 
                  label={stops === 0 ? 'Non-stop' : `${stops} stop${stops > 1 ? 's' : ''}`} 
                  size="small" 
                  variant="outlined"
                />
                {flight.isMock && (
                  <Chip 
                    label="Mock Data" 
                    size="small" 
                    color="warning"
                    variant="outlined"
                  />
                )}
              </Box>
            </Grid>
            
            <Grid item xs={12} md={4} sx={{ textAlign: isMobile ? 'left' : 'right' }}>
              <Typography variant="h5" color="primary" fontWeight={600} gutterBottom>
                {formatPrice(parseFloat(flight.price.total), flight.price.currency)}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {flight.travelerPricings?.length || 1} {flight.travelerPricings?.length === 1 ? 'person' : 'people'}
              </Typography>
              <Button 
                variant="contained" 
                color="primary" 
                size="large" 
                fullWidth={isMobile}
                onClick={handleBookNow}
              >
                Book Now
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
      
      {/* Tabs for different sections */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          allowScrollButtonsMobile
          sx={{
            borderBottom: 1,
            borderColor: 'divider',
            '& .MuiTab-root': {
              minHeight: 64,
            },
          }}
        >
          <Tab label="Flight Details" />
          <Tab label="Price Breakdown" />
          <Tab label="Cabin & Bags" />
          <Tab label="Airport Info" />
        </Tabs>
        
        <Box p={3}>
          {activeTab === 0 && <FlightTimeline flight={flight} />}
          {activeTab === 1 && <PriceBreakdown flight={flight} />}
          {activeTab === 2 && <CabinDetails flight={flight} />}
          {activeTab === 3 && <AirportInfo flight={flight} />}
        </Box>
      </Paper>
    </Box>
  );
};

export default FlightDetails;
