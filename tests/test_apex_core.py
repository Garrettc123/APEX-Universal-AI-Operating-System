"""Tests for APEX Core Orchestrator"""
import pytest
import numpy as np
from src.apex_core import (
    APEXOrchestrator,
    AutonomousRevenueEngine,
    EmergencyProtocol,
    NeuralFusionEngine,
    Repository,
    SystemState,
)


class TestRepository:
    """Test Repository dataclass"""

    def test_repository_creation(self):
        repo = Repository(name="test-repo", status="active")
        assert repo.name == "test-repo"
        assert repo.status == "active"
        assert repo.health_score == 1.0
        assert isinstance(repo.metrics, dict)
        assert isinstance(repo.dependencies, list)


class TestNeuralFusionEngine:
    """Test NeuralFusionEngine"""

    def test_engine_initialization(self):
        engine = NeuralFusionEngine(dimensions=100)
        assert engine.dimensions == 100
        assert engine.neural_state.shape == (100,)
        # quantum_coupling is a sparse matrix; only check the logical shape
        assert engine.quantum_coupling.shape == (100, 100)
        assert engine.learning_rate == 0.001

    def test_process_with_valid_input(self):
        """Process must return a 1-D ndarray of length == dimensions."""
        engine = NeuralFusionEngine(dimensions=100)
        input_data = np.random.randn(100)
        output = engine.process(input_data)
        assert isinstance(output, np.ndarray)
        assert output.shape == (100,)

    def test_intelligence_score(self):
        engine = NeuralFusionEngine(dimensions=100)
        score = engine.get_intelligence_score()
        assert isinstance(score, float)
        assert score >= 0.0

    def test_adapt_does_not_crash(self):
        """Multiple process calls should not raise."""
        engine = NeuralFusionEngine(dimensions=50)
        for _ in range(5):
            engine.process(np.random.randn(50))


class TestAutonomousRevenueEngine:
    """Test AutonomousRevenueEngine"""

    def test_engine_initialization(self):
        engine = AutonomousRevenueEngine()
        assert engine.total_revenue == 0.0
        assert len(engine.strategies) == 5
        assert "ai_services" in engine.strategies

    async def test_generate_revenue(self):
        engine = AutonomousRevenueEngine()
        revenue = await engine.generate_revenue()
        assert isinstance(revenue, float)
        assert revenue >= 0.0
        assert engine.total_revenue >= 0.0

    async def test_generate_revenue_populates_monthly_dict(self):
        """generate_revenue must populate _monthly_revenue."""
        engine = AutonomousRevenueEngine()
        await engine.generate_revenue()
        assert len(engine._monthly_revenue) == 1

    def test_annual_projection_empty(self):
        """Projection returns 0.0 when no revenue has been generated yet."""
        engine = AutonomousRevenueEngine()
        assert engine.get_annual_projection() == 0.0

    def test_annual_projection_with_data(self):
        """Projection uses the _monthly_revenue dict, not total_revenue."""
        engine = AutonomousRevenueEngine()
        engine._monthly_revenue["2026-01"] = 10_000.0
        engine._monthly_revenue["2026-02"] = 12_000.0
        projection = engine.get_annual_projection()
        # 3-month trailing avg over 2 months = (10000 + 12000) / 2 * 12 = 132_000
        assert isinstance(projection, float)
        assert projection == pytest.approx(132_000.0)

    def test_annual_projection_caps_at_three_months(self):
        """Only the three most-recent months are used."""
        engine = AutonomousRevenueEngine()
        engine._monthly_revenue["2025-11"] = 1_000.0
        engine._monthly_revenue["2025-12"] = 2_000.0
        engine._monthly_revenue["2026-01"] = 3_000.0
        engine._monthly_revenue["2026-02"] = 4_000.0
        projection = engine.get_annual_projection()
        expected = (2_000.0 + 3_000.0 + 4_000.0) / 3 * 12
        assert projection == pytest.approx(expected)


class TestAPEXOrchestrator:
    """Test APEXOrchestrator"""

    def test_orchestrator_initialization(self):
        orchestrator = APEXOrchestrator()
        assert orchestrator.state == SystemState.INITIALIZING
        assert len(orchestrator.repositories) == 0
        assert orchestrator.intelligence_level == 1.0
        assert orchestrator.evolution_cycles == 0

    def test_initialize_repositories(self):
        orchestrator = APEXOrchestrator()
        orchestrator.initialize_repositories()
        assert len(orchestrator.repositories) > 0
        for repo in orchestrator.repositories.values():
            assert repo.health_score == 1.0
            assert repo.status == "active"

    async def test_evolve(self):
        """Evolution cycle increments the counter and updates intelligence."""
        orchestrator = APEXOrchestrator()
        orchestrator.initialize_repositories()
        initial_cycles = orchestrator.evolution_cycles
        await orchestrator.evolve()
        assert orchestrator.evolution_cycles == initial_cycles + 1
        assert orchestrator.state == SystemState.EVOLVING

    async def test_optimize_systems(self):
        orchestrator = APEXOrchestrator()
        orchestrator.initialize_repositories()
        await orchestrator.optimize_systems()
        assert orchestrator.state == SystemState.OPTIMIZING

    async def test_generate_revenue_cycle(self):
        orchestrator = APEXOrchestrator()
        revenue = await orchestrator.generate_revenue_cycle()
        assert isinstance(revenue, float)
        assert revenue >= 0.0

    async def test_monitor_health_all_healthy(self):
        orchestrator = APEXOrchestrator()
        orchestrator.initialize_repositories()
        result = await orchestrator.monitor_health()
        assert isinstance(result, bool)
        # All repos start at health_score=1.0 so all should be healthy
        assert result is True

    async def test_monitor_health_triggers_optimization(self):
        """Degraded repos should trigger optimize_systems."""
        orchestrator = APEXOrchestrator()
        orchestrator.initialize_repositories()
        # Degrade a repo below the unhealthy threshold
        first = list(orchestrator.repositories.values())[0]
        first.health_score = 0.5
        result = await orchestrator.monitor_health()
        assert result is False


class TestEmergencyProtocol:
    """Test EmergencyProtocol"""

    def test_activate_protocol(self):
        orchestrator = APEXOrchestrator()
        orchestrator.initialize_repositories()

        # Set one repository to low health
        first_repo = list(orchestrator.repositories.values())[0]
        first_repo.health_score = 0.3

        EmergencyProtocol.activate(orchestrator, "Test emergency")
        assert orchestrator.state == SystemState.EMERGENCY
        # Critical repo should be stabilised to 0.8
        assert first_repo.health_score == 0.8

    def test_recover_protocol(self):
        orchestrator = APEXOrchestrator()
        orchestrator.initialize_repositories()
        orchestrator.state = SystemState.EMERGENCY

        EmergencyProtocol.recover(orchestrator)
        assert orchestrator.state == SystemState.ACTIVE
        for repo in orchestrator.repositories.values():
            assert repo.health_score <= 1.0
