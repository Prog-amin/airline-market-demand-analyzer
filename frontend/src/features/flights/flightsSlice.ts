import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { flightsApi } from '../../services/api';

interface Segment {
  id: string;
  departure: {
    iataCode: string;
    at: string;
  };
  arrival: {
    iataCode: string;
    at: string;
  };
  carrierCode: string;
  number: string;
  aircraft: {
    code: string;
  };
  duration: string;
}

interface Itinerary {
  duration: string;
  segments: Segment[];
}

interface Price {
  currency: string;
  total: string;
  base: string;
  fees: Array<{
    amount: string;
    type: string;
  }>;
  grandTotal: string;
}

interface PricingOptions {
  fareType: string[];
  includedCheckedBagsOnly: boolean;
}

interface TravelerPricing {
  travelerId: string;
  fareOption: string;
  travelerType: string;
  price: {
    currency: string;
    total: string;
    base: string;
  };
  fareDetailsBySegment: Array<{
    segmentId: string;
    cabin: string;
    fareBasis: string;
    class: string;
    includedCheckedBags: {
      quantity: number;
    };
  }>;
}

export interface FlightOffer {
  type: string;
  id: string;
  source: string;
  instantTicketingRequired: boolean;
  nonHomogeneous: boolean;
  oneWay: boolean;
  lastTicketingDate: string;
  lastTicketingDateTime: string;
  numberOfBookableSeats: number;
  itineraries: Itinerary[];
  price: Price;
  pricingOptions: PricingOptions;
  validatingAirlineCodes: string[];
  travelerPricings: TravelerPricing[];
  isMock?: boolean;
  sourceProvider?: string;
}

interface FlightsState {
  searchResults: FlightOffer[];
  loading: boolean;
  error: string | null;
  searchParams: {
    origin: string;
    destination: string;
    departureDate: string;
    returnDate?: string;
    adults: number;
    children: number;
    infants: number;
    travelClass: string;
    nonStop: boolean;
    maxPrice?: number;
    includeAirlines: string[];
    excludeAirlines: string[];
    useRealData: boolean;
  };
  selectedFlight: FlightOffer | null;
}

const initialState: FlightsState = {
  searchResults: [],
  loading: false,
  error: null,
  searchParams: {
    origin: 'SYD',
    destination: 'MEL',
    departureDate: new Date().toISOString().split('T')[0],
    adults: 1,
    children: 0,
    infants: 0,
    travelClass: 'ECONOMY',
    nonStop: false,
    includeAirlines: [],
    excludeAirlines: [],
    useRealData: true,
  },
  selectedFlight: null,
};

export const searchFlights = createAsyncThunk(
  'flights/search',
  async (params: Partial<FlightsState['searchParams']>, { rejectWithValue }) => {
    try {
      const response = await flightsApi.searchFlights({
        ...initialState.searchParams,
        ...params,
      });
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to search flights');
    }
  }
);

const flightsSlice = createSlice({
  name: 'flights',
  initialState,
  reducers: {
    setSearchParams: (state, action: PayloadAction<Partial<FlightsState['searchParams']>>) => {
      state.searchParams = {
        ...state.searchParams,
        ...action.payload,
      };
    },
    resetSearchParams: (state) => {
      state.searchParams = initialState.searchParams;
    },
    selectFlight: (state, action: PayloadAction<FlightOffer | null>) => {
      state.selectedFlight = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(searchFlights.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(searchFlights.fulfilled, (state, action: PayloadAction<{ data: FlightOffer[] }>) => {
        state.loading = false;
        state.searchResults = action.payload.data;
      })
      .addCase(searchFlights.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { setSearchParams, resetSearchParams, selectFlight, clearError } = flightsSlice.actions;

export default flightsSlice.reducer;

// Selectors
export const selectSearchResults = (state: { flights: FlightsState }) => state.flights.searchResults;
export const selectSearchParams = (state: { flights: FlightsState }) => state.flights.searchParams;
export const selectSelectedFlight = (state: { flights: FlightsState }) => state.flights.selectedFlight;
export const selectFlightsLoading = (state: { flights: FlightsState }) => state.flights.loading;
export const selectFlightsError = (state: { flights: FlightsState }) => state.flights.error;
