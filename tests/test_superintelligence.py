"""Tests for APEX Superintelligence Module"""

import pytest
import numpy as np
from src.superintelligence import (
    Knowledge,
    ReasoningEngine,
    SelfImprovementEngine,
    GoalPlanner,
    Superintelligence
)


class TestKnowledge:
    """Test Knowledge dataclass"""
    
    def test_knowledge_creation(self):
        """Test creating a knowledge instance"""
        knowledge = Knowledge(
            domain="test_domain",
            facts=["fact1", "fact2"],
            confidence=0.9,
            timestamp=1.0
        )
        assert knowledge.domain == "test_domain"
        assert len(knowledge.facts) == 2
        assert knowledge.confidence == 0.9


class TestReasoningEngine:
    """Test Reasoning Engine"""
    
    def test_initialization(self):
        """Test reasoning engine initialization"""
        engine = ReasoningEngine()
        assert isinstance(engine.knowledge_base, list)
        assert engine.reasoning_depth == 10
        assert isinstance(engine.logic_chains, list)
        
    def test_add_knowledge(self):
        """Test adding knowledge to the engine"""
        engine = ReasoningEngine()
        initial_count = len(engine.knowledge_base)
        engine.add_knowledge("test_domain", ["fact1", "fact2"], confidence=0.85)
        assert len(engine.knowledge_base) == initial_count + 1
        
    def test_infer(self):
        """Test logical inference"""
        engine = ReasoningEngine()
        premises = ["A implies B", "B implies C"]
        conclusions = engine.infer(premises)
        assert isinstance(conclusions, list)
        
    def test_reason_about(self):
        """Test multi-step reasoning"""
        engine = ReasoningEngine()
        engine.add_knowledge("quantum", ["Quantum computing is fast"], confidence=0.9)
        result = engine.reason_about("quantum computing")
        assert isinstance(result, dict)
        assert 'query' in result
        assert 'confidence' in result
        assert 'steps' in result


class TestSelfImprovementEngine:
    """Test Self-Improvement Engine"""
    
    def test_initialization(self):
        """Test self-improvement engine initialization"""
        engine = SelfImprovementEngine()
        assert isinstance(engine.performance_history, list)
        assert engine.improvement_rate == 0.01
        assert len(engine.capabilities) == 5
        
    def test_improve(self):
        """Test self-improvement mechanism"""
        engine = SelfImprovementEngine()
        initial_reasoning = engine.capabilities['reasoning']
        engine.improve({'reasoning': 0.8, 'learning': 0.9})
        # Capability should improve when score is below 1.0
        assert len(engine.performance_history) == 1
        
    def test_get_capability_score(self):
        """Test overall capability score calculation"""
        engine = SelfImprovementEngine()
        score = engine.get_capability_score()
        assert isinstance(score, float)
        assert score > 0
        
    def test_identify_weaknesses(self):
        """Test weakness identification"""
        engine = SelfImprovementEngine()
        weaknesses = engine.identify_weaknesses()
        assert isinstance(weaknesses, list)


class TestGoalPlanner:
    """Test Goal Planner"""
    
    def test_initialization(self):
        """Test goal planner initialization"""
        planner = GoalPlanner()
        assert isinstance(planner.goals, list)
        assert isinstance(planner.completed_goals, list)
        
    def test_create_goal(self):
        """Test goal creation"""
        planner = GoalPlanner()
        goal = planner.create_goal("Test goal", priority=8)
        assert goal['description'] == "Test goal"
        assert goal['priority'] == 8
        assert goal['status'] == 'planned'
        assert len(planner.goals) == 1
        
    def test_decompose_goal(self):
        """Test goal decomposition into subgoals"""
        planner = GoalPlanner()
        goal = planner.create_goal("Complex goal")
        subgoals = planner.decompose_goal(goal, num_subgoals=3)
        assert len(subgoals) == 3
        assert len(goal['subgoals']) == 3
        
    def test_execute_goal(self):
        """Test goal execution"""
        planner = GoalPlanner()
        goal = planner.create_goal("Executable goal")
        goal_id = goal['id']
        planner.execute_goal(goal_id, progress=1.0)
        assert len(planner.completed_goals) == 1
        assert len(planner.goals) == 0
        
    def test_get_next_goal(self):
        """Test getting highest priority goal"""
        planner = GoalPlanner()
        planner.create_goal("Low priority", priority=3)
        planner.create_goal("High priority", priority=9)
        next_goal = planner.get_next_goal()
        assert next_goal['priority'] == 9
        
    def test_get_next_goal_empty(self):
        """Test getting next goal when none exist"""
        planner = GoalPlanner()
        next_goal = planner.get_next_goal()
        assert next_goal is None


class TestSuperintelligence:
    """Test Superintelligence System"""
    
    def test_initialization(self):
        """Test superintelligence initialization"""
        si = Superintelligence()
        assert isinstance(si.reasoning_engine, ReasoningEngine)
        assert isinstance(si.improvement_engine, SelfImprovementEngine)
        assert isinstance(si.goal_planner, GoalPlanner)
        assert si.consciousness_level == 1.0
        
    def test_think(self):
        """Test high-level thinking process"""
        si = Superintelligence()
        result = si.think("Test problem")
        assert isinstance(result, dict)
        assert 'problem' in result
        assert 'reasoning' in result
        assert 'plan' in result
        assert 'capability_score' in result
        
    def test_learn(self):
        """Test learning from experience"""
        si = Superintelligence()
        initial_consciousness = si.consciousness_level
        experience = {
            'domain': 'test',
            'facts': ['fact1', 'fact2'],
            'confidence': 0.9,
            'performance': {'reasoning': 0.85}
        }
        si.learn(experience)
        assert si.consciousness_level >= initial_consciousness
        
    def test_autonomous_decision(self):
        """Test autonomous decision making"""
        si = Superintelligence()
        context = {
            'options': ['option1', 'option2', 'option3'],
            'constraints': ['time', 'budget']
        }
        decision = si.autonomous_decision(context)
        assert isinstance(decision, str)
        assert decision in context['options'] or decision == "No action"
        
    def test_autonomous_decision_no_options(self):
        """Test autonomous decision with no options"""
        si = Superintelligence()
        context = {'options': [], 'constraints': []}
        decision = si.autonomous_decision(context)
        assert decision == "No action"
