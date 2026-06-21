#!/usr/bin/env python3

import argparse
import json
import logging
import os
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    from pydantic import BaseModel, ValidationError, Field
except ImportError as e:
    print(f"Missing required packages. Please install: pip install google-cloud-aiplatform pydantic")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuizGenerationService:
    def __init__(self, project_id: str, location: str = "us-central1"):
        self.project_id = project_id
        self.location = location

        try:
            vertexai.init(project=project_id, location=location)
            self.model = GenerativeModel("gemini-1.5-pro")
            logger.info(f"Initialized Vertex AI with project: {project_id}, location: {location}")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            raise

    def generate_quiz(self, request: QuizGenerationRequest) -> GeneratedQuizData:
        try:
            logger.info(f"Generating quiz for topic: {request.topic}, difficulty: {request.difficulty_level}")

            prompt = self._create_generation_prompt(request)

            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "max_output_tokens": 4096,
                    "response_mime_type": "application/json"
                }
            )

            logger.info("Received response from Gemini AI")

            quiz_data = self._parse_and_validate_response(response.text)

            logger.info(f"Successfully generated quiz with {len(quiz_data.questions)} questions")
            return quiz_data

        except Exception as e:
            logger.error(f"Error generating quiz: {str(e)}")
            raise ValueError(f"Failed to generate quiz: {str(e)}")

    def _create_generation_prompt(self, request: QuizGenerationRequest) -> str:

        learner_context = ""
        if request.learner_history:
            learner_context = f"""
            Learner History:
            - Previous performance: {request.learner_history.performance}
            - Preferred learning style: {request.learner_history.learning_style}
            - Completed topics: {', '.join(request.learner_history.completed_topics) if request.learner_history.completed_topics else 'None'}
            - Areas needing improvement: {', '.join(request.learner_history.weak_areas) if request.learner_history.weak_areas else 'None'}
            """

        prompt = f"""
        Generate a personalized quiz for the following specifications:

        Topic: {request.topic}
        Difficulty Level: {request.difficulty_level.value}
        Number of Questions: {request.num_questions}
        {learner_context}

        Requirements:
        1. Create a quiz title and description that reflects the topic and difficulty
        2. Generate exactly {request.num_questions} questions
        3. Mix question types: multiple-choice (60%), true-false (20%), short-answer (20%)
        4. For multiple-choice questions, provide exactly 4 options with one correct answer
        5. For true-false questions, correct_answer should be exactly "True" or "False"
        6. For short-answer questions, provide a concise expected answer
        7. Include helpful explanations for correct answers
        8. Set appropriate duration based on difficulty:
           - easy: 15-20 minutes
           - medium: 20-30 minutes
           - hard: 30-45 minutes
        9. Ensure questions are educational and appropriately challenging for the difficulty level
        10. Make questions progressively more challenging within the quiz

        Return the response as a valid JSON object with this exact structure:
        {{
            "title": "Quiz Title",
            "description": "Brief description of the quiz",
            "duration": 30,
            "questions": [
                {{
                    "question_text": "What is the capital of France?",
                    "type": "multiple-choice",
                    "options": ["London", "Paris", "Berlin", "Madrid"],
                    "correct_answer": "Paris",
                    "explanation": "Paris is the capital and largest city of France.",
                    "points": 1
                }},
                {{
                    "question_text": "The Earth is round.",
                    "type": "true-false",
                    "correct_answer": "True",
                    "explanation": "Scientific evidence confirms the Earth is an oblate spheroid.",
                    "points": 1
                }},
                {{
                    "question_text": "Explain Newton's First Law of Motion.",
                    "type": "short-answer",
                    "correct_answer": "An object at rest stays at rest, and an object in motion stays in motion with the same speed and in the same direction unless acted upon by an unbalanced force.",
                    "explanation": "This is also known as the law of inertia.",
                    "points": 2
                }}
            ]
        }}

        IMPORTANT: Ensure the JSON is valid, properly formatted, and all required fields are present.
        Do not include any text outside the JSON structure.
        """

        return prompt

    def _parse_and_validate_response(self, response_text: str) -> GeneratedQuizData:
        try:
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()

            logger.debug(f"Cleaned response: {cleaned_text[:200]}...")

            data = json.loads(cleaned_text)

            quiz_data = GeneratedQuizData(**data)

            if len(quiz_data.questions) == 0:
                raise ValueError("No questions generated")

            if quiz_data.duration < 5 or quiz_data.duration > 120:
                raise ValueError(f"Invalid duration: {quiz_data.duration} minutes")

            for i, question in enumerate(quiz_data.questions):
                if question.type not in ["multiple-choice", "true-false", "short-answer"]:
                    raise ValueError(f"Invalid question type for question {i+1}: {question.type}")

                if question.type == "multiple-choice":
                    if not question.options or len(question.options) != 4:
                        raise ValueError(f"Multiple-choice question {i+1} must have exactly 4 options")
                    if question.correct_answer not in question.options:
                        raise ValueError(f"Correct answer for question {i+1} must be one of the options")

                if question.type == "true-false" and question.correct_answer not in ["True", "False"]:
                    raise ValueError(f"True-false question {i+1} must have 'True' or 'False' as correct answer")

                if not question.question_text.strip():
                    raise ValueError(f"Question {i+1} text cannot be empty")

                if not question.correct_answer.strip():
                    raise ValueError(f"Question {i+1} correct answer cannot be empty")

            logger.info("Quiz data validation successful")
            return quiz_data

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {response_text}")
            raise ValueError(f"AI returned invalid JSON: {str(e)}")

        except ValidationError as e:
            logger.error(f"Pydantic validation error: {e}")
            raise ValueError(f"AI response validation failed: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Generate AI-powered quizzes using Vertex AI Gemini")
    parser.add_argument("--topic", required=True, help="Quiz topic")
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard"], default="medium", help="Difficulty level")
    parser.add_argument("--questions", type=int, default=10, help="Number of questions")
    parser.add_argument("--project", help="Google Cloud Project ID (or set GOOGLE_CLOUD_PROJECT env var)")
    parser.add_argument("--location", default="us-central1", help="Google Cloud location")
    parser.add_argument("--output", help="Output file path (default: stdout)")
    parser.add_argument("--performance", help="Learner's previous performance")
    parser.add_argument("--learning-style", help="Learner's preferred learning style")
    parser.add_argument("--completed-topics", help="Comma-separated list of completed topics")
    parser.add_argument("--weak-areas", help="Comma-separated list of weak areas")

    args = parser.parse_args()

    project_id = args.project or os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("Error: Google Cloud Project ID must be provided via --project or GOOGLE_CLOUD_PROJECT environment variable")
        sys.exit(1)

    try:
        learner_history = LearnerHistory(
            performance=args.performance or "Unknown",
            learning_style=args.learning_style or "Not specified",
            completed_topics=args.completed_topics.split(",") if args.completed_topics else [],
            weak_areas=args.weak_areas.split(",") if args.weak_areas else []
        )

        request = QuizGenerationRequest(
            topic=args.topic,
            difficulty_level=DifficultyLevel(args.difficulty),
            num_questions=args.questions,
            learner_history=learner_history
        )

        service = QuizGenerationService(project_id, args.location)

        quiz_data = service.generate_quiz(request)

        result = quiz_data.dict()

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Quiz saved to {args.output}")
        else:
            print(json.dumps(result, indent=2))

    except Exception as e:
        logger.error(f"Quiz generation failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
