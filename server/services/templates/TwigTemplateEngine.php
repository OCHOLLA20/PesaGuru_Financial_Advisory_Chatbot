<?php

namespace PesaGuru\Server\Services\Templates;

use Twig\Environment;
use Twig\Loader\FilesystemLoader;
use Twig\Error\LoaderError;
use Twig\Error\RuntimeError;
use Twig\Error\SyntaxError;

/**
 * TwigTemplateEngine
 * 
 * Template rendering service using Twig for the PesaGuru financial advisory application.
 * Handles rendering of views for chatbot interfaces, financial dashboards, and advisory pages.
 */
class TwigTemplateEngine
{
    /**
     * @var Environment Twig environment instance
     */
    private $twig;
    
    /**
     * @var string Templates directory path
     */
    private $templatesDir;
    
    /**
     * Constructor
     * 
     * @param string $templatesDir Directory where templates are stored
     * @param array $options Twig configuration options
     */
    public function __construct(string $templatesDir = '../client/pages', array $options = [])
    {
        $this->templatesDir = $templatesDir;
        
        // Default options for PesaGuru templates
        $defaultOptions = [
            'cache' => '../cache/twig',
            'debug' => true,
            'auto_reload' => true,
            'strict_variables' => true,
        ];
        
        // Merge default options with provided options
        $options = array_merge($defaultOptions, $options);
        
        // Initialize Twig with PesaGuru templates
        $loader = new FilesystemLoader($this->templatesDir);
        $this->twig = new Environment($loader, $options);
        
        // Add PesaGuru global variables
        $this->addDefaultGlobals();
    }
    
    /**
     * Render a template with the given context
     * 
     * @param string $template Template file name (e.g., "Chatbot_Interaction/chatbot.html")
     * @param array $context Variables to pass to the template
     * @return string Rendered template
     * @throws LoaderError|RuntimeError|SyntaxError
     */
    public function render(string $template, array $context = []): string
    {
        try {
            return $this->twig->render($template, $context);
        } catch (LoaderError | RuntimeError | SyntaxError $e) {
            // Log the error for debugging
            error_log('PesaGuru Twig rendering error: ' . $e->getMessage());
            
            // In development mode, show detailed error
            if ($this->twig->isDebug()) {
                throw $e;
            }
            
            // In production, return a friendly error page
            return $this->renderErrorPage($e->getMessage());
        }
    }
    
    /**
     * Add default global variables available to all templates
     */
    private function addDefaultGlobals(): void
    {
        // Add application name
        $this->twig->addGlobal('app_name', 'PesaGuru');
        
        // Add current year for copyright notices
        $this->twig->addGlobal('current_year', date('Y'));
        
        // Add environment
        $env = getenv('APP_ENV') ?: 'development';
        $this->twig->addGlobal('environment', $env);
        
        // Add asset helper
        $this->addFunction('asset', function($path) {
            $basePath = '/assets/';
            return $basePath . ltrim($path, '/');
        });
    }
    
    /**
     * Render an error page when template rendering fails
     * 
     * @param string $errorMessage Error message
     * @return string Rendered error page
     */
    private function renderErrorPage(string $errorMessage): string
    {
        // Simple inline error template
        $errorTemplate = <<<HTML
<!DOCTYPE html>
<html>
<head>
    <title>PesaGuru - Error</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .error-container { max-width: 800px; margin: 50px auto; background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #e74c3c; }
        .support { margin-top: 30px; color: #7f8c8d; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="error-container">
        <h1>Something went wrong</h1>
        <p>We're sorry, but there was a problem rendering the page. Our team has been notified.</p>
        <div class="support">
            <p>If you need immediate assistance, please contact support.</p>
        </div>
    </div>
</body>
</html>
HTML;
        return $errorTemplate;
    }
    
    /**
     * Add a global variable to all templates
     * 
     * @param string $name Variable name
     * @param mixed $value Variable value
     */
    public function addGlobal(string $name, $value): void
    {
        $this->twig->addGlobal($name, $value);
    }
    
    /**
     * Add a custom Twig extension
     * 
     * @param \Twig\Extension\ExtensionInterface $extension
     */
    public function addExtension($extension): void
    {
        $this->twig->addExtension($extension);
    }
    
    /**
     * Add a custom Twig filter
     * 
     * @param string $name Filter name
     * @param callable $filter Filter function
     * @param array $options Filter options
     */
    public function addFilter(string $name, callable $filter, array $options = []): void
    {
        $twigFilter = new \Twig\TwigFilter($name, $filter, $options);
        $this->twig->addFilter($twigFilter);
    }
    
    /**
     * Add a custom Twig function
     * 
     * @param string $name Function name
     * @param callable $function Function callback
     * @param array $options Function options
     */
    public function addFunction(string $name, callable $function, array $options = []): void
    {
        $twigFunction = new \Twig\TwigFunction($name, $function, $options);
        $this->twig->addFunction($twigFunction);
    }
    
    /**
     * Get the underlying Twig environment
     * 
     * @return Environment Twig environment instance
     */
    public function getTwig(): Environment
    {
        return $this->twig;
    }
    
    /**
     * Add financial formatting filters specific to PesaGuru
     */
    public function addFinancialFilters(): void
    {
        // Format currency in KES
        $this->addFilter('kes', function($amount) {
            return 'KES ' . number_format($amount, 2);
        });
        
        // Format percentage values
        $this->addFilter('percent', function($value) {
            return number_format($value, 2) . '%';
        });
        
        // Format large numbers (millions, billions)
        $this->addFilter('shortNumber', function($number) {
            if ($number >= 1000000000) {
                return number_format($number / 1000000000, 2) . 'B';
            } else if ($number >= 1000000) {
                return number_format($number / 1000000, 2) . 'M';
            } else if ($number >= 1000) {
                return number_format($number / 1000, 2) . 'K';
            }
            return number_format($number, 2);
        });
    }
}