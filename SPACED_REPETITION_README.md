# Spaced Repetition Service

A standalone spaced repetition algorithm that calculates optimal review intervals based on learner performance. This service implements an adaptive scheduling system that updates memory strength scores and schedules reviews to maximize long-term retention.

## Features

- **Adaptive Scheduling**: Calculates optimal review intervals based on performance
- **Memory Strength Tracking**: Maintains and updates memory strength scores
- **Forgetting Curve Modeling**: Applies exponential decay to simulate forgetting
- **Performance-Based Adjustments**: Modifies intervals based on correctness and difficulty
- **Due Review Tracking**: Identifies topics that need review
- **Persistent Storage**: Saves memory records to JSON files
- **Configurable Parameters**: Customizable intervals and multipliers

## Algorithm Overview

### Memory Strength Updates
- **Correct Answers**: Increase memory strength based on performance rating and difficulty
- **Incorrect Answers**: Decrease memory strength with penalty
- **Consecutive Success**: Rewards streaks of correct answers
- **Time Factor**: Adjusts based on time spent vs. expected time

### Review Intervals
- **Base Intervals**: Different schedules for easy, medium, and hard difficulty
  - Easy: [1, 3, 7, 14, 30] days
  - Medium: [1, 2, 5, 10, 20] days
  - Hard: [1, 1, 3, 7, 14] days
- **Memory Multipliers**: Adjust intervals based on current memory strength
- **Performance Multipliers**: Scale intervals based on answer quality

### Forgetting Decay
- **Exponential Decay**: Memory strength decreases over time when not reviewed
- **Decay Rate**: Configurable forgetting rate (default: 0.1)
- **Time-Based**: Decay factor based on days since last review

## Installation

```bash
pip install -r spaced_repetition_requirements.txt
```

## Usage

### Command Line Interface

#### Process a Quiz Attempt
```bash
python spaced_repetition.py \
  --user-id "user123" \
  --topic-id "algebra_basics" \
  --difficulty medium \
  --performance correct \
  --time-spent 25
```

#### List Due Reviews
```bash
python spaced_repetition.py --user-id "user123" --list-due
```

### Parameters

- `--user-id`: User identifier (required)
- `--topic-id`: Topic/quiz identifier (required for processing attempts)
- `--difficulty`: Difficulty level (easy, medium, hard) - required for attempts
- `--performance`: Performance rating (incorrect, correct_with_difficulty, correct, perfect) - required for attempts
- `--time-spent`: Time spent in minutes (optional)
- `--output`: Output file path (default: stdout)
- `--list-due`: List all due reviews for the user

### Programmatic Usage

```python
from spaced_repetition import SpacedRepetitionService, QuizAttemptData, DifficultyLevel, PerformanceRating
from datetime import datetime

# Initialize service
service = SpacedRepetitionService()

# Process a quiz attempt
attempt = QuizAttemptData(
    user_id="user123",
    topic_id="calculus_limits",
    difficulty_level=DifficultyLevel.HARD,
    performance_rating=PerformanceRating.CORRECT_WITH_DIFFICULTY,
    time_spent_minutes=35,
    completed_at=datetime.now()
)

# Get updated schedule
schedule = service.process_quiz_attempt(attempt)
print(f"Next review: {schedule.next_review_date}")
print(f"Memory strength: {schedule.memory_strength}")

# Get due reviews
due_reviews = service.get_due_reviews("user123")
for review in due_reviews:
    print(f"Topic {review['topic_id']} is due (overdue by {review['days_overdue']} days)")
```

## Algorithm Details

### Memory Strength Calculation

```
new_strength = old_strength + (performance_multiplier × difficulty_factor × time_factor)
```

- **Performance Multipliers**:
  - `incorrect`: 0.5
  - `correct_with_difficulty`: 0.8
  - `correct`: 1.0
  - `perfect`: 1.3

- **Difficulty Factors**:
  - `easy`: 0.8
  - `medium`: 1.0
  - `hard`: 1.3

- **Time Factors**:
  - Based on ratio of actual time to expected time
  - Fast completion: 1.2 (bonus)
  - Slow completion: 0.8 (penalty)

### Forgetting Decay

```
decayed_strength = current_strength × exp(-decay_rate × days_since_review)
```

### Next Review Calculation

```
base_interval = base_intervals[difficulty][min(consecutive_correct, len(intervals)-1)]
memory_multiplier = clamp(0.5, 2.0, 1.0 + (memory_strength - 2.5) × 0.2)
adjusted_days = base_interval × memory_multiplier
next_review = now + adjusted_days
```

## Data Models

