FROM php:8.0-apache 
RUN docker-php-ext-install pdo pdo_mysql 
RUN a2enmod rewrite 
COPY php.ini /usr/local/etc/php/ 
WORKDIR /var/www/html 

