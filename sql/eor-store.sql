
create table files (
    id                  text                not null    primary key,  -- hex uuid
    type                text                not null,
    orig_name           text                not null,
    orig_name_sanitized text                not null,
    ext                 text                not null,
    --user_id             text                not null,                 -- who uploaded the image
    added               timestamp           not null    default current_timestamp
);
