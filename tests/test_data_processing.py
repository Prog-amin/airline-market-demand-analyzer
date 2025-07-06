"""
Tests for the data processing module.
"""
import pytest
import sys
import os
from datetime import datetime, timedelta

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.data_processing import DataCleaner, DataProcessor, process_flight_data

def test_clean_flight_data():
    ""Test cleaning flight data with various input formats."""
    # Test data with various formats and potential issues
    raw_flights = [
        {
            'id': 'QF400',
            'origin': '  syd  ',  # Extra spaces
            'destination': 'MEL',
            'departure_time': '2023-12-01T08:00:00',
            'arrival_time': '2023-12-01T09:30:00',
            'price': '$199.99',  # Currency symbol
            'available_seats': '150',  # String number
            'flight_number': 'QF400',
            'booking_class': 'Y',
            'created_at': 1701388800  # Unix timestamp
        },
        {
            'origin': 'MEL',
            'destination': 'SYD',
            'departure_time': '2023-12-02T18:00:00+10:00',  # Timezone
            'price': 249.99,
            'available_seats': 0,  # Zero value
            'flight_number': 'VA800',
            'booking_class': 'J',
            'total_seats': 200
        },
        {
            'origin': 'INVALID',  # Invalid airport code
            'destination': 'SYD',
            'departure_time': 'invalid-date',  # Invalid date
            'price': 'N/A',  # Invalid price
            'flight_number': 'QF401',
            'booking_class': 'F'
        }
    ]
    
    # Clean the data
    cleaner = DataCleaner()
    cleaned = cleaner.clean_flight_data(raw_flights)
    
    # Assertions
    assert len(cleaned) == 3  # All records should be present
    
    # Test first flight
    assert cleaned[0]['origin'] == 'SYD'  # Should be uppercase and trimmed
    assert isinstance(cleaned[0]['price'], float)  # Should be converted to float
    assert cleaned[0]['price'] == 199.99
    assert isinstance(cleaned[0]['available_seats'], int)  # Should be converted to int
    assert cleaned[0]['available_seats'] == 150
    assert 'created_at' in cleaned[0]  # Should be converted to ISO format
    assert cleaned[0]['cabin_class'] == 'Economy'  # Derived field
    
    # Test second flight
    assert cleaned[1]['departure_time'].endswith('+10:00')  # Timezone preserved
    assert 'total_seats' in cleaned[1]
    assert 'load_factor' in cleaned[1]  # Should be calculated
    
    # Test third flight (with invalid data)
    assert 'origin_raw' in cleaned[2]  # Original invalid value should be preserved
    assert 'departure_time' not in cleaned[2]  # Invalid date should be removed
    assert 'price' not in cleaned[2]  # Invalid price should be removed

def test_calculate_market_trends():
    ""Test calculating market trends from flight data."""
    # Create test data with flights over several days
    test_flights = []
    base_date = datetime(2023, 12, 1)
    
    for i in range(10):  # 10 days of data
        flight_date = base_date + timedelta(days=i)
        for j in range(3):  # 3 flights per day
            test_flights.append({
                'departure_time': flight_date.isoformat(),
                'price': 200 + (i * 10) + (j * 5),  # Increasing price over time
                'available_seats': 100 - (i * 5) - j,  # Decreasing availability
                'total_seats': 200,
                'origin': 'SYD',
                'destination': 'MEL',
                'flight_number': f'QF{400 + j}'
            })
    
    # Calculate trends
    processor = DataProcessor()
    trends = processor.calculate_market_trends(
        test_flights, 
        group_by='day',
        metrics=['price', 'available_seats']
    )
    
    # Assertions
    assert 'price' in trends
    assert 'available_seats' in trends
    assert 'load_factor' in trends  # Should be calculated automatically
    
    # Should have 10 days of data
    assert len(trends['price']['mean']) == 10
    
    # Prices should be increasing over time
    prices = list(trends['price']['mean'].values())
    assert all(prices[i] <= prices[i+1] for i in range(len(prices)-1))
    
    # Available seats should be decreasing
    seats = list(trends['available_seats']['sum'].values())
    assert all(seats[i] >= seats[i+1] for i in range(len(seats)-1))

