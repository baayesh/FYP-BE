-- Seed data for retinify database
-- Insert in order respecting foreign key constraints

-- 1. Insert Users (Teachers, Students, Parents)
INSERT INTO users (id, email, password_hash, first_name, last_name, role, phone, status, email_verified, created_at, updated_at) VALUES
-- Teachers
('teacher-001', 'john.smith@retinify.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYuN7w8PQVG', 'John', 'Smith', 'teacher', '+1234567890', 'active', 1, NOW(), NOW()),
('teacher-002', 'sarah.johnson@retinify.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYuN7w8PQVG', 'Sarah', 'Johnson', 'teacher', '+1234567891', 'active', 1, NOW(), NOW()),
('teacher-003', 'michael.brown@retinify.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYuN7w8PQVG', 'Michael', 'Brown', 'teacher', '+1234567892', 'active', 1, NOW(), NOW()),

-- Students
('student-001', 'alice.williams@student.retinify.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYuN7w8PQVG', 'Alice', 'Williams', 'student', '+1234567893', 'active', 1, NOW(), NOW()),
('student-002', 'bob.davis@student.retinify.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYuN7w8PQVG', 'Bob', 'Davis', 'student', '+1234567894', 'active', 1, NOW(), NOW()),
('student-003', 'carol.miller@student.retinify.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYuN7w8PQVG', 'Carol', 'Miller', 'student', '+1234567895', 'active', 1, NOW(), NOW()),
('student-004', 'david.wilson@student.retinify.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYuN7w8PQVG', 'David', 'Wilson', 'student', '+1234567896', 'active', 1, NOW(), NOW()),
('student-005', 'emma.moore@student.retinify.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYuN7w8PQVG', 'Emma', 'Moore', 'student', '+1234567897', 'active', 1, NOW(), NOW()),

-- Parents
('parent-001', 'robert.williams@parent.retinify.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYuN7w8PQVG', 'Robert', 'Williams', 'parent', '+1234567898', 'active', 1, NOW(), NOW()),
('parent-002', 'mary.davis@parent.retinify.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYuN7w8PQVG', 'Mary', 'Davis', 'parent', '+1234567899', 'active', 1, NOW(), NOW());

-- 2. Insert Parent-Child Relationships
INSERT INTO parent_child_relationships (id, parent_id, child_id, relationship_type, verified, created_at) VALUES
('rel-001', 'parent-001', 'student-001', 'father', 1, NOW()),
('rel-002', 'parent-002', 'student-002', 'mother', 1, NOW());

-- 3. Insert Student Levels
INSERT INTO student_levels (id, student_id, grade, stream, overall_progress, academic_year, created_at, updated_at) VALUES
('level-001', 'student-001', 'Grade 10', 'Science', 85.50, '2024-2025', NOW(), NOW()),
('level-002', 'student-002', 'Grade 11', 'Commerce', 78.20, '2024-2025', NOW(), NOW()),
('level-003', 'student-003', 'Grade 9', 'General', 92.30, '2024-2025', NOW(), NOW()),
('level-004', 'student-004', 'Grade 10', 'Science', 88.75, '2024-2025', NOW(), NOW()),
('level-005', 'student-005', 'Grade 11', 'Arts', 81.40, '2024-2025', NOW(), NOW());

-- 4. Insert Courses
INSERT INTO courses (id, teacher_id, title, description, category, level, duration, status, created_at, updated_at) VALUES
('course-001', 'teacher-001', 'Introduction to Python Programming', 'Learn Python from basics to advanced concepts', 'Programming', 'Beginner', '8 weeks', 'active', NOW(), NOW()),
('course-002', 'teacher-001', 'Advanced Web Development', 'Master modern web technologies including React and Node.js', 'Web Development', 'Advanced', '12 weeks', 'active', NOW(), NOW()),
('course-003', 'teacher-002', 'Mathematics Grade 10', 'Complete mathematics curriculum for grade 10 students', 'Mathematics', 'Beginner', '40 weeks', 'active', NOW(), NOW()),
('course-004', 'teacher-002', 'Physics Fundamentals', 'Introduction to physics concepts and practical applications', 'Science', 'Beginner', '16 weeks', 'active', NOW(), NOW()),
('course-005', 'teacher-003', 'English Literature', 'Study classic and modern literature with critical analysis', 'Literature', 'Beginner', '20 weeks', 'active', NOW(), NOW());

