import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  useTheme,
  Avatar,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  AirlineSeatReclineNormal as SeatIcon,
  Luggage as LuggageIcon,
  Wifi as WifiIcon,
  Restaurant as MealIcon,
  Tv as EntertainmentIcon,
  Power as PowerIcon,
  LocalDrink as DrinkIcon,
  ExpandMore as ExpandMoreIcon,
  AirlineSeatIndividualSuite as SuiteIcon,
  AirlineSeatFlat as LieFlatIcon,
  AirlineSeatReclineExtra as ExtraLegroomIcon,
  AirlineSeatLegroomReduced as StandardSeatIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { FlightOffer } from '../../types/flight';

interface CabinDetailsProps {
  flight: FlightOffer;
}

const CabinDetails: React.FC<CabinDetailsProps> = ({ flight }) => {
  const theme = useTheme();
  
  // Get cabin class details
  const cabinClass = flight.travelerPricings?.[0]?.fareOption || 'ECONOMY';
  const cabinDetails = getCabinDetails(cabinClass);
  
  // Get airline amenities
  const airlineCode = flight.validatingAirlineCodes?.[0] || 'QF';
  const amenities = getAirlineAmenities(airlineCode);
  
  // Get baggage allowance based on cabin class
  const baggageAllowance = getBaggageAllowance(cabinClass);
  
  // Get seat details based on cabin class
  const seatDetails = getSeatDetails(cabinClass);
  
  // Format price with currency
  const formatPrice = (price: number, currency: string = 'AUD'): string => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };
  
  // Helper function to get cabin class details
  function getCabinDetails(cabin: string) {
    const cabins: Record<string, { 
      name: string; 
      description: string; 
      icon: React.ReactNode;
      features: string[];
    }> = {
      'ECONOMY': {
        name: 'Economy Class',
        description: 'Comfortable seating with standard legroom and in-flight service.',
        icon: <StandardSeatIcon sx={{ color: theme.palette.primary.main }} />,
        features: [
          'Standard legroom (76-81 cm / 30-32")',
          'Seat width: 43-46 cm (17-18")',
          'Seat recline: 4-6"',
          'Personal entertainment screen',
          'Complimentary meals and beverages',
          'USB power port',
        ],
      },
      'PREMIUM_ECONOMY': {
        name: 'Premium Economy',
        description: 'Extra legroom and enhanced service for a more comfortable journey.',
        icon: <ExtraLegroomIcon sx={{ color: theme.palette.primary.main }} />,
        features: [
          'Up to 10 cm (4") extra legroom',
          'Wider seats with more recline',
          'Larger personal entertainment screen',
          'Premium meals and beverages',
          'Priority boarding',
          'USB and power outlets',
        ],
      },
      'BUSINESS': {
        name: 'Business Class',
        description: 'Lie-flat seats and premium service for maximum comfort.',
        icon: <LieFlatIcon sx={{ color: theme.palette.primary.main }} />,
        features: [
          'Fully flat beds (180° recline)',
          'Direct aisle access',
          'Premium dining with à la carte menu',
          'Luxury amenity kit',
          'Priority check-in and boarding',
          'Airport lounge access',
        ],
      },
      'FIRST': {
        name: 'First Class',
        description: 'The ultimate in luxury with private suites and personalized service.',
        icon: <SuiteIcon sx={{ color: theme.palette.primary.main }} />,
        features: [
          'Private suite with closing door',
          'Fully flat bed with luxury bedding',
          'Gourmet dining with fine wines',
          'Premium amenity kit and pajamas',
          'Exclusive check-in and security',
          'Chauffeur service (select routes)',
        ],
      },
    };
    
    return cabins[cabin] || cabins['ECONOMY'];
  }
  
  // Helper function to get airline amenities
  function getAirlineAmenities(airlineCode: string) {
    const airlineAmenities: Record<string, Array<{
      id: string;
      label: string;
      icon: React.ReactNode;
      included: boolean;
    }>> = {
      'QF': [
        { id: 'wifi', label: 'WiFi Available', icon: <WifiIcon />, included: true },
        { id: 'meals', label: 'Complimentary Meals', icon: <MealIcon />, included: true },
        { id: 'entertainment', label: 'In-flight Entertainment', icon: <EntertainmentIcon />, included: true },
        { id: 'power', label: 'Power Outlets', icon: <PowerIcon />, included: true },
        { id: 'alcohol', label: 'Complimentary Alcohol', icon: <DrinkIcon />, included: cabinClass !== 'ECONOMY' },
      ],
      'VA': [
        { id: 'wifi', label: 'WiFi Available', icon: <WifiIcon />, included: true },
        { id: 'meals', label: 'Complimentary Meals', icon: <MealIcon />, included: true },
        { id: 'entertainment', label: 'In-flight Entertainment', icon: <EntertainmentIcon />, included: true },
        { id: 'power', label: 'Power Outlets', icon: <PowerIcon />, included: false },
        { id: 'alcohol', label: 'Complimentary Alcohol', icon: <DrinkIcon />, included: cabinClass !== 'ECONOMY' },
      ],
      'JQ': [
        { id: 'wifi', label: 'WiFi Available', icon: <WifiIcon />, included: true },
        { id: 'meals', label: 'Meals for Purchase', icon: <MealIcon />, included: false },
        { id: 'entertainment', label: 'BYO Device Entertainment', icon: <EntertainmentIcon />, included: true },
        { id: 'power', label: 'Power Outlets', icon: <PowerIcon />, included: false },
        { id: 'alcohol', label: 'Alcohol for Purchase', icon: <DrinkIcon />, included: true },
      ],
    };
    
    return airlineAmenities[airlineCode] || airlineAmenities['QF'];
  }
  
  // Helper function to get baggage allowance
  function getBaggageAllowance(cabin: string) {
    const allowances: Record<string, { checked: string; cabin: string; }> = {
      'ECONOMY': {
        checked: '1 x 23kg (50lb)',
        cabin: '1 x 7kg (15lb) + 1 small personal item',
      },
      'PREMIUM_ECONOMY': {
        checked: '2 x 23kg (50lb)',
        cabin: '2 x 7kg (15lb) + 1 small personal item',
      },
      'BUSINESS': {
        checked: '2 x 32kg (70lb)',
        cabin: '2 x 7kg (15lb) + 1 small personal item',
      },
      'FIRST': {
        checked: '3 x 32kg (70lb)',
        cabin: '2 x 7kg (15lb) + 1 small personal item',
      },
    };
    
    return allowances[cabin] || allowances['ECONOMY'];
  }
  
  // Helper function to get seat details
  function getSeatDetails(cabin: string) {
    const seats: Record<string, { 
      pitch: string; 
      width: string; 
      recline: string;
      bedLength?: string;
    }> = {
      'ECONOMY': {
        pitch: '76-81 cm (30-32")',
        width: '43-46 cm (17-18")',
        recline: '10-15 cm (4-6")',
      },
      'PREMIUM_ECONOMY': {
        pitch: '86-96 cm (34-38")',
        width: '48-53 cm (19-21")',
        recline: '15-20 cm (6-8")',
      },
      'BUSINESS': {
        pitch: '183-203 cm (72-80")',
        width: '53-61 cm (21-24")',
        recline: 'Fully flat 180°',
        bedLength: '190-203 cm (75-80")',
      },
      'FIRST': {
        pitch: '203-218 cm (80-86")',
        width: '61-76 cm (24-30")',
        recline: 'Fully flat 180°',
        bedLength: '203-218 cm (80-86")',
      },
    };
    
    return seats[cabin] || seats['ECONOMY'];
  }
  
  return (
    <Box>
      <Box mb={4}>
        <Box display="flex" alignItems="center" mb={2}>
          {React.cloneElement(cabinDetails.icon, { sx: { fontSize: 32, mr: 1.5 } })}
          <Typography variant="h6" component="h2">
            {cabinDetails.name}
          </Typography>
        </Box>
        <Typography variant="body1" color="text.secondary" paragraph>
          {cabinDetails.description}
        </Typography>
        
        <Grid container spacing={3} mt={2}>
          <Grid item xs={12} md={6}>
            <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
              <Typography variant="subtitle2" gutterBottom>Seat Features</Typography>
              <List dense disablePadding>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <SeatIcon color="action" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Seat Pitch" 
                    secondary={seatDetails.pitch} 
                  />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <SeatIcon color="action" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Seat Width" 
                    secondary={seatDetails.width} 
                  />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <SeatIcon color="action" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Seat Recline" 
                    secondary={seatDetails.recline} 
                  />
                </ListItem>
                {seatDetails.bedLength && (
                  <ListItem disableGutters>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <SeatIcon color="action" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Bed Length" 
                      secondary={seatDetails.bedLength} 
                    />
                  </ListItem>
                )}
              </List>
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
              <Typography variant="subtitle2" gutterBottom>Baggage Allowance</Typography>
              <List dense disablePadding>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <LuggageIcon color="action" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Checked Baggage" 
                    secondary={baggageAllowance.checked} 
                  />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <LuggageIcon color="action" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Cabin Baggage" 
                    secondary={baggageAllowance.cabin} 
                  />
                </ListItem>
              </List>
              
              <Box mt={2} pt={2} borderTop={`1px solid ${theme.palette.divider}`}>
                <Button 
                  variant="outlined" 
                  size="small" 
                  startIcon={<InfoIcon />}
                  fullWidth
                >
                  View Baggage Policy
                </Button>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Box>
      
      <Box mb={4}>
        <Typography variant="subtitle1" gutterBottom>
          Cabin Amenities
        </Typography>
        <Grid container spacing={2}>
          {amenities.map((amenity) => (
            <Grid item xs={6} sm={4} md={3} key={amenity.id}>
              <Paper 
                variant="outlined" 
                sx={{ 
                  p: 2, 
                  height: '100%',
                  borderColor: amenity.included ? 'primary.light' : 'divider',
                  bgcolor: amenity.included ? 'primary.50' : 'background.paper',
                }}
              >
                <Box 
                  display="flex" 
                  flexDirection="column" 
                  alignItems="center"
                  textAlign="center"
                >
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: '50%',
                      bgcolor: amenity.included ? 'primary.main' : 'action.disabledBackground',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mb: 1,
                      color: amenity.included ? 'primary.contrastText' : 'action.disabled',
                    }}
                  >
                    {React.cloneElement(amenity.icon, { fontSize: 'medium' })}
                  </Box>
                  <Typography variant="body2">{amenity.label}</Typography>
                  <Typography 
                    variant="caption" 
                    color={amenity.included ? 'primary.main' : 'text.secondary'}
                    fontWeight={500}
                  >
                    {amenity.included ? 'Included' : 'Not Included'}
                  </Typography>
                </Box>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Box>
      
      <Box>
        <Typography variant="subtitle1" gutterBottom>
          Cabin Features
        </Typography>
        
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography>Seating & Comfort</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <List dense>
              {cabinDetails.features.map((feature, index) => (
                <ListItem key={index} disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <Box sx={{ color: 'primary.main' }}>•</Box>
                  </ListItemIcon>
                  <ListItemText primary={feature} />
                </ListItem>
              ))}
            </List>
          </AccordionDetails>
        </Accordion>
        
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography>Food & Beverage</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" color="text.secondary">
              {cabinClass === 'ECONOMY' ? (
                'Complimentary meals and beverages served on all flights. Alcoholic beverages available for purchase.'
              ) : cabinClass === 'PREMIUM_ECONOMY' ? (
                'Premium meals and complimentary alcoholic beverages served on all flights.'
              ) : cabinClass === 'BUSINESS' ? (
                'Gourmet dining with à la carte menu and premium beverages, including champagne and fine wines.'
              ) : (
                'Restaurant-quality dining with multi-course meals, fine wines, and premium spirits. Pre-order your meal selection before your flight.'
              )}
            </Typography>
          </AccordionDetails>
        </Accordion>
        
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography>Entertainment</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" color="text.secondary">
              {cabinClass === 'ECONOMY' ? (
                'Personal seatback entertainment screen with a wide selection of movies, TV shows, music, and games. Headphones provided.'
              ) : cabinClass === 'PREMIUM_ECONOMY' ? (
                'Larger personal entertainment screen with noise-canceling headphones and an enhanced selection of entertainment options.'
              ) : cabinClass === 'BUSINESS' ? (
                'Large HD touchscreen with noise-canceling headphones and an extensive library of movies, TV shows, music, and games.'
              ) : (
                'Ultra HD touchscreen with premium noise-canceling headphones, an extensive entertainment library, and the ability to create your own playlist.'
              )}
            </Typography>
          </AccordionDetails>
        </Accordion>
        
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography>Onboard Services</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" color="text.secondary">
              {cabinClass === 'ECONOMY' ? (
                'Complimentary pillows and blankets on long-haul flights. Duty-free shopping available.'
              ) : cabinClass === 'PREMIUM_ECONOMY' ? (
                'Enhanced amenity kit, premium pillow and blanket, and priority meal service.'
              ) : cabinClass === 'BUSINESS' ? (
                'Luxury amenity kit, premium bedding, and dedicated cabin crew for personalized service.'
              ) : (
                'Exclusive luxury amenity kit, premium bedding designed for maximum comfort, and dedicated cabin crew providing personalized service throughout your flight.'
              )}
            </Typography>
          </AccordionDetails>
        </Accordion>
      </Box>
      
      <Box mt={4} p={2} bgcolor="grey.50" borderRadius={1}>
        <Typography variant="body2" color="text.secondary">
          <strong>Note:</strong> Amenities and services may vary by aircraft type, flight duration, and route. Some services may be modified or unavailable due to operational requirements or government regulations.
        </Typography>
      </Box>
    </Box>
  );
};

export default CabinDetails;
