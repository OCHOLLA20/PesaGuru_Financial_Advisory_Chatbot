# Use the official PHP image with FPM
FROM php:7.4-fpm

# Set the working directory
WORKDIR /var/www/html

# Copy the existing application directory contents
COPY . .

# Install any necessary PHP extensions
RUN docker-php-ext-install pdo pdo_mysql

# Expose the port the app runs on
EXPOSE 9000
