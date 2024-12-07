CREATE DATABASE IF NOT EXISTS recipeapp;


USE recipeapp;


DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS recipes;
DROP TABLE IF EXISTS allergies;


CREATE TABLE users
(
    userid       int not null AUTO_INCREMENT,
    firstname    varchar(64) not null,
    lastname     varchar(64) not null,
    PRIMARY KEY  (userid)
);


ALTER TABLE users AUTO_INCREMENT = 80001;  -- starting value


CREATE TABLE recipes
(
    mealdbid     int not null,
    recipename   varchar(256) not null, 
    assetname    varchar(256) not null,  -- results filename in S3 bucket
    recipeid     int not null AUTO_INCREMENT,
    PRIMARY KEY (recipeid)
    -- FOREIGN KEY (userid) REFERENCES users(userid),
);


ALTER TABLE recipes AUTO_INCREMENT = 1001;  -- starting value

CREATE TABLE allergies
(
    allergyid      int not null AUTO_INCREMENT,
    allergyname    varchar(256) not null, 
    userid         int not null,
    PRIMARY KEY (allergyid),
    FOREIGN KEY (userid) REFERENCES users(userid)
);


ALTER TABLE allergies AUTO_INCREMENT = 101;  -- starting value


--
-- Insert some users to start with:
-- 
-- PWD hashing: https://phppasswordhash.com/
--


--
-- creating user accounts for database access:
--
-- ref: https://dev.mysql.com/doc/refman/8.0/en/create-user.html
--


DROP USER IF EXISTS 'recipeapp-read-only';
DROP USER IF EXISTS 'recipeapp-read-write';


CREATE USER 'recipeapp-read-only' IDENTIFIED BY 'abc123!!';
CREATE USER 'recipeapp-read-write' IDENTIFIED BY 'def456!!';


GRANT SELECT, SHOW VIEW ON recipeapp.* 
      TO 'recipeapp-read-only';
GRANT SELECT, SHOW VIEW, INSERT, UPDATE, DELETE, DROP, CREATE, ALTER ON recipeapp.* 
      TO 'recipeapp-read-write';
      
FLUSH PRIVILEGES;


--
-- done
--
