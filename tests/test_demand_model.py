"""
Tests for the demand prediction model.
"""
import sys
import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.demand_model import DemandPredictor, train_demand_model, predict_demand

@pytest.fixture
def sample_flight_data() -> pd.DataFrame:
    """Generate sample flight data for testing."""
    np.random.seed(42)
    n_samples = 1000
    
    # Generate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
    
    # Generate sample data
    data = {
        'departure_time': np.random.choice(dates, size=n_samples),
        'origin': np.random.choice(['SYD', 'MEL', 'BNE', 'PER', 'ADL'], size=n_samples),
        'destination': np.random.choice(['LAX', 'JFK', 'SFO', 'LHR', 'CDG'], size=n_samples),
        'airline': np.random.choice(['QF', 'VA', 'JQ', 'NZ', 'EY'], size=n_samples),
        'cabin_class': np.random.choice(['Economy', 'Business', 'First'], size=n_samples, p=[0.7, 0.25, 0.05]),
        'price': np.random.normal(500, 200, size=n_samples).clip(100, 2000),
        'demand': np.random.poisson(lam=50, size=n_samples).clip(1, 200)
    }
    
    # Add some seasonality
    df = pd.DataFrame(data)
    df['month'] = df['departure_time'].dt.month
    df.loc[df['month'].isin([6, 7, 12]), 'demand'] = (df['demand'] * 1.5).clip(1, 200)
    df.loc[df['month'].isin([1, 2, 9]), 'demand'] = (df['demand'] * 0.7).clip(1, 200)
    
    # Add weekends/holidays effect
    df['day_of_week'] = df['departure_time'].dt.dayofweek
    df.loc[df['day_of_week'].isin([5, 6]), 'demand'] = (df['demand'] * 1.3).clip(1, 200)
    
    # Add price-demand relationship
    df['demand'] = (df['demand'] * (1.5 - (df['price'] / df['price'].max()))).clip(1, 200).astype(int)
    
    return df

def test_demand_predictor_initialization() -> None:
    """Test initialization of the DemandPredictor class."""
    # Test default initialization
    predictor = DemandPredictor()
    assert predictor.model_type == 'random_forest'
    assert predictor.model is not None
    assert predictor.feature_processor is not None
    
    # Test initialization with custom model type
    predictor = DemandPredictor(model_type='gradient_boosting')
    assert predictor.model_type == 'gradient_boosting'
    
    # Test initialization with custom parameters
    predictor = DemandPredictor(model_params={'n_estimators': 50, 'max_depth': 5})
    assert predictor.model.n_estimators == 50
    assert predictor.model.max_depth == 5

def test_prepare_features(sample_flight_data: pd.DataFrame) -> None:
    """Test feature preparation."""
    predictor = DemandPredictor()
    
    # Test with minimal required columns
    df = sample_flight_data[['departure_time', 'origin', 'destination']].copy()
    prepared = predictor.prepare_features(df)
    
    # Check that required features are created
    assert 'day_of_week' in prepared.columns
    assert 'month' in prepared.columns
    assert 'is_weekend' in prepared.columns
    assert 'days_until_departure' in prepared.columns
    assert 'seasonal_factor' in prepared.columns
    assert 'is_holiday' in prepared.columns
    
    # Check data types
    assert prepared['day_of_week'].dtype == int
    assert prepared['is_weekend'].dtype == int
    assert prepared['is_holiday'].dtype == int
    
    # Test with booking date
    df = sample_flight_data[['departure_time', 'booking_date', 'origin', 'destination']].copy()
    df['booking_date'] = df['departure_time'] - pd.to_timedelta(np.random.randint(1, 30, size=len(df)), unit='D')
    prepared = predictor.prepare_features(df)
    assert 'days_since_booking' in prepared.columns
    assert 'advance_purchase' in prepared.columns

def test_train_model(sample_flight_data: pd.DataFrame) -> None:
    """Test model training."""
    # Prepare data
    df = sample_flight_data.copy()
    
    # Test training with default parameters
    predictor = DemandPredictor()
    metrics = predictor.train(df, validation_split=0.2)
    
    # Check that metrics are returned
    assert 'train' in metrics
    assert 'mae' in metrics['train']
    assert 'r2' in metrics['train']
    
    # Check validation metrics are included
    assert 'validation' in metrics
    assert 'mae' in metrics['validation']
    
    # Test training without validation
    metrics = predictor.train(df, validation_split=0.0)
    assert 'validation' not in metrics

