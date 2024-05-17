insert into parasun_rental (parasun_id, expiration_time) values
(%s, null) returning id;