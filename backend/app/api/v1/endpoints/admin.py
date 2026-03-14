"""
Admin API Endpoints (Regional Admin + Super Admin)
"""
from datetime import datetime
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.sql import text

from app.core.database import get_db
from app.core.security import get_password_hash
from app.core.revenue_service import RevenueService
from app.models.models import (
    User, UserRole, Region, Category, Vendor, Booking, BookingStatus,
    Complaint, ComplaintStatus, ComplaintEscalationLog, Service
)
from app.schemas.schemas import (
    UserCreate, UserResponse, RegionCreate, RegionResponse,
    CategoryCreate, CategoryResponse, VendorResponse,
    ComplaintResponse, VendorRevenueResponse, RegionTrafficResponse,
    PlatformRevenueResponse, RegionRevenueListResponse, 
    RegionalRevenueResponse, TransactionDetailResponse,
    AdminWithRegionResponse
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


@router.delete("/vendors/{vendor_id}")
def delete_vendor_admin(
    vendor_id: int,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
) -> Any:
    """Delete vendor (Super Admin only)
    
    Args:
        vendor_id: ID of the vendor to delete
        force: If True, deletes vendor and all related data (services, bookings, workers)
    """
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    # Count related data using raw SQL
    service_count = db.execute(
        text("SELECT COUNT(*) FROM services WHERE vendor_id = :vendor_id"),
        {"vendor_id": vendor_id}
    ).scalar()
    
    worker_count = db.execute(
        text("SELECT COUNT(*) FROM workers WHERE vendor_id = :vendor_id"),
        {"vendor_id": vendor_id}
    ).scalar()
    
    booking_count = db.execute(
        text("SELECT COUNT(*) FROM bookings WHERE service_id IN (SELECT id FROM services WHERE vendor_id = :vendor_id)"),
        {"vendor_id": vendor_id}
    ).scalar()
    
    if (service_count > 0 or worker_count > 0 or booking_count > 0) and not force:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete vendor with {service_count} service(s), {worker_count} worker(s), and {booking_count} booking(s). Use force=true to delete all related data."
        )
    
    # If force is true, delete all related data using raw SQL
    if force:
        # Delete related records in correct order (children first)
        db.execute(text("DELETE FROM booking_status_history WHERE booking_id IN (SELECT b.id FROM bookings b JOIN services s ON b.service_id = s.id WHERE s.vendor_id = :vendor_id)"), {"vendor_id": vendor_id})
        db.execute(text("DELETE FROM reviews WHERE booking_id IN (SELECT b.id FROM bookings b JOIN services s ON b.service_id = s.id WHERE s.vendor_id = :vendor_id)"), {"vendor_id": vendor_id})
        db.execute(text("DELETE FROM complaints WHERE booking_id IN (SELECT b.id FROM bookings b JOIN services s ON b.service_id = s.id WHERE s.vendor_id = :vendor_id)"), {"vendor_id": vendor_id})
        db.execute(text("DELETE FROM transactions WHERE booking_id IN (SELECT b.id FROM bookings b JOIN services s ON b.service_id = s.id WHERE s.vendor_id = :vendor_id)"), {"vendor_id": vendor_id})
        db.execute(text("DELETE FROM bookings WHERE service_id IN (SELECT id FROM services WHERE vendor_id = :vendor_id)"), {"vendor_id": vendor_id})
        db.execute(text("DELETE FROM services WHERE vendor_id = :vendor_id"), {"vendor_id": vendor_id})
        
        # Deactivate worker user accounts and delete worker records
        db.execute(text("UPDATE users SET is_active = 0 WHERE id IN (SELECT user_id FROM workers WHERE vendor_id = :vendor_id)"), {"vendor_id": vendor_id})
        db.execute(text("DELETE FROM workers WHERE vendor_id = :vendor_id"), {"vendor_id": vendor_id})
        
        db.commit()
    
    # Deactivate vendor user account
    if vendor.user_id:
        vendor_user = db.query(User).filter(User.id == vendor.user_id).first()
        if vendor_user:
            vendor_user.is_active = False
    
    # Delete the vendor
    db.delete(vendor)
    db.commit()
    
    return {"message": f"Vendor deleted successfully{f' ({service_count} service(s), {worker_count} worker(s), {booking_count} booking(s) deleted)' if force and (service_count > 0 or worker_count > 0 or booking_count > 0) else ''}"}


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


@router.get("/revenue/platform", response_model=PlatformRevenueResponse)
def get_platform_revenue(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
) -> Any:
    """Get total platform revenue (Super Admin only)"""
    total_revenue = RevenueService.get_platform_revenue(db)
    return {"total_revenue": total_revenue}


