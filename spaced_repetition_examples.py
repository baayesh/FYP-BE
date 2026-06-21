#!/usr/bin/env python3
"""
Example usage of the Spaced Repetition Service

This script demonstrates how to use the spaced_repetition.py module
programmatically in your applications.
"""

import os
import json
from datetime import datetime, timedelta
from spaced_repetition import (
    SpacedRepetitionService,
    QuizAttemptData,
    DifficultyLevel,
    PerformanceRating
)

def example_basic_attempt():
    """Process a basic quiz attempt"""
    print("=== Basic Quiz Attempt Processing ===")

    service = SpacedRepetitionService()

    attempt = QuizAttemptData(
        user_id="student001",
        topic_id="python_variables",
        difficulty_level=DifficultyLevel.EASY,
        performance_rating=PerformanceRating.CORRECT,
        time_spent_minutes=12,
        completed_at=datetime.now()
    )

    try:
        schedule = service.process_quiz_attempt(attempt)
        print(f"User: {schedule.user_id}")
        print(f"Topic: {schedule.topic_id}")
        print(f"Memory Strength: {schedule.memory_strength:.2f}")
        print(f"Next Review: {schedule.next_review_date}")
        print(f"Review Count: {schedule.review_count}")
        print(f"Consecutive Correct: {schedule.consecutive_correct}")

    except Exception as e:
        print(f"Error: {e}")

def example_difficulty_levels():
    """Demonstrate different difficulty levels"""
    print("\n=== Different Difficulty Levels ===")

    service = SpacedRepetitionService()

    difficulties = [
        (DifficultyLevel.EASY, PerformanceRating.CORRECT),
        (DifficultyLevel.MEDIUM, PerformanceRating.CORRECT),
        (DifficultyLevel.HARD, PerformanceRating.CORRECT_WITH_DIFFICULTY)
    ]

    for difficulty, performance in difficulties:
        attempt = QuizAttemptData(
            user_id="student002",
            topic_id=f"topic_{difficulty.value}",
            difficulty_level=difficulty,
            performance_rating=performance,
            time_spent_minutes=20,
            completed_at=datetime.now()
        )

        schedule = service.process_quiz_attempt(attempt)
        print(f"{difficulty.value}: Next review in {(schedule.next_review_date - datetime.now()).days} days")

def example_performance_ratings():
    """Demonstrate different performance ratings"""
    print("\n=== Different Performance Ratings ===")

    service = SpacedRepetitionService()

    ratings = [
        PerformanceRating.INCORRECT,
        PerformanceRating.CORRECT_WITH_DIFFICULTY,
        PerformanceRating.CORRECT,
        PerformanceRating.PERFECT
    ]

    for rating in ratings:
        attempt = QuizAttemptData(
            user_id="student003",
            topic_id=f"performance_{rating.value}",
            difficulty_level=DifficultyLevel.MEDIUM,
            performance_rating=rating,
            time_spent_minutes=25,
            completed_at=datetime.now()
        )

        schedule = service.process_quiz_attempt(attempt)
        print(f"{rating.value}: Memory strength = {schedule.memory_strength:.2f}")

def example_due_reviews():
    """Demonstrate due review tracking"""
    print("\n=== Due Reviews Tracking ===")

    service = SpacedRepetitionService()

    # Create some past attempts
    past_attempts = [
        ("student004", "math_addition", DifficultyLevel.EASY, PerformanceRating.PERFECT, 1),
        ("student004", "math_subtraction", DifficultyLevel.EASY, PerformanceRating.CORRECT, 2),
        ("student004", "math_multiplication", DifficultyLevel.MEDIUM, PerformanceRating.CORRECT_WITH_DIFFICULTY, 7),
    ]

    for user_id, topic_id, difficulty, performance, days_ago in past_attempts:
        attempt = QuizAttemptData(
            user_id=user_id,
            topic_id=topic_id,
            difficulty_level=difficulty,
            performance_rating=performance,
            time_spent_minutes=15,
            completed_at=datetime.now() - timedelta(days=days_ago)
        )
        service.process_quiz_attempt(attempt)

    # Check due reviews
    due_reviews = service.get_due_reviews("student004")
    print(f"Found {len(due_reviews)} due reviews:")
    for review in due_reviews:
        print(f"  {review['topic_id']}: overdue by {review['days_overdue']} days")

def example_learning_progression():
    """Demonstrate learning progression over multiple attempts"""
    print("\n=== Learning Progression ===")

    service = SpacedRepetitionService()

    topic_id = "spanish_vocab"
    user_id = "student005"

    # Simulate learning progression
    attempts = [
        (PerformanceRating.INCORRECT, 30),  # First attempt - failed
        (PerformanceRating.CORRECT_WITH_DIFFICULTY, 25),  # Second attempt - struggled
        (PerformanceRating.CORRECT, 20),  # Third attempt - got it
        (PerformanceRating.CORRECT, 18),  # Fourth attempt - confident
        (PerformanceRating.PERFECT, 15),  # Fifth attempt - mastered
    ]

    print("Learning progression for Spanish vocabulary:")
    for i, (performance, time_spent) in enumerate(attempts, 1):
        attempt = QuizAttemptData(
            user_id=user_id,
            topic_id=topic_id,
            difficulty_level=DifficultyLevel.MEDIUM,
            performance_rating=performance,
            time_spent_minutes=time_spent,
            completed_at=datetime.now() + timedelta(days=i-1)
        )

        schedule = service.process_quiz_attempt(attempt)
        next_review_days = (schedule.next_review_date - attempt.completed_at).days

        print(f"  Attempt {i}: {performance.value} -> Memory: {schedule.memory_strength:.2f}, Next review: {next_review_days} days")

def example_error_handling():
    """Demonstrate error handling"""
    print("\n=== Error Handling ===")

    service = SpacedRepetitionService()

    try:
        # Invalid attempt data
        attempt = QuizAttemptData(
            user_id="",
            topic_id="",
            difficulty_level=DifficultyLevel.EASY,
            performance_rating=PerformanceRating.CORRECT,
            time_spent_minutes=-5,  # Invalid time
            completed_at=datetime.now()
        )
        schedule = service.process_quiz_attempt(attempt)
    except ValueError as e:
        print(f"Caught validation error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    print("Spaced Repetition Service Examples")
    print("=" * 50)

    try:
        example_basic_attempt()
        example_difficulty_levels()
        example_performance_ratings()
        example_due_reviews()
        example_learning_progression()
        example_error_handling()

        print("\n=== Usage Instructions ===")
        print("1. Run individual examples by uncommenting function calls")
        print("2. Modify parameters to test different scenarios")
        print("3. Check generated JSON files for persistent storage")
        print("4. Use command line: python spaced_repetition.py --help")

    except Exception as e:
        print(f"Example execution failed: {e}")
        print("Make sure spaced_repetition.py is in the same directory")</content>
<parameter name="filePath">/Users/ayeshbamunuarachchi/Documents/projects/FYP/retinify_backend/spaced_repetition_examples.py