-- Running upgrade  -> 0001_initial_schema

CREATE TABLE image_assets (
    id INTEGER NOT NULL, 
    object_key VARCHAR(512) NOT NULL, 
    filename VARCHAR(255) NOT NULL, 
    content_type VARCHAR(128) NOT NULL, 
    size_bytes INTEGER NOT NULL, 
    alt_text VARCHAR(500) NOT NULL, 
    created_at DATETIME NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_image_assets_object_key ON image_assets (object_key);

CREATE TABLE posts (
    id INTEGER NOT NULL, 
    slug VARCHAR(200) NOT NULL, 
    title VARCHAR(300) NOT NULL, 
    description VARCHAR(1000) NOT NULL, 
    content VARCHAR NOT NULL, 
    category VARCHAR(100) NOT NULL, 
    hero_image_key VARCHAR(512), 
    hero_image_url VARCHAR(1024) NOT NULL, 
    image_alt VARCHAR(500) NOT NULL, 
    published BOOLEAN NOT NULL, 
    pub_date DATETIME NOT NULL, 
    updated_date DATETIME, 
    created_at DATETIME NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(hero_image_key) REFERENCES image_assets (object_key)
);

CREATE INDEX ix_posts_category ON posts (category);

CREATE INDEX ix_posts_pub_date ON posts (pub_date);

CREATE INDEX ix_posts_published ON posts (published);

CREATE UNIQUE INDEX ix_posts_slug ON posts (slug);
