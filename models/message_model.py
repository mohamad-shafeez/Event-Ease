"""
EventEase — Message Model
Handles all database operations for conversations and messages.
"""
from db import query

def get_or_create_conversation(user_id, creator_id, event_id=None):
    """Get existing conversation or create a new one."""
    # Check if exists
    if event_id:
        existing = query(
            "SELECT id FROM conversations WHERE user_id=%s AND creator_id=%s AND event_id=%s",
            (user_id, creator_id, event_id), fetchone=True
        )
    else:
        existing = query(
            "SELECT id FROM conversations WHERE user_id=%s AND creator_id=%s",
            (user_id, creator_id), fetchone=True
        )
        
    if existing:
        return existing['id']
        
    # Create new
    if event_id:
        query(
            "INSERT INTO conversations (user_id, creator_id, event_id) VALUES (%s, %s, %s)",
            (user_id, creator_id, event_id)
        )
    else:
        query(
            "INSERT INTO conversations (user_id, creator_id) VALUES (%s, %s)",
            (user_id, creator_id)
        )
        
    # Fetch the newly created ID
    new_conv = query("SELECT LAST_INSERT_ID() as id", fetchone=True)
    return new_conv['id']

def send_message(conversation_id, sender_id, text):
    """Insert a message and update conversation last_message_at."""
    msg_id = query(
        "INSERT INTO messages (conversation_id, sender_id, message_text) VALUES (%s, %s, %s)",
        (conversation_id, sender_id, text)
    )

    query(
        "UPDATE conversations SET last_message_at = CURRENT_TIMESTAMP WHERE id = %s",
        (conversation_id,)
    )

    # Return message details
    return query("SELECT * FROM messages WHERE id=%s", (msg_id,), fetchone=True)

def get_conversations(user_id, role):
    """Fetch all conversations for a user, enriched with other person's details."""
    if role == 'user':
        # User is 'user_id', so the other person is 'creator_id'
        sql = """
            SELECT c.*,
                   u.name as other_name, u.avatar as other_photo,
                   e.title as event_title,
                   (SELECT message_text FROM messages m WHERE m.conversation_id = c.id ORDER BY sent_at DESC LIMIT 1) as last_message,
                   (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id AND m.is_read = 0 AND m.sender_id != %s) as unread_count
            FROM conversations c
            JOIN users u ON c.creator_id = u.id
            LEFT JOIN events e ON c.event_id = e.id
            WHERE c.user_id = %s
            ORDER BY c.last_message_at DESC
        """
        return query(sql, (user_id, user_id))
    else:
        # User is 'creator_id', so the other person is 'user_id'
        sql = """
            SELECT c.*,
                   u.name as other_name, u.avatar as other_photo,
                   e.title as event_title,
                   (SELECT message_text FROM messages m WHERE m.conversation_id = c.id ORDER BY sent_at DESC LIMIT 1) as last_message,
                   (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id AND m.is_read = 0 AND m.sender_id != %s) as unread_count
            FROM conversations c
            JOIN users u ON c.user_id = u.id
            LEFT JOIN events e ON c.event_id = e.id
            WHERE c.creator_id = %s
            ORDER BY c.last_message_at DESC
        """
        return query(sql, (user_id, user_id))

def get_messages(conversation_id, current_user_id):
    """Fetch all messages in a conversation and mark them as read."""
    messages = query(
        "SELECT * FROM messages WHERE conversation_id = %s ORDER BY sent_at ASC",
        (conversation_id,)
    )
    
    # Mark unread messages as read
    query(
        "UPDATE messages SET is_read = 1 WHERE conversation_id = %s AND sender_id != %s AND is_read = 0",
        (conversation_id, current_user_id)
    )
    
    return messages

def get_conversation_by_id(conversation_id):
    """Fetch raw conversation info to check ownership."""
    return query("SELECT * FROM conversations WHERE id = %s", (conversation_id,), fetchone=True)

def get_unread_count(user_id):
    """Count total unread messages for a user."""
    sql = """
        SELECT COUNT(*) as c 
        FROM messages m 
        JOIN conversations c ON m.conversation_id = c.id 
        WHERE m.is_read = 0 
        AND m.sender_id != %s 
        AND (c.user_id = %s OR c.creator_id = %s)
    """
    return query(sql, (user_id, user_id, user_id), fetchone=True)['c']

def delete_message(message_id, sender_id):
    """Soft delete a message if user is the sender."""
    query(
        "UPDATE messages SET message_text = 'This message was deleted' WHERE id = %s AND sender_id = %s",
        (message_id, sender_id)
    )
