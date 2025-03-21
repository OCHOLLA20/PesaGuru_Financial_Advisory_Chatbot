<?php

namespace PesaGuru\Server\Config;

use Psr\Container\ContainerInterface;
use Psr\Container\NotFoundExceptionInterface;
use Exception;

/**
 * Service Container for PesaGuru
 * 
 * Manages application dependencies and service initialization
 * Implements PSR-11 ContainerInterface for compatibility
 */
class ServiceContainer implements ContainerInterface
{
    /**
     * Service definitions
     *
     * @var array
     */
    protected $definitions = [];

    /**
     * Resolved service instances (singletons)
     *
     * @var array
     */
    protected $instances = [];

    /**
     * Register a service definition
     *
     * @param string $id Service identifier
     * @param callable|object|null $concrete Service factory or instance
     * @param bool $shared Whether the service should be a singleton
     * @return self
     */
    public function register(string $id, $concrete = null, bool $shared = true): self
    {
        // If no concrete implementation provided, use the ID as the class name
        if ($concrete === null) {
            $concrete = $id;
        }

        $this->definitions[$id] = [
            'concrete' => $concrete,
            'shared' => $shared,
        ];

        return $this;
    }

    /**
     * Register a singleton service
     *
     * @param string $id Service identifier
     * @param callable|object|null $concrete Service factory or instance
     * @return self
     */
    public function singleton(string $id, $concrete = null): self
    {
        return $this->register($id, $concrete, true);
    }

    /**
     * Register a factory service (non-singleton)
     *
     * @param string $id Service identifier
     * @param callable|object|null $concrete Service factory or instance
     * @return self
     */
    public function factory(string $id, $concrete = null): self
    {
        return $this->register($id, $concrete, false);
    }

    /**
     * Register an instance as a service
     *
     * @param string $id Service identifier
     * @param object $instance Service instance
     * @return self
     */
    public function instance(string $id, $instance): self
    {
        $this->instances[$id] = $instance;
        
        return $this;
    }

    /**
     * Check if a service is registered
     *
     * @param string $id Service identifier
     * @return bool
     */
    public function has($id): bool
    {
        return isset($this->definitions[$id]) || isset($this->instances[$id]);
    }

    /**
     * Get a service from the container
     *
     * @param string $id Service identifier
     * @return mixed
     * @throws Exception If service not found
     */
    public function get($id)
    {
        // Return from instances if already resolved
        if (isset($this->instances[$id])) {
            return $this->instances[$id];
        }

        // Check if the service is defined
        if (!isset($this->definitions[$id])) {
            throw new class("Service not found: $id") extends Exception implements NotFoundExceptionInterface {};
        }

        $definition = $this->definitions[$id];
        $concrete = $definition['concrete'];
        $shared = $definition['shared'];

        // Resolve the service
        $instance = $this->resolve($concrete);

        // If shared (singleton), store the instance
        if ($shared) {
            $this->instances[$id] = $instance;
        }

        return $instance;
    }

    /**
     * Resolve a service definition into an instance
     *
     * @param mixed $concrete Service definition
     * @return mixed Resolved service
     */
    protected function resolve($concrete)
    {
        // If the concrete is a closure or callable, call it with the container
        if (is_callable($concrete) && !is_string($concrete)) {
            return $concrete($this);
        }

        // If it's already an object, return it
        if (is_object($concrete) && !is_callable($concrete)) {
            return $concrete;
        }

        // If it's a string, assume it's a class name and instantiate it
        if (is_string($concrete) && class_exists($concrete)) {
            return $this->buildFromClass($concrete);
        }

        // If we got here, we don't know how to resolve this
        throw new Exception("Cannot resolve service: " . (is_string($concrete) ? $concrete : gettype($concrete)));
    }

    /**
     * Instantiate a class using autowiring
     *
     * @param string $className Full class name
     * @return object Instance of the class
     * @throws Exception If class cannot be instantiated
     */
    protected function buildFromClass(string $className)
    {
        $reflector = new \ReflectionClass($className);

        // Check if the class can be instantiated
        if (!$reflector->isInstantiable()) {
            throw new Exception("Class $className is not instantiable");
        }

        // Get the constructor
        $constructor = $reflector->getConstructor();

        // If no constructor or no parameters, just instantiate without args
        if ($constructor === null || count($constructor->getParameters()) === 0) {
            return new $className();
        }

        // Otherwise, resolve constructor parameters
        $parameters = $constructor->getParameters();
        $dependencies = [];

        foreach ($parameters as $parameter) {
            $type = $parameter->getType();
            
            // If the parameter has a class type hint, try to resolve it from the container
            if ($type && !$type->isBuiltin()) {
                $dependencies[] = $this->get($type->getName());
            } 
            // If the parameter has a default value, use it
            elseif ($parameter->isDefaultValueAvailable()) {
                $dependencies[] = $parameter->getDefaultValue();
            } 
            // Otherwise, we can't resolve this parameter
            else {
                throw new Exception("Cannot resolve parameter {$parameter->getName()} of class $className");
            }
        }

        // Instantiate the class with the resolved dependencies
        return $reflector->newInstanceArgs($dependencies);
    }

    /**
     * Clear all singleton instances
     *
     * @return self
     */
    public function clearInstances(): self
    {
        $this->instances = [];
        
        return $this;
    }
}