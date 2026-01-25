"""
Admin API Endpoints (Regional Admin + Super Admin)
"""
from datetime import datetime
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.models import (
    User, UserRole, Region, Category, Vendor, Booking, BookingStatus,
    Complaint, ComplaintStatus, ComplaintEscalationLog
)
from app.schemas.schemas import (
    UserCreate, UserResponse, RegionCreate, RegionResponse,
    CategoryCreate, CategoryResponse, VendorResponse,
    ComplaintResponse, VendorRevenueResponse, RegionTrafficResponse
)
from app.api.deps import (
    get_current_active_user, require_regional_admin, 
    require_super_admin, require_any_admin
)

router = APIRouter()


# ==================== REGIONAL ADMIN ====================

@router.get("/vendors", response_model=List[VendorResponse])
def get_vendors_for_approval(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_admin)
) -> Any:
    """Get vendors for the admin's region"""
    if current_user.role == UserRole.SUPER_ADMIN:
        vendors = db.query(Vendor).all()
    else:
        # Regional admin - get vendors in their region
        region = db.query(Region).filter(Region.admin_id == current_user.id).first()
        if not region:
            return []
        vendors = db.query(Vendor).filter(Vendor.region_id == region.id).all()
    
    return vendors


@router.put("/vendors/{vendor_id}/approve")
def approve_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_admin)
) -> Any:
    """Approve a vendor"""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    # Check region access for regional admin
    if current_user.role == UserRole.REGIONAL_ADMIN:
        region = db.query(Region).filter(Region.admin_id == current_user.id).first()
        if not region or vendor.region_id != region.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    vendor.is_approved = True
    vendor.is_visible = True
    vendor.approved_by = current_user.id
    vendor.approved_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Vendor approved"}


@router.put("/vendors/{vendor_id}/reject")
def reject_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_admin)
) -> Any:
    """Reject a vendor"""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    vendor.is_approved = False
    vendor.is_visible = False
    db.commit()
    
    return {"message": "Vendor rejected"}


@router.put("/vendors/{vendor_id}/visibility")
def toggle_vendor_visibility(
    vendor_id: int,
    visible: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_admin)
) -> Any:
    """Toggle vendor visibility to customers"""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    vendor.is_visible = visible
    db.commit()
    
    return {"message": f"Vendor visibility set to {visible}"}


@router.get("/revenue/vendors", response_model=List[VendorRevenueResponse])
def get_vendor_revenue(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_admin)
) -> Any:
    """Get revenue per vendor"""
    if current_user.role == UserRole.SUPER_ADMIN:
        vendors = db.query(Vendor).all()
    else:
        region = db.query(Region).filter(Region.admin_id == current_user.id).first()
        if not region:
            return []
        vendors = db.query(Vendor).filter(Vendor.region_id == region.id).all()
    
    result = []
    completed_statuses = [BookingStatus.COMPLETED, BookingStatus.PAYMENT_UPLOADED]
    
    for vendor in vendors:
        service_ids = [s.id for s in vendor.services]
        stats = db.query(
            func.count(Booking.id),
            func.coalesce(func.sum(Booking.total_cost), 0)
        ).filter(
            Booking.service_id.in_(service_ids) if service_ids else False,
            Booking.status.in_(completed_statuses)
        ).first()
        
        result.append({
            "vendor_id": vendor.id,
            "vendor_name": vendor.business_name,
            "total_orders": stats[0] or 0,
            "total_revenue": float(stats[1] or 0)
        })
    
    return result


@router.get("/complaints", response_model=List[ComplaintResponse])
def get_escalated_complaints(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_admin)
) -> Any:
    """Get complaints escalated to admin level"""
    if current_user.role == UserRole.SUPER_ADMIN:
        level = 3
    else:
        level = 2  # Regional admin
    
    complaints = db.query(Complaint).filter(
        Complaint.escalation_level == level
    ).all()
    
    return complaints


@router.put("/complaints/{complaint_id}/resolve")
def resolve_complaint_admin(
    complaint_id: int,
    resolution_notes: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_admin)
) -> Any:
    """Resolve complaint at admin level"""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    complaint.status = ComplaintStatus.RESOLVED_PENDING_CUSTOMER
    complaint.resolution_notes = resolution_notes
    complaint.resolved_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Complaint resolved"}


# ==================== SUPER ADMIN ONLY ====================

@router.get("/regions", response_model=List[RegionResponse])
def get_regions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
) -> Any:
    """Get all regions"""
    return db.query(Region).all()


@router.post("/regions", response_model=RegionResponse)
def create_region(
    region_in: RegionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
) -> Any:
    """Create a new region"""
    region = Region(**region_in.model_dump())
    db.add(region)
    db.commit()
    db.refresh(region)
    return region


@router.get("/categories", response_model=List[CategoryResponse])
def get_all_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_admin)
) -> Any:
    """Get all categories"""
    return db.query(Category).all()


@router.post("/categories", response_model=CategoryResponse)
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
) -> Any:
    """Create category (Super Admin only)"""
    category = Category(
        **category_in.model_dump(),
        created_by=current_user.id,
        is_default=False
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
) -> Any:
    """Delete category"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if category.is_default:
        raise HTTPException(status_code=400, detail="Cannot delete default category")
    
    category.is_active = False
    db.commit()
    return {"message": "Category deleted"}


@router.get("/admins", response_model=List[UserResponse])
def get_admins(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
) -> Any:
    """Get all regional admins"""
    return db.query(User).filter(User.role == UserRole.REGIONAL_ADMIN).all()


@router.post("/admins", response_model=UserResponse)
def create_admin(
    admin_in: UserCreate,
    region_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
) -> Any:
    """Create regional admin"""
    existing = db.query(User).filter(User.email == admin_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=admin_in.email,
        hashed_password=get_password_hash(admin_in.password),
        role=UserRole.REGIONAL_ADMIN,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Assign to region
    region = db.query(Region).filter(Region.id == region_id).first()
    if region:
        region.admin_id = user.id
        db.commit()
    
    return user


@router.delete("/admins/{admin_id}")
def delete_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
) -> Any:
    """Remove regional admin"""
    admin = db.query(User).filter(
        User.id == admin_id,
        User.role == UserRole.REGIONAL_ADMIN
    ).first()
    
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    # Remove from region
    region = db.query(Region).filter(Region.admin_id == admin_id).first()
    if region:
        region.admin_id = None
    
    admin.is_active = False
    db.commit()
    return {"message": "Admin removed"}


@router.get("/traffic/regions", response_model=List[RegionTrafficResponse])
def get_region_traffic(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
) -> Any:
    """Get customer traffic per region"""
    regions = db.query(Region).all()
    result = []
    
    for region in regions:
        vendor_count = db.query(Vendor).filter(Vendor.region_id == region.id).count()
        vendor_ids = [v.id for v in db.query(Vendor).filter(Vendor.region_id == region.id).all()]
        
        booking_count = 0
        if vendor_ids:
            from app.models.models import Service
            service_ids = [s.id for s in db.query(Service).filter(Service.vendor_id.in_(vendor_ids)).all()]
            if service_ids:
                booking_count = db.query(Booking).filter(Booking.service_id.in_(service_ids)).count()
        
        result.append({
            "region_id": region.id,
            "region_name": region.name,
            "total_customers": 0,  # Would need to track customer locations
            "total_vendors": vendor_count,
            "total_bookings": booking_count
        })
    
    return result