@router.get("/revenue/regions", response_model=List[RegionRevenueListResponse])
def get_regions_revenue(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
) -> Any:
    """Get revenue for all regions (Super Admin only)"""
    regions_revenue = RevenueService.get_revenue_by_regions(db)
    return [
        {
            "region_id": region.region_id,
            "region_name": region.region_name,
            "revenue": region.revenue
        }
        for region in regions_revenue
    ]


@router.get("/revenue/region/{region_id}", response_model=RegionalRevenueResponse)
def get_region_revenue(
    region_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_admin)
) -> Any:
    """Get revenue for a specific region (Regional Admin for own region or Super Admin)"""
    # Check authorization
    if current_user.role == UserRole.REGIONAL_ADMIN:
        # Regional admin can only access their own region
        admin_region = db.query(Region).filter(Region.admin_id == current_user.id).first()
        if not admin_region or admin_region.id != region_id:
            raise HTTPException(
                status_code=403, 
                detail="Access denied. You can only view revenue for your assigned region."
            )
    
    # Verify region exists
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    
    revenue = RevenueService.get_regional_revenue(db, region_id)
    return {"region_id": region_id, "revenue": revenue}


@router.get("/vendors/{vendor_id}/transactions", response_model=List[TransactionDetailResponse])
def get_vendor_transactions(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_admin)
) -> Any:
    """Get complete transaction history for a vendor (Regional Admin or Super Admin)"""
    # Verify vendor exists
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    # Check authorization for regional admin
    if current_user.role == UserRole.REGIONAL_ADMIN:
        admin_region = db.query(Region).filter(Region.admin_id == current_user.id).first()
        if not admin_region or vendor.region_id != admin_region.id:
            raise HTTPException(
                status_code=403,
                detail="Access denied. You can only view transactions for vendors in your region."
            )
    
    transactions = RevenueService.get_vendor_transactions(db, vendor_id)
    return [
        {
            "transaction_id": txn.transaction_id,
            "amount": txn.amount,
            "datetime": txn.datetime,
            "screenshot_url": txn.screenshot_url
        }
        for txn in transactions
    ]


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


@router.put("/regions/{region_id}", response_model=RegionResponse)
def update_region(
    region_id: int,
    region_in: RegionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
) -> Any:
    """Update a region"""
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    
    # Update fields
    region.name = region_in.name
    if region_in.state is not None:
        region.state = region_in.state
    if region_in.description is not None:
        region.description = region_in.description
    
    db.commit()
    db.refresh(region)
    return region


@router.delete("/regions/{region_id}")
def delete_region(
    region_id: int,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
) -> Any:
    """Delete a region (Super Admin only)
    
    Args:
        region_id: ID of the region to delete
        force: If True, deletes region and reassigns/removes all vendors and admins
    """
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")

    # Check if region has an assigned admin
    admin_count = 1 if region.admin_id else 0
    
    # Check if region has any vendors
    vendor_count = db.query(Vendor).filter(Vendor.region_id == region_id).count()
    
    if (admin_count > 0 or vendor_count > 0) and not force:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete region with {admin_count} admin(s) and {vendor_count} vendor(s). Use force=true to remove all associations and delete."
        )

    # If force is true, handle related data
    if force:
        # Remove admin assignment
        if region.admin_id:
            admin_user = db.query(User).filter(User.id == region.admin_id).first()
            if admin_user:
                admin_user.is_active = False  # Deactivate the admin
            region.admin_id = None
            db.commit()
        
        # Delete all vendors in this region (and their related data)
        if vendor_count > 0:
            vendors = db.query(Vendor).filter(Vendor.region_id == region_id).all()
            for vendor in vendors:
                # Delete vendor's services and related data using raw SQL
                db.execute(text("DELETE FROM booking_status_history WHERE booking_id IN (SELECT b.id FROM bookings b JOIN services s ON b.service_id = s.id WHERE s.vendor_id = :vendor_id)"), {"vendor_id": vendor.id})
                db.execute(text("DELETE FROM reviews WHERE booking_id IN (SELECT b.id FROM bookings b JOIN services s ON b.service_id = s.id WHERE s.vendor_id = :vendor_id)"), {"vendor_id": vendor.id})
                db.execute(text("DELETE FROM complaints WHERE booking_id IN (SELECT b.id FROM bookings b JOIN services s ON b.service_id = s.id WHERE s.vendor_id = :vendor_id)"), {"vendor_id": vendor.id})
                db.execute(text("DELETE FROM transactions WHERE booking_id IN (SELECT b.id FROM bookings b JOIN services s ON b.service_id = s.id WHERE s.vendor_id = :vendor_id)"), {"vendor_id": vendor.id})
                db.execute(text("DELETE FROM bookings WHERE service_id IN (SELECT id FROM services WHERE vendor_id = :vendor_id)"), {"vendor_id": vendor.id})
                db.execute(text("DELETE FROM services WHERE vendor_id = :vendor_id"), {"vendor_id": vendor.id})
                db.execute(text("DELETE FROM workers WHERE vendor_id = :vendor_id"), {"vendor_id": vendor.id})
                db.delete(vendor)
            db.commit()

    # Delete the region
    db.delete(region)
    db.commit()
    
    return {"message": f"Region deleted successfully{f' ({admin_count} admin(s) deactivated, {vendor_count} vendor(s) deleted)' if force and (admin_count > 0 or vendor_count > 0) else ''}"}


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


