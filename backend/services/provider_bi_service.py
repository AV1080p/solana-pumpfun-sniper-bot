"""
Provider Business Intelligence Service
Handles real-time analytics, customer insights, revenue tracking, and marketing tools for service providers
"""
import logging
import json
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, case
from collections import defaultdict

from models import (
    ServiceProvider, Tour, Booking, Payment, Review, MarketingCampaign,
    CustomerBehavior, ProviderAnalytics, User
)

logger = logging.getLogger(__name__)


class ProviderBIService:
    """Service for provider business intelligence and analytics"""
    
    # ========== REAL-TIME BOOKING ANALYTICS ==========
    
    async def get_booking_analytics(
        self,
        provider_id: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        db: Session
    ) -> Dict[str, Any]:
        """Get real-time booking analytics"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get provider's tours
            tours = db.query(Tour).filter(Tour.provider_id == provider_id).all()
            tour_ids = [t.id for t in tours]
            
            if not tour_ids:
                return self._empty_analytics()
            
            # Total bookings
            total_bookings = db.query(func.count(Booking.id)).filter(
                and_(
                    Booking.tour_id.in_(tour_ids),
                    Booking.created_at >= start_date,
                    Booking.created_at <= end_date
                )
            ).scalar()
            
            # Bookings by status
            bookings_by_status = {}
            for status in ["pending", "confirmed", "cancelled", "completed"]:
                count = db.query(func.count(Booking.id)).filter(
                    and_(
                        Booking.tour_id.in_(tour_ids),
                        Booking.status == status,
                        Booking.created_at >= start_date,
                        Booking.created_at <= end_date
                    )
                ).scalar()
                bookings_by_status[status] = count
            
            # Bookings by day
            bookings_by_day = defaultdict(int)
            bookings = db.query(Booking).filter(
                and_(
                    Booking.tour_id.in_(tour_ids),
                    Booking.created_at >= start_date,
                    Booking.created_at <= end_date
                )
            ).all()
            
            for booking in bookings:
                day_key = booking.created_at.strftime("%Y-%m-%d")
                bookings_by_day[day_key] += 1
            
            # Top tours by bookings
            top_tours = db.query(
                Booking.tour_id,
                func.count(Booking.id).label('count')
            ).filter(
                and_(
                    Booking.tour_id.in_(tour_ids),
                    Booking.created_at >= start_date,
                    Booking.created_at <= end_date
                )
            ).group_by(Booking.tour_id).order_by(desc('count')).limit(5).all()
            
            top_tours_list = []
            for tour_id, count in top_tours:
                tour = db.query(Tour).filter(Tour.id == tour_id).first()
                if tour:
                    top_tours_list.append({
                        "tour_id": tour.id,
                        "tour_name": tour.name,
                        "bookings_count": count
                    })
            
            return {
                "success": True,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_bookings": total_bookings,
                "bookings_by_status": bookings_by_status,
                "bookings_by_day": dict(bookings_by_day),
                "top_tours": top_tours_list
            }
        except Exception as e:
            logger.error(f"Error getting booking analytics: {e}")
            return {"success": False, "error": str(e)}
    
    # ========== CUSTOMER BEHAVIOR INSIGHTS ==========
    
    async def get_customer_insights(
        self,
        provider_id: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        db: Session
    ) -> Dict[str, Any]:
        """Get customer behavior insights"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get provider's tours
            tours = db.query(Tour).filter(Tour.provider_id == provider_id).all()
            tour_ids = [t.id for t in tours]
            
            if not tour_ids:
                return self._empty_customer_insights()
            
            # Customer actions
            behaviors = db.query(CustomerBehavior).filter(
                and_(
                    CustomerBehavior.provider_id == provider_id,
                    CustomerBehavior.created_at >= start_date,
                    CustomerBehavior.created_at <= end_date
                )
            ).all()
            
            actions_by_type = defaultdict(int)
            unique_customers = set()
            conversion_funnel = {
                "views": 0,
                "add_to_cart": 0,
                "bookings": 0,
                "reviews": 0
            }
            
            for behavior in behaviors:
                actions_by_type[behavior.action_type] += 1
                if behavior.user_id:
                    unique_customers.add(behavior.user_id)
                
                if behavior.action_type == "view_tour":
                    conversion_funnel["views"] += 1
                elif behavior.action_type == "add_to_cart":
                    conversion_funnel["add_to_cart"] += 1
                elif behavior.action_type == "booking":
                    conversion_funnel["bookings"] += 1
                elif behavior.action_type == "review":
                    conversion_funnel["reviews"] += 1
            
            # Repeat customers
            bookings = db.query(Booking).filter(
                and_(
                    Booking.tour_id.in_(tour_ids),
                    Booking.created_at >= start_date,
                    Booking.created_at <= end_date
                )
            ).all()
            
            customer_booking_count = defaultdict(int)
            for booking in bookings:
                if booking.user_id:
                    customer_booking_count[booking.user_id] += 1
            
            repeat_customers = sum(1 for count in customer_booking_count.values() if count > 1)
            total_customers = len(customer_booking_count)
            repeat_rate = (repeat_customers / total_customers * 100) if total_customers > 0 else 0
            
            # Customer demographics (simplified)
            customer_locations = defaultdict(int)
            for booking in bookings:
                if booking.user_email:
                    # Extract domain for basic location insight
                    domain = booking.user_email.split('@')[-1] if '@' in booking.user_email else 'unknown'
                    customer_locations[domain] += 1
            
            return {
                "success": True,
                "unique_customers": len(unique_customers),
                "actions_by_type": dict(actions_by_type),
                "conversion_funnel": conversion_funnel,
                "repeat_customer_rate": round(repeat_rate, 2),
                "repeat_customers": repeat_customers,
                "total_customers": total_customers,
                "customer_locations": dict(customer_locations)
            }
        except Exception as e:
            logger.error(f"Error getting customer insights: {e}")
            return {"success": False, "error": str(e)}
    
    # ========== REVENUE TRACKING ==========
    
    async def get_revenue_analytics(
        self,
        provider_id: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        db: Session
    ) -> Dict[str, Any]:
        """Get revenue tracking and analytics"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get provider's tours
            tours = db.query(Tour).filter(Tour.provider_id == provider_id).all()
            tour_ids = [t.id for t in tours]
            
            if not tour_ids:
                return self._empty_revenue()
            
            # Get completed payments
            completed_payments = db.query(Payment).join(Booking).filter(
                and_(
                    Booking.tour_id.in_(tour_ids),
                    Payment.status == "completed",
                    Payment.created_at >= start_date,
                    Payment.created_at <= end_date
                )
            ).all()
            
            total_revenue = sum(p.amount for p in completed_payments)
            
            # Revenue by payment method
            revenue_by_method = defaultdict(float)
            for payment in completed_payments:
                method = payment.payment_method.value if hasattr(payment.payment_method, 'value') else str(payment.payment_method)
                revenue_by_method[method] += payment.amount
            
            # Revenue by day
            revenue_by_day = defaultdict(float)
            for payment in completed_payments:
                day_key = payment.created_at.strftime("%Y-%m-%d")
                revenue_by_day[day_key] += payment.amount
            
            # Revenue by tour
            revenue_by_tour = defaultdict(float)
            for payment in completed_payments:
                if payment.booking and payment.booking.tour_id:
                    revenue_by_tour[payment.booking.tour_id] += payment.amount
            
            revenue_by_tour_list = []
            for tour_id, revenue in sorted(revenue_by_tour.items(), key=lambda x: x[1], reverse=True)[:10]:
                tour = db.query(Tour).filter(Tour.id == tour_id).first()
                if tour:
                    revenue_by_tour_list.append({
                        "tour_id": tour.id,
                        "tour_name": tour.name,
                        "revenue": revenue
                    })
            
            # Calculate commission (if applicable)
            provider = db.query(ServiceProvider).filter(ServiceProvider.id == provider_id).first()
            commission_rate = provider.commission_rate if provider else 0.0
            platform_commission = total_revenue * (commission_rate / 100)
            net_revenue = total_revenue - platform_commission
            
            return {
                "success": True,
                "total_revenue": total_revenue,
                "net_revenue": net_revenue,
                "platform_commission": platform_commission,
                "commission_rate": commission_rate,
                "revenue_by_method": dict(revenue_by_method),
                "revenue_by_day": dict(revenue_by_day),
                "revenue_by_tour": revenue_by_tour_list,
                "total_transactions": len(completed_payments)
            }
        except Exception as e:
            logger.error(f"Error getting revenue analytics: {e}")
            return {"success": False, "error": str(e)}
    
    # ========== PERFORMANCE METRICS ==========
    
    async def get_performance_metrics(
        self,
        provider_id: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        db: Session
    ) -> Dict[str, Any]:
        """Get performance metrics"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get provider's tours
            tours = db.query(Tour).filter(Tour.provider_id == provider_id).all()
            tour_ids = [t.id for t in tours]
            
            if not tour_ids:
                return self._empty_performance()
            
            # Reviews and ratings
            reviews = db.query(Review).filter(
                and_(
                    Review.provider_id == provider_id,
                    Review.created_at >= start_date,
                    Review.created_at <= end_date,
                    Review.is_published == True
                )
            ).all()
            
            total_reviews = len(reviews)
            average_rating = sum(r.rating for r in reviews) / total_reviews if total_reviews > 0 else 0
            
            rating_distribution = defaultdict(int)
            for review in reviews:
                rating_distribution[review.rating] += 1
            
            # Bookings
            bookings = db.query(Booking).filter(
                and_(
                    Booking.tour_id.in_(tour_ids),
                    Booking.created_at >= start_date,
                    Booking.created_at <= end_date
                )
            ).all()
            
            total_bookings = len(bookings)
            confirmed_bookings = sum(1 for b in bookings if b.status.value == "confirmed")
            cancelled_bookings = sum(1 for b in bookings if b.status.value == "cancelled")
            cancellation_rate = (cancelled_bookings / total_bookings * 100) if total_bookings > 0 else 0
            
            # Views and conversion
            views = db.query(CustomerBehavior).filter(
                and_(
                    CustomerBehavior.provider_id == provider_id,
                    CustomerBehavior.action_type == "view_tour",
                    CustomerBehavior.created_at >= start_date,
                    CustomerBehavior.created_at <= end_date
                )
            ).count()
            
            conversion_rate = (total_bookings / views * 100) if views > 0 else 0
            
            # Response time (for reviews)
            reviews_with_response = [r for r in reviews if r.response_at]
            response_times = []
            for review in reviews_with_response:
                if review.response_at and review.created_at:
                    response_time = (review.response_at - review.created_at).total_seconds() / 3600  # hours
                    response_times.append(response_time)
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else None
            
            return {
                "success": True,
                "total_reviews": total_reviews,
                "average_rating": round(average_rating, 2),
                "rating_distribution": dict(rating_distribution),
                "total_bookings": total_bookings,
                "confirmed_bookings": confirmed_bookings,
                "cancellation_rate": round(cancellation_rate, 2),
                "total_views": views,
                "conversion_rate": round(conversion_rate, 2),
                "average_response_time_hours": round(avg_response_time, 2) if avg_response_time else None,
                "response_rate": round((len(reviews_with_response) / total_reviews * 100) if total_reviews > 0 else 0, 2)
            }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {"success": False, "error": str(e)}
    
    # ========== REVIEW MANAGEMENT ==========
    
    async def get_reviews(
        self,
        provider_id: int,
        tour_id: Optional[int],
        rating: Optional[int],
        limit: int,
        offset: int,
        db: Session
    ) -> Dict[str, Any]:
        """Get reviews for provider"""
        try:
            query = db.query(Review).filter(Review.provider_id == provider_id)
            
            if tour_id:
                query = query.filter(Review.tour_id == tour_id)
            
            if rating:
                query = query.filter(Review.rating == rating)
            
            total = query.count()
            reviews = query.order_by(desc(Review.created_at)).offset(offset).limit(limit).all()
            
            reviews_list = []
            for review in reviews:
                review_dict = {
                    "id": review.id,
                    "tour_id": review.tour_id,
                    "user_id": review.user_id,
                    "rating": review.rating,
                    "title": review.title,
                    "comment": review.comment,
                    "photos": json.loads(review.photos) if review.photos else [],
                    "is_verified": review.is_verified,
                    "helpful_count": review.helpful_count,
                    "response": review.response,
                    "response_at": review.response_at.isoformat() if review.response_at else None,
                    "created_at": review.created_at.isoformat()
                }
                
                # Add user info
                if review.user_id:
                    user = db.query(User).filter(User.id == review.user_id).first()
                    if user:
                        review_dict["user_name"] = user.full_name or user.username
                        review_dict["user_email"] = user.email
                
                # Add tour info
                if review.tour_id:
                    tour = db.query(Tour).filter(Tour.id == review.tour_id).first()
                    if tour:
                        review_dict["tour_name"] = tour.name
                
                reviews_list.append(review_dict)
            
            return {
                "success": True,
                "reviews": reviews_list,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        except Exception as e:
            logger.error(f"Error getting reviews: {e}")
            return {"success": False, "error": str(e)}
    
    async def respond_to_review(
        self,
        review_id: int,
        provider_id: int,
        response: str,
        db: Session
    ) -> Dict[str, Any]:
        """Add response to a review"""
        try:
            review = db.query(Review).filter(
                and_(
                    Review.id == review_id,
                    Review.provider_id == provider_id
                )
            ).first()
            
            if not review:
                return {"success": False, "error": "Review not found"}
            
            review.response = response
            review.response_at = datetime.utcnow()
            db.commit()
            
            return {"success": True, "review": review}
        except Exception as e:
            logger.error(f"Error responding to review: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    # ========== MARKETING TOOLS ==========
    
    async def get_marketing_campaigns(
        self,
        provider_id: int,
        status: Optional[str],
        db: Session
    ) -> Dict[str, Any]:
        """Get marketing campaigns"""
        try:
            query = db.query(MarketingCampaign).filter(MarketingCampaign.provider_id == provider_id)
            
            if status:
                query = query.filter(MarketingCampaign.status == status)
            
            campaigns = query.order_by(desc(MarketingCampaign.created_at)).all()
            
            campaigns_list = []
            for campaign in campaigns:
                campaign_dict = {
                    "id": campaign.id,
                    "name": campaign.name,
                    "campaign_type": campaign.campaign_type,
                    "description": campaign.description,
                    "discount_percentage": campaign.discount_percentage,
                    "discount_amount": campaign.discount_amount,
                    "start_date": campaign.start_date.isoformat(),
                    "end_date": campaign.end_date.isoformat(),
                    "budget": campaign.budget,
                    "spent": campaign.spent,
                    "status": campaign.status,
                    "metrics": json.loads(campaign.metrics) if campaign.metrics else {},
                    "created_at": campaign.created_at.isoformat()
                }
                campaigns_list.append(campaign_dict)
            
            return {
                "success": True,
                "campaigns": campaigns_list
            }
        except Exception as e:
            logger.error(f"Error getting campaigns: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_marketing_campaign(
        self,
        provider_id: int,
        name: str,
        campaign_type: str,
        description: Optional[str],
        discount_percentage: Optional[float],
        discount_amount: Optional[float],
        start_date: datetime,
        end_date: datetime,
        budget: Optional[float],
        target_audience: Optional[dict],
        db: Session
    ) -> Dict[str, Any]:
        """Create a new marketing campaign"""
        try:
            campaign = MarketingCampaign(
                provider_id=provider_id,
                name=name,
                campaign_type=campaign_type,
                description=description,
                discount_percentage=discount_percentage,
                discount_amount=discount_amount,
                start_date=start_date,
                end_date=end_date,
                budget=budget,
                spent=0.0,
                status="draft",
                target_audience=json.dumps(target_audience) if target_audience else None
            )
            
            db.add(campaign)
            db.commit()
            db.refresh(campaign)
            
            return {
                "success": True,
                "campaign": campaign
            }
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    # ========== HELPER METHODS ==========
    
    def _empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure"""
        return {
            "success": True,
            "total_bookings": 0,
            "bookings_by_status": {},
            "bookings_by_day": {},
            "top_tours": []
        }
    
    def _empty_customer_insights(self) -> Dict[str, Any]:
        """Return empty customer insights structure"""
        return {
            "success": True,
            "unique_customers": 0,
            "actions_by_type": {},
            "conversion_funnel": {"views": 0, "add_to_cart": 0, "bookings": 0, "reviews": 0},
            "repeat_customer_rate": 0,
            "repeat_customers": 0,
            "total_customers": 0,
            "customer_locations": {}
        }
    
    def _empty_revenue(self) -> Dict[str, Any]:
        """Return empty revenue structure"""
        return {
            "success": True,
            "total_revenue": 0.0,
            "net_revenue": 0.0,
            "platform_commission": 0.0,
            "commission_rate": 0.0,
            "revenue_by_method": {},
            "revenue_by_day": {},
            "revenue_by_tour": [],
            "total_transactions": 0
        }
    
    def _empty_performance(self) -> Dict[str, Any]:
        """Return empty performance structure"""
        return {
            "success": True,
            "total_reviews": 0,
            "average_rating": 0.0,
            "rating_distribution": {},
            "total_bookings": 0,
            "confirmed_bookings": 0,
            "cancellation_rate": 0.0,
            "total_views": 0,
            "conversion_rate": 0.0,
            "average_response_time_hours": None,
            "response_rate": 0.0
        }

