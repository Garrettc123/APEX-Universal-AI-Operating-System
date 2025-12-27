"""Tests for Unicorn Factory"""

import pytest
import asyncio
from src.unicorn_factory import (
    UnicornCompany,
    MarketIntelligence,
    AutomatedBusinessPlan,
    RapidScalingEngine,
    UnicornFactory
)


class TestUnicornCompany:
    """Test UnicornCompany dataclass"""
    
    def test_company_creation(self):
        company = UnicornCompany(
            id="unicorn-1",
            name="Test AI Corp",
            industry="AI SaaS",
            business_model="subscription",
            valuation=1e9,
            arr=100e6,
            growth_rate=0.5
        )
        assert company.id == "unicorn-1"
        assert company.name == "Test AI Corp"
        assert company.valuation == 1e9
        assert company.arr == 100e6
        assert company.growth_rate == 0.5


class TestMarketIntelligence:
    """Test MarketIntelligence"""
    
    def test_initialization(self):
        intel = MarketIntelligence()
        assert len(intel.opportunities) == 0
        
    @pytest.mark.asyncio
    async def test_scan_markets(self):
        intel = MarketIntelligence()
        opportunities = await intel.scan_markets()
        assert isinstance(opportunities, list)
        assert len(opportunities) > 0
        # Check that opportunities are sorted by score
        for i in range(len(opportunities) - 1):
            assert opportunities[i]["opportunity_score"] >= opportunities[i + 1]["opportunity_score"]


class TestAutomatedBusinessPlan:
    """Test AutomatedBusinessPlan"""
    
    def test_initialization(self):
        planner = AutomatedBusinessPlan()
        assert planner.plans_generated == 0
        
    @pytest.mark.asyncio
    async def test_generate_plan(self):
        planner = AutomatedBusinessPlan()
        market = {
            "name": "AI Platform",
            "size": 100e9,
            "growth": 0.5,
            "competition": "low"
        }
        plan = await planner.generate_plan(market)
        assert "market" in plan
        assert "go_to_market" in plan
        assert "revenue_model" in plan
        assert "unit_economics" in plan
        assert "growth_projections" in plan
        assert planner.plans_generated == 1


class TestRapidScalingEngine:
    """Test RapidScalingEngine"""
    
    def test_initialization(self):
        engine = RapidScalingEngine()
        assert engine.scaling_multiplier == 10
        
    @pytest.mark.asyncio
    async def test_scale_company(self):
        engine = RapidScalingEngine()
        company = UnicornCompany(
            id="test-1",
            name="Scale Test",
            industry="AI",
            business_model="SaaS",
            arr=1e6,
            growth_rate=0.3
        )
        initial_arr = company.arr
        await engine.scale_company(company, months=12)
        assert company.arr > initial_arr
        assert company.valuation > 0


class TestUnicornFactory:
    """Test UnicornFactory"""
    
    def test_initialization(self):
        factory = UnicornFactory()
        assert isinstance(factory.market_intel, MarketIntelligence)
        assert isinstance(factory.business_planner, AutomatedBusinessPlan)
        assert isinstance(factory.scaling_engine, RapidScalingEngine)
        assert len(factory.unicorns_created) == 0
        
    @pytest.mark.asyncio
    async def test_create_unicorn(self):
        factory = UnicornFactory()
        unicorn = await factory.create_unicorn()
        assert isinstance(unicorn, UnicornCompany)
        assert unicorn.valuation > 0
        assert len(factory.unicorns_created) == 1
        
    @pytest.mark.asyncio
    async def test_create_unicorn_portfolio(self):
        factory = UnicornFactory()
        await factory.create_unicorn_portfolio(count=2)
        assert len(factory.unicorns_created) == 2
        total_valuation = sum(u.valuation for u in factory.unicorns_created)
        assert total_valuation > 0
