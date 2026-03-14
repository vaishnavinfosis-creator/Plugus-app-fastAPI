"""
Revenue Service
Handles revenue calculation and aggregation for platform and regional dashboards
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import Transaction, Booking, Service, Vendor, Region


class RegionRevenue:
    """Data class for region revenue information"""
    def __init__(self, region_id: int, region_name: str, revenue: float):
        self.region_id = region_id
        self.region_name = region_name
        self.revenue = revenue


class TransactionDetail:
    """Data class for transaction details"""
    def __init__(self, transaction_id: int, amount: float, datetime: str, screenshot_url: Optional[str]):
        self.transaction_id = transaction_id
        self.amount = amount
        self.datetime = datetime
        self.screenshot_url = screenshot_url


class RevenueService:
    """Service for calculating and aggregating revenue data"""
    
    @staticmethod
    def get_platform_revenue(db: Session) -> float:
        """
        Calculate total platform revenue from all transactions
        
        Args:
            db: Database session
            
        Returns:
            Total revenue across all regions in INR
        """
        total = db.query(func.sum(Transaction.amount)).scalar()
        return float(total) if total else 0.0
    
    @staticmethod
    def get_regional_revenue(db: Session, region_id: int) -> float:
        """
        Calculate total revenue for a specific region
        
        Args:
            db: Database session
            region_id: ID of the region
            
        Returns:
            Total revenue for the specified region in INR
        """
        total = db.query(func.sum(Transaction.amount)).join(
            Booking, Transaction.booking_id == Booking.id
        ).join(
            Service, Booking.service_id == Service.id
        ).join(
            Vendor, Service.vendor_id == Vendor.id
        ).filter(
            Vendor.region_id == region_id
        ).scalar()
        
        return float(total) if total else 0.0
    
    @staticmethod
    def get_revenue_by_regions(db: Session) -> List[RegionRevenue]:
        """
        Get revenue grouped by region for all regions
        
        Args:
            db: Database session
            
        Returns:
            List of RegionRevenue objects with region details and revenue
        """
        # Query to get revenue per region
        results = db.query(
            Region.id,
            Region.name,
            func.coalesce(func.sum(Transaction.amount), 0).label('revenue')
        ).outerjoin(
            Vendor, Region.id == Vendor.region_id
        ).outerjoin(
            Service, Vendor.id == Service.vendor_id
        ).outerjoin(
            Booking, Service.id == Booking.service_id
        ).outerjoin(
            Transaction, Booking.id == Transaction.booking_id
        ).group_by(
            Region.id, Region.name
        ).all()
        
        return [
            RegionRevenue(
                region_id=row.id,
                region_name=row.name,
                revenue=float(row.revenue)
            )
            for row in results
        ]
    
    @staticmethod
    def get_vendor_transactions(db: Session, vendor_id: int) -> List[TransactionDetail]:
        """
        Get complete transaction history for a specific vendor
        
        Args:
            db: Database session
            vendor_id: ID of the vendor
            
        Returns:
            List of TransactionDetail objects ordered by datetime (most recent first)
        """
        results = db.query(
            Transaction.id,
            Transaction.amount,
            Transaction.created_at,
            Transaction.screenshot_url
        ).join(
            Booking, Transaction.booking_id == Booking.id
        ).join(
            Service, Booking.service_id == Service.id
        ).filter(
            Service.vendor_id == vendor_id
        ).order_by(
            Transaction.created_at.desc()
        ).all()
        
        return [
            TransactionDetail(
                transaction_id=row.id,
                amount=float(row.amount),
                datetime=row.created_at.isoformat(),
                screenshot_url=row.screenshot_url
            )
            for row in results
        ]
