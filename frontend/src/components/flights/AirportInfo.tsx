import React from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Button,
  Chip,
  useTheme,
  Link,
  Tabs,
  Tab,
  Card,
  CardContent,
  CardMedia,
  CardActions,
  Avatar,
} from '@mui/material';
import {
  FlightTakeoff as DepartureIcon,
  FlightLand as ArrivalIcon,
  LocationOn as LocationIcon,
  Phone as PhoneIcon,
  Language as WebsiteIcon,
  AccessTime as HoursIcon,
  LocalParking as ParkingIcon,
  DirectionsBus as TransitIcon,
  LocalTaxi as TaxiIcon,
  Hotel as HotelIcon,
  Restaurant as RestaurantIcon,
  ShoppingCart as ShoppingIcon,
  Wifi as WifiIcon,
  Business as BusinessIcon,
  LocalAtm as AtmIcon,
  LocalDrink as LoungeIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { FlightOffer } from '../../types/flight';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`airport-tabpanel-${index}`}
      aria-labelledby={`airport-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `airport-tab-${index}`,
    'aria-controls': `airport-tabpanel-${index}`,
  };
}

interface AirportInfoProps {
  flight: FlightOffer;
}

const AirportInfo: React.FC<AirportInfoProps> = ({ flight }) => {
  const theme = useTheme();
  const [tabValue, setTabValue] = React.useState(0);
  
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };
  
  // Get departure and arrival airports
  const departureAirport = flight.itineraries[0].segments[0].departure;
  const arrivalAirport = flight.itineraries[0].segments[
    flight.itineraries[0].segments.length - 1
  ].arrival;
  
  // Mock airport data (in a real app, this would come from an API)
  const getAirportData = (iataCode: string) => {
    const airports: Record<string, any> = {
      'SYD': {
        name: 'Sydney Kingsford Smith Airport',
        city: 'Sydney',
        country: 'Australia',
        terminal: 'T1 (International)',
        phone: '+61 2 9667 9111',
        website: 'https://www.sydneyairport.com.au',
        description: 'Sydney Airport is Australia\'s busiest airport, located 8km south of the Sydney central business district. It serves as a hub for Qantas and Virgin Australia, and is a major hub for international travel to and from Australia.',
        facilities: [
          'Free WiFi',
          'Currency Exchange',
          'Luggage Storage',
          'Showers',
          'Prayer Room',
          'Medical Services',
        ],
        services: [
          { name: 'Lounges', icon: <LoungeIcon /> },
          { name: 'ATMs', icon: <AtmIcon /> },
          { name: 'Business Center', icon: <BusinessIcon /> },
          { name: 'Shops', icon: <ShoppingIcon /> },
          { name: 'Restaurants', icon: <RestaurantIcon /> },
          { name: 'Hotels', icon: <HotelIcon /> },
        ],
        transport: [
          {
            name: 'Train',
            description: 'Airport Link train service to Sydney CBD (15 mins)',
            icon: <TransitIcon />,
            price: 'AUD 18.70',
            frequency: 'Every 10-15 mins',
            hours: '5:00 AM - 12:00 AM'
          },
          {
            name: 'Taxi',
            description: 'Taxi rank outside all terminals',
            icon: <TaxiIcon />,
            price: 'AUD 45-60',
            time: '20-30 mins to CBD',
            hours: '24/7'
          },
          {
            name: 'Ride Share',
            description: 'Uber, Ola and other ride-share services',
            icon: <TaxiIcon />,
            price: 'AUD 35-50',
            pickup: 'Designated pickup zones',
            hours: '24/7'
          },
          {
            name: 'Bus',
            description: 'Route 400 & 420 to Bondi Junction',
            icon: <TransitIcon />,
            price: 'AUD 4.80',
            frequency: 'Every 15-30 mins',
            hours: '5:00 AM - 11:30 PM'
          },
        ],
        parking: [
          {
            name: 'Terminal Parking',
            type: 'Short-term',
            price: 'AUD 25 first hour, then AUD 15 per hour',
            max: 'AUD 129 per day',
            walking: '2-5 min walk to terminals'
          },
          {
            name: 'Domestic Parking',
            type: 'Long-term',
            price: 'AUD 15 first hour, then AUD 10 per hour',
            max: 'AUD 69 per day',
            shuttle: '5-10 min shuttle to terminals'
          },
          {
            name: 'Value Parking',
            type: 'Economy',
            price: 'AUD 12 first hour, then AUD 8 per hour',
            max: 'AUD 49 per day',
            shuttle: '10-15 min shuttle to terminals'
          },
        ],
        hotels: [
          {
            name: 'Rydges Sydney Airport',
            distance: '5 min walk to T1',
            price: 'AUD 250-350',
            rating: 4.2,
            amenities: ['Free WiFi', 'Restaurant', 'Bar', 'Gym', 'Pool'],
            image: 'https://images.unsplash.com/photo-1566073771259-6a8506099945?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80'
          },
          {
            name: 'Ibis Budget Sydney Airport',
            distance: 'Shuttle to terminals',
            price: 'AUD 120-180',
            rating: 3.8,
            amenities: ['Free WiFi', '24-hour front desk', 'Airport shuttle'],
            image: 'https://images.unsplash.com/photo-1566073771259-6a8506099945?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80'
          },
        ]
      },
      'MEL': {
        name: 'Melbourne Airport',
        city: 'Melbourne',
        country: 'Australia',
        terminal: 'T2 (International)',
        phone: '+61 3 9297 1600',
        website: 'https://www.melbourneairport.com.au',
        description: 'Melbourne Airport is the second busiest airport in Australia, located 23km northwest of Melbourne city center. It serves as a major hub for both domestic and international flights.',
        facilities: [
          'Free WiFi',
          'Currency Exchange',
          'Luggage Storage',
          'Showers',
          'Prayer Room',
        ],
        services: [
          { name: 'Lounges', icon: <LoungeIcon /> },
          { name: 'ATMs', icon: <AtmIcon /> },
          { name: 'Business Center', icon: <BusinessIcon /> },
        ],
      },
      'BNE': {
        name: 'Brisbane Airport',
        city: 'Brisbane',
        country: 'Australia',
        terminal: 'International Terminal',
        phone: '+61 7 3406 3000',
        website: 'https://www.bne.com.au',
        description: 'Brisbane Airport is the primary international airport serving Brisbane and South East Queensland. It is the third busiest airport in Australia.',
        facilities: [
          'Free WiFi',
          'Currency Exchange',
          'Luggage Storage',
        ],
        services: [
          { name: 'Lounges', icon: <LoungeIcon /> },
          { name: 'ATMs', icon: <AtmIcon /> },
        ],
      },
    };
    
    return airports[iataCode] || {
      name: `${iataCode} Airport`,
      city: iataCode,
      country: 'Australia',
      terminal: 'Main Terminal',
      phone: 'N/A',
      website: '#',
      description: `Information about ${iataCode} Airport is not available.`,
      facilities: [],
      services: [],
      transport: [],
      parking: [],
      hotels: [],
    };
  };
  
  const departureData = getAirportData(departureAirport.iataCode);
  const arrivalData = getAirportData(arrivalAirport.iataCode);
  const currentAirport = tabValue === 0 ? departureData : arrivalData;
  const isCurrentDeparture = tabValue === 0;
  
  // Format time
  const formatTime = (dateString: string): string => {
    return new Date(dateString).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: true 
    });
  };
  
  // Format date
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-AU', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });
  };
  
  // Render transport options
  const renderTransport = () => {
    if (!currentAirport.transport || currentAirport.transport.length === 0) {
      return (
        <Box textAlign="center" py={4}>
          <Typography variant="body1" color="text.secondary">
            No transport information available
          </Typography>
        </Box>
      );
    }
    
    return (
      <Grid container spacing={2}>
        {currentAirport.transport.map((transport: any, index: number) => (
          <Grid item xs={12} sm={6} key={index}>
            <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
              <Box display="flex" alignItems="center" mb={1}>
                <Box 
                  sx={{
                    width: 40,
                    height: 40,
                    borderRadius: '50%',
                    bgcolor: 'primary.main',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'primary.contrastText',
                    mr: 2,
                  }}
                >
                  {React.cloneElement(transport.icon, { fontSize: 'small' })}
                </Box>
                <Typography variant="subtitle1">{transport.name}</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" mb={1}>
                {transport.description}
              </Typography>
              <Typography variant="body2">
                <strong>Price:</strong> {transport.price}
              </Typography>
              {transport.time && (
                <Typography variant="body2">
                  <strong>Time to city:</strong> {transport.time}
                </Typography>
              )}
              {transport.frequency && (
                <Typography variant="body2">
                  <strong>Frequency:</strong> {transport.frequency}
                </Typography>
              )}
              <Typography variant="body2">
                <strong>Hours:</strong> {transport.hours}
              </Typography>
              {transport.pickup && (
                <Typography variant="caption" display="block" color="text.secondary" mt={1}>
                  {transport.pickup}
                </Typography>
              )}
            </Paper>
          </Grid>
        ))}
      </Grid>
    );
  };
  
  // Render parking information
  const renderParking = () => {
    if (!currentAirport.parking || currentAirport.parking.length === 0) {
      return (
        <Box textAlign="center" py={4}>
          <Typography variant="body1" color="text.secondary">
            No parking information available
          </Typography>
        </Box>
      );
    }
    
    return (
      <Grid container spacing={2}>
        {currentAirport.parking.map((parking: any, index: number) => (
          <Grid item xs={12} sm={6} md={4} key={index}>
            <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
              <Box display="flex" alignItems="center" mb={1}>
                <ParkingIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="subtitle1">{parking.name}</Typography>
                <Chip 
                  label={parking.type} 
                  size="small" 
                  color="primary" 
                  variant="outlined"
                  sx={{ ml: 'auto' }}
                />
              </Box>
              <Typography variant="body2" color="text.secondary" mb={1}>
                {parking.walking && `🚶‍♂️ ${parking.walking}`}
                {parking.shuttle && `🚌 ${parking.shuttle}`}
              </Typography>
              <Typography variant="body2">
                <strong>Price:</strong> {parking.price}
              </Typography>
              <Typography variant="body2">
                <strong>Max daily:</strong> {parking.max}
              </Typography>
              <Button 
                variant="outlined" 
                size="small" 
                fullWidth 
                sx={{ mt: 2 }}
                startIcon={<InfoIcon />}
              >
                Book Parking
              </Button>
            </Paper>
          </Grid>
        ))}
      </Grid>
    );
  };
  
  // Render nearby hotels
  const renderHotels = () => {
    if (!currentAirport.hotels || currentAirport.hotels.length === 0) {
      return (
        <Box textAlign="center" py={4}>
          <Typography variant="body1" color="text.secondary">
            No hotel information available
          </Typography>
        </Box>
      );
    }
    
    return (
      <Grid container spacing={3}>
        {currentAirport.hotels.map((hotel: any, index: number) => (
          <Grid item xs={12} md={6} key={index}>
            <Card sx={{ display: 'flex', height: '100%' }}>
              <CardMedia
                component="img"
                sx={{ width: 150, display: { xs: 'none', sm: 'block' } }}
                image={hotel.image}
                alt={hotel.name}
              />
              <Box sx={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
                <CardContent sx={{ flex: '1 0 auto' }}>
                  <Typography component="div" variant="h6">
                    {hotel.name}
                  </Typography>
                  <Typography variant="subtitle2" color="text.secondary" component="div" mb={1}>
                    {hotel.distance} • ★ {hotel.rating.toFixed(1)}
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={0.5} mb={1}>
                    {hotel.amenities.map((amenity: string, idx: number) => (
                      <Chip 
                        key={idx} 
                        label={amenity} 
                        size="small" 
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </CardContent>
                <CardActions sx={{ justifyContent: 'space-between', p: 2, pt: 0 }}>
                  <Typography variant="h6" color="primary">
                    From {hotel.price}
                  </Typography>
                  <Button size="small" variant="contained">
                    Book Now
                  </Button>
                </CardActions>
              </Box>
            </Card>
          </Grid>
        ))}
      </Grid>
    );
  };
  
  // Render terminal map
  const renderTerminalMap = () => {
    // In a real app, this would be an actual map or terminal diagram
    return (
      <Box textAlign="center" py={4}>
        <Box 
          sx={{
            height: 300,
            bgcolor: 'grey.100',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 1,
            mb: 2,
          }}
        >
          <Typography color="text.secondary">
            {currentAirport.name} Terminal Map
          </Typography>
        </Box>
        <Button 
          variant="outlined" 
          startIcon={<ExpandMoreIcon />}
          onClick={() => window.open(`https://www.google.com/search?q=${currentAirport.name}+terminal+map`, '_blank')}
        >
          View Full Terminal Map
        </Button>
      </Box>
    );
  };
  
  return (
    <Box>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          aria-label="airport tabs"
          variant="fullWidth"
        >
          <Tab 
            label={
              <Box sx={{ textTransform: 'none' }}>
                <Box>Departure</Box>
                <Box sx={{ fontSize: '0.75rem' }}>{departureAirport.iataCode}</Box>
              </Box>
            } 
            {...a11yProps(0)} 
          />
          <Tab 
            label={
              <Box sx={{ textTransform: 'none' }}>
                <Box>Arrival</Box>
                <Box sx={{ fontSize: '0.75rem' }}>{arrivalAirport.iataCode}</Box>
              </Box>
            } 
            {...a11yProps(1)} 
          />
        </Tabs>
      </Box>
      
      <TabPanel value={tabValue} index={0}>
        <Box mb={4}>
          <Box display="flex" alignItems="center" mb={2}>
            <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
              <DepartureIcon />
            </Avatar>
            <Box>
              <Typography variant="h6">
                {departureData.name} ({departureAirport.iataCode})
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {departureData.city}, {departureData.country}
              </Typography>
            </Box>
          </Box>
          
          <Box mb={3}>
            <Typography variant="subtitle2" color="text.secondary">
              Your flight departs from
            </Typography>
            <Typography variant="h6" gutterBottom>
              {departureData.terminal || 'Main Terminal'}
            </Typography>
            <Typography variant="body1" gutterBottom>
              <strong>Departure:</strong> {formatTime(departureAirport.at)} on {formatDate(departureAirport.at)}
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Please arrive at least 3 hours before departure for international flights.
            </Typography>
          </Box>
          
          <Box mb={3}>
            <Typography variant="subtitle1" gutterBottom>
              About {departureData.name}
            </Typography>
            <Typography variant="body2" paragraph>
              {departureData.description}
            </Typography>
            
            <Box display="flex" flexWrap="wrap" gap={2} mb={2}>
              <Button 
                variant="outlined" 
                size="small" 
                startIcon={<PhoneIcon />}
                href={`tel:${departureData.phone}`}
              >
                {departureData.phone}
              </Button>
              <Button 
                variant="outlined" 
                size="small" 
                startIcon={<WebsiteIcon />}
                href={departureData.website}
                target="_blank"
                rel="noopener noreferrer"
              >
                Visit Website
              </Button>
            </Box>
          </Box>
          
          <Divider sx={{ my: 3 }} />
          
          <Box mb={4}>
            <Typography variant="subtitle1" gutterBottom>
              Terminal Map
            </Typography>
            {renderTerminalMap()}
          </Box>
          
          <Box mb={4}>
            <Typography variant="subtitle1" gutterBottom>
              Airport Facilities
            </Typography>
            <Grid container spacing={2}>
              {departureData.facilities.map((facility: string, index: number) => (
                <Grid item xs={6} sm={4} md={3} key={index}>
                  <Chip 
                    label={facility} 
                    variant="outlined" 
                    icon={<InfoIcon />}
                    sx={{ width: '100%', justifyContent: 'flex-start' }}
                  />
                </Grid>
              ))}
            </Grid>
          </Box>
          
          <Box mb={4}>
            <Typography variant="subtitle1" gutterBottom>
              Transport to Airport
            </Typography>
            {renderTransport()}
          </Box>
          
          <Box mb={4}>
            <Typography variant="subtitle1" gutterBottom>
              Parking Options
            </Typography>
            {renderParking()}
          </Box>
          
          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Nearby Hotels
            </Typography>
            {renderHotels()}
          </Box>
        </Box>
      </TabPanel>
      
      <TabPanel value={tabValue} index={1}>
        <Box mb={4}>
          <Box display="flex" alignItems="center" mb={2}>
            <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
              <ArrivalIcon />
            </Avatar>
            <Box>
              <Typography variant="h6">
                {arrivalData.name} ({arrivalAirport.iataCode})
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {arrivalData.city}, {arrivalData.country}
              </Typography>
            </Box>
          </Box>
          
          <Box mb={3}>
            <Typography variant="subtitle2" color="text.secondary">
              Your flight arrives at
            </Typography>
            <Typography variant="h6" gutterBottom>
              {arrivalData.terminal || 'Main Terminal'}
            </Typography>
            <Typography variant="body1" gutterBottom>
              <strong>Arrival:</strong> {formatTime(arrivalAirport.at)} on {formatDate(arrivalAirport.at)}
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Estimated time to clear immigration: 30-60 minutes
            </Typography>
          </Box>
          
          <Box mb={3}>
            <Typography variant="subtitle1" gutterBottom>
              About {arrivalData.name}
            </Typography>
            <Typography variant="body2" paragraph>
              {arrivalData.description}
            </Typography>
            
            <Box display="flex" flexWrap="wrap" gap={2} mb={2}>
              <Button 
                variant="outlined" 
                size="small" 
                startIcon={<PhoneIcon />}
                href={`tel:${arrivalData.phone}`}
              >
                {arrivalData.phone}
              </Button>
              <Button 
                variant="outlined" 
                size="small" 
                startIcon={<WebsiteIcon />}
                href={arrivalData.website}
                target="_blank"
                rel="noopener noreferrer"
              >
                Visit Website
              </Button>
            </Box>
          </Box>
          
          <Divider sx={{ my: 3 }} />
          
          <Box mb={4}>
            <Typography variant="subtitle1" gutterBottom>
              Terminal Map
            </Typography>
            {renderTerminalMap()}
          </Box>
          
          <Box mb={4}>
            <Typography variant="subtitle1" gutterBottom>
              Transport from Airport
            </Typography>
            {renderTransport()}
          </Box>
          
          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Nearby Hotels
            </Typography>
            {renderHotels()}
          </Box>
        </Box>
      </TabPanel>
    </Box>
  );
};

export default AirportInfo;
