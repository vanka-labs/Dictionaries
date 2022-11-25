create table fks_table
(
    fk_id           INTEGER     not null
        primary key autoincrement,
    parent_table    varchar(20) not null,
    child_table     varchar(20) not null,
    child_key_name  varchar(20) not null,
    parent_key_name varchar(20) not null,
    additional_info varchar(20)
);

create table города
(
    id                 INTEGER        not null
        primary key autoincrement,
    год_основания      INT            not null,
    город              varchar(20)    not null,
    количество_жителей decimal(10, 6) not null,
    страна             varchar(20)    not null,
    deleted            INT default 0,
    check ((год_основания > 0 AND год_основания < 2100) AND (страна != '') AND
           (количество_жителей > 0 AND количество_жителей < 1000) AND (город != ''))
);

create table университеты
(
    id                   INTEGER        not null
        primary key autoincrement,
    city_id              INT            not null
        constraint table2_fk
            references города,
    дата_основания       date           not null,
    название             varchar(20)    not null,
    количество_студентов decimal(10, 3) not null,
    deleted              INT default 0,
    check ((название != '') AND (количество_студентов > 0 AND количество_студентов < 100) AND
           (date('1700-01-01') < дата_основания AND дата_основания < current_date))
);



INSERT INTO университеты (id, city_id, дата_основания, название, количество_студентов, deleted) VALUES (1, 1, '1921-10-31', 'BSU', 44.877, 0)
INSERT INTO города (id, год_основания, город, количество_жителей, страна, deleted) VALUES (1, 1066, 'Минск', 'Беларусь', 1.996556, 0)

