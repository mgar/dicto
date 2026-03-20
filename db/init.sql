-- Ensure UTF-8 encoding
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  display_name VARCHAR(255) NOT NULL,
  is_admin TINYINT(1) NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
  daily_new_limit INT NULL,
  content_preference VARCHAR(20) NULL,
  selected_levels TEXT NULL,
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sessions (
  id CHAR(36) NOT NULL PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP NOT NULL,
  INDEX idx_sessions_user_id (user_id),
  INDEX idx_sessions_expires_at (expires_at),
  CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================
-- Grammar Points
-- =========================
CREATE TABLE IF NOT EXISTS grammar_points (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  level VARCHAR(10) NOT NULL,
  slug VARCHAR(255) NOT NULL UNIQUE,
  title VARCHAR(255) NOT NULL,
  short_description VARCHAR(512) NOT NULL,
  structure TEXT NULL,              -- JSON array of structure patterns, e.g. ["Noun + ser", "Adjective + ser"]
  explanation TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================
-- Grammar Examples
-- =========================
CREATE TABLE IF NOT EXISTS grammar_examples (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  grammar_point_id BIGINT UNSIGNED NOT NULL,
  sentence VARCHAR(1024) NOT NULL,
  translation VARCHAR(1024) NOT NULL,
  highlight VARCHAR(255) NULL,       -- the part to highlight in the sentence
  notes VARCHAR(512) NULL,
  sort_order INT NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_grammar_examples_gp (grammar_point_id),
  CONSTRAINT fk_grammar_examples_gp FOREIGN KEY (grammar_point_id) REFERENCES grammar_points(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================
-- Vocabulary Items (independent from grammar)
-- =========================
CREATE TABLE IF NOT EXISTS vocab_items (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  level VARCHAR(10) NOT NULL,
  word VARCHAR(255) NOT NULL,
  translation VARCHAR(255) NOT NULL,
  part_of_speech VARCHAR(32) NULL,  -- noun, verb, adjective, etc.
  gender VARCHAR(10) NULL,           -- m, f, n (for nouns)
  example_sentence VARCHAR(1024) NULL,
  example_translation VARCHAR(1024) NULL,
  notes VARCHAR(1024) NULL,
  tags VARCHAR(512) NULL,            -- comma-separated: "food,kitchen,daily"
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_vocab_level (level),
  INDEX idx_vocab_word (word)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================
-- Prompts (cloze exercises)
-- =========================
CREATE TABLE IF NOT EXISTS prompts (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  grammar_point_id BIGINT UNSIGNED NULL,
  vocab_item_id BIGINT UNSIGNED NULL,
  kind VARCHAR(16) NOT NULL DEFAULT 'grammar',  -- 'grammar' or 'vocab'
  sentence VARCHAR(1024) NOT NULL,
  notes VARCHAR(1024) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_prompts_gp (grammar_point_id),
  INDEX idx_prompts_vocab (vocab_item_id),
  INDEX idx_prompts_kind (kind),
  CONSTRAINT fk_prompts_gp FOREIGN KEY (grammar_point_id) REFERENCES grammar_points(id) ON DELETE CASCADE,
  CONSTRAINT fk_prompts_vocab FOREIGN KEY (vocab_item_id) REFERENCES vocab_items(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS prompt_answers (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  prompt_id BIGINT UNSIGNED NOT NULL,
  answer VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_prompt_answers_prompt (prompt_id),
  CONSTRAINT fk_prompt_answers_prompt FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================
-- Review state + logs
-- =========================
CREATE TABLE IF NOT EXISTS review_state (
  user_id BIGINT UNSIGNED NOT NULL,
  prompt_id BIGINT UNSIGNED NOT NULL,
  ease_factor DOUBLE NOT NULL,
  interval_days INT NOT NULL,
  repetitions INT NOT NULL,
  due_at DATETIME NOT NULL,
  last_reviewed_at DATETIME NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'reviewing',
  PRIMARY KEY (user_id, prompt_id),
  INDEX idx_review_state_due (user_id, due_at),
  CONSTRAINT fk_review_state_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_review_state_prompt FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS review_log (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  prompt_id BIGINT UNSIGNED NOT NULL,
  answered_at DATETIME NOT NULL,
  local_date DATE NULL,
  user_answer VARCHAR(255) NOT NULL,
  grade TINYINT NOT NULL,
  is_correct BOOLEAN NOT NULL,
  missing_accent BOOLEAN NOT NULL DEFAULT FALSE,
  spacing_normalized BOOLEAN NOT NULL DEFAULT FALSE,
  expected_answer VARCHAR(255) NULL,
  INDEX idx_review_log_user_time (user_id, answered_at),
  INDEX idx_review_log_local_date (user_id, local_date),
  CONSTRAINT fk_review_log_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_review_log_prompt FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

