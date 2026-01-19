from database import SessionLocal
from models import Tour
from datetime import datetime

def seed_tours():
    db = SessionLocal()
    try:
        # Check if tours already exist
        if db.query(Tour).count() > 0:
            print("Tours already seeded")
            return

        tours = [
            Tour(
                name="Tropical Paradise Beach Tour",
                description="Experience the pristine beaches and crystal-clear waters of our tropical paradise. Includes snorkeling, beach activities, and a delicious lunch.",
                price=299.99,
                price_sol=0.15,
                duration="Full Day (8 hours)",
                location="Maldives",
                image_url="https://images.unsplash.com/photo-1507525421304-677d4f1a0cfe?w=800&h=600&fit=crop&q=80"
            ),
            Tour(
                name="Mountain Adventure Expedition",
                description="Conquer the peaks with our guided mountain expedition. Perfect for adventure enthusiasts looking for a challenge.",
                price=499.99,
                price_sol=0.25,
                duration="2 Days",
                location="Swiss Alps",
                image_url="https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=800&h=600&fit=crop&q=80"
            ),
            Tour(
                name="Cultural Heritage Walk",
                description="Explore ancient temples, historical sites, and local markets. Immerse yourself in the rich culture and traditions.",
                price=149.99,
                price_sol=0.075,
                duration="Half Day (4 hours)",
                location="Kyoto, Japan",
                image_url="https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop&q=80"
            ),
            Tour(
                name="Safari Wildlife Experience",
                description="Get up close with wildlife in their natural habitat. Professional guides and comfortable vehicles included.",
                price=399.99,
                price_sol=0.20,
                duration="Full Day (10 hours)",
                location="Serengeti, Tanzania",
                image_url="https://images.unsplash.com/photo-1518546305927-5a555bb7020d?w=800&h=600&fit=crop&q=80"
            ),
            Tour(
                name="City Lights Night Tour",
                description="Discover the vibrant nightlife and illuminated landmarks of the city. Includes dinner at a rooftop restaurant.",
                price=199.99,
                price_sol=0.10,
                duration="Evening (5 hours)",
                location="New York City",
                image_url="https://images.unsplash.com/photo-1501594907352-04c32438d422?w=800&h=600&fit=crop&q=80"
            ),
            Tour(
                name="Island Hopping Adventure",
                description="Visit multiple islands in one day. Snorkeling, swimming, and island exploration included.",
                price=349.99,
                price_sol=0.175,
                duration="Full Day (9 hours)",
                location="Greek Islands",
                image_url="https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?w=800&h=600&fit=crop&q=80"
            ),
        ]

        for tour in tours:
            db.add(tour)
        
        db.commit()
        print(f"Seeded {len(tours)} tours successfully")
    except Exception as e:
        print(f"Error seeding tours: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_tours()

