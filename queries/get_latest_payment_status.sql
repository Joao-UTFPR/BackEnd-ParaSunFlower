select status from payment where created_at = (select max(created_at) from payment where rental_id = '%s')