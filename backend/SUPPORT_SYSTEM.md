# 24/7 Support System Documentation

## Overview

The 24/7 Support System provides comprehensive customer support through three main channels:
1. **AI Assistant** - Natural language queries with context-aware responses
2. **Human Support** - Multilingual support agents with video call assistance
3. **Self-Service** - FAQ, video tutorials, and community help

---

## Architecture

### Database Models

#### SupportTicket
- Tracks support requests with ticket numbers
- Categories: technical, billing, booking, general, emergency
- Priorities: low, normal, high, urgent
- Statuses: open, assigned, in_progress, waiting, resolved, closed
- AI suggestions for quick resolution

#### SupportMessage
- Messages within tickets
- Sender types: user, agent, ai, system
- Internal notes for agents only
- Attachment support

#### FAQ
- Frequently asked questions
- Categorized and searchable
- Multi-language support
- Helpfulness tracking

#### Tutorial
- Video tutorials and guides
- Categories: getting_started, booking, payment, account, advanced
- View count tracking
- Multi-language support

#### SupportAgent
- Agent availability and capabilities
- Languages spoken
- Specialties
- Performance metrics (rating, response time)

#### LocalSupport
- On-ground support locations
- Contact information
- Service offerings
- Geographic coordinates

#### AISupportConversation & AISupportMessage
- AI assistant conversation history
- Intent detection
- Confidence scoring
- Escalation tracking

---

## API Endpoints

### AI Assistant

**POST `/support/ai/chat`**
- Process AI support queries
- Returns context-aware responses with suggestions
- Auto-escalates to human when needed

**GET `/support/ai/conversations/{session_id}`**
- Retrieve conversation history
- Access control by user

### Support Tickets

**POST `/support/tickets`**
- Create new support ticket
- Auto-assigns to available agent
- Generates AI suggestions

**GET `/support/tickets`**
- List user's tickets
- Filter by status

**GET `/support/tickets/{ticket_id}`**
- Get ticket details

**GET `/support/tickets/{ticket_id}/messages`**
- Get ticket conversation

**POST `/support/tickets/{ticket_id}/messages`**
- Add message to ticket

**PATCH `/support/tickets/{ticket_id}`**
- Update ticket (Admin only)

### FAQ

**GET `/support/faqs`**
- List FAQs with filtering
- Search support

**GET `/support/faqs/{faq_id}`**
- Get specific FAQ
- Increments view count

**POST `/support/faqs/{faq_id}/feedback`**
- Submit helpfulness feedback

**POST `/support/faqs`**
- Create FAQ (Admin only)

### Tutorials

**GET `/support/tutorials`**
- List tutorials with filtering

**GET `/support/tutorials/{tutorial_id}`**
- Get specific tutorial
- Increments view count

### Local Support

**GET `/support/local`**
- Get local support locations
- Filter by country/city

### Support Agents

**GET `/support/agents`**
- Get available agents
- Filter by language

---

## Features

### AI Assistant

**Natural Language Processing**
- Intent detection (booking, payment, account, technical, general)
- Context-aware responses
- Conversation history tracking

**Proactive Suggestions**
- Related FAQs
- Suggested actions
- Escalation recommendations

**Escalation Logic**
- Low confidence responses
- Urgent keywords detected
- Technical issues
- User request

### Human Support

**Agent Management**
- Availability tracking
- Language matching
- Auto-assignment
- Performance metrics

**Video Call Integration**
- Uses existing CallSession model
- WebRTC support
- Call history tracking

**Multilingual Support**
- Agent language matching
- Multi-language FAQs
- Local support locations

### Self-Service

**FAQ System**
- Categorized questions
- Search functionality
- Helpfulness tracking
- Multi-language support

**Video Tutorials**
- Category organization
- View tracking
- Thumbnail support
- Duration tracking

**Community Help**
- Integrated with Forum system
- User-generated content
- Moderation support

---

## Usage Examples

### Creating a Support Ticket

```python
POST /support/tickets
{
    "subject": "Payment issue",
    "description": "I was charged twice for my booking",
    "category": "billing",
    "priority": "high",
    "language": "en"
}
```

### AI Chat Query

```python
POST /support/ai/chat
{
    "message": "How do I cancel my booking?",
    "session_id": "optional-session-id",
    "context": {}
}
```

### Getting FAQs

```python
GET /support/faqs?category=booking&language=en&search=cancel
```

---

## Integration Points

### With Communication Service
- Uses CallSession for video calls
- Uses ChatRoom for agent-user chat
- Uses Message for ticket conversations

### With Authentication
- User context for personalized support
- Role-based access control
- Session management

### With Payment System
- Ticket creation for payment issues
- Integration with booking system
- Invoice references

---

## Best Practices

### AI Assistant
- Provide clear, concise responses
- Escalate when confidence is low
- Track conversation context
- Learn from user feedback

### Ticket Management
- Auto-assign based on language/specialty
- Set appropriate priorities
- Track resolution time
- Follow up on resolved tickets

### FAQ Management
- Keep FAQs up-to-date
- Monitor helpfulness metrics
- Organize by category
- Support multiple languages

### Agent Management
- Track availability
- Balance workload
- Monitor performance
- Provide training resources

---

## Future Enhancements

1. **Advanced AI**
   - Integration with GPT-4/Claude
   - Sentiment analysis
   - Predictive suggestions

2. **Knowledge Base**
   - Article management
   - Version control
   - Content moderation

3. **Analytics**
   - Support metrics dashboard
   - Response time tracking
   - Satisfaction surveys

4. **Automation**
   - Auto-responses for common issues
   - Ticket routing rules
   - Escalation workflows