-- 5. Insert Lessons
INSERT INTO lessons (id, course_id, title, type, content, description, status, duration, duration_text, video_link, order_index, created_at, updated_at) VALUES
-- Python Course Lessons
('lesson-001', 'course-001', 'Python Basics - Variables and Data Types', 'video', 'Introduction to Python variables, data types, and basic operations', 'Learn about Python variables, integers, strings, and basic data types', 'published', 45, '45 minutes', 'https://www.youtube.com/watch?v=example1', 1, NOW(), NOW()),
('lesson-002', 'course-001', 'Control Flow - If Statements', 'video', 'Learn conditional statements and control flow in Python', 'Master if, elif, and else statements', 'published', 50, '50 minutes', 'https://www.youtube.com/watch?v=example2', 2, NOW(), NOW()),
('lesson-003', 'course-001', 'Loops in Python', 'video', 'Understanding for and while loops', 'Learn iteration with for and while loops', 'published', 55, '55 minutes', 'https://www.youtube.com/watch?v=example3', 3, NOW(), NOW()),

-- Web Development Lessons
('lesson-004', 'course-002', 'Introduction to React', 'video', 'Getting started with React framework', 'Learn React basics and component architecture', 'published', 60, '1 hour', 'https://www.youtube.com/watch?v=example4', 1, NOW(), NOW()),
('lesson-005', 'course-002', 'React Hooks Deep Dive', 'video', 'Understanding useState and useEffect', 'Master React hooks for state management', 'published', 75, '75 minutes', 'https://www.youtube.com/watch?v=example5', 2, NOW(), NOW()),

-- Mathematics Lessons
('lesson-006', 'course-003', 'Algebra Basics', 'video', 'Introduction to algebraic expressions', 'Learn basic algebra and equation solving', 'published', 40, '40 minutes', 'https://www.youtube.com/watch?v=example6', 1, NOW(), NOW()),
('lesson-007', 'course-003', 'Quadratic Equations', 'video', 'Solving quadratic equations', 'Master quadratic formula and factoring', 'published', 45, '45 minutes', 'https://www.youtube.com/watch?v=example7', 2, NOW(), NOW()),

-- Physics Lessons
('lesson-008', 'course-004', 'Newton\'s Laws of Motion', 'video', 'Understanding fundamental laws of physics', 'Learn the three laws of motion', 'published', 50, '50 minutes', 'https://www.youtube.com/watch?v=example8', 1, NOW(), NOW()),

-- Literature Lessons
('lesson-009', 'course-005', 'Introduction to Shakespeare', 'reading', 'Overview of Shakespeare\'s works', 'Explore the world of Shakespeare', 'published', 30, '30 minutes', NULL, 1, NOW(), NOW());

-- 6. Insert Course Enrollments
INSERT INTO course_enrollments (id, student_id, course_id, enrollment_date, status, progress) VALUES
('enroll-001', 'student-001', 'course-001', DATE_SUB(NOW(), INTERVAL 2 WEEK), 'active', 45.50),
('enroll-002', 'student-001', 'course-003', DATE_SUB(NOW(), INTERVAL 1 MONTH), 'active', 65.25),
('enroll-003', 'student-002', 'course-001', DATE_SUB(NOW(), INTERVAL 3 WEEK), 'active', 38.75),
('enroll-004', 'student-002', 'course-004', DATE_SUB(NOW(), INTERVAL 2 MONTH), 'active', 72.50),
('enroll-005', 'student-003', 'course-002', DATE_SUB(NOW(), INTERVAL 1 WEEK), 'active', 15.00),
('enroll-006', 'student-003', 'course-005', DATE_SUB(NOW(), INTERVAL 3 WEEK), 'active', 55.80),
('enroll-007', 'student-004', 'course-003', DATE_SUB(NOW(), INTERVAL 5 WEEK), 'active', 80.25),
('enroll-008', 'student-005', 'course-005', DATE_SUB(NOW(), INTERVAL 2 WEEK), 'active', 42.30);

