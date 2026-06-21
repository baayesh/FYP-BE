#!/usr/bin/env python3
"""
Example usage of the Quiz Generator

This script demonstrates how to use the quiz_generator.py module
programmatically in your applications.
"""

import os
import json
from quiz_generator import (
    QuizGenerationService,
    QuizGenerationRequest,
    DifficultyLevel,
    LearnerHistory
)

def example_basic_quiz():
    """Generate a basic quiz without learner history"""
    print("=== Basic Quiz Generation ===")

    # Initialize service (replace with your project ID)
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id")
    service = QuizGenerationService(project_id)

    # Create request
    request = QuizGenerationRequest(
        topic="Python Programming",
        difficulty_level=DifficultyLevel.MEDIUM,
        num_questions=5
    )

    try:
        quiz = service.generate_quiz(request)
        print(f"Generated quiz: {quiz.title}")
        print(f"Duration: {quiz.duration} minutes")
        print(f"Questions: {len(quiz.questions)}")

        # Print first question as example
        if quiz.questions:
            q = quiz.questions[0]
            print(f"\nExample Question: {q.question_text}")
            print(f"Type: {q.type}")
            if q.options:
                print(f"Options: {q.options}")
            print(f"Correct Answer: {q.correct_answer}")

    except Exception as e:
        print(f"Error: {e}")

def example_personalized_quiz():
    """Generate a personalized quiz with learner history"""
    print("\n=== Personalized Quiz Generation ===")

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id")
    service = QuizGenerationService(project_id)

    # Create learner history
    learner_history = LearnerHistory(
        performance="Good understanding of basic concepts",
        learning_style="Visual and practical examples",
        completed_topics=["Variables", "Data Types", "Basic Operators"],
        weak_areas=["Functions", "Object-Oriented Programming"]
    )

    # Create request
    request = QuizGenerationRequest(
        topic="Python Functions",
        difficulty_level=DifficultyLevel.HARD,
        num_questions=8,
        learner_history=learner_history
    )

    try:
        quiz = service.generate_quiz(request)
        print(f"Generated personalized quiz: {quiz.title}")
        print(f"Description: {quiz.description}")
        print(f"Duration: {quiz.duration} minutes")

        # Save to file
        with open("personalized_quiz.json", "w") as f:
            json.dump(quiz.dict(), f, indent=2)
        print("Quiz saved to personalized_quiz.json")

    except Exception as e:
        print(f"Error: {e}")

def example_error_handling():
    """Demonstrate error handling"""
    print("\n=== Error Handling Example ===")

    try:
        # This will fail if project ID is invalid
        service = QuizGenerationService("invalid-project-id")
        request = QuizGenerationRequest("Test Topic", DifficultyLevel.EASY)
        quiz = service.generate_quiz(request)
    except ValueError as e:
        print(f"Caught expected error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    print("Quiz Generator Examples")
    print("=" * 50)

    # Check if Google Cloud credentials are available
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        print("Warning: GOOGLE_CLOUD_PROJECT environment variable not set.")
        print("Please set it to your Google Cloud Project ID to run these examples.")
        print("Example: export GOOGLE_CLOUD_PROJECT='my-project-id'")
        print("\nContinuing with examples that will demonstrate error handling...\n")

    example_error_handling()

    # Uncomment these to run actual quiz generation (requires valid GCP setup)
    # example_basic_quiz()
    # example_personalized_quiz()

    print("\n=== Usage Instructions ===")
    print("1. Set your Google Cloud Project ID:")
    print("   export GOOGLE_CLOUD_PROJECT='your-project-id'")
    print("")
    print("2. Set up authentication (choose one):")
    print("   a) Service Account: export GOOGLE_APPLICATION_CREDENTIALS='/path/to/key.json'")
    print("   b) ADC: gcloud auth application-default login")
    print("")
    print("3. Run the examples by uncommenting the function calls above")
    print("")
    print("4. Or use the command line:")