def test_detect_price_anomalies():
    ""Test detecting price anomalies in flight data."""
    # Create test data with some anomalies
    test_flights = []
    base_date = datetime(2023, 12, 1)
    
    # Add normal prices around $200
    for i in range(20):
        test_flights.append({
            'departure_time': (base_date + timedelta(hours=i)).isoformat(),
            'price': 190 + (i % 20),  # Oscillating around 200
            'origin': 'SYD',
            'destination': 'MEL',
            'flight_number': f'QF{400 + (i % 5)}'
        })
    
    # Add some anomalies
    test_flights.extend([
        {'departure_time': (base_date + timedelta(hours=21)).isoformat(), 'price': 500, 'origin': 'SYD', 'destination': 'MEL', 'flight_number': 'QF999'},
        {'departure_time': (base_date + timedelta(hours=22)).isoformat(), 'price': 50, 'origin': 'SYD', 'destination': 'MEL', 'flight_number': 'QF888'}
    ])
    
    # Detect anomalies
    processor = DataProcessor()
    result = processor.detect_price_anomalies(test_flights, window=7, threshold=2.0)
    
    # Convert back to a more usable format
    anomalies = [f for f in result if f.get('is_anomaly', False)]
    
    # Should detect the two anomalies we added
    assert len(anomalies) == 2
    assert any(f['price'] == 500 for f in anomalies)
    assert any(f['price'] == 50 for f in anomalies)
    
    # The anomalies should have high absolute z-scores
    anomaly_scores = [f['price_zscore'] for f in anomalies]
    assert all(abs(score) > 2.0 for score in anomaly_scores)

def test_process_flight_data_integration():
    ""Test the integrated process_flight_data function."""
    # Test data with various issues
    test_flights = [
        {
            'origin': '  syd  ',
            'destination': 'MEL',
            'departure_time': '2023-12-01T08:00:00',
            'price': '$199.99',
            'available_seats': '150',
            'total_seats': '200',
            'flight_number': 'QF400'
        },
        {
            'origin': 'MEL',
            'destination': 'SYD',
            'departure_time': '2023-12-02T18:00:00',
            'price': 249.99,
            'available_seats': 50,
            'total_seats': 200,
            'flight_number': 'VA800'
        }
    ]
    
    # Process the data
    result = process_flight_data(
        test_flights,
        clean=True,
        calculate_trends=True,
        detect_anomalies=True
    )
    
    # Assertions
    assert result['raw_count'] == 2
    assert len(result['flights']) == 2
    assert 'trends' in result
    assert 'anomalies' in result
    
    # Check that cleaning was applied
    assert result['flights'][0]['origin'] == 'SYD'  # Cleaned
    assert isinstance(result['flights'][0]['price'], float)  # Converted to float
    
    # Check that trends were calculated
    assert 'price' in result['trends']
    assert 'available_seats' in result['trends']
    
    # Check that anomalies were detected (though none expected in this small dataset)
    assert isinstance(result['anomalies'], list)

def test_calculate_demand_metrics():
    ""Test calculating demand metrics from flight data."""
    # Create test data with bookings over time
    test_flights = []
    base_date = datetime(2023, 12, 1)
    
    # Create bookings from 30 days before to day of departure
    for days_before in range(30, -1, -1):
        departure_time = base_date
        booking_date = departure_time - timedelta(days=days_before)
        
        # Price generally increases as departure approaches
        price = 100 + (30 - days_before) * 5
        
        test_flights.append({
            'departure_time': departure_time.isoformat(),
            'booking_date': booking_date.isoformat(),
            'price': price,
            'origin': 'SYD',
            'destination': 'MEL',
            'flight_number': 'QF400'
        })
    
    # Calculate demand metrics
    processor = DataProcessor()
    metrics = processor.calculate_demand_metrics(
        test_flights,
        departure_date=base_date.isoformat(),
        lookback_days=30
    )
    
    # Assertions
    assert 'price_trend' in metrics
    assert 'booking_curve' in metrics
    
    # Should have data for all 30 days
    assert len(metrics['price_trend']['mean']) == 31  # 30 days + day of
    
    # Prices should generally increase as days_until_departure decreases
    price_trend = metrics['price_trend']
    days = sorted(int(d) for d in price_trend['mean'].keys())
    prices = [price_trend['mean'][str(d)] for d in days]
    
    # Overall trend should be decreasing (higher prices as departure approaches)
    assert sum(prices[i] <= prices[i+1] for i in range(len(prices)-1)) > len(prices) / 2
    
    # Check booking curve data
    if metrics['booking_curve']:  # Might be empty if booking_date wasn't properly parsed
        assert 'mean' in metrics['booking_curve']
        assert len(metrics['booking_curve']['mean']) > 0
