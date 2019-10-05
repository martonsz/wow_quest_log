
-- Drop table

-- DROP TABLE public.tbl_quest;

CREATE TABLE public.tbl_quest (
	id serial NOT NULL,
	username text NOT NULL,
	quest_name text NOT NULL,
	quest_status text NOT NULL,
	quest_timestamp timestamp NOT NULL,
	quest_ignore bool NULL,
	changed timestamptz NOT NULL DEFAULT now(),
	CONSTRAINT tbl_quest_pk PRIMARY KEY (id),
	CONSTRAINT tbl_quest_un UNIQUE (username, quest_name, quest_status, quest_timestamp)
);