-- 7. Insert Lesson Progress
INSERT INTO lesson_progress (id, student_id, lesson_id, completed, completed_at, time_spent) VALUES
('progress-001', 'student-001', 'lesson-001', 1, DATE_SUB(NOW(), INTERVAL 10 DAY), 47),
('progress-002', 'student-001', 'lesson-002', 1, DATE_SUB(NOW(), INTERVAL 8 DAY), 52),
('progress-003', 'student-001', 'lesson-003', 0, NULL, 25),
('progress-004', 'student-002', 'lesson-001', 1, DATE_SUB(NOW(), INTERVAL 15 DAY), 50),
('progress-005', 'student-003', 'lesson-004', 1, DATE_SUB(NOW(), INTERVAL 5 DAY), 65);

-- 8. Insert Assignments
INSERT INTO assignments (id, course_id, title, description, instructions, due_date, points, created_at, updated_at) VALUES
('assign-001', 'course-001', 'Python Variables Exercise', 'Practice assignment on Python variables', 'Complete all exercises in the attached notebook', DATE_ADD(NOW(), INTERVAL 7 DAY), 100, NOW(), NOW()),
('assign-002', 'course-001', 'Control Flow Project', 'Build a simple calculator using if statements', 'Create a calculator with basic operations', DATE_ADD(NOW(), INTERVAL 14 DAY), 150, NOW(), NOW()),
('assign-003', 'course-003', 'Algebra Problem Set', 'Solve 20 algebra problems', 'Show all working and solutions', DATE_ADD(NOW(), INTERVAL 5 DAY), 100, NOW(), NOW()),
('assign-004', 'course-004', 'Physics Lab Report', 'Write a report on Newton\'s Laws experiment', 'Include observations, calculations, and conclusions', DATE_ADD(NOW(), INTERVAL 10 DAY), 200, NOW(), NOW());

-- 9. Insert Assignment Submissions
INSERT INTO assignment_submissions (id, assignment_id, student_id, content, submitted_at, status, grade, feedback) VALUES
('submit-001', 'assign-001', 'student-001', 'Completed all exercises. Results attached.', DATE_SUB(NOW(), INTERVAL 2 DAY), 'graded', 92.00, 'Excellent work! Minor improvements needed in exercise 5.'),
('submit-002', 'assign-001', 'student-002', 'Assignment completed with solutions.', DATE_SUB(NOW(), INTERVAL 3 DAY), 'graded', 85.50, 'Good effort. Check your variable naming conventions.'),
('submit-003', 'assign-003', 'student-001', 'All 20 problems solved with working.', DATE_SUB(NOW(), INTERVAL 1 DAY), 'submitted', NULL, NULL);

-- 10. Insert Assignment Files
INSERT INTO assignment_files (id, submission_id, file_name, file_url, file_size, uploaded_at) VALUES
('file-001', 'submit-001', 'python_exercises.py', 'https://storage.retinify.com/files/python_exercises.py', 15420, DATE_SUB(NOW(), INTERVAL 2 DAY)),
('file-002', 'submit-002', 'variables_solution.ipynb', 'https://storage.retinify.com/files/variables_solution.ipynb', 28950, DATE_SUB(NOW(), INTERVAL 3 DAY));

-- 11. Insert Quizzes
INSERT INTO quizzes (id, course_id, title, description, duration, passing_score, max_attempts, created_at) VALUES
('quiz-001', 'course-001', 'Python Basics Quiz', 'Test your knowledge of Python fundamentals', 30, 70, 3, NOW()),
('quiz-002', 'course-003', 'Algebra Mid-term Quiz', 'Comprehensive algebra assessment', 45, 75, 2, NOW()),
('quiz-003', 'course-004', 'Physics Laws Quiz', 'Quiz on Newton\'s Laws of Motion', 25, 70, 3, NOW());

-- 12. Insert Quiz Questions
INSERT INTO quiz_questions (id, quiz_id, question_text, type, options, correct_answer, points, explanation, order_index) VALUES
('q-001', 'quiz-001', 'What is the correct way to create a variable in Python?', 'multiple_choice', '["x = 5", "var x = 5", "int x = 5", "x := 5"]', 'x = 5', 10, 'In Python, variables are created using simple assignment.', 1),
('q-002', 'quiz-001', 'Which data type is used to store text in Python?', 'multiple_choice', '["int", "str", "float", "bool"]', 'str', 10, 'String (str) is used for text data.', 2),
('q-003', 'quiz-002', 'Solve: 2x + 5 = 15', 'short_answer', NULL, '5', 15, 'Subtract 5 from both sides, then divide by 2.', 1);

