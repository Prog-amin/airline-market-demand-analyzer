"""
Base database models and mixins.

This module contains the base model class and common mixins that are used across all models.
"""
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, Integer, event
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Session

class TimestampMixin:
    """Mixin that adds timestamp fields to models."""
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        nullable=False
    )

class SoftDeleteMixin:
    """Mixin that adds soft delete functionality to models."""
    
    is_deleted = Column(
        Boolean, 
        default=False,
        nullable=False,
        index=True
    )
    
    deleted_at = Column(DateTime, nullable=True)
    
    def delete(self, commit: bool = True):
        """
        Soft delete the model instance.
        
        Args:
            commit: Whether to commit the transaction
        """
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        
        if commit and hasattr(self, 'session'):
            self.session.commit()
    
    def restore(self, commit: bool = True):
        """
        Restore a soft-deleted model instance.
        
        Args:
            commit: Whether to commit the transaction
        """
        self.is_deleted = False
        self.deleted_at = None
        
        if commit and hasattr(self, 'session'):
            self.session.commit()

@as_declarative()
class Base:
    """Base class for all SQLAlchemy models."""
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model instance to a dictionary.
        
        Returns:
            Dict[str, Any]: A dictionary representation of the model
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def update(self, **kwargs):
        """
        Update model attributes.
        
        Args:
            **kwargs: Attributes to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

# Register event listeners for models
@event.listens_for(Session, 'before_flush')
def before_flush(session: Session, context, instances):
    """Set updated_at timestamp before flush."""
    for instance in session.dirty:
        if hasattr(instance, 'updated_at'):
            instance.updated_at = datetime.utcnow()
