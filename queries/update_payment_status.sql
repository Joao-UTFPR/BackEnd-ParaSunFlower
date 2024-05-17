update payment
set status = '%s', paid_at = %s
where id = (
select id from payment where rental_id = %d and created_at =
                                                (select max(created_at) from payment where rental_id = %d))
returning time, status;