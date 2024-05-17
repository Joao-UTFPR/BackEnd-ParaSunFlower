update parasun_rental
set expiration_time = greatest(now() + interval '%d' minute, (select expiration_time from parasun_rental where id = '%d')),
    updated_at = now()
where id = '%d'
returning expiration_time
