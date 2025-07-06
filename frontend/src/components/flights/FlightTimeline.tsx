import React from 'react';
import {
  Box,
  Typography,
  Grid,
  Divider,
  Chip,
  Avatar,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Paper,
  useTheme,
} from '@mui/material';
import { FlightOffer } from '../../types/flight';
import AirplanemodeActiveIcon from '@mui/icons-material/AirplanemodeActive';

interface FlightTimelineProps {
  flight: FlightOffer;
}

const FlightTimeline: React.FC<FlightTimelineProps> = ({ flight }) => {
  const theme = useTheme();
  
  // Format duration in minutes to hours and minutes
  const formatDuration = (minutes: number): string => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins.toString().padStart(2, '0')}m`;
  };
  
  // Format date to a readable time
  const formatTime = (dateString: string): string => {
    return new Date(dateString).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: true 
    });
  };
  
  // Format date to day and date
  const formatDayAndDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-AU', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
    });
  };
  
  // Get airport name by IATA code
  const getAirportName = (iataCode: string): string => {
    const airports: Record<string, string> = {
      'SYD': 'Sydney Kingsford Smith Airport',
      'MEL': 'Melbourne Airport',
      'BNE': 'Brisbane Airport',
      'PER': 'Perth Airport',
      'ADL': 'Adelaide Airport',
      'CBR': 'Canberra Airport',
      'HBA': 'Hobart International Airport',
      'DRW': 'Darwin International Airport',
    };
    return airports[iataCode] || iataCode;
  };
  
  // Get aircraft name by code
  const getAircraftName = (code: string): string => {
    const aircraft: Record<string, string> = {
      '320': 'Airbus A320',
      '321': 'Airbus A321',
      '332': 'Airbus A330-200',
      '333': 'Airbus A330-300',
      '359': 'Airbus A350-900',
      '388': 'Airbus A380-800',
      '738': 'Boeing 737-800',
      '789': 'Boeing 787-9 Dreamliner',
      '77W': 'Boeing 777-300ER',
      '788': 'Boeing 787-8 Dreamliner',
    };
    return aircraft[code] || code;
  };
  
  const segments = flight.itineraries[0].segments;
  
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Flight Itinerary
      </Typography>
      
      <Stepper orientation="vertical" sx={{ mt: 2 }}>
        {segments.map((segment, idx) => {
          const departureTime = new Date(segment.departure.at);
          const arrivalTime = new Date(segment.arrival.at);
          const duration = (arrivalTime.getTime() - departureTime.getTime()) / (1000 * 60); // in minutes
          
          return (
            <Step key={idx} active={true}>
              <StepLabel
                StepIconComponent={() => (
                  <Avatar
                    sx={{
                      bgcolor: 'primary.main',
                      width: 32,
                      height: 32,
                      fontSize: '1rem',
                    }}
                  >
                    {idx + 1}
                  </Avatar>
                )}
              >
                <Box display="flex" justifyContent="space-between" flexWrap="wrap" width="100%">
                  <Box>
                    <Typography variant="subtitle1" fontWeight={500}>
                      {segment.departure.iataCode} → {segment.arrival.iataCode}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {segment.carrierCode} {segment.number} • {getAircraftName(segment.aircraft.code)}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {formatDuration(duration)}
                  </Typography>
                </Box>
              </StepLabel>
              <StepContent>
                <Grid container spacing={2} sx={{ mt: 1, mb: 2 }}>
                  <Grid item xs={12} md={5}>
                    <Box display="flex" justifyContent="space-between">
                      <Box>
                        <Typography variant="h6">{formatTime(segment.departure.at)}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {formatDayAndDate(segment.departure.at)}
                        </Typography>
                      </Box>
                      
                      <Box textAlign="center" px={2} sx={{ flex: 1, maxWidth: 100 }}>
                        <Box sx={{ position: 'relative', height: 2, bgcolor: 'divider', my: 2 }}>
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
                            <AirplanemodeActiveIcon color="action" fontSize="small" />
                          </Box>
                        </Box>
                        <Typography variant="caption" color="text.secondary">
                          {formatDuration(duration)}
                        </Typography>
                      </Box>
                      
                      <Box textAlign="right">
                        <Typography variant="h6">{formatTime(segment.arrival.at)}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {formatDayAndDate(segment.arrival.at)}
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} md={7}>
                    <Paper variant="outlined" sx={{ p: 2 }}>
                      <Grid container spacing={2}>
                        <Grid item xs={6} sm={3}>
                          <Box>
                            <Typography variant="caption" color="text.secondary">
                              Departure
                            </Typography>
                            <Typography variant="body2">
                              {segment.departure.iataCode} • {segment.departure.terminal || 'T1'}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              {getAirportName(segment.departure.iataCode)}
                            </Typography>
                          </Box>
                        </Grid>
                        
                        <Grid item xs={6} sm={3}>
                          <Box>
                            <Typography variant="caption" color="text.secondary">
                              Arrival
                            </Typography>
                            <Typography variant="body2">
                              {segment.arrival.iataCode} • {segment.arrival.terminal || 'T1'}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              {getAirportName(segment.arrival.iataCode)}
                            </Typography>
                          </Box>
                        </Grid>
                        
                        <Grid item xs={6} sm={3}>
                          <Box>
                            <Typography variant="caption" color="text.secondary">
                              Flight
                            </Typography>
                            <Typography variant="body2">
                              {segment.carrierCode} {segment.number}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              {getAircraftName(segment.aircraft.code)}
                            </Typography>
                          </Box>
                        </Grid>
                        
                        <Grid item xs={6} sm={3}>
                          <Box>
                            <Typography variant="caption" color="text.secondary">
                              Cabin Class
                            </Typography>
                            <Typography variant="body2">
                              {flight.travelerPricings?.[0]?.fareOption?.replace('_', ' ') || 'Economy'}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {segment.operating?.carrierCode ? `Operated by ${segment.operating.carrierCode}` : ''}
                            </Typography>
                          </Box>
                        </Grid>
                      </Grid>
                    </Paper>
                  </Grid>
                </Grid>
                
                {idx < segments.length - 1 && (
                  <Box textAlign="center" my={2}>
                    <Chip
                      label={`Layover: ${formatDuration(
                        (new Date(segments[idx + 1].departure.at).getTime() - 
                        new Date(segment.arrival.at).getTime()) / (1000 * 60)
                      )} in ${segment.arrival.iataCode}`}
                      size="small"
                      variant="outlined"
                      sx={{ bgcolor: 'background.paper' }}
                    />
                  </Box>
                )}
              </StepContent>
            </Step>
          );
        })}
      </Stepper>
      
      <Box mt={3}>
        <Typography variant="subtitle1" gutterBottom>
          Total Travel Time
        </Typography>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography variant="body1">
              {formatTime(segments[0].departure.at)} - {formatTime(segments[segments.length - 1].arrival.at)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {formatDayAndDate(segments[0].departure.at)} - {formatDayAndDate(segments[segments.length - 1].arrival.at)}
            </Typography>
          </Box>
          <Chip 
            label={`${Math.floor(flight.itineraries[0].duration / 60)}h ${flight.itineraries[0].duration % 60}m`} 
            color="primary" 
            variant="outlined"
          />
        </Box>
      </Box>
    </Box>
  );
};

export default FlightTimeline;
