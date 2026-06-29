import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc, func as sqlfunc, or_

from app.models.conversation import Conversation, ConversationType
from app.models.conversation_participant import ConversationParticipant
from app.models.message import Message
from app.models.user import User, UserRole
from app.models.course import Course, CourseEnrollment
from app.models.calendar_event import ParentChildRelationship


class MessageService:
    def __init__(self, db: Session):
        self.db = db

    def _can_message_user(self, sender: User, target_id: str) -> bool:
        if sender.role == UserRole.ADMIN:
            return True

        target = self.db.query(User).filter(User.id == target_id).first()
        if not target:
            return False

        if sender.role == UserRole.STUDENT:
            if target.role == UserRole.TEACHER:
                count = self.db.query(CourseEnrollment).join(
                    Course, CourseEnrollment.course_id == Course.id
                ).filter(
                    CourseEnrollment.student_id == sender.id,
                    Course.teacher_id == target_id,
                    CourseEnrollment.status == "active"
                ).count()
                return count > 0
            if target.role == UserRole.PARENT:
                count = self.db.query(ParentChildRelationship).filter(
                    ParentChildRelationship.child_id == sender.id,
                    ParentChildRelationship.parent_id == target_id
                ).count()
                return count > 0
            return False

        if sender.role == UserRole.TEACHER:
            if target.role == UserRole.STUDENT:
                count = self.db.query(CourseEnrollment).join(
                    Course, CourseEnrollment.course_id == Course.id
                ).filter(
                    CourseEnrollment.student_id == target_id,
                    Course.teacher_id == sender.id,
                    CourseEnrollment.status == "active"
                ).count()
                return count > 0
            if target.role == UserRole.PARENT:
                count = self.db.query(CourseEnrollment).join(
                    Course, CourseEnrollment.course_id == Course.id
                ).join(
                    ParentChildRelationship,
                    ParentChildRelationship.child_id == CourseEnrollment.student_id
                ).filter(
                    Course.teacher_id == sender.id,
                    ParentChildRelationship.parent_id == target_id,
                    CourseEnrollment.status == "active"
                ).count()
                return count > 0
            return False

        if sender.role == UserRole.PARENT:
            if target.role == UserRole.TEACHER:
                count = self.db.query(ParentChildRelationship).join(
                    CourseEnrollment,
                    CourseEnrollment.student_id == ParentChildRelationship.child_id
                ).join(
                    Course, CourseEnrollment.course_id == Course.id
                ).filter(
                    ParentChildRelationship.parent_id == sender.id,
                    Course.teacher_id == target_id,
                    CourseEnrollment.status == "active"
                ).count()
                return count > 0
            return False

        return False

    def _get_participant_info(self, user: User) -> dict:
        return {
            "id": user.id,
            "name": user.full_name,
            "avatar": user.avatar,
            "role": user.role.value if hasattr(user.role, 'value') else user.role
        }

    def create_conversation(self, current_user: User, participant_ids: list[str],
                            subject: Optional[str] = None,
                            context_type: Optional[str] = None,
                            context_id: Optional[str] = None) -> Conversation:
        all_ids = list(set([current_user.id] + participant_ids))

        for pid in participant_ids:
            if pid == current_user.id:
                continue
            if not self._can_message_user(current_user, pid):
                raise PermissionError(f"Cannot message user {pid}")

        conv_type = ConversationType.GROUP if len(participant_ids) > 1 else ConversationType.DIRECT

        conversation = Conversation(
            id=str(uuid.uuid4()),
            subject=subject,
            type=conv_type,
            context_type=context_type,
            context_id=context_id,
        )
        self.db.add(conversation)
        self.db.flush()

        for uid in all_ids:
            participant = ConversationParticipant(
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                user_id=uid,
            )
            self.db.add(participant)

        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_user_conversations(self, current_user: User, page: int = 1, limit: int = 20) -> dict:
        offset = (page - 1) * limit

        base_query = self.db.query(Conversation).join(
            ConversationParticipant,
            ConversationParticipant.conversation_id == Conversation.id
        ).filter(
            ConversationParticipant.user_id == current_user.id,
            ConversationParticipant.left_at.is_(None)
        ).order_by(desc(Conversation.last_message_at)).distinct()

        total = base_query.count()
        conversations = base_query.offset(offset).limit(limit).all()

        items = []
        for conv in conversations:
            participant_users = self.db.query(User).join(
                ConversationParticipant,
                ConversationParticipant.user_id == User.id
            ).filter(
                ConversationParticipant.conversation_id == conv.id,
                ConversationParticipant.left_at.is_(None)
            ).all()

            other_participants = [u for u in participant_users if u.id != current_user.id]

            last_msg = self.db.query(Message).filter(
                Message.conversation_id == conv.id
            ).order_by(desc(Message.created_at)).first()

            unread = self.db.query(Message).filter(
                Message.conversation_id == conv.id,
                Message.recipient_id == current_user.id,
                Message.is_read == False
            ).count()

            items.append({
                "id": conv.id,
                "subject": conv.subject,
                "type": conv.type.value if hasattr(conv.type, 'value') else conv.type,
                "last_preview": last_msg.content[:150] if last_msg else None,
                "last_message_at": last_msg.created_at if last_msg else conv.last_message_at,
                "unread_count": unread,
                "other_participants": [self._get_participant_info(u) for u in other_participants],
                "created_at": conv.created_at,
            })

        return {
            "conversations": items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": max(1, (total + limit - 1) // limit),
        }

    def get_conversation_by_id(self, conversation_id: str, current_user: User) -> Optional[dict]:
        conv = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            return None

        is_participant = self.db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id,
            ConversationParticipant.left_at.is_(None)
        ).first()

        if not is_participant and current_user.role != UserRole.ADMIN:
            return None

        participant_users = self.db.query(User).join(
            ConversationParticipant,
            ConversationParticipant.user_id == User.id
        ).filter(
            ConversationParticipant.conversation_id == conv.id,
            ConversationParticipant.left_at.is_(None)
        ).all()

        unread = self.db.query(Message).filter(
            Message.conversation_id == conv.id,
            Message.recipient_id == current_user.id,
            Message.is_read == False
        ).count()

        last_msg = self.db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(desc(Message.created_at)).first()

        return {
            "id": conv.id,
            "subject": conv.subject,
            "type": conv.type.value if hasattr(conv.type, 'value') else conv.type,
            "context_type": conv.context_type,
            "context_id": conv.context_id,
            "last_message_at": last_msg.created_at if last_msg else conv.last_message_at,
            "last_preview": last_msg.content[:150] if last_msg else None,
            "unread_count": unread,
            "participants": [self._get_participant_info(u) for u in participant_users],
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
        }

    def get_conversation_messages(self, conversation_id: str, current_user: User,
                                  page: int = 1, limit: int = 50) -> Optional[dict]:
        conv = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            return None

        is_participant = self.db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id,
            ConversationParticipant.left_at.is_(None)
        ).first()

        if not is_participant and current_user.role != UserRole.ADMIN:
            return None

        offset = (page - 1) * limit

        base_query = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(desc(Message.created_at))

        total = base_query.count()
        messages = base_query.offset(offset).limit(limit).all()
        messages.reverse()

        user_cache = {}
        result_messages = []
        for msg in messages:
            if msg.sender_id not in user_cache:
                sender = self.db.query(User).filter(User.id == msg.sender_id).first()
                user_cache[msg.sender_id] = sender

            sender = user_cache[msg.sender_id]
            result_messages.append({
                "id": msg.id,
                "conversation_id": msg.conversation_id,
                "sender_id": msg.sender_id,
                "sender_name": sender.full_name if sender else "Unknown",
                "sender_avatar": sender.avatar if sender else None,
                "content": msg.content,
                "is_read": msg.is_read,
                "read_at": msg.read_at,
                "created_at": msg.created_at,
            })

        return {
            "messages": result_messages,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": max(1, (total + limit - 1) // limit),
        }

    def send_message(self, conversation_id: str, current_user: User, content: str) -> Optional[Message]:
        conv = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            return None

        is_participant = self.db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id,
            ConversationParticipant.left_at.is_(None)
        ).first()

        if not is_participant and current_user.role != UserRole.ADMIN:
            return None

        participants = self.db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.left_at.is_(None),
            ConversationParticipant.user_id != current_user.id
        ).all()

        for p in participants:
            message = Message(
                id=str(uuid.uuid4()),
                sender_id=current_user.id,
                recipient_id=p.user_id,
                conversation_id=conversation_id,
                content=content,
                is_read=False,
            )
            self.db.add(message)

        if not participants:
            message = Message(
                id=str(uuid.uuid4()),
                sender_id=current_user.id,
                recipient_id=current_user.id,
                conversation_id=conversation_id,
                content=content,
                is_read=True,
                read_at=datetime.now(timezone.utc),
            )
            self.db.add(message)

        now = datetime.now(timezone.utc)
        conv.last_message_at = now
        conv.last_preview = content[:150]

        self.db.commit()

        return message

    def mark_as_read(self, conversation_id: str, current_user: User) -> bool:
        participant = self.db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id,
            ConversationParticipant.left_at.is_(None)
        ).first()

        if not participant:
            return False

        participant.last_read_at = datetime.now(timezone.utc)

        self.db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.recipient_id == current_user.id,
            Message.is_read == False
        ).update({
            "is_read": True,
            "read_at": datetime.now(timezone.utc)
        })

        self.db.commit()
        return True

    def get_unread_count(self, current_user: User) -> int:
        count = self.db.query(Message).filter(
            Message.recipient_id == current_user.id,
            Message.is_read == False
        ).count()
        return count

    def add_participant(self, conversation_id: str, current_user: User, user_id: str) -> bool:
        conv = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            return False

        is_creator = self.db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id,
            ConversationParticipant.left_at.is_(None)
        ).first()

        if not is_creator:
            return False

        if not self._can_message_user(current_user, user_id):
            raise PermissionError(f"Cannot add user {user_id}")

        existing = self.db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user_id
        ).first()

        if existing:
            if existing.left_at is not None:
                existing.left_at = None
                self.db.commit()
            return True

        participant = ConversationParticipant(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            user_id=user_id,
        )
        self.db.add(participant)
        self.db.commit()
        return True

    def remove_participant(self, conversation_id: str, current_user: User, user_id: str) -> bool:
        participant = self.db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user_id,
            ConversationParticipant.left_at.is_(None)
        ).first()

        if not participant:
            return False

        if current_user.id != user_id:
            is_creator = self.db.query(ConversationParticipant).filter(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == current_user.id,
                ConversationParticipant.left_at.is_(None)
            ).first()
            if not is_creator and current_user.role != UserRole.ADMIN:
                return False

        participant.left_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def get_eligible_recipients(self, current_user: User) -> list[dict]:
        if current_user.role == UserRole.ADMIN:
            users = self.db.query(User).filter(User.status == "active").all()
            return [self._get_participant_info(u) for u in users]

        if current_user.role == UserRole.STUDENT:
            teacher_ids = self.db.query(Course.teacher_id).join(
                CourseEnrollment, CourseEnrollment.course_id == Course.id
            ).filter(
                CourseEnrollment.student_id == current_user.id,
                CourseEnrollment.status == "active"
            ).distinct().all()
            teacher_ids = [t[0] for t in teacher_ids]

            parent_ids = self.db.query(ParentChildRelationship.parent_id).filter(
                ParentChildRelationship.child_id == current_user.id
            ).distinct().all()
            parent_ids = [p[0] for p in parent_ids]

            user_ids = list(set(teacher_ids + parent_ids))
            users = self.db.query(User).filter(User.id.in_(user_ids)).all()
            return [self._get_participant_info(u) for u in users]

        if current_user.role == UserRole.TEACHER:
            student_ids = self.db.query(CourseEnrollment.student_id).join(
                Course, CourseEnrollment.course_id == Course.id
            ).filter(
                Course.teacher_id == current_user.id,
                CourseEnrollment.status == "active"
            ).distinct().all()
            student_ids = [s[0] for s in student_ids]

            parent_ids = self.db.query(ParentChildRelationship.parent_id).join(
                CourseEnrollment,
                CourseEnrollment.student_id == ParentChildRelationship.child_id
            ).join(
                Course, CourseEnrollment.course_id == Course.id
            ).filter(
                Course.teacher_id == current_user.id,
                CourseEnrollment.status == "active"
            ).distinct().all()
            parent_ids = [p[0] for p in parent_ids]

            user_ids = list(set(student_ids + parent_ids))
            users = self.db.query(User).filter(User.id.in_(user_ids)).all()
            return [self._get_participant_info(u) for u in users]

        if current_user.role == UserRole.PARENT:
            teacher_ids = self.db.query(Course.teacher_id).join(
                CourseEnrollment, CourseEnrollment.course_id == Course.id
            ).join(
                ParentChildRelationship,
                ParentChildRelationship.child_id == CourseEnrollment.student_id
            ).filter(
                ParentChildRelationship.parent_id == current_user.id,
                CourseEnrollment.status == "active"
            ).distinct().all()
            teacher_ids = [t[0] for t in teacher_ids]

            users = self.db.query(User).filter(User.id.in_(teacher_ids)).all()
            return [self._get_participant_info(u) for u in users]

        return []
