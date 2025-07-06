"""
Demand prediction model for airline market data.
"""
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, TimeSeriesSplit, GridSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
import joblib
import os

logger = logging.getLogger(__name__)

class DemandPredictor:
    """
    A machine learning model for predicting airline demand and high periods.
    """
    
    def __init__(self, model_type: str = 'random_forest', model_params: Optional[Dict] = None):
        """
        Initialize the demand predictor.
        
        Args:
            model_type: Type of model to use ('random_forest' or 'gradient_boosting')
            model_params: Optional dictionary of model parameters
        """
        self.model_type = model_type
        self.model = None
        self.feature_processor = None
        self.target_scaler = None
        self.feature_columns = None
        self.categorical_features = [
            'origin', 'destination', 'day_of_week', 'month', 'is_weekend',
            'is_holiday', 'cabin_class', 'airline'
        ]
        self.numerical_features = [
            'days_until_departure', 'days_since_booking', 'advance_purchase',
            'historical_avg_demand', 'historical_avg_price', 'load_factor_7d_avg',
            'price_change_7d', 'demand_change_7d', 'seasonal_factor'
        ]
        self.target_column = 'demand'
        self.model_params = model_params or {}
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the machine learning model with default or provided parameters."""
        # Set default parameters if not provided
        default_params = {
            'random_forest': {
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 5,
                'min_samples_leaf': 2,
                'random_state': 42,
                'n_jobs': -1
            },
            'gradient_boosting': {
                'n_estimators': 200,
                'learning_rate': 0.1,
                'max_depth': 5,
                'min_samples_split': 5,
                'min_samples_leaf': 2,
                'random_state': 42
            }
        }
        
        # Update default parameters with any provided parameters
        model_params = default_params.get(self.model_type, {}).copy()
        model_params.update(self.model_params)
        
        # Initialize the appropriate model
        if self.model_type == 'gradient_boosting':
            self.model = GradientBoostingRegressor(**model_params)
        else:  # Default to Random Forest
            self.model = RandomForestRegressor(**model_params)
        
        # Set up the feature processing pipeline
        self._setup_feature_processor()
    
    def _setup_feature_processor(self):
        """Set up the feature processing pipeline."""
        # Preprocessing for numerical features
        numerical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])
        
        # Preprocessing for categorical features
        categorical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])
        
        # Bundle preprocessing for numerical and categorical features
        self.feature_processor = ColumnTransformer(
            transformers=[
                ('num', numerical_transformer, self.numerical_features),
                ('cat', categorical_transformer, self.categorical_features)
            ])
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features from raw data for model training or prediction.
        
        Args:
            data: Raw flight data as a pandas DataFrame
            
        Returns:
            DataFrame with engineered features
        """
        df = data.copy()
        
        # Ensure required columns exist
        if 'departure_time' not in df.columns:
            raise ValueError("Missing required column: departure_time")
            
        # Convert departure_time to datetime if it's not already
        if not pd.api.types.is_datetime64_any_dtype(df['departure_time']):
            df['departure_time'] = pd.to_datetime(df['departure_time'])
        
        # Extract date-related features
        df['day_of_week'] = df['departure_time'].dt.dayofweek
        df['month'] = df['departure_time'].dt.month
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Days until departure
        current_date = datetime.now()
        df['days_until_departure'] = (df['departure_time'] - current_date).dt.days
        
        # Days since booking (if booking_date is available)
        if 'booking_date' in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df['booking_date']):
                df['booking_date'] = pd.to_datetime(df['booking_date'])
            df['days_since_booking'] = (current_date - df['booking_date']).dt.days
            df['advance_purchase'] = (df['departure_time'] - df['booking_date']).dt.days
        
        # Add seasonal factors (example: higher demand in summer and holidays)
        df['seasonal_factor'] = self._calculate_seasonal_factor(df['departure_time'])
        
        # Add holiday indicator (simplified example)
        df['is_holiday'] = self._is_holiday(df['departure_time'])
        
        # Add historical demand/price features (if historical data is available)
        if 'historical_avg_demand' not in df.columns and 'demand' in df.columns:
            # Calculate rolling averages if we have a time series
            if len(df) > 7:
                df = df.sort_values('departure_time')
                df['historical_avg_demand'] = df['demand'].shift(1).rolling(window=7, min_periods=1).mean()
                if 'price' in df.columns:
                    df['historical_avg_price'] = df['price'].shift(1).rolling(window=7, min_periods=1).mean()
        
        # Add price and demand change features
        if 'price' in df.columns and 'historical_avg_price' in df.columns:
            df['price_change_7d'] = (df['price'] - df['historical_avg_price']) / df['historical_avg_price']
        
        if 'demand' in df.columns and 'historical_avg_demand' in df.columns:
            df['demand_change_7d'] = (df['demand'] - df['historical_avg_demand']) / df['historical_avg_demand']
        
        # Ensure all required columns exist (fill with defaults if not)
        for col in self.categorical_features + self.numerical_features:
            if col not in df.columns:
                if col in self.categorical_features:
                    df[col] = 'unknown'
                else:
                    df[col] = 0
        
        return df
    
    def _calculate_seasonal_factor(self, dates: pd.Series) -> np.ndarray:
        """Calculate seasonal factors based on date."""
        # This is a simplified example - in practice, you'd want to use historical data
        # to calculate more accurate seasonal factors
        months = dates.dt.month
        seasonal_factors = np.ones_like(months, dtype=float)
        
        # Higher demand in summer (June-August in Northern Hemisphere)
        summer_months = [6, 7, 8]
        seasonal_factors[months.isin(summer_months)] = 1.3
        
        # Higher demand around holidays
        holiday_months = [12]  # December holidays
        holiday_days = [
            (12, 25),  # Christmas
            (1, 1),    # New Year
            (7, 4),    # July 4th (US)
            (11, 27),  # Thanksgiving (US, simplified)
        ]
        
        for month, day in holiday_days:
            mask = (dates.dt.month == month) & (dates.dt.day == day)
            seasonal_factors[mask] = 1.5
        
        # Lower demand in off-peak months
        off_peak_months = [1, 2, 9]
        seasonal_factors[months.isin(off_peak_months)] = 0.8
        
        return seasonal_factors
    
    def _is_holiday(self, dates: pd.Series) -> np.ndarray:
        """Determine if dates are holidays (simplified)."""
        # In a real application, you'd want to use a proper holiday calendar
        holidays = {
            (1, 1),   # New Year's Day
            (7, 4),   # Independence Day (US)
            (12, 25), # Christmas
            (12, 31), # New Year's Eve
        }
        
        return dates.dt.month.astype(str) + '-' + dates.dt.day.astype(str)\
            .isin([f"{m}-{d}" for m, d in holidays]).astype(int)
    
    def train(self, X: pd.DataFrame, y: Optional[pd.Series] = None, 
              validation_split: float = 0.2, random_state: int = 42) -> Dict:
        """
        Train the demand prediction model.
        
        Args:
            X: Feature DataFrame
            y: Target values (if None, 'demand' column will be used from X)
            validation_split: Fraction of data to use for validation
            random_state: Random seed for reproducibility
            
        Returns:
            Dictionary with training metrics
        """
        # Prepare the data
        if y is None and 'demand' in X.columns:
            y = X['demand']
            X = X.drop(columns=['demand'])
        
        # Prepare features
        X_processed = self.prepare_features(X)
        
        # Split into training and validation sets
        if validation_split > 0:
            X_train, X_val, y_train, y_val = train_test_split(
                X_processed, y, test_size=validation_split, 
                random_state=random_state, shuffle=False
            )
        else:
            X_train, y_train = X_processed, y
            X_val, y_val = None, None
        
        # Create pipeline with feature processing and model
        pipeline = Pipeline([
            ('preprocessor', self.feature_processor),
            ('model', self.model)
        ])
        
        # Train the model
        pipeline.fit(X_train, y_train)
        
        # Evaluate on training and validation sets
        metrics = {}
        y_train_pred = pipeline.predict(X_train)
        metrics['train'] = self._calculate_metrics(y_train, y_train_pred)
        
        if X_val is not None and y_val is not None:
            y_val_pred = pipeline.predict(X_val)
            metrics['validation'] = self._calculate_metrics(y_val, y_val_pred)
        
        # Update the model and feature processor
        self.model = pipeline.named_steps['model']
        self.feature_processor = pipeline.named_steps['preprocessor']
        
        return metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make demand predictions for new data.
        
        Args:
            X: Feature DataFrame
            
        Returns:
            Array of predicted demand values
        """
        if self.model is None or self.feature_processor is None:
            raise ValueError("Model has not been trained yet")
        
        # Prepare features
        X_processed = self.prepare_features(X)
        
        # Create pipeline for prediction
        pipeline = Pipeline([
            ('preprocessor', self.feature_processor),
            ('model', self.model)
        ])
        
        # Make predictions
        return pipeline.predict(X_processed)
    
    def _calculate_metrics(self, y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate regression metrics."""
        return {
            'mae': mean_absolute_error(y_true, y_pred),
            'mse': mean_squared_error(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'r2': r2_score(y_true, y_pred)
        }
    
    def save(self, filepath: str):
        """Save the trained model to disk."""
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save the model and feature processor
        model_data = {
            'model_type': self.model_type,
            'model': self.model,
            'feature_processor': self.feature_processor,
            'categorical_features': self.categorical_features,
            'numerical_features': self.numerical_features,
            'target_column': self.target_column,
            'model_params': self.model_params
        }
        
        joblib.dump(model_data, filepath)
    
    @classmethod
    def load(cls, filepath: str) -> 'DemandPredictor':
        """Load a trained model from disk."""
        model_data = joblib.load(filepath)
        
        # Create a new predictor instance
        predictor = cls(
            model_type=model_data['model_type'],
            model_params=model_data.get('model_params', {})
        )
        
        # Restore the model state
        predictor.model = model_data['model']
        predictor.feature_processor = model_data['feature_processor']
        predictor.categorical_features = model_data['categorical_features']
        predictor.numerical_features = model_data['numerical_features']
        predictor.target_column = model_data['target_column']
        
        return predictor


def train_demand_model(historical_data: pd.DataFrame,
                      model_type: str = 'random_forest',
                      validation_split: float = 0.2,
                      output_path: Optional[str] = None) -> DemandPredictor:
    """
    Train a demand prediction model on historical flight data.
    
    Args:
        historical_data: DataFrame containing historical flight data
        model_type: Type of model to train ('random_forest' or 'gradient_boosting')
        validation_split: Fraction of data to use for validation
        output_path: If provided, save the trained model to this path
        
    Returns:
        Trained DemandPredictor instance
    """
    # Initialize the predictor
    predictor = DemandPredictor(model_type=model_type)
    
    # Train the model
    metrics = predictor.train(historical_data, validation_split=validation_split)
    
    # Log metrics
    logger.info(f"Training metrics: {metrics.get('train', {})}")
    if 'validation' in metrics:
        logger.info(f"Validation metrics: {metrics['validation']}")
    
    # Save the model if output path is provided
    if output_path:
        predictor.save(output_path)
        logger.info(f"Model saved to {output_path}")
    
    return predictor


def predict_demand(model: Union[DemandPredictor, str], 
                  flight_data: pd.DataFrame) -> pd.Series:
    """
    Make demand predictions for flight data using a trained model.
    
    Args:
        model: Either a trained DemandPredictor instance or a path to a saved model
        flight_data: DataFrame containing flight data for prediction
        
    Returns:
        Series of predicted demand values
    """
    # Load the model if a path is provided
    if isinstance(model, str):
        model = DemandPredictor.load(model)
    
    # Make predictions
    predictions = model.predict(flight_data)
    
    return pd.Series(predictions, index=flight_data.index, name='predicted_demand')