def test_predict(sample_flight_data: pd.DataFrame) -> None:
    """
    Test making predictions.

    This test checks that the predict method correctly makes predictions using the trained model.
    """
    # Train a model
    df = sample_flight_data.copy()
    predictor = DemandPredictor(model_params={'n_estimators': 10})  # Small model for testing
    predictor.train(df, validation_split=0.0)
    
    # Make predictions
    test_data = df.drop(columns=['demand']).iloc[:10]  # First 10 samples for testing
    predictions = predictor.predict(test_data)
    
    # Check predictions
    assert len(predictions) == len(test_data)
    assert all(predictions >= 0)  # Demand should be non-negative
    
    # Test with minimal required features
    test_data_minimal = test_data[['departure_time', 'origin', 'destination']]
    predictions_minimal = predictor.predict(test_data_minimal)
    assert len(predictions_minimal) == len(test_data_minimal)

def test_save_load_model(tmp_path: Any, sample_flight_data: pd.DataFrame) -> None:
    """Test saving and loading the model."""
    # Train a model
    df = sample_flight_data.copy()
    predictor = DemandPredictor(model_params={'n_estimators': 10})  # Small model for testing
    predictor.train(df, validation_split=0.0)
    
    # Save the model
    model_path = tmp_path / "test_model.joblib"
    predictor.save(model_path)
    assert model_path.exists()
    
    # Load the model
    loaded_predictor = DemandPredictor.load(model_path)
    
    # Test that predictions are the same
    test_data = df.drop(columns=['demand']).iloc[:5]
    original_predictions = predictor.predict(test_data)
    loaded_predictions = loaded_predictor.predict(test_data)
    
    assert np.allclose(original_predictions, loaded_predictions, rtol=1e-5)

def test_train_demand_model_helper(
    sample_flight_data: pd.DataFrame, 
    tmp_path: Any
) -> None:
    """Test the train_demand_model helper function."""
    # Test with default parameters
    model = train_demand_model(
        sample_flight_data,
        model_type='random_forest',
        output_path=str(tmp_path / "model.joblib")
    )
    
    assert model is not None
    assert (tmp_path / "model.joblib").exists()
    
    # Test with gradient boosting
    model = train_demand_model(
        sample_flight_data,
        model_type='gradient_boosting',
        output_path=str(tmp_path / "gb_model.joblib")
    )
    assert model.model_type == 'gradient_boosting'
    assert (tmp_path / "gb_model.joblib").exists()

def test_predict_demand_helper(sample_flight_data: pd.DataFrame, tmp_path: Any) -> None:
    """Test the predict_demand helper function."""
    # Train and save a model
    model_path = tmp_path / "test_model.joblib"
    model = train_demand_model(
        sample_flight_data, 
        model_type='random_forest',
        output_path=str(model_path)
    )
    
    # Test with model instance
    test_data = sample_flight_data.drop(columns=['demand']).iloc[:10]
    predictions = predict_demand(model, test_data)
    assert len(predictions) == len(test_data)
    
    # Test with model path
    predictions_from_path = predict_demand(str(model_path), test_data)
    assert len(predictions_from_path) == len(test_data)
    assert all(predictions == predictions_from_path)

def test_feature_importance(sample_flight_data: pd.DataFrame) -> None:
    """Test that feature importance can be accessed after training."""
    # Train a model
    predictor = DemandPredictor(n_estimators=10)
    predictor.train(sample_flight_data)
    
    # For Random Forest, feature_importances_ should be available
    if hasattr(predictor.model, 'feature_importances_'):
        importances = predictor.model.feature_importances_
        assert len(importances) > 0
        assert all(imp >= 0 for imp in importances)

def test_handle_missing_values() -> None:
    """Test handling of missing values in the input data."""
    # Create test data with missing values
    data = {
        'departure_time': [datetime.now()] * 5,
        'origin': ['SYD', 'MEL', None, 'BNE', 'PER'],
        'destination': ['LAX', None, 'JFK', 'SFO', 'LHR'],
        'price': [100, 200, None, 300, 400],
        'demand': [50, 60, 70, None, 90]
    }
    df = pd.DataFrame(data)
    
    # Test that the model can handle missing values
    predictor = DemandPredictor(n_estimators=10)
    
    # Should not raise an error
    predictor.train(df)
    
    # Test prediction with missing values
    test_data = df.drop(columns=['demand'])
    predictions = predictor.predict(test_data)
    assert len(predictions) == len(test_data)
