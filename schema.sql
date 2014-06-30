drop table if exists graphics;
create table graphics (
  id integer primary key autoincrement,
  title text not null,
  category text not null,
  info text,
  starred integer,
  views integer
);