### QuizAttemptData
```python
{
    "user_id": "string",
    "topic_id": "string",
    "difficulty_level": "easy|medium|hard",
    "performance_rating": "incorrect|correct_with_difficulty|correct|perfect",
    "time_spent_minutes": 30,
    "completed_at": "2024-01-01T10:00:00Z"
}
```

### ReviewScheduleData
```python
{
    "user_id": "string",
    "topic_id": "string",
    "memory_strength": 2.5,
    "next_review_date": "2024-01-03T10:00:00Z",
    "review_count": 5,
    "consecutive_correct": 3,
    "total_attempts": 8,
    "correct_attempts": 6,
    "last_updated": "2024-01-01T10:00:00Z"
}
```

## Storage

Memory records are stored as JSON files with naming pattern:
```
memory_records_{user_id}_{topic_id}.json
```

Example:
```json
{
  "user_id": "user123",
  "topic_id": "algebra_basics",
  "memory_strength": 2.8,
  "last_review_date": "2024-01-01T10:00:00",
  "next_review_date": "2024-01-03T10:00:00",
  "review_count": 5,
  "consecutive_correct": 3,
  "total_attempts": 8,
  "correct_attempts": 6,
  "created_at": "2023-12-01T09:00:00",
  "updated_at": "2024-01-01T10:00:00"
}
```

## Configuration

The service includes several configurable parameters:

```python
class SpacedRepetitionService:
    def __init__(self):
        self.base_intervals = {
            DifficultyLevel.EASY: [1, 3, 7, 14, 30],
            DifficultyLevel.MEDIUM: [1, 2, 5, 10, 20],
            DifficultyLevel.HARD: [1, 1, 3, 7, 14]
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
```

## Examples

### Example 1: Processing a Perfect Score
```bash
python spaced_repetition.py \
  --user-id "student001" \
  --topic-id "python_loops" \
  --difficulty easy \
  --performance perfect \
  --time-spent 15
```

Output:
```json
{
  "user_id": "student001",
  "topic_id": "python_loops",
  "memory_strength": 1.56,
  "next_review_date": "2024-01-04T10:30:00",
  "review_count": 1,
  "consecutive_correct": 1,
  "total_attempts": 1,
  "correct_attempts": 1,
  "last_updated": "2024-01-01T10:30:00"
}
```

### Example 2: Listing Due Reviews
```bash
python spaced_repetition.py --user-id "student001" --list-due
```

Output:
```json
{
  "user_id": "student001",
  "due_reviews": [
    {
      "topic_id": "python_loops",
      "next_review_date": "2024-01-04T10:30:00",
      "memory_strength": 1.56,
      "days_overdue": 0
    }
  ],
  "total_due": 1
}
```

## Integration

This service can be easily integrated into larger applications:

```python
from spaced_repetition import SpacedRepetitionService

class LearningManagementSystem:
    def __init__(self):
        self.spaced_repetition = SpacedRepetitionService()

    def complete_quiz(self, user_id, quiz_data):
        # Process quiz results
        attempt = QuizAttemptData(
            user_id=user_id,
            topic_id=quiz_data.topic_id,
            difficulty_level=quiz_data.difficulty,
            performance_rating=self.calculate_performance(quiz_data),
            time_spent_minutes=quiz_data.time_spent
        )

        # Update spaced repetition schedule
        schedule = self.spaced_repetition.process_quiz_attempt(attempt)

        # Schedule next review
        self.schedule_review_reminder(user_id, schedule.topic_id, schedule.next_review_date)

        return schedule
```

## Performance Ratings

- **incorrect**: Completely wrong answer
- **correct_with_difficulty**: Correct but required significant effort/hints
- **correct**: Correct answer given confidently
- **perfect**: Correct with perfect understanding and speed

## Troubleshooting

### Common Issues

1. **No memory record found**: First attempt for user/topic combination - normal
2. **Negative memory strength**: Algorithm allows temporary negative values for difficult material
3. **Very long intervals**: High memory strength leads to extended review periods
4. **Very short intervals**: Low memory strength or incorrect answers trigger frequent reviews

### Debug Information

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

- **Database Integration**: Replace file-based storage with database
- **Advanced Algorithms**: Implement SM-2, FSRS, or other spaced repetition algorithms
- **User Preferences**: Allow customization of intervals and multipliers
- **Analytics**: Track learning patterns and provide insights
- **Batch Processing**: Handle multiple quiz attempts simultaneously

## License

This spaced repetition service is provided as-is for educational and development purposes.</content>
<parameter name="filePath">/Users/ayeshbamunuarachchi/Documents/projects/FYP/retinify_backend/SPACED_REPETITION_README.md