-- 13. Insert Quiz Attempts
INSERT INTO quiz_attempts (id, quiz_id, student_id, started_at, submitted_at, score, passed, answers) VALUES
('attempt-001', 'quiz-001', 'student-001', DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 5 DAY), 90.00, 1, '{"q-001": "x = 5", "q-002": "str"}'),
('attempt-002', 'quiz-001', 'student-002', DATE_SUB(NOW(), INTERVAL 6 DAY), DATE_SUB(NOW(), INTERVAL 6 DAY), 75.00, 1, '{"q-001": "x = 5", "q-002": "int"}'),
('attempt-003', 'quiz-002', 'student-001', DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY), 82.00, 1, '{"q-003": "5"}');

-- 14. Insert Essays
INSERT INTO essays (id, course_id, title, question, word_limit, due_date, difficulty, points, created_at) VALUES
('essay-001', 'course-005', 'Shakespeare Analysis', 'Analyze the theme of revenge in Hamlet', 1500, DATE_ADD(NOW(), INTERVAL 14 DAY), 'medium', 100, NOW()),
('essay-002', 'course-005', 'Modern Literature Essay', 'Compare two contemporary novels of your choice', 2000, DATE_ADD(NOW(), INTERVAL 21 DAY), 'hard', 150, NOW());

-- 15. Insert Essay Submissions
INSERT INTO essay_submissions (id, essay_id, student_id, content, word_count, submitted_at, status, grade, feedback, draft_saved_at) VALUES
('essay-sub-001', 'essay-001', 'student-003', 'The theme of revenge in Hamlet is central to the play...', 1450, DATE_SUB(NOW(), INTERVAL 1 DAY), 'submitted', NULL, NULL, DATE_SUB(NOW(), INTERVAL 3 DAY));

-- 16. Insert Grades
INSERT INTO grades (id, student_id, course_id, item_type, item_id, grade, points_earned, points_possible, letter_grade, graded_by, graded_at) VALUES
('grade-001', 'student-001', 'course-001', 'assignment', 'assign-001', 92.00, 92.00, 100.00, 'A', 'teacher-001', DATE_SUB(NOW(), INTERVAL 1 DAY)),
('grade-002', 'student-002', 'course-001', 'assignment', 'assign-001', 85.50, 85.50, 100.00, 'B', 'teacher-001', DATE_SUB(NOW(), INTERVAL 1 DAY)),
('grade-003', 'student-001', 'course-001', 'quiz', 'quiz-001', 90.00, 18.00, 20.00, 'A', 'teacher-001', DATE_SUB(NOW(), INTERVAL 5 DAY)),
('grade-004', 'student-002', 'course-001', 'quiz', 'quiz-001', 75.00, 15.00, 20.00, 'C', 'teacher-001', DATE_SUB(NOW(), INTERVAL 6 DAY));

-- 17. Insert Attendance
INSERT INTO attendance (id, course_id, student_id, date, status, check_in_time, notes, marked_by, marked_at) VALUES
('attend-001', 'course-001', 'student-001', DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'present', '09:00:00', NULL, 'teacher-001', DATE_SUB(NOW(), INTERVAL 1 DAY)),
('attend-002', 'course-001', 'student-002', DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'present', '09:05:00', 'Late arrival', 'teacher-001', DATE_SUB(NOW(), INTERVAL 1 DAY)),
('attend-003', 'course-003', 'student-001', DATE_SUB(CURDATE(), INTERVAL 2 DAY), 'present', '10:00:00', NULL, 'teacher-002', DATE_SUB(NOW(), INTERVAL 2 DAY)),
('attend-004', 'course-003', 'student-004', DATE_SUB(CURDATE(), INTERVAL 2 DAY), 'absent', NULL, 'Medical leave', 'teacher-002', DATE_SUB(NOW(), INTERVAL 2 DAY));

-- 18. Insert Calendar Events
INSERT INTO calendar_events (id, course_id, creator_id, title, description, type, start_time, end_time, location) VALUES
('event-001', 'course-001', 'teacher-001', 'Python Workshop', 'Hands-on Python coding workshop', 'class', DATE_ADD(NOW(), INTERVAL 3 DAY), DATE_ADD(NOW(), INTERVAL 3 DAY) + INTERVAL 2 HOUR, 'Room 101'),
('event-002', 'course-003', 'teacher-002', 'Algebra Exam', 'Mid-term algebra examination', 'exam', DATE_ADD(NOW(), INTERVAL 7 DAY), DATE_ADD(NOW(), INTERVAL 7 DAY) + INTERVAL 2 HOUR, 'Exam Hall'),
('event-003', NULL, 'teacher-001', 'Staff Meeting', 'Monthly staff meeting', 'meeting', DATE_ADD(NOW(), INTERVAL 2 DAY), DATE_ADD(NOW(), INTERVAL 2 DAY) + INTERVAL 1 HOUR, 'Conference Room');

