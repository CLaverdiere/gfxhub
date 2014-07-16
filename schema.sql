drop table if exists graphics;
create table graphics (
  id integer primary key autoincrement,
  title text not null,
  category text not null,
  info text DEFAULT "",
  starred integer DEFAULT 0,
  views integer DEFAULT 0, 
  created_at timestamp DEFAULT CURRENT_TIMESTAMP
);
