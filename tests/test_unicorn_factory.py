"""Tests for Autonomous Unicorn Factory"""

import pytest
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
        """Test creating a unicorn company instance"""
        company = UnicornCompany(
            id="test-1",
            name="Test Unicorn",
            industry="AI SaaS",
            business_model="Subscription",
            valuation=1.5e9,
            arr=100e6
        )
        assert company.id == "test-1"
        assert company.name == "Test Unicorn"
        assert company.valuation == 1.5e9
        assert company.arr == 100e6


class TestMarketIntelligence:
    """Test Market Intelligence System"""
    
    def test_initialization(self):
        """Test market intelligence initialization"""
        mi = MarketIntelligence()
        assert isinstance(mi.opportunities, list)
        
    @pytest.mark.asyncio
    async def test_scan_markets(self):
        """Test market scanning functionality"""
        mi = MarketIntelligence()
        opportunities = await mi.scan_markets()
        assert isinstance(opportunities, list)
        assert len(opportunities) > 0
        assert all('name' in opp for opp in opportunities)
        assert all('opportunity_score' in opp for opp in opportunities)
        # Verify opportunities are sorted by score
        scores = [opp['opportunity_score'] for opp in opportunities]
        assert scores == sorted(scores, reverse=True)


class TestAutomatedBusinessPlan:
    """Test Automated Business Plan Generator"""
    
    def test_initialization(self):
        """Test business plan generator initialization"""
        planner = AutomatedBusinessPlan()
        assert planner.plans_generated == 0
        
    @pytest.mark.asyncio
    async def test_generate_plan(self):
        """Test business plan generation"""
        planner = AutomatedBusinessPlan()
        market = {
            'name': 'AI-powered SaaS',
            'size': 50e9,
            'growth': 0.45,
            'competition': 'low'
        }
        plan = await planner.generate_plan(market)
        
        assert isinstance(plan, dict)
        assert 'market' in plan
        assert 'go_to_market' in plan
        assert 'revenue_model' in plan
        assert 'unit_economics' in plan
        assert 'growth_projections' in plan
        assert 'exit_strategy' in plan
        assert 'time_to_unicorn' in plan
        assert planner.plans_generated == 1
        
    @pytest.mark.asyncio
    async def test_multiple_plan_generation(self):
        """Test generating multiple plans"""
        planner = AutomatedBusinessPlan()
        market1 = {'name': 'Market 1', 'size': 50e9, 'growth': 0.45, 'competition': 'low'}
        market2 = {'name': 'Market 2', 'size': 100e9, 'growth': 0.60, 'competition': 'none'}
        
        await planner.generate_plan(market1)
        await planner.generate_plan(market2)
        
        assert planner.plans_generated == 2


class TestRapidScalingEngine:
    """Test Rapid Scaling Engine"""
    
    def test_initialization(self):
        """Test scaling engine initialization"""
        engine = RapidScalingEngine()
        assert engine.scaling_multiplier == 10
        
    @pytest.mark.asyncio
    async def test_scale_company(self):
        """Test company scaling"""
        engine = RapidScalingEngine()
        company = UnicornCompany(
            id="test-1",
            name="Test Company",
            industry="AI",
            business_model="SaaS",
            arr=1e6,
            growth_rate=0.5
        )
        
        initial_arr = company.arr
        await engine.scale_company(company, months=12)
        
        # Company should have grown
        assert company.arr > initial_arr
        assert company.valuation > 0
        
    @pytest.mark.asyncio
    async def test_scale_to_unicorn(self):
        """Test scaling company to unicorn status"""
        engine = RapidScalingEngine()
        company = UnicornCompany(
            id="test-1",
            name="Fast Growth",
            industry="AI",
            business_model="SaaS",
            arr=10e6,
            growth_rate=1.2  # Very high growth rate
        )
        
        initial_valuation = company.valuation
        await engine.scale_company(company, months=36)
        
        # Verify company scaled significantly
        assert company.valuation > initial_valuation
        assert company.arr > 10e6


class TestUnicornFactory:
    """Test Unicorn Factory System"""
    
    def test_initialization(self):
        """Test unicorn factory initialization"""
        factory = UnicornFactory()
        assert isinstance(factory.market_intel, MarketIntelligence)
        assert isinstance(factory.business_planner, AutomatedBusinessPlan)
        assert isinstance(factory.scaling_engine, RapidScalingEngine)
        assert isinstance(factory.unicorns_created, list)
        assert len(factory.unicorns_created) == 0
        
    @pytest.mark.asyncio
    async def test_create_unicorn(self):
        """Test creating a single unicorn"""
        factory = UnicornFactory()
        unicorn = await factory.create_unicorn()
        
        assert isinstance(unicorn, UnicornCompany)
        assert unicorn.name != ""
        assert unicorn.industry != ""
        assert unicorn.valuation > 0
        assert len(factory.unicorns_created) == 1
        
    @pytest.mark.asyncio
    async def test_create_unicorn_portfolio(self):
        """Test creating a portfolio of unicorns"""
        factory = UnicornFactory()
        await factory.create_unicorn_portfolio(count=3)
        
        assert len(factory.unicorns_created) == 3
        assert all(isinstance(u, UnicornCompany) for u in factory.unicorns_created)
        assert all(u.valuation > 0 for u in factory.unicorns_created)
        
    @pytest.mark.asyncio
    async def test_unicorn_uniqueness(self):
        """Test that each unicorn in portfolio is unique"""
        factory = UnicornFactory()
        await factory.create_unicorn_portfolio(count=2)
        
        unicorn_ids = [u.id for u in factory.unicorns_created]
        # All IDs should be unique
        assert len(unicorn_ids) == len(set(unicorn_ids))