-- 19. Insert Forum Threads
INSERT INTO forum_threads (id, course_id, author_id, title, content, category, is_pinned, is_resolved, views, created_at, updated_at) VALUES
('thread-001', 'course-001', 'student-001', 'Help with loops exercise', 'I am having trouble understanding nested loops. Can someone explain?', 'question', 0, 1, 25, DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY)),
('thread-002', 'course-001', 'teacher-001', 'Course Announcement', 'Next class will cover functions and modules', 'general', 1, 0, 45, DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)),
('thread-003', 'course-003', 'student-004', 'Study Group', 'Looking for students to form an algebra study group', 'general', 0, 0, 15, DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY));

-- 20. Insert Forum Replies
INSERT INTO forum_replies (id, thread_id, parent_reply_id, author_id, content, is_answer, created_at, updated_at) VALUES
('reply-001', 'thread-001', NULL, 'student-002', 'Nested loops work by having one loop inside another. Let me give you an example...', 0, DATE_SUB(NOW(), INTERVAL 4 DAY), DATE_SUB(NOW(), INTERVAL 4 DAY)),
('reply-002', 'thread-001', NULL, 'teacher-001', 'Great question! Think of nested loops like a grid. The outer loop controls rows, inner loop controls columns.', 1, DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY)),
('reply-003', 'thread-003', NULL, 'student-001', 'I would like to join! When are you planning to meet?', 0, DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY));

-- 21. Insert Messages
INSERT INTO messages (id, sender_id, recipient_id, conversation_id, content, is_read, read_at) VALUES
('msg-001', 'student-001', 'teacher-001', 'conv-001', 'Hello Professor, I have a question about the assignment.', 1, DATE_SUB(NOW(), INTERVAL 2 DAY)),
('msg-002', 'teacher-001', 'student-001', 'conv-001', 'Sure, what would you like to know?', 1, DATE_SUB(NOW(), INTERVAL 2 DAY)),
('msg-003', 'parent-001', 'teacher-002', 'conv-002', 'How is Alice performing in mathematics?', 1, DATE_SUB(NOW(), INTERVAL 1 DAY)),
('msg-004', 'teacher-002', 'parent-001', 'conv-002', 'Alice is doing very well! She scored 92% on the recent quiz.', 0, NULL);

-- 22. Insert Notifications
INSERT INTO notifications (id, user_id, type, title, message, link, is_read) VALUES
('notif-001', 'student-001', 'grade', 'New Grade Posted', 'Your assignment has been graded: 92/100', '/grades/grade-001', 1),
('notif-002', 'student-002', 'assignment', 'Assignment Due Soon', 'Python Variables Exercise is due in 2 days', '/assignments/assign-001', 0),
('notif-003', 'student-001', 'announcement', 'Course Update', 'New lesson available in Python Programming', '/courses/course-001', 1),
('notif-004', 'teacher-001', 'submission', 'New Submission', 'Bob Davis submitted Assignment: Python Variables Exercise', '/submissions/submit-002', 1);

-- 23. Insert Resources
INSERT INTO resources (id, course_id, uploaded_by, title, type, url, description, file_size, downloads, uploaded_at) VALUES
('res-001', 'course-001', 'teacher-001', 'Python Cheat Sheet', 'document', 'https://storage.retinify.com/resources/python-cheat-sheet.pdf', 'Quick reference guide for Python syntax', 524288, 45, DATE_SUB(NOW(), INTERVAL 10 DAY)),
('res-002', 'course-001', 'teacher-001', 'Sample Code Repository', 'link', 'https://github.com/retinify/python-examples', 'GitHub repository with example code', NULL, 32, DATE_SUB(NOW(), INTERVAL 15 DAY)),
('res-003', 'course-003', 'teacher-002', 'Algebra Formula Sheet', 'document', 'https://storage.retinify.com/resources/algebra-formulas.pdf', 'All important algebra formulas', 256000, 67, DATE_SUB(NOW(), INTERVAL 20 DAY));

