<?php

namespace App\Interfaces;

/**
 * Interface for investment data providers
 * 
 * This interface defines the contract that any investment provider must implement
 * to be compatible with the InvestmentAdapter.
 */
interface InvestmentProviderInterface
{
    /**
     * Get market data including trends, economic indicators, and financial metrics
     * 
     * @return array An associative array containing market data:
     *               - equity_market_trend: string ('bullish', 'bearish', 'neutral')
     *               - interest_rate_trend: string ('rising', 'falling', 'neutral')
     *               - economic_outlook: string ('growth', 'recession', 'stable')
     *               - inflation_rate: float (percentage)
     *               - market_volatility: string ('low', 'moderate', 'high')
     *               - kenya_specific_factors: array of factors specific to the Kenyan market
     */
    public function getMarketData(): array;
    
    /**
     * Get the risk profile for a specific user
     * 
     * @param int $userId The ID of the user
     * @return string The risk profile of the user ('conservative', 'moderate', 'aggressive')
     */
    public function getUserRiskProfile(int $userId): string;
}