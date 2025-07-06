"""
Data cleaning and processing utilities for airline market data.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import logging
import pandas as pd
import numpy as np
from dateutil import parser

logger = logging.getLogger(__name__)

class DataCleaner:
    """
    Handles cleaning and preprocessing of raw airline market data.
    """
    
    @staticmethod
    def clean_flight_data(flight_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean and standardize flight data from various sources.
        
        Args:
            flight_data: List of flight records as dictionaries
            
        Returns:
            List[Dict]: Cleaned flight data
        """
        if not flight_data:
            return []
            
        cleaned_data = []
        
        for flight in flight_data:
            try:
                # Standardize date/time fields
                flight = DataCleaner._standardize_dates(flight)
                
                # Clean and validate airport codes
                flight = DataCleaner._clean_airport_codes(flight)
                
                # Convert numeric fields and handle missing values
                flight = DataCleaner._clean_numeric_fields(flight)
                
                # Clean and standardize airline and flight numbers
                flight = DataCleaner._clean_airline_info(flight)
                
                # Add derived fields
                flight = DataCleaner._add_derived_fields(flight)
                
                cleaned_data.append(flight)
                
            except Exception as e:
                logger.error(f"Error cleaning flight data: {e}", exc_info=True)
                continue
                
        return cleaned_data
    
    @staticmethod
    def _standardize_dates(flight: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize date/time fields to ISO format."""
        date_fields = [
            'departure_time', 'arrival_time', 'booking_date', 
            'created_at', 'updated_at'
        ]
        
        for field in date_fields:
            if field in flight and flight[field]:
                try:
                    if isinstance(flight[field], (int, float)):
                        # Handle Unix timestamps
                        flight[field] = datetime.fromtimestamp(flight[field]).isoformat()
                    elif isinstance(flight[field], str):
                        # Parse and standardize date strings
                        flight[field] = parser.parse(flight[field]).isoformat()
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse {field}: {flight[field]}")
                    flight[f"{field}_raw"] = flight[field]
                    del flight[field]
                    
        return flight
    
    @staticmethod
    def _clean_airport_codes(flight: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate airport codes."""
        for code_field in ['origin', 'destination', 'operating_airline', 'marketing_airline']:
            if code_field in flight and flight[code_field]:
                # Convert to string and uppercase
                code = str(flight[code_field]).strip().upper()
                
                # Basic validation - should be 2-4 letter code
                if not (2 <= len(code) <= 4 and code.isalpha()):
                    logger.warning(f"Invalid {code_field} code: {code}")
                    flight[f"{code_field}_raw"] = code
                    del flight[code_field]
                else:
                    flight[code_field] = code
                    
        return flight
    
    @staticmethod
    def _clean_numeric_fields(flight: Dict[str, Any]) -> Dict[str, Any]:
        """Convert and clean numeric fields."""
        numeric_fields = [
            'price', 'base_fare', 'taxes', 'fees', 'available_seats',
            'total_seats', 'flight_duration', 'distance', 'baggage_allowance'
        ]
        
        for field in numeric_fields:
            if field in flight and flight[field] is not None:
                try:
                    # Handle different numeric formats and strings with currency symbols
                    if isinstance(flight[field], str):
                        # Remove currency symbols and thousands separators
                        value = ''.join(c for c in flight[field] if c.isdigit() or c in '.-')
                        flight[field] = float(value) if '.' in value else int(value)
                    else:
                        # Convert to appropriate numeric type
                        flight[field] = float(flight[field])
                        
                    # Ensure non-negative values
                    if flight[field] < 0:
                        logger.warning(f"Negative value for {field}: {flight[field]}")
                        flight[field] = abs(flight[field])
                        
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not convert {field}: {flight[field]}")
                    flight[f"{field}_raw"] = flight[field]
                    del flight[field]
                    
        return flight
    
    @staticmethod
    def _clean_airline_info(flight: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and standardize airline and flight number information."""
        if 'flight_number' in flight and flight['flight_number']:
            # Extract numeric flight number
            try:
                if isinstance(flight['flight_number'], str):
                    # Remove any non-numeric characters
                    flight['flight_number'] = int(''.join(c for c in flight['flight_number'] if c.isdigit()))
                else:
                    flight['flight_number'] = int(flight['flight_number'])
            except (ValueError, TypeError):
                logger.warning(f"Invalid flight number: {flight['flight_number']}")
                flight['flight_number_raw'] = flight['flight_number']
                del flight['flight_number']
                
        # Standardize airline codes
        for airline_field in ['operating_airline', 'marketing_airline']:
            if airline_field in flight and flight[airline_field]:
                # Convert to 2-letter IATA code if it's a known airline name
                flight[airline_field] = flight[airline_field].upper()
                
        return flight
    
    @staticmethod
    def _add_derived_fields(flight: Dict[str, Any]) -> Dict[str, Any]:
        """Add useful derived fields to the flight data."""
        # Add a unique identifier if not present
        if 'id' not in flight:
            flight_id_parts = [
                flight.get('operating_airline', ''),
                str(flight.get('flight_number', '')),
                flight.get('origin', ''),
                flight.get('departure_time', '')
            ]
            flight['id'] = '_'.join(part for part in flight_id_parts if part)
            
        # Calculate flight duration if not provided
        if 'flight_duration' not in flight and all(k in flight for k in ['departure_time', 'arrival_time']):
            try:
                dep_time = parser.isoparse(flight['departure_time'])
                arr_time = parser.isoparse(flight['arrival_time'])
                flight['flight_duration'] = (arr_time - dep_time).total_seconds() / 60  # in minutes
            except (ValueError, TypeError):
                pass
                
        # Add booking class category
        if 'booking_class' in flight and isinstance(flight['booking_class'], str):
            booking_class = flight['booking_class'].upper()
            if booking_class in ['F', 'A', 'P']:
                flight['cabin_class'] = 'First'
            elif booking_class in ['J', 'C', 'D', 'I', 'Z']:
                flight['cabin_class'] = 'Business'
            elif booking_class in ['W', 'E', 'Y', 'B', 'M', 'H', 'Q', 'K', 'L', 'V', 'S', 'N']:
                flight['cabin_class'] = 'Economy'
                
        return flight


class DataProcessor:
    """
    Handles data processing and transformation for market analysis.
    """
    
    @staticmethod
    def calculate_market_trends(flights: List[Dict[str, Any]], 
                              group_by: str = 'day',
                              metrics: List[str] = None) -> Dict[str, Any]:
        """
        Calculate market trends from flight data.
        
        Args:
            flights: List of flight records
            group_by: Time period to group by ('hour', 'day', 'week', 'month')
            metrics: List of metrics to calculate (default: ['price', 'available_seats'])
            
        Returns:
            Dict containing aggregated market trends
        """
        if not flights:
            return {}
            
        metrics = metrics or ['price', 'available_seats']
        
        try:
            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(flights)
            
            # Ensure required columns exist
            if 'departure_time' not in df.columns:
                raise ValueError("Missing required column: departure_time")
                
            # Convert departure_time to datetime if it's not already
            if not pd.api.types.is_datetime64_any_dtype(df['departure_time']):
                df['departure_time'] = pd.to_datetime(df['departure_time'])
            
            # Set departure_time as index for time-based operations
            df.set_index('departure_time', inplace=True)
            
            # Group by time period
            if group_by == 'hour':
                grouper = df.groupby([pd.Grouper(freq='H')])
            elif group_by == 'day':
                grouper = df.groupby([pd.Grouper(freq='D')])
            elif group_by == 'week':
                grouper = df.groupby([pd.Grouper(freq='W-MON')])
            elif group_by == 'month':
                grouper = df.groupby([pd.Grouper(freq='M')])
            else:
                raise ValueError(f"Invalid group_by value: {group_by}. Must be one of: hour, day, week, month")
            
            # Calculate metrics
            result = {}
            
            if 'price' in metrics and 'price' in df.columns:
                result['price'] = {
                    'min': grouper['price'].min().to_dict(),
                    'max': grouper['price'].max().to_dict(),
                    'mean': grouper['price'].mean().to_dict(),
                    'median': grouper['price'].median().to_dict(),
                    'count': grouper['price'].count().to_dict()
                }
                
            if 'available_seats' in metrics and 'available_seats' in df.columns:
                result['available_seats'] = {
                    'sum': grouper['available_seats'].sum().to_dict(),
                    'mean': grouper['available_seats'].mean().to_dict(),
                    'count': grouper['available_seats'].count().to_dict()
                }
                
            # Calculate load factor if we have both available_seats and total_seats
            if all(col in df.columns for col in ['available_seats', 'total_seats']):
                df['booked_seats'] = df['total_seats'] - df['available_seats']
                df['load_factor'] = (df['booked_seats'] / df['total_seats']) * 100
                
                result['load_factor'] = {
                    'mean': grouper['load_factor'].mean().to_dict(),
                    'median': grouper['load_factor'].median().to_dict()
                }
                
            return result
            
        except Exception as e:
            logger.error(f"Error calculating market trends: {e}", exc_info=True)
            raise
    
    @staticmethod
    def detect_price_anomalies(flights: List[Dict[str, Any]], 
                             window: int = 7,
                             threshold: float = 2.0) -> List[Dict[str, Any]]:
        """
        Detect price anomalies in flight data using Z-score method.
        
        Args:
            flights: List of flight records
            window: Rolling window size for calculating mean and std
            threshold: Z-score threshold for anomaly detection
            
        Returns:
            List of flights with anomaly scores and flags
        """
        if not flights or 'price' not in flights[0]:
            return []
            
        try:
            df = pd.DataFrame(flights)
            
            # Ensure we have a datetime index
            if 'departure_time' in df.columns:
                df['departure_time'] = pd.to_datetime(df['departure_time'])
                df = df.sort_values('departure_time')
                df.set_index('departure_time', inplace=True)
            
            # Calculate rolling statistics
            roll_mean = df['price'].rolling(window=window, min_periods=1).mean()
            roll_std = df['price'].rolling(window=window, min_periods=1).std()
            
            # Calculate Z-scores
            df['price_zscore'] = (df['price'] - roll_mean) / roll_std
            df['is_anomaly'] = abs(df['price_zscore']) > threshold
            
            # Convert back to list of dicts
            result = df.reset_index().to_dict('records')
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting price anomalies: {e}", exc_info=True)
            return flights  # Return original data on error
    
    @staticmethod
    def calculate_demand_metrics(flights: List[Dict[str, Any]], 
                               departure_date: str = None,
                               lookback_days: int = 30) -> Dict[str, Any]:
        """
        Calculate demand metrics for flights.
        
        Args:
            flights: List of flight records
            departure_date: Reference date for demand calculation (default: today)
            lookback_days: Number of days to look back for historical comparison
            
        Returns:
            Dict containing demand metrics
        """
        if not flights:
            return {}
            
        try:
            df = pd.DataFrame(flights)
            
            # Ensure we have required columns
            if 'departure_time' not in df.columns:
                raise ValueError("Missing required column: departure_time")
                
            # Convert departure_time to datetime if it's not already
            df['departure_time'] = pd.to_datetime(df['departure_time'])
            
            # Set reference date
            ref_date = pd.to_datetime(departure_date) if departure_date else pd.Timestamp.now()
            start_date = ref_date - pd.Timedelta(days=lookback_days)
            
            # Filter data for the lookback period
            mask = (df['departure_time'] >= start_date) & (df['departure_time'] <= ref_date)
            df_filtered = df[mask].copy()
            
            if df_filtered.empty:
                return {}
                
            # Calculate days until departure
            df_filtered['days_until_departure'] = (df_filtered['departure_time'] - ref_date).dt.days
            
            # Group by days until departure
            grouped = df_filtered.groupby('days_until_departure')
            
            # Calculate demand metrics
            metrics = {
                'price_trend': {
                    'mean': grouped['price'].mean().to_dict(),
                    'median': grouped['price'].median().to_dict(),
                    'count': grouped['price'].count().to_dict()
                },
                'booking_curve': {}
            }
            
            # Calculate booking curve if we have booking dates
            if 'booking_date' in df_filtered.columns:
                df_filtered['booking_date'] = pd.to_datetime(df_filtered['booking_date'])
                df_filtered['days_booked_in_advance'] = (df_filtered['departure_time'] - df_filtered['booking_date']).dt.days
                
                # Group by days booked in advance
                booking_curve = df_filtered.groupby('days_booked_in_advance')['price'].agg(['mean', 'median', 'count'])
                metrics['booking_curve'] = booking_curve.to_dict()
                
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating demand metrics: {e}", exc_info=True)
            return {}


def process_flight_data(flights: List[Dict[str, Any]], 
                      clean: bool = True,
                      calculate_trends: bool = True,
                      detect_anomalies: bool = False) -> Dict[str, Any]:
    """
    Process flight data with optional cleaning and analysis.
    
    Args:
        flights: List of flight records
        clean: Whether to clean the data
        calculate_trends: Whether to calculate market trends
        detect_anomalies: Whether to detect price anomalies
        
    Returns:
        Dict containing processed data and analysis results
    """
    result = {'raw_count': len(flights) if flights else 0}
    
    # Clean the data if requested
    if clean and flights:
        cleaner = DataCleaner()
        flights = cleaner.clean_flight_data(flights)
        result['cleaned_count'] = len(flights)
    
    result['flights'] = flights
    
    # Perform additional analysis if requested
    if flights:
        processor = DataProcessor()
        
        if calculate_trends:
            try:
                result['trends'] = processor.calculate_market_trends(flights)
            except Exception as e:
                logger.error(f"Error calculating trends: {e}")
                result['trends_error'] = str(e)
                
        if detect_anomalies and any('price' in f for f in flights):
            try:
                result['anomalies'] = processor.detect_price_anomalies(flights)
            except Exception as e:
                logger.error(f"Error detecting anomalies: {e}")
                result['anomalies_error'] = str(e)
    
    return result
