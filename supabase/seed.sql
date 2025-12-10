-- Insert Mock Users
insert into app_users (username, role) values
('alice_eng', 'engineer'),
('bob_hr', 'hr'),
('charlie_intern', 'intern');

-- Note: We will ingest documents via the python/node script to generate real embeddings.
