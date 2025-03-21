FROM mysql:8.0 
RUN echo "default-character-set=utf8mb4" 
RUN echo "default-collation=utf8mb4_unicode_ci" 
COPY my-custom.cnf /etc/mysql/conf.d/ 
COPY ./init/ /docker-entrypoint-initdb.d/ 
WORKDIR /var/lib/mysql 
