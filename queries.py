#
#
#
# def insert_entry_query(veiculo, latitude, longitude):
#     conn = psycopg2.connect(
#         "dbname=postgres user=postgres password=postgres host=localhost"
#     )
#     cur = conn.cursor()
#
#     cur.execute(
#         f"INSERT INTO entry (vehicle_id, latitude, longitude) VALUES ({veiculo}, {latitude}, {longitude})"
#     )
#     conn.commit()
#     conn.close()
#
# def get_vehicle_info_query(vehicle_id):
#     conn = psycopg2.connect(
#         "dbname=postgres user=postgres password=postgres host=localhost"
#     )
#
#     cur = conn.cursor()
#
#     cur.execute(
#         f"SELECT * FROM vehicle WHERE _id={vehicle_id}"
#     )
#     info = cur.fetchall()
#     conn.close()
#     return info
