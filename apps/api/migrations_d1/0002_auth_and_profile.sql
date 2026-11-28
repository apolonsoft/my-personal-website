-- Running upgrade 0001_initial_schema -> 0002_auth_and_profile

CREATE TABLE users (
    id INTEGER NOT NULL, 
    email VARCHAR(255) NOT NULL, 
    password_hash VARCHAR(512) NOT NULL, 
    role VARCHAR(32) NOT NULL, 
    is_active BOOLEAN NOT NULL, 
    full_name VARCHAR(200) NOT NULL, 
    headline VARCHAR(300) NOT NULL, 
    bio VARCHAR(4000) NOT NULL, 
    avatar_key VARCHAR(512), 
    avatar_url VARCHAR(1024) NOT NULL, 
    social_links_json VARCHAR(4000) NOT NULL, 
    created_at DATETIME NOT NULL, 
    updated_at DATETIME NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(avatar_key) REFERENCES image_assets (object_key)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE INDEX ix_users_is_active ON users (is_active);

CREATE TABLE password_reset_tokens (
    id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    token_hash VARCHAR(64) NOT NULL, 
    expires_at DATETIME NOT NULL, 
    used_at DATETIME, 
    created_at DATETIME NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_password_reset_tokens_expires_at ON password_reset_tokens (expires_at);

CREATE UNIQUE INDEX ix_password_reset_tokens_token_hash ON password_reset_tokens (token_hash);

CREATE INDEX ix_password_reset_tokens_user_id ON password_reset_tokens (user_id);
