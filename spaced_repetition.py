#!/usr/bin/env python3

import argparse
import json
import logging
import os
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import math

try:
    from pydantic import BaseModel, ValidationError, Field
except ImportError as e:
    print(f"Missing required packages. Please install: pip install pydantic")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class PerformanceRating(str, Enum):
    INCORRECT = "incorrect"
    CORRECT_WITH_DIFFICULTY = "correct_with_difficulty"
    CORRECT = "correct"
    PERFECT = "perfect"

@dataclass
class LearnerMemoryRecord:
    user_id: str
    topic_id: str
    memory_strength: float = 0.0
    last_review_date: Optional[datetime] = None
    next_review_date: Optional[datetime] = None
    review_count: int = 0
    consecutive_correct: int = 0
    total_attempts: int = 0
    correct_attempts: int = 0
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

class QuizAttemptData(BaseModel):
    user_id: str = Field(..., description="ID of the learner")
    topic_id: str = Field(..., description="ID of the topic/quiz")
    difficulty_level: DifficultyLevel = Field(..., description="Difficulty level of the quiz")
    performance_rating: PerformanceRating = Field(..., description="Learner's performance rating")
    time_spent_minutes: Optional[int] = Field(None, description="Time spent on the quiz in minutes")
    completed_at: datetime = Field(default_factory=datetime.now, description="When the quiz was completed")

class ReviewScheduleData(BaseModel):
    user_id: str
    topic_id: str
    memory_strength: float
    next_review_date: datetime
    review_count: int
    consecutive_correct: int
    total_attempts: int
    correct_attempts: int
    last_updated: datetime

