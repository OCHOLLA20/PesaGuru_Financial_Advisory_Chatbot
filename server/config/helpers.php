<?php

if (!function_exists('base_path')) {
    /**
     * Get the base path of the application.
     *
     * @param  string  $path
     * @return string
     */
    function base_path($path = '')
    {
        return dirname(dirname(dirname(__FILE__))) . ($path ? DIRECTORY_SEPARATOR . $path : $path);
    }
}

if (!function_exists('storage_path')) {
    /**
     * Get the storage path.
     *
     * @param  string  $path
     * @return string
     */
    function storage_path($path = '')
    {
        return base_path('storage') . ($path ? DIRECTORY_SEPARATOR . $path : $path);
    }
}

if (!function_exists('public_path')) {
    /**
     * Get the public path.
     *
     * @param  string  $path
     * @return string
     */
    function public_path($path = '')
    {
        return base_path('public') . ($path ? DIRECTORY_SEPARATOR . $path : $path);
    }
}

if (!function_exists('resource_path')) {
    /**
     * Get the resources path.
     *
     * @param  string  $path
     * @return string
     */
    function resource_path($path = '')
    {
        return base_path('resources') . ($path ? DIRECTORY_SEPARATOR . $path : $path);
    }
}

if (!function_exists('env')) {
    /**
     * Gets the value of an environment variable.
     *
     * @param  string  $key
     * @param  mixed   $default
     * @return mixed
     */
    function env($key, $default = null)
    {
        $value = getenv($key);

        if ($value === false) {
            return $default;
        }

        switch (strtolower($value)) {
            case 'true':
            case '(true)':
                return true;
            case 'false':
            case '(false)':
                return false;
            case 'empty':
            case '(empty)':
                return '';
            case 'null':
            case '(null)':
                return null;
        }

        return $value;
    }
}