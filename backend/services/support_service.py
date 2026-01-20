"""
Support Service
Handles 24/7 support system including AI assistant, tickets, FAQ, tutorials, and human support
"""
import logging
import json
import uuid
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc
import re

from models import (
    SupportTicket, SupportMessage, FAQ, SupportAgent, Tutorial, LocalSupport,
    AISupportConversation, AISupportMessage, User
)

logger = logging.getLogger(__name__)


class SupportService:
    """Service for handling 24/7 support system"""
    
    def __init__(self):
        self.ai_provider = "openai"  # Could be configurable
    
    # ========== AI ASSISTANT ==========
    
    async def process_ai_query(
        self,
        message: str,
        user_id: Optional[int],
        session_id: Optional[str],
        context: Optional[dict],
        db: Session
    ) -> Dict[str, Any]:
        """Process AI support query with context awareness and proactive suggestions"""
        try:
            # Get or create conversation session
            if session_id:
                conversation = db.query(AISupportConversation).filter(
                    AISupportConversation.session_id == session_id
                ).first()
            else:
                session_id = str(uuid.uuid4())
                conversation = None
            
            if not conversation:
                conversation = AISupportConversation(
                    user_id=user_id,
                    session_id=session_id,
                    context=json.dumps(context or {}),
                    resolved=False,
                    escalated_to_human=False
                )
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
            
            # Detect user intent
            intent = self._detect_intent(message)
            
            # Search relevant FAQs
            suggested_faqs = await self._find_relevant_faqs(message, db)
            
            # Generate AI response (simplified - in production, use actual AI API)
            ai_response = await self._generate_ai_response(message, intent, suggested_faqs, conversation, db)
            
            # Generate proactive suggestions
            suggestions = self._generate_proactive_suggestions(message, intent, context)
            
            # Determine if escalation needed
            escalate = self._should_escalate(message, intent, ai_response.get('confidence', 0.5))
            
            # Save user message
            user_msg = AISupportMessage(
                conversation_id=conversation.id,
                role="user",
                content=message
            )
            db.add(user_msg)
            
            # Save AI response
            ai_msg = AISupportMessage(
                conversation_id=conversation.id,
                role="assistant",
                content=ai_response['message'],
                confidence_score=ai_response.get('confidence'),
                suggested_faqs=json.dumps([f['id'] for f in suggested_faqs[:3]]) if suggested_faqs else None
            )
            db.add(ai_msg)
            
            # Update conversation context
            conv_context = json.loads(conversation.context or '{}')
            conv_context['last_intent'] = intent
            conv_context['message_count'] = conv_context.get('message_count', 0) + 1
            conversation.context = json.dumps(conv_context)
            conversation.user_intent = intent
            
            if escalate:
                conversation.escalated_to_human = True
            
            db.commit()
            
            return {
                "success": True,
                "message": ai_response['message'],
                "session_id": session_id,
                "suggestions": suggestions,
                "suggested_faqs": [{"id": f['id'], "question": f['question']} for f in suggested_faqs[:3]],
                "escalate_to_human": escalate,
                "confidence_score": ai_response.get('confidence', 0.5)
            }
        except Exception as e:
            logger.error(f"Error processing AI query: {e}")
            return {
                "success": False,
                "message": "I apologize, but I'm having trouble processing your request. Please try again or contact human support.",
                "session_id": session_id or str(uuid.uuid4()),
                "escalate_to_human": True
            }
    
    def _detect_intent(self, message: str) -> str:
        """Detect user intent from message"""
        message_lower = message.lower()
        
        intent_keywords = {
            "booking": ["book", "reserve", "booking", "tour", "schedule"],
            "payment": ["pay", "payment", "refund", "charge", "billing", "invoice"],
            "account": ["account", "profile", "password", "login", "sign up"],
            "technical": ["error", "bug", "not working", "broken", "issue"],
            "general": ["help", "how", "what", "where", "when"]
        }
        
        for intent, keywords in intent_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return intent
        
        return "general"
    
    async def _find_relevant_faqs(self, query: str, db: Session) -> List[Dict]:
        """Find relevant FAQs based on query"""
        query_lower = query.lower()
        
        # Search FAQs by keyword matching
        faqs = db.query(FAQ).filter(
            and_(
                FAQ.is_published == True,
                or_(
                    FAQ.question.ilike(f"%{query}%"),
                    FAQ.answer.ilike(f"%{query}%")
                )
            )
        ).order_by(desc(FAQ.helpful_count)).limit(5).all()
        
        return [
            {
                "id": faq.id,
                "question": faq.question,
                "answer": faq.answer,
                "category": faq.category
            }
            for faq in faqs
        ]
    
    async def _generate_ai_response(
        self,
        message: str,
        intent: str,
        suggested_faqs: List[Dict],
        conversation: AISupportConversation,
        db: Session
    ) -> Dict[str, Any]:
        """Generate AI response (simplified - integrate with actual AI service)"""
        # In production, this would call OpenAI, Anthropic, or similar API
        
        # Simple rule-based responses for demo
        responses = {
            "booking": "I can help you with booking a tour. Would you like to see available tours or do you have a specific tour in mind?",
            "payment": "I can assist with payment questions. Are you having trouble with a payment, need a refund, or have billing questions?",
            "account": "I can help with account-related questions. What do you need help with - login, password reset, or profile updates?",
            "technical": "I understand you're experiencing a technical issue. Can you provide more details about what's not working?",
            "general": "I'm here to help! How can I assist you today?"
        }
        
        base_response = responses.get(intent, responses["general"])
        
        # If relevant FAQs found, mention them
        if suggested_faqs:
            base_response += f"\n\nI found some related articles that might help:"
            for faq in suggested_faqs[:2]:
                base_response += f"\n- {faq['question']}"
        
        # Confidence score (simplified)
        confidence = 0.7 if suggested_faqs else 0.5
        
        return {
            "message": base_response,
            "confidence": confidence
        }
    
    def _generate_proactive_suggestions(
        self,
        message: str,
        intent: str,
        context: Optional[dict]
    ) -> List[str]:
        """Generate proactive suggestions based on user query"""
        suggestions = []
        message_lower = message.lower()
        
        if intent == "booking":
            suggestions = [
                "View available tours",
                "Check booking status",
                "Modify existing booking"
            ]
        elif intent == "payment":
            suggestions = [
                "View payment history",
                "Request refund",
                "Update payment method"
            ]
        elif intent == "account":
            suggestions = [
                "Update profile",
                "Change password",
                "View account settings"
            ]
        else:
            suggestions = [
                "Browse FAQ",
                "Contact support",
                "View tutorials"
            ]
        
        return suggestions
    
    def _should_escalate(self, message: str, intent: str, confidence: float) -> bool:
        """Determine if query should be escalated to human support"""
        # Escalate if confidence is low or urgent keywords detected
        urgent_keywords = ["urgent", "emergency", "critical", "immediately", "asap"]
        message_lower = message.lower()
        
        if confidence < 0.4:
            return True
        
        if any(keyword in message_lower for keyword in urgent_keywords):
            return True
        
        if intent == "technical" and "not working" in message_lower:
            return True
        
        return False
    
    # ========== SUPPORT TICKETS ==========
    
    async def create_ticket(
        self,
        user_id: Optional[int],
        user_email: str,
        subject: str,
        description: str,
        category: str,
        priority: str,
        language: str,
        db: Session
    ) -> Dict[str, Any]:
        """Create a new support ticket"""
        try:
            # Generate ticket number
            ticket_number = f"TKT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
            
            # Get AI suggestions for the ticket
            ai_suggestions = await self._get_ticket_suggestions(description, category, db)
            
            ticket = SupportTicket(
                ticket_number=ticket_number,
                user_id=user_id,
                user_email=user_email,
                subject=subject,
                description=description,
                category=category,
                priority=priority,
                status="open",
                language=language,
                ai_suggestions=json.dumps(ai_suggestions) if ai_suggestions else None
            )
            
            db.add(ticket)
            db.commit()
            db.refresh(ticket)
            
            # Auto-assign if possible
            await self._auto_assign_ticket(ticket, db)
            
            return {
                "success": True,
                "ticket": ticket,
                "ticket_number": ticket_number
            }
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_ticket_suggestions(self, description: str, category: str, db: Session) -> List[str]:
        """Get AI-powered suggestions for ticket resolution"""
        # Find similar resolved tickets
        similar_tickets = db.query(SupportTicket).filter(
            and_(
                SupportTicket.category == category,
                SupportTicket.status == "resolved",
                SupportTicket.resolution.isnot(None)
            )
        ).limit(3).all()
        
        suggestions = []
        if similar_tickets:
            suggestions.append("Similar issues have been resolved. Check resolved tickets for solutions.")
        
        # Find relevant FAQs
        relevant_faqs = await self._find_relevant_faqs(description, db)
        if relevant_faqs:
            suggestions.append(f"Found {len(relevant_faqs)} related FAQ articles that might help.")
        
        return suggestions
    
    async def _auto_assign_ticket(self, ticket: SupportTicket, db: Session):
        """Auto-assign ticket to available agent"""
        # Find available agent matching language and specialty
        agents = db.query(SupportAgent).filter(
            and_(
                SupportAgent.is_active == True,
                SupportAgent.availability_status.in_(["online", "away"]),
                SupportAgent.current_tickets_count < SupportAgent.max_concurrent_tickets
            )
        ).all()
        
        # Try to find agent with matching language
        for agent in agents:
            agent_languages = json.loads(agent.languages or '[]')
            if ticket.language in agent_languages:
                ticket.assigned_to = agent.user_id
                ticket.status = "assigned"
                agent.current_tickets_count += 1
                db.commit()
                return
        
        # Assign to any available agent
        if agents:
            agent = agents[0]
            ticket.assigned_to = agent.user_id
            ticket.status = "assigned"
            agent.current_tickets_count += 1
            db.commit()
    
    async def add_message_to_ticket(
        self,
        ticket_id: int,
        sender_id: Optional[int],
        sender_email: str,
        sender_type: str,
        content: str,
        is_internal: bool,
        attachments: Optional[List[str]],
        db: Session
    ) -> Dict[str, Any]:
        """Add message to support ticket"""
        try:
            ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
            if not ticket:
                return {"success": False, "error": "Ticket not found"}
            
            message = SupportMessage(
                ticket_id=ticket_id,
                sender_id=sender_id,
                sender_email=sender_email,
                sender_type=sender_type,
                content=content,
                is_internal=is_internal,
                attachments=json.dumps(attachments) if attachments else None
            )
            
            db.add(message)
            
            # Update ticket status
            if ticket.status == "open":
                ticket.status = "in_progress"
            
            ticket.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(message)
            
            return {
                "success": True,
                "message": message
            }
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_ticket(
        self,
        ticket_id: int,
        status: Optional[str],
        priority: Optional[str],
        assigned_to: Optional[int],
        resolution: Optional[str],
        db: Session
    ) -> Dict[str, Any]:
        """Update support ticket"""
        try:
            ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
            if not ticket:
                return {"success": False, "error": "Ticket not found"}
            
            if status:
                ticket.status = status
                if status == "resolved":
                    ticket.resolved_at = datetime.utcnow()
                    ticket.resolution = resolution
                    # Update agent stats
                    if ticket.assigned_to:
                        agent = db.query(SupportAgent).filter(
                            SupportAgent.user_id == ticket.assigned_to
                        ).first()
                        if agent:
                            agent.current_tickets_count = max(0, agent.current_tickets_count - 1)
                            agent.total_resolved += 1
            
            if priority:
                ticket.priority = priority
            
            if assigned_to:
                ticket.assigned_to = assigned_to
                ticket.status = "assigned"
            
            if resolution:
                ticket.resolution = resolution
            
            ticket.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(ticket)
            
            return {
                "success": True,
                "ticket": ticket
            }
        except Exception as e:
            logger.error(f"Error updating ticket: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_user_tickets(
        self,
        user_id: Optional[int],
        user_email: Optional[str],
        status: Optional[str],
        db: Session
    ) -> List[SupportTicket]:
        """Get tickets for a user"""
        query = db.query(SupportTicket)
        
        if user_id:
            query = query.filter(SupportTicket.user_id == user_id)
        elif user_email:
            query = query.filter(SupportTicket.user_email == user_email)
        
        if status:
            query = query.filter(SupportTicket.status == status)
        
        return query.order_by(desc(SupportTicket.created_at)).all()
    
    # ========== FAQ MANAGEMENT ==========
    
    async def get_faqs(
        self,
        category: Optional[str],
        language: str,
        search: Optional[str],
        db: Session
    ) -> List[FAQ]:
        """Get FAQs with optional filtering"""
        query = db.query(FAQ).filter(
            and_(
                FAQ.is_published == True,
                FAQ.language == language
            )
        )
        
        if category:
            query = query.filter(FAQ.category == category)
        
        if search:
            query = query.filter(
                or_(
                    FAQ.question.ilike(f"%{search}%"),
                    FAQ.answer.ilike(f"%{search}%")
                )
            )
        
        return query.order_by(FAQ.order, FAQ.helpful_count.desc()).all()
    
    async def get_faq(self, faq_id: int, db: Session) -> Optional[FAQ]:
        """Get a specific FAQ"""
        faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
        if faq:
            faq.view_count += 1
            db.commit()
        return faq
    
    async def record_faq_feedback(self, faq_id: int, helpful: bool, db: Session) -> Dict[str, Any]:
        """Record FAQ helpfulness feedback"""
        faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
        if not faq:
            return {"success": False, "error": "FAQ not found"}
        
        if helpful:
            faq.helpful_count += 1
        else:
            faq.not_helpful_count += 1
        
        db.commit()
        return {"success": True}
    
    # ========== TUTORIALS ==========
    
    async def get_tutorials(
        self,
        category: Optional[str],
        language: str,
        db: Session
    ) -> List[Tutorial]:
        """Get tutorials with optional filtering"""
        query = db.query(Tutorial).filter(
            and_(
                Tutorial.is_published == True,
                Tutorial.language == language
            )
        )
        
        if category:
            query = query.filter(Tutorial.category == category)
        
        return query.order_by(Tutorial.order).all()
    
    async def get_tutorial(self, tutorial_id: int, db: Session) -> Optional[Tutorial]:
        """Get a specific tutorial"""
        tutorial = db.query(Tutorial).filter(Tutorial.id == tutorial_id).first()
        if tutorial:
            tutorial.view_count += 1
            db.commit()
        return tutorial
    
    # ========== LOCAL SUPPORT ==========
    
    async def get_local_support(
        self,
        country: Optional[str],
        city: Optional[str],
        db: Session
    ) -> List[LocalSupport]:
        """Get local support locations"""
        query = db.query(LocalSupport).filter(LocalSupport.is_active == True)
        
        if country:
            query = query.filter(LocalSupport.country == country)
        
        if city:
            query = query.filter(LocalSupport.city == city)
        
        return query.all()
    
    # ========== SUPPORT AGENTS ==========
    
    async def get_available_agents(
        self,
        language: Optional[str],
        db: Session
    ) -> List[SupportAgent]:
        """Get available support agents"""
        query = db.query(SupportAgent).filter(
            and_(
                SupportAgent.is_active == True,
                SupportAgent.availability_status.in_(["online", "away"])
            )
        )
        
        if language:
            # Filter agents who speak the language
            agents = query.all()
            matching_agents = []
            for agent in agents:
                agent_languages = json.loads(agent.languages or '[]')
                if language in agent_languages:
                    matching_agents.append(agent)
            return matching_agents
        
        return query.all()

