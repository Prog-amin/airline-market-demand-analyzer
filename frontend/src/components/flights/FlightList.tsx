import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Divider,
  Chip,
  Grid,
  Paper,
  ToggleButtonGroup,
  ToggleButton,
  Tooltip,
  IconButton,
  useTheme,
  useMediaQuery,
  Collapse,
  Rating,
  Avatar,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Badge,
  Skeleton,
} from '@mui/material';
import {
  FlightTakeoff as FlightTakeoffIcon,
  FlightLand as FlightLandIcon,
  AirplanemodeActive as AirlineIcon,
  AccessTime as DurationIcon,
  AttachMoney as PriceIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  SwapHoriz as SwapHorizIcon,
  Info as InfoIcon,
  AirlineSeatReclineNormal as SeatIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { FlightOffer } from '../../types/flight';

// Mock airline logos (in a real app, these would be actual image imports)
const AIRLINE_LOGOS: Record<string, string> = {
  QF: 'https://logos-world.net/wp-content/uploads/2020/03/Qantas-Logo.png',
  VA: 'https://logos-world.net/wp-content/uploads/2020/04/Virgin-Australia-Logo.png',
  JQ: 'https://logos-world.net/wp-content/uploads/2020/04/Jetstar-Logo.png',
  NZ: 'https://logos-world.net/wp-content/uploads/2020/03/Air-New-Zealand-Logo.png',
  SQ: 'https://logos-world.net/wp-content/uploads/2020/03/Singapore-Airlines-Logo.png',
};

// Format duration in minutes to hours and minutes
const formatDuration = (minutes: number): string => {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${hours}h ${mins}m`;
};

// Format price with currency
const formatPrice = (price: number, currency: string = 'AUD'): string => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(price);
};

// Format date to a readable time
const formatTime = (dateString: string): string => {
  return new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

// Format date to a readable date
const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('en-AU', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  });
};

interface FlightListProps {
  flights: FlightOffer[];
  onSelectFlight: (flight: FlightOffer) => void;
  loading?: boolean;
}

const FlightList: React.FC<FlightListProps> = ({
  flights,
  onSelectFlight,
  loading = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [expandedFlight, setExpandedFlight] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'price' | 'duration' | 'departure' | 'arrival'>('price');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  
  // Toggle flight details expansion
  const toggleExpandFlight = (flightId: string) => {
    setExpandedFlight(expandedFlight === flightId ? null : flightId);
  };
  
  // Handle sort change
  const handleSortChange = (
    event: React.MouseEvent<HTMLElement>,
    newSortBy: 'price' | 'duration' | 'departure' | 'arrival' | null,
  ) => {
    if (newSortBy !== null) {
      if (newSortBy === sortBy) {
        // Toggle sort order if clicking the same sort option
        setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
      } else {
        // Default to ascending when changing sort field
        setSortBy(newSortBy);
        setSortOrder('asc');
      }
    }
  };
  
  // Sort flights based on selected criteria
  const sortedFlights = [...flights].sort((a, b) => {
    let compareValue = 0;
    
    switch (sortBy) {
      case 'price':
        compareValue = parseFloat(a.price.total) - parseFloat(b.price.total);
        break;
      case 'duration':
        compareValue = a.itineraries[0].duration - b.itineraries[0].duration;
        break;
      case 'departure':
        compareValue = new Date(a.itineraries[0].segments[0].departure.at).getTime() - 
                      new Date(b.itineraries[0].segments[0].departure.at).getTime();
        break;
      case 'arrival':
        const lastSegmentA = a.itineraries[0].segments[a.itineraries[0].segments.length - 1];
        const lastSegmentB = b.itineraries[0].segments[b.itineraries[0].segments.length - 1];
        compareValue = new Date(lastSegmentA.arrival.at).getTime() - 
                      new Date(lastSegmentB.arrival.at).getTime();
        break;
    }
    
    return sortOrder === 'asc' ? compareValue : -compareValue;
  });
  
  // Render flight segments
  const renderSegments = (segments: any[], isMobile: boolean) => {
    return (
      <List disablePadding>
        {segments.map((segment, idx) => (
          <React.Fragment key={idx}>
            <ListItem alignItems="flex-start" disableGutters>
              <ListItemIcon sx={{ minWidth: 40, pt: 1 }}>
                <AirlineIcon color="action" />
              </ListItemIcon>
              <ListItemText
                primary={
                  <Box display="flex" flexWrap="wrap" alignItems="center" gap={1}>
                    <Typography variant="body1" fontWeight={500}>
                      {segment.carrierCode} {segment.number}
                    </Typography>
                    <Chip 
                      label={segment.aircraft.code} 
                      size="small" 
                      variant="outlined" 
                    />
                  </Box>
                }
                secondary={
                  <Box component="span" display="flex" flexDirection={isMobile ? 'column' : 'row'} gap={isMobile ? 0 : 2}>
                    <Box>
                      <Typography variant="body2" color="text.primary">
                        {formatTime(segment.departure.at)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {segment.departure.iataCode}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', my: isMobile ? 0.5 : 0 }}>
                      <Box sx={{ 
                        flex: 1, 
                        height: '1px', 
                        bgcolor: 'divider',
                        mx: isMobile ? 0 : 2,
                        my: isMobile ? 1 : 0,
                      }} />
                      <Typography variant="caption" color="text.secondary" sx={{ whiteSpace: 'nowrap' }}>
                        {formatDuration(segment.duration)}
                      </Typography>
                      <Box sx={{ 
                        flex: 1, 
                        height: '1px', 
                        bgcolor: 'divider',
                        mx: isMobile ? 0 : 2,
                        my: isMobile ? 1 : 0,
                      }} />
                    </Box>
                    <Box sx={{ textAlign: isMobile ? 'left' : 'right' }}>
                      <Typography variant="body2" color="text.primary">
                        {formatTime(segment.arrival.at)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {segment.arrival.iataCode}
                      </Typography>
                    </Box>
                  </Box>
                }
                sx={{ my: 0 }}
              />
            </ListItem>
            
            {idx < segments.length - 1 && (
              <Box sx={{ textAlign: 'center', my: 1 }}>
                <Chip
                  label={`Layover: ${formatDuration(
                    (new Date(segments[idx + 1].departure.at).getTime() - 
                    new Date(segment.arrival.at).getTime()) / (1000 * 60)
                  )}`}
                  size="small"
                  variant="outlined"
                />
              </Box>
            )}
          </React.Fragment>
        ))}
      </List>
    );
  };
  
  // Render flight card
  const renderFlightCard = (flight: FlightOffer) => {
    const firstSegment = flight.itineraries[0].segments[0];
    const lastSegment = flight.itineraries[0].segments[flight.itineraries[0].segments.length - 1];
    const totalDuration = flight.itineraries[0].duration;
    const stops = flight.itineraries[0].segments.length - 1;
    const isExpanded = expandedFlight === flight.id;
    
    return (
      <Card 
        key={flight.id} 
        variant="outlined"
        sx={{
          mb: 2,
          transition: 'all 0.3s ease-in-out',
          '&:hover': {
            boxShadow: theme.shadows[2],
          },
        }}
      >
        <CardContent sx={{ p: isMobile ? 1 : 2, pb: '0 !important' }}>
          <Grid container spacing={2} alignItems="center">
            {/* Airline Logo and Info */}
            <Grid item xs={12} md={3}>
              <Box display="flex" alignItems="center">
                <Avatar 
                  src={AIRLINE_LOGOS[flight.validatingAirlineCodes?.[0] || '']}
                  alt={flight.validatingAirlineCodes?.[0] || 'Airline'}
                  sx={{ width: 48, height: 48, mr: 2 }}
                >
                  <AirlineIcon />
                </Avatar>
                <Box>
                  <Typography variant="subtitle1" fontWeight={500}>
                    {flight.validatingAirlineCodes?.map(code => code).join(', ')}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {stops === 0 ? 'Non-stop' : `${stops} stop${stops > 1 ? 's' : ''}`}
                  </Typography>
                </Box>
              </Box>
              
              {flight.isMock && (
                <Chip
                  label="Mock Data"
                  size="small"
                  color="warning"
                  variant="outlined"
                  sx={{ mt: 1 }}
                />
              )}
            </Grid>
            
            {/* Flight Times */}
            <Grid item xs={12} md={5}>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box textAlign={isMobile ? 'left' : 'center'}>
                  <Typography variant="h6">
                    {formatTime(firstSegment.departure.at)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {firstSegment.departure.iataCode}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {formatDate(firstSegment.departure.at)}
                  </Typography>
                </Box>
                
                <Box textAlign="center" px={1} sx={{ flex: 1, maxWidth: 200, mx: 'auto' }}>
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
                      <FlightTakeoffIcon color="action" fontSize="small" />
                    </Box>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {formatDuration(totalDuration)}
                  </Typography>
                  
                  {stops > 0 && (
                    <Typography variant="caption" color="text.secondary" display="block">
                      {stops} stop{stops > 1 ? 's' : ''}
                    </Typography>
                  )}
                </Box>
                
                <Box textAlign={isMobile ? 'right' : 'center'}>
                  <Typography variant="h6">
                    {formatTime(lastSegment.arrival.at)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {lastSegment.arrival.iataCode}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {formatDate(lastSegment.arrival.at)}
                  </Typography>
                </Box>
              </Box>
            </Grid>
            
            {/* Price and Actions */}
            <Grid item xs={12} md={4}>
              <Box display="flex" flexDirection="column" alignItems={isMobile ? 'flex-start' : 'flex-end'}>
                <Box textAlign={isMobile ? 'left' : 'right'} mb={1}>
                  <Typography variant="h5" color="primary" fontWeight={600}>
                    {formatPrice(parseFloat(flight.price.total), flight.price.currency)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {flight.travelerPricings?.length || 1} {flight.travelerPricings?.length === 1 ? 'person' : 'people'}
                  </Typography>
                </Box>
                
                <Box display="flex" gap={1} mt={1}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => toggleExpandFlight(flight.id)}
                    endIcon={isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                  >
                    {isExpanded ? 'Less' : 'Details'}
                  </Button>
                  <Button
                    variant="contained"
                    size="small"
                    onClick={() => onSelectFlight(flight)}
                  >
                    Select
                  </Button>
                </Box>
              </Box>
            </Grid>
          </Grid>
          
          {/* Flight Details */}
          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <Box mt={2} pt={2} borderTop={`1px solid ${theme.palette.divider}`}>
              <Typography variant="subtitle2" gutterBottom>
                Flight Details
              </Typography>
              {renderSegments(flight.itineraries[0].segments, isMobile)}
              
              <Box mt={2} pt={2} borderTop={`1px solid ${theme.palette.divider}`}>
                <Typography variant="subtitle2" gutterBottom>
                  Price Details
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <List dense disablePadding>
                      {flight.travelerPricings?.map((pricing, idx) => (
                        <ListItem key={idx} disableGutters>
                          <ListItemText
                            primary={`${pricing.travelerType.charAt(0).toUpperCase() + pricing.travelerType.slice(1)} (x${pricing.quantity || 1})`}
                            secondary={`${formatPrice(parseFloat(pricing.price.total), pricing.price.currency)}`}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Box bgcolor="grey.50" p={2} borderRadius={1}>
                      <Box display="flex" justifyContent="space-between" mb={1}>
                        <Typography>Total:</Typography>
                        <Typography fontWeight={600}>
                          {formatPrice(parseFloat(flight.price.total), flight.price.currency)}
                        </Typography>
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        Includes taxes and fees
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </Box>
            </Box>
          </Collapse>
        </CardContent>
      </Card>
    );
  };
  
  // Render loading skeleton
  const renderLoadingSkeleton = () => {
    return Array(3).fill(0).map((_, idx) => (
      <Card key={idx} variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={3}>
              <Box display="flex" alignItems="center">
                <Skeleton variant="circular" width={48} height={48} />
                <Box sx={{ ml: 2 }}>
                  <Skeleton width={100} height={24} />
                  <Skeleton width={80} height={20} />
                </Box>
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Skeleton variant="rectangular" width="100%" height={60} />
            </Grid>
            <Grid item xs={12} md={3}>
              <Skeleton variant="rectangular" width="100%" height={40} />
              <Skeleton variant="rectangular" width="100%" height={36} sx={{ mt: 1 }} />
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    ));
  };
  
  return (
    <Box id="search-results">
      {/* Sort Options */}
      <Box mb={3} display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2}>
        <Typography variant="subtitle1" fontWeight={500}>
          {flights.length} {flights.length === 1 ? 'Flight' : 'Flights'} Found
        </Typography>
        
        <Box display="flex" alignItems="center" flexWrap="wrap" gap={1}>
          <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>
            Sort by:
          </Typography>
          <ToggleButtonGroup
            size="small"
            value={sortBy}
            exclusive
            onChange={handleSortChange}
            aria-label="sort flights"
          >
            <ToggleButton value="price">
              <PriceIcon fontSize="small" sx={{ mr: 0.5 }} />
              Price
            </ToggleButton>
            <ToggleButton value="duration">
              <DurationIcon fontSize="small" sx={{ mr: 0.5 }} />
              Duration
            </ToggleButton>
            <ToggleButton value="departure">
              <FlightTakeoffIcon fontSize="small" sx={{ mr: 0.5 }} />
              Departure
            </ToggleButton>
            <ToggleButton value="arrival">
              <FlightLandIcon fontSize="small" sx={{ mr: 0.5 }} />
              Arrival
            </ToggleButton>
          </ToggleButtonGroup>
          
          <Tooltip title={sortOrder === 'asc' ? 'Sort ascending' : 'Sort descending'}>
            <IconButton 
              size="small" 
              onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
              color={sortOrder === 'asc' ? 'primary' : 'default'}
            >
              {sortOrder === 'asc' ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Tooltip>
        </Box>
      </Box>
      
      {/* Flight List */}
      {loading ? (
        renderLoadingSkeleton()
      ) : sortedFlights.length > 0 ? (
        sortedFlights.map(flight => renderFlightCard(flight))
      ) : (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No flights found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Try adjusting your search criteria to find more options.
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default FlightList;