@router.delete("/services/{service_id}")
def delete_service_admin(
    service_id: int,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
) -> Any:
    """Delete service (Super Admin only)
    
    Args:
        service_id: ID of the service to delete
        force: If True, deletes service and all its bookings using raw SQL (bypasses ORM relationships)
    """
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Count bookings using raw SQL to avoid loading relationships
    booking_count = db.execute(
        text("SELECT COUNT(*) FROM bookings WHERE service_id = :service_id"),
        {"service_id": service_id}
    ).scalar()
    
    active_booking_count = db.execute(
        text("SELECT COUNT(*) FROM bookings WHERE service_id = :service_id AND status NOT IN ('COMPLETED', 'PAYMENT_UPLOADED', 'CANCELLED')"),
        {"service_id": service_id}
    ).scalar()
    
    if booking_count > 0 and not force:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete service with {booking_count} bookings ({active_booking_count} active). Use force=true to delete all bookings and the service."
        )
    
    # If force is true, delete all related data using raw SQL
    if force and booking_count > 0:
        # Delete related records in correct order (children first)
        db.execute(text("DELETE FROM booking_status_history WHERE booking_id IN (SELECT id FROM bookings WHERE service_id = :service_id)"), {"service_id": service_id})
        db.execute(text("DELETE FROM reviews WHERE booking_id IN (SELECT id FROM bookings WHERE service_id = :service_id)"), {"service_id": service_id})
        db.execute(text("DELETE FROM complaints WHERE booking_id IN (SELECT id FROM bookings WHERE service_id = :service_id)"), {"service_id": service_id})
        db.execute(text("DELETE FROM transactions WHERE booking_id IN (SELECT id FROM bookings WHERE service_id = :service_id)"), {"service_id": service_id})
        db.execute(text("DELETE FROM bookings WHERE service_id = :service_id"), {"service_id": service_id})
        db.commit()
    
    # Delete the service
    db.delete(service)
    db.commit()
    
    return {"message": f"Service deleted successfully{f' ({booking_count} bookings deleted, {active_booking_count} were active)' if force and booking_count > 0 else ''}"}


@router.get("/admins", response_model=List[UserResponse])
@router.get("/admins", response_model=List[AdminWithRegionResponse])
def get_admins(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
) -> Any:
    """Get all regional admins with their assigned regions"""
    admins = db.query(User).filter(User.role == UserRole.REGIONAL_ADMIN).all()
    
    # Build response with region information
    result = []
    for admin in admins:
        # Find the region assigned to this admin
        region = db.query(Region).filter(Region.admin_id == admin.id).first()
        
        admin_dict = {
            "id": admin.id,
            "email": admin.email,
            "full_name": admin.full_name,
            "role": admin.role,
            "is_active": admin.is_active,
            "created_at": admin.created_at,
            "region": {
                "id": region.id,
                "name": region.name,
                "state": region.state,
                "description": region.description,
                "is_active": region.is_active
            } if region else None
        }
        result.append(admin_dict)
    
    return result


@router.post("/admins", response_model=UserResponse)
def create_admin(
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
) -> Any:
    """Create regional admin"""
    # Extract data from request
    admin_data = request.get('admin_in', {})
    region_id = request.get('region_id')
    
    if not admin_data.get('email') or not admin_data.get('password'):
        raise HTTPException(status_code=400, detail="Email and password are required")
    
    if not region_id:
        raise HTTPException(status_code=400, detail="Region ID is required")
    
    # Prevent creation of Super Admin via this endpoint
    # Only one Super Admin should exist in the system
    if admin_data.get('role') == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=400, 
            detail="Cannot create Super Admin through this endpoint. Only one Super Admin is allowed in the system."
        )
    
    # Check if email already exists
    existing = db.query(User).filter(User.email == admin_data['email']).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Check if region exists
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    
    # Check if region already has an admin
    if region.admin_id:
        raise HTTPException(status_code=400, detail="Region already has an admin assigned")
    
    # Create user (force role to REGIONAL_ADMIN)
    user = User(
        email=admin_data['email'],
        hashed_password=get_password_hash(admin_data['password']),
        role=UserRole.REGIONAL_ADMIN,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Assign to region
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
