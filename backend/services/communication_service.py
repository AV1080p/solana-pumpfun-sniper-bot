"""
Communication Service
Handles messaging, AI chatbot, translation, and communication features
"""
import logging
import json
import uuid
from typing import Optional, Dict, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from models import (
    ChatRoom, ChatParticipant, Message, AIConversation, AIMessage,
    CallSession, BroadcastAlert, BroadcastView, ForumCategory, ForumPost, ForumReply, User
)

logger = logging.getLogger(__name__)


class CommunicationService:
    """Service for handling all communication features"""
    
    def __init__(self):
        self.ai_provider = "openai"  # Could be configurable
    
    # ========== CHAT ROOMS & MESSAGING ==========
    
    async def create_chat_room(
        self,
        room_type: str,
        user_id: int,
        provider_id: Optional[int] = None,
        guide_id: Optional[int] = None,
        name: Optional[str] = None,
        db: Session = None
    ) -> Dict:
        """Create a new chat room"""
        # Check if room already exists
        if room_type == "user_provider" and provider_id:
            existing = db.query(ChatRoom).filter(
                and_(
                    ChatRoom.room_type == room_type,
                    ChatRoom.created_by == user_id,
                    ChatRoom.provider_id == provider_id
                )
            ).first()
            if existing:
                return {"success": True, "room": existing, "existing": True}
        
        room = ChatRoom(
            room_type=room_type,
            name=name,
            created_by=user_id,
            provider_id=provider_id,
            guide_id=guide_id,
            is_active=True
        )
        db.add(room)
        db.commit()
        db.refresh(room)
        
        # Add participants
        participant1 = ChatParticipant(room_id=room.id, user_id=user_id)
        db.add(participant1)
        
        if provider_id:
            participant2 = ChatParticipant(room_id=room.id, user_id=provider_id)
            db.add(participant2)
        elif guide_id:
            participant2 = ChatParticipant(room_id=room.id, user_id=guide_id)
            db.add(participant2)
        
        db.commit()
        
        return {"success": True, "room": room, "existing": False}
    
    async def get_user_chat_rooms(self, user_id: int, db: Session) -> List[ChatRoom]:
        """Get all chat rooms for a user"""
        rooms = db.query(ChatRoom).join(ChatParticipant).filter(
            ChatParticipant.user_id == user_id
        ).order_by(ChatRoom.updated_at.desc()).all()
        return rooms
    
    async def send_message(
        self,
        room_id: int,
        sender_id: int,
        content: str,
        message_type: str = "text",
        translate_to: Optional[str] = None,
        db: Session = None
    ) -> Dict:
        """Send a message in a chat room"""
        # Verify user is participant
        participant = db.query(ChatParticipant).filter(
            and_(
                ChatParticipant.room_id == room_id,
                ChatParticipant.user_id == sender_id
            )
        ).first()
        
        if not participant:
            return {"success": False, "error": "Not a participant in this room"}
        
        message = Message(
            room_id=room_id,
            sender_id=sender_id,
            content=content,
            message_type=message_type,
            is_read=False
        )
        
        # Handle translation if requested
        if translate_to:
            translated = await self.translate_text(content, translate_to)
            if translated:
                message.translated_content = translated["translated_text"]
                message.original_language = translated.get("source_language", "auto")
                message.translated_language = translate_to
        
        db.add(message)
        
        # Update room updated_at
        room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
        if room:
            room.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(message)
        
        return {"success": True, "message": message}
    
    async def get_messages(
        self,
        room_id: int,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        db: Session = None
    ) -> Dict:
        """Get messages from a chat room"""
        # Verify user is participant
        participant = db.query(ChatParticipant).filter(
            and_(
                ChatParticipant.room_id == room_id,
                ChatParticipant.user_id == user_id
            )
        ).first()
        
        if not participant:
            return {"success": False, "error": "Not a participant in this room", "messages": []}
        
        messages = db.query(Message).filter(
            Message.room_id == room_id
        ).order_by(Message.created_at.desc()).offset(offset).limit(limit).all()
        
        # Mark messages as read
        unread_ids = [m.id for m in messages if not m.is_read and m.sender_id != user_id]
        if unread_ids:
            db.query(Message).filter(Message.id.in_(unread_ids)).update(
                {"is_read": True, "read_at": datetime.utcnow()},
                synchronize_session=False
            )
            participant.last_read_at = datetime.utcnow()
            db.commit()
        
        return {"success": True, "messages": list(reversed(messages))}
    
    # ========== AI CHATBOT ==========
    
    async def create_ai_conversation(self, user_id: int, db: Session) -> Dict:
        """Create a new AI conversation session"""
        session_id = str(uuid.uuid4())
        conversation = AIConversation(
            user_id=user_id,
            session_id=session_id
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        return {"success": True, "conversation": conversation}
    
    async def get_ai_conversation(self, session_id: str, user_id: int, db: Session) -> Optional[AIConversation]:
        """Get AI conversation by session ID"""
        return db.query(AIConversation).filter(
            and_(
                AIConversation.session_id == session_id,
                AIConversation.user_id == user_id
            )
        ).first()
    
    async def send_ai_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: int = None,
        context: Optional[Dict] = None,
        db: Session = None
    ) -> Dict:
        """Send a message to AI chatbot and get response"""
        # Get or create conversation
        if session_id:
            conversation = await self.get_ai_conversation(session_id, user_id, db)
        else:
            result = await self.create_ai_conversation(user_id, db)
            conversation = result["conversation"]
            session_id = conversation.session_id
        
        if not conversation:
            return {"success": False, "error": "Conversation not found"}
        
        # Save user message
        user_msg = AIMessage(
            conversation_id=conversation.id,
            role="user",
            content=message
        )
        db.add(user_msg)
        db.commit()
        
        # Get AI response (simplified - in production, integrate with OpenAI/Claude/etc.)
        ai_response = await self._generate_ai_response(message, context)
        
        # Save AI response
        ai_msg = AIMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=ai_response
        )
        db.add(ai_msg)
        db.commit()
        db.refresh(ai_msg)
        
        return {
            "success": True,
            "response": ai_response,
            "session_id": session_id,
            "message": ai_msg
        }
    
    async def _generate_ai_response(self, message: str, context: Optional[Dict] = None) -> str:
        """Generate AI response (placeholder - integrate with actual AI service)"""
        # This is a placeholder. In production, integrate with OpenAI, Anthropic, etc.
        # For now, return a simple response
        responses = {
            "hello": "Hello! How can I help you with your travel plans today?",
            "help": "I'm here to help! I can assist with booking tours, answering questions about destinations, and more.",
            "booking": "I can help you with bookings. Would you like to see available tours?",
        }
        
        message_lower = message.lower()
        for key, response in responses.items():
            if key in message_lower:
                return response
        
        return "I'm here to help! How can I assist you with your travel needs today?"
    
    async def get_ai_conversation_history(self, session_id: str, user_id: int, db: Session) -> List[AIMessage]:
        """Get AI conversation history"""
        conversation = await self.get_ai_conversation(session_id, user_id, db)
        if not conversation:
            return []
        
        return db.query(AIMessage).filter(
            AIMessage.conversation_id == conversation.id
        ).order_by(AIMessage.created_at.asc()).all()
    
    # ========== TRANSLATION ==========
    
    async def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> Dict:
        """Translate text to target language (placeholder - integrate with translation API)"""
        # This is a placeholder. In production, integrate with Google Translate, DeepL, etc.
        # For now, return the original text with a note
        return {
            "success": True,
            "original_text": text,
            "translated_text": f"[{target_language}] {text}",  # Placeholder
            "source_language": source_language or "auto",
            "target_language": target_language
        }
    
    # ========== VOICE/VIDEO CALLS ==========
    
    async def initiate_call(
        self,
        call_type: str,
        initiator_id: int,
        recipient_id: Optional[int] = None,
        guide_id: Optional[int] = None,
        room_id: Optional[int] = None,
        db: Session = None
    ) -> Dict:
        """Initiate a voice or video call"""
        session_id = str(uuid.uuid4())
        
        call = CallSession(
            call_type=call_type,
            initiator_id=initiator_id,
            recipient_id=recipient_id,
            guide_id=guide_id,
            room_id=room_id,
            session_id=session_id,
            status="initiated"
        )
        db.add(call)
        db.commit()
        db.refresh(call)
        
        return {
            "success": True,
            "call": call,
            "session_id": session_id
        }
    
    async def update_call_status(
        self,
        session_id: str,
        status: str,
        db: Session = None
    ) -> Dict:
        """Update call status"""
        call = db.query(CallSession).filter(CallSession.session_id == session_id).first()
        if not call:
            return {"success": False, "error": "Call not found"}
        
        call.status = status
        
        if status == "active" and not call.started_at:
            call.started_at = datetime.utcnow()
        elif status == "ended":
            call.ended_at = datetime.utcnow()
            if call.started_at:
                duration = (call.ended_at - call.started_at).total_seconds()
                call.duration_seconds = int(duration)
        
        db.commit()
        db.refresh(call)
        
        return {"success": True, "call": call}
    
    # ========== BROADCAST ALERTS ==========
    
    async def create_broadcast(
        self,
        alert_type: str,
        priority: str,
        title: str,
        message: str,
        target_audience: str,
        target_user_ids: Optional[List[int]] = None,
        expires_at: Optional[datetime] = None,
        created_by: Optional[int] = None,
        db: Session = None
    ) -> Dict:
        """Create a broadcast alert"""
        alert = BroadcastAlert(
            alert_type=alert_type,
            priority=priority,
            title=title,
            message=message,
            target_audience=target_audience,
            target_user_ids=json.dumps(target_user_ids) if target_user_ids else None,
            expires_at=expires_at,
            created_by=created_by,
            is_active=True
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        return {"success": True, "alert": alert}
    
    async def get_active_broadcasts(
        self,
        user_id: Optional[int] = None,
        user_role: Optional[str] = None,
        db: Session = None
    ) -> List[Dict]:
        """Get active broadcast alerts for a user"""
        now = datetime.utcnow()
        query = db.query(BroadcastAlert).filter(
            and_(
                BroadcastAlert.is_active == True,
                or_(
                    BroadcastAlert.expires_at == None,
                    BroadcastAlert.expires_at > now
                )
            )
        )
        
        # Filter by target audience
        if user_id and user_role:
            query = query.filter(
                or_(
                    BroadcastAlert.target_audience == "all",
                    BroadcastAlert.target_audience == user_role,
                    BroadcastAlert.target_audience == "specific"
                )
            )
        
        alerts = query.order_by(
            BroadcastAlert.priority.desc(),
            BroadcastAlert.created_at.desc()
        ).all()
        
        result = []
        for alert in alerts:
            # Check if specific targeting
            if alert.target_audience == "specific" and alert.target_user_ids:
                target_ids = json.loads(alert.target_user_ids)
                if user_id not in target_ids:
                    continue
            
            # Check if user has viewed
            viewed = False
            if user_id:
                view = db.query(BroadcastView).filter(
                    and_(
                        BroadcastView.alert_id == alert.id,
                        BroadcastView.user_id == user_id
                    )
                ).first()
                viewed = view is not None
            
            alert_dict = {
                "id": alert.id,
                "alert_type": alert.alert_type,
                "priority": alert.priority,
                "title": alert.title,
                "message": alert.message,
                "created_at": alert.created_at,
                "viewed": viewed
            }
            result.append(alert_dict)
        
        return result
    
    async def mark_broadcast_viewed(self, alert_id: int, user_id: int, db: Session) -> Dict:
        """Mark a broadcast as viewed by user"""
        # Check if already viewed
        existing = db.query(BroadcastView).filter(
            and_(
                BroadcastView.alert_id == alert_id,
                BroadcastView.user_id == user_id
            )
        ).first()
        
        if existing:
            return {"success": True, "already_viewed": True}
        
        view = BroadcastView(alert_id=alert_id, user_id=user_id)
        db.add(view)
        db.commit()
        
        return {"success": True, "already_viewed": False}
    
    # ========== FORUMS ==========
    
    async def get_forum_categories(self, db: Session) -> List[ForumCategory]:
        """Get all active forum categories"""
        return db.query(ForumCategory).filter(
            ForumCategory.is_active == True
        ).order_by(ForumCategory.order.asc()).all()
    
    async def create_forum_post(
        self,
        category_id: int,
        author_id: int,
        title: str,
        content: str,
        db: Session = None
    ) -> Dict:
        """Create a forum post"""
        import re
        # Simple slug generation
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        
        post = ForumPost(
            category_id=category_id,
            author_id=author_id,
            title=title,
            content=content,
            slug=slug
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        
        return {"success": True, "post": post}
    
    async def get_forum_posts(
        self,
        category_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0,
        db: Session = None
    ) -> List[ForumPost]:
        """Get forum posts"""
        query = db.query(ForumPost)
        
        if category_id:
            query = query.filter(ForumPost.category_id == category_id)
        
        return query.order_by(
            ForumPost.is_pinned.desc(),
            ForumPost.created_at.desc()
        ).offset(offset).limit(limit).all()
    
    async def create_forum_reply(
        self,
        post_id: int,
        author_id: int,
        content: str,
        parent_reply_id: Optional[int] = None,
        db: Session = None
    ) -> Dict:
        """Create a forum reply"""
        reply = ForumReply(
            post_id=post_id,
            author_id=author_id,
            content=content,
            parent_reply_id=parent_reply_id
        )
        db.add(reply)
        
        # Update post reply count and last reply time
        post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
        if post:
            post.reply_count = (post.reply_count or 0) + 1
            post.last_reply_at = datetime.utcnow()
        
        db.commit()
        db.refresh(reply)
        
        return {"success": True, "reply": reply}

