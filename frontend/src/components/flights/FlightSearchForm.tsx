import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Grid,
  Typography,
  Divider,
  IconButton,
  Paper,
  ToggleButtonGroup,
  ToggleButton,
  useTheme,
  useMediaQuery,
  Collapse,
  Chip,
  SelectChangeEvent,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import {
  FlightTakeoff as FlightTakeoffIcon,
  FlightLand as FlightLandIcon,
  SwapHoriz as SwapHorizIcon,
  AirlineSeatReclineNormal as PassengerIcon,
  BusinessClass as ClassIcon,
  FilterList as FilterIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';

// Mock data for airlines and airports
const AIRLINES = [
  { code: 'QF', name: 'Qantas' },
  { code: 'VA', name: 'Virgin Australia' },
  { code: 'JQ', name: 'Jetstar' },
  { code: 'NZ', name: 'Air New Zealand' },
  { code: 'SQ', name: 'Singapore Airlines' },
];

const AIRPORTS = [
  { code: 'SYD', name: 'Sydney Airport', city: 'Sydney', country: 'Australia' },
  { code: 'MEL', name: 'Melbourne Airport', city: 'Melbourne', country: 'Australia' },
  { code: 'BNE', name: 'Brisbane Airport', city: 'Brisbane', country: 'Australia' },
  { code: 'PER', name: 'Perth Airport', city: 'Perth', country: 'Australia' },
  { code: 'ADL', name: 'Adelaide Airport', city: 'Adelaide', country: 'Australia' },
  { code: 'CBR', name: 'Canberra Airport', city: 'Canberra', country: 'Australia' },
  { code: 'HBA', name: 'Hobart Airport', city: 'Hobart', country: 'Australia' },
  { code: 'DRW', name: 'Darwin International Airport', city: 'Darwin', country: 'Australia' },
];

interface FlightSearchFormProps {
  initialValues: {
    origin: string;
    destination: string;
    departureDate: Date;
    returnDate: Date | null;
    adults: number;
    children: number;
    infants: number;
    travelClass: string;
    nonStop: boolean;
    maxPrice: string;
    includeAirlines: string[];
    excludeAirlines: string[];
    useRealData: boolean;
  };
  onSubmit: (values: any) => void;
  loading?: boolean;
}

const FlightSearchForm: React.FC<FlightSearchFormProps> = ({
  initialValues,
  onSubmit,
  loading = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  // Form state
  const [tripType, setTripType] = useState<'one-way' | 'round-trip'>('round-trip');
  const [showFilters, setShowFilters] = useState(false);
  const [formData, setFormData] = useState(initialValues);
  
  // Update form data when initialValues change
  useEffect(() => {
    setFormData(initialValues);
  }, [initialValues]);
  
  // Handle input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target as HTMLInputElement;
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseInt(value, 10) : value,
    }));
  };
  
  // Handle select changes
  const handleSelectChange = (e: SelectChangeEvent<string | string[]>) => {
    const { name, value } = e.target;
    
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };
  
  // Handle date changes
  const handleDateChange = (name: string, date: Date | null) => {
    setFormData(prev => ({
      ...prev,
      [name]: date,
    }));
  };
  
  // Handle switch changes
  const handleSwitchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    
    setFormData(prev => ({
      ...prev,
      [name]: checked,
    }));
  };
  
  // Handle airline selection changes
  const handleAirlineChange = (e: SelectChangeEvent<string[]>) => {
    const { name, value } = e.target;
    
    setFormData(prev => ({
      ...prev,
      [name]: typeof value === 'string' ? value.split(',') : value,
    }));
  };
  
  // Handle swap origin and destination
  const handleSwapLocations = () => {
    setFormData(prev => ({
      ...prev,
      origin: prev.destination,
      destination: prev.origin,
    }));
  };
  
  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };
  
  // Toggle filters section
  const toggleFilters = () => {
    setShowFilters(!showFilters);
  };
  
  // Handle trip type change
  const handleTripTypeChange = (
    event: React.MouseEvent<HTMLElement>,
    newType: 'one-way' | 'round-trip' | null,
  ) => {
    if (newType !== null) {
      setTripType(newType);
      if (newType === 'one-way') {
        setFormData(prev => ({ ...prev, returnDate: null }));
      } else if (newType === 'round-trip' && !formData.returnDate) {
        const returnDate = new Date(formData.departureDate);
        returnDate.setDate(returnDate.getDate() + 7);
        setFormData(prev => ({ ...prev, returnDate }));
      }
    }
  };
  
  // Get airport name by code
  const getAirportName = (code: string) => {
    const airport = AIRPORTS.find(a => a.code === code);
    return airport ? `${airport.city} (${airport.code})` : code;
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <Box>
        {/* Trip Type Toggle */}
        <Box mb={3}>
          <ToggleButtonGroup
            color="primary"
            value={tripType}
            exclusive
            onChange={handleTripTypeChange}
            aria-label="trip type"
            fullWidth
          >
            <ToggleButton value="round-trip">Round Trip</ToggleButton>
            <ToggleButton value="one-way">One Way</ToggleButton>
          </ToggleButtonGroup>
        </Box>
        
        {/* Origin and Destination */}
        <Grid container spacing={2} mb={2}>
          <Grid item xs={12} sm={5}>
            <FormControl fullWidth>
              <InputLabel id="origin-label">From</InputLabel>
              <Select
                labelId="origin-label"
                id="origin"
                name="origin"
                value={formData.origin}
                onChange={handleSelectChange}
                label="From"
                required
                startAdornment={<FlightTakeoffIcon color="action" sx={{ mr: 1 }} />}
              >
                {AIRPORTS.map((airport) => (
                  <MenuItem key={airport.code} value={airport.code}>
                    {airport.city} ({airport.code})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={2} sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <IconButton
              onClick={handleSwapLocations}
              color="primary"
              sx={{ border: `1px solid ${theme.palette.divider}`, borderRadius: 1 }}
              aria-label="swap locations"
            >
              <SwapHorizIcon />
            </IconButton>
          </Grid>
          
          <Grid item xs={12} sm={5}>
            <FormControl fullWidth>
              <InputLabel id="destination-label">To</InputLabel>
              <Select
                labelId="destination-label"
                id="destination"
                name="destination"
                value={formData.destination}
                onChange={handleSelectChange}
                label="To"
                required
                startAdornment={<FlightLandIcon color="action" sx={{ mr: 1 }} />}
              >
                {AIRPORTS.filter(airport => airport.code !== formData.origin).map((airport) => (
                  <MenuItem key={airport.code} value={airport.code}>
                    {airport.city} ({airport.code})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
        
        {/* Dates */}
        <Grid container spacing={2} mb={2}>
          <Grid item xs={12} sm={tripType === 'round-trip' ? 6 : 12}>
            <DatePicker
              label="Departure"
              value={formData.departureDate}
              onChange={(date) => handleDateChange('departureDate', date)}
              minDate={new Date()}
              renderInput={(params) => (
                <TextField
                  {...params}
                  fullWidth
                  required
                />
              )}
            />
          </Grid>
          
          {tripType === 'round-trip' && (
            <Grid item xs={12} sm={6}>
              <DatePicker
                label="Return"
                value={formData.returnDate}
                onChange={(date) => handleDateChange('returnDate', date)}
                minDate={formData.departureDate || new Date()}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    fullWidth
                    required
                  />
                )}
              />
            </Grid>
          )}
        </Grid>
        
        {/* Passengers and Class */}
        <Grid container spacing={2} mb={3}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel id="passengers-label">Passengers</InputLabel>
              <Select
                labelId="passengers-label"
                id="passengers"
                value={`${formData.adults} Adult${formData.adults > 1 ? 's' : ''}${formData.children > 0 ? `, ${formData.children} Child${formData.children > 1 ? 'ren' : ''}` : ''}${formData.infants > 0 ? `, ${formData.infants} Infant${formData.infants > 1 ? 's' : ''}` : ''}`}
                label="Passengers"
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <PassengerIcon sx={{ mr: 1, color: 'action.active' }} />
                    {selected as string}
                  </Box>
                )}
              >
                <Box sx={{ p: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Box>
                      <Typography>Adults</Typography>
                      <Typography variant="caption" color="text.secondary">12+ years</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <IconButton
                        size="small"
                        onClick={() => {
                          if (formData.adults > 1) {
                            setFormData(prev => ({ ...prev, adults: prev.adults - 1 }));
                          }
                        }}
                        disabled={formData.adults <= 1}
                      >
                        -
                      </IconButton>
                      <Typography sx={{ mx: 1, minWidth: '24px', textAlign: 'center' }}>
                        {formData.adults}
                      </Typography>
                      <IconButton
                        size="small"
                        onClick={() => {
                          setFormData(prev => ({ ...prev, adults: prev.adults + 1 }));
                        }}
                      >
                        +
                      </IconButton>
                    </Box>
                  </Box>
                  
                  <Divider sx={{ my: 2 }} />
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Box>
                      <Typography>Children</Typography>
                      <Typography variant="caption" color="text.secondary">2-11 years</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <IconButton
                        size="small"
                        onClick={() => {
                          if (formData.children > 0) {
                            setFormData(prev => ({ ...prev, children: prev.children - 1 }));
                          }
                        }}
                        disabled={formData.children <= 0}
                      >
                        -
                      </IconButton>
                      <Typography sx={{ mx: 1, minWidth: '24px', textAlign: 'center' }}>
                        {formData.children}
                      </Typography>
                      <IconButton
                        size="small"
                        onClick={() => {
                          setFormData(prev => ({ ...prev, children: prev.children + 1 }));
                        }}
                      >
                        +
                      </IconButton>
                    </Box>
                  </Box>
                  
                  <Divider sx={{ my: 2 }} />
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                      <Typography>Infants</Typography>
                      <Typography variant="caption" color="text.secondary">Under 2 years</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <IconButton
                        size="small"
                        onClick={() => {
                          if (formData.infants > 0) {
                            setFormData(prev => ({ ...prev, infants: prev.infants - 1 }));
                          }
                        }}
                        disabled={formData.infants <= 0}
                      >
                        -
                      </IconButton>
                      <Typography sx={{ mx: 1, minWidth: '24px', textAlign: 'center' }}>
                        {formData.infants}
                      </Typography>
                      <IconButton
                        size="small"
                        onClick={() => {
                          if (formData.infants < formData.adults) {
                            setFormData(prev => ({ ...prev, infants: prev.infants + 1 }));
                          }
                        }}
                        disabled={formData.infants >= formData.adults}
                      >
                        +
                      </IconButton>
                    </Box>
                  </Box>
                </Box>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel id="class-label">Travel Class</InputLabel>
              <Select
                labelId="class-label"
                id="travelClass"
                name="travelClass"
                value={formData.travelClass}
                onChange={handleSelectChange}
                label="Travel Class"
                startAdornment={<ClassIcon color="action" sx={{ mr: 1 }} />}
              >
                <MenuItem value="ECONOMY">Economy</MenuItem>
                <MenuItem value="PREMIUM_ECONOMY">Premium Economy</MenuItem>
                <MenuItem value="BUSINESS">Business</MenuItem>
                <MenuItem value="FIRST">First Class</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
        
        {/* Advanced Filters */}
        <Box mb={3}>
          <Button
            fullWidth
            variant="outlined"
            onClick={toggleFilters}
            startIcon={<FilterIcon />}
            endIcon={showFilters ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            sx={{ justifyContent: 'space-between' }}
          >
            {showFilters ? 'Hide Filters' : 'Advanced Filters'}
          </Button>
          
          <Collapse in={showFilters} timeout="auto" unmountOnExit>
            <Paper elevation={0} sx={{ p: 2, mt: 2, border: `1px solid ${theme.palette.divider}`, borderRadius: 1 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Max Price (AUD)"
                    type="number"
                    name="maxPrice"
                    value={formData.maxPrice}
                    onChange={handleInputChange}
                    InputProps={{
                      startAdornment: <span style={{ marginRight: 8 }}>$</span>,
                    }}
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel id="include-airlines-label">Include Airlines</InputLabel>
                    <Select
                      labelId="include-airlines-label"
                      id="includeAirlines"
                      name="includeAirlines"
                      multiple
                      value={formData.includeAirlines}
                      onChange={handleAirlineChange}
                      renderValue={(selected) => (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {(selected as string[]).map((value) => (
                            <Chip
                              key={value}
                              label={AIRLINES.find(a => a.code === value)?.name || value}
                              size="small"
                            />
                          ))}
                        </Box>
                      )}
                      label="Include Airlines"
                    >
                      {AIRLINES.map((airline) => (
                        <MenuItem key={airline.code} value={airline.code}>
                          {airline.name} ({airline.code})
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel id="exclude-airlines-label">Exclude Airlines</InputLabel>
                    <Select
                      labelId="exclude-airlines-label"
                      id="excludeAirlines"
                      name="excludeAirlines"
                      multiple
                      value={formData.excludeAirlines}
                      onChange={handleAirlineChange}
                      renderValue={(selected) => (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {(selected as string[]).map((value) => (
                            <Chip
                              key={value}
                              label={AIRLINES.find(a => a.code === value)?.name || value}
                              size="small"
                              variant="outlined"
                            />
                          ))}
                        </Box>
                      )}
                      label="Exclude Airlines"
                    >
                      {AIRLINES.map((airline) => (
                        <MenuItem key={airline.code} value={airline.code}>
                          {airline.name} ({airline.code})
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={formData.nonStop}
                        onChange={handleSwitchChange}
                        name="nonStop"
                        color="primary"
                      />
                    }
                    label="Non-stop flights only"
                  />
                  
                  <FormControlLabel
                    control={
                      <Switch
                        checked={formData.useRealData}
                        onChange={handleSwitchChange}
                        name="useRealData"
                        color="primary"
                      />
                    }
                    label="Use real-time data"
                    sx={{ ml: 2 }}
                  />
                </Grid>
              </Grid>
            </Paper>
          </Collapse>
        </Box>
        
        {/* Search Button */}
        <Button
          type="submit"
          variant="contained"
          color="primary"
          size="large"
          fullWidth
          disabled={loading}
        >
          {loading ? 'Searching...' : 'Search Flights'}
        </Button>
      </Box>
    </form>
  );
};

export default FlightSearchForm;
