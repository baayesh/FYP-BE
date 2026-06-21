# AI-Powered Quiz Generator

A standalone Python script that generates personalized quizzes using Google's Vertex AI Gemini. This tool creates structured prompts containing topic, difficulty level, and learner history, then validates and returns JSON-formatted quizzes.

## Features

- **AI-Powered Generation**: Uses Vertex AI Gemini 1.5 Pro for intelligent quiz creation
- **Personalized Content**: Incorporates learner history and performance data
- **Structured Validation**: Ensures generated quizzes meet quality standards
- **Multiple Question Types**: Supports multiple-choice, true-false, and short-answer questions
- **Flexible Difficulty**: Easy, medium, and hard difficulty levels
- **Error Handling**: Graceful handling of AI response errors and validation failures

## Prerequisites

1. **Google Cloud Project** with Vertex AI API enabled
2. **Python 3.8+**
3. **Google Cloud Authentication** (Service Account Key or Application Default Credentials)

## Installation

1. Install required packages:
```bash
pip install -r quiz_generator_requirements.txt
```

2. Set up Google Cloud authentication:
```bash
# Option 1: Service Account Key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# Option 2: Application Default Credentials
gcloud auth application-default login
```

## Usage

### Command Line Interface

```bash
python quiz_generator.py --topic "Python Programming" --difficulty medium --questions 10
```

### Parameters

- `--topic` (required): The quiz topic/subject
- `--difficulty`: Difficulty level (easy, medium, hard) - default: medium
- `--questions`: Number of questions (5-20) - default: 10
- `--project`: Google Cloud Project ID (or set `GOOGLE_CLOUD_PROJECT` env var)
- `--location`: Google Cloud region - default: us-central1
- `--output`: Output file path (default: stdout)
- `--performance`: Learner's previous performance level
- `--learning-style`: Learner's preferred learning style
- `--completed-topics`: Comma-separated list of completed topics
- `--weak-areas`: Comma-separated list of weak areas

### Examples

#### Basic Quiz Generation
```bash
python quiz_generator.py \
  --topic "Machine Learning" \
  --difficulty hard \
  --questions 15 \
  --project my-gcp-project
```

#### Personalized Quiz with Learner History
```bash
python quiz_generator.py \
  --topic "Calculus" \
  --difficulty medium \
  --questions 10 \
  --performance "Good understanding of algebra" \
  --learning-style "Visual" \
  --completed-topics "Limits,Differentiation" \
  --weak-areas "Integration techniques" \
  --output calculus_quiz.json
```

#### Save to File
```bash
python quiz_generator.py \
  --topic "World History" \
  --difficulty easy \
  --output history_quiz.json
```

## Output Format

The script returns a JSON object with the following structure:

```json
{
  "title": "Machine Learning Fundamentals Quiz",
  "description": "Test your knowledge of basic machine learning concepts",
  "duration": 25,
  "questions": [
    {
      "question_text": "What is supervised learning?",
      "type": "multiple-choice",
      "options": [
        "Learning without labeled data",
        "Learning with labeled training data",
        "Learning from unstructured data",
        "Learning from reinforcement signals"
      ],
      "correct_answer": "Learning with labeled training data",
      "explanation": "Supervised learning uses labeled training data to learn patterns.",
      "points": 1
    },
    {
      "question_text": "Neural networks are inspired by the human brain.",
      "type": "true-false",
      "correct_answer": "True",
      "explanation": "Neural networks mimic the structure and function of biological neurons.",
      "points": 1
    }
  ]
}
```

## Question Types

1. **Multiple Choice**: 4 options with 1 correct answer
2. **True/False**: Boolean questions
3. **Short Answer**: Open-ended questions requiring concise responses

## Error Handling

The script includes comprehensive error handling:

- **Authentication Errors**: Invalid Google Cloud credentials
- **API Errors**: Vertex AI service issues
- **Validation Errors**: Invalid quiz structure or content
- **JSON Parsing Errors**: Malformed AI responses

All errors are logged and provide clear error messages for troubleshooting.

## Integration

This standalone script can be easily integrated into larger applications:

```python
from quiz_generator import QuizGenerationService, QuizGenerationRequest, DifficultyLevel, LearnerHistory

# Initialize service
service = QuizGenerationService(project_id="my-project")

# Create request
request = QuizGenerationRequest(
    topic="Data Structures",
    difficulty_level=DifficultyLevel.MEDIUM,
    num_questions=8,
    learner_history=LearnerHistory(
        performance="Strong in algorithms",
        weak_areas=["Trees", "Graphs"]
    )
)

# Generate quiz
quiz = service.generate_quiz(request)
print(quiz.json())
```

## Configuration

Set the following environment variables for easier usage:

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

## Troubleshooting

### Common Issues

1. **"Permission denied"**: Check Google Cloud credentials and project permissions
2. **"Vertex AI API not enabled"**: Enable Vertex AI API in Google Cloud Console
3. **"Invalid JSON response"**: AI occasionally returns malformed responses; the script handles this gracefully
4. **"Validation failed"**: AI response doesn't meet structure requirements; try again

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

This script is provided as-is for educational and development purposes.</content>
<parameter name="filePath">/Users/ayeshbamunuarachchi/Documents/projects/FYP/retinify_backend/QUIZ_GENERATOR_README.md