import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { Box, Container, Typography, Grid, Paper, CircularProgress, Alert } from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

// Components
import FlightSearchForm from '../components/flights/FlightSearchForm';
import FlightList from '../components/flights/FlightList';

// Redux
import { searchFlights, selectSearchResults, selectFlightsLoading, selectFlightsError } from '../features/flights/flightsSlice';
import { AppDispatch } from '../store';

// Types
import { FlightOffer } from '../types/flight';

const FlightSearchPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  
  // Redux state
  const searchResults = useSelector(selectSearchResults);
  const loading = useSelector(selectFlightsLoading);
  const error = useSelector(selectFlightsError);
  
  // Local state for search parameters
  const [searchParams, setSearchParams] = useState({
    origin: 'SYD',
    destination: 'MEL',
    departureDate: new Date(),
    returnDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 7 days from now
    adults: 1,
    children: 0,
    infants: 0,
    travelClass: 'ECONOMY',
    nonStop: false,
    maxPrice: '',
    includeAirlines: [],
    excludeAirlines: [],
    useRealData: true,
  });
  
  // Handle search form submission
  const handleSearch = (params: typeof searchParams) => {
    setSearchParams(params);
    
    // Prepare search parameters for the API
    const apiParams = {
      ...params,
      departureDate: params.departureDate.toISOString().split('T')[0],
      returnDate: params.returnDate ? params.returnDate.toISOString().split('T')[0] : undefined,
      maxPrice: params.maxPrice ? parseInt(params.maxPrice, 10) : undefined,
    };
    
    // Dispatch search action
    dispatch(searchFlights(apiParams));
    
    // Scroll to results
    if (searchResults.length > 0 || error) {
      const resultsElement = document.getElementById('search-results');
      if (resultsElement) {
        resultsElement.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };
  
  // Handle flight selection
  const handleSelectFlight = (flight: FlightOffer) => {
    navigate(`/flights/${flight.id}`, { state: { flight } });
  };
  
  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Container maxWidth={false} sx={{ maxWidth: 1600, py: 4 }}>
        <Grid container spacing={3}>
          {/* Search Form */}
          <Grid item xs={12} md={4} lg={3}>
            <Paper elevation={3} sx={{ p: 3, borderRadius: 2, position: 'sticky', top: 20 }}>
              <FlightSearchForm 
                initialValues={searchParams}
                onSubmit={handleSearch}
                loading={loading}
              />
            </Paper>
          </Grid>
          
          {/* Search Results */}
          <Grid item xs={12} md={8} lg={9}>
            {error && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {error}
              </Alert>
            )}
            
            {loading ? (
              <Box display="flex" justifyContent="center" my={8}>
                <CircularProgress />
              </Box>
            ) : searchResults.length > 0 ? (
              <FlightList 
                flights={searchResults}
                onSelectFlight={handleSelectFlight}
              />
            ) : !loading && !error ? (
              <Box textAlign="center" py={8}>
                <Typography variant="h6" color="text.secondary">
                  No flights found. Try adjusting your search criteria.
                </Typography>
              </Box>
            ) : null}
          </Grid>
        </Grid>
      </Container>
    </LocalizationProvider>
  );
};

export default FlightSearchPage;