-- 24. Insert Performance Trends
INSERT INTO performance_trends (id, student_id, date, score, course_id, created_at, updated_at) VALUES
('perf-001', 'student-001', DATE_SUB(CURDATE(), INTERVAL 30 DAY), 78.50, 'course-001', NOW(), NOW()),
('perf-002', 'student-001', DATE_SUB(CURDATE(), INTERVAL 23 DAY), 82.00, 'course-001', NOW(), NOW()),
('perf-003', 'student-001', DATE_SUB(CURDATE(), INTERVAL 16 DAY), 85.50, 'course-001', NOW(), NOW()),
('perf-004', 'student-001', DATE_SUB(CURDATE(), INTERVAL 9 DAY), 88.75, 'course-001', NOW(), NOW()),
('perf-005', 'student-001', DATE_SUB(CURDATE(), INTERVAL 2 DAY), 92.00, 'course-001', NOW(), NOW()),
('perf-006', 'student-002', DATE_SUB(CURDATE(), INTERVAL 28 DAY), 70.00, 'course-004', NOW(), NOW()),
('perf-007', 'student-002', DATE_SUB(CURDATE(), INTERVAL 14 DAY), 75.00, 'course-004', NOW(), NOW()),
('perf-008', 'student-002', DATE_SUB(CURDATE(), INTERVAL 7 DAY), 78.50, 'course-004', NOW(), NOW());

-- 25. Insert Weekly Activities
INSERT INTO weekly_activities (id, student_id, date, day_of_week, hours_studied, assignments_completed, quizzes_completed, lessons_viewed, created_at, updated_at) VALUES
('activity-001', 'student-001', DATE_SUB(CURDATE(), INTERVAL 6 DAY), 'Monday', 3.50, 1, 0, 2, NOW(), NOW()),
('activity-002', 'student-001', DATE_SUB(CURDATE(), INTERVAL 5 DAY), 'Tuesday', 2.75, 0, 1, 1, NOW(), NOW()),
('activity-003', 'student-001', DATE_SUB(CURDATE(), INTERVAL 4 DAY), 'Wednesday', 4.00, 1, 0, 3, NOW(), NOW()),
('activity-004', 'student-001', DATE_SUB(CURDATE(), INTERVAL 3 DAY), 'Thursday', 2.00, 0, 0, 1, NOW(), NOW()),
('activity-005', 'student-001', DATE_SUB(CURDATE(), INTERVAL 2 DAY), 'Friday', 3.25, 1, 1, 2, NOW(), NOW()),
('activity-006', 'student-002', DATE_SUB(CURDATE(), INTERVAL 6 DAY), 'Monday', 2.50, 1, 0, 1, NOW(), NOW()),
('activity-007', 'student-002', DATE_SUB(CURDATE(), INTERVAL 5 DAY), 'Tuesday', 3.00, 0, 1, 2, NOW(), NOW());

-- 26. Insert Student Skills
INSERT INTO student_skills (id, student_id, skill_name, skill_value, last_assessed, course_id, created_at, updated_at) VALUES
('skill-001', 'student-001', 'Problem Solving', 88.50, DATE_SUB(CURDATE(), INTERVAL 5 DAY), 'course-001', NOW(), NOW()),
('skill-002', 'student-001', 'Critical Thinking', 85.00, DATE_SUB(CURDATE(), INTERVAL 5 DAY), 'course-001', NOW(), NOW()),
('skill-003', 'student-001', 'Code Quality', 90.00, DATE_SUB(CURDATE(), INTERVAL 3 DAY), 'course-001', NOW(), NOW()),
('skill-004', 'student-002', 'Mathematical Reasoning', 82.50, DATE_SUB(CURDATE(), INTERVAL 7 DAY), 'course-003', NOW(), NOW()),
('skill-005', 'student-003', 'Creativity', 92.00, DATE_SUB(CURDATE(), INTERVAL 4 DAY), 'course-002', NOW(), NOW());