class SpacedRepetitionService:
    def __init__(self):
        self.base_intervals = {
            DifficultyLevel.EASY: [1, 3, 7, 14, 30],
            DifficultyLevel.MEDIUM: [1, 3, 7, 14, 30],
            DifficultyLevel.HARD: [1, 3, 7, 14, 30]
        }

        self.performance_multipliers = {
            PerformanceRating.INCORRECT: 0.5,
            PerformanceRating.CORRECT_WITH_DIFFICULTY: 0.8,
            PerformanceRating.CORRECT: 1.0,
            PerformanceRating.PERFECT: 1.3
        }

        self.forgetting_decay_rate = 0.1
        self.min_memory_strength = 0.0
        self.max_memory_strength = 5.0

    def process_quiz_attempt(self, attempt: QuizAttemptData) -> ReviewScheduleData:
        try:
            memory_record = self._retrieve_memory_record(attempt.user_id, attempt.topic_id)

            updated_record = self._update_memory_strength(memory_record, attempt)

            next_review = self._calculate_next_review_date(updated_record, attempt.difficulty_level)

            schedule_data = ReviewScheduleData(
                user_id=updated_record.user_id,
                topic_id=updated_record.topic_id,
                memory_strength=updated_record.memory_strength,
                next_review_date=next_review,
                review_count=updated_record.review_count,
                consecutive_correct=updated_record.consecutive_correct,
                total_attempts=updated_record.total_attempts,
                correct_attempts=updated_record.correct_attempts,
                last_updated=datetime.now()
            )

            self._store_updated_schedule(schedule_data)

            logger.info(f"Processed quiz attempt for user {attempt.user_id}, topic {attempt.topic_id}. Next review: {next_review}")
            return schedule_data

        except Exception as e:
            logger.error(f"Error processing quiz attempt: {str(e)}")
            raise ValueError(f"Failed to process quiz attempt: {str(e)}")

    def _retrieve_memory_record(self, user_id: str, topic_id: str) -> LearnerMemoryRecord:
        try:
            record = self._load_memory_record_from_storage(user_id, topic_id)
            if record is None:
                record = LearnerMemoryRecord(
                    user_id=user_id,
                    topic_id=topic_id,
                    memory_strength=0.0,
                    last_review_date=None,
                    next_review_date=datetime.now(),
                    review_count=0,
                    consecutive_correct=0,
                    total_attempts=0,
                    correct_attempts=0
                )
                logger.info(f"Created new memory record for user {user_id}, topic {topic_id}")
            return record
        except Exception as e:
            logger.error(f"Error retrieving memory record: {str(e)}")
            raise

    def _update_memory_strength(self, record: LearnerMemoryRecord, attempt: QuizAttemptData) -> LearnerMemoryRecord:
        record.total_attempts += 1

        is_correct = attempt.performance_rating in [PerformanceRating.CORRECT, PerformanceRating.PERFECT, PerformanceRating.CORRECT_WITH_DIFFICULTY]
        if is_correct:
            record.correct_attempts += 1
            record.consecutive_correct += 1
        else:
            record.consecutive_correct = 0

        performance_multiplier = self.performance_multipliers[attempt.performance_rating]

        difficulty_factor = self._get_difficulty_factor(attempt.difficulty_level)

        time_factor = self._calculate_time_factor(attempt.time_spent_minutes, attempt.difficulty_level)

        strength_change = performance_multiplier * difficulty_factor * time_factor

        if is_correct:
            record.memory_strength = min(self.max_memory_strength,
                                       record.memory_strength + strength_change)
        else:
            record.memory_strength = max(self.min_memory_strength,
                                       record.memory_strength - strength_change * 0.5)

        record.memory_strength = self._apply_forgetting_decay(record)

        record.last_review_date = attempt.completed_at
        record.review_count += 1
        record.updated_at = datetime.now()

        logger.debug(f"Updated memory strength to {record.memory_strength} for user {record.user_id}")
        return record

    def _apply_forgetting_decay(self, record: LearnerMemoryRecord) -> float:
        if record.last_review_date is None:
            return record.memory_strength

        days_since_review = (datetime.now() - record.last_review_date).days
        if days_since_review <= 0:
            return record.memory_strength

        decay_factor = math.exp(-self.forgetting_decay_rate * days_since_review)
        decayed_strength = record.memory_strength * decay_factor

        return max(self.min_memory_strength, decayed_strength)

    def _calculate_next_review_date(self, record: LearnerMemoryRecord, difficulty: DifficultyLevel) -> datetime:
        base_intervals = self.base_intervals[difficulty]

        interval_index = min(record.consecutive_correct, len(base_intervals) - 1)
        base_days = base_intervals[interval_index]

        memory_multiplier = max(0.5, min(2.0, 1.0 + (record.memory_strength - 2.5) * 0.2))

        adjusted_days = int(base_days * memory_multiplier)

        if record.memory_strength < 1.0:
            adjusted_days = max(1, adjusted_days // 2)
        elif record.memory_strength > 4.0:
            adjusted_days = int(adjusted_days * 1.5)

        next_review = datetime.now() + timedelta(days=adjusted_days)

        logger.debug(f"Calculated next review date: {next_review} (adjusted_days: {adjusted_days})")
        return next_review

    def _get_difficulty_factor(self, difficulty: DifficultyLevel) -> float:
        factors = {
            DifficultyLevel.EASY: 0.8,
            DifficultyLevel.MEDIUM: 1.0,
            DifficultyLevel.HARD: 1.3
        }
        return factors[difficulty]

    def _calculate_time_factor(self, time_spent: Optional[int], difficulty: DifficultyLevel) -> float:
        if time_spent is None:
            return 1.0

        expected_times = {
            DifficultyLevel.EASY: 20,
            DifficultyLevel.MEDIUM: 30,
            DifficultyLevel.HARD: 45
        }

        expected_time = expected_times[difficulty]
        ratio = time_spent / expected_time

        if ratio < 0.5:
            return 1.2
        elif ratio > 1.5:
            return 0.8
        else:
            return 1.0

    def _load_memory_record_from_storage(self, user_id: str, topic_id: str) -> Optional[LearnerMemoryRecord]:
        try:
            storage_file = f"memory_records_{user_id}_{topic_id}.json"
            if os.path.exists(storage_file):
                with open(storage_file, 'r') as f:
                    data = json.load(f)
                    return LearnerMemoryRecord(
                        user_id=data['user_id'],
                        topic_id=data['topic_id'],
                        memory_strength=data['memory_strength'],
                        last_review_date=datetime.fromisoformat(data['last_review_date']) if data.get('last_review_date') else None,
                        next_review_date=datetime.fromisoformat(data['next_review_date']) if data.get('next_review_date') else None,
                        review_count=data['review_count'],
                        consecutive_correct=data['consecutive_correct'],
                        total_attempts=data['total_attempts'],
                        correct_attempts=data['correct_attempts'],
                        created_at=datetime.fromisoformat(data['created_at']),
                        updated_at=datetime.fromisoformat(data['updated_at'])
                    )
            return None
        except Exception as e:
            logger.warning(f"Error loading memory record from storage: {str(e)}")
            return None

    def _store_updated_schedule(self, schedule: ReviewScheduleData) -> None:
        try:
            storage_file = f"memory_records_{schedule.user_id}_{schedule.topic_id}.json"
            data = {
                'user_id': schedule.user_id,
                'topic_id': schedule.topic_id,
                'memory_strength': schedule.memory_strength,
                'last_review_date': schedule.last_updated.isoformat() if schedule.last_updated else None,
                'next_review_date': schedule.next_review_date.isoformat(),
                'review_count': schedule.review_count,
                'consecutive_correct': schedule.consecutive_correct,
                'total_attempts': schedule.total_attempts,
                'correct_attempts': schedule.correct_attempts,
                'created_at': schedule.last_updated.isoformat(),
                'updated_at': schedule.last_updated.isoformat()
            }

            with open(storage_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Stored updated schedule for user {schedule.user_id}, topic {schedule.topic_id}")

        except Exception as e:
            logger.error(f"Error storing updated schedule: {str(e)}")
            raise

    def get_due_reviews(self, user_id: str, current_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        if current_date is None:
            current_date = datetime.now()

        due_reviews = []
        try:
            storage_dir = "."
            for filename in os.listdir(storage_dir):
                if filename.startswith(f"memory_records_{user_id}_") and filename.endswith(".json"):
                    with open(filename, 'r') as f:
                        data = json.load(f)
                        next_review = datetime.fromisoformat(data['next_review_date'])
                        if next_review <= current_date:
                            due_reviews.append({
                                'topic_id': data['topic_id'],
                                'next_review_date': next_review,
                                'memory_strength': data['memory_strength'],
                                'days_overdue': (current_date - next_review).days
                            })
        except Exception as e:
            logger.error(f"Error retrieving due reviews: {str(e)}")

        return sorted(due_reviews, key=lambda x: x['next_review_date'])

def main():
    parser = argparse.ArgumentParser(description="Process spaced repetition quiz attempts")
    parser.add_argument("--user-id", required=True, help="User ID")
    parser.add_argument("--topic-id", required=True, help="Topic/Quiz ID")
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard"], required=True, help="Quiz difficulty level")
    parser.add_argument("--performance", choices=["incorrect", "correct_with_difficulty", "correct", "perfect"], required=True, help="Performance rating")
    parser.add_argument("--time-spent", type=int, help="Time spent in minutes")
    parser.add_argument("--output", help="Output file path (default: stdout)")
    parser.add_argument("--list-due", action="store_true", help="List due reviews for user")

    args = parser.parse_args()

    try:
        service = SpacedRepetitionService()

        if args.list_due:
            due_reviews = service.get_due_reviews(args.user_id)
            result = {
                "user_id": args.user_id,
                "due_reviews": due_reviews,
                "total_due": len(due_reviews)
            }
        else:
            attempt = QuizAttemptData(
                user_id=args.user_id,
                topic_id=args.topic_id,
                difficulty_level=DifficultyLevel(args.difficulty),
                performance_rating=PerformanceRating(args.performance),
                time_spent_minutes=args.time_spent
            )

            schedule = service.process_quiz_attempt(attempt)
            result = schedule.dict()

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"Results saved to {args.output}")
        else:
            print(json.dumps(result, indent=2, default=str))

    except Exception as e:
        logger.error(f"Spaced repetition processing failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()