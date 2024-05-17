insert into parasun_rental (parasun_id, expiration_time) values
(%s, '%s') returning id;