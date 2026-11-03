--
CREATE TABLE user_missions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    mission_id INTEGER NOT NULL,
    current_objective_id INTEGER NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE harvest_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    mission_id INTEGER NOT NULL,
    item_id TEXT NOT NULL,
    amount INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE objectives (
    id SERIAL PRIMARY KEY,
    mission_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    is_completed BOOLEAN DEFAULT FALSE,
    requirements JSON DEFAULT '{}'
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    points INTEGER DEFAULT 0,
    is_admin BOOLEAN DEFAULT FALSE
);

CREATE TABLE missions (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    base_points INTEGER DEFAULT 0
);