-- 27. Insert Subject Marks
INSERT INTO subject_marks (id, student_id, subject_name, score, max_score, assessment_type, assessment_date, course_id, created_at, updated_at) VALUES
('mark-001', 'student-001', 'Python Programming', 92.00, 100.00, 'Assignment', DATE_SUB(CURDATE(), INTERVAL 2 DAY), 'course-001', NOW(), NOW()),
('mark-002', 'student-001', 'Python Programming', 90.00, 100.00, 'Quiz', DATE_SUB(CURDATE(), INTERVAL 5 DAY), 'course-001', NOW(), NOW()),
('mark-003', 'student-001', 'Mathematics', 88.00, 100.00, 'Test', DATE_SUB(CURDATE(), INTERVAL 10 DAY), 'course-003', NOW(), NOW()),
('mark-004', 'student-002', 'Python Programming', 85.50, 100.00, 'Assignment', DATE_SUB(CURDATE(), INTERVAL 3 DAY), 'course-001', NOW(), NOW()),
('mark-005', 'student-002', 'Physics', 78.00, 100.00, 'Lab Report', DATE_SUB(CURDATE(), INTERVAL 8 DAY), 'course-004', NOW(), NOW());

-- 28. Insert Improvement Areas
INSERT INTO improvement_areas (id, student_id, subject_name, reason, suggestion, priority, status, course_id, identified_date, resolved_date, created_at, updated_at) VALUES
('improve-001', 'student-002', 'Python Programming', 'Difficulty with loop concepts', 'Review nested loops tutorial and practice more exercises', 'high', 'active', 'course-001', DATE_SUB(CURDATE(), INTERVAL 5 DAY), NULL, NOW(), NOW()),
('improve-002', 'student-004', 'Physics', 'Lab report writing needs improvement', 'Attend writing workshop and review sample reports', 'medium', 'active', 'course-004', DATE_SUB(CURDATE(), INTERVAL 8 DAY), NULL, NOW(), NOW()),
('improve-003', 'student-001', 'Mathematics', 'Minor calculation errors', 'Double-check calculations and use calculator', 'low', 'resolved', 'course-003', DATE_SUB(CURDATE(), INTERVAL 15 DAY), DATE_SUB(CURDATE(), INTERVAL 3 DAY), NOW(), NOW());

-- 29. Insert Teacher Stats
INSERT INTO teacher_stats (id, teacher_id, snapshot_date, total_courses, total_students, pending_grading, upcoming_classes, avg_feedback_rating, avg_grade, enrollments_today, assignments_submitted_today, created_at) VALUES
('tstat-001', 'teacher-001', CURDATE(), 2, 8, 3, 2, 4.5, 87.50, 0, 1, NOW()),
('tstat-002', 'teacher-002', CURDATE(), 2, 6, 1, 3, 4.7, 85.25, 1, 0, NOW()),
('tstat-003', 'teacher-003', CURDATE(), 1, 2, 0, 1, 4.8, 88.00, 0, 0, NOW()),
('tstat-004', 'teacher-001', DATE_SUB(CURDATE(), INTERVAL 1 DAY), 2, 7, 5, 2, 4.5, 86.75, 1, 2, DATE_SUB(NOW(), INTERVAL 1 DAY)),
('tstat-005', 'teacher-002', DATE_SUB(CURDATE(), INTERVAL 1 DAY), 2, 6, 2, 2, 4.7, 84.50, 0, 1, DATE_SUB(NOW(), INTERVAL 1 DAY));

-- 30. Insert Teacher Stats Timeseries
INSERT INTO teacher_stat_timeseries (id, teacher_id, metric_name, metric_value, timestamp) VALUES
('ts-001', 'teacher-001', 'enrollments', 1, DATE_SUB(NOW(), INTERVAL 2 HOUR)),
('ts-002', 'teacher-001', 'submissions', 2, DATE_SUB(NOW(), INTERVAL 5 HOUR)),
('ts-003', 'teacher-001', 'avg_grade', 87.5, DATE_SUB(NOW(), INTERVAL 1 DAY)),
('ts-004', 'teacher-002', 'enrollments', 1, DATE_SUB(NOW(), INTERVAL 3 HOUR)),
('ts-005', 'teacher-002', 'avg_grade', 85.25, DATE_SUB(NOW(), INTERVAL 1 DAY)),
('ts-006', 'teacher-001', 'feedback_rating', 4.5, DATE_SUB(NOW(), INTERVAL 12 HOUR)),
('ts-007', 'teacher-002', 'feedback_rating', 4.7, DATE_SUB(NOW(), INTERVAL 12 HOUR));
