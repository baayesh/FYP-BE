CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> add_student_performance

CREATE TABLE performance_trends (
    id VARCHAR(36) NOT NULL, 
    student_id VARCHAR(36) NOT NULL, 
    date DATE NOT NULL, 
    score NUMERIC(5, 2) NOT NULL, 
    course_id VARCHAR(36), 
    created_at DATETIME DEFAULT now(), 
    updated_at DATETIME DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(student_id) REFERENCES users (id) ON DELETE CASCADE, 
    FOREIGN KEY(course_id) REFERENCES courses (id) ON DELETE SET NULL
);

CREATE INDEX ix_performance_trends_date ON performance_trends (date);

CREATE INDEX ix_performance_trends_student_id ON performance_trends (student_id);

CREATE TABLE weekly_activities (
    id VARCHAR(36) NOT NULL, 
    student_id VARCHAR(36) NOT NULL, 
    date DATE NOT NULL, 
    day_of_week VARCHAR(10) NOT NULL, 
    hours_studied NUMERIC(4, 2) DEFAULT '0.0', 
    assignments_completed INTEGER DEFAULT '0', 
    quizzes_completed INTEGER DEFAULT '0', 
    lessons_viewed INTEGER DEFAULT '0', 
    created_at DATETIME DEFAULT now(), 
    updated_at DATETIME DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(student_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_weekly_activities_date ON weekly_activities (date);

CREATE INDEX ix_weekly_activities_student_id ON weekly_activities (student_id);

CREATE TABLE student_skills (
    id VARCHAR(36) NOT NULL, 
    student_id VARCHAR(36) NOT NULL, 
    skill_name VARCHAR(100) NOT NULL, 
    skill_value NUMERIC(5, 2) NOT NULL, 
    last_assessed DATE NOT NULL, 
    course_id VARCHAR(36), 
    created_at DATETIME DEFAULT now(), 
    updated_at DATETIME DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(student_id) REFERENCES users (id) ON DELETE CASCADE, 
    FOREIGN KEY(course_id) REFERENCES courses (id) ON DELETE SET NULL
);

CREATE INDEX ix_student_skills_student_id ON student_skills (student_id);

CREATE TABLE student_levels (
    id VARCHAR(36) NOT NULL, 
    student_id VARCHAR(36) NOT NULL, 
    grade VARCHAR(50) NOT NULL, 
    stream VARCHAR(50), 
    overall_progress NUMERIC(5, 2) DEFAULT '0.0', 
    academic_year VARCHAR(20), 
    created_at DATETIME DEFAULT now(), 
    updated_at DATETIME DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(student_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_student_levels_student_id ON student_levels (student_id);

CREATE TABLE subject_marks (
    id VARCHAR(36) NOT NULL, 
    student_id VARCHAR(36) NOT NULL, 
    subject_name VARCHAR(100) NOT NULL, 
    score NUMERIC(5, 2) NOT NULL, 
    max_score NUMERIC(5, 2) DEFAULT '100.0', 
    assessment_type VARCHAR(50), 
    assessment_date DATE NOT NULL, 
    course_id VARCHAR(36), 
    created_at DATETIME DEFAULT now(), 
    updated_at DATETIME DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(student_id) REFERENCES users (id) ON DELETE CASCADE, 
    FOREIGN KEY(course_id) REFERENCES courses (id) ON DELETE SET NULL
);

CREATE INDEX ix_subject_marks_student_id ON subject_marks (student_id);

CREATE TABLE improvement_areas (
    id VARCHAR(36) NOT NULL, 
    student_id VARCHAR(36) NOT NULL, 
    subject_name VARCHAR(100) NOT NULL, 
    reason TEXT NOT NULL, 
    suggestion TEXT NOT NULL, 
    priority VARCHAR(20) DEFAULT 'medium', 
    status VARCHAR(20) DEFAULT 'active', 
    course_id VARCHAR(36), 
    identified_date DATE NOT NULL, 
    resolved_date DATE, 
    created_at DATETIME DEFAULT now(), 
    updated_at DATETIME DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(student_id) REFERENCES users (id) ON DELETE CASCADE, 
    FOREIGN KEY(course_id) REFERENCES courses (id) ON DELETE SET NULL
);

CREATE INDEX ix_improvement_areas_student_id ON improvement_areas (student_id);

INSERT INTO alembic_version (version_num) VALUES ('add_student_performance');

-- Running upgrade add_student_performance -> ab1cd4348e15

ALTER TABLE courses ADD COLUMN level VARCHAR(50);

ALTER TABLE courses ADD COLUMN duration VARCHAR(50);

UPDATE alembic_version SET version_num='ab1cd4348e15' WHERE alembic_version.version_num = 'add_student_performance';

-- Running upgrade ab1cd4348e15 -> fix_teacher_id_type

ALTER TABLE course_enrollments DROP FOREIGN KEY course_enrollments_ibfk_2;

ALTER TABLE courses MODIFY teacher_id VARCHAR(36) NULL;

ALTER TABLE course_enrollments MODIFY student_id VARCHAR(36) NOT NULL;

ALTER TABLE courses ADD CONSTRAINT fk_courses_teacher_id FOREIGN KEY(teacher_id) REFERENCES users (id) ON DELETE CASCADE;

ALTER TABLE course_enrollments ADD CONSTRAINT fk_course_enrollments_student_id FOREIGN KEY(student_id) REFERENCES users (id) ON DELETE CASCADE;

ALTER TABLE course_enrollments ADD CONSTRAINT fk_course_enrollments_course_id FOREIGN KEY(course_id) REFERENCES courses (id) ON DELETE CASCADE;

UPDATE alembic_version SET version_num='fix_teacher_id_type' WHERE alembic_version.version_num = 'ab1cd4348e15';

-- Running upgrade fix_teacher_id_type -> ef17fdf2e3b0

ALTER TABLE lessons ADD COLUMN description TEXT;

ALTER TABLE lessons ADD COLUMN status VARCHAR(20);

ALTER TABLE lessons ADD COLUMN duration_text VARCHAR(50);

ALTER TABLE lessons ADD COLUMN quizzes_json JSON;

ALTER TABLE lessons ADD COLUMN assignments_json JSON;

UPDATE alembic_version SET version_num='ef17fdf2e3b0' WHERE alembic_version.version_num = 'fix_teacher_id_type';

-- Running upgrade ef17fdf2e3b0 -> 31748d11b4d1

ALTER TABLE lessons ADD COLUMN video_link VARCHAR(500);

UPDATE alembic_version SET version_num='31748d11b4d1' WHERE alembic_version.version_num = 'ef17fdf2e3b0';

-- Running upgrade 31748d11b4d1 -> 457857de2395

ALTER TABLE lessons ADD COLUMN video_link VARCHAR(500);

UPDATE alembic_version SET version_num='457857de2395' WHERE alembic_version.version_num = '31748d11b4d1';

-- Running upgrade 457857de2395 -> b7a2d3c4e5f6

CREATE TABLE teacher_stats (
    id VARCHAR(36) NOT NULL, 
    teacher_id VARCHAR(36) NOT NULL, 
    snapshot_date DATE NOT NULL, 
    total_courses INTEGER NOT NULL DEFAULT '0', 
    total_students INTEGER NOT NULL DEFAULT '0', 
    pending_grading INTEGER NOT NULL DEFAULT '0', 
    upcoming_classes INTEGER NOT NULL DEFAULT '0', 
    avg_feedback_rating FLOAT NOT NULL DEFAULT '0', 
    avg_grade FLOAT NOT NULL DEFAULT '0', 
    enrollments_today INTEGER NOT NULL DEFAULT '0', 
    assignments_submitted_today INTEGER NOT NULL DEFAULT '0', 
    created_at DATETIME NOT NULL DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(teacher_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_teacher_stats_snapshot_date ON teacher_stats (snapshot_date);

CREATE INDEX ix_teacher_stats_teacher_id ON teacher_stats (teacher_id);

CREATE INDEX ix_teacher_stats_id ON teacher_stats (id);

CREATE INDEX idx_teacher_stats_teacher_date ON teacher_stats (teacher_id, snapshot_date);

CREATE TABLE teacher_stat_timeseries (
    id VARCHAR(36) NOT NULL, 
    teacher_id VARCHAR(36) NOT NULL, 
    metric_name VARCHAR(50) NOT NULL, 
    metric_value FLOAT NOT NULL, 
    timestamp DATETIME NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(teacher_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_teacher_stat_timeseries_id ON teacher_stat_timeseries (id);

CREATE INDEX ix_teacher_stat_timeseries_teacher_id ON teacher_stat_timeseries (teacher_id);

CREATE INDEX ix_teacher_stat_timeseries_timestamp ON teacher_stat_timeseries (timestamp);

CREATE INDEX ix_teacher_stat_timeseries_metric_name ON teacher_stat_timeseries (metric_name);

CREATE INDEX idx_tstats_ts_teacher_metric ON teacher_stat_timeseries (teacher_id, metric_name, timestamp);

UPDATE alembic_version SET version_num='b7a2d3c4e5f6' WHERE alembic_version.version_num = '457857de2395';

