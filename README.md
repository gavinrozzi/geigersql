# geigersql
Store Geiger counter data in a PostgreSQL database. Based on Geigerlog and modified to store Geiger counter readings every 60 seconds.

This script expects a database with a table named "cpm" that contains the columns id(bigserial), cpm and cps (numeric).
